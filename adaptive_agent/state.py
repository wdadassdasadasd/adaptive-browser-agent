"""Long-lived domain state for the adaptive research loop."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def new_id() -> str:
    """Return a storage-friendly UUID string."""

    return str(uuid4())


class StrictModel(BaseModel):
    """Base model that rejects accidental runtime-only fields."""

    model_config = ConfigDict(extra="forbid")


class SubgoalStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationErrorType(StrEnum):
    NONE = "none"
    TECHNICAL = "technical"
    SEMANTIC = "semantic"
    INSUFFICIENT_INFO = "insufficient_info"


class Subgoal(StrictModel):
    id: str = Field(default_factory=new_id)
    description: str = Field(min_length=1)
    status: SubgoalStatus = SubgoalStatus.PENDING
    priority: int = 0


class ResearchFact(StrictModel):
    id: str = Field(default_factory=new_id)
    subgoal_id: str | None = None
    content: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    evidence: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: datetime = Field(default_factory=utc_now)


class ResearchState(StrictModel):
    """Durable agent state only; runtime resources deliberately do not belong here."""

    task_id: str = Field(default_factory=new_id)
    goal: str = Field(min_length=1)
    status: ResearchStatus = ResearchStatus.PENDING
    step: int = Field(default=0, ge=0)
    max_steps: int = Field(default=30, ge=1)
    subgoals: list[Subgoal] = Field(default_factory=list)
    facts: list[ResearchFact] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    search_history: list[str] = Field(default_factory=list)
    current_subgoal_id: str | None = None
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cancellation_requested: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PlanDecision(StrictModel):
    subgoal_id: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    tool: Literal["browser", "github"]
    action: str = Field(min_length=1)
    target: str | None = None
    element_index: int | None = Field(default=None, ge=0)
    value: str | None = None
    expected_result: str = Field(min_length=1)


class EvaluationResult(StrictModel):
    success: bool
    reason: str = Field(min_length=1)
    subgoal_completed: bool = False
    should_replan: bool = False
    new_facts: list[ResearchFact] = Field(default_factory=list)
    error_type: EvaluationErrorType = EvaluationErrorType.NONE


class Finding(StrictModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class ResearchReport(StrictModel):
    task_id: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    findings: list[Finding] = Field(default_factory=list)
    comparison: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    markdown: str = Field(min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
