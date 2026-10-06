"""Environment-backed application configuration."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    deepseek_api_key: SecretStr | None = Field(
        default=None, validation_alias="DEEPSEEK_API_KEY"
    )
    github_token: SecretStr | None = Field(
        default=None, validation_alias="GITHUB_TOKEN"
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/adaptive_agent.db",
        validation_alias="DATABASE_URL",
    )
    max_concurrent_tasks: int = Field(
        default=2, ge=1, validation_alias="MAX_CONCURRENT_TASKS"
    )
    max_steps: int = Field(default=30, ge=1, validation_alias="MAX_STEPS")
    recent_trace_count: int = Field(
        default=5, ge=3, le=5, validation_alias="RECENT_TRACE_COUNT"
    )
    deepseek_model: str = Field(
        default="deepseek-chat", validation_alias="DEEPSEEK_MODEL"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable configuration snapshot."""

    return Settings()
