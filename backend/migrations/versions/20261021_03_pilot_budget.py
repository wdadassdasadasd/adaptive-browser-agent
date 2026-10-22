"""Durable local budget ceiling for a separately authorized pilot."""

import sqlalchemy as sa
from alembic import op

revision = "20261021_03"
down_revision = "20261021_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_budget",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("phase_max_cny", sa.Numeric(18, 8), nullable=False),
        sa.Column("project_max_cny", sa.Numeric(18, 8), nullable=False),
        sa.Column("reserve_per_call_cny", sa.Numeric(18, 8), nullable=False),
        sa.Column("price_revision", sa.String(128), nullable=False),
        sa.Column("authorization_reference", sa.String(128), nullable=False),
        sa.Column("halt_reason", sa.String(64)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("id = 1", name="ck_app_budget_singleton"),
        sa.CheckConstraint(
            "status IN ('armed', 'halted')", name="ck_app_budget_status"
        ),
        sa.CheckConstraint(
            "phase_max_cny > 0 AND project_max_cny > phase_max_cny AND reserve_per_call_cny > 0",
            name="ck_app_budget_bounds",
        ),
    )


def downgrade() -> None:
    op.drop_table("app_budget")
