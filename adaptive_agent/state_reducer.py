"""State transition boundary for evaluated research steps."""

from adaptive_agent.state import EvaluationResult, PlanDecision, ResearchState


class StateReducer:
    def reduce(
        self,
        state: ResearchState,
        decision: PlanDecision,
        evaluation: EvaluationResult,
    ) -> ResearchState:
        """Return the next immutable-style durable state snapshot."""

        raise NotImplementedError(
            "TODO(V1): apply evaluated step results to durable state"
        )
