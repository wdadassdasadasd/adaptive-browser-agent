"""Async SQLAlchemy engine, session factory, and schema lifecycle."""

from collections.abc import AsyncIterator

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from adaptive_research.infrastructure.config import get_settings
from adaptive_research.infrastructure.db.base import Base

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
    """Apply safe additive upgrades, then reject incompatible tables."""

    from adaptive_research.infrastructure.db import models  # noqa: F401

    async with target_engine.begin() as connection:

        def prepare_schema(sync_connection) -> None:
            if sync_connection.dialect.name == "sqlite":
                # Serialize startup migrations before inspecting the schema.
                # SQLite starts transactions lazily, so acquire its write lock.
                sync_connection.exec_driver_sql("BEGIN IMMEDIATE")
            inspector = inspect(sync_connection)
            existing = set(inspector.get_table_names())
            missing = {
                table.name: sorted(
                    {column.name for column in table.columns}
                    - {column["name"] for column in inspector.get_columns(table.name)}
                )
                for table in Base.metadata.sorted_tables
                if table.name in existing
            }
            incompatible = {
                table: columns for table, columns in missing.items() if columns
            }
            additive_upgrade = {"research_task": ["decision_context"]}
            if incompatible and incompatible != additive_upgrade:
                detail = "; ".join(
                    f"{table}: {', '.join(columns)}"
                    for table, columns in incompatible.items()
                )
                raise RuntimeError(
                    f"Incompatible SQLite schema, missing columns: {detail}"
                )
            if (
                sync_connection.dialect.name == "sqlite"
                and incompatible == additive_upgrade
            ):
                sync_connection.exec_driver_sql(
                    "ALTER TABLE research_task ADD COLUMN decision_context JSON"
                )

        await connection.run_sync(prepare_schema)
        await connection.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    await engine.dispose()
