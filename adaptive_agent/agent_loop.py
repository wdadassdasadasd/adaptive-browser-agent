"""Bounded observe, decide, act, evaluate, reduce, and report orchestration."""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any

from adaptive_agent.context_manager import ContextManager
from adaptive_agent.evaluator import EvaluatorService
from adaptive_agent.events import AgentEvent
from adaptive_agent.goal_count import parse_goal_targets, targets_met
from adaptive_agent.llm.base import (
    BaseLLMClient,
    LLMCompletion,
    LLMError,
    StructuredCompletion,
    T,
)
from adaptive_agent.planner import PlannerService
from adaptive_agent.reporter import ReporterService
from adaptive_agent.state import (
    EvaluationErrorType,
    ResearchReport,
    ResearchState,
    ResearchStatus,
    SubgoalStatus,
    ToolResult,
)
from adaptive_agent.state_reducer import StateReducer
from adaptive_agent.tools.router import ToolRouter


@dataclass(frozen=True)
class AgentRunResult:
    state: ResearchState
    report: ResearchReport | None
    events: tuple[AgentEvent, ...]
    pending_tool_result: ToolResult | None = None


class _MeteredProvider:
    """Keep reported task usage, including usage attached to LLM failures."""

    def __init__(self, provider: BaseLLMClient, max_tokens: int) -> None:
        self.provider = provider
        self.max_tokens = max_tokens
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def _record(self, prompt: int | None, completion: int | None) -> None:
        if prompt is not None:
            self.prompt_tokens += prompt
        if completion is not None:
            self.completion_tokens += completion

    async def complete(self, prompt: str) -> LLMCompletion:
        try:
            response = await self.provider.complete(prompt)
        except LLMError as exc:
            self._record(exc.prompt_tokens, exc.completion_tokens)
            raise
        self._record(response.prompt_tokens, response.completion_tokens)
        return response

    async def complete_structured(
        self, prompt: str, schema: type[T]
    ) -> StructuredCompletion[T]:
        remaining = self.max_tokens - self.prompt_tokens - self.completion_tokens
        if remaining <= 0:
            raise LLMError("Token budget exhausted", kind="budget")
        try:
            budgeted = getattr(self.provider, "complete_structured_budgeted", None)
            response = (
                await budgeted(prompt, schema, remaining)
                if budgeted is not None
                else await self.provider.complete_structured(prompt, schema)
            )
        except LLMError as exc:
            self._record(exc.prompt_tokens, exc.completion_tokens)
            raise
        self._record(response.prompt_tokens, response.completion_tokens)
        return response

    async def aclose(self) -> None:
        await self.provider.aclose()


