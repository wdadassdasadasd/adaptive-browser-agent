"""Planner decisions must use the current state and observation."""

import pytest
from pydantic import ValidationError

from adaptive_research.agent.context_manager import ContextManager
from adaptive_research.agent.llm.base import LLMError, StructuredCompletion
from adaptive_research.agent.planner import InitialSubgoals, PlannerService
from adaptive_research.agent.state import ResearchState, Subgoal


class FakeLLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.invalid_action = False
        self.decision_overrides: dict[str, object] = {}

    async def complete_structured(self, prompt: str, schema: type):
        self.prompts.append(prompt)
        if schema.__name__ == "InitialSubgoals":
            return StructuredCompletion(
                schema.model_validate(
                    {
                        "subgoals": [
                            {
                                "id": "s1",
                                "description": "Find documentation",
                                "completion_criteria": "A sourced official page names the project",
                            },
                        ]
                    }
                ),
                2,
                1,
            )
        if self.invalid_action:
            action = "delete_files"
        elif '"step": 0' in prompt and '"title": "Search results"' in prompt:
            action = "navigate"
        else:
            action = "extract"
        decision = {
            "subgoal_id": "s1",
            "reasoning": "Inspect current evidence",
            "tool": "browser",
            "action": action,
            "target": "https://example.com/docs"
            if action == "navigate"
            else "What does the page say?",
            "expected_result": "A sourced answer",
        }
        decision.update(self.decision_overrides)
        return StructuredCompletion(
            schema.model_validate(decision),
            3,
            2,
        )


@pytest.mark.asyncio
async def test_browser_only_prompt_leaves_github_mistake_for_router_replan() -> None:
    llm = FakeLLM()
    llm.decision_overrides = {
        "tool": "github",
        "action": "search_repositories",
        "target": "fastapi",
    }
    planner = PlannerService(llm, browser_only=True)
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(id="s1", description="Find docs", completion_criteria="source")
        ],
    )
    decision = await planner.next_step(state, {})
    assert decision.tool == "github"
    assert "Only browser actions" in llm.prompts[-1]


@pytest.mark.asyncio
async def test_initialize_returns_observable_subgoals_without_mutating_state() -> None:
    llm = FakeLLM()
    subgoals = await PlannerService(llm).initialize("Find project docs")
    assert len(subgoals) == 1
    assert (
        subgoals[0].completion_criteria == "A sourced official page names the project"
    )
    assert "Find project docs" in llm.prompts[0]


def test_initialize_rejects_more_than_three_subgoals() -> None:
    with pytest.raises(ValidationError, match="at most 3 items"):
        InitialSubgoals.model_validate(
            {
                "subgoals": [
                    {
                        "id": f"s{index}",
                        "description": f"Evidence {index}",
                        "completion_criteria": "Official source cited",
                    }
                    for index in range(4)
                ]
            }
        )


@pytest.mark.asyncio
async def test_initialize_requests_tool_agnostic_sourced_criteria() -> None:
    llm = FakeLLM()

    await PlannerService(llm).initialize("Find a release and two changes")

    prompt = llm.prompts[0]
    assert "1-3 high-level evidence subgoals" in prompt
    assert "not a required tool or rendered page" in prompt
    assert "all requested output fields" in prompt


@pytest.mark.asyncio
async def test_next_step_changes_when_state_or_observation_changes() -> None:
    llm = FakeLLM()
    planner = PlannerService(llm)
    initial = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find docs",
                completion_criteria="A sourced official page names the project",
            )
        ],
    )
    first = await planner.next_step(
        initial, {"title": "Search results", "url": "https://example.com"}
    )
    assert first.action == "navigate"
    changed_observation = await planner.next_step(
        initial, {"title": "Documentation", "url": "https://example.com/docs"}
    )
    assert changed_observation.action == "extract"
    advanced = initial.model_copy(update={"step": 1})
    second = await planner.next_step(
        advanced, {"title": "Search results", "url": "https://example.com"}
    )
    assert second.action == "extract"
    assert first != second
    assert '"step": 1' in llm.prompts[-1]
    assert '"title": "Search results"' in llm.prompts[-1]


