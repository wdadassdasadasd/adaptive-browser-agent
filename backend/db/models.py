"""Initial SQLAlchemy persistence models."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base, utc_now


def new_uuid() -> str:
    return str(uuid4())


class ResearchTaskModel(Base):
    __tablename__ = "research_task"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="queued", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ResearchStepModel(Base):
    __tablename__ = "research_step"
    __table_args__ = (Index("ix_research_step_task_step", "task_id", "step"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_task.id", ondelete="CASCADE"),
        nullable=False,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class ResearchFactModel(Base):
    __tablename__ = "research_fact"
    __table_args__ = (Index("ix_research_fact_task_created", "task_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_task.id", ondelete="CASCADE"),
        nullable=False,
    )
    subgoal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class AgentTraceModel(Base):
    __tablename__ = "agent_trace"
    __table_args__ = (Index("ix_agent_trace_task_step", "task_id", "step"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("research_task.id", ondelete="CASCADE"),
        nullable=False,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
