"""Technical-first evaluation and observed-source fact admission."""

import pytest

from adaptive_agent.evaluator import EvaluatorService
from adaptive_agent.events import AgentEvent
from adaptive_agent.llm.base import LLMError, StructuredCompletion
from adaptive_agent.state import (
    EvaluationResult,
    PlanDecision,
    ResearchFact,
    ResearchState,
    Subgoal,
    ToolResult,
)
from adaptive_agent.state_reducer import StateReducer


def state() -> ResearchState:
    return ResearchState(
        goal="Find FastAPI release evidence",
        status="running",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find release",
                completion_criteria="Sourced version",
            )
        ],
    )


def decision(action: str = "extract") -> PlanDecision:
    return PlanDecision(
        subgoal_id="s1",
        reasoning="inspect",
        tool="browser",
        action=action,
        target="release",
        expected_result="Find a release version",
    )


def result(**changes: object) -> ToolResult:
    return ToolResult(
        tool="browser",
        action="extract",
        success=True,
        content="FastAPI version 1.0 released",
        source_url="https://fastapi.tiangolo.com/",
        **changes,
    )


class FakeLLM:
    def __init__(self, outcome: EvaluationResult) -> None:
        self.outcome = outcome
        self.prompts: list[str] = []

    async def complete_structured(
        self, prompt: str, schema: object
    ) -> StructuredCompletion:
        self.prompts.append(prompt)
        return StructuredCompletion(self.outcome, 10, 5)


@pytest.mark.asyncio
async def test_technical_failure_skips_semantic_model() -> None:
    llm = FakeLLM(EvaluationResult(success=True, reason="unused"))
    tool_result = ToolResult(
        tool="browser",
        action="extract",
        success=False,
        content="",
        error_type="technical",
        error_message="navigation failed",
    )
    actual = await EvaluatorService(llm).evaluate(state(), decision(), tool_result, {})
    assert (
        not actual.success and actual.error_type == "technical" and actual.should_replan
    )
    assert llm.prompts == []


@pytest.mark.asyncio
async def test_empty_extract_is_insufficient_without_semantic_model() -> None:
    llm = FakeLLM(EvaluationResult(success=True, reason="unused"))
    empty = ToolResult(
        tool="browser",
        action="extract",
        success=True,
        content="",
        source_url="https://fastapi.tiangolo.com/",
    )
    actual = await EvaluatorService(llm).evaluate(state(), decision(), empty, {})
    assert actual.error_type == "insufficient_info" and llm.prompts == []


@pytest.mark.asyncio
async def test_navigation_success_needs_no_semantic_model() -> None:
    llm = FakeLLM(
        EvaluationResult(
            success=False, reason="unused", should_replan=True, error_type="semantic"
        )
    )
    opened = ToolResult(
        tool="browser",
        action="navigate",
        success=True,
        content="Navigated",
        source_url="https://fastapi.tiangolo.com/",
    )
    actual = await EvaluatorService(llm).evaluate(
        state(), decision("navigate"), opened, {}
    )
    assert (
        actual.success and actual.error_type == "none" and not actual.subgoal_completed
    )
    assert llm.prompts == []


@pytest.mark.asyncio
async def test_semantic_failure_is_distinct_from_technical() -> None:
    llm = FakeLLM(
        EvaluationResult(
            success=False,
            reason="Goal mismatch",
            should_replan=True,
            error_type="semantic",
        )
    )
    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})
    assert actual.error_type == "semantic" and len(llm.prompts) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source,evidence",
    [
        ("https://example.com/", "FastAPI version 1.0"),
        ("https://fastapi.tiangolo.com/", "invented version 9.9"),
    ],
)
async def test_unobserved_or_unsupported_fact_is_rejected(
    source: str, evidence: str
) -> None:
    fact = ResearchFact(
        content="FastAPI version 1.0",
        source_url=source,
        source_title="FastAPI",
        evidence=evidence,
    )
    llm = FakeLLM(
        EvaluationResult(
            success=True, reason="Found it", subgoal_completed=True, facts=[fact]
        )
    )
    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})
    assert actual.error_type == "insufficient_info" and actual.facts == []


@pytest.mark.asyncio
async def test_supported_fact_can_complete_subgoal() -> None:
    fact = ResearchFact(
        content="FastAPI version 1.0",
        source_url="https://fastapi.tiangolo.com/",
        source_title="FastAPI",
        evidence="FastAPI version 1.0",
    )
    llm = FakeLLM(
        EvaluationResult(
            success=True, reason="Found it", subgoal_completed=True, facts=[fact]
        )
    )
    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})
    assert actual.success and actual.subgoal_completed and actual.facts == [fact]


@pytest.mark.asyncio
async def test_counted_subject_must_appear_in_observed_evidence() -> None:
    fact = ResearchFact(
        content="FastAPI version 1.0",
        source_url="https://fastapi.tiangolo.com/",
        source_title="FastAPI",
        evidence="FastAPI version 1.0",
        subject="Flask",
        subject_kind="project",
    )
    llm = FakeLLM(
        EvaluationResult(
            success=True, reason="Found it", subgoal_completed=True, facts=[fact]
        )
    )

    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})

    assert actual.error_type == "insufficient_info"
    assert actual.facts == []