class AgentLoop:
    """One-shot Agent-domain runner; TaskManager will own task scheduling in D5."""

    def __init__(
        self,
        provider: BaseLLMClient,
        tool_router: ToolRouter,
        *,
        reducer: StateReducer | None = None,
        context_manager: ContextManager | None = None,
        max_steps: int = 30,
        max_seconds: float = 900,
        max_tokens: int = 40_000,
        max_no_progress: int = 5,
        cleanup_timeout: float = 5,
        clock: Callable[[], float] = monotonic,
        browser_only: bool = False,
    ) -> None:
        if (
            max_steps < 1
            or max_seconds <= 0
            or max_tokens < 1
            or max_no_progress < 1
            or cleanup_timeout <= 0
        ):
            raise ValueError("AgentLoop limits must be positive")
        self.provider = provider
        self.tool_router = tool_router
        self.reducer = reducer or StateReducer()
        self.context_manager = context_manager or ContextManager(5)
        self.max_steps = max_steps
        self.max_seconds = max_seconds
        self.max_tokens = max_tokens
        self.max_no_progress = max_no_progress
        self.cleanup_timeout = cleanup_timeout
        self.clock = clock
        self.browser_only = browser_only
        self._used = False

    async def run(
        self,
        goal: str,
        *,
        cancellation: asyncio.Event | None = None,
        task_id: str | None = None,
        on_event: Callable[[AgentEvent], Awaitable[None]] | None = None,
    ) -> AgentRunResult:
        """Execute one bounded research task and return its terminal evidence."""

        if self._used:
            raise RuntimeError("AgentLoop is one-shot")
        self._used = True
        state = ResearchState(
            goal=goal,
            max_steps=self.max_steps,
            **({"task_id": task_id} if task_id else {}),
        )
        events: list[AgentEvent] = []
        meter = _MeteredProvider(self.provider, self.max_tokens)
        planner = PlannerService(meter, browser_only=self.browser_only)
        evaluator = EvaluatorService(meter)
        reporter = ReporterService(meter)
        started = self.clock()
        browser_started = False
        observation: dict[str, object] = {}
        previous_failed_action: tuple[object, ...] | None = None
        stop_reason: str | None = None

        async def emit(
            event_type: str, payload: dict[str, object] | None = None
        ) -> None:
            nonlocal state
            event = AgentEvent(
                task_id=state.task_id,
                event_type=event_type,
                step=state.step,
                payload=payload or {},
            )
            next_state = self.reducer.reduce(state, event)
            if on_event is not None:
                await on_event(event)
            state = next_state
            events.append(event)

        def usage_delta() -> dict[str, int]:
            return {
                "prompt_tokens": meter.prompt_tokens - state.prompt_tokens,
                "completion_tokens": meter.completion_tokens - state.completion_tokens,
            }

        def limit_reason() -> str | None:
            if cancellation is not None and cancellation.is_set():
                return "user_cancelled"
            if self.clock() - started >= self.max_seconds:
                return "time_limit"
            if meter.prompt_tokens + meter.completion_tokens >= self.max_tokens:
                return "token_budget"
            targets = parse_goal_targets(state.goal)
            if targets_met(targets, state.facts):
                return "target_count"
            if state.step >= state.max_steps:
                return "max_steps"
            if state.consecutive_no_progress_replans >= self.max_no_progress:
                return "no_progress"
            if state.subgoals and all(
                item.status == SubgoalStatus.COMPLETED for item in state.subgoals
            ):
                return (
                    "goal_satisfied"
                    if not targets and state.facts
                    else "insufficient_info"
                )
            return None

        async def bounded(awaitable: Awaitable[Any]) -> Any:
            remaining = self.max_seconds - (self.clock() - started)
            if remaining <= 0:
                if inspect.iscoroutine(awaitable):
                    awaitable.close()
                raise TimeoutError
            work = asyncio.ensure_future(awaitable)
            cancel_waiter = (
                asyncio.create_task(cancellation.wait())
                if cancellation is not None
                else None
            )
            try:
                waiting = {work}
                if cancel_waiter is not None:
                    waiting.add(cancel_waiter)
                done, _ = await asyncio.wait(
                    waiting, timeout=remaining, return_when=asyncio.FIRST_COMPLETED
                )
                if cancel_waiter is not None and cancel_waiter in done:
                    raise asyncio.CancelledError
                if work in done:
                    return work.result()
                raise TimeoutError
            finally:
                if not work.done():
                    work.cancel()
                    await asyncio.wait({work}, timeout=0.1)
                if cancel_waiter is not None:
                    cancel_waiter.cancel()

        pending_tool_result: ToolResult | None = None
        try:
            await emit("task_started")
            stop_reason = limit_reason()
            if stop_reason is None:
                subgoals = await bounded(planner.initialize(goal))
                await emit(
                    "subgoals_initialized",
                    {
                        "subgoals": [item.model_dump(mode="json") for item in subgoals],
                        **usage_delta(),
                    },
                )
            while stop_reason is None:
                stop_reason = limit_reason()
                if stop_reason is not None:
                    break
                if browser_started:
                    current = await bounded(self.tool_router.browser.observe("light"))
                    browser_view = (
                        current
                        if isinstance(current, dict)
                        else {
                            "url": getattr(current, "url", None),
                            "title": getattr(current, "title", None),
                            "dom_state": getattr(current, "dom_state", None),
                        }
                    )
                    observation = {**observation, **browser_view}
                context = await bounded(
                    self.context_manager.build(state, observation, events[-5:])
                )
                decision = await bounded(planner.next_step(state, observation, context))
                stop_reason = limit_reason()
                if stop_reason is not None:
                    break
                signature = (
                    decision.subgoal_id,
                    decision.tool,
                    decision.action,
                    decision.target,
                    decision.element_index,
                    decision.value,
                )
                if signature == previous_failed_action:
                    result = ToolResult(
                        tool=decision.tool,
                        action=decision.action,
                        success=False,
                        content="",
                        error_type=EvaluationErrorType.SEMANTIC,
                        error_message="Repeated unsuccessful action",
                    )
                else:
                    if decision.tool == "browser" and not browser_started:
                        await bounded(self.tool_router.browser.start_session())
                        browser_started = True
                    result = await bounded(self.tool_router.execute(decision, state))
                    pending_tool_result = result
                    if (
                        result.error_type == EvaluationErrorType.TECHNICAL
                        and limit_reason() is None
                    ):
                        result = await bounded(
                            self.tool_router.execute(decision, state)
                        )
                        pending_tool_result = result
                if signature == previous_failed_action:
                    pending_tool_result = result
                stop_reason = limit_reason()
                if stop_reason is not None:
                    break
                evaluation = await bounded(
                    evaluator.evaluate(state, decision, result, observation)
                )
                await emit(
                    "step_evaluated",
                    {
                        "decision": decision.model_dump(mode="json"),
                        "tool_result": result.model_dump(mode="json"),
                        "evaluation": evaluation.model_dump(mode="json"),
                        **usage_delta(),
                    },
                )
                pending_tool_result = None
                previous_failed_action = (
                    signature
                    if not evaluation.success
                    and evaluation.error_type
                    in {
                        EvaluationErrorType.SEMANTIC,
                        EvaluationErrorType.INSUFFICIENT_INFO,
                    }
                    else None
                )
                observation = {
                    "tool": result.tool,
                    "action": result.action,
                    "content": result.content,
                    "source_url": result.source_url,
                    "error_type": result.error_type,
                }
            if stop_reason == "user_cancelled" and not state.cancellation_requested:
                await emit("cancel_requested")
        except TimeoutError:
            stop_reason = "time_limit"
        except asyncio.CancelledError:
            stop_reason = "user_cancelled"
            if not state.cancellation_requested:
                await emit("cancel_requested")
        except LLMError as exc:
            stop_reason = "token_budget" if exc.kind == "budget" else "execution_error"
        except Exception:  # noqa: BLE001 - turn unhandled execution errors into a terminal result
            stop_reason = "execution_error"

        async def close_safely(close: Callable[[], Awaitable[None]]) -> bool:
            """Finish one resource close despite cancellation of the outer task."""

            nonlocal stop_reason
            close_task = asyncio.create_task(close())
            deadline = monotonic() + self.cleanup_timeout
            while not close_task.done():
                remaining = deadline - monotonic()
                if remaining <= 0:
                    close_task.cancel()
                    return False
                try:
                    await asyncio.wait({close_task}, timeout=remaining)
                except asyncio.CancelledError:
                    stop_reason = "user_cancelled"
            try:
                close_task.result()
            except asyncio.CancelledError:
                return False
            except Exception:  # noqa: BLE001 - retain terminal evidence on cleanup error
                return False
            return True

        cleanup_failed = False
        for close in (
            self.tool_router.browser.close_session,
            self.tool_router.github.aclose,
        ):
            if not await close_safely(close):
                cleanup_failed = True
        if cleanup_failed:
            stop_reason = "cleanup_error"
        stop_reason = stop_reason or "execution_error"
        status, level = self._terminal_outcome(stop_reason, bool(state.facts))
        provisional = ResearchState.model_validate(
            {
                **state.model_dump(),
                "status": status,
                "completion_level": level,
                "stop_reason": stop_reason,
            }
        )
        try:
            report_service = (
                ReporterService()
                if stop_reason in {"token_budget", "time_limit", "user_cancelled"}
                else reporter
            )
            report = (
                await bounded(report_service.generate(provisional))
                if report_service is reporter
                else await report_service.generate(provisional)
            )
        except TimeoutError:
            stop_reason = "time_limit"
            status, level = self._terminal_outcome(stop_reason, bool(state.facts))
            provisional = provisional.model_copy(
                update={
                    "status": status,
                    "completion_level": level,
                    "stop_reason": stop_reason,
                }
            )
            report = await ReporterService().generate(provisional)
        except asyncio.CancelledError:
            stop_reason = "user_cancelled"
            status, level = self._terminal_outcome(stop_reason, bool(state.facts))
            provisional = provisional.model_copy(
                update={
                    "status": status,
                    "completion_level": level,
                    "stop_reason": stop_reason,
                }
            )
            report = await ReporterService().generate(provisional)
        except Exception:  # noqa: BLE001 - preserve verified facts if report drafting fails
            report = await ReporterService().generate(provisional)
        if stop_reason != "user_cancelled":
            if self.clock() - started >= self.max_seconds:
                stop_reason = "time_limit"
            elif meter.prompt_tokens + meter.completion_tokens >= self.max_tokens:
                stop_reason = "token_budget"
            if stop_reason != provisional.stop_reason:
                status, level = self._terminal_outcome(stop_reason, bool(state.facts))
                provisional = provisional.model_copy(
                    update={
                        "status": status,
                        "completion_level": level,
                        "stop_reason": stop_reason,
                    }
                )
                report = await ReporterService().generate(provisional)
        if not await close_safely(meter.aclose):
            stop_reason = "cleanup_error"
        if (
            stop_reason != "cleanup_error"
            and cancellation is not None
            and cancellation.is_set()
        ):
            stop_reason = "user_cancelled"
        if stop_reason != provisional.stop_reason:
            status, level = self._terminal_outcome(stop_reason, bool(state.facts))
            provisional = provisional.model_copy(
                update={
                    "status": status,
                    "completion_level": level,
                    "stop_reason": stop_reason,
                }
            )
            report = await ReporterService().generate(provisional)
        if stop_reason == "user_cancelled" and not state.cancellation_requested:
            await emit("cancel_requested")
        await emit(
            "task_finished",
            {
                "status": status,
                "completion_level": level,
                "stop_reason": stop_reason,
                "report": report.model_dump(mode="json"),
                **usage_delta(),
            },
        )
        return AgentRunResult(
            state=state,
            report=report,
            events=tuple(events),
            pending_tool_result=pending_tool_result,
        )

    @staticmethod
    def _terminal_outcome(reason: str, has_facts: bool) -> tuple[ResearchStatus, str]:
        if reason == "user_cancelled":
            return ResearchStatus.CANCELLED, "partial" if has_facts else "none"
        if reason in {"execution_error", "cleanup_error"}:
            return ResearchStatus.FAILED, "none"
        if reason in {"goal_satisfied", "target_count"}:
            return ResearchStatus.COMPLETED, "full"
        return (
            (ResearchStatus.PARTIAL, "partial")
            if has_facts
            else (ResearchStatus.FAILED, "none")
        )
