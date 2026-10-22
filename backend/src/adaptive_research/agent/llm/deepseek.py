"""Bounded DeepSeek chat completions over an owned or injected HTTP client."""

import json

import httpx
from pydantic import TypeAdapter, ValidationError

from adaptive_research.agent.call_observer import (
    CallObservationError,
    CallRecorder,
    UnknownCallOutcome,
)
from adaptive_research.agent.llm.base import (
    LLMCompletion,
    LLMError,
    ProviderUsage,
    StructuredCompletion,
    StructuredOutputError,
    T,
)


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None,
        model: str = "deepseek-flash",
        client: httpx.AsyncClient | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if client is not None and transport is not None:
            raise ValueError("provide either client or transport")
        self.api_key = api_key
        self.model = model
        self._recorder: CallRecorder | None = None
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url="https://api.deepseek.com", timeout=60, transport=transport
        )

    def bind_call_recorder(self, recorder: CallRecorder) -> None:
        """Record each physical HTTP request, including JSON repair requests."""

        self._recorder = recorder

    async def complete(self, prompt: str) -> LLMCompletion:
        return await self._request(prompt, structured=False)

    async def complete_budgeted(
        self, prompt: str, remaining_tokens: int
    ) -> LLMCompletion:
        """Bound terminal reporting calls by the same task allowance."""
        return await self._request(
            prompt, structured=False, remaining_tokens=remaining_tokens
        )

    async def complete_structured(
        self, prompt: str, schema: type[T]
    ) -> StructuredCompletion[T]:
        return await self._complete_structured(prompt, schema, None)

    async def complete_structured_budgeted(
        self, prompt: str, schema: type[T], remaining_tokens: int
    ) -> StructuredCompletion[T]:
        """Bound output from the conservative remaining task-token allowance."""

        return await self._complete_structured(prompt, schema, remaining_tokens)

    async def _complete_structured(
        self, prompt: str, schema: type[T], remaining_tokens: int | None
    ) -> StructuredCompletion[T]:
        schema_prompt = (
            f"{prompt}\n\nReturn JSON matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )
        first = await self._request(
            schema_prompt, structured=True, remaining_tokens=remaining_tokens
        )
        adapter = TypeAdapter(schema)
        try:
            value = adapter.validate_json(first.text)
        except (ValidationError, ValueError):
            repair_prompt = (
                f"Original request:\n{schema_prompt}\n\nThe previous response did not match the required JSON schema. "
                f"Return only corrected JSON matching {schema.__name__}. Previous response:\n"
                f"{first.text[:4000]}"
            )
            try:
                repair = await self._request(
                    repair_prompt,
                    structured=True,
                    remaining_tokens=(
                        remaining_tokens - first.prompt_tokens - first.completion_tokens
                        if remaining_tokens is not None
                        else None
                    ),
                )
            except LLMError as exc:
                raise LLMError(
                    "structured repair request failed",
                    first.prompt_tokens + (exc.prompt_tokens or 0),
                    first.completion_tokens + (exc.completion_tokens or 0),
                    kind=exc.kind,
                    provider_usage=exc.provider_usage,
                ) from None
            except CallObservationError as exc:
                raise CallObservationError(
                    "Structured repair outcome could not be persisted",
                    first.prompt_tokens + (exc.prompt_tokens or 0),
                    first.completion_tokens + (exc.completion_tokens or 0),
                ) from exc
            prompt_tokens = first.prompt_tokens + repair.prompt_tokens
            completion_tokens = first.completion_tokens + repair.completion_tokens
            try:
                value = adapter.validate_json(repair.text)
            except (ValidationError, ValueError):
                raise StructuredOutputError(
                    "structured output invalid after repair",
                    prompt_tokens,
                    completion_tokens,
                    kind="structured",
                ) from None
            return StructuredCompletion(value, prompt_tokens, completion_tokens)
        return StructuredCompletion(value, first.prompt_tokens, first.completion_tokens)

    async def _request(
        self,
        prompt: str,
        *,
        structured: bool,
        remaining_tokens: int | None = None,
    ) -> LLMCompletion:
        if not self.api_key:
            raise LLMError(
                "DEEPSEEK_API_KEY is required for DeepSeek requests",
                kind="configuration",
            )
        body: dict[str, object] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return valid JSON only."
                    if structured
                    else "Answer the user.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        if structured:
            body["response_format"] = {"type": "json_object"}
        if remaining_tokens is not None:
            # Use UTF-8 bytes without ASCII escapes as a conservative prompt
            # bound; JSON escaping would reject ordinary Chinese context.
            prompt_bound = (
                len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 128
            )
            output_allowance = remaining_tokens - prompt_bound
            if output_allowance < 1:
                raise LLMError("remaining token budget is too small", kind="budget")
            body["max_tokens"] = output_allowance
        for attempt in range(2):
            try:
                return (
                    await self._recorder.run(
                        "model",
                        "deepseek.chat_completion",
                        lambda: self._request_once(body),
                    )
                    if self._recorder is not None
                    else await self._request_once(body)
                )
            except httpx.RequestError:
                if attempt == 0:
                    continue
                raise LLMError(
                    "temporary DeepSeek request failure", kind="technical"
                ) from None
            except LLMError as exc:
                if attempt == 0 and exc.kind == "technical":
                    continue
                raise
        raise AssertionError("unreachable retry state")

    async def _request_once(self, body: dict[str, object]) -> LLMCompletion:
        try:
            response = await self.client.post(
                "https://api.deepseek.com/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        except httpx.RequestError:
            if self._recorder is not None:
                raise UnknownCallOutcome(
                    "Provider transport outcome is unknown"
                ) from None
            raise
        if response.status_code == 429 or response.status_code >= 500:
            raise LLMError("temporary DeepSeek service failure", kind="technical")
        if response.status_code >= 400:
            raise LLMError(
                f"DeepSeek request rejected with HTTP {response.status_code}",
                kind="rejected",
            )
        try:
            data = response.json()
        except ValueError:
            raise LLMError(
                "invalid DeepSeek response", kind="invalid_response"
            ) from None
        provider_usage = self._provider_usage(data)
        try:
            usage = data["usage"]
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            if any(
                type(value) is not int or value < 0
                for value in (prompt_tokens, completion_tokens)
            ):
                raise TypeError("usage")
        except (ValueError, TypeError, KeyError, IndexError):
            raise LLMError(
                "invalid DeepSeek response",
                kind="invalid_response",
                provider_usage=provider_usage,
            ) from None
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("content")
        except (TypeError, KeyError, IndexError):
            raise LLMError(
                "invalid DeepSeek response",
                prompt_tokens,
                completion_tokens,
                kind="invalid_response",
                provider_usage=provider_usage,
            ) from None
        return LLMCompletion(content, prompt_tokens, completion_tokens, provider_usage)

    @staticmethod
    def _provider_usage(data: object) -> ProviderUsage | None:
        if not isinstance(data, dict):
            return None
        usage = data.get("usage")
        usage = usage if isinstance(usage, dict) else {}

        def count(value: object, maximum: int = 2**31 - 1) -> int | None:
            return value if type(value) is int and 0 <= value <= maximum else None

        def label(value: object, maximum: int) -> str | None:
            return (
                value
                if isinstance(value, str) and value.strip() and len(value) <= maximum
                else None
            )

        metadata = ProviderUsage(
            prompt_cache_hit_tokens=count(usage.get("prompt_cache_hit_tokens")),
            prompt_cache_miss_tokens=count(usage.get("prompt_cache_miss_tokens")),
            provider_created_at=count(data.get("created"), 2**63 - 1),
            reported_model=label(data.get("model"), 128),
            system_fingerprint=label(data.get("system_fingerprint"), 256),
        )
        return (
            metadata
            if any(value is not None for value in vars(metadata).values())
            else None
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
