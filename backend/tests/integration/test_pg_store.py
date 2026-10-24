"""P-01 PostgreSQL ledger tests; opt in with an empty P01_TEST_DATABASE_URL."""

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.agent.llm.base import ProviderUsage
from adaptive_research.agent.state import utc_now
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_models import (
    PgBase,
    PgCallAttempt,
    PgEvent,
    PgFact,
    PgTask,
)
from adaptive_research.infrastructure.pg_store import (
    CapacityFull,
    FenceLost,
    IdempotencyConflict,
    PgStore,
    PricingUnavailable,
)
from adaptive_research.infrastructure.pricing import load_price_book
from adaptive_research.worker.runner import PgCallObserver


def test_postgres_metadata_is_separate_from_v1_sqlite() -> None:
    names = set(PgBase.metadata.tables)
    assert {
        "app_owner",
        "scheduler_guard",
        "app_task",
        "app_event",
        "app_call_attempt",
        "app_fact",
        "app_report",
        "app_cost",
        "app_budget",
    } <= names
    assert "research_task" not in names


@pytest.mark.skipif(
    not (os.getenv("P01_TEST_DATABASE_URL") or os.getenv("P01_TEST_DATABASE_NAME")),
    reason="set P01_TEST_DATABASE_URL or P01_TEST_DATABASE_NAME for a fresh disposable database",
)
@pytest.mark.asyncio
async def test_postgres_capacity_fifo_fencing_recovery_and_events(monkeypatch) -> None:
    original = Settings().require_postgres_url()
    test_name = os.getenv("P01_TEST_DATABASE_NAME")
    url = (
        make_url(original).set(database=test_name).render_as_string(hide_password=False)
        if test_name
        else os.getenv("P01_TEST_DATABASE_URL")
    )
    if not url:
        pytest.skip("set a fresh disposable PostgreSQL test database")
    parsed = make_url(url)
    if parsed.drivername != "postgresql+asyncpg":
        pytest.fail("P01_TEST_DATABASE_URL must use postgresql+asyncpg")
    if parsed.database == make_url(original).database:
        pytest.fail(
            "The PostgreSQL test database must differ from the application database"
        )

    engine = create_async_engine(url, pool_pre_ping=True)
    tables_created = False
    try:
        async with engine.connect() as connection:
            existing = set(
                await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            )
        if existing - {"alembic_version"}:
            pytest.fail("PostgreSQL test database contains non-Alembic tables")
        if "alembic_version" in existing:
            async with engine.connect() as connection:
                version_count = await connection.scalar(
                    text("SELECT count(*) FROM alembic_version")
                )
            if version_count:
                pytest.fail("PostgreSQL test database has an applied migration")
        migration_ini = (
            Path(__file__).resolve().parents[2] / "migrations" / "alembic.ini"
        )
        monkeypatch.setenv("P01_DATABASE_URL", url)
        await asyncio.to_thread(command.upgrade, Config(str(migration_ini)), "head")
        tables_created = True

        store = PgStore(async_sessionmaker(engine, expire_on_commit=False))
        waiting = [
            await store.create_task(
                "synthetic-owner",
                f"goal-{n}",
                idempotency_key=f"p01-test-key-{n}",
                decision_context=(
                    {
                        "use_case": "Python API",
                        "must_have": ["MIT"],
                        "preferences": ["test-secret-marker-642"],
                        "candidate_projects": ["FastAPI", "Flask"],
                    }
                    if n == 0
                    else None
                ),
            )
            for n in range(8)
        ]
        replayed = await store.create_task(
            "synthetic-owner",
            "goal-0",
            idempotency_key="p01-test-key-0",
            decision_context={
                "use_case": " Python API ",
                "must_have": [" MIT "],
                "preferences": [" test-secret-marker-642 "],
                "candidate_projects": ["FastAPI", "Flask"],
            },
        )
        assert replayed.id == waiting[0].id
        assert replayed.decision_context["must_have"] == ["MIT"]
        assert [
            event.event_type
            for event in await store.list_events("synthetic-owner", waiting[0].id)
        ] == ["task_queued"]
        assert "test-secret-marker-642" not in str(
            (await store.list_events("synthetic-owner", waiting[0].id))[0].payload
        )
        concurrent_replays = await asyncio.gather(
            *(
                store.create_task(
                    "synthetic-owner",
                    "goal-0",
                    idempotency_key="p01-test-key-0",
                    decision_context=replayed.decision_context,
                )
                for _ in range(2)
            )
        )
        assert [task.id for task in concurrent_replays] == [waiting[0].id] * 2
        legacy_replay = await store.create_task(
            "synthetic-owner",
            "goal-1",
            idempotency_key="p01-test-key-1",
            decision_context=None,
        )
        assert legacy_replay.id == waiting[1].id
        assert (
            await store.get_task_by_idempotency_key("synthetic-owner", "p01-test-key-0")
        ).id == waiting[0].id
        assert (
            await store.get_task_by_idempotency_key("other-owner", "p01-test-key-0")
            is None
        )
        with pytest.raises(IdempotencyConflict):
            await store.create_task(
                "synthetic-owner", "different goal", idempotency_key="p01-test-key-0"
            )
        with pytest.raises(IdempotencyConflict):
            await store.create_task(
                "synthetic-owner",
                "goal-0",
                idempotency_key="p01-test-key-0",
                decision_context={
                    "use_case": "Python API",
                    "must_have": ["Apache-2.0"],
                },
            )
        for different_context in (
            {
                "use_case": "Python CLI",
                "must_have": ["MIT"],
                "preferences": ["test-secret-marker-642"],
                "candidate_projects": ["FastAPI", "Flask"],
            },
            {
                "use_case": "Python API",
                "must_have": ["MIT"],
                "preferences": ["small footprint"],
                "candidate_projects": ["FastAPI", "Flask"],
            },
            {
                "use_case": "Python API",
                "must_have": ["MIT"],
                "preferences": ["test-secret-marker-642"],
                "candidate_projects": ["Flask", "FastAPI"],
            },
        ):
            with pytest.raises(IdempotencyConflict):
                await store.create_task(
                    "synthetic-owner",
                    "goal-0",
                    idempotency_key="p01-test-key-0",
                    decision_context=different_context,
                )
        assert len(await store.list_tasks("synthetic-owner")) == 8
        first, second = await asyncio.gather(
            store.claim_next("worker-a", lease_seconds=30),
            store.claim_next("worker-b", lease_seconds=30),
        )
        assert {first.id, second.id} == {waiting[0].id, waiting[1].id}
        assert first.fencing_token == second.fencing_token == 1
        assert await store.claim_next("worker-c") is None
        more = [await store.create_task("synthetic-owner", f"goal-{n}") for n in (8, 9)]
        with pytest.raises(CapacityFull):
            await store.create_task("synthetic-owner", "eleventh")
        assert len(await store.list_tasks("synthetic-owner")) == 10
        assert await store.get_task("other-owner", first.id) is None
        assert await store.list_events("other-owner", first.id) is None

        queued = await store.request_cancel("synthetic-owner", more[1].id)
        assert queued.status == "cancelled"
        replacement = await store.create_task("synthetic-owner", "replacement")
        assert replacement.status == "queued"
        assert await store.request_cancel("synthetic-owner", first.id)
        assert (
            await store.get_task("synthetic-owner", first.id)
        ).cancellation_requested

        call = await store.start_call(
            first.id, first.fencing_token, phase="tool", kind="browser"
        )
        assert call.status == "started"
        finished = await store.finish_task(
            first.id,
            first.fencing_token,
            "cancelled",
            stop_reason="user_cancelled",
        )
        assert finished.status == "cancelled"
        assert (await store.list_calls("synthetic-owner", first.id))[
            0
        ].status == "unknown_outcome"

        # A failed event serialization must roll back its accompanying facts.
        with pytest.raises(StatementError):
            await store.append_event(
                second.id,
                second.fencing_token,
                "step_evaluated",
                payload={"not_json": object()},
                facts=[
                    {
                        "id": "must-rollback",
                        "subject": "synthetic",
                        "claim": "synthetic fact",
                        "official_source_url": "https://example.org/fixture",
                        "retrieved_at": utc_now(),
                        "machine_admission_status": "candidate_unverified_official",
                    }
                ],
            )
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    select(PgFact.id).where(PgFact.id == "must-rollback")
                )
                is None
            )
        assert len(await store.list_events("synthetic-owner", second.id)) == 2

        await store.append_event(
            second.id,
            second.fencing_token,
            "step_evaluated",
            facts=[
                {
                    "id": "persisted-fact",
                    "subject": "synthetic",
                    "claim": "source has a license",
                    "official_source_url": "https://example.org/fixture",
                    "retrieved_at": utc_now(),
                    "machine_admission_status": "candidate_unverified_official",
                    "official_identity_basis": "fixture owner",
                    "evidence_excerpt": "license",
                    "evidence_locator": "LICENSE:1",
                }
            ],
        )
        assert await store.list_facts("other-owner", second.id) is None
        visible_facts = await store.list_facts("synthetic-owner", second.id)
        assert len(visible_facts) == 1
        assert visible_facts[0].id == "persisted-fact"
        assert visible_facts[0].official_identity_basis == "fixture owner"
        assert visible_facts[0].human_review_status is None

        local_tool = await store.start_call(
            second.id,
            second.fencing_token,
            phase="github.get_repository",
            kind="tool",
            execution_source_sha256="a" * 64,
        )
        priced_tool = await store.fail_call(
            second.id,
            second.fencing_token,
            local_tool.id,
            failure_type="technical",
        )
        assert priced_tool.known_cost_cny == 0
        assert priced_tool.cost_basis == "public_github_rest_get_v1"
        assert priced_tool.execution_source_sha256 == "a" * 64
        unpriced = await store.start_call(
            second.id, second.fencing_token, phase="model", kind="model"
        )
        await store.complete_call(
            second.id,
            second.fencing_token,
            unpriced.id,
            prompt_tokens=7,
            completion_tokens=3,
        )
        cost = await store.get_cost("synthetic-owner", second.id)
        assert cost.known_cost_cny == 0 and cost.unknown_attempt_count == 1
        with pytest.raises(FenceLost):
            await store.complete_call(
                second.id,
                second.fencing_token,
                unpriced.id,
                prompt_tokens=7,
                completion_tokens=3,
            )
        with pytest.raises(FenceLost):
            await store.append_event(first.id, first.fencing_token, "step_evaluated")
        third = await store.claim_next("worker-c")
        assert third.id == waiting[2].id
        assert await store.renew_lease(third.id, third.fencing_token, "worker-c")
        assert not await store.renew_lease(third.id, third.fencing_token, "worker-a")

        # Force expiry in the disposable database to avoid a wall-clock sleep.
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_task SET lease_expires_at = clock_timestamp() - interval '1 second' WHERE id = :id"
                ),
                {"id": third.id},
            )
        changed = await store.reconcile_expired()
        assert [row.id for row in changed] == [third.id]
        assert changed[0].status == "queued" and changed[0].recovery_count == 1
        with pytest.raises(FenceLost):
            await store.append_event(third.id, third.fencing_token, "step_evaluated")
        # Recovery retains original submission order, then the second expiry terminates it.
        recovered = await store.claim_next("worker-d")
        assert (
            recovered.id == third.id
            and recovered.fencing_token == third.fencing_token + 1
        )
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_task SET lease_expires_at = clock_timestamp() - interval '1 second' WHERE id = :id"
                ),
                {"id": recovered.id},
            )
        changed = await store.reconcile_expired()
        assert [row.id for row in changed] == [recovered.id]
        assert (
            changed[0].status == "failed"
            and changed[0].stop_reason == "second_worker_failure"
        )

        events = await store.list_events("synthetic-owner", first.id)
        assert [event.event_type for event in events] == [
            "task_queued",
            "task_started",
            "cancel_requested",
            "task_finished",
        ]
        assert [event.id for event in events] == sorted(event.id for event in events)
        assert [
            event.id
            for event in await store.list_events(
                "synthetic-owner", first.id, events[1].id
            )
        ] == [events[2].id, events[3].id]
        async with engine.connect() as connection:
            terminal_events = await connection.scalar(
                select(func.count(PgEvent.id)).where(
                    PgEvent.task_id == first.id, PgEvent.event_type == "task_finished"
                )
            )
            assert terminal_events == 1
            assert (
                await connection.scalar(select(PgTask).where(PgTask.goal == "eleventh"))
                is None
            )
            assert (
                await connection.scalar(
                    select(PgCallAttempt).where(PgCallAttempt.id == call.id)
                )
                is not None
            )
        # Price against a frozen simulated clock, never today's changing tariff.
        # Only this claimed task is altered in the refused-unless-empty test DB.
        priced_task = await store.claim_next("priced-fixture")
        book = load_price_book(
            Path(__file__).resolve().parents[3]
            / "docs/evaluation/DEEPSEEK_CNY_PRICING_2026-10-21.json"
        )
        fixed_now = datetime.fromisoformat(book["verified_at"]) + timedelta(minutes=10)
        async with engine.begin() as connection:
            await connection.execute(
                text("UPDATE app_task SET lease_expires_at = :expires WHERE id = :id"),
                {"expires": fixed_now + timedelta(hours=1), "id": priced_task.id},
            )
        priced = PgStore(store.sessions, price_book=book)

        async def fixed_clock(session):
            return fixed_now

        monkeypatch.setattr(priced, "_now", fixed_clock)
        observer = PgCallObserver(
            priced, priced_task.id, priced_task.fencing_token, "deepseek-flash"
        )
        priced_call_id = await observer.started("model", "deepseek.http")
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_call_attempt SET started_at = :started WHERE id = :id"
                ),
                {"started": fixed_now, "id": priced_call_id},
            )
        await observer.finished(
            priced_call_id,
            "completed",
            prompt_tokens=100,
            completion_tokens=20,
            provider_usage=ProviderUsage(
                prompt_cache_hit_tokens=40,
                prompt_cache_miss_tokens=60,
                provider_created_at=int(fixed_now.timestamp()),
                reported_model="DeepSeek-V4.1-Flash-1017",
                system_fingerprint="fixture",
            ),
        )
        saved = (await priced.list_calls("synthetic-owner", priced_task.id))[0]
        assert saved.known_cost_cny == Decimal("0.0001408")
        assert saved.prompt_cache_hit_tokens == 40
        assert saved.prompt_cache_miss_tokens == 60
        assert saved.reported_model == "DeepSeek-V4.1-Flash-1017"
        assert saved.system_fingerprint == "fixture"
        assert saved.pricing_tariff == "off_peak" and saved.pricing_error is None
        assert saved.price_revision == book["price_revision"]

        async def stale_clock(session):
            return datetime.fromisoformat(book["valid_until"])

        monkeypatch.setattr(priced, "_now", stale_clock)
        # Keep the synthetic lease live while testing price expiration itself.
        async with engine.begin() as connection:
            await connection.execute(
                text("UPDATE app_task SET lease_expires_at = :expires WHERE id = :id"),
                {
                    "expires": datetime.fromisoformat(book["valid_until"])
                    + timedelta(hours=1),
                    "id": priced_task.id,
                },
            )
        with pytest.raises(PricingUnavailable):
            await observer.started("model", "deepseek.http")
        assert len(await priced.list_calls("synthetic-owner", priced_task.id)) == 1
        monkeypatch.setattr(priced, "_now", fixed_clock)

        unpriced_id = await observer.started("model", "deepseek.http")
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_call_attempt SET started_at = :started WHERE id = :id"
                ),
                {"started": fixed_now, "id": unpriced_id},
            )
        with pytest.raises(PricingUnavailable):
            await observer.finished(
                unpriced_id, "completed", prompt_tokens=100, completion_tokens=20
            )
        saved_calls = await priced.list_calls("synthetic-owner", priced_task.id)
        unpriced_call = next(row for row in saved_calls if row.id == unpriced_id)
        assert unpriced_call.status == "completed"
        assert unpriced_call.known_cost_cny is None
        assert unpriced_call.pricing_error == "unsupported_model"
        cost = await priced.get_cost("synthetic-owner", priced_task.id)
        assert (
            cost.known_cost_cny == Decimal("0.0001408")
            and cost.unknown_attempt_count == 1
        )
        with pytest.raises(PricingUnavailable):
            await observer.started("model", "deepseek.http")
        assert len(await priced.list_calls("synthetic-owner", priced_task.id)) == 2
    finally:
        await engine.dispose()
        if tables_created:
            # The test refuses pre-existing application tables, so only its own DDL is removed.
            await asyncio.to_thread(
                command.downgrade, Config(str(migration_ini)), "base"
            )


