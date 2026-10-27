"""DEC-T04-01: synthetic offline contrasts, not claims about real projects."""

from datetime import UTC, datetime

import pytest

from adaptive_research.agent.decision import DecisionService, JudgmentDraft
from adaptive_research.agent.llm.base import StructuredCompletion
from adaptive_research.agent.reporter import ReportDraft, ReporterService
from adaptive_research.agent.state import DecisionContext, ResearchFact, ResearchState

ASYNC = "async request handlers"
EMBEDDED = "in-process embedded storage"
PREFERENCE = "small footprint"
OBSERVED_AT = datetime(2026, 10, 26, tzinfo=UTC)


def sample_state() -> ResearchState:
    """One fixed catalogue; only the user hard conditions vary in the contrasts."""
    claims = [
        ("atlas-async", "AtlasAPI", "Supports async request handlers."),
        ("atlas-embedded", "AtlasAPI", "Does not support in-process embedded storage."),
        ("atlas-size", "AtlasAPI", "Does not meet the small footprint preference."),
        ("birch-async", "BirchAPI", "Does not support async request handlers."),
        ("birch-embedded", "BirchAPI", "Supports in-process embedded storage."),
        ("birch-size", "BirchAPI", "Meets the small footprint preference."),
    ]
    return ResearchState(
        task_id="dec-t04-01-synthetic-offline",
        goal="Compare the synthetic AtlasAPI and BirchAPI fixtures",
        status="partial",
        completion_level="partial",
        stop_reason="max_steps",
        decision_context=DecisionContext(
            use_case="Synthetic offline Python service selection",
            must_have=[ASYNC],
            preferences=[PREFERENCE],
            candidate_projects=["AtlasAPI", "BirchAPI"],
        ),
        facts=[
            ResearchFact(
                id=fact_id,
                subject=subject,
                subject_kind="project",
                content=claim,
                evidence=f"Synthetic offline fixture: {claim}",
                source_url=f"https://{subject.lower()}.invalid/reference",
                source_title=f"{subject} synthetic offline fixture",
                created_at=OBSERVED_AT,
            )
            for fact_id, subject, claim in claims
        ],
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )


class FixedJudgmentLLM:
    """Scripted responses are identical across scenarios; no provider is called."""

    def __init__(self, candidate_ids: dict[str, str]):
        self.schemas: list[type] = []
        self.rows = []
        for label, condition, kind, verdict, fact_id in [
            ("AtlasAPI", ASYNC, "must_have", "satisfied", "atlas-async"),
            ("AtlasAPI", EMBEDDED, "must_have", "not_satisfied", "atlas-embedded"),
            ("AtlasAPI", PREFERENCE, "preference", "not_satisfied", "atlas-size"),
            ("BirchAPI", ASYNC, "must_have", "not_satisfied", "birch-async"),
            ("BirchAPI", EMBEDDED, "must_have", "satisfied", "birch-embedded"),
            ("BirchAPI", PREFERENCE, "preference", "satisfied", "birch-size"),
        ]:
            self.rows.append(
                {
                    "candidate_id": candidate_ids[label],
                    "condition_type": kind,
                    "condition": condition,
                    "verdict": verdict,
                    "supporting_fact_ids": [fact_id] if verdict == "satisfied" else [],
                    "contradicting_fact_ids": [fact_id]
                    if verdict == "not_satisfied"
                    else [],
                    "reason": "Scripted judgment over synthetic offline evidence.",
                }
            )

    async def complete_structured(self, prompt: str, schema: type):
        self.schemas.append(schema)
        if schema is JudgmentDraft:
            value = {"rows": self.rows}
        elif schema is ReportDraft:
            value = {
                "title": "Synthetic offline comparison",
                "findings": [
                    {
                        "name": "AtlasAPI",
                        "fact_ids": ["atlas-async", "atlas-embedded", "atlas-size"],
                    },
                    {
                        "name": "BirchAPI",
                        "fact_ids": ["birch-async", "birch-embedded", "birch-size"],
                    },
                ],
            }
        else:
            raise AssertionError(f"Unexpected model schema: {schema}")
        return StructuredCompletion(schema.model_validate(value), 0, 0)


async def build_sample_reports():
    """Also reused by the local acceptance-artifact command."""
    original = sample_state()
    assert original.decision_context is not None
    discovery = await DecisionService().build(original)
    candidate_ids = {item.label: item.candidate_id for item in discovery.candidates}
    llm = FixedJudgmentLLM(candidate_ids)
    results = []
    for name, hard_conditions in [
        ("async", [ASYNC]),
        ("embedded", [EMBEDDED]),
        ("both", [ASYNC, EMBEDDED]),
    ]:
        state = original.model_copy(deep=True)
        state.decision_context.must_have = hard_conditions
        before = state.model_dump(mode="json")
        reporter = ReporterService(llm)
        report = await reporter.generate(state)
        assert not reporter.used_fallback
        assert state.model_dump(mode="json") == before
        results.append((name, state, report))
    assert llm.schemas == [ReportDraft, JudgmentDraft] * 3
    return results


