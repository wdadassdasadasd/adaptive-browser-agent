"""A report may present only facts admitted to ResearchState."""

import pytest

from adaptive_agent.llm.base import LLMError, StructuredCompletion
from adaptive_agent.reporter import ReporterService
from adaptive_agent.state import ResearchFact, ResearchState, Subgoal


def state_with_facts() -> ResearchState:
    return ResearchState(
        goal="Compare two projects",
        status="partial",
        stop_reason="max_steps",
        completion_level="partial",
        subgoals=[
            Subgoal(
                id="s1",
                description="Find two projects",
                completion_criteria="Two sourced projects",
                status="in_progress",
            )
        ],
        facts=[
            ResearchFact(
                id="f1",
                content="FastAPI supports async route handlers.",
                source_url="https://fastapi.tiangolo.com/async/",
                source_title="FastAPI documentation",
                evidence="FastAPI supports async route handlers.",
                subject="FastAPI",
                subject_kind="project",
            )
        ],
    )


class DraftLLM:
    def __init__(self, draft: dict | None = None, error: LLMError | None = None):
        self.draft = draft
        self.error = error
        self.calls = 0

    async def complete_structured(self, prompt: str, schema: type):
        self.calls += 1
        if self.error:
            raise self.error
        return StructuredCompletion(schema.model_validate(self.draft), 7, 3)


@pytest.mark.asyncio
async def test_reporter_renders_only_selected_sourced_facts_and_gaps() -> None:
    state = state_with_facts()
    llm = DraftLLM(
        {
            "title": "FastAPI research",
            "findings": [{"name": "FastAPI", "fact_ids": ["f1"]}],
        }
    )

    report = await ReporterService(llm).generate(state)

    assert report.findings[0].supporting_fact_ids == ["f1"]
    assert report.findings[0].source_urls == ["https://fastapi.tiangolo.com/async/"]
    assert "FastAPI supports async route handlers." in report.markdown
    assert "Find two projects" in report.markdown
    assert "Requested 2 project(s); verified 1" in report.markdown
    assert "https://fastapi.tiangolo.com/async/" in report.markdown
    assert report.sources == ["https://fastapi.tiangolo.com/async/"]


@pytest.mark.asyncio
async def test_reporter_rejects_uncollected_fact_id_and_falls_back() -> None:
    llm = DraftLLM(
        {"title": "Invented", "findings": [{"name": "FastAPI", "fact_ids": ["fake"]}]}
    )

    report = await ReporterService(llm).generate(state_with_facts())

    assert "Invented" not in report.markdown
    assert report.findings[0].supporting_fact_ids == ["f1"]
    assert report.sources == ["https://fastapi.tiangolo.com/async/"]


@pytest.mark.asyncio
async def test_reporter_falls_back_on_malformed_draft_value() -> None:
    class MalformedDraftLLM:
        async def complete_structured(self, prompt: str, schema: type):
            return StructuredCompletion({"findings": "not a list"}, 2, 1)

    report = await ReporterService(MalformedDraftLLM()).generate(state_with_facts())

    assert report.findings[0].supporting_fact_ids == ["f1"]
    assert report.sources == ["https://fastapi.tiangolo.com/async/"]


@pytest.mark.asyncio
async def test_reporter_falls_back_after_model_failure_without_losing_evidence() -> (
    None
):
    llm = DraftLLM(error=LLMError("provider unavailable", 4, 2, kind="technical"))

    report = await ReporterService(llm).generate(state_with_facts())

    assert report.findings[0].supporting_fact_ids == ["f1"]
    assert "insufficient evidence" in report.comparison.lower()
    assert "Find two projects" in report.markdown


@pytest.mark.asyncio
async def test_reporter_explains_failure_without_facts() -> None:
    state = ResearchState(
        goal="Research project",
        status="failed",
        stop_reason="execution_error",
    )

    report = await ReporterService(DraftLLM()).generate(state)

    assert report.findings == []
    assert report.sources == []
    assert "execution_error" in report.markdown
    assert "insufficient evidence" in report.summary.lower()
    assert "unexpected error" in report.summary.lower()


@pytest.mark.asyncio
async def test_comparison_uses_only_facts_from_two_distinct_subjects() -> None:
    state = state_with_facts()
    state.facts.append(
        ResearchFact(
            id="f2",
            content="Flask documents async route handlers.",
            source_url="https://flask.palletsprojects.com/en/stable/async-await/",
            source_title="Flask documentation",
            evidence="Flask documents async route handlers.",
            subject="Flask",
            subject_kind="project",
        )
    )

    report = await ReporterService().generate(state)

    assert "FastAPI supports async route handlers." in report.comparison
    assert "Flask documents async route handlers." in report.comparison
    assert "https://fastapi.tiangolo.com/async/" in report.markdown
    assert "https://flask.palletsprojects.com/en/stable/async-await/" in report.markdown
