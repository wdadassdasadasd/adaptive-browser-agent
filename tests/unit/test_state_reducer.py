from datetime import timedelta

import pytest

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchFact, ResearchState, Subgoal
from adaptive_agent.state_reducer import StateReducer


def event(
    state: ResearchState,
    event_type: str,
    payload: dict[str, object] | None = None,
    *,
    step: int | None = None,
    task_id: str | None = None,
) -> AgentEvent:
    return AgentEvent(
        event_type=event_type,
        task_id=task_id or state.task_id,
        step=state.step if step is None else step,
        payload={} if payload is None else payload,
    )


def subgoal() -> Subgoal:
    return Subgoal(
        id="s1",
        description="Find framework",
        completion_criteria="A cited page names the framework",
    )


def fact() -> ResearchFact:
    return ResearchFact(
        content="The project uses FastAPI",
        source_url="https://example.com/project",
        source_title="Project documentation",
    )


def test_queued_confirmation_returns_new_equal_state_without_mutating_input() -> None:
    state = ResearchState(goal="Research")
    before = state.model_dump()
    result = StateReducer().reduce(
        state, event(state, "task_queued", {"goal": "Research"})
    )
    assert result is not state
    assert result.model_dump() == before
    assert state.model_dump() == before


@pytest.mark.parametrize(
    "state_changes,payload",
    [
        ({"status": "running"}, {"goal": "Research"}),
        ({}, {"goal": "Different"}),
        ({}, {}),
        ({}, {"goal": "Research", "unexpected": True}),
        ({"step": 1}, {"goal": "Research"}),
        ({"facts": [fact()]}, {"goal": "Research"}),
    ],
)
def test_queued_confirmation_rejects_noninitial_or_wrong_goal(
    state_changes: dict[str, object], payload: dict[str, object]
) -> None:
    state = ResearchState(goal="Research", **state_changes)
    with pytest.raises(ValueError):
        StateReducer().reduce(state, event(state, "task_queued", payload))


def test_start_then_initialize_subgoals_once() -> None:
    state = ResearchState(goal="Research")
    started_event = event(state, "task_started")
    started = StateReducer().reduce(state, started_event)
    assert started.status == "running"
    assert started.updated_at == started_event.timestamp
    assert state.status == "queued"
    initialized = StateReducer().reduce(
        started,
        event(
            started,
            "subgoals_initialized",
            {"subgoals": [subgoal().model_dump(mode="json")]},
        ),
    )
    assert [item.id for item in initialized.subgoals] == ["s1"]
    assert started.subgoals == []
    with pytest.raises(ValueError):
        StateReducer().reduce(
            initialized,
            event(
                initialized,
                "subgoals_initialized",
                {"subgoals": [subgoal().model_dump(mode="json")]},
            ),
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"subgoals": []},
        {"subgoals": [{"id": "s1", "description": "No criteria"}]},
        {"subgoals": [subgoal().model_dump(mode="json")] * 2},
        {"subgoals": [subgoal().model_dump(mode="json")], "extra": True},
    ],
)
def test_subgoal_initialization_rejects_invalid_payload(
    payload: dict[str, object],
) -> None:
    state = ResearchState(goal="Research", status="running")
    with pytest.raises(ValueError):
        StateReducer().reduce(state, event(state, "subgoals_initialized", payload))


def test_start_requires_queued_and_empty_payload() -> None:
    for state, payload in [
        (ResearchState(goal="Research", status="running"), {}),
        (ResearchState(goal="Research"), {"extra": True}),
    ]:
        with pytest.raises(ValueError):
            StateReducer().reduce(state, event(state, "task_started", payload))


def test_cancel_is_idempotent_only_before_terminal() -> None:
    state = ResearchState(goal="Research")
    cancelled = StateReducer().reduce(state, event(state, "cancel_requested"))
    again = StateReducer().reduce(cancelled, event(cancelled, "cancel_requested"))
    assert cancelled.cancellation_requested is True
    assert again.cancellation_requested is True
    assert state.cancellation_requested is False
    with pytest.raises(ValueError):
        StateReducer().reduce(state, event(state, "cancel_requested", {"x": 1}))


@pytest.mark.parametrize(
    "status,level,reason,with_fact",
    [
        ("completed", "full", "goal_satisfied", True),
        ("completed", "full", "target_count", True),
        ("partial", "partial", "max_steps", True),
        ("failed", "none", "technical_failure", False),
        ("cancelled", "none", "user_cancelled", False),
        ("cancelled", "partial", "user_cancelled", True),
    ],
)
def test_finish_applies_legal_terminal_combination(
    status: str, level: str, reason: str, with_fact: bool
) -> None:
    state = ResearchState(
        goal="Research",
        status="running",
        facts=[fact()] if with_fact else [],
    )
    finished = StateReducer().reduce(
        state,
        event(
            state,
            "task_finished",
            {"status": status, "completion_level": level, "stop_reason": reason},
        ),
    )
    assert (finished.status, finished.completion_level, finished.stop_reason) == (
        status,
        level,
        reason,
    )
    assert state.status == "running"
    with pytest.raises(ValueError):
        StateReducer().reduce(finished, event(finished, "cancel_requested"))


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "running", "completion_level": "none", "stop_reason": "x"},
        {
            "status": "completed",
            "completion_level": "partial",
            "stop_reason": "goal_satisfied",
        },
        {"status": "completed", "completion_level": "full", "stop_reason": "max_steps"},
        {"status": "partial", "completion_level": "none", "stop_reason": "max_steps"},
        {"status": "failed", "completion_level": "full", "stop_reason": "error"},
        {"status": "cancelled", "completion_level": "none", "stop_reason": "max_steps"},
        {"status": "failed", "completion_level": "none", "stop_reason": " "},
        {"status": "failed", "completion_level": "none"},
        {
            "status": "failed",
            "completion_level": "none",
            "stop_reason": "error",
            "extra": 1,
        },
    ],
)
def test_finish_rejects_invalid_combination_or_payload(
    payload: dict[str, object],
) -> None:
    state = ResearchState(goal="Research", status="running")
    with pytest.raises(ValueError):
        StateReducer().reduce(state, event(state, "task_finished", payload))


