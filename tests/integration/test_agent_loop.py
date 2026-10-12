"""D4 Agent domain execution with controlled model and tool outcomes."""

import asyncio

import pytest

from adaptive_agent.agent_loop import AgentLoop
from adaptive_agent.llm.base import LLMError, StructuredCompletion
from adaptive_agent.state import EvaluationResult, ResearchFact, ToolResult
from adaptive_agent.tools.router import ToolRouter


class FakeProvider:
    def __init__(
        self,
        *,
        completed: bool = True,
        usage: tuple[int, int] = (10, 5),
        after_call=None,
        init_error: LLMError | None = None,
        cancel_report: bool = False,
        bad_source: bool = False,
        tool: str = "github",
    ) -> None:
        self.completed = completed
        self.usage = usage
        self.after_call = after_call
        self.init_error = init_error
        self.cancel_report = cancel_report
        self.bad_source = bad_source
        self.tool = tool
        self.calls: list[str] = []
        self.closed = False

    async def complete_structured(self, prompt: str, schema: type):
        self.calls.append(schema.__name__)
        if self.after_call is not None:
            self.after_call(schema.__name__, len(self.calls))
        if schema.__name__ == "InitialSubgoals":
            if self.init_error is not None:
                raise self.init_error
            value = schema.model_validate(
                {
                    "subgoals": [
                        {
                            "id": "s1",
                            "description": "Find FastAPI",
                            "completion_criteria": "Sourced project description",
                        }
                    ]
                }
            )
        elif schema.__name__ == "PlanDecision":
            value = schema.model_validate(
                {
                    "subgoal_id": "s1",
                    "reasoning": "Inspect official repository",
                    "tool": self.tool,
                    "action": "get_repository" if self.tool == "github" else "navigate",
                    "target": "fastapi/fastapi"
                    if self.tool == "github"
                    else "https://fastapi.tiangolo.com/",
                    "expected_result": "Project description",
                }
            )
        elif schema.__name__ == "EvaluationResult":
            value = EvaluationResult(
                success=True,
                reason="Sourced description found",
                subgoal_completed=self.completed,
                should_replan=not self.completed,
                facts=[
                    ResearchFact(
                        id="f1",
                        content="FastAPI is a web framework.",
                        source_url="https://example.com/unsupported"
                        if self.bad_source
                        else "https://api.github.com/repos/fastapi/fastapi",
                        source_title="GitHub API",
                        evidence="FastAPI is a web framework.",
                        subject="FastAPI",
                        subject_kind="project",
                    )
                ],
            )
        elif schema.__name__ == "ReportDraft":
            if self.cancel_report:
                raise asyncio.CancelledError
            value = schema.model_validate(
                {
                    "title": "FastAPI",
                    "findings": [{"name": "FastAPI", "fact_ids": ["f1"]}],
                }
            )
        else:
            raise AssertionError(schema)
        return StructuredCompletion(value, *self.usage)

    async def aclose(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, cancellation: asyncio.Event | None = None) -> None:
        self.started = False
        self.closed = False
        self.cancellation = cancellation
        self.calls = 0

    async def start_session(self) -> None:
        self.started = True

    async def observe(self, level: str = "light") -> dict:
        return {"title": "Blank"}

    async def close_session(self) -> None:
        self.closed = True

    async def execute(self, action: object) -> dict:
        self.calls += 1
        if self.cancellation is not None:
            self.cancellation.set()
        return {
            "success": True,
            "action": action.action,
            "content": "Navigated",
            "url": "https://fastapi.tiangolo.com/",
        }


