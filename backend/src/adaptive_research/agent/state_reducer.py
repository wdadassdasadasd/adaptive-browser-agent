"""Pure transitions from validated AgentEvents to serializable research state."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.normalization import normalize_query as _normalized_query
from adaptive_research.agent.normalization import normalize_url as _normalized_url
from adaptive_research.agent.state import (
    EvaluationErrorType,
    EvaluationResult,
    PlanDecision,
    ResearchReport,
    ResearchState,
    ResearchStatus,
    Subgoal,
    SubgoalStatus,
    ToolResult,
)

TERMINAL_STATUSES = {
    ResearchStatus.COMPLETED,
    ResearchStatus.PARTIAL,
    ResearchStatus.FAILED,
    ResearchStatus.CANCELLED,
}


class _StepEvaluatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: PlanDecision
    tool_result: ToolResult
    evaluation: EvaluationResult
    prompt_tokens: int = Field(ge=0, strict=True)
    completion_tokens: int = Field(ge=0, strict=True)


class StateReducer:
    """Apply validated events without mutating the input snapshot."""

    def reduce(self, state: ResearchState, event: AgentEvent) -> ResearchState:
        if event.task_id != state.task_id:
            raise ValueError("event task_id does not match state")
        if state.status in TERMINAL_STATUSES:
            raise ValueError("terminal state cannot be modified")
        if event.step != state.step:
            raise ValueError("event step must equal current state step")

        if event.event_type == "task_queued":
            self._expect_keys(event.payload, {"goal"})
            if (
                state.status != ResearchStatus.QUEUED
                or state.step != 0
                or state.subgoals
                or state.facts
                or state.visited_urls
                or state.search_history
                or state.current_subgoal_id is not None
                or state.prompt_tokens
                or state.completion_tokens
                or state.consecutive_no_progress_replans
                or state.cancellation_requested
                or state.stop_reason is not None
                or state.completion_level != "none"
                or event.payload["goal"] != state.goal
            ):
                raise ValueError(
                    "task_queued requires the matching initial queued state"
                )
            return state.model_copy(deep=True)

        if event.event_type == "task_started":
            self._expect_keys(event.payload, set())
            if state.status != ResearchStatus.QUEUED:
                raise ValueError("task_started requires queued state")
            return self._next_state(
                state, status=ResearchStatus.RUNNING, updated_at=event.timestamp
            )

        if event.event_type == "subgoals_initialized":
            self._expect_keys(
                event.payload,
                {"subgoals"},
                {"prompt_tokens", "completion_tokens"},
            )
            usage = self._usage(event.payload)
            if (
                state.status != ResearchStatus.RUNNING
                or state.step != 0
                or state.subgoals
            ):
                raise ValueError("subgoals can only be initialized once before steps")
            raw_subgoals = event.payload["subgoals"]
            if not isinstance(raw_subgoals, list) or not raw_subgoals:
                raise ValueError("subgoals must be a nonempty list")
            subgoals = [Subgoal.model_validate(item) for item in raw_subgoals]
            if len({item.id for item in subgoals}) != len(subgoals):
                raise ValueError("subgoal IDs must be unique")
            if any(item.status != SubgoalStatus.PENDING for item in subgoals):
                raise ValueError("initial subgoals must be pending")
            return self._next_state(
                state,
                subgoals=subgoals,
                prompt_tokens=state.prompt_tokens + usage[0],
                completion_tokens=state.completion_tokens + usage[1],
                updated_at=event.timestamp,
            )

        if event.event_type == "cancel_requested":
            self._expect_keys(event.payload, set())
            return self._next_state(
                state, cancellation_requested=True, updated_at=event.timestamp
            )

        if event.event_type == "task_finished":
            self._expect_keys(
                event.payload,
                {"status", "completion_level", "stop_reason"},
                {"report", "prompt_tokens", "completion_tokens", "budget_preflight"},
            )
            if "budget_preflight" in event.payload:
                diagnostic = event.payload["budget_preflight"]
                if (
                    not isinstance(diagnostic, dict)
                    or set(diagnostic)
                    != {
                        "request_kind",
                        "remaining_tokens",
                        "prompt_bound",
                        "output_allowance",
                        "provider_request_started",
                    }
                    or diagnostic["request_kind"] not in {"structured", "plain"}
                    or type(diagnostic["remaining_tokens"]) is not int
                    or diagnostic["remaining_tokens"] < 0
                    or type(diagnostic["prompt_bound"]) is not int
                    or diagnostic["prompt_bound"] < 0
                    or type(diagnostic["output_allowance"]) is not int
                    or diagnostic["output_allowance"]
                    != diagnostic["remaining_tokens"] - diagnostic["prompt_bound"]
                    or diagnostic["provider_request_started"] is not False
                ):
                    raise ValueError("invalid budget preflight diagnostic")
            usage = self._usage(event.payload)
            status = ResearchStatus(event.payload["status"])
            level = event.payload["completion_level"]
            reason = event.payload["stop_reason"]
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("task_finished requires a nonempty stop_reason")
            if "report" in event.payload and event.payload["report"] is not None:
                report = ResearchReport.model_validate(event.payload["report"])
                if report.task_id != state.task_id or report.goal != state.goal:
                    raise ValueError("terminal report must match the task")
            self._validate_terminal(state, status, level, reason)
            subgoals = [item.model_copy(deep=True) for item in state.subgoals]
            if status != ResearchStatus.COMPLETED:
                for item in subgoals:
                    if item.status != SubgoalStatus.COMPLETED:
                        item.status = SubgoalStatus.FAILED
                        item.failure_reason = reason
            return self._next_state(
                state,
                status=status,
                completion_level=level,
                stop_reason=reason,
                subgoals=subgoals,
                prompt_tokens=state.prompt_tokens + usage[0],
                completion_tokens=state.completion_tokens + usage[1],
                updated_at=event.timestamp,
            )

        if event.event_type == "step_evaluated":
            if state.status != ResearchStatus.RUNNING:
                raise ValueError("step_evaluated requires running state")
            if state.step >= state.max_steps:
                raise ValueError("step_evaluated exceeds max_steps")
            payload = _StepEvaluatedPayload.model_validate(event.payload)
            decision = payload.decision
            result = payload.tool_result
            evaluation = payload.evaluation
            selected = next(
                (item for item in state.subgoals if item.id == decision.subgoal_id),
                None,
            )
            if selected is None or selected.status in {
                SubgoalStatus.COMPLETED,
                SubgoalStatus.FAILED,
            }:
                raise ValueError("decision requires an existing unfinished subgoal")
            if result.tool != decision.tool or result.action != decision.action:
                raise ValueError("tool result action must match decision")
            if evaluation.success and not result.success:
                raise ValueError(
                    "successful evaluation requires successful tool result"
                )
            if evaluation.facts and (not result.success or not evaluation.success):
                raise ValueError("facts require successful tool evaluation")

            observed_url = (
                _normalized_url(result.source_url) if result.source_url else None
            )
            facts = list(state.facts)
            fact_keys = {
                (_normalized_url(item.source_url), _normalized_query(item.content))
                for item in facts
            }
            fact_ids = {
                item.id: (
                    _normalized_url(item.source_url),
                    _normalized_query(item.content),
                )
                for item in facts
            }
            for fact in evaluation.facts:
                if (
                    observed_url is None
                    or _normalized_url(fact.source_url) != observed_url
                ):
                    raise ValueError("fact source must match an observed tool source")
                if fact.subgoal_id not in {None, decision.subgoal_id}:
                    raise ValueError("fact subgoal must match selected subgoal")
                key = (
                    _normalized_url(fact.source_url),
                    _normalized_query(fact.content),
                )
                if fact.id in fact_ids and fact_ids[fact.id] != key:
                    raise ValueError("fact ID already identifies different evidence")
                if key not in fact_keys:
                    facts.append(fact)
                    fact_keys.add(key)
                    fact_ids[fact.id] = key

            subgoals = [item.model_copy(deep=True) for item in state.subgoals]
            for item in subgoals:
                if item.id == decision.subgoal_id:
                    item.status = (
                        SubgoalStatus.COMPLETED
                        if evaluation.subgoal_completed
                        else SubgoalStatus.IN_PROGRESS
                    )
            visited = list(
                dict.fromkeys(_normalized_url(url) for url in state.visited_urls)
            )
            if result.success and observed_url and observed_url not in visited:
                visited.append(observed_url)
            searches = list(
                dict.fromkeys(
                    _normalized_query(query) for query in state.search_history
                )
            )
            if (
                decision.tool == "github"
                and decision.action == "search_repositories"
                and decision.target
                and result.error_type != EvaluationErrorType.TECHNICAL
            ):
                query = _normalized_query(decision.target)
                if query and query not in searches:
                    searches.append(query)

            progress = len(facts) > len(state.facts) or (
                evaluation.subgoal_completed
                and selected.status != SubgoalStatus.COMPLETED
            )
            no_progress = (
                0
                if progress
                else state.consecutive_no_progress_replans
                + int(evaluation.should_replan)
            )
            return self._next_state(
                state,
                step=state.step + 1,
                subgoals=subgoals,
                facts=facts,
                visited_urls=visited,
                search_history=searches,
                current_subgoal_id=decision.subgoal_id,
                prompt_tokens=state.prompt_tokens + payload.prompt_tokens,
                completion_tokens=state.completion_tokens + payload.completion_tokens,
                consecutive_no_progress_replans=no_progress,
                updated_at=event.timestamp,
            )

        raise ValueError("unsupported event type")

    @staticmethod
    def _expect_keys(
        payload: dict[str, Any], required: set[str], optional: set[str] | None = None
    ) -> None:
        keys = set(payload)
        if not required <= keys or keys - required - (optional or set()):
            raise ValueError("invalid event payload fields")

    @staticmethod
    def _usage(payload: dict[str, Any]) -> tuple[int, int]:
        prompt = payload.get("prompt_tokens", 0)
        completion = payload.get("completion_tokens", 0)
        if any(type(value) is not int or value < 0 for value in (prompt, completion)):
            raise ValueError("usage counters must be nonnegative integers")
        return prompt, completion

    @staticmethod
    def _validate_terminal(
        state: ResearchState, status: ResearchStatus, level: object, reason: str
    ) -> None:
        if status not in TERMINAL_STATUSES:
            raise ValueError("task_finished requires terminal status")
        if status == ResearchStatus.COMPLETED:
            if (
                level != "full"
                or reason not in {"goal_satisfied", "target_count"}
                or not state.facts
            ):
                raise ValueError("completed requires full level, reason, and a fact")
        elif status == ResearchStatus.PARTIAL:
            if (
                level != "partial"
                or not state.facts
                or reason in {"goal_satisfied", "target_count", "user_cancelled"}
            ):
                raise ValueError(
                    "partial requires recorded facts and a limiting reason"
                )
        elif status == ResearchStatus.FAILED:
            if level != "none" or reason in {
                "goal_satisfied",
                "target_count",
                "user_cancelled",
            }:
                raise ValueError("failed requires none and a failure reason")
        elif reason != "user_cancelled" or level != (
            "partial" if state.facts else "none"
        ):
            raise ValueError("cancelled requires user_cancelled and fact-based level")

    @staticmethod
    def _next_state(state: ResearchState, **changes: Any) -> ResearchState:
        return ResearchState.model_validate({**state.model_dump(), **changes})
