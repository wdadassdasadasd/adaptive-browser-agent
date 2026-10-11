"""Bounded, useful planner context over long task history."""

import json

import pytest

from adaptive_agent.context_manager import ContextManager
from adaptive_agent.events import AgentEvent
from adaptive_agent.state import ResearchFact, ResearchState, Subgoal


@pytest.mark.asyncio
async def test_context_bounds_observation_and_keeps_recent_sources() -> None:
    state = ResearchState(
        goal="Research FastAPI releases",
        status="running",
        step=8,
        subgoals=[
            Subgoal(
                id="s1",
                description="Find releases",
                completion_criteria="Sourced release",
            )
        ],
        current_subgoal_id="s1",
        facts=[
            ResearchFact(
                content="FastAPI is a framework",
                source_url="https://fastapi.tiangolo.com/",
                source_title="FastAPI",
                evidence="framework",
            )
        ],
        visited_urls=[f"https://example.com/{i}" for i in range(1000)],
    )
    traces = [
        AgentEvent(
            task_id=state.task_id,
            event_type="step_evaluated",
            step=i,
            message=f"trace-{i} " + "x" * 2000,
        )
        for i in range(8)
    ]
    rendered = await ContextManager(5).build(
        state, {"title": "Documentation", "text": "y" * 50000}, traces
    )
    assert len(rendered) <= 12000
    assert "s1" in rendered and "https://fastapi.tiangolo.com/" in rendered
    assert "trace-3" in rendered and "trace-7" in rendered
    assert "trace-2" not in rendered
    assert "TRUNCATED" in rendered


@pytest.mark.asyncio
async def test_context_rejects_unbounded_trace_configuration() -> None:
    with pytest.raises(ValueError):
        ContextManager(6)


@pytest.mark.asyncio
async def test_huge_current_subgoal_does_not_hide_latest_observation_and_trace() -> (
    None
):
    state = ResearchState(
        goal="Research",
        status="running",
        current_subgoal_id="s1",
        subgoals=[
            Subgoal(id="s1", description="d" * 20000, completion_criteria="c" * 20000)
        ],
    )
    trace = AgentEvent(
        task_id=state.task_id,
        event_type="step_evaluated",
        message="recent failure clue",
    )
    rendered = await ContextManager(5).build(
        state, {"title": "Current source page"}, [trace]
    )
    assert len(rendered) <= 12000
    assert "Current source page" in rendered
    assert "recent failure clue" in rendered
    assert "TRUNCATED" in rendered


@pytest.mark.asyncio
async def test_context_retains_completed_goal_and_older_failed_action_clues() -> None:
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="done",
                description="Find docs",
                completion_criteria="Source",
                status="completed",
            ),
            Subgoal(
                id="next", description="Find release", completion_criteria="Source"
            ),
        ],
    )
    failure = AgentEvent(
        task_id=state.task_id,
        event_type="step_evaluated",
        payload={
            "decision": {
                "tool": "github",
                "action": "search_repositories",
                "target": "old query",
            },
            "tool_result": {
                "success": False,
                "error_type": "technical",
                "error_message": "rate limited",
            },
        },
    )
    later = [
        AgentEvent(task_id=state.task_id, event_type="step_evaluated", message=str(i))
        for i in range(6)
    ]
    rendered = await ContextManager(5).build(state, {}, [failure, *later])
    assert '"completed_subgoals": ["done"]' in rendered
    assert "old query" in rendered and "rate limited" in rendered


@pytest.mark.asyncio
async def test_oversized_fact_sources_keep_current_observation_and_trace() -> None:
    state = ResearchState(
        goal="Research",
        status="running",
        facts=[
            ResearchFact(
                content="sourced fact",
                source_url="https://example.com/" + "x" * 1900 + str(index),
                source_title="Example",
            )
            for index in range(8)
        ],
    )
    trace = AgentEvent(
        task_id=state.task_id, event_type="step_evaluated", message="LATEST TRACE"
    )

    rendered = await ContextManager(5).build(
        state, {"title": "LATEST OBSERVATION"}, [trace]
    )

    parsed = json.loads(rendered)
    assert len(rendered) <= 12000
    assert parsed["observation"]["title"] == "LATEST OBSERVATION"
    assert parsed["recent_traces"][-1]["message"] == "LATEST TRACE"
    assert parsed["truncation"].startswith("TRUNCATED")


@pytest.mark.asyncio
async def test_browser_dom_and_deep_events_survive_observation_bounding() -> None:
    class DOMState:
        def llm_representation(self) -> str:
            return "x" * 9000 + "[42] Search releases"

    observation = {
        "dom_state": DOMState(),
        "tabs": [],
        "screenshot": None,
        "page_info": None,
        "pixels_above": 0,
        "pixels_below": 0,
        "pending_network_requests": [],
        "pagination_buttons": [],
        "url": "https://fastapi.tiangolo.com/",
        "title": "FastAPI docs",
        "recent_events": "Clicked search and loaded releases",
    }

    rendered = await ContextManager(5).build(
        ResearchState(goal="Research", status="running"), observation, []
    )

    parsed = json.loads(rendered)
    assert parsed["observation"]["url"] == "https://fastapi.tiangolo.com/"
    assert parsed["observation"]["title"] == "FastAPI docs"
    assert "[42] Search releases" in parsed["observation"]["dom_state"]
    assert "Clicked search" in parsed["observation"]["recent_events"]


@pytest.mark.asyncio
async def test_recent_trace_keeps_action_and_outcome_without_message() -> None:
    state = ResearchState(goal="Research", status="running")
    trace = AgentEvent(
        task_id=state.task_id,
        event_type="step_evaluated",
        payload={
            "decision": {"tool": "browser", "action": "click", "target": "Search"},
            "tool_result": {"success": True, "error_type": "none"},
            "evaluation": {"success": True, "subgoal_completed": False},
        },
    )

    rendered = await ContextManager(5).build(state, {"title": "Results"}, [trace])

    summary = json.loads(rendered)["recent_traces"][0]
    assert summary["decision"]["action"] == "click"
    assert summary["decision"]["target"] == "Search"
    assert summary["tool_result"]["success"] is True
    assert summary["evaluation"]["subgoal_completed"] is False


@pytest.mark.asyncio
async def test_dom_target_survives_when_other_observation_text_is_large() -> None:
    class DOMState:
        def llm_representation(self) -> str:
            return "d" * 4000 + "[42] Search releases"

    state = ResearchState(goal="Research", status="running")
    traces = [
        AgentEvent(
            task_id=state.task_id,
            event_type="step_evaluated",
            message="m" * 250,
            payload={
                "decision": {"tool": "browser", "action": "click", "target": "Search"},
                "tool_result": {"success": True, "error_type": "none"},
                "evaluation": {"success": True, "subgoal_completed": False},
            },
        )
        for _ in range(5)
    ]

    rendered = await ContextManager(5).build(
        state,
        {
            "dom_state": DOMState(),
            "text": "t" * 3000,
            "content": "c" * 3000,
            "recent_events": "Loaded releases",
        },
        traces,
    )

    parsed = json.loads(rendered)
    assert len(rendered) <= 12000
    assert "[42] Search releases" in parsed["observation"]["dom_state"]
    assert parsed["observation"]["recent_events"] == "Loaded releases"
    assert len(parsed["recent_traces"]) == 5
