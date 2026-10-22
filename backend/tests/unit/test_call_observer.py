"""Durable attempt ordering without a paid provider or browser."""

import asyncio

import pytest

from adaptive_research.agent.agent_loop import AgentLoop, _MeteredProvider
from adaptive_research.agent.call_observer import CallObservationError, CallRecorder
from adaptive_research.agent.llm.base import (
    LLMCompletion,
    LLMError,
    ProviderUsage,
    StructuredCompletion,
)
from adaptive_research.agent.state import EvaluationResult, ResearchFact, ToolResult


class FakeObserver:
    def __init__(
        self, timeline: list[tuple], *, fail_start: int = 0, fail_finish: int = 0
    ) -> None:
        self.timeline = timeline
        self.fail_start = fail_start
        self.fail_finish = fail_finish
        self.starts = 0
        self.finishes = 0

    async def started(self, kind: str, operation: str) -> str:
        self.starts += 1
        self.timeline.append(("started", kind, operation))
        if self.starts == self.fail_start:
            raise RuntimeError("lease lost")
        return str(self.starts)

    async def finished(
        self,
        call_id: str,
        outcome: str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        error_type: str | None = None,
    ) -> None:
        self.finishes += 1
        self.timeline.append(
            ("finished", call_id, outcome, prompt_tokens, completion_tokens, error_type)
        )
        if self.finishes == self.fail_finish:
            raise RuntimeError("lease lost")


class FakeProvider:
    def __init__(
        self,
        timeline: list[tuple],
        *,
        fail_initial: bool = False,
    ) -> None:
        self.timeline = timeline
        self.fail_initial = fail_initial
        self.calls = 0
        self.closed = False

    async def complete_structured(self, prompt: str, schema: type):
        self.calls += 1
        name = schema.__name__
        self.timeline.append(("provider", name))
        if name == "InitialSubgoals" and self.fail_initial:
            raise LLMError(
                "provider rejected",
                prompt_tokens=3,
                completion_tokens=1,
                kind="rejected",
            )
        if name == "InitialSubgoals":
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
        elif name == "PlanDecision":
            value = schema.model_validate(
                {
                    "subgoal_id": "s1",
                    "reasoning": "Inspect official repository",
                    "tool": "github",
                    "action": "get_repository",
                    "target": "fastapi/fastapi",
                    "expected_result": "Project description",
                }
            )
        elif name == "EvaluationResult":
            value = EvaluationResult(
                success=True,
                reason="Sourced description found",
                subgoal_completed=True,
                should_replan=False,
                facts=[
                    ResearchFact(
                        id="f1",
                        content="FastAPI is a web framework.",
                        source_url="https://api.github.com/repos/fastapi/fastapi",
                        source_title="GitHub API",
                        evidence="FastAPI is a web framework.",
                        subject="FastAPI",
                        subject_kind="project",
                    )
                ],
            )
        elif name == "ReportDraft":
            value = schema.model_validate(
                {
                    "title": "FastAPI",
                    "findings": [{"name": "FastAPI", "fact_ids": ["f1"]}],
                }
            )
        else:
            raise AssertionError(name)
        return StructuredCompletion(value, 4, 2)

    async def aclose(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self) -> None:
        self.closed = False

    async def close_session(self) -> None:
        self.closed = True


class FakeGithub:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeRouter:
    def __init__(self, timeline: list[tuple]) -> None:
        self.timeline = timeline
        self.browser = FakeBrowser()
        self.github = FakeGithub()
        self.calls = 0

    async def execute(self, decision, state) -> ToolResult:
        self.calls += 1
        self.timeline.append(("tool", decision.action))
        return ToolResult(
            tool="github",
            action=decision.action,
            success=True,
            content='{"description":"FastAPI is a web framework."}',
            source_url="https://api.github.com/repos/fastapi/fastapi",
        )


def make_loop(timeline: list[tuple], **provider_options):
    provider = FakeProvider(timeline, **provider_options)
    router = FakeRouter(timeline)
    return AgentLoop(provider, router), provider, router


