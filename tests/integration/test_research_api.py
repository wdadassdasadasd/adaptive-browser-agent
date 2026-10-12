"""Six-route HTTP contract backed by a temporary SQLite database."""

import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient

from adaptive_agent.events import AgentEvent
from adaptive_agent.llm.base import StructuredCompletion
from backend.api.research import _response
from backend.config import Settings
from backend.main import create_app
from tests.integration.test_agent_loop import (
    FakeBrowser,
    FakeGithub,
    FakeProvider,
    make_loop,
)


class FakeAgent:
    async def run(self, goal, *, cancellation, task_id, on_event):
        await on_event(AgentEvent(event_type="task_started", task_id=task_id))
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


class WaitingAgent:
    async def run(self, goal, *, cancellation, task_id, on_event):
        await on_event(AgentEvent(event_type="task_started", task_id=task_id))
        await cancellation.wait()
        await on_event(AgentEvent(event_type="cancel_requested", task_id=task_id))
        await on_event(
            AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                payload={
                    "status": "cancelled",
                    "completion_level": "none",
                    "stop_reason": "user_cancelled",
                },
            )
        )


def test_missing_provider_key_creates_no_task(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'missing.db'}",
        DEEPSEEK_API_KEY=None,
    )
    with TestClient(create_app(settings=settings, agent_factory=FakeAgent)) as client:
        assert (
            client.post("/api/research", json={"goal": "Research"}).status_code == 503
        )
        assert client.get("/api/research").json() == []
        assert client.post("/api/research", json={"goal": ""}).status_code == 422
        assert client.post("/api/research", json={"goal": "   "}).status_code == 422
        assert client.get("/api/research/unknown").status_code == 404
        assert client.get("/api/research/unknown/traces").status_code == 404
        assert client.post("/api/research/unknown/cancel").status_code == 404
        assert client.get("/api/research/unknown/events").status_code == 404


