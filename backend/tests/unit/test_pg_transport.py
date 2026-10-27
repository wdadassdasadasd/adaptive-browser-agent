"""Transport races and service-unavailable responses without a database."""

from types import SimpleNamespace
from uuid import UUID

import httpx
import pytest

from adaptive_research.agent.call_observer import CallObservationError, CallRecorder
from adaptive_research.agent.state import utc_now
from adaptive_research.api.pg_main import create_app
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_store import (
    EventRecord,
    IdempotencyConflict,
)
from adaptive_research.worker.runner import PgCallObserver


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


@pytest.mark.asyncio
async def test_idempotent_replay_is_available_without_provider_configuration() -> None:
    now = utc_now()

    class ReplayStore:
        def __init__(self) -> None:
            self.create_called = False
            self.lookup: tuple[str, str, str] | None = None

        async def get_idempotent_task(
            self, owner_id, goal, idempotency_key, *, decision_context=None
        ):
            self.lookup = (owner_id, goal, idempotency_key)
            return SimpleNamespace(
                id="existing-task",
                goal=goal,
                status="queued",
                error_message=None,
                created_at=now,
                updated_at=now,
                completion_level="none",
                stop_reason=None,
                report=None,
                cancellation_requested=False,
                decision_context=None,
            )

        async def create_task(self, *_args, **_kwargs):
            self.create_called = True
            raise AssertionError("A replay must not create a second task")

    app = create_app(Settings(_env_file=None))
    store = ReplayStore()
    app.state.pg_store = store
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/research",
            json={"goal": "same request"},
            headers={"Idempotency-Key": "retry-key-0001"},
        )

    assert response.status_code == 202
    assert response.json()["id"] == "existing-task"
    assert store.lookup == ("p01-local-owner", "same request", "retry-key-0001")
    assert store.create_called is False


@pytest.mark.asyncio
async def test_idempotency_conflict_is_returned_before_provider_check() -> None:
    class ConflictStore:
        async def get_idempotent_task(self, *_args, **_kwargs):
            raise IdempotencyConflict

        async def create_task(self, *_args, **_kwargs):
            pytest.fail("A conflicting idempotency key must not create a task")

    app = create_app(Settings(_env_file=None))
    app.state.pg_store = ConflictStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/research",
            json={"goal": "different request"},
            headers={"Idempotency-Key": "retry-key-0001"},
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_new_task_still_requires_provider_after_idempotency_miss() -> None:
    class EmptyStore:
        async def get_idempotent_task(self, *_args, **_kwargs):
            return None

        async def create_task(self, *_args, **_kwargs):
            pytest.fail("A task must not be created without provider configuration")

    app = create_app(Settings(_env_file=None))
    app.state.pg_store = EmptyStore()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/research",
            json={"goal": "new request"},
            headers={"Idempotency-Key": "retry-key-0002"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "DeepSeek provider is not configured"}


@pytest.mark.asyncio
async def test_unknown_model_cost_without_price_book_stops_followup_calls() -> None:
    class Store:
        price_book = None

        def __init__(self) -> None:
            self.finished_calls = 0

        async def start_call(self, *_args, **_kwargs):
            return SimpleNamespace(id="call-1")

        async def complete_call(self, *_args, **_kwargs):
            self.finished_calls += 1
            return SimpleNamespace(
                kind="model", known_cost_cny=None, pricing_error="missing_price_book"
            )

    store = Store()
    observer = PgCallObserver(store, "task-1", 1)
    recorder = CallRecorder(observer)
    provider_calls = 0

    async def provider_call():
        nonlocal provider_calls
        provider_calls += 1
        return SimpleNamespace(prompt_tokens=1, completion_tokens=1)

    with pytest.raises(CallObservationError):
        await recorder.run("model", "fake", provider_call)
    with pytest.raises(CallObservationError):
        await recorder.run("model", "fake", provider_call)

    assert provider_calls == 1
    assert store.finished_calls == 1