@pytest.mark.asyncio
async def test_observer_persists_start_before_each_external_call_and_known_usage() -> (
    None
):
    timeline: list[tuple] = []
    observer = FakeObserver(timeline)
    loop, provider, router = make_loop(timeline)

    result = await loop.run("Research FastAPI", call_observer=observer)

    assert result.state.status == "completed"
    assert observer.starts == observer.finishes == 5
    assert timeline[:3] == [
        ("started", "model", "complete_structured:InitialSubgoals"),
        ("provider", "InitialSubgoals"),
        ("finished", "1", "completed", 4, 2, None),
    ]
    tool_index = timeline.index(("tool", "get_repository"))
    assert timeline[tool_index - 1] == ("started", "tool", "github.get_repository")
    assert timeline[tool_index + 1] == ("finished", "3", "completed", None, None, None)
    assert all("fastapi/fastapi" not in str(item) for item in timeline)
    assert router.calls == 1
    assert provider.closed and router.browser.closed and router.github.closed


@pytest.mark.asyncio
async def test_known_provider_failure_records_usage_and_cleans_up() -> None:
    timeline: list[tuple] = []
    observer = FakeObserver(timeline)
    loop, provider, router = make_loop(timeline, fail_initial=True)

    result = await loop.run("Research FastAPI", call_observer=observer)

    assert result.state.status == "failed"
    assert timeline[:3] == [
        ("started", "model", "complete_structured:InitialSubgoals"),
        ("provider", "InitialSubgoals"),
        ("finished", "1", "failed", 3, 1, "rejected"),
    ]
    assert provider.calls == 1 and router.calls == 0
    assert provider.closed and router.browser.closed and router.github.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["start", "finish"])
async def test_ledger_failure_blocks_later_calls_and_keeps_cleanup(
    failure: str,
) -> None:
    timeline: list[tuple] = []
    observer = FakeObserver(
        timeline,
        fail_start=1 if failure == "start" else 0,
        fail_finish=1 if failure == "finish" else 0,
    )
    loop, provider, router = make_loop(timeline)

    result = await loop.run("Research FastAPI", call_observer=observer)

    assert result.state.status == "failed"
    assert provider.calls == (0 if failure == "start" else 1)
    assert result.state.prompt_tokens == (0 if failure == "start" else 4)
    assert result.state.completion_tokens == (0 if failure == "start" else 2)
    assert router.calls == 0
    assert provider.closed and router.browser.closed and router.github.closed


@pytest.mark.asyncio
async def test_cancelled_call_remains_started_and_recorder_refuses_retry() -> None:
    timeline: list[tuple] = []
    observer = FakeObserver(timeline)
    recorder = CallRecorder(observer)

    async def cancelled() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await recorder.run("tool", "github.get_repository", cancelled)
    with pytest.raises(RuntimeError, match="ledger unavailable"):
        await recorder.run("tool", "github.get_repository", cancelled)
    assert timeline == [("started", "tool", "github.get_repository")]


@pytest.mark.asyncio
async def test_failed_finish_retains_known_plain_usage_and_blocks_followup() -> None:
    class Provider:
        calls = 0

        async def complete(self, prompt):
            self.calls += 1
            return LLMCompletion("private body", 7, 3)

    provider = Provider()
    recorder = CallRecorder(FakeObserver([], fail_finish=1))
    meter = _MeteredProvider(provider, 100, recorder)
    with pytest.raises(CallObservationError) as caught:
        await meter.complete("private prompt")
    assert (caught.value.prompt_tokens, caught.value.completion_tokens) == (7, 3)
    assert (meter.prompt_tokens, meter.completion_tokens) == (7, 3)
    with pytest.raises(CallObservationError):
        await meter.complete("must not run")
    assert provider.calls == 1
    assert (meter.prompt_tokens, meter.completion_tokens) == (7, 3)


@pytest.mark.asyncio
async def test_optional_metadata_is_content_free_and_observer_rejection_is_sticky() -> (
    None
):
    metadata = ProviderUsage(4, 3, 1_792_540_800, "deepseek-flash", "fp-test")
    seen = []

    class Observer:
        async def started(self, kind, operation):
            return "1"

        async def finished(self, call_id, outcome, **usage):
            seen.append(usage)
            raise RuntimeError("unknown pricing")

    recorder = CallRecorder(Observer())

    async def response():
        return LLMCompletion("private response", 7, 3, metadata)

    with pytest.raises(CallObservationError) as caught:
        await recorder.run("model", "complete", response)
    assert caught.value.prompt_tokens == 7
    assert seen[0]["provider_usage"] == metadata
    assert "private" not in str(seen)
    with pytest.raises(CallObservationError):
        await recorder.run("model", "complete", response)
    assert len(seen) == 1
