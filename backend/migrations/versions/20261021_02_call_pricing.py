"""Retain provider-reported usage and the decision behind per-call CNY cost."""

import sqlalchemy as sa
from alembic import op

revision = "20261021_02"
down_revision = "20261020_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in (
        sa.Column("prompt_cache_hit_tokens", sa.Integer()),
        sa.Column("prompt_cache_miss_tokens", sa.Integer()),
        sa.Column("provider_created_at", sa.BigInteger()),
        sa.Column("reported_model", sa.String(128)),
        sa.Column("system_fingerprint", sa.String(256)),
        sa.Column("pricing_error", sa.String(64)),
        sa.Column("pricing_tariff", sa.String(16)),
    ):
        op.add_column("app_call_attempt", column)


def downgrade() -> None:
    for name in (
        "pricing_tariff",
        "pricing_error",
        "system_fingerprint",
        "reported_model",
        "provider_created_at",
        "prompt_cache_miss_tokens",
        "prompt_cache_hit_tokens",
    ):
        op.drop_column("app_call_attempt", name)
