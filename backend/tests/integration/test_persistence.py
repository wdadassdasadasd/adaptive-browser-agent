"""Durable task and event behavior against a temporary SQLite database."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import DecisionContext, ResearchFact, ResearchReport
from adaptive_research.infrastructure.db.base import Base
from adaptive_research.infrastructure.persistence import PersistenceService


@pytest.mark.asyncio
async def test_terminal_status_and_trace_are_atomic(tmp_path, monkeypatch) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'tasks.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task = await PersistenceService(session).create_task("Research")
            task_id = task.id
        event = AgentEvent(
            event_type="task_finished",
            task_id=task_id,
            payload={
                "status": "failed",
                "completion_level": "none",
                "stop_reason": "execution_error",
            },
        )

        async def fail_trace(*_args):
            raise RuntimeError("trace write failed")

        monkeypatch.setattr(PersistenceService, "_save_trace", fail_trace)
        async with sessions() as session:
            with pytest.raises(RuntimeError, match="trace write failed"):
                await PersistenceService(session).record_event(event)
        async with sessions() as session:
            service = PersistenceService(session)
            assert (await service.get_task(task_id)).status == "queued"
            assert [
                trace.event_type for trace in await service.get_task_traces(task_id)
            ] == ["task_queued"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_restart_finalizes_unfinished_task_once(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'restart.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        async with sessions() as session:
            assert await PersistenceService(session).finalize_unfinished() == 1
        async with sessions() as session:
            service = PersistenceService(session)
            assert (await service.get_task(task_id)).status == "failed"
            traces = await service.get_task_traces(task_id)
            assert [trace.event_type for trace in traces] == [
                "task_queued",
                "task_finished",
            ]
            assert traces[-1].payload["stop_reason"] == "server_restart"
            assert await service.finalize_unfinished() == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_restart_report_keeps_fact_subject_and_source(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'facts.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Find FastAPI")).id
        async with sessions() as session:
            await PersistenceService(session).save_fact(
                task_id,
                ResearchFact(
                    content="FastAPI is a framework",
                    source_url="https://fastapi.tiangolo.com/",
                    source_title="Official docs",
                    subject="FastAPI",
                    subject_kind="project",
                ),
            )
        async with sessions() as session:
            await PersistenceService(session).finalize_unfinished()
        async with sessions() as session:
            report = await PersistenceService(session).report_for_task(task_id)
            assert report is not None
            assert report.findings[0].name == "FastAPI"
            assert report.sources == ["https://fastapi.tiangolo.com/"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_restart_report_keeps_persisted_decision_context(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'context.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    context = DecisionContext(
        use_case="Async web API",
        must_have=["async handlers"],
        candidate_projects=["FastAPI", "Flask"],
    )
    try:
        async with sessions() as session:
            task_id = (
                await PersistenceService(session).create_task(
                    "Choose a framework", context
                )
            ).id
        async with sessions() as session:
            assert await PersistenceService(session).finalize_unfinished() == 1
        async with sessions() as session:
            service = PersistenceService(session)
            task = await service.get_task(task_id)
            report = await service.report_for_task(task_id)
            assert task is not None and task.decision_context == context.model_dump(
                mode="json"
            )
            assert report is not None and report.decision is not None
            assert report.decision.use_case == context.use_case
            assert report.decision.must_have == context.must_have
            assert report.decision.preferences == context.preferences
            assert report.decision.candidate_projects == context.candidate_projects
            assert report.decision.recommendation is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_cancel_wins_over_start_and_terminal_event_is_unique(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        cancelled = AgentEvent(
            event_type="task_finished",
            task_id=task_id,
            payload={
                "status": "cancelled",
                "completion_level": "none",
                "stop_reason": "user_cancelled",
            },
        )
        async with sessions() as session:
            assert (
                await PersistenceService(session).cancel_queued(task_id, cancelled)
                is not None
            )
        async with sessions() as session:
            service = PersistenceService(session)
            assert (
                await service.record_event(
                    AgentEvent(event_type="task_started", task_id=task_id)
                )
                is None
            )
        async with sessions() as session:
            service = PersistenceService(session)
            assert await service.record_event(cancelled) is None
            assert (
                await service.record_event(
                    AgentEvent(event_type="cancel_requested", task_id=task_id)
                )
                is None
            )
            traces = await service.get_task_traces(task_id)
            assert [row.event_type for row in traces] == [
                "task_queued",
                "task_finished",
            ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_trace_redacts_configured_secret(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'secret.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        async with sessions() as session:
            await PersistenceService(session, ["secret-sentinel"]).save_trace(
                AgentEvent(
                    event_type="cancel_requested",
                    task_id=task_id,
                    message="secret-sentinel",
                    payload={"note": "secret-sentinel"},
                )
            )
        async with sessions() as session:
            traces = await PersistenceService(session).get_task_traces(task_id)
            assert "secret-sentinel" not in str([trace.payload for trace in traces])
            assert traces[-1].message == "[REDACTED]"
            assert traces[-1].payload["note"] == "[REDACTED]"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_terminal_report_redacts_configured_secret(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'report-secret.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        event = AgentEvent(
            event_type="task_finished",
            task_id=task_id,
            payload={
                "status": "failed",
                "completion_level": "none",
                "stop_reason": "execution_error",
                "report": {
                    "task_id": task_id,
                    "goal": "Research",
                    "title": "Result",
                    "summary": "secret-sentinel",
                    "findings": [],
                    "comparison": "none",
                    "recommendation": "none",
                    "sources": [],
                    "markdown": "secret-sentinel",
                    "generated_at": event_time(),
                },
            },
        )
        async with sessions() as session:
            await PersistenceService(session, ["secret-sentinel"]).record_event(event)
        async with sessions() as session:
            service = PersistenceService(session)
            report = await service.report_for_task(task_id)
            assert report is not None
            assert "secret-sentinel" not in report.model_dump_json()
            assert "secret-sentinel" not in str(
                [trace.payload for trace in await service.get_task_traces(task_id)]
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_save_trace_rejects_terminal_without_status_transition(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'trace-only.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        async with sessions() as session:
            with pytest.raises(ValueError, match="record_event"):
                await PersistenceService(session).save_trace(
                    AgentEvent(
                        event_type="task_finished",
                        task_id=task_id,
                        payload={
                            "status": "failed",
                            "completion_level": "none",
                            "stop_reason": "execution_error",
                        },
                    )
                )
        async with sessions() as session:
            service = PersistenceService(session)
            assert (await service.get_task(task_id)).status == "queued"
            assert [
                row.event_type for row in await service.get_task_traces(task_id)
            ] == ["task_queued"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_repeated_evidence_is_stored_only_once(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dedup.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        async with sessions() as session:
            await PersistenceService(session).record_event(
                AgentEvent(event_type="task_started", task_id=task_id)
            )
        fact = ResearchFact(
            id="fact-1",
            content="FastAPI is a framework",
            source_url="https://fastapi.tiangolo.com/",
            source_title="Official docs",
        )
        for step, candidate in enumerate(
            (fact, fact.model_copy(update={"id": "fact-2"}))
        ):
            event = AgentEvent(
                event_type="step_evaluated",
                task_id=task_id,
                step=step,
                payload={
                    "decision": {
                        "subgoal_id": "s1",
                        "reasoning": "Inspect",
                        "tool": "github",
                        "action": "get_repository",
                        "target": "fastapi/fastapi",
                        "expected_result": "Evidence",
                    },
                    "tool_result": {
                        "tool": "github",
                        "action": "get_repository",
                        "success": True,
                        "content": "Evidence",
                        "source_url": "https://fastapi.tiangolo.com/",
                    },
                    "evaluation": {
                        "success": True,
                        "reason": "Found",
                        "facts": [candidate.model_dump(mode="json")],
                    },
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                },
            )
            async with sessions() as session:
                await PersistenceService(session).record_event(event)
        async with sessions() as session:
            service = PersistenceService(session)
            assert len(await service.get_task_steps(task_id)) == 2
            assert [row.id for row in await service.get_task_facts(task_id)] == [
                "fact-1"
            ]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_direct_fact_saves_deduplicate_same_evidence(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'direct-dedup.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        first = ResearchFact(
            id="fact-first",
            content="FastAPI is a framework",
            source_url="https://fastapi.tiangolo.com/",
            source_title="Official docs",
        )
        duplicate = first.model_copy(
            update={"id": "fact-duplicate", "content": " FASTAPI  is a framework "}
        )
        async with sessions() as session:
            original = await PersistenceService(session).save_fact(task_id, first)
        async with sessions() as session:
            repeated = await PersistenceService(session).save_fact(task_id, duplicate)
            rows = await PersistenceService(session).get_task_facts(task_id)
            assert repeated.id == original.id
            assert [row.id for row in rows] == ["fact-first"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_large_sourced_terminal_report_is_not_lost(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'large-report.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (await PersistenceService(session).create_task("Research")).id
        async with sessions() as session:
            await PersistenceService(session).record_event(
                AgentEvent(event_type="task_started", task_id=task_id)
            )
        source = "https://fastapi.tiangolo.com/"
        report = ResearchReport(
            task_id=task_id,
            goal="Research",
            title="Research",
            summary="Sourced result",
            findings=[],
            comparison="Sourced comparison",
            recommendation="Sourced recommendation",
            sources=[source],
            markdown="Evidence from https://fastapi.tiangolo.com/ " * 2000,
        )
        async with sessions() as session:
            await PersistenceService(session).record_event(
                AgentEvent(
                    event_type="task_finished",
                    task_id=task_id,
                    payload={
                        "status": "completed",
                        "completion_level": "full",
                        "stop_reason": "goal_satisfied",
                        "report": report.model_dump(mode="json"),
                    },
                )
            )
        async with sessions() as session:
            service = PersistenceService(session)
            assert (await service.get_task(task_id)).status == "completed"
            restored = await service.report_for_task(task_id)
            assert restored is not None
            assert restored.markdown == report.markdown
            assert restored.sources == [source]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_restart_report_names_unfinished_subgoal(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'subgoals.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            task_id = (
                await PersistenceService(session).create_task("Compare two projects")
            ).id
        async with sessions() as session:
            service = PersistenceService(session)
            await service.record_event(
                AgentEvent(event_type="task_started", task_id=task_id)
            )
        async with sessions() as session:
            await PersistenceService(session).record_event(
                AgentEvent(
                    event_type="subgoals_initialized",
                    task_id=task_id,
                    payload={
                        "subgoals": [
                            {
                                "id": "s1",
                                "description": "Find first project",
                                "completion_criteria": "One sourced fact",
                            },
                            {
                                "id": "s2",
                                "description": "Compare alternatives",
                                "completion_criteria": "Two sourced facts",
                            },
                        ]
                    },
                )
            )
        async with sessions() as session:
            await PersistenceService(session).save_fact(
                task_id,
                ResearchFact(
                    content="FastAPI is a framework",
                    source_url="https://fastapi.tiangolo.com/",
                    source_title="Official docs",
                ),
            )
        async with sessions() as session:
            await PersistenceService(session).finalize_unfinished()
        async with sessions() as session:
            report = await PersistenceService(session).report_for_task(task_id)
            assert report is not None
            assert "Find first project" in report.markdown
            assert "Compare alternatives" in report.markdown
    finally:
        await engine.dispose()


def event_time() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()