@pytest.mark.asyncio
async def test_planner_uses_bounded_context_without_reexpanding_history() -> None:
    llm = FakeLLM()
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1", description="Find docs", completion_criteria="Sourced page"
            )
        ],
        search_history=["old clue " + "z" * 50000],
    )
    observation = {"title": "Search results", "text": "q" * 50000}
    context = await ContextManager(5).build(state, observation, [])
    await PlannerService(llm).next_step(state, observation, context)
    assert len(llm.prompts[-1]) < 13000
    assert "TRUNCATED" in llm.prompts[-1]


@pytest.mark.asyncio
async def test_supplied_history_keeps_current_state_and_observation() -> None:
    llm = FakeLLM()
    state = ResearchState(
        goal="Research",
        status="running",
        step=2,
        subgoals=[
            Subgoal(
                id="s1", description="Find docs", completion_criteria="Sourced page"
            )
        ],
    )

    await PlannerService(llm).next_step(
        state, {"title": "Current documentation"}, "Earlier GitHub search failed"
    )

    prompt = llm.prompts[-1]
    assert '"step": 2' in prompt
    assert '"title": "Current documentation"' in prompt
    assert "Earlier GitHub search failed" in prompt
    assert len(prompt) < 13000


@pytest.mark.asyncio
async def test_next_step_rejects_invalid_model_action_after_one_repair() -> None:
    llm = FakeLLM()
    llm.invalid_action = True
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find docs",
                completion_criteria="A sourced official page names the project",
            )
        ],
    )
    with pytest.raises(ValueError, match="action"):
        await PlannerService(llm).next_step(state, {"title": "Documentation"})
    assert len(llm.prompts) == 2


@pytest.mark.asyncio
async def test_next_step_explains_real_tool_actions_and_target_shapes() -> None:
    llm = FakeLLM()
    state = ResearchState(
        goal="Find two browser-automation projects",
        status="running",
        subgoals=[
            Subgoal(id="s1", description="Find projects", completion_criteria="sources")
        ],
    )

    await PlannerService(llm).next_step(state, {})

    prompt = llm.prompts[-1]
    assert "browser has no search action" in prompt
    assert "navigate(target: public HTTP(S) URL)" in prompt
    assert "search_repositories(target: query)" in prompt
    assert "get_repository(target: owner/repo)" in prompt
    assert "list_releases(target: owner/repo)" in prompt


@pytest.mark.asyncio
async def test_next_step_repairs_one_invalid_action_contract() -> None:
    class RepairingLLM:
        def __init__(self) -> None:
            self.prompts: list[str] = []

        async def complete_structured(self, prompt: str, schema: type):
            self.prompts.append(prompt)
            decision = {
                "subgoal_id": "s1",
                "reasoning": "Read the current official page",
                "tool": "browser",
                "action": "extract",
                "target": "What are the route declarations?",
                "element_index": 1 if len(self.prompts) == 1 else None,
                "expected_result": "Official route examples",
            }
            return StructuredCompletion(schema.model_validate(decision), 3, 2)

    llm = RepairingLLM()
    state = ResearchState(
        goal="Compare official API docs",
        status="running",
        subgoals=[
            Subgoal(id="s1", description="Read docs", completion_criteria="source")
        ],
    )

    decision = await PlannerService(llm).next_step(state, {"title": "Official docs"})

    assert decision.action == "extract" and decision.element_index is None
    assert len(llm.prompts) == 2
    assert "extract action requires only a question" in llm.prompts[1]


@pytest.mark.asyncio
async def test_local_budget_rejection_retries_once_with_current_page_and_failures() -> (
    None
):
    class BudgetLLM:
        def __init__(self) -> None:
            self.prompts: list[str] = []

        async def complete_structured(self, prompt: str, schema: type):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                raise LLMError(
                    "remaining token budget is too small",
                    kind="budget",
                    budget_preflight={
                        "remaining_tokens": 8123,
                        "prompt_bound": 15171,
                        "output_allowance": -7048,
                        "provider_request_started": False,
                    },
                )
            return StructuredCompletion(
                schema.model_validate(
                    {
                        "subgoal_id": "s1",
                        "reasoning": "Extract the current source",
                        "tool": "browser",
                        "action": "extract",
                        "target": "What does the official page say?",
                        "expected_result": "A sourced answer",
                    }
                ),
                3,
                2,
            )

    llm = BudgetLLM()
    state = ResearchState(
        goal="Check FastAPI release information",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find release information",
                completion_criteria="Official source and version",
            )
        ],
    )
    history = (
        '{"failed_actions":[{"tool":"github","action":"list_releases",'
        '"error_type":"technical"}],"noise":"' + "x" * 9000 + '"}'
    )
    decision = await PlannerService(llm).next_step(
        state,
        {
            "url": "https://fastapi.tiangolo.com/release-notes/",
            "title": "Release notes",
        },
        history,
    )

    assert decision.action == "extract"
    assert len(llm.prompts) == 2
    assert len(llm.prompts[1].encode("utf-8")) < len(llm.prompts[0].encode("utf-8"))
    assert "Find release information" in llm.prompts[1]
    assert "https://fastapi.tiangolo.com/release-notes/" in llm.prompts[1]
    assert "Official source and version" in llm.prompts[1]
    assert "list_releases" in llm.prompts[1]


