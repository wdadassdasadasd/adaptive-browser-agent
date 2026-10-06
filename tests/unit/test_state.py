from datetime import UTC

import pytest
from pydantic import ValidationError

from adaptive_agent.state import (
    EvaluationResult,
    PlanDecision,
    ResearchFact,
    ResearchReport,
    ResearchState,
)
from benchmark.metrics import BenchmarkMetrics


def test_research_state_contains_only_durable_fields() -> None:
    state = ResearchState(goal="Research the project")

    assert state.goal == "Research the project"
    assert state.step == 0
    assert state.max_steps == 30
    assert state.subgoals == []
    assert state.facts == []
    assert state.visited_urls == []
    assert state.search_history == []
    assert state.prompt_tokens == 0
    assert state.completion_tokens == 0
    assert state.cancellation_requested is False
    assert state.created_at.tzinfo is UTC

    with pytest.raises(ValidationError):
        ResearchState(goal="Research", runtime_task=object())


def test_plan_decision_requires_declared_contract() -> None:
    decision = PlanDecision(
        subgoal_id="subgoal-1",
        reasoning="Need the project page",
        tool="browser",
        action="navigate",
        target="https://example.com",
        element_index=None,
        value=None,
        expected_result="The project page is visible",
    )

    assert decision.action == "navigate"

    with pytest.raises(ValidationError):
        PlanDecision(
            subgoal_id="subgoal-1",
            reasoning="Missing expected result",
            tool="browser",
            action="navigate",
        )

    with pytest.raises(ValidationError):
        PlanDecision(
            subgoal_id="subgoal-1",
            reasoning="Unsupported tool",
            tool="shell",
            action="run",
            expected_result="Command completed",
        )


def test_evaluation_error_type_is_closed() -> None:
    result = EvaluationResult(
        success=True, reason="Observed expected content", error_type="none"
    )
    assert result.error_type == "none"

    with pytest.raises(ValidationError):
        EvaluationResult(success=False, reason="Unknown", error_type="unexpected")


def test_facts_and_reports_require_traceable_sources() -> None:
    fact = ResearchFact(
        content="The project uses FastAPI.",
        source_url="https://example.com/project",
        source_title="Project documentation",
    )
    result = EvaluationResult(
        success=True,
        reason="Observed expected content",
        new_facts=[fact],
    )
    report = ResearchReport(
        task_id="task-1",
        goal="Research the project",
        title="Project research",
        summary="The project uses FastAPI.",
        comparison="No alternative was requested.",
        recommendation="Review the cited documentation.",
        sources=[fact.source_url],
        markdown="# Research report",
    )

    assert result.new_facts == [fact]
    assert report.markdown.startswith("#")

    with pytest.raises(ValidationError):
        ResearchFact(content="Untraceable fact")


def test_benchmark_metrics_cover_v1_measurements() -> None:
    metrics = BenchmarkMetrics(
        success=True,
        steps=3,
        duration_seconds=1.5,
        duplicate_urls=1,
        prompt_tokens=120,
        completion_tokens=40,
        result_coverage=0.75,
    )

    assert metrics.result_coverage == 0.75
