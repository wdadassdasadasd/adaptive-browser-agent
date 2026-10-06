"""Minimal tool routing boundary."""

from typing import Any

from adaptive_agent.adapters.browser_use_adapter import BrowserAction, BrowserUseAdapter
from adaptive_agent.state import PlanDecision
from adaptive_agent.tools.github_tool import GitHubTool


class ToolRouter:
    def __init__(self, browser: BrowserUseAdapter, github: GitHubTool) -> None:
        self.browser = browser
        self.github = github

    async def execute(self, decision: PlanDecision) -> dict[str, Any]:
        tool = decision.tool.lower()
        if tool == "browser":
            action = BrowserAction(
                action=decision.action,
                target=decision.target,
                element_index=decision.element_index,
                value=decision.value,
            )
            return await self.browser.execute(action)
        if tool == "github":
            return await self.github.execute(
                decision.action, decision.target, decision.value
            )
        raise ValueError(f"Unsupported tool: {decision.tool}")
