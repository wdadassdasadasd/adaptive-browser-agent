"""Optional, content-free ledger boundary for external agent calls."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal, Protocol

from adaptive_research.agent.llm.base import LLMError, ProviderUsage
from adaptive_research.agent.state import ToolResult

CallKind = Literal["model", "tool"]
CallOutcome = Literal["completed", "failed"]


class CallObserver(Protocol):
    """Persist attempts using an implementation-bound task and fencing token.

    Operation names are fixed labels. Prompts, tool arguments and response bodies
    are deliberately absent from this interface.
    """

    async def started(self, kind: CallKind, operation: str) -> str: ...

    async def finished(
        self,
        call_id: str,
        outcome: CallOutcome,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        error_type: str | None = None,
        provider_usage: ProviderUsage | None = None,
    ) -> None: ...


class CallObservationError(RuntimeError):
    """The durable call ledger is unavailable or the execution lease was lost."""

    def __init__(
        self,
        message: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        super().__init__(message)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class UnknownCallOutcome(RuntimeError):
    """Transport failed after an external request may have reached its provider."""


class CallRecorder:
    def __init__(self, observer: CallObserver | None) -> None:
        self.observer = observer
        self.failed = False

    async def run[R](
        self, kind: CallKind, operation: str, call: Callable[[], Awaitable[R]]
    ) -> R:
        if self.failed:
            raise CallObservationError("Call ledger unavailable")
        if self.observer is None:
            return await call()
        try:
            call_id = await self.observer.started(kind, operation)
        except Exception as exc:
            self.failed = True
            raise CallObservationError("Call start could not be persisted") from exc
        if not call_id:
            self.failed = True
            raise CallObservationError("Call start returned no ID")
        try:
            result = await call()
        except asyncio.CancelledError:
            # The external action may have happened; reconciliation owns this start.
            self.failed = True
            raise
        except (TimeoutError, UnknownCallOutcome):
            # A timeout does not prove the remote side did nothing.
            self.failed = True
            raise
        except Exception as exc:
            prompt = exc.prompt_tokens if isinstance(exc, LLMError) else None
            completion = exc.completion_tokens if isinstance(exc, LLMError) else None
            error_type = exc.kind if isinstance(exc, LLMError) else type(exc).__name__
            await self._finish(
                call_id,
                "failed",
                prompt_tokens=prompt,
                completion_tokens=completion,
                error_type=error_type,
                provider_usage=(
                    exc.provider_usage if isinstance(exc, LLMError) else None
                ),
            )
            raise
        prompt = getattr(result, "prompt_tokens", None)
        completion = getattr(result, "completion_tokens", None)
        failed_tool = isinstance(result, ToolResult) and not result.success
        await self._finish(
            call_id,
            "failed" if failed_tool else "completed",
            prompt_tokens=prompt,
            completion_tokens=completion,
            error_type=(str(result.error_type) if failed_tool else None),
            provider_usage=getattr(result, "provider_usage", None),
        )
        return result

    async def _finish(
        self,
        call_id: str,
        outcome: CallOutcome,
        *,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        error_type: str | None,
        provider_usage: ProviderUsage | None = None,
    ) -> None:
        assert self.observer is not None
        try:
            if provider_usage is None:
                # Existing observers with explicit V1 signatures remain compatible.
                await self.observer.finished(
                    call_id,
                    outcome,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_type=error_type,
                )
            else:
                await self.observer.finished(
                    call_id,
                    outcome,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_type=error_type,
                    provider_usage=provider_usage,
                )
        except Exception as exc:
            self.failed = True
            raise CallObservationError(
                "Call outcome could not be persisted", prompt_tokens, completion_tokens
            ) from exc
