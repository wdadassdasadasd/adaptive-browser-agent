"""Tool routing and pre-call duplicate suppression."""

from typing import Any

import pytest

from adaptive_research.agent.state import PlanDecision, ResearchState, ToolResult
from adaptive_research.agent.tools.router import ToolRouter


def decision(tool: str, action: str, target: str | None = None) -> PlanDecision:
    return PlanDecision(
        subgoal_id="s1",
        reasoning="next",
        tool=tool,
        action=action,
        target=target,
        expected_result="evidence",
    )


class FakeBrowser:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def execute(self, action: Any) -> dict[str, Any]:
        self.calls.append(action)
        return {
            "success": True,
            "action": action.action,
            "url": "https://example.com/",
            "content": "Page",
        }


class FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def execute(
        self, action: str, target: str | None, value: str | None
    ) -> ToolResult:
        self.calls.append((action, target, value))
        return ToolResult(
            tool="github",
            action=action,
            success=True,
            content="{}",
            source_url="https://api.github.com/search/repositories?q=fastapi",
        )


@pytest.mark.asyncio
async def test_browser_only_rejects_github_before_dispatch() -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    result = await ToolRouter(browser, github, browser_only=True).execute(
        decision("github", "search_repositories", "fastapi"),
        ResearchState(goal="research"),
    )
    assert result.error_type == "semantic"
    assert browser.calls == github.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "target", "index", "value"),
    [
        ("navigate", "https://example.com/", None, None),
        ("click", None, 1, None),
        ("input_text", None, 1, "FastAPI"),
        ("scroll", "down", None, None),
        ("extract", "What is FastAPI?", None, None),
        ("go_back", None, None, None),
        ("wait", None, None, "0"),
    ],
)
async def test_router_dispatches_each_browser_action(
    action: str, target: str | None, index: int | None, value: str | None
) -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    selected = decision("browser", action, target).model_copy(
        update={"element_index": index, "value": value}
    )
    result = await ToolRouter(browser, github).execute(
        selected, ResearchState(goal="research")
    )
    assert result.success and result.action == action
    assert len(browser.calls) == 1 and browser.calls[0].action == action
    assert github.calls == []


@pytest.mark.asyncio
async def test_router_suppresses_normalized_url_and_query_before_call() -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    router = ToolRouter(browser, github)
    state = ResearchState(
        goal="research",
        visited_urls=["https://EXAMPLE.com/path#old"],
        search_history=["fastapi browser"],
    )
    page = await router.execute(
        decision("browser", "navigate", "https://example.com/path#new"), state
    )
    search = await router.execute(
        decision("github", "search_repositories", "  FastAPI   Browser "), state
    )
    assert page.error_type == "semantic" and not page.success
    assert search.error_type == "semantic" and not search.success
    assert browser.calls == [] and github.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "visited_url"),
    [
        ("get_repository", "https://API.GITHUB.COM/repos/fastapi/fastapi#old"),
        (
            "list_releases",
            "https://API.GITHUB.COM/repos/fastapi/fastapi/releases?per_page=5#old",
        ),
    ],
)
async def test_router_suppresses_repeated_github_resource_before_call(
    action: str, visited_url: str
) -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    state = ResearchState(goal="research", visited_urls=[visited_url])

    result = await ToolRouter(browser, github).execute(
        decision("github", action, "fastapi/fastapi"), state
    )

    assert result.error_type == "semantic" and not result.success
    assert browser.calls == [] and github.calls == []


@pytest.mark.asyncio
async def test_router_maps_browser_result_and_rejects_unsupported_action() -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    router = ToolRouter(browser, github)
    state = ResearchState(goal="research")
    result = await router.execute(
        decision("browser", "navigate", "https://example.com/"), state
    )
    invalid = await router.execute(
        decision("github", "delete_repository", "owner/repo"), state
    )
    assert result == ToolResult(
        tool="browser",
        action="navigate",
        success=True,
        content="Page",
        source_url="https://example.com/",
    )
    assert invalid.error_type == "semantic" and not invalid.success
    assert len(browser.calls) == 1 and github.calls == []


@pytest.mark.asyncio
async def test_router_rejects_go_back_with_unexpected_target_without_browser_call() -> (
    None
):
    browser, github = FakeBrowser(), FakeGitHub()
    result = await ToolRouter(browser, github).execute(
        decision("browser", "go_back", "https://unexpected.example/"),
        ResearchState(goal="research"),
    )
    assert result.error_type == "semantic" and browser.calls == []


@pytest.mark.asyncio
async def test_router_rejects_unused_github_value_without_tool_call() -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    selected = decision("github", "get_repository", "fastapi/fastapi").model_copy(
        update={"value": "unused"}
    )
    result = await ToolRouter(browser, github).execute(
        selected, ResearchState(goal="research")
    )
    assert result.error_type == "semantic" and github.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "target", "index", "value"),
    [
        ("click", "Search", None, "ignored"),
        ("extract", "Question", 1, None),
        ("wait", "unexpected", None, "1"),
        ("scroll", "down", None, "ignored"),
    ],
)
async def test_router_rejects_unused_browser_parameters_without_call(
    action: str, target: str | None, index: int | None, value: str | None
) -> None:
    browser, github = FakeBrowser(), FakeGitHub()
    selected = decision("browser", action, target).model_copy(
        update={"element_index": index, "value": value}
    )
    result = await ToolRouter(browser, github).execute(
        selected, ResearchState(goal="research")
    )
    assert result.error_type == "semantic" and browser.calls == []


@pytest.mark.asyncio
async def test_wait_on_blank_tab_has_structured_result_without_source() -> None:
    class BlankBrowser(FakeBrowser):
        async def execute(self, action: Any) -> dict[str, Any]:
            self.calls.append(action)
            return {
                "success": True,
                "action": action.action,
                "url": "about:blank",
                "content": "Waited",
            }

    browser, github = BlankBrowser(), FakeGitHub()
    selected = decision("browser", "wait")
    result = await ToolRouter(browser, github).execute(
        selected, ResearchState(goal="research")
    )

    assert result.success and result.source_url is None
    assert len(browser.calls) == 1 and github.calls == []
