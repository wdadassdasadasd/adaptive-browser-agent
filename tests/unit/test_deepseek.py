"""Fake-transport coverage for the DeepSeek provider boundary."""

import asyncio
import json

import httpx
import pytest
from pydantic import BaseModel

from adaptive_agent.llm.base import LLMError, StructuredOutputError
from adaptive_agent.llm.deepseek import DeepSeekClient


class Answer(BaseModel):
    name: str


def response(content: str, prompt: int = 4, completion: int = 2) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
        },
    )


@pytest.mark.asyncio
async def test_missing_credential_fails_before_network_request() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response("unexpected")

    provider = DeepSeekClient(None, transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError, match="DEEPSEEK_API_KEY") as caught:
        await provider.complete("Prompt")
    assert caught.value.kind == "configuration"
    assert calls == 0
    await provider.aclose()


@pytest.mark.asyncio
async def test_structured_completion_sends_json_request_and_reports_usage() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response('{"name":"FastAPI"}', 11, 5)

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    result = await provider.complete_structured("Return JSON", Answer)
    assert result.value == Answer(name="FastAPI")
    assert (result.prompt_tokens, result.completion_tokens) == (11, 5)
    assert len(seen) == 1
    assert seen[0].url.path.endswith("/chat/completions")
    assert seen[0].headers["authorization"] == "Bearer secret-sentinel"
    assert seen[0].read().count(b"json_object") == 1
    await provider.aclose()
    assert provider.client.is_closed


@pytest.mark.asyncio
async def test_plain_completion_returns_text_and_actual_usage() -> None:
    provider = DeepSeekClient(
        "key", transport=httpx.MockTransport(lambda _: response("Hello", 3, 1))
    )
    result = await provider.complete("Say hello")
    assert (result.text, result.prompt_tokens, result.completion_tokens) == (
        "Hello",
        3,
        1,
    )
    await provider.aclose()


@pytest.mark.asyncio
async def test_budgeted_structured_call_caps_generated_tokens() -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return response('{"name":"FastAPI"}', 20, 5)

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))

    result = await provider.complete_structured_budgeted("Return JSON", Answer, 2000)

    assert result.value.name == "FastAPI"
    assert len(bodies) == 1
    assert 1 <= bodies[0]["max_tokens"] < 2000
    assert bodies[0]["max_tokens"] + result.prompt_tokens < 2000
    await provider.aclose()


@pytest.mark.asyncio
async def test_budgeted_chinese_prompt_uses_utf8_request_size() -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return response('{"name":"FastAPI"}', 20, 5)

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))

    result = await provider.complete_structured_budgeted("项目" * 4000, Answer, 40_000)

    assert result.value.name == "FastAPI"
    assert len(bodies) == 1
    assert 0 < bodies[0]["max_tokens"]
    assert bodies[0]["max_tokens"] + result.prompt_tokens < 40_000
    await provider.aclose()


@pytest.mark.asyncio
async def test_budgeted_prompt_too_large_makes_no_request() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response("unexpected")

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))

    with pytest.raises(LLMError) as caught:
        await provider.complete_structured_budgeted("Long prompt" * 100, Answer, 10)

    assert caught.value.kind == "budget"
    assert calls == 0
    await provider.aclose()


@pytest.mark.asyncio
async def test_budgeted_repair_uses_smaller_remaining_allowance() -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return response("{}" if len(bodies) == 1 else '{"name":"FastAPI"}', 8, 4)

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))

    result = await provider.complete_structured_budgeted("Return JSON", Answer, 5000)

    assert result.value.name == "FastAPI"
    assert (result.prompt_tokens, result.completion_tokens) == (16, 8)
    assert len(bodies) == 2
    assert bodies[1]["max_tokens"] < bodies[0]["max_tokens"]
    await provider.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["timeout", 429, 500, 503])
async def test_temporary_failure_retries_once_then_succeeds(failure: str | int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            if failure == "timeout":
                raise httpx.ReadTimeout("secret-sentinel", request=request)
            return httpx.Response(failure, text="secret-sentinel")
        return response("ok")

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    assert (await provider.complete("Prompt")).text == "ok"
    assert calls == 2
    await provider.aclose()


@pytest.mark.asyncio
async def test_repeated_timeout_is_bounded_and_redacted() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("secret-sentinel", request=request)

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError) as caught:
        await provider.complete("Prompt")
    assert calls == 2
    assert caught.value.kind == "technical"
    assert "secret-sentinel" not in str(caught.value)
    await provider.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 500, 503])
