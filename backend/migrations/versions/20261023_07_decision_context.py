"""Persist normalized, optional user decision context with the queued task."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261023_07"
down_revision = "20261022_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_task", sa.Column("decision_context", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_task", "decision_context")
