"""Construct one isolated research executor for a claimed task."""

from adaptive_research.agent.adapters.browser_use_adapter import BrowserUseAdapter
from adaptive_research.agent.agent_loop import AgentLoop
from adaptive_research.agent.context_manager import ContextManager
from adaptive_research.agent.llm.deepseek import DeepSeekClient
from adaptive_research.agent.tools.github_tool import GitHubTool
from adaptive_research.agent.tools.router import ToolRouter
from adaptive_research.infrastructure.config import Settings


def new_agent(settings: Settings) -> AgentLoop:
    provider = DeepSeekClient(
        settings.deepseek_api_key.get_secret_value()
        if settings.deepseek_api_key
        else None,
        model=settings.deepseek_model,
    )
    github = GitHubTool(
        token=settings.github_token.get_secret_value()
        if settings.github_token
        else None
    )
    return AgentLoop(
        provider,
        ToolRouter(BrowserUseAdapter(), github),
        context_manager=ContextManager(settings.recent_trace_count),
        max_steps=settings.max_steps,
    )