@pytest.mark.skipif(
    not (os.getenv("P01_TEST_DATABASE_URL") or os.getenv("P01_TEST_DATABASE_NAME")),
    reason="set an empty disposable P01 PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_pilot_budget_blocks_unpriced_calls_across_tasks(monkeypatch) -> None:
    original = Settings().require_postgres_url()
    test_name = os.getenv("P01_TEST_DATABASE_NAME")
    url = (
        make_url(original).set(database=test_name).render_as_string(hide_password=False)
        if test_name
        else os.environ["P01_TEST_DATABASE_URL"]
    )
    if make_url(url).database == make_url(original).database:
        pytest.fail("Budget test database must differ from application database")
    engine = create_async_engine(url, pool_pre_ping=True)
    migration_ini = Path(__file__).resolve().parents[2] / "migrations" / "alembic.ini"
    migrated = False
    try:
        async with engine.connect() as connection:
            existing = set(
                await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            )
        if existing - {"alembic_version"}:
            pytest.fail("Budget test database contains application tables")
        if "alembic_version" in existing:
            async with engine.connect() as connection:
                if await connection.scalar(
                    text("SELECT count(*) FROM alembic_version")
                ):
                    pytest.fail("Budget test database already has applied migrations")
        monkeypatch.setenv("P01_DATABASE_URL", url)
        await asyncio.to_thread(command.upgrade, Config(str(migration_ini)), "head")
        migrated = True
        book = load_price_book(
            Path(__file__).resolve().parents[3]
            / "docs/evaluation/DEEPSEEK_CNY_PRICING_2026-10-21.json"
        )
        fixed_now = datetime.fromisoformat(book["verified_at"]) + timedelta(minutes=10)
        store = PgStore(
            async_sessionmaker(engine, expire_on_commit=False),
            price_book=book,
            require_budget=True,
        )

        async def fixed_clock(session):
            return fixed_now

        monkeypatch.setattr(store, "_now", fixed_clock)
        with pytest.raises(ValueError):
            await store.arm_pilot_budget(
                authorization_reference="synthetic-test", phase_max_cny=Decimal(50)
            )
        await store.arm_pilot_budget(
            authorization_reference="synthetic-test", phase_max_cny=Decimal(2)
        )
        assert (await store.get_budget()).price_book_sha256 == book["snapshot_sha256"]
        with pytest.raises(PricingUnavailable):
            await store.arm_pilot_budget(
                authorization_reference="synthetic-test", phase_max_cny=Decimal(2)
            )
        tasks = [
            await store.create_task("synthetic-owner", f"budget-{i}") for i in range(2)
        ]
        claimed = [await store.claim_next(f"worker-{i}") for i in range(2)]
        assert {row.id for row in claimed} == {row.id for row in tasks}
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_task SET lease_expires_at = :expires WHERE id = ANY(:ids)"
                ),
                {
                    "expires": fixed_now + timedelta(hours=1),
                    "ids": [row.id for row in claimed],
                },
            )
        first = PgCallObserver(
            store, claimed[0].id, claimed[0].fencing_token, "deepseek-flash"
        )
        second = PgCallObserver(
            store, claimed[1].id, claimed[1].fencing_token, "deepseek-flash"
        )
        mismatched_book = dict(book)
        mismatched_book["snapshot_sha256"] = "0" * 64
        mismatched = PgStore(
            store.sessions, price_book=mismatched_book, require_budget=True
        )
        monkeypatch.setattr(mismatched, "_now", fixed_clock)
        with pytest.raises(PricingUnavailable):
            await mismatched.start_call(
                claimed[1].id,
                claimed[1].fencing_token,
                phase="deepseek.http",
                kind="model",
                model="deepseek-flash",
            )
        call_id = await first.started("model", "deepseek.http")
        with pytest.raises(PricingUnavailable):
            await second.started("model", "deepseek.http")
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_call_attempt SET started_at = :started WHERE id = :id"
                ),
                {"started": fixed_now, "id": call_id},
            )
        await first.finished(
            call_id,
            "completed",
            prompt_tokens=100,
            completion_tokens=20,
            provider_usage=ProviderUsage(
                prompt_cache_hit_tokens=40,
                prompt_cache_miss_tokens=60,
                reported_model="DeepSeek-V4.1-Flash-1017",
            ),
        )
        assert (await store.get_budget()).status == "armed"
        # Simulate a tighter approved ceiling; a new call must reserve its
        # worst-case allowance before any provider request is sent.
        async with engine.begin() as connection:
            await connection.execute(text("UPDATE app_budget SET phase_max_cny = 1"))
        with pytest.raises(PricingUnavailable):
            await second.started("model", "deepseek.http")
        async with engine.begin() as connection:
            await connection.execute(text("UPDATE app_budget SET phase_max_cny = 2"))
        unpriced_id = await second.started("model", "deepseek.http")
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE app_call_attempt SET started_at = :started WHERE id = :id"
                ),
                {"started": fixed_now, "id": unpriced_id},
            )
        with pytest.raises(PricingUnavailable):
            await second.finished(
                unpriced_id, "completed", prompt_tokens=100, completion_tokens=20
            )
        budget = await store.get_budget()
        assert budget.status == "halted" and budget.halt_reason == "unknown_model_cost"
        with pytest.raises(PricingUnavailable):
            await first.started("model", "deepseek.http")
        missing_book = PgStore(store.sessions)
        monkeypatch.setattr(missing_book, "_now", fixed_clock)
        with pytest.raises(PricingUnavailable):
            await missing_book.start_call(
                claimed[0].id,
                claimed[0].fencing_token,
                phase="deepseek.http",
                kind="model",
                model="deepseek-flash",
            )
        assert len(await store.list_calls("synthetic-owner", claimed[0].id)) == 1
        assert len(await store.list_calls("synthetic-owner", claimed[1].id)) == 1
    finally:
        await engine.dispose()
        if migrated:
            await asyncio.to_thread(
                command.downgrade, Config(str(migration_ini)), "base"
            )
