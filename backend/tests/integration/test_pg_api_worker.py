"""Offline API-to-Worker integration on a disposable PostgreSQL database."""

import asyncio
import os
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.agent.decision import DecisionService
from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import DecisionContext
from adaptive_research.api.pg_main import create_app
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_models import PgFact
from adaptive_research.infrastructure.pg_store import PgStore
from adaptive_research.worker.runner import WorkerRunner
from tests.integration.test_agent_loop import (
    FakeBrowser,
    FakeGithub,
    FakeProvider,
    make_loop,
)
from tests.unit.test_decision import JudgmentLLM, row


class FakeAgent:
    def __init__(self, gate: asyncio.Event | None = None) -> None:
        self.gate = gate

    async def run(self, goal, *, cancellation, task_id, on_event, call_observer):
        await on_event(AgentEvent(event_type="task_started", task_id=task_id))
        call_id = await call_observer.started("tool", "controlled_fake")
        if self.gate is not None:
            await self.gate.wait()
        await call_observer.finished(call_id, "completed")
        await on_event(AgentEvent(event_type="step_evaluated", task_id=task_id, step=1))
        await on_event(
            AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                step=1,
                payload={
                    "status": "failed",
                    "completion_level": "none",
                    "stop_reason": "insufficient_info",
                },
            )
        )


class ContextCapturingAgent:
    def __init__(self) -> None:
        self.received: list[tuple[DecisionContext, object, object]] = []

    async def run(
        self,
        goal,
        *,
        task_id,
        on_event,
        decision_context,
        resume_state=None,
        prior_events=(),
        **kwargs,
    ):
        self.received.append((decision_context, resume_state, prior_events))
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


