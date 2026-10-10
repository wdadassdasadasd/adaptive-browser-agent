"""Serializable, closed event contract shared by runtime and API transports."""

import json
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from adaptive_agent.state import NonEmptyText, UtcDateTime, new_id, utc_now

EventType = Literal[
    "task_queued",
    "task_started",
    "subgoals_initialized",
    "step_evaluated",
    "cancel_requested",
    "task_finished",
]


class AgentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=new_id)
    event_type: EventType
    task_id: NonEmptyText
    step: int = Field(default=0, ge=0, strict=True)
    timestamp: UtcDateTime = Field(default_factory=utc_now)
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        try:
            UUID(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("event_id must be a UUID string") from exc
        return value

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("payload must be JSON serializable") from exc
        return value
