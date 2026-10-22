"""D2 component chain with real provider parsing and a simulated observation."""

import httpx
import pytest

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.llm.deepseek import DeepSeekClient
from adaptive_research.agent.planner import PlannerService
from adaptive_research.agent.state import ResearchFact, ResearchState
from adaptive_research.agent.state_reducer import StateReducer


@pytest.mark.asyncio
async def test_research_goal_produces_one_sourced_step_and_closes_http_client() -> None:
    goal = "Find official FastAPI docs and verify ASGI support"
    source = "https://fastapi.tiangolo.com/"
    replies = [
        (
            '{"subgoals":[{"id":"official-docs","description":"Verify ASGI support",'
            '"completion_criteria":"A cited official page states FastAPI supports ASGI"}]}'
        ),
        (
            '{"subgoal_id":"official-docs","reasoning":"Open the official documentation",'
            '"tool":"browser","action":"navigate","target":"https://fastapi.tiangolo.com/",'
            '"expected_result":"The official page provides evidence about ASGI support"}'
        ),
    ]
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": replies[len(requests) - 1]}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 5},
            },
        )

    provider = DeepSeekClient("test-key", transport=httpx.MockTransport(handler))
    try:
        planner = PlannerService(provider)
        reducer = StateReducer()
        state = ResearchState(goal=goal)
        state = reducer.reduce(
            state, AgentEvent(task_id=state.task_id, event_type="task_started")
        )
        subgoals = await planner.initialize(goal)
        state = reducer.reduce(
            state,
            AgentEvent(
                task_id=state.task_id,
                event_type="subgoals_initialized",
                payload={
                    "subgoals": [item.model_dump(mode="json") for item in subgoals]
                },
            ),
        )
        decision = await planner.next_step(
            state,
            {"url": "https://example.com/search", "title": "Search results"},
        )
        fact = ResearchFact(
            subgoal_id="official-docs",
            content="The official docs state FastAPI supports ASGI",
            source_url=source,
            source_title="FastAPI documentation",
        )
        state = reducer.reduce(
            state,
            AgentEvent(
                task_id=state.task_id,
                event_type="step_evaluated",
                step=state.step,
                payload={
                    "decision": decision.model_dump(mode="json"),
                    "tool_result": {
                        "tool": "browser",
                        "action": "navigate",
                        "success": True,
                        "content": "FastAPI supports ASGI",
                        "source_url": source,
                        "error_type": "none",
                    },
                    "evaluation": {
                        "success": True,
                        "reason": "Official source supports the goal",
                        "subgoal_completed": True,
                        "facts": [fact.model_dump(mode="json")],
                        "error_type": "none",
                    },
                    "prompt_tokens": 11,
                    "completion_tokens": 5,
                },
            ),
        )
        assert decision.action == "navigate"
        assert decision.target == source
        assert state.step == 1
        assert state.subgoals[0].status == "completed"
        assert state.facts == [fact]
        assert state.visited_urls == [source]
        assert (state.prompt_tokens, state.completion_tokens) == (11, 5)
        assert len(requests) == 2
    finally:
        await provider.aclose()
    assert provider.client.is_closed