class FakeGithub:
    def __init__(
        self,
        *,
        error: bool = False,
        cancellation: asyncio.Event | None = None,
        raise_error: bool = False,
    ):
        self.error = error
        self.cancellation = cancellation
        self.raise_error = raise_error
        self.calls = 0
        self.closed = False

    async def execute(self, action: str, target: str | None, value: str | None):
        self.calls += 1
        if self.raise_error:
            raise RuntimeError("unexpected tool failure")
        if self.cancellation is not None:
            self.cancellation.set()
        return ToolResult(
            tool="github",
            action=action,
            success=not self.error,
            content=""
            if self.error
            else '{"description":"FastAPI is a web framework."}',
            source_url="https://api.github.com/repos/fastapi/fastapi",
            error_type="technical" if self.error else "none",
            error_message="temporary failure" if self.error else None,
        )

    async def aclose(self) -> None:
        self.closed = True


def make_loop(
    provider: FakeProvider, github: FakeGithub, browser: FakeBrowser, **limits
):
    return AgentLoop(provider, ToolRouter(browser, github), **limits)


@pytest.mark.asyncio
async def test_completed_loop_has_one_terminal_event_sourced_report_and_usage() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert result.state.status == "completed"
    assert result.state.completion_level == "full"
    assert result.state.stop_reason == "goal_satisfied"
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert result.report.findings[0].supporting_fact_ids == ["f1"]
    assert result.report.sources == ["https://api.github.com/repos/fastapi/fastapi"]
    assert (result.state.prompt_tokens, result.state.completion_tokens) == (40, 20)
    assert github.calls == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_event_callback_receives_progress_before_loop_returns() -> None:
    seen: list[str] = []

    async def on_event(event) -> None:
        seen.append(event.event_type)

    result = await make_loop(FakeProvider(), FakeGithub(), FakeBrowser()).run(
        "Research FastAPI", on_event=on_event
    )
    assert seen == [event.event_type for event in result.events]
    assert "step_evaluated" in seen


@pytest.mark.asyncio
async def test_completed_subgoal_does_not_override_unmet_explicit_count() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_steps=1).run(
        "Find two projects"
    )

    assert (result.state.status, result.state.stop_reason) == ("partial", "max_steps")
    assert github.calls == 1
    assert result.report.findings[0].supporting_fact_ids == ["f1"]
    assert "Requested 2 project(s); verified 1" in result.report.markdown


@pytest.mark.asyncio
async def test_unmet_count_with_no_unfinished_subgoal_stops_as_partial() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Find two projects")

    assert (result.state.status, result.state.completion_level) == (
        "partial",
        "partial",
    )
    assert result.state.stop_reason == "insufficient_info"
    assert result.state.step == 1
    assert provider.calls == [
        "InitialSubgoals",
        "PlanDecision",
        "EvaluationResult",
        "ReportDraft",
    ]
    assert github.calls == 1
    assert "Requested 2 project(s); verified 1" in result.report.markdown
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_same_browser_question_can_serve_a_different_subgoal() -> None:
    class TwoSubgoalProvider(FakeProvider):
        def __init__(self) -> None:
            super().__init__()
            self.plans = 0
            self.evaluations = 0

        async def complete_structured(self, prompt: str, schema: type):
            if schema.__name__ == "InitialSubgoals":
                return StructuredCompletion(
                    schema.model_validate(
                        {
                            "subgoals": [
                                {
                                    "id": "s1",
                                    "description": "First question",
                                    "completion_criteria": "Sourced answer",
                                },
                                {
                                    "id": "s2",
                                    "description": "Second question",
                                    "completion_criteria": "Sourced answer",
                                },
                            ]
                        }
                    ),
                    10,
                    5,
                )
            if schema.__name__ == "PlanDecision":
                self.plans += 1
                return StructuredCompletion(
                    schema.model_validate(
                        {
                            "subgoal_id": f"s{self.plans}",
                            "reasoning": "Read the page",
                            "tool": "browser",
                            "action": "extract",
                            "target": "What is FastAPI?",
                            "expected_result": "A sourced answer",
                        }
                    ),
                    10,
                    5,
                )
            if schema.__name__ == "EvaluationResult":
                self.evaluations += 1
                return StructuredCompletion(
                    EvaluationResult(
                        success=self.evaluations == 2,
                        reason="Second subgoal has a sourced answer",
                        subgoal_completed=self.evaluations == 2,
                        should_replan=self.evaluations == 1,
                        error_type="insufficient_info"
                        if self.evaluations == 1
                        else "none",
                        facts=[
                            ResearchFact(
                                id="f2",
                                content="Navigated",
                                source_url="https://fastapi.tiangolo.com/",
                                source_title="FastAPI docs",
                                evidence="Navigated",
                                subgoal_id="s2",
                            )
                        ]
                        if self.evaluations == 2
                        else [],
                    ),
                    10,
                    5,
                )
            return await super().complete_structured(prompt, schema)

    provider, github, browser = TwoSubgoalProvider(), FakeGithub(), FakeBrowser()
    result = await make_loop(provider, github, browser, max_steps=2).run(
        "Research FastAPI"
    )

    assert browser.calls == 2
    assert result.state.stop_reason == "max_steps"
    assert [fact.id for fact in result.state.facts] == ["f2"]


