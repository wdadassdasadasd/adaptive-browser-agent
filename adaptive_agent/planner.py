"""Planning service boundary."""

from adaptive_agent.state import PlanDecision, ResearchState


class PlannerService:
    async def initialize(self, goal: str) -> ResearchState:
        """Create the initial durable state for a research goal."""

        return ResearchState(goal=goal)

    async def next_step(self, state: ResearchState, context: str) -> PlanDecision:
        """Choose the next action from durable state and bounded context."""

        raise NotImplementedError("TODO(V1): implement LLM-backed next-step planning")
