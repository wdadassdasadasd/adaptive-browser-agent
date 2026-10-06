"""Single evaluation service for technical and semantic checks."""

from collections.abc import Mapping
from typing import Any

from adaptive_agent.state import EvaluationResult, PlanDecision, ResearchState


class EvaluatorService:
    async def evaluate(
        self,
        state: ResearchState,
        decision: PlanDecision,
        observation: Mapping[str, Any],
    ) -> EvaluationResult:
        """Evaluate one step without splitting evaluation into separate services."""

        raise NotImplementedError(
            "TODO(V1): run deterministic technical checks followed by LLM semantic checks"
        )

    def _run_technical_checks(
        self,
        state: ResearchState,
        decision: PlanDecision,
        observation: Mapping[str, Any],
    ) -> EvaluationResult | None:
        raise NotImplementedError(
            "TODO(V1): implement deterministic technical validation"
        )

    async def _run_semantic_checks(
        self,
        state: ResearchState,
        decision: PlanDecision,
        observation: Mapping[str, Any],
    ) -> EvaluationResult:
        raise NotImplementedError("TODO(V1): implement LLM semantic validation")
