from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from adaptive_research.agent.llm.deepseek import DeepSeekClient
from adaptive_research.infrastructure.config import REPOSITORY_ROOT, Settings


def test_recent_trace_count_defaults_to_bounded_v1_window() -> None:
    settings = Settings(_env_file=None)

    assert settings.recent_trace_count == 5

    with pytest.raises(ValidationError):
        Settings(_env_file=None, RECENT_TRACE_COUNT=10)


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
