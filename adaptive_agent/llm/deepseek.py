"""Bounded DeepSeek chat completions over an owned or injected HTTP client."""

import json

import httpx
from pydantic import TypeAdapter, ValidationError

from adaptive_agent.llm.base import (
    LLMCompletion,
    LLMError,
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
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url="https://api.deepseek.com", timeout=60, transport=transport
        )

    async def complete(self, prompt: str) -> LLMCompletion:
        return await self._request(prompt, structured=False)

    async def complete_structured(
        self, prompt: str, schema: type[T]
    ) -> StructuredCompletion[T]:
        schema_prompt = (
            f"{prompt}\n\nReturn JSON matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )
        first = await self._request(schema_prompt, structured=True)
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
                repair = await self._request(repair_prompt, structured=True)
            except LLMError as exc:
                raise LLMError(
                    "structured repair request failed",
                    first.prompt_tokens + (exc.prompt_tokens or 0),
                    first.completion_tokens + (exc.completion_tokens or 0),
                    kind=exc.kind,
                ) from None
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

    async def _request(self, prompt: str, *, structured: bool) -> LLMCompletion:
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
        for attempt in range(2):
            try:
                response = await self.client.post(
                    "https://api.deepseek.com/chat/completions",
                    json=body,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            except httpx.RequestError:
                if attempt == 0:
                    continue
                raise LLMError(
                    "temporary DeepSeek request failure", kind="technical"
                ) from None
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 0:
                    continue
                raise LLMError("temporary DeepSeek service failure", kind="technical")
            if response.status_code >= 400:
                raise LLMError(
                    f"DeepSeek request rejected with HTTP {response.status_code}",
                    kind="rejected",
                )
            try:
                data = response.json()
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
                    "invalid DeepSeek response", kind="invalid_response"
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
                ) from None
            return LLMCompletion(content, prompt_tokens, completion_tokens)
        raise AssertionError("unreachable retry state")

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
