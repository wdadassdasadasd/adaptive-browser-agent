"""D3 component chain; provider, GitHub network and browser are controlled."""

import httpx
import pytest

from adaptive_research.agent.context_manager import ContextManager
from adaptive_research.agent.evaluator import EvaluatorService
from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.llm.base import StructuredCompletion
from adaptive_research.agent.planner import PlannerService
from adaptive_research.agent.state import (
    EvaluationResult,
    PlanDecision,
    ResearchFact,
    ResearchState,
    Subgoal,
)
from adaptive_research.agent.state_reducer import StateReducer
from adaptive_research.agent.tools.github_tool import GitHubTool
from adaptive_research.agent.tools.router import ToolRouter


class FakeBrowser:
    async def execute(self, action: object) -> dict[str, object]:
        return {
            "success": True,
            "action": action.action,
            "content": "Navigated",
            "url": "https://fastapi.tiangolo.com/",
        }


class FakeLLM:
    async def complete_structured(self, prompt: str, schema: type):
        if schema is PlanDecision:
            tool = "github" if "GitHub results" in prompt else "browser"
            return StructuredCompletion(
                PlanDecision(
                    subgoal_id="s1",
                    reasoning="Use current observation",
                    tool=tool,
                    action="get_repository" if tool == "github" else "navigate",
                    target="fastapi/fastapi"
                    if tool == "github"
                    else "https://fastapi.tiangolo.com/",
                    expected_result="Find FastAPI project evidence",
                ),
                4,
                2,
            )
        assert schema is EvaluationResult
        return StructuredCompletion(
            EvaluationResult(
                success=True,
                reason="Observed project description",
                subgoal_completed=True,
                facts=[
                    ResearchFact(
                        content="FastAPI framework",
                        source_url="https://api.github.com/repos/fastapi/fastapi",
                        source_title="GitHub API",
                        evidence="FastAPI framework",
                    )
                ],
            ),
            6,
            3,
        )


@pytest.mark.asyncio
async def test_state_observation_drives_both_paths_and_sourced_reducer_step() -> None:
    state = ResearchState(
        goal="Research FastAPI",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find FastAPI",
                completion_criteria="Sourced description",
            )
        ],
    )
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"full_name": "fastapi/fastapi", "description": "FastAPI framework"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        router = ToolRouter(FakeBrowser(), GitHubTool(client=client))
        llm = FakeLLM()
        planner = PlannerService(llm)
        browser_observation = {"title": "Documentation"}
        browser_context = await ContextManager(5).build(state, browser_observation, [])
        browser_decision = await planner.next_step(
            state, browser_observation, browser_context
        )
        browser_result = await router.execute(browser_decision, state)
        assert browser_decision.action == "navigate" and browser_result.success

        github_observation = {"title": "GitHub results"}
        github_context = await ContextManager(5).build(state, github_observation, [])
        github_decision = await planner.next_step(
            state, github_observation, github_context
        )
        github_result = await router.execute(github_decision, state)
        evaluation = await EvaluatorService(llm).evaluate(
            state, github_decision, github_result, github_observation
        )
        event = AgentEvent(
            task_id=state.task_id,
            event_type="step_evaluated",
            step=0,
            payload={
                "decision": github_decision.model_dump(mode="json"),
                "tool_result": github_result.model_dump(mode="json"),
                "evaluation": evaluation.model_dump(mode="json"),
                "prompt_tokens": 10,
                "completion_tokens": 5,
            },
        )
        updated = StateReducer().reduce(state, event)
        assert github_decision.action == "get_repository" and github_result.success
        assert updated.step == 1 and updated.subgoals[0].status == "completed"
        assert (
            len(updated.facts) == 1 and updated.facts[0].content == "FastAPI framework"
        )
        assert len(requests) == 1 and requests[0].url.host == "api.github.com"
    assert client.is_closed
