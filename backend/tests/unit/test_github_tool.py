"""GitHub REST boundary against a controlled HTTP transport."""

import asyncio
import json

import httpx
import pytest

from adaptive_research.agent.tools.github_tool import GitHubTool


@pytest.mark.asyncio
async def test_github_search_uses_fixed_host_and_observed_api_source() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "total_count": 1,
                "items": [
                    {
                        "full_name": "fastapi/fastapi",
                        "html_url": "https://github.com/fastapi/fastapi",
                        "description": "FastAPI framework",
                        "stargazers_count": 100,
                    }
                ],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    tool = GitHubTool(client=client)
    result = await tool.execute("search_repositories", "FastAPI", None)
    assert result.success and result.source_url == str(requests[0].url)
    assert requests[0].url.host == "api.github.com"
    assert requests[0].url.path == "/search/repositories"
    assert "fastapi/fastapi" in result.content
    await tool.aclose()
    assert not client.is_closed
    await client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "kind"),
    [(404, "insufficient_info"), (429, "technical"), (503, "technical")],
)
async def test_github_http_failures_are_structured_and_not_retried(
    status: int, kind: str
) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={"message": "secret server text"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await GitHubTool(client=client).execute(
            "get_repository", "fastapi/fastapi", None
        )
    assert not result.success and result.error_type == kind
    assert calls == 1 and "secret server text" not in str(result)


@pytest.mark.asyncio
async def test_github_rejects_malformed_target_without_request() -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await GitHubTool(client=client).execute(
            "list_releases", "../admin", None
        )
    assert result.error_type == "semantic" and calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "path", "payload"),
    [
        (
            "get_repository",
            "/repos/fastapi/fastapi",
            {
                "full_name": "fastapi/fastapi",
                "html_url": "https://github.com/fastapi/fastapi",
            },
        ),
        (
            "list_releases",
            "/repos/fastapi/fastapi/releases",
            [
                {
                    "tag_name": "v1.0",
                    "html_url": "https://github.com/fastapi/fastapi/releases/tag/v1.0",
                }
            ],
        ),
    ],
)
async def test_github_repository_paths_and_content(
    action: str, path: str, payload: object
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await GitHubTool(client=client).execute(
            action, "fastapi/fastapi", None
        )
    assert result.success and requests[0].url.path == path
    assert result.source_url == str(requests[0].url)
    assert "fastapi/fastapi" in result.content
    if action == "list_releases":
        assert requests[0].url.params.get_list("per_page") == ["5"]


@pytest.mark.asyncio
async def test_github_timeout_is_technical_and_owned_client_closes() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(timeout))
    tool = GitHubTool(client=client)
    result = await tool.execute("search_repositories", "FastAPI", None)
    assert result.error_type == "technical"
    await tool.aclose()
    assert not client.is_closed
    await client.aclose()


@pytest.mark.asyncio
async def test_github_large_release_body_stays_bounded_json() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"tag_name": "v1", "body": "\\" * 20000}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await GitHubTool(client=client).execute(
            "list_releases", "fastapi/fastapi", None
        )
    assert result.success and len(result.content) <= 12000
    releases = json.loads(result.content)
    assert isinstance(releases, list) and releases[0]["tag_name"] == "v1"
    assert result.metadata["truncated"] is True


@pytest.mark.asyncio
async def test_github_cancel_propagates_and_owned_client_can_close() -> None:
    def cancel(request: httpx.Request) -> httpx.Response:
        raise asyncio.CancelledError

    async with httpx.AsyncClient(transport=httpx.MockTransport(cancel)) as client:
        tool = GitHubTool(client=client)
        with pytest.raises(asyncio.CancelledError):
            await tool.execute("search_repositories", "FastAPI", None)
        await tool.aclose()
        assert not client.is_closed
    owned = GitHubTool()
    await owned.aclose()
    assert owned.client.is_closed
