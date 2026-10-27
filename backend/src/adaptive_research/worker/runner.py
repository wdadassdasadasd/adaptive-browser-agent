"""Claim and execute tasks with leases; committed PostgreSQL rows own truth."""

import argparse
import asyncio
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.agent.agent_loop import AgentLoop
from adaptive_research.agent.call_observer import CallObserver
from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.llm.base import ProviderUsage
from adaptive_research.agent.state import (
    DecisionContext,
    ResearchState,
    ResearchStatus,
)
from adaptive_research.agent.state_reducer import StateReducer
from adaptive_research.application.agent_factory import new_agent
from adaptive_research.evaluation.current import _source_fingerprint
from adaptive_research.infrastructure.config import (
    REPOSITORY_ROOT,
    Settings,
    get_settings,
)
from adaptive_research.infrastructure.pg_store import (
    FenceLost,
    PgStore,
    PricingUnavailable,
    TaskRecord,
)
from adaptive_research.infrastructure.pricing import load_price_book

log = logging.getLogger(__name__)


class PgCallObserver(CallObserver):
    """Only a fenced task and fixed operation labels cross the ledger boundary."""

    def __init__(
        self,
        store: PgStore,
        task_id: str,
        token: int,
        model: str | None = None,
        source_sha256: str | None = None,
    ) -> None:
        self.store = store
        self.task_id = task_id
        self.token = token
        self.model = model
        self.source_sha256 = source_sha256

    async def started(self, kind: str, operation: str) -> str:
        call = await self.store.start_call(
            self.task_id,
            self.token,
            phase=operation,
            kind=kind,
            provider="deepseek" if kind == "model" else None,
            model=self.model if kind == "model" else None,
            execution_source_sha256=self.source_sha256,
        )
        return call.id

    async def finished(
        self,
        call_id: str,
        outcome: str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        error_type: str | None = None,
        provider_usage: ProviderUsage | None = None,
    ) -> None:
        if outcome == "completed":
            call = await self.store.complete_call(
                self.task_id,
                self.token,
                call_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider_usage=provider_usage,
            )
        else:
            call = await self.store.fail_call(
                self.task_id,
                self.token,
                call_id,
                failure_type=error_type or "unknown_failure",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider_usage=provider_usage,
            )
        if call.kind == "model" and (
            call.known_cost_cny is None or call.pricing_error is not None
        ):
            # The result and unknown expense are already durable. Stop the
            # shared recorder so no retry, repair or report call can follow.
            raise PricingUnavailable("Model response cost is unknown")