async def test_repeated_temporary_http_failure_stops_after_two_requests(
    status: int,
) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, text="secret-sentinel")

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError, match="temporary") as caught:
        await provider.complete("Prompt")
    assert calls == 2
    assert caught.value.kind == "technical"
    assert "secret-sentinel" not in str(caught.value)
    await provider.aclose()
    assert provider.client.is_closed


@pytest.mark.asyncio
async def test_authentication_error_is_not_retried_or_leaked() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, text="secret-sentinel")

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError) as caught:
        await provider.complete("Prompt")
    assert calls == 1
    assert caught.value.kind == "rejected"
    assert "secret-sentinel" not in str(caught.value)
    await provider.aclose()


@pytest.mark.asyncio
async def test_invalid_output_gets_one_separate_repair_and_sums_usage() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return (
            response("not json", 4, 2)
            if calls == 1
            else response('{"name":"Flask"}', 7, 3)
        )

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    result = await provider.complete_structured("Return JSON", Answer)
    assert result.value.name == "Flask"
    assert (result.prompt_tokens, result.completion_tokens) == (11, 5)
    assert calls == 2
    await provider.aclose()


@pytest.mark.asyncio
async def test_structured_initial_and_repair_prompts_include_schema_fields() -> None:
    prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        prompts.append(request.read().decode())
        return response("{}" if len(prompts) == 1 else '{"name":"FastAPI"}')

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    result = await provider.complete_structured("Return JSON", Answer)
    assert result.value.name == "FastAPI"
    assert len(prompts) == 2
    assert all('\\"name\\"' in prompt for prompt in prompts)
    await provider.aclose()


@pytest.mark.asyncio
async def test_final_invalid_output_has_bounded_attempts_and_known_usage() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response("not json", 4, 2)

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    with pytest.raises(StructuredOutputError) as caught:
        await provider.complete_structured("Return JSON", Answer)
    assert calls == 2
    assert caught.value.kind == "structured"
    assert (caught.value.prompt_tokens, caught.value.completion_tokens) == (8, 4)
    await provider.aclose()


@pytest.mark.asyncio
async def test_repair_request_has_own_single_technical_retry() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return response("{}")
        if calls == 2:
            return httpx.Response(429)
        return response('{"name":"Done"}')

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    result = await provider.complete_structured("Return JSON", Answer)
    assert result.value.name == "Done"
    assert calls == 3
    await provider.aclose()


@pytest.mark.asyncio
async def test_repair_technical_failure_preserves_initial_usage_and_stops() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return response("not json", 5, 2)
        return httpx.Response(429, text="secret-sentinel")

    provider = DeepSeekClient("secret-sentinel", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError, match="repair") as caught:
        await provider.complete_structured("Prompt", Answer)
    assert calls == 3
    assert caught.value.kind == "technical"
    assert (caught.value.prompt_tokens, caught.value.completion_tokens) == (5, 2)
    assert "secret-sentinel" not in str(caught.value)
    await provider.aclose()


@pytest.mark.asyncio
async def test_cancelled_request_propagates_and_owned_client_closes() -> None:
    started = asyncio.Event()

    async def handler(_: httpx.Request) -> httpx.Response:
        started.set()
        await asyncio.Event().wait()
        return response("unreachable")

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    task = asyncio.create_task(provider.complete("Prompt"))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await provider.aclose()
    assert provider.client.is_closed


@pytest.mark.asyncio
async def test_injected_client_remains_open_on_provider_close() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response("ok")))
    provider = DeepSeekClient("key", client=client)
    await provider.aclose()
    assert not client.is_closed
    await client.aclose()


@pytest.mark.asyncio
async def test_injected_client_without_base_url_uses_fixed_provider_endpoint() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response("ok")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = DeepSeekClient("key", client=client)
    try:
        result = await provider.complete("Prompt")
        assert result.text == "ok"
        assert len(seen) == 1
        assert str(seen[0].url) == "https://api.deepseek.com/chat/completions"
    finally:
        await provider.aclose()
        await client.aclose()


@pytest.mark.asyncio
async def test_invalid_response_preserves_known_usage_without_inventing_missing_usage() -> (
    None
):
    responses = [
        httpx.Response(
            200,
            json={
                "choices": [{}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 2},
            },
        ),
        httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
    ]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        result = responses[calls]
        calls += 1
        return result

    provider = DeepSeekClient("key", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError) as known:
        await provider.complete("First")
    assert known.value.kind == "invalid_response"
    assert (known.value.prompt_tokens, known.value.completion_tokens) == (9, 2)
    with pytest.raises(LLMError) as unknown:
        await provider.complete("Second")
    assert unknown.value.kind == "invalid_response"
    assert (unknown.value.prompt_tokens, unknown.value.completion_tokens) == (
        None,
        None,
    )
    assert calls == 2
    await provider.aclose()
