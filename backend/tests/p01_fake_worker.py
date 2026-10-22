"""Explicit local-only Worker fixture; no provider or browser is constructed."""

import asyncio
import logging
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.agent.events import AgentEvent
from adaptive_research.infrastructure.config import REPOSITORY_ROOT, get_settings
from adaptive_research.infrastructure.pg_store import PgStore
from adaptive_research.worker.runner import WorkerRunner


class ControlledAgent:
    def __init__(self, control_directory: Path) -> None:
        self.control_directory = control_directory

    async def run(
        self,
        goal,
        *,
        cancellation,
        task_id,
        on_event,
        call_observer,
        resume_state=None,
        prior_events=(),
    ) -> None:
        UUID(task_id)
        release = self.control_directory / f"{task_id}.release"
        await on_event(AgentEvent(event_type="task_started", task_id=task_id))
        call_id = await call_observer.started("tool", "controlled_fake.wait")
        while not cancellation.is_set() and not release.is_file():
            await asyncio.sleep(0.1)
        cancelled = cancellation.is_set()
        await call_observer.finished(
            call_id,
            "failed" if cancelled else "completed",
            error_type="controlled_cancelled" if cancelled else None,
        )
        await on_event(
            AgentEvent(
                event_type="task_finished",
                task_id=task_id,
                payload={
                    "status": "cancelled" if cancelled else "failed",
                    "completion_level": "none",
                    "stop_reason": "user_cancelled"
                    if cancelled
                    else "insufficient_info",
                },
            )
        )


async def main() -> None:
    settings = get_settings()
    database_url = settings.require_postgres_url()
    expected_database = os.environ.get("P01_MEASURE_DATABASE_NAME", "")
    if (
        not expected_database
        or "p01" not in expected_database
        or make_url(database_url).database != expected_database
    ):
        raise ValueError("Controlled Worker requires an explicit P-01 test database")
    if (
        settings.deepseek_api_key is None
        or settings.deepseek_api_key.get_secret_value() != "offline-p01-fake"
        or settings.github_token is not None
    ):
        raise ValueError("Controlled Worker requires the offline fixture credentials")
    raw_directory = os.environ.get("P01_FAKE_CONTROL_DIR", "")
    control_directory = Path(raw_directory)
    if not raw_directory or not control_directory.is_absolute():
        raise ValueError("P01_FAKE_CONTROL_DIR must be absolute")
    control_directory = control_directory.resolve()
    control_directory.relative_to((REPOSITORY_ROOT / "data" / "p01").resolve())
    if not control_directory.is_dir():
        raise ValueError("Controlled Worker directory does not exist")
    engine = create_async_engine(database_url, pool_pre_ping=True)
    store = PgStore(async_sessionmaker(engine, expire_on_commit=False))
    runner = WorkerRunner(
        store,
        settings,
        agent_factory=lambda: ControlledAgent(control_directory),
    )
    try:
        await runner.run_forever()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
