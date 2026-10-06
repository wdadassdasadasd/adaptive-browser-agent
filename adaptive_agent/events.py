"""Event contract shared by runtime and API transports."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from adaptive_agent.state import utc_now


class AgentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    step: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=utc_now)
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