@pytest.mark.asyncio
async def test_wall_time_limit_interrupts_in_flight_tool_call() -> None:
    class HangingGithub(FakeGithub):
        async def execute(self, action: str, target: str | None, value: str | None):
            self.calls += 1
            await asyncio.Event().wait()

    provider, github, browser = FakeProvider(), HangingGithub(), FakeBrowser()

    result = await asyncio.wait_for(
        make_loop(provider, github, browser, max_seconds=0.05).run("Research FastAPI"),
        timeout=1,
    )

    assert (result.state.status, result.state.stop_reason) == (
        "failed",
        "time_limit",
    )
    assert github.calls == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_cancellation_interrupts_in_flight_tool_call() -> None:
    entered = asyncio.Event()
    cancellation = asyncio.Event()

    class HangingGithub(FakeGithub):
        async def execute(self, action: str, target: str | None, value: str | None):
            self.calls += 1
            entered.set()
            await asyncio.Event().wait()

    provider, github, browser = FakeProvider(), HangingGithub(), FakeBrowser()
    task = asyncio.create_task(
        make_loop(provider, github, browser).run(
            "Research FastAPI", cancellation=cancellation
        )
    )
    await entered.wait()
    cancellation.set()
    done, _ = await asyncio.wait({task}, timeout=0.2)
    if not done:
        task.cancel()
        await task
    assert done, "cancellation did not interrupt the in-flight tool"
    result = task.result()

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_hanging_resource_close_has_bounded_terminal_failure() -> None:
    class HangingBrowser(FakeBrowser):
        async def close_session(self) -> None:
            await asyncio.Event().wait()

    provider, github, browser = FakeProvider(), FakeGithub(), HangingBrowser()
    result = await asyncio.wait_for(
        make_loop(provider, github, browser, cleanup_timeout=0.05).run(
            "Research FastAPI"
        ),
        timeout=1,
    )

    assert (result.state.status, result.state.stop_reason) == (
        "failed",
        "cleanup_error",
    )
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert github.closed and provider.closed


@pytest.mark.asyncio
async def test_cancellation_signal_during_cleanup_changes_terminal_outcome() -> None:
    cancellation = asyncio.Event()

    class CancellingProvider(FakeProvider):
        async def aclose(self) -> None:
            cancellation.set()
            self.closed = True

    provider, github, browser = CancellingProvider(), FakeGithub(), FakeBrowser()
    result = await make_loop(provider, github, browser).run(
        "Research FastAPI", cancellation=cancellation
    )

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_wall_time_limit_interrupts_report_model_call() -> None:
    class HangingReportProvider(FakeProvider):
        async def complete_structured(self, prompt: str, schema: type):
            if schema.__name__ == "ReportDraft":
                self.calls.append(schema.__name__)
                await asyncio.Event().wait()
            return await super().complete_structured(prompt, schema)

    provider, github, browser = HangingReportProvider(), FakeGithub(), FakeBrowser()

    result = await asyncio.wait_for(
        make_loop(provider, github, browser, max_seconds=0.05).run("Research FastAPI"),
        timeout=1,
    )

    assert (result.state.status, result.state.stop_reason) == (
        "partial",
        "time_limit",
    )
    assert result.report.findings[0].supporting_fact_ids == ["f1"]
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_loop_passes_remaining_token_allowance_to_provider() -> None:
    class BudgetAwareProvider(FakeProvider):
        def __init__(self) -> None:
            super().__init__()
            self.allowances: list[int] = []

        async def complete_structured_budgeted(
            self, prompt: str, schema: type, remaining_tokens: int
        ):
            self.allowances.append(remaining_tokens)
            return await super().complete_structured(prompt, schema)

    provider, github, browser = BudgetAwareProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_tokens=100).run(
        "Research FastAPI"
    )

    assert result.state.status == "completed"
    assert provider.allowances == [100, 85, 70, 55]


