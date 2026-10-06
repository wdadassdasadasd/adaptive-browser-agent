"""Lightweight persistence service contract."""

from sqlalchemy.ext.asyncio import AsyncSession

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import EvaluationResult, PlanDecision, ResearchFact
from backend.db.models import (
    AgentTraceModel,
    ResearchFactModel,
    ResearchStepModel,
    ResearchTaskModel,
)


class PersistenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_task(self, goal: str) -> ResearchTaskModel:
        raise NotImplementedError("TODO(V1): persist a research task")

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        raise NotImplementedError("TODO(V1): update research task status")

    async def save_step(
        self,
        task_id: str,
        step: int,
        decision: PlanDecision,
        evaluation: EvaluationResult | None,
    ) -> ResearchStepModel:
        raise NotImplementedError("TODO(V1): persist one research step")

    async def save_fact(self, task_id: str, fact: ResearchFact) -> ResearchFactModel:
        raise NotImplementedError("TODO(V1): persist one research fact")

    async def save_trace(self, event: AgentEvent) -> AgentTraceModel:
        raise NotImplementedError("TODO(V1): persist one agent trace")

    async def get_task(self, task_id: str) -> ResearchTaskModel | None:
        raise NotImplementedError("TODO(V1): load a research task")

    async def list_tasks(self) -> list[ResearchTaskModel]:
        raise NotImplementedError("TODO(V1): list research tasks")

    async def get_task_steps(self, task_id: str) -> list[ResearchStepModel]:
        raise NotImplementedError("TODO(V1): list research steps")

    async def get_task_facts(self, task_id: str) -> list[ResearchFactModel]:
        raise NotImplementedError("TODO(V1): list research facts")

    async def get_task_traces(self, task_id: str) -> list[AgentTraceModel]:
        raise NotImplementedError("TODO(V1): list agent traces")