def test_create_list_detail_traces_and_cancel(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'api.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    with TestClient(create_app(settings=settings, agent_factory=FakeAgent)) as client:
        created = client.post("/api/research", json={"goal": "Find FastAPI"})
        assert created.status_code == 202
        task_id = created.json()["id"]
        assert created.json()["status"] == "queued"
        assert created.json()["report"] is None
        for _ in range(100):
            detail = client.get(f"/api/research/{task_id}")
            if detail.json()["status"] in {
                "failed",
                "completed",
                "partial",
                "cancelled",
            }:
                break
            time.sleep(0.01)
        assert detail.status_code == 200
        assert task_id in [item["id"] for item in client.get("/api/research").json()]
        traces = client.get(f"/api/research/{task_id}/traces")
        assert traces.status_code == 200
        assert traces.json()[0]["event_type"] == "task_queued"
        assert client.post(f"/api/research/{task_id}/cancel").json() == {
            "task_id": task_id,
            "cancelled": detail.json()["status"] == "cancelled",
        }


def test_full_agent_loop_rebuilds_sourced_report_via_api(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'full.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )

    def agent_factory():
        return make_loop(FakeProvider(), FakeGithub(), FakeBrowser())

    with TestClient(
        create_app(settings=settings, agent_factory=agent_factory)
    ) as client:
        task_id = client.post(
            "/api/research", json={"goal": "Research FastAPI"}
        ).json()["id"]
        for _ in range(200):
            detail = client.get(f"/api/research/{task_id}")
            if detail.json()["status"] == "completed":
                break
            time.sleep(0.01)
        assert detail.json()["status"] == "completed"
        assert detail.json()["report"]["sources"] == [
            "https://api.github.com/repos/fastapi/fastapi"
        ]
        traces = client.get(f"/api/research/{task_id}/traces").json()
        assert [item["event_type"] for item in traces] == [
            "task_queued",
            "task_started",
            "subgoals_initialized",
            "step_evaluated",
            "task_finished",
        ]
        assert len({item["event_id"] for item in traces}) == len(traces)
    with TestClient(
        create_app(settings=settings, agent_factory=agent_factory)
    ) as client:
        restored = client.get(f"/api/research/{task_id}")
        assert restored.status_code == 200
        assert restored.json()["report"]["sources"] == [
            "https://api.github.com/repos/fastapi/fastapi"
        ]
        assert client.get(f"/api/research/{task_id}/traces").json() == traces


def test_queued_and_running_cancel_are_idempotent(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'cancel.db'}",
        DEEPSEEK_API_KEY="fake-key",
        MAX_CONCURRENT_TASKS=1,
    )
    with TestClient(
        create_app(settings=settings, agent_factory=WaitingAgent)
    ) as client:
        first = client.post("/api/research", json={"goal": "First"}).json()["id"]
        for _ in range(100):
            if client.get(f"/api/research/{first}").json()["status"] == "running":
                break
            time.sleep(0.01)
        second = client.post("/api/research", json={"goal": "Second"}).json()["id"]
        assert client.get(f"/api/research/{second}").json()["status"] == "queued"
        for task_id in (second, first):
            assert (
                client.post(f"/api/research/{task_id}/cancel").json()["cancelled"]
                is True
            )
            for _ in range(100):
                if (
                    client.get(f"/api/research/{task_id}").json()["status"]
                    == "cancelled"
                ):
                    break
                time.sleep(0.01)
            assert (
                client.get(f"/api/research/{task_id}").json()["status"] == "cancelled"
            )
            assert (
                client.post(f"/api/research/{task_id}/cancel").json()["cancelled"]
                is True
            )
            traces = client.get(f"/api/research/{task_id}/traces").json()
            assert [trace["event_type"] for trace in traces].count("task_finished") == 1


@pytest.mark.asyncio
async def test_cancel_racing_with_completed_terminal_returns_false(
    tmp_path, monkeypatch
) -> None:
    release_finish = asyncio.Event()
    terminal_saved = asyncio.Event()
    release_return = asyncio.Event()
    status_read = asyncio.Event()
    resume_cancel = asyncio.Event()

    class FinishingAgent:
        async def run(self, goal, *, cancellation, task_id, on_event):
            await on_event(AgentEvent(event_type="task_started", task_id=task_id))
            await release_finish.wait()
            await on_event(
                AgentEvent(
                    event_type="task_finished",
                    task_id=task_id,
                    payload={
                        "status": "completed",
                        "completion_level": "full",
                        "stop_reason": "goal_satisfied",
                    },
                )
            )
            terminal_saved.set()
            await release_return.wait()

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'cancel-race.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=FinishingAgent)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task = await service.create("Research")
        for _ in range(100):
            if (await service.get(task.id)).status == "running":
                break
            await asyncio.sleep(0)
        original_get = service.get

        async def pause_after_read(task_id):
            snapshot = await original_get(task_id)
            if snapshot is not None and snapshot.status == "running":
                status_read.set()
                await resume_cancel.wait()
            return snapshot

        monkeypatch.setattr(service, "get", pause_after_read)
        cancelling = asyncio.create_task(service.cancel(task.id))
        await asyncio.wait_for(status_read.wait(), 2)
        release_finish.set()
        await asyncio.wait_for(terminal_saved.wait(), 2)
        resume_cancel.set()
        try:
            assert await asyncio.wait_for(cancelling, 2) is False
            assert (await original_get(task.id)).status == "completed"
        finally:
            release_return.set()


@pytest.mark.asyncio
async def test_parallel_agents_keep_resources_and_cancellation_isolated(
    tmp_path,
) -> None:
    agents = []

    class IsolatedAgent:
        def __init__(self):
            self.started = asyncio.Event()
            self.closed = asyncio.Event()
            self.task_id = None

        async def run(self, goal, *, cancellation, task_id, on_event):
            self.task_id = task_id
            try:
                await on_event(AgentEvent(event_type="task_started", task_id=task_id))
                self.started.set()
                await cancellation.wait()
                await on_event(
                    AgentEvent(event_type="cancel_requested", task_id=task_id)
                )
                await on_event(
                    AgentEvent(
                        event_type="task_finished",
                        task_id=task_id,
                        payload={
                            "status": "cancelled",
                            "completion_level": "none",
                            "stop_reason": "user_cancelled",
                        },
                    )
                )
            finally:
                self.closed.set()

    def agent_factory():
        agent = IsolatedAgent()
        agents.append(agent)
        return agent

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'isolated.db'}",
        DEEPSEEK_API_KEY="fake-key",
        MAX_CONCURRENT_TASKS=2,
    )
    app = create_app(settings=settings, agent_factory=agent_factory)
    async with app.router.lifespan_context(app):
        service = app.state.research
        first = await service.create("First")
        second = await service.create("Second")
        for _ in range(100):
            if len(agents) == 2 and all(agent.started.is_set() for agent in agents):
                break
            await asyncio.sleep(0.01)
        assert len(agents) == 2
        assert {agent.task_id for agent in agents} == {first.id, second.id}
        by_task = {agent.task_id: agent for agent in agents}
        subscription = service.manager.subscribe(second.id)
        assert await service.cancel(first.id) is True
        await asyncio.wait_for(by_task[first.id].closed.wait(), 2)
        assert by_task[second.id].closed.is_set() is False
        assert (await service.get(second.id)).status == "running"
        assert service.manager.subscriber_count(second.id) == 1
        service.manager.unsubscribe(second.id, subscription)
    assert all(agent.closed.is_set() for agent in agents)
    assert service.manager.active_task_count == 0
    assert service.manager.subscriber_count(second.id) == 0


def test_unhandled_agent_error_persists_failure_and_frees_slot(tmp_path) -> None:
    class CrashingAgent:
        async def run(self, goal, *, cancellation, task_id, on_event):
            await on_event(AgentEvent(event_type="task_started", task_id=task_id))
            raise RuntimeError("controlled agent failure")

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'failure.db'}",
        DEEPSEEK_API_KEY="fake-key",
        MAX_CONCURRENT_TASKS=1,
    )
    with TestClient(
        create_app(settings=settings, agent_factory=CrashingAgent)
    ) as client:
        for label in ("First", "Second"):
            created = client.post("/api/research", json={"goal": label})
            assert created.status_code == 202
            task_id = created.json()["id"]
            for _ in range(100):
                detail = client.get(f"/api/research/{task_id}").json()
                if detail["status"] == "failed":
                    break
                time.sleep(0.01)
            assert (detail["status"], detail["stop_reason"]) == (
                "failed",
                "execution_error",
            )
            traces = client.get(f"/api/research/{task_id}/traces").json()
            assert [row["event_type"] for row in traces].count("task_finished") == 1


