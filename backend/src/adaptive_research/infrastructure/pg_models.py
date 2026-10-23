"""PostgreSQL application ledger for the P-01 worker boundary.

These tables are deliberately separate from the preserved V1 SQLite metadata.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


class PgBase(DeclarativeBase):
    pass


class PgOwner(PgBase):
    __tablename__ = "app_owner"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    is_synthetic: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgSchedulerGuard(PgBase):
    __tablename__ = "scheduler_guard"
    __table_args__ = (CheckConstraint("id = 1", name="ck_scheduler_guard_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class PgTask(PgBase):
    __tablename__ = "app_task"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','completed','partial','failed','cancelled')",
            name="ck_app_task_status",
        ),
        CheckConstraint(
            "fencing_token >= 0 AND recovery_count BETWEEN 0 AND 1",
            name="ck_app_task_generation",
        ),
        Index("ix_app_task_status_created", "status", "created_at", "id"),
        Index("ix_app_task_owner_created", "owner_id", "created_at", "id"),
        Index(
            "uq_app_task_owner_idempotency_key",
            "owner_id",
            "idempotency_key",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("app_owner.id", ondelete="RESTRICT"), nullable=False
    )
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'queued'")
    )
    cancellation_requested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    fencing_token: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    recovery_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    lease_owner: Mapped[str | None] = mapped_column(String(128))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_level: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'none'")
    )
    stop_reason: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    terminal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PgEvent(PgBase):
    __tablename__ = "app_event"
    __table_args__ = (
        Index("ix_app_event_task_id", "task_id", "id"),
        Index(
            "uq_app_event_one_terminal",
            "task_id",
            unique=True,
            postgresql_where=text("event_type = 'task_finished'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_task.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    message: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    fencing_token: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgCallAttempt(PgBase):
    __tablename__ = "app_call_attempt"
    __table_args__ = (
        CheckConstraint(
            "status IN ('started','completed','failed','unknown_outcome')",
            name="ck_app_call_status",
        ),
        Index("ix_app_call_task_started", "task_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_task.id", ondelete="CASCADE"), nullable=False
    )
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'started'")
    )
    safe_input_digest: Mapped[str | None] = mapped_column(String(64))
    safe_output_digest: Mapped[str | None] = mapped_column(String(64))
    failure_type: Mapped[str | None] = mapped_column(String(64))
    provider: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    reported_prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    reported_completion_tokens: Mapped[int | None] = mapped_column(Integer)
    prompt_cache_hit_tokens: Mapped[int | None] = mapped_column(Integer)
    prompt_cache_miss_tokens: Mapped[int | None] = mapped_column(Integer)
    provider_created_at: Mapped[int | None] = mapped_column(BigInteger)
    reported_model: Mapped[str | None] = mapped_column(String(128))
    system_fingerprint: Mapped[str | None] = mapped_column(String(256))
    pricing_error: Mapped[str | None] = mapped_column(String(64))
    pricing_tariff: Mapped[str | None] = mapped_column(String(16))
    known_cost_cny: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    cost_basis: Mapped[str | None] = mapped_column(String(128))
    price_revision: Mapped[str | None] = mapped_column(String(128))
    execution_source_sha256: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PgFact(PgBase):
    __tablename__ = "app_fact"
    __table_args__ = (Index("ix_app_fact_task_created", "task_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_task.id", ondelete="CASCADE"), nullable=False
    )
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    official_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    official_identity_basis: Mapped[str | None] = mapped_column(Text)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text)
    evidence_locator: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    machine_admission_status: Mapped[str] = mapped_column(String(32), nullable=False)
    human_review_status: Mapped[str | None] = mapped_column(String(32))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgReport(PgBase):
    __tablename__ = "app_report"

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_task.id", ondelete="CASCADE"), primary_key=True
    )
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgCost(PgBase):
    __tablename__ = "app_cost"
    __table_args__ = (
        CheckConstraint("unknown_attempt_count >= 0", name="ck_app_cost_unknown"),
    )

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("app_task.id", ondelete="CASCADE"), primary_key=True
    )
    known_cost_cny: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), nullable=False, server_default=text("0")
    )
    unknown_attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PgBudget(PgBase):
    """One durable local paid-run ceiling shared by every Worker process."""

    __tablename__ = "app_budget"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_app_budget_singleton"),
        CheckConstraint("status IN ('armed', 'halted')", name="ck_app_budget_status"),
        CheckConstraint(
            "phase_max_cny > 0 AND project_max_cny > phase_max_cny AND reserve_per_call_cny > 0",
            name="ck_app_budget_bounds",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    phase_max_cny: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    project_max_cny: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    reserve_per_call_cny: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), nullable=False
    )
    price_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    price_book_sha256: Mapped[str | None] = mapped_column(String(64))
    authorization_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    halt_reason: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
