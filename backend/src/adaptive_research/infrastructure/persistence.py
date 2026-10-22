"""Transactional SQLite boundary for research tasks and Agent events."""

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.normalization import normalize_query, normalize_url
from adaptive_research.agent.reporter import ReporterService
from adaptive_research.agent.state import (
    EvaluationResult,
    PlanDecision,
    ResearchFact,
    ResearchReport,
    ResearchState,
    Subgoal,
    SubgoalStatus,
    utc_now,
)
from adaptive_research.infrastructure.db.models import (
    AgentTraceModel,
    ResearchFactModel,
    ResearchStepModel,
    ResearchTaskModel,
)

TERMINAL = {"completed", "partial", "failed", "cancelled"}
MAX_TRACE_BYTES = 64_000


class PersistenceService:
    def __init__(self, session: AsyncSession, secrets: Iterable[str] = ()) -> None:
        self.session = session
        self.secrets = tuple(value for value in secrets if value)

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

    def _safe_event(self, event: AgentEvent) -> AgentEvent:
        safe = event.model_copy(
            update={
                "message": self._redact(event.message),
                "payload": self._redact(event.payload),
            }
        )
        encoded = json.dumps(safe.model_dump(mode="json"), ensure_ascii=False)
        # A terminal event carries the durable report. Rejecting it for size
        # would turn completed research into a reportless execution failure.
        if (
            event.event_type != "task_finished"
            and len(encoded.encode("utf-8")) > MAX_TRACE_BYTES
        ):
            raise ValueError("Agent trace exceeds the storage limit")
        return safe

    async def create_task(self, goal: str) -> ResearchTaskModel:
        task = ResearchTaskModel(goal=goal)
        async with self.session.begin():
            self.session.add(task)
            await self.session.flush()
            queued = AgentEvent(
                event_type="task_queued", task_id=task.id, payload={"goal": goal}
            )
            await self._save_trace(self._safe_event(queued))
        return task

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        if status != "running":
            raise ValueError("terminal status requires a task_finished event")
        async with self.session.begin():
            result = await self.session.execute(
                update(ResearchTaskModel)
                .where(
                    ResearchTaskModel.id == task_id,
                    ResearchTaskModel.status == "queued",
                )
                .values(
                    status="running", error_message=error_message, updated_at=utc_now()
                )
            )
            if result.rowcount != 1:
                raise ValueError("task is not queued")

    async def save_step(
        self,
        task_id: str,
        step: int,
        decision: PlanDecision,
        evaluation: EvaluationResult | None,
    ) -> ResearchStepModel:
        row = ResearchStepModel(
            task_id=task_id,
            step=step,
            decision=self._redact(decision.model_dump(mode="json")),
            evaluation=self._redact(evaluation.model_dump(mode="json"))
            if evaluation
            else None,
        )
        async with self.session.begin():
            self.session.add(row)
            await self.session.flush()
        return row

    async def save_fact(self, task_id: str, fact: ResearchFact) -> ResearchFactModel:
        row = self._fact_row(task_id, fact)
        key = (normalize_url(row.source_url), normalize_query(row.content))
        async with self.session.begin():
            for existing in await self.get_task_facts(task_id):
                existing_key = (
                    normalize_url(existing.source_url),
                    normalize_query(existing.content),
                )
                if existing.id == row.id and existing_key != key:
                    raise ValueError("fact ID already identifies different evidence")
                if existing_key == key:
                    return existing
            self.session.add(row)
            await self.session.flush()
        return row

    def _fact_row(self, task_id: str, fact: ResearchFact) -> ResearchFactModel:
        return ResearchFactModel(
            id=fact.id,
            task_id=task_id,
            subgoal_id=fact.subgoal_id,
            content=self._redact(fact.content),
            source_url=self._redact(fact.source_url),
            source_title=self._redact(fact.source_title),
            subject=self._redact(fact.subject),
            subject_kind=fact.subject_kind,
            evidence=self._redact(fact.evidence),
            confidence=fact.confidence,
            created_at=fact.created_at,
        )

    async def _save_trace(self, event: AgentEvent) -> AgentTraceModel:
        row = AgentTraceModel(
            task_id=event.task_id,
            step=event.step,
            event_type=event.event_type,
            message=event.message,
            payload={
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                **event.payload,
            },
            created_at=event.timestamp,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_trace(self, event: AgentEvent) -> AgentTraceModel:
        if event.event_type in {"task_queued", "task_started", "task_finished"}:
            raise ValueError("status-changing traces require record_event")
        async with self.session.begin():
            row = await self._save_trace(self._safe_event(event))
        return row

    async def record_event(self, event: AgentEvent) -> AgentTraceModel | None:
        """Commit an event and its derived rows, or commit none of them."""

        event = self._safe_event(event)
        async with self.session.begin():
            if event.event_type == "task_started":
                changed = await self.session.execute(
                    update(ResearchTaskModel)
                    .where(
                        ResearchTaskModel.id == event.task_id,
                        ResearchTaskModel.status == "queued",
                    )
                    .values(status="running", updated_at=event.timestamp)
                )
                if changed.rowcount != 1:
                    return None
            elif event.event_type == "task_finished":
                status = event.payload["status"]
                if status not in TERMINAL:
                    raise ValueError("invalid terminal status")
                changed = await self.session.execute(
                    update(ResearchTaskModel)
                    .where(
                        ResearchTaskModel.id == event.task_id,
                        ResearchTaskModel.status.in_(("queued", "running")),
                    )
                    .values(status=status, updated_at=event.timestamp)
                )
                if changed.rowcount != 1:
                    return None
            else:
                current_status = await self.session.scalar(
                    select(ResearchTaskModel.status).where(
                        ResearchTaskModel.id == event.task_id
                    )
                )
                if current_status != "running":
                    return None
            if event.event_type == "step_evaluated":
                payload = event.payload
                self.session.add(
                    ResearchStepModel(
                        task_id=event.task_id,
                        step=event.step,
                        decision=payload["decision"],
                        evaluation=payload["evaluation"],
                        created_at=event.timestamp,
                    )
                )
                existing = await self.get_task_facts(event.task_id)
                by_id = {
                    item.id: (
                        normalize_url(item.source_url),
                        normalize_query(item.content),
                    )
                    for item in existing
                }
                known = set(by_id.values())
                for raw in payload["evaluation"].get("facts", []):
                    fact = ResearchFact.model_validate(raw)
                    key = (
                        normalize_url(fact.source_url),
                        normalize_query(fact.content),
                    )
                    if fact.id in by_id and by_id[fact.id] != key:
                        raise ValueError(
                            "fact ID already identifies different evidence"
                        )
                    if key not in known:
                        self.session.add(self._fact_row(event.task_id, fact))
                        known.add(key)
                        by_id[fact.id] = key
            row = await self._save_trace(event)
        return row

    async def cancel_queued(
        self, task_id: str, event: AgentEvent
    ) -> AgentTraceModel | None:
        event = self._safe_event(event)
        async with self.session.begin():
            changed = await self.session.execute(
                update(ResearchTaskModel)
                .where(
                    ResearchTaskModel.id == task_id,
                    ResearchTaskModel.status == "queued",
                )
                .values(status="cancelled", updated_at=event.timestamp)
            )
            if changed.rowcount != 1:
                return None
            row = await self._save_trace(event)
        return row

    async def get_task(self, task_id: str) -> ResearchTaskModel | None:
        return await self.session.get(ResearchTaskModel, task_id)

    async def list_tasks(self) -> list[ResearchTaskModel]:
        return list(
            (
                await self.session.scalars(
                    select(ResearchTaskModel)
                    .order_by(ResearchTaskModel.created_at.desc())
                    .limit(50)
                )
            ).all()
        )

    async def get_task_steps(self, task_id: str) -> list[ResearchStepModel]:
        return list(
            (
                await self.session.scalars(
                    select(ResearchStepModel)
                    .where(ResearchStepModel.task_id == task_id)
                    .order_by(ResearchStepModel.step, ResearchStepModel.id)
                )
            ).all()
        )

    async def get_task_facts(self, task_id: str) -> list[ResearchFactModel]:
        return list(
            (
                await self.session.scalars(
                    select(ResearchFactModel)
                    .where(ResearchFactModel.task_id == task_id)
                    .order_by(ResearchFactModel.created_at, ResearchFactModel.id)
                )
            ).all()
        )

    async def get_task_traces(
        self, task_id: str, after_id: int = 0
    ) -> list[AgentTraceModel]:
        return list(
            (
                await self.session.scalars(
                    select(AgentTraceModel)
                    .where(
                        AgentTraceModel.task_id == task_id,
                        AgentTraceModel.id > after_id,
                    )
                    .order_by(AgentTraceModel.id)
                )
            ).all()
        )

    async def trace_id_for_event(self, task_id: str, event_id: str) -> int | None:
        for trace in await self.get_task_traces(task_id):
            if trace.payload.get("event_id") == event_id:
                return trace.id
        return None

    @staticmethod
    def trace_event(trace: AgentTraceModel) -> AgentEvent:
        data = dict(trace.payload)
        event_id = data.pop("event_id")
        timestamp = datetime.fromisoformat(data.pop("timestamp"))
        return AgentEvent(
            event_id=event_id,
            task_id=trace.task_id,
            event_type=trace.event_type,
            step=trace.step,
            timestamp=timestamp,
            message=trace.message,
            payload=data,
        )

    async def report_for_task(self, task_id: str) -> ResearchReport | None:
        for trace in reversed(await self.get_task_traces(task_id)):
            if trace.event_type == "task_finished":
                raw = trace.payload.get("report")
                return ResearchReport.model_validate(raw) if raw else None
        return None

    async def finalize_unfinished(self) -> int:
        task_ids = list(
            (
                await self.session.scalars(
                    select(ResearchTaskModel.id).where(
                        ResearchTaskModel.status.in_(("queued", "running"))
                    )
                )
            ).all()
        )
        count = 0
        for task_id in task_ids:
            task = await self.get_task(task_id)
            if task is None:
                continue
            facts = await self.get_task_facts(task_id)
            traces = await self.get_task_traces(task_id)
            status = "partial" if facts else "failed"
            level = "partial" if facts else "none"
            subgoals: dict[str, Subgoal] = {}
            for trace in traces:
                if trace.event_type == "subgoals_initialized":
                    subgoals = {
                        item.id: item
                        for item in (
                            Subgoal.model_validate(raw)
                            for raw in trace.payload.get("subgoals", [])
                        )
                    }
                elif trace.event_type == "step_evaluated":
                    selected_id = trace.payload.get("decision", {}).get("subgoal_id")
                    selected = subgoals.get(selected_id)
                    if selected is not None:
                        selected.status = (
                            SubgoalStatus.COMPLETED
                            if trace.payload.get("evaluation", {}).get(
                                "subgoal_completed"
                            )
                            else SubgoalStatus.IN_PROGRESS
                        )
            state = ResearchState(
                task_id=task_id,
                goal=task.goal,
                status=status,
                completion_level=level,
                stop_reason="server_restart",
                subgoals=list(subgoals.values()),
                facts=[
                    ResearchFact(
                        id=row.id,
                        subgoal_id=row.subgoal_id,
                        content=row.content,
                        source_url=row.source_url,
                        source_title=row.source_title,
                        subject=row.subject,
                        subject_kind=row.subject_kind,
                        evidence=row.evidence,
                        confidence=row.confidence,
                        created_at=row.created_at.replace(tzinfo=utc_now().tzinfo)
                        if row.created_at.tzinfo is None
                        else row.created_at,
                    )
                    for row in facts
                ],
            )
            report = await ReporterService().generate(state)
            event = AgentEvent(
                task_id=task_id,
                event_type="task_finished",
                step=max((trace.step for trace in traces), default=0),
                payload={
                    "status": status,
                    "completion_level": level,
                    "stop_reason": "server_restart",
                    "report": report.model_dump(mode="json"),
                },
            )
            await self.session.rollback()
            count += int(await self.record_event(event) is not None)
        return count
