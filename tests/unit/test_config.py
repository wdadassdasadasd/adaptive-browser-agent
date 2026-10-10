import pytest
from pydantic import ValidationError

from adaptive_agent.llm.deepseek import DeepSeekClient
from backend.config import Settings


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
    )

    assert settings.deepseek_api_key is None
    assert settings.github_token is None


@pytest.mark.asyncio
async def test_default_deepseek_model_matches_current_provider_name() -> None:
    settings = Settings(_env_file=None)
    provider = DeepSeekClient(None)
    try:
        assert settings.deepseek_model == "deepseek-flash"
        assert provider.model == settings.deepseek_model
    finally:
        await provider.aclose()
