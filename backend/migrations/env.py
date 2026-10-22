"""Run only the isolated P-01 PostgreSQL migration family."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_models import PgBase

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def migration_url() -> str:
    return Settings().require_postgres_url()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=PgBase.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(migration_url(), pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("P-01 migrations require an online isolated PostgreSQL database")

asyncio.run(run_online())