@pytest.mark.skipif(
    not (os.getenv("P01_TEST_DATABASE_NAME") or os.getenv("P01_TEST_DATABASE_URL")),
    reason="requires a fresh disposable PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_postgres_api_worker_replay_and_capacity(monkeypatch) -> None:
    original = Settings().require_postgres_url()
    name = os.getenv("P01_TEST_DATABASE_NAME")
    url = (
        make_url(original).set(database=name).render_as_string(hide_password=False)
        if name
        else os.environ["P01_TEST_DATABASE_URL"]
    )
    if make_url(url).database == make_url(original).database:
        pytest.fail("Test database must differ from the application database")
    engine = create_async_engine(url, pool_pre_ping=True)
    migration_ini = Path(__file__).resolve().parents[2] / "migrations" / "alembic.ini"
    migrated = False
    try:
        async with engine.connect() as connection:
            existing = set(
                await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            )
        if existing - {"alembic_version"}:
            pytest.fail("Disposable test database contains non-Alembic tables")
        if "alembic_version" in existing:
            async with engine.connect() as connection:
                version_count = await connection.scalar(
                    text("SELECT count(*) FROM alembic_version")
                )
            if version_count:
                pytest.fail("Disposable test database has an applied migration")
        monkeypatch.setenv("P01_DATABASE_URL", url)
        await asyncio.to_thread(command.upgrade, Config(str(migration_ini)), "head")
        migrated = True

        settings = Settings(
            _env_file=None,
            P01_DATABASE_URL=url,
            DEEPSEEK_API_KEY="offline-test-key",
        )
        app = create_app(settings)
        store = PgStore(async_sessionmaker(engine, expire_on_commit=False))
        runner = WorkerRunner(store, settings, agent_factory=FakeAgent)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client,
        ):
            created = await client.post(
                "/api/research",
                json={"goal": "offline"},
                headers={"Idempotency-Key": "pilot-test-run-001"},
            )
            assert created.status_code == 202
            task_id = created.json()["id"]
            assert created.json()["status"] == "queued"
            retry = await client.post(
                "/api/research",
                json={"goal": "offline", "decision_context": None},
                headers={"Idempotency-Key": "pilot-test-run-001"},
            )
            assert retry.status_code == 202 and retry.json()["id"] == task_id
            conflict = await client.post(
                "/api/research",
                json={"goal": "different"},
                headers={"Idempotency-Key": "pilot-test-run-001"},
            )
            assert conflict.status_code == 409
            invalid = await client.post(
                "/api/research",
                json={"goal": "offline"},
                headers={"Idempotency-Key": "invalid key"},
            )
            assert invalid.status_code == 422
            assert await runner.tick() == 1
            await asyncio.gather(*runner.active.values())
            detail = await client.get(f"/api/research/{task_id}")
            assert detail.json()["status"] == "failed"
            traces = (await client.get(f"/api/research/{task_id}/traces")).json()
            assert [item["event_type"] for item in traces] == [
                "task_queued",
                "task_started",
                "step_evaluated",
                "task_finished",
            ]
            replay = await client.get(
                f"/api/research/{task_id}/events",
                headers={"Last-Event-ID": traces[0]["event_id"]},
            )
            assert replay.status_code == 200
            assert replay.text.count("event: ") == 3
            assert "event: task_finished" in replay.text
            assert (
                await client.get(
                    f"/api/research/{task_id}/events",
                    headers={"Last-Event-ID": "not-a-uuid"},
                )
            ).status_code == 422

            factual = await client.post(
                "/api/research", json={"goal": "Research FastAPI"}
            )
            fact_id = factual.json()["id"]
            fact_runner = WorkerRunner(
                store,
                settings,
                agent_factory=lambda: make_loop(
                    FakeProvider(), FakeGithub(), FakeBrowser()
                ),
            )
            assert await fact_runner.tick() == 1
            await asyncio.gather(*fact_runner.active.values())
            factual_detail = await client.get(f"/api/research/{fact_id}")
            assert factual_detail.json()["status"] == "completed"
            async with engine.connect() as connection:
                fact_count = await connection.scalar(
                    select(func.count(PgFact.id)).where(PgFact.task_id == fact_id)
                )
            assert fact_count >= 1
            persisted = await store.get_task("p01-local-owner", fact_id)
            restored_state, history = await fact_runner._recovery_snapshot(persisted)
            assert restored_state.facts
            assert any(event.event_type == "step_evaluated" for event in history)
            stored_facts = await store.list_facts("p01-local-owner", fact_id)
            assert [item.id for item in stored_facts] == [
                item.id for item in restored_state.facts
            ]
            assert len(stored_facts) == 1
            assert stored_facts[0].subject == restored_state.facts[0].subject
            assert stored_facts[0].official_source_url == str(
                restored_state.facts[0].source_url
            )
            assert stored_facts[0].evidence_excerpt == restored_state.facts[0].evidence
            assert stored_facts[0].retrieved_at == restored_state.facts[0].created_at
            assert stored_facts[0].machine_admission_status == (
                "candidate_unverified_official"
            )
            assert stored_facts[0].human_review_status is None
            matrix_state = restored_state.model_copy(
                update={
                    "decision_context": DecisionContext(
                        use_case="Offline framework comparison",
                        must_have=["documented framework", "unknown license"],
                        candidate_projects=["FastAPI", "Flask"],
                    )
                }
            )
            candidates = (await DecisionService().build(matrix_state)).candidates
            fastapi_id = next(
                item.candidate_id for item in candidates if item.label == "FastAPI"
            )
            flask_id = next(
                item.candidate_id for item in candidates if item.label == "Flask"
            )
            matrix = await DecisionService(
                JudgmentLLM(
                    [
                        row(
                            fastapi_id,
                            "documented framework",
                            "satisfied",
                            [stored_facts[0].id],
                        ),
                        row(
                            flask_id,
                            "documented framework",
                            "satisfied",
                            [stored_facts[0].id],
                        ),
                    ]
                )
            ).build(matrix_state)
            assert [item.verdict for item in matrix.matrix] == [
                "satisfied",
                "unknown",
                "unknown",
                "unknown",
            ]
            assert matrix.matrix[0].supporting_fact_ids == [stored_facts[0].id]
            assert matrix.evidence_facts[0].fact_id == stored_facts[0].id
            assert matrix.evidence_facts[0].observed_at == stored_facts[0].retrieved_at
            assert matrix.verification_status == "machine_admitted_human_unverified"

            context_body = {
                "goal": "Choose a framework",
                "decision_context": {
                    "use_case": " Python API ",
                    "must_have": [" MIT "],
                    "preferences": [" test-secret-marker-642 "],
                    "candidate_projects": ["Flask", "FastAPI"],
                },
            }
            context_created = await client.post(
                "/api/research",
                json=context_body,
                headers={"Idempotency-Key": "decision-context-001"},
            )
            assert context_created.status_code == 202
            context_id = context_created.json()["id"]
            assert context_created.json()["decision_context"] == {
                "use_case": "Python API",
                "must_have": ["MIT"],
                "preferences": ["test-secret-marker-642"],
                "candidate_projects": ["Flask", "FastAPI"],
            }
            context_replay = await client.post(
                "/api/research",
                json={
                    "goal": " Choose a framework ",
                    "decision_context": context_created.json()["decision_context"],
                },
                headers={"Idempotency-Key": "decision-context-001"},
            )
            assert context_replay.status_code == 202
            assert context_replay.json()["id"] == context_id
            context_conflict = await client.post(
                "/api/research",
                json={
                    "goal": "Choose a framework",
                    "decision_context": {
                        **context_created.json()["decision_context"],
                        "preferences": ["different preference"],
                    },
                },
                headers={"Idempotency-Key": "decision-context-001"},
            )
            assert context_conflict.status_code == 409
            assert len(await store.list_tasks("p01-local-owner")) == 3
            persisted_context = await store.get_task("p01-local-owner", context_id)
            assert (
                persisted_context.decision_context
                == context_created.json()["decision_context"]
            )
            context_agent = ContextCapturingAgent()
            context_runner = WorkerRunner(
                store, settings, agent_factory=lambda: context_agent
            )
            assert await context_runner.tick() == 1
            await asyncio.gather(*context_runner.active.values())
            assert context_agent.received == [
                (
                    DecisionContext.model_validate(persisted_context.decision_context),
                    None,
                    (),
                )
            ]
            persisted_context = await store.get_task("p01-local-owner", context_id)
            recovered_context, _ = await context_runner._recovery_snapshot(
                persisted_context
            )
            assert recovered_context.decision_context == context_agent.received[0][0]
            assert "test-secret-marker-642" not in str(
                [
                    event.payload
                    for event in await store.list_events("p01-local-owner", context_id)
                ]
            )

            gate = asyncio.Event()
            blocked = WorkerRunner(
                store, settings, agent_factory=lambda: FakeAgent(gate)
            )
            initial = [
                (await client.post("/api/research", json={"goal": str(i)})).json()
                for i in range(8)
            ]
            assert await blocked.tick() == 2
            extra = [
                await client.post("/api/research", json={"goal": str(i)})
                for i in (8, 9)
            ]
            assert all(item.status_code == 202 for item in extra)
            rejected = await client.post("/api/research", json={"goal": "eleventh"})
            assert rejected.status_code == 429
            assert rejected.headers["Retry-After"] == "2"
            assert len(await store.list_tasks("p01-local-owner")) == 13
            cancelled = await client.post(f"/api/research/{initial[-1]['id']}/cancel")
            assert cancelled.json()["cancelled"] is True
            assert (
                await client.post("/api/research", json={"goal": "replacement"})
            ).status_code == 202
            gate.set()
            await asyncio.gather(*blocked.active.values())
    finally:
        await engine.dispose()
        if migrated:
            await asyncio.to_thread(
                command.downgrade, Config(str(migration_ini)), "base"
            )
