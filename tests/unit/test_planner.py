"""Planner decisions must use the current state and observation."""

import pytest

from adaptive_agent.llm.base import StructuredCompletion
from adaptive_agent.planner import PlannerService
from adaptive_agent.state import ResearchState, Subgoal


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
async def test_initialize_returns_observable_subgoals_without_mutating_state() -> None:
    llm = FakeLLM()
    subgoals = await PlannerService(llm).initialize("Find project docs")
    assert len(subgoals) == 1
    assert (
        subgoals[0].completion_criteria == "A sourced official page names the project"
    )
    assert "Find project docs" in llm.prompts[0]


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
async def test_next_step_rejects_invalid_model_action_without_fallback() -> None:
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
    assert len(llm.prompts) == 1


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