@pytest.mark.asyncio
async def test_budget_retry_stops_after_second_local_rejection() -> None:
    class RejectingLLM:
        def __init__(self) -> None:
            self.calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            raise LLMError(
                "remaining token budget is too small",
                kind="budget",
                budget_preflight={"provider_request_started": False},
            )

    llm = RejectingLLM()
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(id="s1", description="Find docs", completion_criteria="source")
        ],
    )
    with pytest.raises(LLMError, match="remaining token budget"):
        await PlannerService(llm).next_step(
            state, {"url": "https://example.com/docs"}, "x" * 9000
        )
    assert llm.calls == 2


@pytest.mark.asyncio
async def test_budget_failure_after_provider_start_is_not_retried() -> None:
    class StartedLLM:
        def __init__(self) -> None:
            self.calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            raise LLMError(
                "provider outcome unknown",
                kind="budget",
                budget_preflight={"provider_request_started": True},
            )

    llm = StartedLLM()
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(id="s1", description="Find docs", completion_criteria="source")
        ],
    )
    with pytest.raises(LLMError, match="provider outcome unknown"):
        await PlannerService(llm).next_step(state, {}, "x" * 9000)
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_next_step_rejects_missing_or_completed_subgoal() -> None:
    llm = FakeLLM()
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find docs",
                completion_criteria="A sourced official page names the project",
                status="completed",
            )
        ],
    )
    with pytest.raises(ValueError, match="subgoal"):
        await PlannerService(llm).next_step(state, {"title": "Documentation"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"action": "go_back", "target": "https://example.com/other"},
        {"action": "go_back", "target": None, "value": "ignored"},
        {"action": "click", "target": "Search", "element_index": 0},
        {
            "tool": "github",
            "action": "get_repository",
            "target": "https://example.com/x",
        },
        {"tool": "github", "action": "list_releases", "target": "owner/repo/extra"},
        {
            "tool": "github",
            "action": "get_repository",
            "target": "fastapi/fastapi",
            "value": "unused",
        },
        {
            "tool": "browser",
            "action": "navigate",
            "target": "https://example.com/",
            "value": "unused",
        },
        {"action": "click", "target": "Search", "value": "unused"},
        {"action": "extract", "target": "Question", "element_index": 1},
        {"action": "wait", "target": "unexpected", "value": "1"},
        {"action": "scroll", "target": "down", "value": "unused"},
    ],
)
async def test_next_step_rejects_invalid_action_parameters(
    overrides: dict[str, object],
) -> None:
    llm = FakeLLM()
    llm.decision_overrides = overrides
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find docs",
                completion_criteria="A sourced official page names the project",
            )
        ],
    )
    with pytest.raises(ValueError, match="action|target"):
        await PlannerService(llm).next_step(state, {"title": "Documentation"})


@pytest.mark.asyncio
async def test_next_step_accepts_repository_identifier_for_github_action() -> None:
    llm = FakeLLM()
    llm.decision_overrides = {
        "tool": "github",
        "action": "get_repository",
        "target": "fastapi/fastapi",
    }
    state = ResearchState(
        goal="Research",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find repository",
                completion_criteria="A sourced repository entry identifies the project",
            )
        ],
    )
    decision = await PlannerService(llm).next_step(
        state, {"title": "Repository search"}
    )
    assert (decision.tool, decision.action, decision.target) == (
        "github",
        "get_repository",
        "fastapi/fastapi",
    )
