"""Persisted replay and live SSE notifications share one event cursor."""

import asyncio
import socket
from datetime import UTC, datetime

import httpx
import pytest
import uvicorn
from fastapi import Request

from adaptive_research.agent.events import AgentEvent
from adaptive_research.api.main import create_app
from adaptive_research.api.research import stream_research_events
from adaptive_research.infrastructure.config import Settings


class GatedAgent:
    release = asyncio.Event()

    async def run(self, goal, *, cancellation, task_id, on_event):
        await on_event(AgentEvent(event_type="task_started", task_id=task_id))
        await self.release.wait()
        await on_event(
            AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                payload={
                    "status": "failed",
                    "completion_level": "none",
                    "stop_reason": "insufficient_info",
                },
            )
        )


@pytest.mark.asyncio
async def test_replay_joins_live_events_and_reconnect_skips_seen_id(tmp_path) -> None:
    GatedAgent.release = asyncio.Event()
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'sse.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=GatedAgent)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task = await service.create("Research")
        request = Request({"type": "http", "app": app, "headers": []})
        response = await stream_research_events(task.id, request, None)
        stream = response.body_iterator
        queued = await asyncio.wait_for(anext(stream), 2)
        started = await asyncio.wait_for(anext(stream), 2)
        assert "event: task_queued" in queued
        assert "event: task_started" in started
        assert service.manager.subscriber_count(task.id) == 1
        GatedAgent.release.set()
        finished = await asyncio.wait_for(anext(stream), 2)
        assert "event: task_finished" in finished
        with pytest.raises(StopAsyncIteration):
            await anext(stream)
        assert service.manager.subscriber_count(task.id) == 0

        seen_id = started.split("\n", 1)[0].removeprefix("id: ")
        resumed = await stream_research_events(task.id, request, seen_id)
        assert "event: task_finished" in await anext(resumed.body_iterator)
        with pytest.raises(StopAsyncIteration):
            await anext(resumed.body_iterator)


@pytest.mark.asyncio
async def test_slow_subscriber_catches_up_and_disconnect_is_isolated(tmp_path) -> None:
    GatedAgent.release = asyncio.Event()
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'multi.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=GatedAgent)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task = await service.create("Research")
        request = Request({"type": "http", "app": app, "headers": []})
        fast = (await stream_research_events(task.id, request, None)).body_iterator
        slow = (await stream_research_events(task.id, request, None)).body_iterator
        assert "task_queued" in await anext(fast)
        assert "task_queued" in await anext(slow)
        assert "task_started" in await asyncio.wait_for(anext(fast), 2)
        assert service.manager.subscriber_count(task.id) == 2
        await fast.aclose()
        assert service.manager.subscriber_count(task.id) == 1
        GatedAgent.release.set()
        assert "task_started" in await asyncio.wait_for(anext(slow), 2)
        assert "task_finished" in await asyncio.wait_for(anext(slow), 2)
        with pytest.raises(StopAsyncIteration):
            await anext(slow)
        assert service.manager.subscriber_count(task.id) == 0
        assert (await service.get(task.id)).status == "failed"


@pytest.mark.asyncio
async def test_http_sse_disconnect_keeps_database_usable(tmp_path, caplog) -> None:
    GatedAgent.release = asyncio.Event()
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'http-disconnect.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=GatedAgent)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    serving = asyncio.create_task(server.serve())
    try:
        for _ in range(100):
            if server.started:
                break
            await asyncio.sleep(0.02)
        assert server.started
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}", timeout=5
        ) as client:
            created = await client.post("/api/research", json={"goal": "Research"})
            assert created.status_code == 202
            task_id = created.json()["id"]
            async with client.stream(
                "GET", f"/api/research/{task_id}/events"
            ) as response:
                assert response.status_code == 200
                async for line in response.aiter_lines():
                    if line == "event: task_started":
                        break
            for _ in range(100):
                if app.state.research.manager.subscriber_count(task_id) == 0:
                    break
                await asyncio.sleep(0.01)
            assert app.state.research.manager.subscriber_count(task_id) == 0
            detail = await client.get(f"/api/research/{task_id}")
            assert detail.status_code == 200
            assert detail.json()["status"] == "running"
            assert not [
                record
                for record in caplog.records
                if record.levelname == "ERROR"
                and record.name.startswith("sqlalchemy.pool")
            ]
            GatedAgent.release.set()
    finally:
        GatedAgent.release.set()
        server.should_exit = True
        await asyncio.wait_for(serving, 10)


@pytest.mark.asyncio
async def test_sse_and_report_redact_configured_credentials(tmp_path, caplog) -> None:
    deepseek_secret = "deepseek-secret-sentinel"
    github_secret = "github-secret-sentinel"

    class SecretAgent:
        async def run(self, goal, *, cancellation, task_id, on_event):
            await on_event(AgentEvent(event_type="task_started", task_id=task_id))
            await on_event(
                AgentEvent(
                    event_type="cancel_requested",
                    task_id=task_id,
                    message=deepseek_secret,
                    payload={"note": github_secret},
                )
            )
            await on_event(
                AgentEvent(
                    event_type="task_finished",
                    task_id=task_id,
                    payload={
                        "status": "failed",
                        "completion_level": "none",
                        "stop_reason": "execution_error",
                        "report": {
                            "task_id": task_id,
                            "goal": goal,
                            "title": "Result",
                            "summary": deepseek_secret,
                            "findings": [],
                            "comparison": "none",
                            "recommendation": "none",
                            "sources": [],
                            "markdown": github_secret,
                            "generated_at": datetime.now(UTC).isoformat(),
                        },
                    },
                )
            )

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'secrets.db'}",
        DEEPSEEK_API_KEY=deepseek_secret,
        GITHUB_TOKEN=github_secret,
    )
    app = create_app(settings=settings, agent_factory=SecretAgent)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task = await service.create("Research")
        for _ in range(100):
            if (await service.get(task.id)).status == "failed":
                break
            await asyncio.sleep(0.01)
        request = Request({"type": "http", "app": app, "headers": []})
        stream = (await stream_research_events(task.id, request, None)).body_iterator
        frames = []
        async for frame in stream:
            frames.append(frame)
        traces = await service.traces(task.id)
        report = await service.report(task.id)
        combined = "".join(frames) + str([row.payload for row in traces])
        combined += report.model_dump_json()
        assert deepseek_secret not in combined
        assert github_secret not in combined
        assert not any(
            deepseek_secret in record.getMessage()
            or github_secret in record.getMessage()
            for record in caplog.records
        )
