"""Research API transport schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ResearchCreateRequest(ApiModel):
    goal: str = Field(min_length=1)


class ResearchTaskResponse(ApiModel):
    id: str
    goal: str
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentTraceResponse(ApiModel):
    id: int
    task_id: str
    step: int
    event_type: str
    message: str
    payload: dict[str, Any]
    created_at: datetime


class CancelResponse(ApiModel):
    task_id: str
    cancelled: bool