@pytest.mark.asyncio
async def test_provider_budget_refusal_stops_before_tool_action() -> None:
    class RefusingProvider(FakeProvider):
        async def complete_structured_budgeted(
            self, prompt: str, schema: type, remaining_tokens: int
        ):
            if schema.__name__ == "PlanDecision":
                raise LLMError("insufficient budget", kind="budget")
            return await super().complete_structured(prompt, schema)

    provider, github, browser = RefusingProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert (result.state.status, result.state.stop_reason) == (
        "failed",
        "token_budget",
    )
    assert github.calls == 0


@pytest.mark.asyncio
async def test_step_limit_with_sourced_fact_is_partial_and_names_gap() -> None:
    provider, github, browser = (
        FakeProvider(completed=False),
        FakeGithub(),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser, max_steps=1).run(
        "Research FastAPI"
    )

    assert (
        result.state.status,
        result.state.completion_level,
        result.state.stop_reason,
    ) == (
        "partial",
        "partial",
        "max_steps",
    )
    assert "Find FastAPI" in result.report.markdown
    assert result.state.subgoals[0].status == "failed"
    assert result.state.subgoals[0].failure_reason == "max_steps"
    assert github.calls == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_technical_tool_failure_retries_once_then_fails_without_facts() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(error=True), FakeBrowser()

    result = await make_loop(provider, github, browser, max_steps=1).run(
        "Research FastAPI"
    )

    assert (
        result.state.status,
        result.state.completion_level,
        result.state.stop_reason,
    ) == (
        "failed",
        "none",
        "max_steps",
    )
    assert result.report.findings == []
    assert github.calls == 2
    assert provider.calls == ["InitialSubgoals", "PlanDecision"]
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_cancellation_during_tool_action_finishes_once_and_closes_resources() -> (
    None
):
    cancel = asyncio.Event()
    provider, github, browser = (
        FakeProvider(),
        FakeGithub(cancellation=cancel),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser).run(
        "Research FastAPI", cancellation=cancel
    )

    assert (
        result.state.status,
        result.state.completion_level,
        result.state.stop_reason,
    ) == (
        "cancelled",
        "none",
        "user_cancelled",
    )
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert result.report.findings == []
    assert github.calls == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_explicit_count_uses_verified_subject_even_if_subgoal_is_unfinished() -> (
    None
):
    provider, github, browser = (
        FakeProvider(completed=False),
        FakeGithub(),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser).run("Find one project")

    assert result.state.status == "completed"
    assert result.state.stop_reason == "target_count"
    assert github.calls == 1


@pytest.mark.asyncio
async def test_token_limit_after_initialization_prevents_next_provider_call() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_tokens=15).run(
        "Research FastAPI"
    )

    assert (result.state.status, result.state.stop_reason) == ("failed", "token_budget")
    assert (result.state.prompt_tokens, result.state.completion_tokens) == (10, 5)
    assert provider.calls == ["InitialSubgoals"]
    assert github.calls == 0


