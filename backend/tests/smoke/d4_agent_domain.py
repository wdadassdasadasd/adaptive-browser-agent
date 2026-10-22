"""Opt-in public GitHub Agent-domain smoke; no model credential required."""

import asyncio
import json

from adaptive_research.agent.agent_loop import AgentLoop
from adaptive_research.agent.llm.base import StructuredCompletion
from adaptive_research.agent.state import EvaluationResult, ResearchFact
from adaptive_research.agent.tools.github_tool import GitHubTool
from adaptive_research.agent.tools.router import ToolRouter


class ControlledProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.closed = False

    async def complete_structured(self, prompt: str, schema: type):
        self.calls.append(schema.__name__)
        name = schema.__name__
        if name == "InitialSubgoals":
            value = schema.model_validate(
                {
                    "subgoals": [
                        {
                            "id": "s1",
                            "description": "Identify the FastAPI repository",
                            "completion_criteria": "Official sourced repository identity",
                        }
                    ]
                }
            )
        elif name == "PlanDecision":
            value = schema.model_validate(
                {
                    "subgoal_id": "s1",
                    "reasoning": "Read the public GitHub API",
                    "tool": "github",
                    "action": "get_repository",
                    "target": "fastapi/fastapi",
                    "expected_result": "Repository identity",
                }
            )
        elif name == "EvaluationResult":
            value = EvaluationResult(
                success=True,
                reason="Repository identity appears in source",
                subgoal_completed=True,
                facts=[
                    ResearchFact(
                        id="f1",
                        content="The official repository is fastapi/fastapi.",
                        source_url="https://api.github.com/repos/fastapi/fastapi",
                        source_title="GitHub repository API",
                        evidence="fastapi/fastapi",
                        subject="FastAPI",
                        subject_kind="project",
                        subgoal_id="s1",
                    )
                ],
            )
        elif name == "ReportDraft":
            value = schema.model_validate(
                {
                    "title": "FastAPI repository",
                    "findings": [{"name": "FastAPI", "fact_ids": ["f1"]}],
                }
            )
        else:
            raise AssertionError(name)
        return StructuredCompletion(value, 10, 5)

    async def aclose(self) -> None:
        self.closed = True


class UnusedBrowser:
    def __init__(self) -> None:
        self.closed = False

    async def close_session(self) -> None:
        self.closed = True


async def main() -> None:
    provider = ControlledProvider()
    browser = UnusedBrowser()
    github = GitHubTool()
    goal = "Find one project: FastAPI's official repository"
    result = await AgentLoop(
        provider, ToolRouter(browser, github), max_steps=2, max_seconds=60
    ).run(goal)
    record = {
        "goal": goal,
        "status": result.state.status,
        "completion_level": result.state.completion_level,
        "stop_reason": result.state.stop_reason,
        "step": result.state.step,
        "actions": [
            event.payload["decision"]["action"]
            for event in result.events
            if event.event_type == "step_evaluated"
        ],
        "fact_urls": [fact.source_url for fact in result.state.facts],
        "report_sources": result.report.sources if result.report else [],
        "report_summary": result.report.summary if result.report else None,
        "report_markdown": result.report.markdown if result.report else None,
        "terminal_events": sum(
            event.event_type == "task_finished" for event in result.events
        ),
        "provider_calls": provider.calls,
        "reported_fake_tokens": [
            result.state.prompt_tokens,
            result.state.completion_tokens,
        ],
        "closed": {
            "github": github.client.is_closed,
            "browser": browser.closed,
            "provider": provider.closed,
        },
    }
    print(json.dumps(record, ensure_ascii=False, indent=2))
    assert result.state.status == "completed"
    assert result.state.stop_reason == "target_count"
    assert record["fact_urls"] == record["report_sources"]
    assert record["terminal_events"] == 1
    assert record["fact_urls"][0] in record["report_markdown"]
    assert all(record["closed"].values())


if __name__ == "__main__":
    asyncio.run(main())
