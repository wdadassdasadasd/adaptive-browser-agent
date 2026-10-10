"""Pure D1 state transitions; evaluated-step aggregation is assigned to D2."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import (
    EvaluationErrorType,
    EvaluationResult,
    NonEmptyText,
    PlanDecision,
    ResearchReport,
    ResearchState,
    ResearchStatus,
    SourceUrl,
    Subgoal,
)

TERMINAL_STATUSES = {
    ResearchStatus.COMPLETED,
    ResearchStatus.PARTIAL,
    ResearchStatus.FAILED,
    ResearchStatus.CANCELLED,
}


class _ToolResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: Literal["browser", "github"]
    action: NonEmptyText
    success: bool
    content: str
    source_url: SourceUrl | None = None
    error_type: EvaluationErrorType
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class _StepEvaluatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: PlanDecision
    tool_result: _ToolResultPayload
    evaluation: EvaluationResult
    prompt_tokens: int = Field(ge=0, strict=True)
    completion_tokens: int = Field(ge=0, strict=True)


class StateReducer:
    """Apply D1 lifecycle events without mutating the input snapshot."""

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
            self._expect_keys(event.payload, {"subgoals"})
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
            return self._next_state(
                state, subgoals=subgoals, updated_at=event.timestamp
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
                {"report"},
            )
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
            return self._next_state(
                state,
                status=status,
                completion_level=level,
                stop_reason=reason,
                updated_at=event.timestamp,
            )

        if event.event_type == "step_evaluated":
            if state.status != ResearchStatus.RUNNING:
                raise ValueError("step_evaluated requires running state")
            if state.step >= state.max_steps:
                raise ValueError("step_evaluated exceeds max_steps")
            _StepEvaluatedPayload.model_validate(event.payload)
            raise NotImplementedError(
                "D2 must aggregate step_evaluated facts, usage, progress, and steps"
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
