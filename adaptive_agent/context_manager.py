"""Bounded prompt-context assembly boundary."""

from collections.abc import Sequence

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchState


class ContextManager:
    def __init__(self, recent_trace_count: int) -> None:
        self.recent_trace_count = recent_trace_count

    async def build(
        self, state: ResearchState, recent_traces: Sequence[AgentEvent]
    ) -> str:
        """Build bounded context without storing complete traces in ResearchState."""

        raise NotImplementedError(
            "TODO(V1): build planner/evaluator context from state and recent traces"
        )