@pytest.mark.asyncio
async def test_uncounted_subject_must_also_appear_in_observed_evidence() -> None:
    fact = ResearchFact(
        content="FastAPI version 1.0",
        source_url="https://fastapi.tiangolo.com/",
        source_title="FastAPI",
        evidence="FastAPI version 1.0",
        subject="Flask",
    )
    llm = FakeLLM(
        EvaluationResult(
            success=True, reason="Found it", subgoal_completed=True, facts=[fact]
        )
    )

    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})

    assert actual.error_type == "insufficient_info"
    assert actual.facts == []


@pytest.mark.asyncio
async def test_counted_subject_prefix_is_not_observed_name() -> None:
    fact = ResearchFact(
        content="FastAPI2 version 1.0",
        source_url="https://fastapi.tiangolo.com/",
        source_title="FastAPI",
        evidence="FastAPI2 version 1.0",
        subject="FastAPI",
        subject_kind="project",
    )
    llm = FakeLLM(
        EvaluationResult(
            success=True, reason="Found it", subgoal_completed=True, facts=[fact]
        )
    )

    actual = await EvaluatorService(llm).evaluate(state(), decision(), result(), {})

    assert actual.error_type == "insufficient_info"
    assert actual.facts == []


@pytest.mark.asyncio
async def test_empty_github_search_is_insufficient_without_model_call() -> None:
    llm = FakeLLM(EvaluationResult(success=True, reason="unused"))
    selected = PlanDecision(
        subgoal_id="s1",
        reasoning="search",
        tool="github",
        action="search_repositories",
        target="fastapi",
        expected_result="Find repository",
    )
    search = ToolResult(
        tool="github",
        action="search_repositories",
        success=True,
        content='{"total_count":0,"items":[]}',
        source_url="https://api.github.com/search/repositories?q=fastapi",
    )
    actual = await EvaluatorService(llm).evaluate(state(), selected, search, {})
    assert actual.error_type == "insufficient_info" and llm.prompts == []


@pytest.mark.asyncio
async def test_malformed_successful_github_payload_returns_technical_result() -> None:
    llm = FakeLLM(EvaluationResult(success=True, reason="unused"))
    selected = PlanDecision(
        subgoal_id="s1",
        reasoning="search",
        tool="github",
        action="search_repositories",
        target="fastapi",
        expected_result="Find repository",
    )
    malformed = ToolResult(
        tool="github",
        action="search_repositories",
        success=True,
        content="[]",
        source_url="https://api.github.com/search/repositories?q=fastapi",
    )
    actual = await EvaluatorService(llm).evaluate(state(), selected, malformed, {})
    assert actual.error_type == "technical" and llm.prompts == []


@pytest.mark.asyncio
async def test_failed_semantic_result_drops_facts_before_reducer() -> None:
    fact = ResearchFact(
        content="Partial claim",
        source_url="https://fastapi.tiangolo.com/",
        source_title="FastAPI",
        evidence="FastAPI version 1.0",
    )
    llm = FakeLLM(
        EvaluationResult(
            success=False,
            reason="More evidence needed",
            error_type="insufficient_info",
            should_replan=True,
            facts=[fact],
        )
    )
    current = state()
    selected = decision()
    tool_result = result()

    actual = await EvaluatorService(llm).evaluate(current, selected, tool_result, {})

    assert actual.facts == []
    event = AgentEvent(
        task_id=current.task_id,
        event_type="step_evaluated",
        payload={
            "decision": selected.model_dump(mode="json"),
            "tool_result": tool_result.model_dump(mode="json"),
            "evaluation": actual.model_dump(mode="json"),
            "prompt_tokens": 0,
            "completion_tokens": 0,
        },
    )
    assert StateReducer().reduce(current, event).step == 1


@pytest.mark.asyncio
async def test_semantic_prompt_includes_current_completion_criteria() -> None:
    current = state().model_copy(
        update={
            "subgoals": [
                Subgoal(
                    id="s1",
                    description="Compare two release versions",
                    completion_criteria="Two distinct versions have sourced dates",
                )
            ]
        }
    )
    llm = FakeLLM(EvaluationResult(success=True, reason="Observed release evidence"))

    await EvaluatorService(llm).evaluate(current, decision(), result(), {})

    assert "Compare two release versions" in llm.prompts[0]
    assert "Two distinct versions have sourced dates" in llm.prompts[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["invalid_response", "structured"])
async def test_malformed_provider_output_is_technical(kind: str) -> None:
    class FailingLLM:
        async def complete_structured(self, prompt: str, schema: object) -> None:
            raise LLMError("Invalid provider response", kind=kind)

    actual = await EvaluatorService(FailingLLM()).evaluate(
        state(), decision(), result(), {}
    )

    assert actual.error_type == "technical" and actual.facts == []
