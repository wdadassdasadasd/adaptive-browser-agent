"""Async SQLAlchemy engine, session factory, and schema lifecycle."""

from collections.abc import AsyncIterator

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import get_settings
from backend.db.base import Base

settings = get_settings()
engine = create_async_engine(settings.database_url)
AsyncSessionFactory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


async def init_db() -> None:
    """Create the V1 schema without a migration framework."""

    await initialize_schema(engine)


async def initialize_schema(target_engine: AsyncEngine) -> None:
    """Reject incompatible existing tables before create_all can touch the DB."""

    from backend.db import models  # noqa: F401

    async with target_engine.begin() as connection:

        def missing_columns(sync_connection):
            inspector = inspect(sync_connection)
            existing = set(inspector.get_table_names())
            return {
                table.name: sorted(
                    {column.name for column in table.columns}
                    - {column["name"] for column in inspector.get_columns(table.name)}
                )
                for table in Base.metadata.sorted_tables
                if table.name in existing
            }

        missing = await connection.run_sync(missing_columns)
        incompatible = {table: columns for table, columns in missing.items() if columns}
        if incompatible:
            detail = "; ".join(
                f"{table}: {', '.join(columns)}"
                for table, columns in incompatible.items()
            )
            raise RuntimeError(f"Incompatible SQLite schema, missing columns: {detail}")
        await connection.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    await engine.dispose()