class WorkerRunner:
    def __init__(
        self,
        store: PgStore,
        settings: Settings,
        agent_factory: Callable[[], AgentLoop] | None = None,
        *,
        worker_id: str | None = None,
        lease_seconds: int = 30,
        heartbeat_seconds: float = 5,
    ) -> None:
        if lease_seconds <= heartbeat_seconds or heartbeat_seconds <= 0:
            raise ValueError("Lease must exceed a positive heartbeat interval")
        self.store = store
        self.settings = settings
        self.agent_factory = agent_factory or (lambda: new_agent(settings))
        self.worker_id = worker_id or f"{os.getpid()}-{uuid4()}"
        # Computed when the Worker starts, before accepting any paid call.
        self.source_sha256 = (
            _source_fingerprint(REPOSITORY_ROOT)["sha256"]
            if store.require_budget
            else None
        )
        self.lease_seconds = lease_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.active: dict[str, asyncio.Task[None]] = {}
        configured = (
            settings.deepseek_api_key,
            settings.github_token,
            settings.p01_database_url,
        )
        database_password = make_url(settings.require_postgres_url()).password
        self.secrets = tuple(
            value
            for value in (
                *(secret.get_secret_value() for secret in configured if secret),
                database_password,
            )
            if value
        )

    def _redact(self, value: Any) -> Any:
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, "[REDACTED]")
            return value
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, dict):
            return {key: self._redact(item) for key, item in value.items()}
        return value

    async def _recovery_snapshot(
        self, task: TaskRecord
    ) -> tuple[ResearchState, tuple[AgentEvent, ...]]:
        committed = await self.store.list_events(task.owner_id, task.id)
        if committed is None:
            raise ValueError("Claimed task is not visible to its owner")
        state = ResearchState(
            task_id=task.id,
            goal=task.goal,
            decision_context=getattr(task, "decision_context", None),
            max_steps=self.settings.max_steps,
            status=ResearchStatus.RUNNING,
        )
        reducer = StateReducer()
        history: list[AgentEvent] = []
        for row in committed:
            if row.event_type not in {"subgoals_initialized", "step_evaluated"}:
                continue
            event = AgentEvent(
                event_id=str(UUID(int=row.id)),
                event_type=row.event_type,
                task_id=row.task_id,
                step=row.step,
                timestamp=row.created_at,
                message=row.message,
                payload=row.payload,
            )
            state = reducer.reduce(state, event)
            history.append(event)
        persisted_facts = await self.store.list_facts(task.owner_id, task.id)
        if persisted_facts is None:
            raise ValueError("Claimed task facts are not visible to its owner")
        admitted = {
            fact.id: (
                fact.subject or fact.source_title,
                fact.content,
                str(fact.source_url),
                fact.evidence,
            )
            for fact in state.facts
        }
        stored = {
            fact.id: (
                fact.subject,
                fact.claim,
                fact.official_source_url,
                fact.evidence_excerpt,
            )
            for fact in persisted_facts
            if fact.machine_admission_status == "candidate_unverified_official"
        }
        if admitted != stored or len(stored) != len(persisted_facts):
            raise ValueError("Committed facts differ from admitted event history")
        by_id = {fact.id: fact for fact in persisted_facts}
        state = state.model_copy(
            update={
                "facts": [
                    fact.model_copy(update={"created_at": by_id[fact.id].retrieved_at})
                    for fact in state.facts
                ]
            }
        )
        calls = await self.store.list_calls(task.owner_id, task.id)
        # A provider response may commit before its corresponding step event.
        # Retain that known usage on recovery without counting it twice.
        state = state.model_copy(
            update={
                "prompt_tokens": max(
                    state.prompt_tokens,
                    sum(call.reported_prompt_tokens or 0 for call in calls or ()),
                ),
                "completion_tokens": max(
                    state.completion_tokens,
                    sum(call.reported_completion_tokens or 0 for call in calls or ()),
                ),
            }
        )
        return state, tuple(history)

    async def run_claim(self, task: TaskRecord) -> None:
        cancellation = asyncio.Event()
        terminal_written = False
        lease_lost = False
        admitted_state = ResearchState(
            task_id=task.id,
            goal=task.goal,
            decision_context=getattr(task, "decision_context", None),
            max_steps=self.settings.max_steps,
            status=ResearchStatus.RUNNING,
        )

        async def on_event(event: AgentEvent) -> None:
            nonlocal admitted_state, terminal_written
            if lease_lost:
                raise FenceLost(task.id)
            if event.event_type == "task_started":
                # Claim and task_started are already committed in one transaction.
                return
            if event.event_type == "task_finished":
                payload = self._redact(event.payload)
                await self.store.mark_unknown_calls(task.id, task.fencing_token)
                await self.store.finish_task(
                    task.id,
                    task.fencing_token,
                    str(payload["status"]),
                    completion_level=str(payload.get("completion_level", "none")),
                    stop_reason=payload.get("stop_reason"),
                    report=payload.get("report"),
                    budget_preflight=payload.get("budget_preflight"),
                )
                terminal_written = True
                return
            # A pending cancellation has its own committed API event.
            if event.event_type == "cancel_requested":
                return
            safe_payload = self._redact(event.payload)
            safe_message = self._redact(event.message)
            if (
                len(json.dumps(safe_payload, ensure_ascii=False).encode("utf-8"))
                > 64_000
            ):
                raise ValueError("Agent event exceeds the storage limit")
            next_state = admitted_state
            facts: list[dict[str, Any]] = []
            if event.event_type == "subgoals_initialized" or (
                event.event_type == "step_evaluated" and event.payload
            ):
                next_state = StateReducer().reduce(admitted_state, event)
                prior_ids = {fact.id for fact in admitted_state.facts}
                for fact in next_state.facts:
                    if fact.id in prior_ids:
                        continue
                    facts.append(
                        {
                            "id": fact.id,
                            "subject": self._redact(fact.subject or fact.source_title),
                            "claim": self._redact(fact.content),
                            "official_source_url": str(fact.source_url),
                            "retrieved_at": fact.created_at,
                            "machine_admission_status": "candidate_unverified_official",
                            "evidence_excerpt": self._redact(fact.evidence),
                        }
                    )
            await self.store.append_event(
                task.id,
                task.fencing_token,
                event.event_type,
                step=event.step,
                message=safe_message,
                payload=safe_payload,
                facts=facts,
            )
            admitted_state = next_state

        async def heartbeat() -> None:
            nonlocal lease_lost
            while True:
                await asyncio.sleep(self.heartbeat_seconds)
                try:
                    live = await self.store.renew_lease(
                        task.id,
                        task.fencing_token,
                        self.worker_id,
                        self.lease_seconds,
                    )
                    current = await self.store.get_task(task.owner_id, task.id)
                except (SQLAlchemyError, OSError) as exc:
                    # A database outage cannot be interpreted as a successful lease.
                    log.error(
                        "Worker lease check failed for task %s (%s)",
                        task.id,
                        type(exc).__name__,
                    )
                    lease_lost = True
                    cancellation.set()
                    return
                if not live or current is None or current.status != "running":
                    lease_lost = True
                    cancellation.set()
                    return
                if current.cancellation_requested:
                    cancellation.set()

        heartbeat_task = asyncio.create_task(heartbeat())
        try:
            agent = self.agent_factory()
            if self.store.require_budget and (
                agent.max_tokens > 40_000 or self.settings.max_steps > 30
            ):
                raise PricingUnavailable("Pilot agent limits exceed the frozen budget")
            resume_kwargs = {}
            if task.recovery_count:
                state, history = await self._recovery_snapshot(task)
                admitted_state = state
                resume_kwargs = {"resume_state": state, "prior_events": history}
            decision_kwargs = (
                {
                    "decision_context": DecisionContext.model_validate(
                        task.decision_context
                    )
                }
                if getattr(task, "decision_context", None) is not None
                else {}
            )
            await agent.run(
                task.goal,
                cancellation=cancellation,
                task_id=task.id,
                on_event=on_event,
                call_observer=PgCallObserver(
                    self.store,
                    task.id,
                    task.fencing_token,
                    self.settings.deepseek_model,
                    self.source_sha256,
                ),
                **decision_kwargs,
                **resume_kwargs,
            )
            if not terminal_written and not lease_lost:
                await self.store.mark_unknown_calls(task.id, task.fencing_token)
                await self.store.finish_task(
                    task.id,
                    task.fencing_token,
                    "failed",
                    stop_reason="missing_terminal_event",
                )
        except FenceLost:
            log.warning("Fencing token lost for task %s", task.id)
        except Exception as exc:  # noqa: BLE001 - terminal boundary for an isolated task executor
            log.error(
                "Research execution failed for task %s (%s)",
                task.id,
                type(exc).__name__,
            )
            if not lease_lost and not terminal_written:
                try:
                    await self.store.mark_unknown_calls(task.id, task.fencing_token)
                    await self.store.finish_task(
                        task.id,
                        task.fencing_token,
                        "failed",
                        stop_reason="execution_error",
                    )
                except (FenceLost, SQLAlchemyError, OSError) as exc:
                    log.error(
                        "Terminal write failed for task %s (%s)",
                        task.id,
                        type(exc).__name__,
                    )
        finally:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)

    async def tick(self) -> int:
        await self.store.reconcile_expired()
        self.active = {
            key: value for key, value in self.active.items() if not value.done()
        }
        claimed = 0
        while len(self.active) < 2:
            task = await self.store.claim_next(self.worker_id, self.lease_seconds)
            if task is None:
                break
            self.active[task.id] = asyncio.create_task(self.run_claim(task))
            claimed += 1
        return claimed

    async def run_forever(self, poll_seconds: float = 0.25) -> None:
        while True:
            try:
                await self.tick()
            except (SQLAlchemyError, OSError) as exc:
                # No memory queue fallback: wait for PostgreSQL to return.
                log.error("Worker poll failed; retrying (%s)", type(exc).__name__)
            await asyncio.sleep(poll_seconds)


async def main(price_book_path: Path | None = None) -> None:
    settings = get_settings()
    price_book = None
    if price_book_path is not None:
        path = price_book_path
        if not path.is_absolute():
            path = REPOSITORY_ROOT / path
        price_book = load_price_book(path)
    engine = create_async_engine(settings.require_postgres_url(), pool_pre_ping=True)
    store = PgStore(
        async_sessionmaker(engine, expire_on_commit=False),
        price_book=price_book,
        require_budget=price_book is not None,
    )
    runner = WorkerRunner(store, settings)
    try:
        await runner.run_forever()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--price-book",
        type=Path,
        help="explicit CNY snapshot; enable strict model-cost checks (not a budget authorization)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(args.price_book))
