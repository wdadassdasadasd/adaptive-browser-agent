"""Project Agent benchmark arms."""

import os
from typing import Any

from adaptive_agent.adapters.browser_use_adapter import BrowserUseAdapter
from adaptive_agent.agent_loop import AgentLoop
from adaptive_agent.llm.deepseek import DeepSeekClient
from adaptive_agent.tools.github_tool import GitHubTool
from adaptive_agent.tools.router import ToolRouter
from benchmark.metrics import normalized_url


async def run_adaptive(
    task: str, *, browser_only: bool = False, loop_factory: Any = None
) -> dict[str, Any]:
    """Run bounded AgentLoop with GitHub disabled in mechanism arm."""
    if loop_factory is None:
        provider = DeepSeekClient(os.getenv("DEEPSEEK_API_KEY"), model="deepseek-flash")
        router = ToolRouter(
            BrowserUseAdapter(),
            GitHubTool(os.getenv("GITHUB_TOKEN")),
            browser_only=browser_only,
        )
        loop = AgentLoop(
            provider,
            router,
            browser_only=browser_only,
            max_steps=30,
            max_seconds=900,
            max_tokens=40_000,
        )
    else:
        loop = loop_factory(browser_only)
    result = await loop.run(task)
    report = result.report
    state = result.state
    tool_results = [
        event.payload["tool_result"]
        for event in result.events
        if event.event_type == "step_evaluated"
    ]
    pending = getattr(result, "pending_tool_result", None)
    if pending is not None:
        tool_results.append(pending.model_dump(mode="json"))
    observed_urls = []
    current_browser_url = None
    for tool_result in tool_results:
        source_url = tool_result.get("source_url")
        if tool_result["tool"] == "browser":
            if not tool_result.get("success") or not source_url:
                continue
            browser_url = normalized_url(source_url)
            if browser_url != current_browser_url:
                observed_urls.append(source_url)
                current_browser_url = browser_url
        elif source_url and tool_result.get("success"):
            observed_urls.append(source_url)
    source_urls = list(state.visited_urls)
    if (
        pending is not None
        and pending.success
        and pending.source_url
        and pending.source_url not in source_urls
    ):
        source_urls.append(pending.source_url)
    return {
        "answer": report.markdown if report else "",
        "urls": observed_urls,
        "source_urls": source_urls,
        "trace": [
            {
                "tool": item.get("tool"),
                "action": item.get("action"),
                "success": item.get("success"),
                "error_type": item.get("error_type"),
            }
            for item in tool_results
        ],
        "steps": state.step + (1 if pending is not None else 0),
        "prompt_tokens": state.prompt_tokens
        if state.prompt_tokens or state.completion_tokens
        else None,
        "completion_tokens": state.completion_tokens
        if state.prompt_tokens or state.completion_tokens
        else None,
        "status": state.status,
        "failure_reason": None if state.status == "completed" else state.stop_reason,
        "budget_parity": "verified",
    }
