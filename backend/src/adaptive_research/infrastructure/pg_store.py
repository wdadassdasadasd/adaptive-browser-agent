"""Short PostgreSQL transactions for task ownership, leases and committed events."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adaptive_research.agent.llm.base import ProviderUsage
from adaptive_research.agent.state import DecisionContext
from adaptive_research.infrastructure.pg_models import (
    PgBudget,
    PgCallAttempt,
    PgCost,
    PgEvent,
    PgFact,
    PgOwner,
    PgReport,
    PgSchedulerGuard,
    PgTask,
)
from adaptive_research.infrastructure.pricing import calculate_call_cost
from adaptive_research.infrastructure.tool_billing import nonbillable_tool_basis

TERMINAL = frozenset({"completed", "partial", "failed", "cancelled"})


class CapacityFull(Exception):
    """The two running and eight waiting slots are occupied."""


class IdempotencyConflict(Exception):
    """A submitted key already belongs to a different normalized request."""


class FenceLost(Exception):
    """This worker no longer owns the live task generation."""


class PricingUnavailable(Exception):
    """An explicitly priced execution cannot safely start another model call."""


@dataclass(frozen=True)
class TaskRecord:
    id: str
    owner_id: str
    goal: str
    status: str
    cancellation_requested: bool
    fencing_token: int
    recovery_count: int
    lease_owner: str | None
    lease_expires_at: datetime | None
    completion_level: str
    stop_reason: str | None
    error_message: str | None
    report: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    decision_context: dict[str, Any] | None = None


@dataclass(frozen=True)
class EventRecord:
    id: int
    task_id: str
    event_type: str
    step: int
    message: str
    payload: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class CallRecord:
    id: str
    task_id: str
    fencing_token: int
    phase: str
    kind: str
    status: str
    provider: str | None
    model: str | None
    price_revision: str | None
    reported_prompt_tokens: int | None
    reported_completion_tokens: int | None
    prompt_cache_hit_tokens: int | None
    prompt_cache_miss_tokens: int | None
    provider_created_at: int | None
    reported_model: str | None
    system_fingerprint: str | None
    pricing_error: str | None
    pricing_tariff: str | None
    known_cost_cny: Decimal | None
    cost_basis: str | None
    execution_source_sha256: str | None
    failure_type: str | None
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True)
class CostRecord:
    task_id: str
    known_cost_cny: Decimal
    unknown_attempt_count: int
    updated_at: datetime


@dataclass(frozen=True)
class FactRecord:
    id: str
    task_id: str
    fencing_token: int
    subject: str
    claim: str
    official_source_url: str
    official_identity_basis: str | None
    evidence_excerpt: str | None
    evidence_locator: str | None
    retrieved_at: datetime
    machine_admission_status: str
    human_review_status: str | None
    reviewed_at: datetime | None
    created_at: datetime


class PgStore:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        *,
        price_book: Mapping[str, Any] | None = None,
        require_budget: bool = False,
    ) -> None:
        self.sessions = sessions
        self.price_book = price_book
        self.require_budget = require_budget

    @staticmethod
    async def _now(session: AsyncSession) -> datetime:
        return await session.scalar(select(func.clock_timestamp()))

    @staticmethod
    async def _guard(session: AsyncSession) -> None:
        guard = await session.scalar(
            select(PgSchedulerGuard).where(PgSchedulerGuard.id == 1).with_for_update()
        )
        if guard is None:
            raise RuntimeError(
                "PostgreSQL application migration has not seeded scheduler_guard"
            )

    @staticmethod
    async def _event(
        session: AsyncSession,
        task: PgTask,
        event_type: str,
        *,
        step: int = 0,
        message: str = "",
        payload: dict[str, Any] | None = None,
        token: int | None = None,
    ) -> EventRecord:
        event = PgEvent(
            task_id=task.id,
            event_type=event_type,
            step=step,
            message=message,
            payload=payload or {},
            fencing_token=token,
        )
        session.add(event)
        await session.flush()
        return EventRecord(
            event.id,
            event.task_id,
            event.event_type,
            event.step,
            event.message,
            event.payload,
            event.created_at,
        )

    @staticmethod
    async def _record(session: AsyncSession, task: PgTask) -> TaskRecord:
        report = await session.get(PgReport, task.id)
        return PgStore._task_record(
            task, report.payload if report is not None else None
        )

    @staticmethod
    def _task_record(task: PgTask, report: dict[str, Any] | None) -> TaskRecord:
        return TaskRecord(
            task.id,
            task.owner_id,
            task.goal,
            task.status,
            task.cancellation_requested,
            task.fencing_token,
            task.recovery_count,
            task.lease_owner,
            task.lease_expires_at,
            task.completion_level,
            task.stop_reason,
            task.error_message,
            report,
            task.created_at,
            task.updated_at,
            task.decision_context,
        )

    async def _live(self, session: AsyncSession, task_id: str, token: int) -> PgTask:
        task = await session.scalar(
            select(PgTask).where(PgTask.id == task_id).with_for_update()
        )
        now = await self._now(session)
        if (
            task is None
            or task.status != "running"
            or task.fencing_token != token
            or task.lease_expires_at is None
            or task.lease_expires_at <= now
        ):
            raise FenceLost(task_id)
        return task

    async def create_task(
        self,
        owner_id: str,
        goal: str,
        *,
        idempotency_key: str | None = None,
        decision_context: DecisionContext | Mapping[str, Any] | None = None,
    ) -> TaskRecord:
        if not owner_id.strip() or not goal.strip():
            raise ValueError("owner_id and goal are required")
        if idempotency_key is not None and not re.fullmatch(
            r"[A-Za-z0-9._:-]{8,128}", idempotency_key
        ):
            raise ValueError("Invalid idempotency key")
        normalized_context = (
            DecisionContext.model_validate(decision_context).model_dump(mode="json")
            if decision_context is not None
            else None
        )
        async with self.sessions.begin() as session:
            await self._guard(session)
            if idempotency_key is not None:
                prior = await session.scalar(
                    select(PgTask).where(
                        PgTask.owner_id == owner_id,
                        PgTask.idempotency_key == idempotency_key,
                    )
                )
                if prior is not None:
                    if (
                        prior.goal != goal
                        or prior.decision_context != normalized_context
                    ):
                        raise IdempotencyConflict
                    return await self._record(session, prior)
            counts = (
                await session.execute(
                    select(PgTask.status, func.count(PgTask.id))
                    .where(PgTask.status.in_(("running", "queued")))
                    .group_by(PgTask.status)
                )
            ).all()
            by_status = dict(counts)
            if by_status.get("queued", 0) >= 8 or sum(by_status.values()) >= 10:
                raise CapacityFull
            # P-01 uses one fixed synthetic owner. P-03 replaces this with authenticated accounts.
            await session.execute(
                insert(PgOwner)
                .values(id=owner_id, is_synthetic=True)
                .on_conflict_do_nothing(index_elements=[PgOwner.id])
            )
            task = PgTask(
                owner_id=owner_id,
                goal=goal,
                idempotency_key=idempotency_key,
                decision_context=normalized_context,
            )
            session.add(task)
            await session.flush()
            session.add(PgCost(task_id=task.id))
            await self._event(
                session, task, "task_queued", payload={"status": "queued"}
            )
            return await self._record(session, task)

    async def get_idempotent_task(
        self,
        owner_id: str,
        goal: str,
        idempotency_key: str,
        *,
        decision_context: DecisionContext | Mapping[str, Any] | None = None,
    ) -> TaskRecord | None:
        """Return a matching task or reject reuse of its key for another request."""
        if not owner_id.strip() or not goal.strip():
            raise ValueError("owner_id and goal are required")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key):
            raise ValueError("Invalid idempotency key")
        normalized_context = (
            DecisionContext.model_validate(decision_context).model_dump(mode="json")
            if decision_context is not None
            else None
        )
        async with self.sessions.begin() as session:
            prior = await session.scalar(
                select(PgTask).where(
                    PgTask.owner_id == owner_id,
                    PgTask.idempotency_key == idempotency_key,
                )
            )
            if prior is None:
                return None
            if prior.goal != goal or prior.decision_context != normalized_context:
                raise IdempotencyConflict
            return await self._record(session, prior)

    async def claim_next(
        self, worker_id: str, lease_seconds: int = 30
    ) -> TaskRecord | None:
        if not worker_id or lease_seconds <= 0:
            raise ValueError("worker_id and positive lease_seconds are required")
        async with self.sessions.begin() as session:
            await self._guard(session)
            running = await session.scalar(
                select(func.count(PgTask.id)).where(PgTask.status == "running")
            )
            if running >= 2:
                return None
            task = await session.scalar(
                select(PgTask)
                .where(PgTask.status == "queued")
                .order_by(PgTask.created_at, PgTask.id)
                .limit(1)
                .with_for_update()
            )
            if task is None:
                return None
            now = await self._now(session)
            task.status = "running"
            task.fencing_token += 1
            task.lease_owner = worker_id
            task.lease_expires_at = now + timedelta(seconds=lease_seconds)
            task.updated_at = now
            await self._event(
                session,
                task,
                "task_started",
                payload={"status": "running", "recovery_count": task.recovery_count},
                token=task.fencing_token,
            )
            return await self._record(session, task)

    async def renew_lease(
        self, task_id: str, token: int, worker_id: str, lease_seconds: int = 30
    ) -> bool:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        async with self.sessions.begin() as session:
            try:
                task = await self._live(session, task_id, token)
            except FenceLost:
                return False
            if task.lease_owner != worker_id:
                return False
            now = await self._now(session)
            task.lease_expires_at = now + timedelta(seconds=lease_seconds)
            task.updated_at = now
            return True

    async def request_cancel(self, owner_id: str, task_id: str) -> TaskRecord | None:
        async with self.sessions.begin() as session:
            await self._guard(session)
            task = await session.scalar(
                select(PgTask)
                .where(PgTask.id == task_id, PgTask.owner_id == owner_id)
                .with_for_update()
            )
            if task is None:
                return None
            if task.status in TERMINAL or task.cancellation_requested:
                return await self._record(session, task)
            now = await self._now(session)
            task.cancellation_requested = True
            task.updated_at = now
            if task.status == "queued":
                task.status = "cancelled"
                task.stop_reason = "user_cancelled"
                task.terminal_at = now
                await self._event(
                    session, task, "task_finished", payload={"status": "cancelled"}
                )
            else:
                await self._event(
                    session,
                    task,
                    "cancel_requested",
                    payload={"status": "running", "cancellation_requested": True},
                )
            return await self._record(session, task)

    async def append_event(
        self,
        task_id: str,
        token: int,
        event_type: str,
        step: int = 0,
        message: str = "",
        payload: dict[str, Any] | None = None,
        facts: list[dict[str, Any]] | None = None,
    ) -> EventRecord:
        if event_type == "task_finished":
            raise ValueError("use finish_task for a terminal event")
        async with self.sessions.begin() as session:
            await self._guard(session)
            task = await self._live(session, task_id, token)
            for fact in facts or ():
                session.add(PgFact(task_id=task_id, fencing_token=token, **fact))
            await session.flush()
            return await self._event(
                session,
                task,
                event_type,
                step=step,
                message=message,
                payload=payload,
                token=token,
            )

    async def finish_task(
        self,
        task_id: str,
        token: int,
        status: str,
        error_message: str | None = None,
        *,
        completion_level: str = "none",
        stop_reason: str | None = None,
        report: dict[str, Any] | None = None,
        budget_preflight: dict[str, Any] | None = None,
    ) -> TaskRecord:
        if status not in TERMINAL:
            raise ValueError("finish_task requires a terminal status")
        async with self.sessions.begin() as session:
            await self._guard(session)
            task = await self._live(session, task_id, token)
            now = await self._now(session)
            await self._unknown_started(session, task_id, token, now)
            task.status = status
            task.completion_level = completion_level
            task.stop_reason = stop_reason
            task.error_message = error_message
            task.lease_owner = None
            task.lease_expires_at = None
            task.terminal_at = now
            task.updated_at = now
            if report is not None:
                session.add(
                    PgReport(task_id=task.id, fencing_token=token, payload=report)
                )
                await session.flush()
            await self._event(
                session,
                task,
                "task_finished",
                payload={
                    "status": status,
                    "completion_level": completion_level,
                    "stop_reason": stop_reason,
                    "report": report,
                    **(
                        {"budget_preflight": budget_preflight}
                        if budget_preflight is not None
                        else {}
                    ),
                },
                token=token,
            )
            return await self._record(session, task)

    async def get_task(self, owner_id: str, task_id: str) -> TaskRecord | None:
        async with self.sessions() as session:
            row = (
                await session.execute(
                    select(PgTask, PgReport.payload)
                    .outerjoin(PgReport, PgReport.task_id == PgTask.id)
                    .where(PgTask.id == task_id, PgTask.owner_id == owner_id)
                )
            ).first()
            return self._task_record(row[0], row[1]) if row is not None else None

    async def get_task_by_idempotency_key(
        self, owner_id: str, idempotency_key: str
    ) -> TaskRecord | None:
        """Recover an ambiguous submission without creating a second task."""

        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key):
            raise ValueError("Invalid idempotency key")
        async with self.sessions() as session:
            row = (
                await session.execute(
                    select(PgTask, PgReport.payload)
                    .outerjoin(PgReport, PgReport.task_id == PgTask.id)
                    .where(
                        PgTask.owner_id == owner_id,
                        PgTask.idempotency_key == idempotency_key,
                    )
                )
            ).first()
            return self._task_record(row[0], row[1]) if row is not None else None

    async def list_tasks(self, owner_id: str) -> list[TaskRecord]:
        async with self.sessions() as session:
            rows = (
                await session.execute(
                    select(PgTask, PgReport.payload)
                    .outerjoin(PgReport, PgReport.task_id == PgTask.id)
                    .where(PgTask.owner_id == owner_id)
                    .order_by(PgTask.created_at.desc(), PgTask.id.desc())
                )
            ).all()
            return [self._task_record(row[0], row[1]) for row in rows]

    async def list_events(
        self, owner_id: str, task_id: str, after_id: int = 0
    ) -> list[EventRecord] | None:
        async with self.sessions() as session:
            visible = await session.scalar(
                select(PgTask.id).where(
                    PgTask.id == task_id, PgTask.owner_id == owner_id
                )
            )
            if visible is None:
                return None
            events = (
                await session.scalars(
                    select(PgEvent)
                    .where(PgEvent.task_id == task_id, PgEvent.id > after_id)
                    .order_by(PgEvent.id)
                )
            ).all()
            return [
                EventRecord(
                    event.id,
                    event.task_id,
                    event.event_type,
                    event.step,
                    event.message,
                    event.payload,
                    event.created_at,
                )
                for event in events
            ]

    async def reconcile_expired(self) -> list[TaskRecord]:
        changed: list[TaskRecord] = []
        async with self.sessions.begin() as session:
            await self._guard(session)
            now = await self._now(session)
            tasks = (
                await session.scalars(
                    select(PgTask)
                    .where(PgTask.status == "running", PgTask.lease_expires_at <= now)
                    .order_by(PgTask.created_at, PgTask.id)
                    .with_for_update()
                )
            ).all()
            for task in tasks:
                await self._unknown_started(session, task.id, task.fencing_token, now)
                task.lease_owner = None
                task.lease_expires_at = None
                task.updated_at = now
                if task.cancellation_requested:
                    task.status = "cancelled"
                    task.stop_reason = "user_cancelled"
                elif task.recovery_count == 0:
                    task.status = "queued"
                    task.recovery_count = 1
                    await self._event(
                        session,
                        task,
                        "task_requeued",
                        payload={"status": "queued", "recovery_count": 1},
                    )
                    changed.append(await self._record(session, task))
                    continue
                else:
                    fact_count = await session.scalar(
                        select(func.count(PgFact.id)).where(PgFact.task_id == task.id)
                    )
                    task.status = "partial" if fact_count else "failed"
                    task.stop_reason = "second_worker_failure"
                    task.error_message = "worker lease expired twice"
                task.terminal_at = now
                await self._event(
                    session,
                    task,
                    "task_finished",
                    payload={"status": task.status, "stop_reason": task.stop_reason},
                )
                changed.append(await self._record(session, task))
        return changed

    @staticmethod
    async def _unknown_started(
        session: AsyncSession, task_id: str, token: int, now: datetime
    ) -> int:
        calls = (
            await session.scalars(
                select(PgCallAttempt)
                .where(
                    PgCallAttempt.task_id == task_id,
                    PgCallAttempt.fencing_token == token,
                    PgCallAttempt.status == "started",
                )
                .with_for_update()
            )
        ).all()
        for call in calls:
            call.status = "unknown_outcome"
            call.ended_at = now
        if calls:
            cost = await session.get(PgCost, task_id, with_for_update=True)
            cost.unknown_attempt_count += len(calls)
            cost.updated_at = now
            if any(call.kind == "model" for call in calls):
                budget = await session.get(PgBudget, 1)
                if budget is not None:
                    budget.status = "halted"
                    budget.halt_reason = "unknown_model_outcome"
        return len(calls)

    async def mark_unknown_calls(self, task_id: str, token: int) -> int:
        async with self.sessions.begin() as session:
            await self._guard(session)
            await self._live(session, task_id, token)
            return await self._unknown_started(
                session, task_id, token, await self._now(session)
            )

    async def arm_pilot_budget(
        self,
        *,
        authorization_reference: str,
        phase_max_cny: Decimal,
    ) -> None:
        """Persist a single pilot ceiling before accepting any paid attempt.

        The caller must already have separate human authorization. This method
        cannot manufacture authorization and is never called at startup.
        """
        if not re.fullmatch(r"[A-Za-z0-9:/._-]{4,128}", authorization_reference):
            raise ValueError("A safe authorization reference is required")
        if not isinstance(phase_max_cny, Decimal) or not (
            Decimal(1) <= phase_max_cny <= Decimal(49)
        ):
            raise ValueError("Pilot cap must be between 1 and 49 CNY")
        if self.price_book is None:
            raise PricingUnavailable("A verified price book is required")
        async with self.sessions.begin() as session:
            await self._guard(session)
            if await session.get(PgBudget, 1) is not None:
                raise PricingUnavailable("An allocation already exists")
            if await session.scalar(select(func.count(PgTask.id))):
                raise PricingUnavailable("Pilot must use an empty application database")
            now = await self._now(session)
            preflight = calculate_call_cost(
                model="deepseek-flash",
                currency="CNY",
                started_at=now,
                finished_at=now,
                prompt_tokens=0,
                prompt_cache_hit_tokens=0,
                prompt_cache_miss_tokens=0,
                completion_tokens=0,
                price_book=self.price_book,
                evaluated_at=now,
            )
            if preflight.reason is not None:
                raise PricingUnavailable("Price book cannot arm a pilot")
            # The production AgentLoop is capped at 40,000 total tokens.
            # Reserve 1 CNY per in-flight request only if every published
            # input/output tariff prices that entire allowance within 1 CNY.
            rates = self.price_book["rates_cny_per_million"]
            maximum_rate = max(
                Decimal(rate)
                for tariff in ("peak", "off_peak")
                for rate in rates[tariff].values()
            )
            if maximum_rate * Decimal(40000) / Decimal(1000000) > Decimal(1):
                raise PricingUnavailable("Price book exceeds the call reservation")
            session.add(
                PgBudget(
                    id=1,
                    phase="pilot",
                    status="armed",
                    phase_max_cny=phase_max_cny,
                    project_max_cny=Decimal(299),
                    reserve_per_call_cny=Decimal(1),
                    price_revision=preflight.price_revision,
                    price_book_sha256=self.price_book["snapshot_sha256"],
                    authorization_reference=authorization_reference,
                )
            )

    async def get_budget(self) -> PgBudget | None:
        async with self.sessions() as session:
            return await session.get(PgBudget, 1)

    async def start_call(
        self,
        task_id: str,
        token: int,
        *,
        phase: str,
        kind: str,
        safe_input_digest: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        price_revision: str | None = None,
        execution_source_sha256: str | None = None,
    ) -> CallRecord:
        async with self.sessions.begin() as session:
            await self._guard(session)
            await self._live(session, task_id, token)
            budget = await session.get(PgBudget, 1) if kind == "model" else None
            if kind == "model" and (self.require_budget or budget is not None):
                if budget is None or self.price_book is None:
                    raise PricingUnavailable("Pilot budget or price book is missing")
                if (
                    budget.status != "armed"
                    or budget.phase != "pilot"
                    or budget.price_revision != self.price_book.get("price_revision")
                    or budget.price_book_sha256
                    != self.price_book.get("snapshot_sha256")
                ):
                    raise PricingUnavailable("Pilot budget is unavailable")
                unresolved = await session.scalar(
                    select(func.count(PgCallAttempt.id)).where(
                        PgCallAttempt.kind == "model",
                        PgCallAttempt.known_cost_cny.is_(None),
                    )
                )
                known_total = await session.scalar(
                    select(
                        func.coalesce(func.sum(PgCallAttempt.known_cost_cny), 0)
                    ).where(PgCallAttempt.kind == "model")
                )
                if unresolved:
                    raise PricingUnavailable("An earlier model cost is unresolved")
                if (
                    known_total + budget.reserve_per_call_cny > budget.phase_max_cny
                    or known_total + budget.reserve_per_call_cny
                    >= budget.project_max_cny
                ):
                    raise PricingUnavailable("Pilot budget is exhausted")
            if kind == "model" and self.price_book is not None:
                now = await self._now(session)
                preflight = calculate_call_cost(
                    model=model or "",
                    currency="CNY",
                    started_at=now,
                    finished_at=now,
                    prompt_tokens=0,
                    prompt_cache_hit_tokens=0,
                    prompt_cache_miss_tokens=0,
                    completion_tokens=0,
                    price_book=self.price_book,
                    evaluated_at=now,
                )
                unresolved = await session.scalar(
                    select(func.count(PgCallAttempt.id)).where(
                        PgCallAttempt.task_id == task_id,
                        PgCallAttempt.kind == "model",
                        PgCallAttempt.known_cost_cny.is_(None),
                    )
                )
                if preflight.reason is not None or unresolved:
                    raise PricingUnavailable("Model pricing is not confirmed")
                price_revision = preflight.price_revision
            call = PgCallAttempt(
                task_id=task_id,
                fencing_token=token,
                phase=phase,
                kind=kind,
                safe_input_digest=safe_input_digest,
                provider=provider,
                model=model,
                price_revision=price_revision,
                execution_source_sha256=execution_source_sha256,
            )
            session.add(call)
            await session.flush()
            return self._call_record(call)

    @staticmethod
    def _call_record(call: PgCallAttempt) -> CallRecord:
        return CallRecord(
            call.id,
            call.task_id,
            call.fencing_token,
            call.phase,
            call.kind,
            call.status,
            call.provider,
            call.model,
            call.price_revision,
            call.reported_prompt_tokens,
            call.reported_completion_tokens,
            call.prompt_cache_hit_tokens,
            call.prompt_cache_miss_tokens,
            call.provider_created_at,
            call.reported_model,
            call.system_fingerprint,
            call.pricing_error,
            call.pricing_tariff,
            call.known_cost_cny,
            call.cost_basis,
            call.execution_source_sha256,
            call.failure_type,
            call.started_at,
            call.ended_at,
        )

    async def _end_call(
        self,
        task_id: str,
        token: int,
        call_id: str,
        status: str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        known_cost_cny: Decimal | None = None,
        safe_output_digest: str | None = None,
        failure_type: str | None = None,
        provider_usage: ProviderUsage | None = None,
    ) -> CallRecord:
        async with self.sessions.begin() as session:
            await self._guard(session)
            await self._live(session, task_id, token)
            call = await session.scalar(
                select(PgCallAttempt)
                .where(PgCallAttempt.id == call_id, PgCallAttempt.task_id == task_id)
                .with_for_update()
            )
            if call is None or call.fencing_token != token or call.status != "started":
                raise FenceLost(call_id)
            now = await self._now(session)
            call.status = status
            call.reported_prompt_tokens = prompt_tokens
            call.reported_completion_tokens = completion_tokens
            if provider_usage is not None:
                call.prompt_cache_hit_tokens = provider_usage.prompt_cache_hit_tokens
                call.prompt_cache_miss_tokens = provider_usage.prompt_cache_miss_tokens
                call.provider_created_at = provider_usage.provider_created_at
                call.reported_model = provider_usage.reported_model
                call.system_fingerprint = provider_usage.system_fingerprint
            if self.price_book is not None and call.kind == "model":
                # Persist the selected revision even when this request cannot be
                # priced. No response metadata is inferred from requested model.
                call.price_revision = self.price_book.get("price_revision")
                decision = calculate_call_cost(
                    model=call.reported_model,
                    currency="CNY",
                    started_at=call.started_at,
                    finished_at=now,
                    prompt_tokens=prompt_tokens,
                    prompt_cache_hit_tokens=call.prompt_cache_hit_tokens,
                    prompt_cache_miss_tokens=call.prompt_cache_miss_tokens,
                    completion_tokens=completion_tokens,
                    price_book=self.price_book,
                    evaluated_at=now,
                )
                known_cost_cny = decision.known_cost_cny
                call.pricing_error = decision.reason
                call.pricing_tariff = decision.tariff
                if (
                    known_cost_cny is not None
                    and known_cost_cny != known_cost_cny.quantize(Decimal("0.00000001"))
                ):
                    # Numeric(18, 8) must never silently round a verified
                    # calculation to a different persisted amount.
                    known_cost_cny = None
                    call.pricing_error = "unsupported_cost_precision"
                    call.pricing_tariff = None
                if known_cost_cny is not None:
                    call.cost_basis = "deepseek_token_price_snapshot"
            elif call.kind == "tool":
                basis = nonbillable_tool_basis(call.kind, call.phase)
                if basis is not None:
                    known_cost_cny = Decimal(0)
                    call.cost_basis = basis
                else:
                    known_cost_cny = None
            call.known_cost_cny = known_cost_cny
            call.safe_output_digest = safe_output_digest
            call.failure_type = failure_type
            call.ended_at = now
            budget = await session.get(PgBudget, 1) if call.kind == "model" else None
            if budget is not None and (
                known_cost_cny is None or known_cost_cny > budget.reserve_per_call_cny
            ):
                budget.status = "halted"
                budget.halt_reason = (
                    "unknown_model_cost"
                    if known_cost_cny is None
                    else "reservation_exceeded"
                )
                if known_cost_cny is not None:
                    call.pricing_error = "reservation_exceeded"
            cost = await session.get(PgCost, task_id, with_for_update=True)
            if known_cost_cny is not None:
                cost.known_cost_cny += known_cost_cny
            else:
                # A completed call without a verified price is still an
                # unknown expense; a numeric zero would be a false claim.
                cost.unknown_attempt_count += 1
            cost.updated_at = now
            return self._call_record(call)

    async def complete_call(
        self,
        task_id: str,
        token: int,
        call_id: str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        known_cost_cny: Decimal | None = None,
        safe_output_digest: str | None = None,
        provider_usage: ProviderUsage | None = None,
    ) -> CallRecord:
        return await self._end_call(
            task_id,
            token,
            call_id,
            "completed",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            known_cost_cny=known_cost_cny,
            safe_output_digest=safe_output_digest,
            provider_usage=provider_usage,
        )

    async def fail_call(
        self,
        task_id: str,
        token: int,
        call_id: str,
        *,
        failure_type: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        known_cost_cny: Decimal | None = None,
        provider_usage: ProviderUsage | None = None,
    ) -> CallRecord:
        return await self._end_call(
            task_id,
            token,
            call_id,
            "failed",
            failure_type=failure_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            known_cost_cny=known_cost_cny,
            provider_usage=provider_usage,
        )

    async def list_calls(self, owner_id: str, task_id: str) -> list[CallRecord] | None:
        async with self.sessions() as session:
            visible = await session.scalar(
                select(PgTask.id).where(
                    PgTask.id == task_id, PgTask.owner_id == owner_id
                )
            )
            if visible is None:
                return None
            calls = (
                await session.scalars(
                    select(PgCallAttempt)
                    .where(PgCallAttempt.task_id == task_id)
                    .order_by(PgCallAttempt.started_at, PgCallAttempt.id)
                )
            ).all()
            return [self._call_record(call) for call in calls]

    async def store_fact(
        self,
        task_id: str,
        token: int,
        *,
        subject: str,
        claim: str,
        official_source_url: str,
        retrieved_at: datetime,
        machine_admission_status: str,
        official_identity_basis: str | None = None,
        evidence_excerpt: str | None = None,
        evidence_locator: str | None = None,
        human_review_status: str | None = None,
        reviewed_at: datetime | None = None,
    ) -> str:
        async with self.sessions.begin() as session:
            await self._live(session, task_id, token)
            fact = PgFact(
                task_id=task_id,
                fencing_token=token,
                subject=subject,
                claim=claim,
                official_source_url=official_source_url,
                retrieved_at=retrieved_at,
                machine_admission_status=machine_admission_status,
                official_identity_basis=official_identity_basis,
                evidence_excerpt=evidence_excerpt,
                evidence_locator=evidence_locator,
                human_review_status=human_review_status,
                reviewed_at=reviewed_at,
            )
            session.add(fact)
            await session.flush()
            return fact.id

    async def list_facts(self, owner_id: str, task_id: str) -> list[FactRecord] | None:
        """Read machine/human evidence exactly as stored, within one owner's task."""

        async with self.sessions() as session:
            visible = await session.scalar(
                select(PgTask.id).where(
                    PgTask.id == task_id, PgTask.owner_id == owner_id
                )
            )
            if visible is None:
                return None
            facts = (
                await session.scalars(
                    select(PgFact)
                    .where(PgFact.task_id == task_id)
                    .order_by(PgFact.created_at, PgFact.id)
                )
            ).all()
            return [
                FactRecord(
                    **{
                        name: getattr(fact, name)
                        for name in FactRecord.__dataclass_fields__
                    }
                )
                for fact in facts
            ]

    async def get_cost(self, owner_id: str, task_id: str) -> CostRecord | None:
        async with self.sessions() as session:
            visible = await session.scalar(
                select(PgTask.id).where(
                    PgTask.id == task_id, PgTask.owner_id == owner_id
                )
            )
            if visible is None:
                return None
            cost = await session.get(PgCost, task_id)
            return CostRecord(
                cost.task_id,
                cost.known_cost_cny,
                cost.unknown_attempt_count,
                cost.updated_at,
            )
