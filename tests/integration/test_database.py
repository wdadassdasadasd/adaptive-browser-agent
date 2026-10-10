import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.db import models  # noqa: F401
from backend.db.base import Base
from backend.db.models import ResearchTaskModel


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
