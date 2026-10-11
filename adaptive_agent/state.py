"""Long-lived domain state for the adaptive research loop."""

from datetime import UTC, datetime
from enum import StrEnum
from ipaddress import ip_address
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    model_validator,
)

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)


def require_utc(value: datetime) -> datetime:
    """Reject naive and non-UTC timestamps at domain boundaries."""

    if value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp must be UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(require_utc)]


def require_http_url(value: str) -> str:
    """Validate source URL shape without claiming that a tool observed it."""

    _HTTP_URL_ADAPTER.validate_python(value)
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source URL must be HTTP(S)")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("source URL must not contain credentials")
    try:
        address = ip_address(parsed.hostname)
    except ValueError:
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError("source URL must be public") from None
    else:
        if not address.is_global:
            raise ValueError("source URL must be public")
    return value


SourceUrl = Annotated[NonEmptyText, AfterValidator(require_http_url)]


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
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationErrorType(StrEnum):
    NONE = "none"
    TECHNICAL = "technical"
    SEMANTIC = "semantic"
    INSUFFICIENT_INFO = "insufficient_info"


class Subgoal(StrictModel):
    id: NonEmptyText = Field(default_factory=new_id)
    description: NonEmptyText
    completion_criteria: NonEmptyText
    status: SubgoalStatus = SubgoalStatus.PENDING
    priority: int = Field(default=0, ge=0, strict=True)
    failure_reason: NonEmptyText | None = None


class ResearchFact(StrictModel):
    id: NonEmptyText = Field(default_factory=new_id)
    subgoal_id: NonEmptyText | None = None
    content: NonEmptyText
    source_url: SourceUrl
    source_title: NonEmptyText
    evidence: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: UtcDateTime = Field(default_factory=utc_now)


class ResearchState(StrictModel):
    """Durable agent state only; runtime resources deliberately do not belong here."""

    task_id: NonEmptyText = Field(default_factory=new_id)
    goal: NonEmptyText
    status: ResearchStatus = ResearchStatus.QUEUED
    step: int = Field(default=0, ge=0, strict=True)
    max_steps: int = Field(default=30, ge=1, strict=True)
    subgoals: list[Subgoal] = Field(default_factory=list)
    facts: list[ResearchFact] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    search_history: list[str] = Field(default_factory=list)
    current_subgoal_id: NonEmptyText | None = None
    prompt_tokens: int = Field(default=0, ge=0, strict=True)
    completion_tokens: int = Field(default=0, ge=0, strict=True)
    consecutive_no_progress_replans: int = Field(default=0, ge=0, strict=True)
    cancellation_requested: bool = False
    stop_reason: NonEmptyText | None = None
    completion_level: Literal["none", "partial", "full"] = "none"
    created_at: UtcDateTime = Field(default_factory=utc_now)
    updated_at: UtcDateTime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_progress(self) -> "ResearchState":
        if self.step > self.max_steps:
            raise ValueError("step cannot exceed max_steps")
        if self.current_subgoal_id is not None and self.current_subgoal_id not in {
            subgoal.id for subgoal in self.subgoals
        }:
            raise ValueError("current_subgoal_id must identify an existing subgoal")
        return self


class PlanDecision(StrictModel):
    subgoal_id: NonEmptyText
    reasoning: NonEmptyText
    tool: Literal["browser", "github"]
    action: NonEmptyText
    target: str | None = None
    element_index: int | None = Field(default=None, ge=0)
    value: str | None = None
    expected_result: NonEmptyText


class ToolResult(StrictModel):
    """Serializable outcome shared by both tool paths and the reducer."""

    tool: Literal["browser", "github"]
    action: NonEmptyText
    success: bool
    content: str = Field(max_length=12000)
    source_url: SourceUrl | None = None
    error_type: EvaluationErrorType = EvaluationErrorType.NONE
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_outcome(self) -> "ToolResult":
        if self.success != (self.error_type == EvaluationErrorType.NONE):
            raise ValueError("tool result success and error_type disagree")
        return self


class EvaluationResult(StrictModel):
    success: bool
    reason: NonEmptyText
    subgoal_completed: bool = False
    should_replan: bool = False
    facts: list[ResearchFact] = Field(default_factory=list)
    error_type: EvaluationErrorType = EvaluationErrorType.NONE

    @model_validator(mode="after")
    def validate_outcome(self) -> "EvaluationResult":
        if self.success:
            if self.error_type != EvaluationErrorType.NONE:
                raise ValueError("successful evaluation requires error_type=none")
        elif (
            self.error_type == EvaluationErrorType.NONE
            or self.subgoal_completed
            or not self.should_replan
        ):
            raise ValueError(
                "failed evaluation requires an error, replan, and unfinished subgoal"
            )
        return self


class Finding(StrictModel):
    name: NonEmptyText
    description: NonEmptyText
    attributes: dict[str, str] = Field(default_factory=dict)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    source_urls: list[SourceUrl] = Field(default_factory=list)


class ResearchReport(StrictModel):
    task_id: NonEmptyText
    goal: NonEmptyText
    title: NonEmptyText
    summary: NonEmptyText
    findings: list[Finding] = Field(default_factory=list)
    comparison: NonEmptyText
    recommendation: NonEmptyText
    sources: list[SourceUrl] = Field(default_factory=list)
    markdown: NonEmptyText
    generated_at: UtcDateTime = Field(default_factory=utc_now)
