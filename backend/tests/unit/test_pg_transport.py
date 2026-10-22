"""Transport races and service-unavailable responses without a database."""

from types import SimpleNamespace
from uuid import UUID

import httpx
import pytest

from adaptive_research.agent.state import utc_now
from adaptive_research.api.pg_main import create_app
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_store import EventRecord


@pytest.mark.asyncio
async def test_sse_rereads_events_after_observing_a_racing_terminal_commit() -> None:
    class RacingStore:
        reads = 0

        async def get_task(self, _owner, task_id):
            return SimpleNamespace(
                id=task_id, status="failed" if self.reads else "running"
            )

        async def list_events(self, _owner, task_id, after_id=0):
            self.reads += 1
            if self.reads == 1:
                return []
            return [
                EventRecord(
                    1, task_id, "task_finished", 0, "", {"status": "failed"}, utc_now()
                )
            ]

    app = create_app(Settings(_env_file=None))
    app.state.pg_store = RacingStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/research/task/events")
    assert response.status_code == 200
    assert response.text.count("event: task_finished") == 1
    assert app.state.pg_store.reads == 3


@pytest.mark.asyncio
async def test_unknown_uuid_cursor_is_rejected_before_bigint_database_query() -> None:
    class VisibleStore:
        async def get_task(self, _owner, task_id):
            return SimpleNamespace(id=task_id, status="running")

        async def list_events(self, *_args):
            pytest.fail("Out-of-range UUID cursor must not reach the database")

    app = create_app(Settings(_env_file=None))
    app.state.pg_store = VisibleStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/research/task/events",
            headers={"Last-Event-ID": str(UUID(int=1 << 120))},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_database_connection_failure_is_503_without_exception_content() -> None:
    class OfflineStore:
        async def create_task(self, *_args):
            raise ConnectionRefusedError("sensitive connection detail")

    app = create_app(Settings(_env_file=None, DEEPSEEK_API_KEY="offline-key"))
    app.state.pg_store = OfflineStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/research", json={"goal": "offline"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Research database unavailable"}
    assert "sensitive" not in response.text
