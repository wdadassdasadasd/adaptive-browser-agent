"""Record why a completed call has a known cost, including explicit zero."""

import sqlalchemy as sa
from alembic import op

revision = "20261022_06"
down_revision = "20261021_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_call_attempt", sa.Column("cost_basis", sa.String(128)))
    op.add_column(
        "app_call_attempt", sa.Column("execution_source_sha256", sa.String(64))
    )


def downgrade() -> None:
    op.drop_column("app_call_attempt", "execution_source_sha256")
    op.drop_column("app_call_attempt", "cost_basis")
