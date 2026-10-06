"""Benchmark metric contracts."""

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    steps: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    duplicate_urls: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    result_coverage: float = Field(default=0, ge=0, le=1)
