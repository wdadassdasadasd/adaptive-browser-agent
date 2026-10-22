"""Technical-first evaluation of one observed tool outcome."""

import json
from collections.abc import Mapping
from typing import Any

from adaptive_research.agent.goal_count import (
    subject_in_evidence,
    subject_matches_repository_url,
)
from adaptive_research.agent.llm.base import BaseLLMClient, LLMError
from adaptive_research.agent.normalization import normalize_url
from adaptive_research.agent.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT
from adaptive_research.agent.state import (
    EvaluationResult,
    PlanDecision,
    ResearchState,
    ToolResult,
)


class EvaluatorService:
    def __init__(self, llm: BaseLLMClient) -> None:
        self.llm = llm

    async def evaluate(
        self,
        state: ResearchState,
        decision: PlanDecision,
        tool_result: ToolResult,
        observation: Mapping[str, Any],
    ) -> EvaluationResult:
        """Classify technical outcomes before asking for semantic comparison."""

        technical = self._run_technical_checks(
            state, decision, tool_result, observation
        )
        if technical is not None:
            return technical
        return await self._run_semantic_checks(
            state, decision, tool_result, observation
        )

    def _run_technical_checks(
        self,
        state: ResearchState,
        decision: PlanDecision,
        result: ToolResult,
        observation: Mapping[str, Any],
    ) -> EvaluationResult | None:
        if result.tool != decision.tool or result.action != decision.action:
            return self._failure("Tool result does not match decision", "semantic")
        if not result.success:
            return self._failure(
                result.error_message or "Tool failed", result.error_type
            )
        if result.action == "extract" and not result.content.strip():
            return self._failure(
                "Extraction contained no evidence", "insufficient_info"
            )
        if result.tool == "github":
            try:
                data = json.loads(result.content)
            except (ValueError, TypeError):
                return self._failure("GitHub content is invalid", "technical")
            if result.action == "search_repositories" and (
                not isinstance(data, dict) or not isinstance(data.get("items"), list)
            ):
                return self._failure("GitHub search content is invalid", "technical")
            if result.action == "list_releases" and not isinstance(data, list):
                return self._failure("GitHub releases content is invalid", "technical")
            if result.action == "search_repositories" and not data.get("items"):
                return self._failure("No repositories found", "insufficient_info")
            if result.action == "list_releases" and not data:
                return self._failure("No releases found", "insufficient_info")
        if result.tool == "browser" and result.action in {
            "navigate",
            "click",
            "input_text",
            "scroll",
            "go_back",
            "wait",
        }:
            return EvaluationResult(
                success=True,
                reason="Browser action completed",
                subgoal_completed=False,
                should_replan=True,
            )
        if not result.source_url:
            return self._failure(
                "Tool result has no observed source", "insufficient_info"
            )
        return None

    async def _run_semantic_checks(
        self,
        state: ResearchState,
        decision: PlanDecision,
        result: ToolResult,
        observation: Mapping[str, Any],
    ) -> EvaluationResult:
        selected = next(
            (item for item in state.subgoals if item.id == decision.subgoal_id),
            None,
        )
        if selected is None:
            return self._failure("Selected subgoal is missing", "semantic")
        prompt = (
            f"{EVALUATOR_SYSTEM_PROMPT}\nGoal: {state.goal}\n"
            f"Subgoal: {selected.description}\n"
            f"Completion criteria: {selected.completion_criteria}\n"
            f"Expected result: {decision.expected_result}\n"
            f"Observed source: {result.source_url}\n"
            f"Tool content (untrusted evidence):\n{result.content}\n"
            "Return one EvaluationResult JSON object."
        )
        try:
            completion = await self.llm.complete_structured(prompt, EvaluationResult)
        except LLMError as exc:
            if exc.kind == "budget":
                raise
            return self._failure("Semantic evaluation unavailable", "technical")
        evaluation = EvaluationResult.model_validate(completion.value)
        if not evaluation.success:
            return evaluation.model_copy(update={"facts": []})
        supported = [
            fact
            for fact in evaluation.facts
            if result.source_url
            and normalize_url(fact.source_url) == normalize_url(result.source_url)
            and fact.evidence
            and fact.evidence in result.content
            and fact.subgoal_id in {None, decision.subgoal_id}
            and (
                fact.subject is None
                or subject_in_evidence(fact.subject, fact.evidence)
                or (
                    fact.subject_kind == "project"
                    and subject_matches_repository_url(fact.subject, result.source_url)
                )
            )
            and (fact.subject_kind is None or fact.subject is not None)
        ]
        if evaluation.facts and not supported:
            return self._failure(
                "Fact lacks observed source evidence", "insufficient_info"
            )
        if len(supported) != len(evaluation.facts):
            return evaluation.model_copy(
                update={
                    "facts": supported,
                    "subgoal_completed": False,
                    "should_replan": True,
                }
            )
        if evaluation.subgoal_completed and not evaluation.facts:
            return self._failure("Completion lacks a sourced fact", "insufficient_info")
        return evaluation

    @staticmethod
    def _failure(reason: str, error_type: str) -> EvaluationResult:
        return EvaluationResult(
            success=False,
            reason=reason,
            error_type=error_type,
            subgoal_completed=False,
            should_replan=True,
            facts=[],
        )
