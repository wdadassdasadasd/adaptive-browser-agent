import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import (
    EvaluationResult,
    Finding,
    PlanDecision,
    ResearchFact,
    ResearchReport,
    ResearchState,
    Subgoal,
)
from adaptive_research.evaluation.legacy_v1.metrics import BenchmarkMetrics


def fact() -> ResearchFact:
    return ResearchFact(
        content="The project uses FastAPI.",
        source_url="https://example.com/project",
        source_title="Project documentation",
    )


def subgoal() -> Subgoal:
    return Subgoal(
        id="subgoal-1",
        description="Find project documentation",
        completion_criteria="A cited project page identifies the framework",
    )


def test_research_state_defaults_round_trip_and_isolates_lists() -> None:
    first = ResearchState(goal="Research the project")
    second = ResearchState(goal="Research another project")
    assert first.status == "queued"
    assert first.step == 0
    assert first.max_steps == 30
    assert first.completion_level == "none"
    assert first.stop_reason is None
    assert first.consecutive_no_progress_replans == 0
    assert first.created_at.utcoffset() == timedelta(0)
    first.facts.append(fact())
    first.subgoals.append(subgoal())
    first.visited_urls.append("https://example.com")
    first.search_history.append("framework")
    assert second.facts == []
    assert second.subgoals == []
    assert second.visited_urls == []
    assert second.search_history == []
    restored = ResearchState.model_validate_json(first.model_dump_json())
    assert restored == first
    assert json.loads(first.model_dump_json())["status"] == "queued"


@pytest.mark.parametrize(
    "changes",
    [
        {"goal": "  "},
        {"task_id": " "},
        {"step": -1},
        {"max_steps": 0},
        {"step": 31},
        {"prompt_tokens": -1},
        {"completion_tokens": -1},
        {"consecutive_no_progress_replans": -1},
        {"current_subgoal_id": "missing"},
        {"runtime_task": object()},
        {"status": "pending"},
        {"created_at": datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None)},
        {"updated_at": datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=8)))},
    ],
)
def test_research_state_rejects_invalid_data(changes: dict[str, object]) -> None:
    data = {"goal": "Research"}
    data.update(changes)
    with pytest.raises(ValidationError):
        ResearchState(**data)


def test_research_state_current_subgoal_must_exist() -> None:
    state = ResearchState(
        goal="Research", subgoals=[subgoal()], current_subgoal_id="subgoal-1"
    )
    assert state.current_subgoal_id == "subgoal-1"


@pytest.mark.parametrize(
    "changes",
    [
        {"description": "  "},
        {"completion_criteria": " "},
        {"failure_reason": " "},
        {"unexpected": True},
    ],
)
def test_subgoal_rejects_invalid_data(changes: dict[str, object]) -> None:
    data = {
        "id": "subgoal-1",
        "description": "Find page",
        "completion_criteria": "A cited page is found",
    }
    data.update(changes)
    with pytest.raises(ValidationError):
        Subgoal(**data)


def test_plan_decision_requires_declared_contract() -> None:
    decision = PlanDecision(
        subgoal_id="subgoal-1",
        reasoning="Need the project page",
        tool="browser",
        action="navigate",
        target="https://example.com",
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


@pytest.mark.parametrize(
    "changes",
    [
        {"success": True, "error_type": "technical"},
        {"success": False, "error_type": "none"},
        {"success": False, "error_type": "technical", "should_replan": False},
        {"success": False, "error_type": "semantic", "subgoal_completed": True},
        {"reason": " "},
        {"error_type": "unexpected"},
        {"new_facts": []},
    ],
)
def test_evaluation_rejects_invalid_combinations(changes: dict[str, object]) -> None:
    data = {"success": True, "reason": "Observed expected content"}
    data.update(changes)
    with pytest.raises(ValidationError):
        EvaluationResult(**data)


def test_facts_evaluation_and_report_use_approved_fields() -> None:
    sourced_fact = fact()
    result = EvaluationResult(
        success=True, reason="Observed expected content", facts=[sourced_fact]
    )
    finding = Finding(
        name="Framework",
        description="The project uses FastAPI.",
        attributes={"framework": "FastAPI"},
        source_urls=[sourced_fact.source_url],
        supporting_fact_ids=[sourced_fact.id],
    )
    report = ResearchReport(
        task_id="task-1",
        goal="Research the project",
        title="Project research",
        summary="The project uses FastAPI.",
        findings=[finding],
        comparison="No alternative was requested.",
        recommendation="Review the cited documentation.",
        sources=[sourced_fact.source_url],
        markdown="# Research report",
    )
    assert result.facts == [sourced_fact]
    assert report.findings[0].name == "Framework"
    assert ResearchReport.model_validate_json(report.model_dump_json()) == report
    with pytest.raises(ValidationError):
        ResearchFact(content="Untraceable fact")
    with pytest.raises(ValidationError):
        ResearchFact(
            content="Bad URL", source_url="file:///private", source_title="Private"
        )
    with pytest.raises(ValidationError):
        ResearchFact(
            content="Bad URL",
            source_url="https://bad domain/path",
            source_title="Invalid host",
        )
    for local_url in ("http://localhost./private", "http://sub.localhost/private"):
        with pytest.raises(ValidationError):
            ResearchFact(
                content="Local URL",
                source_url=local_url,
                source_title="Local page",
            )
    with pytest.raises(ValidationError):
        Finding(title="old", content="old")


def test_event_contract_round_trip_and_independent_payloads() -> None:
    first = AgentEvent(
        event_type="task_queued", task_id="task-1", payload={"goal": "Research"}
    )
    second = AgentEvent(event_type="task_started", task_id="task-1")
    assert first.event_id != second.event_id
    assert first.step == 0
    assert first.timestamp.utcoffset() == timedelta(0)
    assert AgentEvent.model_validate_json(first.model_dump_json()) == first
    first.payload["extra"] = "local"
    assert second.payload == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"event_id": "not-a-uuid"},
        {"event_type": "step"},
        {"type": "task_started"},
        {"task_id": " "},
        {"step": -1},
        {"timestamp": datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None)},
        {"timestamp": datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=8)))},
        {"payload": {"bad": {1, 2}}},
        {"payload": {"bad": float("nan")}},
        {"unexpected": True},
    ],
)
def test_event_rejects_invalid_data(changes: dict[str, object]) -> None:
    data = {"event_type": "task_started", "task_id": "task-1"}
    data.update(changes)
    with pytest.raises(ValidationError):
        AgentEvent(**data)


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