@pytest.mark.asyncio
async def test_time_limit_after_initialization_prevents_next_action() -> None:
    current = [0.0]

    def after_call(schema: str, count: int) -> None:
        if schema == "InitialSubgoals":
            current[0] = 900.0

    provider = FakeProvider(after_call=after_call)
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, clock=lambda: current[0]).run(
        "Research FastAPI"
    )

    assert (result.state.status, result.state.stop_reason) == ("failed", "time_limit")
    assert provider.calls == ["InitialSubgoals"]
    assert github.calls == 0


@pytest.mark.asyncio
async def test_repeated_no_progress_plan_stops_with_gap_and_no_repeat_tool_call() -> (
    None
):
    provider, github, browser = (
        FakeProvider(completed=False),
        FakeGithub(),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser, max_no_progress=2).run(
        "Research FastAPI"
    )

    assert (result.state.status, result.state.stop_reason) == ("partial", "no_progress")
    assert result.state.step == 3
    assert github.calls == 1
    assert "Find FastAPI" in result.report.markdown


@pytest.mark.asyncio
async def test_known_usage_on_provider_failure_is_preserved() -> None:
    provider = FakeProvider(init_error=LLMError("bad output", 8, 4, kind="structured"))
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert (result.state.status, result.state.stop_reason) == (
        "failed",
        "execution_error",
    )
    assert (result.state.prompt_tokens, result.state.completion_tokens) == (8, 4)
    assert provider.calls == ["InitialSubgoals"]
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_cancellation_after_sourced_step_keeps_partial_evidence() -> None:
    cancel = asyncio.Event()

    def after_call(schema: str, count: int) -> None:
        if schema == "PlanDecision" and count > 3:
            cancel.set()

    provider = FakeProvider(completed=False, after_call=after_call)
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run(
        "Research FastAPI", cancellation=cancel
    )

    assert (result.state.status, result.state.completion_level) == (
        "cancelled",
        "partial",
    )
    assert result.state.stop_reason == "user_cancelled"
    assert result.report.findings[0].supporting_fact_ids == ["f1"]
    assert github.calls == 1


@pytest.mark.asyncio
async def test_report_usage_reaching_token_limit_downgrades_completion() -> None:
    provider, github, browser = FakeProvider(), FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_tokens=60).run(
        "Research FastAPI"
    )

    assert (result.state.status, result.state.stop_reason) == (
        "partial",
        "token_budget",
    )
    assert (result.state.prompt_tokens, result.state.completion_tokens) == (40, 20)
    assert "token_budget" in result.report.markdown
    assert [event.event_type for event in result.events].count("task_finished") == 1


@pytest.mark.asyncio
async def test_cancellation_during_report_still_closes_and_finishes_once() -> None:
    provider = FakeProvider(cancel_report=True)
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert result.report.findings[0].supporting_fact_ids == ["f1"]
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_frozen_30_step_limit_stops_without_more_tool_calls() -> None:
    provider, github, browser = (
        FakeProvider(completed=False),
        FakeGithub(),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser, max_no_progress=31).run(
        "Research FastAPI"
    )

    assert (result.state.step, result.state.stop_reason) == (30, "max_steps")
    assert result.state.status == "partial"
    assert github.calls == 1


@pytest.mark.asyncio
async def test_frozen_40000_token_limit_stops_after_reported_usage() -> None:
    provider = FakeProvider(usage=(30_000, 10_000))
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert result.state.stop_reason == "token_budget"
    assert (result.state.prompt_tokens, result.state.completion_tokens) == (
        30_000,
        10_000,
    )
    assert provider.calls == ["InitialSubgoals"]
    assert github.calls == 0


@pytest.mark.asyncio
async def test_default_five_no_progress_replans_stop_after_five() -> None:
    provider, github, browser = (
        FakeProvider(completed=False),
        FakeGithub(),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert result.state.stop_reason == "no_progress"
    assert result.state.consecutive_no_progress_replans == 5
    assert result.state.step == 6
    assert github.calls == 1


@pytest.mark.asyncio
async def test_mismatched_source_fact_is_rejected_before_count_stop() -> None:
    provider = FakeProvider(bad_source=True)
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_steps=1).run(
        "Find one project"
    )

    assert (result.state.status, result.state.stop_reason) == ("failed", "max_steps")
    assert result.state.facts == []
    assert result.report.findings == []
    assert github.calls == 1


