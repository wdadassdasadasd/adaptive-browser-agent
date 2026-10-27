import asyncio

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.infrastructure.db import models  # noqa: F401
from adaptive_research.infrastructure.db.base import Base
from adaptive_research.infrastructure.db.models import ResearchTaskModel
from adaptive_research.infrastructure.db.session import initialize_schema


@pytest.mark.asyncio
async def test_create_all_builds_expected_tables() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            table_names = await connection.run_sync(
                lambda sync_connection: inspect(sync_connection).get_table_names()
            )
            fact_columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("research_fact")
                }
            )
    finally:
        await engine.dispose()

    assert set(table_names) == {
        "agent_trace",
        "research_fact",
        "research_step",
        "research_task",
    }
    assert {"source_url", "source_title", "evidence"} <= fact_columns


@pytest.mark.asyncio
async def test_new_task_row_defaults_to_queued() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            task = ResearchTaskModel(goal="Research")
            session.add(task)
            await session.flush()
            assert task.status == "queued"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_incompatible_existing_table_is_reported_without_deletion(
    tmp_path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'old.db'}")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE research_fact (id VARCHAR(36) PRIMARY KEY, content TEXT)"
                )
            )
            await connection.execute(
                text("INSERT INTO research_fact (id, content) VALUES ('old', 'keep')")
            )
        with pytest.raises(RuntimeError, match="research_fact.*source_title"):
            await initialize_schema(engine)
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT content FROM research_fact WHERE id='old'")
                )
            ) == "keep"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_initialize_schema_adds_decision_context_to_existing_tasks(
    tmp_path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE research_task ("
                    "id VARCHAR(36) PRIMARY KEY, goal TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, error_message TEXT, "
                    "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO research_task "
                    "(id, goal, status, created_at, updated_at) "
                    "VALUES ('legacy', 'Keep this task', 'completed', "
                    "'2026-10-26 00:00:00', '2026-10-26 00:00:00')"
                )
            )

        await initialize_schema(engine)

        async with engine.connect() as connection:
            task = (
                await connection.execute(
                    text(
                        "SELECT goal, status, decision_context "
                        "FROM research_task WHERE id='legacy'"
                    )
                )
            ).one()
            assert task == ("Keep this task", "completed", None)
            columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("research_task")
                }
            )
            assert "decision_context" in columns
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_incompatible_schema_is_rejected_before_task_upgrade(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'mixed-old.db'}")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE research_task ("
                    "id VARCHAR(36) PRIMARY KEY, goal TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, error_message TEXT, "
                    "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "CREATE TABLE research_fact (id VARCHAR(36) PRIMARY KEY, content TEXT)"
                )
            )
        with pytest.raises(RuntimeError, match="research_fact.*source_title"):
            await initialize_schema(engine)
        async with engine.connect() as connection:
            task_columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("research_task")
                }
            )
            assert "decision_context" not in task_columns
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_schema_initialization_serializes_additive_migration(
    tmp_path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'concurrent.db'}")
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE TABLE research_task ("
                    "id VARCHAR(36) PRIMARY KEY, goal TEXT NOT NULL, "
                    "status VARCHAR(32) NOT NULL, error_message TEXT, "
                    "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
                )
            )

        await asyncio.gather(initialize_schema(engine), initialize_schema(engine))

        async with engine.connect() as connection:
            columns = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("research_task")
                }
            )
            assert "decision_context" in columns
    finally:
        await engine.dispose()