def test_partial_and_completed_require_facts_and_cancel_level_matches_facts() -> None:
    state = ResearchState(goal="Research", status="running")
    for status, level, reason in [
        ("completed", "full", "goal_satisfied"),
        ("partial", "partial", "max_steps"),
        ("cancelled", "partial", "user_cancelled"),
    ]:
        with pytest.raises(ValueError):
            StateReducer().reduce(
                state,
                event(
                    state,
                    "task_finished",
                    {
                        "status": status,
                        "completion_level": level,
                        "stop_reason": reason,
                    },
                ),
            )


@pytest.mark.parametrize(
    "event_type,payload",
    [
        ("task_queued", {"goal": "Research"}),
        ("task_started", {}),
        ("subgoals_initialized", {"subgoals": [subgoal().model_dump(mode="json")]}),
        ("cancel_requested", {}),
        (
            "task_finished",
            {"status": "failed", "completion_level": "none", "stop_reason": "error"},
        ),
        ("step_evaluated", {}),
    ],
)
def test_every_event_rejects_wrong_task_id(
    event_type: str, payload: dict[str, object]
) -> None:
    state = ResearchState(goal="Research")
    with pytest.raises(ValueError, match="task_id"):
        StateReducer().reduce(
            state, event(state, event_type, payload, task_id="other-task")
        )


def test_step_evaluated_rejects_nonconsecutive_step_and_overflow() -> None:
    state = ResearchState(goal="Research", status="running", max_steps=1)
    payload = {
        "decision": {
            "subgoal_id": "s1",
            "reasoning": "Inspect page",
            "tool": "browser",
            "action": "navigate",
            "expected_result": "Page visible",
        },
        "tool_result": {
            "tool": "browser",
            "action": "navigate",
            "success": True,
            "content": "Page visible",
            "error_type": "none",
        },
        "evaluation": {
            "success": True,
            "reason": "Page visible",
            "subgoal_completed": False,
            "should_replan": False,
            "facts": [],
            "error_type": "none",
        },
        "prompt_tokens": 10,
        "completion_tokens": 5,
    }
    with pytest.raises(ValueError, match="step"):
        StateReducer().reduce(state, event(state, "step_evaluated", payload, step=1))
    with pytest.raises(NotImplementedError, match="D2"):
        StateReducer().reduce(state, event(state, "step_evaluated", payload))
    assert state.step == 0
    full = ResearchState(goal="Research", status="running", step=1, max_steps=1)
    with pytest.raises(ValueError, match="max_steps"):
        StateReducer().reduce(full, event(full, "step_evaluated", payload))


@pytest.mark.parametrize(
    "changes",
    [
        {"decision": {}},
        {"tool_result": {}},
        {"evaluation": {}},
        {"prompt_tokens": -1},
        {"completion_tokens": -1},
        {"extra": True},
    ],
)
def test_step_evaluated_rejects_bad_payload(changes: dict[str, object]) -> None:
    state = ResearchState(goal="Research", status="running")
    payload = {
        "decision": {
            "subgoal_id": "s1",
            "reasoning": "Inspect page",
            "tool": "browser",
            "action": "navigate",
            "expected_result": "Page visible",
        },
        "tool_result": {
            "tool": "browser",
            "action": "navigate",
            "success": True,
            "content": "Page visible",
            "error_type": "none",
        },
        "evaluation": {
            "success": True,
            "reason": "Page visible",
            "facts": [],
        },
        "prompt_tokens": 10,
        "completion_tokens": 5,
    }
    payload.update(changes)
    with pytest.raises(ValueError):
        StateReducer().reduce(state, event(state, "step_evaluated", payload))


def test_nonstep_event_rejects_wrong_step_and_terminal_mutation() -> None:
    state = ResearchState(goal="Research")
    with pytest.raises(ValueError, match="step"):
        StateReducer().reduce(state, event(state, "task_started", step=1))
    finished = StateReducer().reduce(
        state,
        event(
            state,
            "task_finished",
            {"status": "failed", "completion_level": "none", "stop_reason": "error"},
        ),
    )
    assert finished.updated_at.utcoffset() == timedelta(0)
    with pytest.raises(ValueError, match="terminal"):
        StateReducer().reduce(
            finished,
            event(
                finished,
                "task_finished",
                {
                    "status": "failed",
                    "completion_level": "none",
                    "stop_reason": "error",
                },
            ),
        )
