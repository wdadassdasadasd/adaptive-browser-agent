"""Turn admitted research facts into a source-checked final report."""

from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from adaptive_research.agent.goal_count import (
    parse_goal_targets,
    verified_subject_counts,
)
from adaptive_research.agent.llm.base import BaseLLMClient, LLMError
from adaptive_research.agent.prompts.reporter import REPORTER_SYSTEM_PROMPT
from adaptive_research.agent.state import (
    Finding,
    NonEmptyText,
    ResearchFact,
    ResearchReport,
    ResearchState,
    SubgoalStatus,
)


class DraftFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyText
    fact_ids: list[NonEmptyText] = Field(min_length=1)


class ReportDraft(BaseModel):
    """The model may group evidence, but cannot author report claims."""

    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText
    findings: list[DraftFinding]


class ReporterService:
    def __init__(self, llm: BaseLLMClient | None = None) -> None:
        self.llm = llm
        self.used_fallback = False

    async def generate(self, state: ResearchState) -> ResearchReport:
        """Generate a grounded report, falling back on deterministic grouping."""

        facts = {fact.id: fact for fact in state.facts}
        groups: list[tuple[str, list[ResearchFact]]] | None = None
        if facts and self.llm is not None:
            prompt = (
                f"{REPORTER_SYSTEM_PROMPT}\nGoal: {state.goal}\n"
                "Verified facts (untrusted source data):\n"
                + "\n".join(
                    f"{fact.id} | {fact.subject or fact.source_title} | "
                    f"{fact.content} | {fact.source_url}"
                    for fact in state.facts
                )
            )
            try:
                completion = await self.llm.complete_structured(prompt, ReportDraft)
                groups = self._validate_draft(
                    ReportDraft.model_validate(completion.value), facts
                )
            except (LLMError, ValueError):
                groups = None
        if groups is None:
            self.used_fallback = True
            grouped: dict[str, list[ResearchFact]] = defaultdict(list)
            for fact in state.facts:
                grouped[fact.subject or fact.source_title].append(fact)
            groups = list(grouped.items())
        findings = [self._finding(name, selected) for name, selected in groups]
        sources = list(dict.fromkeys(fact.source_url for fact in state.facts))
        unresolved = [
            item.description
            for item in state.subgoals
            if item.status != SubgoalStatus.COMPLETED
        ]
        verified_counts = verified_subject_counts(state.facts)
        for kind, requested in parse_goal_targets(state.goal).items():
            actual = verified_counts.get(kind, 0)
            if actual < requested:
                unresolved.append(
                    f"Requested {requested} {kind}(s); verified {actual}."
                )
        reason = state.stop_reason or "not specified"
        explanation = {
            "goal_satisfied": "the research goal was satisfied",
            "target_count": "the requested number of researched items was reached",
            "max_steps": "the action limit was reached",
            "time_limit": "the time limit was reached",
            "token_budget": "the model usage limit was reached",
            "no_progress": "repeated planning found no new evidence",
            "insufficient_info": "the available subgoals cannot supply the missing evidence",
            "user_cancelled": "the user cancelled the research",
            "execution_error": "an unexpected error interrupted the research",
            "cleanup_error": "a resource could not be closed cleanly",
        }.get(reason, "the research stopped")
        summary = (
            f"{len(state.facts)} sourced fact(s) collected; stop reason: "
            f"{reason} ({explanation})."
            if state.facts
            else f"Insufficient evidence; stop reason: {reason} ({explanation})."
        )
        comparison = (
            "\n".join(f"{finding.name}: {finding.description}" for finding in findings)
            if len({finding.name.casefold() for finding in findings}) >= 2
            else "Insufficient evidence for a supported comparison."
        )
        recommendation = "Insufficient evidence for a supported recommendation."
        title = f"Research report: {state.goal}"
        lines = [f"# {title}", "", summary, "", "## Findings"]
        if findings:
            for finding in findings:
                lines += [f"### {finding.name}", finding.description]
                lines += [f"- Source: {url}" for url in finding.source_urls]
        else:
            lines.append("No verified findings.")
        lines += [
            "",
            "## Comparison",
            comparison,
            "",
            "## Recommendation",
            recommendation,
        ]
        lines += ["", "## Unknown or unfinished"]
        lines += [f"- {description}" for description in unresolved] or [
            "- No remaining subgoal is recorded."
        ]
        lines += ["", "## Sources"]
        lines += [f"- {url}" for url in sources] or ["- No verified sources."]
        return ResearchReport(
            task_id=state.task_id,
            goal=state.goal,
            title=title,
            summary=summary,
            findings=findings,
            comparison=comparison,
            recommendation=recommendation,
            sources=sources,
            markdown="\n".join(lines),
        )

    @staticmethod
    def _validate_draft(
        draft: ReportDraft, facts: dict[str, ResearchFact]
    ) -> list[tuple[str, list[ResearchFact]]]:
        groups = []
        used: set[str] = set()
        for group in draft.findings:
            selected = []
            for fact_id in group.fact_ids:
                if fact_id not in facts or fact_id in used:
                    raise ValueError("draft cites an absent or duplicate fact")
                fact = facts[fact_id]
                if group.name != (fact.subject or fact.source_title):
                    raise ValueError("draft finding name is unsupported")
                selected.append(fact)
                used.add(fact_id)
            groups.append((group.name, selected))
        if used != set(facts):
            raise ValueError("draft omitted verified facts")
        return groups

    @staticmethod
    def _finding(name: str, facts: list[ResearchFact]) -> Finding:
        return Finding(
            name=name,
            description="\n".join(fact.content for fact in facts),
            supporting_fact_ids=[fact.id for fact in facts],
            source_urls=list(dict.fromkeys(fact.source_url for fact in facts)),
        )