@pytest.mark.asyncio
async def test_browser_session_starts_for_browser_action_and_closes_on_stop() -> None:
    provider = FakeProvider(tool="browser")
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser, max_steps=1).run(
        "Research FastAPI"
    )

    assert (result.state.status, result.state.stop_reason) == ("failed", "max_steps")
    assert browser.started and browser.closed and browser.calls == 1
    assert github.closed and provider.closed


@pytest.mark.asyncio
async def test_cancel_during_browser_action_closes_started_session() -> None:
    cancel = asyncio.Event()
    provider = FakeProvider(tool="browser")
    github, browser = FakeGithub(), FakeBrowser(cancellation=cancel)

    result = await make_loop(provider, github, browser).run(
        "Research FastAPI", cancellation=cancel
    )

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert browser.started and browser.closed and browser.calls == 1
    assert github.closed and provider.closed


@pytest.mark.asyncio
async def test_unhandled_tool_exception_is_terminal_and_closes_every_resource() -> None:
    provider, github, browser = (
        FakeProvider(),
        FakeGithub(raise_error=True),
        FakeBrowser(),
    )

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert (result.state.status, result.state.stop_reason) == (
        "failed",
        "execution_error",
    )
    assert result.report.findings == []
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_unhandled_planner_error_after_facts_is_failed_not_partial() -> None:
    def fail_second_plan(schema: str, count: int) -> None:
        if schema == "PlanDecision" and count == 4:
            raise RuntimeError("planner failed")

    provider = FakeProvider(completed=False, after_call=fail_second_plan)
    github, browser = FakeGithub(), FakeBrowser()

    result = await make_loop(provider, github, browser).run("Research FastAPI")

    assert len(result.state.facts) == 1
    assert (result.state.status, result.state.completion_level) == (
        "failed",
        "none",
    )
    assert result.state.stop_reason == "execution_error"
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_external_cancellation_during_cleanup_still_finishes_and_closes() -> None:
    class BlockingCloseBrowser(FakeBrowser):
        def __init__(self) -> None:
            super().__init__()
            self.close_started = asyncio.Event()
            self.release = asyncio.Event()

        async def close_session(self) -> None:
            self.close_started.set()
            await self.release.wait()
            self.closed = True

    provider, github, browser = FakeProvider(), FakeGithub(), BlockingCloseBrowser()
    task = asyncio.create_task(
        make_loop(provider, github, browser).run("Research FastAPI")
    )
    await asyncio.wait_for(browser.close_started.wait(), timeout=2)
    task.cancel()
    browser.release.set()

    result = await asyncio.wait_for(task, timeout=2)

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed


@pytest.mark.asyncio
async def test_external_cancellation_during_provider_close_updates_terminal_report() -> (
    None
):
    class BlockingCloseProvider(FakeProvider):
        def __init__(self) -> None:
            super().__init__()
            self.close_started = asyncio.Event()
            self.release = asyncio.Event()

        async def aclose(self) -> None:
            self.close_started.set()
            await self.release.wait()
            self.closed = True

    provider, github, browser = BlockingCloseProvider(), FakeGithub(), FakeBrowser()
    task = asyncio.create_task(
        make_loop(provider, github, browser).run("Research FastAPI")
    )
    await asyncio.wait_for(provider.close_started.wait(), timeout=2)
    task.cancel()
    provider.release.set()

    result = await asyncio.wait_for(task, timeout=2)

    assert (result.state.status, result.state.stop_reason) == (
        "cancelled",
        "user_cancelled",
    )
    assert "user_cancelled" in result.report.markdown
    assert [event.event_type for event in result.events].count("task_finished") == 1
    assert browser.closed and github.closed and provider.closed
