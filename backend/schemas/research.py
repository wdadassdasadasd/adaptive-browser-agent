"""Research API transport schemas."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints

from adaptive_agent.state import ResearchReport


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ResearchCreateRequest(ApiModel):
    goal: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]


class ResearchTaskResponse(ApiModel):
    id: str
    goal: str
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completion_level: str | None = None
    stop_reason: str | None = None
    report: ResearchReport | None = None


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