@pytest.mark.asyncio
async def test_same_facts_with_changed_hard_condition_switch_winner() -> None:
    cases = await build_sample_reports()
    initial = cases[0][1].model_dump(mode="json", exclude={"decision_context"})
    for (_, state, report), winner, fact_ids in zip(
        cases[:2],
        ["AtlasAPI", "BirchAPI"],
        [{"atlas-async", "atlas-size"}, {"birch-embedded", "birch-size"}],
        strict=True,
    ):
        assert state.model_dump(mode="json", exclude={"decision_context"}) == initial
        decision = report.decision
        assert decision is not None
        assert decision.must_have == state.decision_context.must_have
        assert decision.preferences == [PREFERENCE]
        assert decision.candidate_projects == ["AtlasAPI", "BirchAPI"]
        recommendation = decision.recommendation
        assert recommendation is not None
        label = next(
            item.label
            for item in decision.candidates
            if item.candidate_id == recommendation.candidate_id
        )
        assert label == winner
        assert set(recommendation.supporting_fact_ids) == fact_ids
        assert report.recommendation == recommendation.text
        assert winner in report.recommendation
        hard_rows = [
            row for row in decision.matrix if row.condition_type == "must_have"
        ]
        assert len(hard_rows) == 2
        assert {row.condition for row in hard_rows} == set(decision.must_have)
        assert sorted(row.verdict for row in hard_rows) == [
            "not_satisfied",
            "satisfied",
        ]
        assert decision.no_recommendation_reason is None
        assert len(decision.change_conditions) == 1
        assert decision.must_have[0] in decision.change_conditions[0]
    # Birch's satisfied preference cannot override its failed hard condition.
    assert "small footprint: not_satisfied" in cases[0][2].recommendation
    assert "small footprint: satisfied" in cases[1][2].recommendation
    assert cases[0][2].recommendation != cases[1][2].recommendation


@pytest.mark.asyncio
async def test_combined_hard_conditions_reject_both_candidates_with_reason() -> None:
    cases = await build_sample_reports()
    _, state, report = cases[2]
    assert state.facts == cases[0][1].facts == cases[1][1].facts
    decision = report.decision
    assert decision is not None
    assert decision.must_have == [ASYNC, EMBEDDED]
    assert decision.recommendation is None
    assert decision.no_recommendation_reason
    assert report.recommendation == decision.no_recommendation_reason
    assert "Decision gap: " + decision.no_recommendation_reason in report.markdown
    assert "only candidate supported" not in report.recommendation
    for candidate in decision.candidates:
        rows = [
            row
            for row in decision.matrix
            if row.candidate_id == candidate.candidate_id
            and row.condition_type == "must_have"
        ]
        assert {row.condition for row in rows} == {ASYNC, EMBEDDED}
        assert sorted(row.verdict for row in rows) == ["not_satisfied", "satisfied"]
    assert len(decision.change_conditions) == 2
    for condition in (ASYNC, EMBEDDED):
        assert any(condition in item for item in decision.change_conditions)


@pytest.mark.asyncio
async def test_contrast_reports_keep_fact_provenance_and_human_review_status() -> None:
    for _, state, report in await build_sample_reports():
        decision = report.decision
        assert decision is not None
        assert decision.verification_status == "machine_admitted_human_unverified"
        if decision.recommendation is not None:
            assert (
                decision.recommendation.verification_status
                == "machine_admitted_human_unverified"
            )
            assert "pending human verification" in report.recommendation
        assert "Machine-admitted; official sources require human verification." in (
            report.markdown
        )
        assert "## Decision evidence" in report.markdown
        facts = {fact.id: fact for fact in state.facts}
        evidence = {item.fact_id: item for item in decision.evidence_facts}
        cited = {
            fact_id
            for row in decision.matrix
            for fact_id in row.supporting_fact_ids + row.contradicting_fact_ids
        }
        assert set(evidence) == cited
        assert decision.unknowns == []
        assert decision.conflicts == []
        for fact_id, item in evidence.items():
            fact = facts[fact_id]
            assert (item.subject, item.source_url, item.excerpt, item.observed_at) == (
                fact.subject,
                fact.source_url,
                fact.evidence,
                OBSERVED_AT,
            )
            assert (
                f"- {fact_id} | {fact.subject} | {fact.source_url} |" in report.markdown
            )
        for row in decision.matrix:
            ids = row.supporting_fact_ids + row.contradicting_fact_ids
            assert f"{row.verdict} | fact IDs: {', '.join(ids)}" in report.markdown
