"""DEC-T01 offline projections of the frozen r11 failure traces."""

import json
from pathlib import Path

import pytest

from adaptive_research.agent.context_manager import ContextManager
from adaptive_research.agent.llm.base import LLMError, StructuredCompletion
from adaptive_research.agent.planner import PlannerService
from adaptive_research.agent.state import ResearchFact, ResearchState, Subgoal

_ROOT = Path(__file__).resolve().parents[3]
_R11 = _ROOT / "data/evaluation/p02-pilot-r11-20261023"


def _state(*, fact: bool = False) -> ResearchState:
    return ResearchState(
        goal="Find official Python project evidence",
        status="running",
        current_subgoal_id="s1",
        subgoals=[
            Subgoal(
                id="s1",
                description="Extract the current official page",
                completion_criteria="Cite an official source and project fact",
            )
        ],
        facts=(
            [
                ResearchFact(
                    id="r11-fact-1",
                    content="Version is shown on the release page",
                    source_url="https://github.com/browser-use/browser-use/releases",
                    source_title="Releases",
                    evidence="Version 0.13.13",
                    subject="browser-use",
                )
            ]
            if fact
            else []
        ),
    )


def _decision(schema: type) -> StructuredCompletion:
    return StructuredCompletion(
        schema.model_validate(
            {
                "subgoal_id": "s1",
                "reasoning": "Read the current page",
                "tool": "browser",
                "action": "extract",
                "target": "What official evidence supports the subgoal?",
                "expected_result": "A sourced answer",
            }
        ),
        3,
        2,
    )


@pytest.mark.asyncio
async def test_b01_projection_guides_extraction_before_more_navigation() -> None:
    events = json.loads(
        (_R11 / "39d4a2d0-8729-5b97-be65-a87d0678a0f2/capture/events.json").read_text(
            encoding="utf-8"
        )
    )
    actions = [
        event["payload"]["decision"]["action"]
        for event in events
        if event["event_type"] == "step_evaluated"
    ]
    assert actions[-3:] == ["navigate", "navigate", "navigate"]
    assert events[-1]["payload"]["stop_reason"] == "no_progress"

    class CaptureLLM:
        prompt = ""

        async def complete_structured(self, prompt: str, schema: type):
            self.prompt = prompt
            return _decision(schema)

    llm = CaptureLLM()
    await PlannerService(llm).next_step(
        _state(), {"url": "https://example.org/project", "title": "Project docs"}
    )
    assert "extract its evidence before navigating away" in llm.prompt
    assert "https://example.org/project" in llm.prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", ["B02", "B03"])
async def test_r11_local_budget_preflight_gets_one_compact_retry(case_id: str) -> None:
    supplement = json.loads(
        (_R11 / "budget-preflight-supplement-20261023.json").read_text(encoding="utf-8")
    )
    preflight = next(
        attempt["budget_preflight_from_persisted_event"]
        for attempt in supplement["attempts"]
        if attempt["case_id"] == case_id
    )
    assert preflight["provider_request_started"] is False
    assert preflight["output_allowance"] < 0

    class BudgetLLM:
        def __init__(self) -> None:
            self.prompts: list[str] = []

        async def complete_structured(self, prompt: str, schema: type):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                raise LLMError(
                    "local budget preflight refused",
                    kind="budget",
                    budget_preflight=preflight,
                )
            return _decision(schema)

    llm = BudgetLLM()
    history = json.dumps(
        {
            "failed_actions": [
                {"tool": "github", "action": "list_releases", "error_type": "technical"}
            ],
            "noise": "x" * 9000,
        }
    )
    decision = await PlannerService(llm).next_step(
        _state(fact=True),
        {"url": "https://github.com/browser-use/browser-use/releases"},
        history,
    )
    assert decision.action == "extract"
    assert len(llm.prompts) == 2
    assert len(llm.prompts[1].encode("utf-8")) < len(llm.prompts[0].encode("utf-8"))
    for required in (
        "Extract the current official page",
        "https://github.com/browser-use/browser-use/releases",
        "list_releases",
        "r11-fact-1",
    ):
        assert required in llm.prompts[1]


@pytest.mark.asyncio
async def test_second_local_refusal_stops_after_one_retry() -> None:
    class RefusingLLM:
        calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            raise LLMError(
                "local budget preflight refused",
                kind="budget",
                budget_preflight={"provider_request_started": False},
            )

    llm = RefusingLLM()
    with pytest.raises(LLMError, match="budget preflight"):
        await PlannerService(llm).next_step(_state(), {}, "x" * 9000)
    assert llm.calls == 2


@pytest.mark.asyncio
async def test_invalid_compact_action_does_not_get_a_second_budget_retry() -> None:
    class InvalidThenRefusingLLM:
        calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            if self.calls != 2:
                raise LLMError(
                    "local budget preflight refused",
                    kind="budget",
                    budget_preflight={"provider_request_started": False},
                )
            return StructuredCompletion(
                schema.model_validate(
                    {
                        "subgoal_id": "s1",
                        "reasoning": "Wrong action",
                        "tool": "browser",
                        "action": "navigate",
                        "target": "not a public URL",
                        "expected_result": "Page",
                    }
                ),
                3,
                2,
            )

    llm = InvalidThenRefusingLLM()
    with pytest.raises(LLMError, match="budget preflight"):
        await PlannerService(llm).next_step(_state(), {}, "x" * 9000)
    assert llm.calls == 3


@pytest.mark.asyncio
async def test_provider_started_failure_is_never_retried() -> None:
    class StartedLLM:
        calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            raise LLMError(
                "provider result unknown",
                kind="budget",
                budget_preflight={"provider_request_started": True},
            )

    llm = StartedLLM()
    with pytest.raises(LLMError, match="provider result unknown"):
        await PlannerService(llm).next_step(_state(), {}, "x" * 9000)
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_preflight_flag_with_reported_usage_is_not_retried() -> None:
    class ChargedLLM:
        calls = 0

        async def complete_structured(self, prompt: str, schema: type):
            self.calls += 1
            raise LLMError(
                "budget refused after prior usage",
                prompt_tokens=10,
                completion_tokens=1,
                kind="budget",
                budget_preflight={"provider_request_started": False},
            )

    llm = ChargedLLM()
    with pytest.raises(LLMError, match="prior usage"):
        await PlannerService(llm).next_step(_state(), {}, "x" * 9000)
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_normal_context_keeps_fact_id_with_source() -> None:
    context = await ContextManager(5).build(
        _state(fact=True), {"text": "x" * 50000}, []
    )
    assert "r11-fact-1" in context
    assert "https://github.com/browser-use/browser-use/releases" in context