@pytest.mark.asyncio
async def test_shutdown_finalizes_running_task_as_server_restart(tmp_path) -> None:
    started = asyncio.Event()

    class ShutdownAgent:
        async def run(self, goal, *, cancellation, task_id, on_event):
            await on_event(AgentEvent(event_type="task_started", task_id=task_id))
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                await on_event(
                    AgentEvent(
                        event_type="task_finished",
                        task_id=task_id,
                        payload={
                            "status": "cancelled",
                            "completion_level": "none",
                            "stop_reason": "user_cancelled",
                        },
                    )
                )

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'shutdown.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=ShutdownAgent)
    async with app.router.lifespan_context(app):
        task_id = (await app.state.research.create("Research")).id
        await asyncio.wait_for(started.wait(), 2)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task = await service.get(task_id)
        assert (task.status, (await service.report(task_id)) is not None) == (
            "failed",
            True,
        )
        traces = await service.traces(task_id)
        terminal = [row for row in traces if row.event_type == "task_finished"]
        assert len(terminal) == 1
        assert terminal[0].payload["stop_reason"] == "server_restart"


@pytest.mark.asyncio
async def test_response_status_matches_terminal_trace_during_completion(
    tmp_path, monkeypatch
) -> None:
    from backend.services.persistence import PersistenceService

    started = asyncio.Event()
    release = asyncio.Event()

    class PausedAgent:
        async def run(self, goal, *, cancellation, task_id, on_event):
            await on_event(AgentEvent(event_type="task_started", task_id=task_id))
            started.set()
            await release.wait()

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'snapshot.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )
    app = create_app(settings=settings, agent_factory=PausedAgent)
    async with app.router.lifespan_context(app):
        service = app.state.research
        task_id = (await service.create("Research")).id
        await asyncio.wait_for(started.wait(), 2)
        task = await service.get(task_id)
        assert task.status == "running"
        original_traces = service.traces

        async def finish_before_trace_read(task_id, after_id=0):
            async with service.sessions() as session:
                await PersistenceService(session).record_event(
                    AgentEvent(
                        event_type="task_finished",
                        task_id=task_id,
                        payload={
                            "status": "completed",
                            "completion_level": "full",
                            "stop_reason": "goal_satisfied",
                        },
                    )
                )
            return await original_traces(task_id, after_id)

        monkeypatch.setattr(service, "traces", finish_before_trace_read)
        try:
            response = await _response(service, task)
            assert (response.status, response.completion_level) == (
                "completed",
                "full",
            )
            assert response.stop_reason == "goal_satisfied"
        finally:
            release.set()


def test_rejected_step_does_not_put_unstored_facts_in_report(tmp_path) -> None:
    observed = json.dumps({"description": "FastAPI " + "x" * 10_900})

    class LargeEvidenceProvider(FakeProvider):
        async def complete_structured(self, prompt, schema):
            response = await super().complete_structured(prompt, schema)
            if schema.__name__ == "EvaluationResult":
                facts = [
                    response.value.facts[0].model_copy(
                        update={
                            "id": f"f{index}",
                            "content": f"FastAPI fact {index}",
                            "evidence": observed,
                        }
                    )
                    for index in range(6)
                ]
                value = response.value.model_copy(update={"facts": facts})
                return StructuredCompletion(
                    value, response.prompt_tokens, response.completion_tokens
                )
            return response

    class LargeEvidenceGithub(FakeGithub):
        async def execute(self, action, target, value):
            result = await super().execute(action, target, value)
            return result.model_copy(update={"content": observed})

    settings = Settings(
        _env_file=None,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'large-step.db'}",
        DEEPSEEK_API_KEY="fake-key",
    )

    def agent_factory():
        return make_loop(LargeEvidenceProvider(), LargeEvidenceGithub(), FakeBrowser())

    with TestClient(
        create_app(settings=settings, agent_factory=agent_factory)
    ) as client:
        task_id = client.post(
            "/api/research", json={"goal": "Research FastAPI"}
        ).json()["id"]
        for _ in range(200):
            detail = client.get(f"/api/research/{task_id}").json()
            if detail["status"] == "failed":
                break
            time.sleep(0.01)
        assert (detail["status"], detail["stop_reason"]) == (
            "failed",
            "execution_error",
        )
        traces = client.get(f"/api/research/{task_id}/traces").json()
        assert all(row["event_type"] != "step_evaluated" for row in traces)
        assert detail["report"] is not None
        assert detail["report"]["sources"] == []
        assert detail["report"]["findings"] == []
