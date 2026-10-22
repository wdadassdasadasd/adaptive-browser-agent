"""Allow safe retry of an ambiguous research task submission."""

import sqlalchemy as sa
from alembic import op

revision = "20261021_05"
down_revision = "20261021_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_task", sa.Column("idempotency_key", sa.String(128)))
    op.create_index(
        "uq_app_task_owner_idempotency_key",
        "app_task",
        ["owner_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_app_task_owner_idempotency_key", table_name="app_task")
    op.drop_column("app_task", "idempotency_key")
