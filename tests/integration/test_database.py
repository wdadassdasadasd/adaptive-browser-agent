import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from backend.db import models  # noqa: F401
from backend.db.base import Base


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
