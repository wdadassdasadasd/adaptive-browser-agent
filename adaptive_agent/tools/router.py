"""Strict tool routing with pre-call duplicate suppression."""

from pydantic import ValidationError

from adaptive_agent.adapters.browser_use_adapter import BrowserAction, BrowserUseAdapter
from adaptive_agent.normalization import normalize_query, normalize_url
from adaptive_agent.state import (
    PlanDecision,
    ResearchState,
    ToolResult,
    require_http_url,
)
from adaptive_agent.tools.github_tool import GitHubTool

BROWSER_ACTIONS = {
    "navigate",
    "click",
    "input_text",
    "scroll",
    "extract",
    "go_back",
    "wait",
}
GITHUB_ACTIONS = {"search_repositories", "get_repository", "list_releases"}


class ToolRouter:
    def __init__(self, browser: BrowserUseAdapter, github: GitHubTool) -> None:
        self.browser = browser
        self.github = github

    async def execute(self, decision: PlanDecision, state: ResearchState) -> ToolResult:
        """Return one safe result; invalid or repeated requests never reach a tool."""

        if decision.tool == "browser":
            if decision.action not in BROWSER_ACTIONS:
                return self._replan(decision, "Unsupported browser action")
            try:
                action = BrowserAction(
                    action=decision.action,
                    target=decision.target,
                    element_index=decision.element_index,
                    value=decision.value,
                )
                if decision.action == "extract" and not (decision.target or "").strip():
                    raise ValueError("Extraction requires a question")
                if decision.action == "extract" and (
                    decision.element_index is not None or decision.value is not None
                ):
                    raise ValueError("Extraction takes only a question")
                if decision.action == "click" and decision.value is not None:
                    raise ValueError("Click takes no value")
                if decision.action == "scroll" and decision.value is not None:
                    raise ValueError("Scroll takes no value")
                if decision.action == "wait" and (
                    decision.target is not None or decision.element_index is not None
                ):
                    raise ValueError("Wait takes only seconds")
                if decision.action == "go_back" and any(
                    value is not None
                    for value in (
                        decision.target,
                        decision.element_index,
                        decision.value,
                    )
                ):
                    raise ValueError("go_back takes no parameters")
                if decision.action == "navigate":
                    assert decision.target is not None
                    if decision.element_index is not None or decision.value is not None:
                        raise ValueError("navigate takes only target")
                    require_http_url(decision.target)
            except (ValueError, ValidationError):
                return self._replan(decision, "Invalid browser action")
            if decision.action == "navigate" and normalize_url(decision.target) in {
                normalize_url(url) for url in state.visited_urls
            }:
                return self._replan(decision, "URL already visited")
            raw = await self.browser.execute(action)
            source_url = raw.get("url")
            if source_url == "about:blank":
                source_url = None
            return ToolResult(
                tool="browser",
                action=decision.action,
                success=raw["success"],
                content=raw.get("content", ""),
                source_url=source_url,
                error_type=raw.get("error_type", "none"),
                error_message=raw.get("error_message"),
            )
        if decision.action not in GITHUB_ACTIONS:
            return self._replan(decision, "Unsupported GitHub action")
        if decision.element_index is not None or decision.value is not None:
            return self._replan(decision, "GitHub action takes only target")
        if (
            decision.action == "search_repositories"
            and decision.target
            and normalize_query(decision.target)
            in {normalize_query(query) for query in state.search_history}
        ):
            return self._replan(decision, "Query already searched")
        resource_url = GitHubTool.resource_url(decision.action, decision.target)
        if resource_url and normalize_url(resource_url) in {
            normalize_url(url) for url in state.visited_urls
        }:
            return self._replan(decision, "GitHub resource already visited")
        return await self.github.execute(
            decision.action, decision.target, decision.value
        )

    @staticmethod
    def _replan(decision: PlanDecision, message: str) -> ToolResult:
        return ToolResult(
            tool=decision.tool,
            action=decision.action,
            success=False,
            content="",
            error_type="semantic",
            error_message=message,
        )
