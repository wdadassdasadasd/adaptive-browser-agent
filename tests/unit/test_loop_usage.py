"""Provider usage outside an action still belongs to the task budget."""

from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchState, Subgoal
from adaptive_agent.state_reducer import StateReducer


def test_initialization_and_terminal_report_usage_are_recorded_once() -> None:
    reducer = StateReducer()
    state = ResearchState(goal="Research FastAPI")
    state = reducer.reduce(
        state, AgentEvent(task_id=state.task_id, event_type="task_started")
    )
    state = reducer.reduce(
        state,
        AgentEvent(
            task_id=state.task_id,
            event_type="subgoals_initialized",
            payload={
                "subgoals": [
                    Subgoal(
                        id="s1",
                        description="Find FastAPI",
                        completion_criteria="Sourced description",
                    ).model_dump(mode="json")
                ],
                "prompt_tokens": 11,
                "completion_tokens": 3,
            },
        ),
    )
    assert (state.prompt_tokens, state.completion_tokens) == (11, 3)
    event = AgentEvent(
        task_id=state.task_id,
        event_type="task_finished",
        payload={
            "status": "failed",
            "completion_level": "none",
            "stop_reason": "execution_error",
            "prompt_tokens": 7,
            "completion_tokens": 2,
        },
    )

    finished = reducer.reduce(state, event)

    assert (finished.prompt_tokens, finished.completion_tokens) == (18, 5)
    assert finished.status == "failed"
