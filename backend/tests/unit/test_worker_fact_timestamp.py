"""Worker persistence must use observed event time for fact retrieval."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import ResearchFact
from adaptive_research.infrastructure.config import Settings
from adaptive_research.worker.runner import WorkerRunner


class RecordingStore:
    require_budget = False

    def __init__(self) -> None:
        self.facts: list[dict] = []

    async def append_event(self, task_id, token, event_type, **kwargs):
        self.facts.extend(kwargs.get("facts", []))

    async def mark_unknown_calls(self, task_id, token):
        return None

    async def finish_task(self, task_id, token, status, **kwargs):
        return None


@pytest.mark.asyncio
async def test_worker_fact_retrieval_uses_event_time_not_model_time() -> None:
    observed_at = datetime(2026, 10, 23, 5, 1, tzinfo=UTC)
    model_time = datetime(2026, 10, 16, tzinfo=UTC)
    fact = ResearchFact(
        id="f1",
        content="Release 0.13.13 is Latest",
        source_url="https://github.com/browser-use/browser-use/releases/tag/0.13.13",
        source_title="Release page",
        evidence="0.13.13 Latest",
        created_at=model_time,
    )

    class Agent:
        async def run(self, goal, *, cancellation, task_id, on_event, call_observer):
            await on_event(
                AgentEvent(
                    event_type="step_evaluated",
                    task_id=task_id,
                    timestamp=observed_at,
                    payload={
                        "evaluation": {
                            "success": True,
                            "facts": [fact.model_dump(mode="json")],
                        }
                    },
                )
            )
            await on_event(
                AgentEvent(
                    event_type="task_finished",
                    task_id=task_id,
                    payload={
                        "status": "partial",
                        "completion_level": "partial",
                        "stop_reason": "token_budget",
                    },
                )
            )

    store = RecordingStore()
    settings = Settings(
        _env_file=None,
        P01_DATABASE_URL="postgresql+asyncpg://user@localhost/test",
    )
    runner = WorkerRunner(store, settings, agent_factory=Agent)
    task = SimpleNamespace(
        id="task-1",
        owner_id="owner-1",
        goal="Research release",
        fencing_token=1,
        recovery_count=0,
    )

    await runner.run_claim(task)

    assert len(store.facts) == 1
    assert store.facts[0]["retrieved_at"] == observed_at
    assert store.facts[0]["retrieved_at"] != model_time
