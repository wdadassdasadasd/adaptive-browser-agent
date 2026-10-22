"""Bind an armed budget to the exact frozen price-book bytes."""

import sqlalchemy as sa
from alembic import op

revision = "20261021_04"
down_revision = "20261021_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_budget", sa.Column("price_book_sha256", sa.String(64)))
    # Older armed rows cannot prove which tariff bytes they authorized.
    op.execute(
        "UPDATE app_budget SET status = 'halted', halt_reason = 'price_book_hash_missing' "
        "WHERE price_book_sha256 IS NULL"
    )


def downgrade() -> None:
    op.drop_column("app_budget", "price_book_sha256")
