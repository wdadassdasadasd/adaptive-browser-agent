"""Worker persistence must use observed event time for fact retrieval."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import ResearchFact, Subgoal
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
    duplicate = fact.model_copy(update={"id": "f2"})
    subgoal = Subgoal(
        id="s1",
        description="Read release",
        completion_criteria="Find cited release",
    )

    class Agent:
        async def run(self, goal, *, cancellation, task_id, on_event, call_observer):
            await on_event(
                AgentEvent(
                    event_type="subgoals_initialized",
                    task_id=task_id,
                    payload={"subgoals": [subgoal.model_dump(mode="json")]},
                )
            )
            await on_event(
                AgentEvent(
                    event_type="step_evaluated",
                    task_id=task_id,
                    timestamp=observed_at,
                    payload={
                        "decision": {
                            "subgoal_id": "s1",
                            "reasoning": "Read release",
                            "tool": "browser",
                            "action": "navigate",
                            "target": str(fact.source_url),
                            "expected_result": "Release evidence",
                        },
                        "tool_result": {
                            "tool": "browser",
                            "action": "navigate",
                            "success": True,
                            "content": "0.13.13 Latest",
                            "source_url": str(fact.source_url),
                            "error_type": "none",
                        },
                        "evaluation": {
                            "success": True,
                            "reason": "Cited release",
                            "facts": [
                                fact.model_dump(mode="json"),
                                duplicate.model_dump(mode="json"),
                            ],
                        },
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
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

    assert [item["id"] for item in store.facts] == ["f1"]
    assert store.facts[0]["retrieved_at"] == observed_at
    assert store.facts[0]["retrieved_at"] != model_time


@pytest.mark.asyncio
async def test_recovery_uses_committed_fact_time_and_rejects_mismatched_facts() -> None:
    event_time = datetime(2026, 10, 23, 5, 2, tzinfo=UTC)
    retrieved_at = datetime(2026, 10, 23, 5, 1, tzinfo=UTC)
    sourced = ResearchFact(
        id="f1",
        content="FastAPI supports async",
        source_url="https://example.com/page",
        source_title="Documentation",
        subject="FastAPI",
        subject_kind="project",
        evidence="FastAPI supports async",
        subgoal_id="s1",
        created_at=datetime(2026, 10, 16, tzinfo=UTC),
    )
    payload = {
        "decision": {
            "subgoal_id": "s1",
            "reasoning": "Read documentation",
            "tool": "browser",
            "action": "navigate",
            "expected_result": "Evidence visible",
        },
        "tool_result": {
            "tool": "browser",
            "action": "navigate",
            "success": True,
            "content": "FastAPI supports async",
            "source_url": "https://example.com/page",
        },
        "evaluation": {
            "success": True,
            "reason": "Evidence visible",
            "facts": [sourced.model_dump(mode="json")],
        },
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }

    class RecoveryStore:
        require_budget = False

        def __init__(self):
            self.fact = SimpleNamespace(
                id="f1",
                subject="FastAPI",
                claim="FastAPI supports async",
                official_source_url="https://example.com/page",
                evidence_excerpt="FastAPI supports async",
                retrieved_at=retrieved_at,
                machine_admission_status="candidate_unverified_official",
            )

        async def list_events(self, owner_id, task_id):
            return [
                SimpleNamespace(
                    id=1,
                    event_type="subgoals_initialized",
                    task_id=task_id,
                    step=0,
                    created_at=event_time,
                    message="",
                    payload={
                        "subgoals": [
                            Subgoal(
                                id="s1",
                                description="Read documentation",
                                completion_criteria="Find cited claim",
                            ).model_dump(mode="json")
                        ]
                    },
                ),
                SimpleNamespace(
                    id=2,
                    event_type="step_evaluated",
                    task_id=task_id,
                    step=0,
                    created_at=event_time,
                    message="",
                    payload=payload,
                ),
            ]

        async def list_facts(self, owner_id, task_id):
            return [self.fact]

        async def list_calls(self, owner_id, task_id):
            return []

    store = RecoveryStore()
    settings = Settings(
        _env_file=None,
        P01_DATABASE_URL="postgresql+asyncpg://user@localhost/test",
    )
    runner = WorkerRunner(store, settings)
    task = SimpleNamespace(id="task-1", owner_id="owner-1", goal="Research")
    restored, _ = await runner._recovery_snapshot(task)
    assert [fact.id for fact in restored.facts] == ["f1"]
    assert restored.facts[0].created_at == retrieved_at
    store.fact.subject = "Flask"
    with pytest.raises(ValueError, match="Committed facts differ"):
        await runner._recovery_snapshot(task)
    store.fact.subject = "FastAPI"
    store.fact.machine_admission_status = "not_admitted"
    with pytest.raises(ValueError, match="Committed facts differ"):
        await runner._recovery_snapshot(task)
