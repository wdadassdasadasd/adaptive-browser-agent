"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
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

    @field_validator(
        "deepseek_api_key", "github_token", "p01_database_url", mode="before"
    )
    @classmethod
    def blank_credential_is_missing(cls, value: object) -> object:
        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if isinstance(raw, str) and not raw.strip():
            return None
        return value

    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{(REPOSITORY_ROOT / 'data' / 'adaptive_agent.db').as_posix()}",
        validation_alias="DATABASE_URL",
    )

    p01_database_url: SecretStr | None = Field(
        default=None, validation_alias="P01_DATABASE_URL"
    )

    def require_postgres_url(self) -> str:
        """Fail closed for the independent API/Worker runtime."""

        if self.p01_database_url is None:
            raise ValueError("P01_DATABASE_URL is required for the PostgreSQL runtime")
        value = self.p01_database_url.get_secret_value()
        if make_url(value).drivername != "postgresql+asyncpg":
            raise ValueError("P01_DATABASE_URL must use postgresql+asyncpg")
        return value

    @field_validator("database_url")
    @classmethod
    def anchor_sqlite_database_to_repository(cls, value: str) -> str:
        """Keep an explicit relative SQLite URL stable across working directories."""

        url = make_url(value)
        if (
            url.get_backend_name() != "sqlite"
            or not url.database
            or url.database == ":memory:"
        ):
            return value
        database = Path(url.database)
        if database.is_absolute():
            return value
        return url.set(
            database=(REPOSITORY_ROOT / database).resolve().as_posix()
        ).render_as_string(hide_password=False)

    max_concurrent_tasks: int = Field(
        default=2, ge=1, validation_alias="MAX_CONCURRENT_TASKS"
    )
    max_steps: int = Field(default=30, ge=1, validation_alias="MAX_STEPS")
    recent_trace_count: int = Field(
        default=5, ge=3, le=5, validation_alias="RECENT_TRACE_COUNT"
    )
    deepseek_model: str = Field(
        default="deepseek-flash", validation_alias="DEEPSEEK_MODEL"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable configuration snapshot."""

    return Settings()
