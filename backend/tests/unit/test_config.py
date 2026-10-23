import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.llm.deepseek import DeepSeekClient
from adaptive_research.agent.state import ResearchState
from adaptive_research.application import agent_factory
from adaptive_research.infrastructure.config import REPOSITORY_ROOT, Settings


def test_recent_trace_count_defaults_to_bounded_v1_window() -> None:
    settings = Settings(_env_file=None)

    assert settings.recent_trace_count == 5

    with pytest.raises(ValidationError):
        Settings(_env_file=None, RECENT_TRACE_COUNT=10)


@pytest.mark.parametrize("recent_trace_count", [3, 5])
@pytest.mark.asyncio
async def test_agent_factory_uses_configured_recent_trace_count(
    monkeypatch, recent_trace_count: int
) -> None:
    # Construct the real loop without opening clients or a browser session.
    monkeypatch.setattr(
        agent_factory, "DeepSeekClient", lambda *args, **kwargs: object()
    )
    monkeypatch.setattr(agent_factory, "GitHubTool", lambda *args, **kwargs: object())
    monkeypatch.setattr(agent_factory, "BrowserUseAdapter", lambda: object())
    monkeypatch.setattr(agent_factory, "ToolRouter", lambda *args: object())

    monkeypatch.setenv("RECENT_TRACE_COUNT", str(recent_trace_count))
    settings = Settings(_env_file=None)
    agent = agent_factory.new_agent(settings)

    assert agent.context_manager.recent_trace_count == recent_trace_count
    assert agent.max_steps == settings.max_steps
    state = ResearchState(goal="Check context window")
    traces = [
        AgentEvent(
            task_id=state.task_id, event_type="step_evaluated", message=f"trace-{i}"
        )
        for i in range(5)
    ]
    context = json.loads(await agent.context_manager.build(state, {}, traces))
    assert [entry["message"] for entry in context["recent_traces"]] == [
        f"trace-{i}" for i in range(5 - recent_trace_count, 5)
    ]


def test_blank_credentials_are_treated_as_missing() -> None:
    settings = Settings(
        _env_file=None,
        DEEPSEEK_API_KEY=" \t ",
        GITHUB_TOKEN="",
        P01_DATABASE_URL=" ",
    )

    assert settings.deepseek_api_key is None
    assert settings.github_token is None
    assert settings.p01_database_url is None


@pytest.mark.asyncio
async def test_default_deepseek_model_matches_current_provider_name() -> None:
    settings = Settings(_env_file=None)
    provider = DeepSeekClient(None)
    try:
        assert settings.deepseek_model == "deepseek-flash"
        assert provider.model == settings.deepseek_model
    finally:
        await provider.aclose()


def test_sqlite_path_is_stable_across_working_directories(monkeypatch) -> None:
    expected = (REPOSITORY_ROOT / "data" / "relative-test.db").as_posix()
    for cwd in (REPOSITORY_ROOT, REPOSITORY_ROOT / "backend"):
        monkeypatch.chdir(cwd)
        settings = Settings(
            _env_file=None,
            DATABASE_URL="sqlite+aiosqlite:///./data/relative-test.db",
        )
        assert make_url(settings.database_url).database == expected
        assert Path(expected).is_absolute()


def test_postgres_runtime_requires_its_own_database_url() -> None:
    with pytest.raises(ValueError, match="P01_DATABASE_URL is required"):
        Settings(_env_file=None, P01_DATABASE_URL=None).require_postgres_url()
    with pytest.raises(ValueError, match="postgresql\\+asyncpg"):
        Settings(
            _env_file=None, P01_DATABASE_URL="sqlite+aiosqlite:///./data/test.db"
        ).require_postgres_url()
    url = "postgresql+asyncpg://user:private@127.0.0.1:5432/research"
    settings = Settings(_env_file=None, P01_DATABASE_URL=url)
    assert settings.require_postgres_url() == url
    assert "private" not in repr(settings)
