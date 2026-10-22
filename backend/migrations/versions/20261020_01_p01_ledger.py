"""Create the P-01 PostgreSQL application ledger.

Revision ID: 20261020_01
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261020_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_owner",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_table(
        "scheduler_guard",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.CheckConstraint("id = 1", name="ck_scheduler_guard_singleton"),
    )
    op.execute("INSERT INTO scheduler_guard (id) VALUES (1)")
    op.create_table(
        "app_task",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(64),
            sa.ForeignKey("app_owner.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(16), nullable=False, server_default=sa.text("'queued'")
        ),
        sa.Column(
            "cancellation_requested",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "fencing_token", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "recovery_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("lease_owner", sa.String(128)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column(
            "completion_level",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
        sa.Column("stop_reason", sa.String(128)),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("terminal_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','partial','failed','cancelled')",
            name="ck_app_task_status",
        ),
        sa.CheckConstraint(
            "fencing_token >= 0 AND recovery_count BETWEEN 0 AND 1",
            name="ck_app_task_generation",
        ),
    )
    op.create_index(
        "ix_app_task_status_created", "app_task", ["status", "created_at", "id"]
    )
    op.create_index(
        "ix_app_task_owner_created", "app_task", ["owner_id", "created_at", "id"]
    )
    op.create_table(
        "app_event",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("app_task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("message", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("fencing_token", sa.Integer()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_app_event_task_id", "app_event", ["task_id", "id"])
    op.create_index(
        "uq_app_event_one_terminal",
        "app_event",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("event_type = 'task_finished'"),
    )
    op.create_table(
        "app_call_attempt",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("app_task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column(
            "status", sa.String(24), nullable=False, server_default=sa.text("'started'")
        ),
        sa.Column("safe_input_digest", sa.String(64)),
        sa.Column("safe_output_digest", sa.String(64)),
        sa.Column("failure_type", sa.String(64)),
        sa.Column("provider", sa.String(64)),
        sa.Column("model", sa.String(128)),
        sa.Column("reported_prompt_tokens", sa.Integer()),
        sa.Column("reported_completion_tokens", sa.Integer()),
        sa.Column("known_cost_cny", sa.Numeric(18, 8)),
        sa.Column("price_revision", sa.String(128)),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('started','completed','failed','unknown_outcome')",
            name="ck_app_call_status",
        ),
    )
    op.create_index(
        "ix_app_call_task_started", "app_call_attempt", ["task_id", "started_at"]
    )
    op.create_table(
        "app_fact",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("app_task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("official_source_url", sa.Text(), nullable=False),
        sa.Column("official_identity_basis", sa.Text()),
        sa.Column("evidence_excerpt", sa.Text()),
        sa.Column("evidence_locator", sa.Text()),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("machine_admission_status", sa.String(32), nullable=False),
        sa.Column("human_review_status", sa.String(32)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_app_fact_task_created", "app_fact", ["task_id", "created_at"])
    op.create_table(
        "app_report",
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("app_task.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_table(
        "app_cost",
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("app_task.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "known_cost_cny",
            sa.Numeric(18, 8),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "unknown_attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("unknown_attempt_count >= 0", name="ck_app_cost_unknown"),
    )


def downgrade() -> None:
    for table in (
        "app_cost",
        "app_report",
        "app_fact",
        "app_call_attempt",
        "app_event",
        "app_task",
        "scheduler_guard",
        "app_owner",
    ):
        op.drop_table(table)
