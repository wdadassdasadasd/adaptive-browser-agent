"""Offline checks for the optional decision request and worker handoff."""

from types import SimpleNamespace

import httpx
import pytest

from adaptive_research.agent.events import AgentEvent
from adaptive_research.agent.state import DecisionContext, utc_now
from adaptive_research.api.pg_main import create_app
from adaptive_research.infrastructure.config import Settings
from adaptive_research.worker.runner import WorkerRunner


class RecordingStore:
    require_budget = False

    def __init__(self) -> None:
        self.created = []
        self.events = []

    async def create_task(self, owner_id, goal, **options):
        self.created.append((owner_id, goal, options))
        context = options.get("decision_context")
        return SimpleNamespace(
            id="task-1",
            goal=goal,
            status="queued",
            error_message=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            completion_level=None,
            stop_reason=None,
            report=None,
            cancellation_requested=False,
            decision_context=context.model_dump(mode="json") if context else None,
        )

    async def list_events(self, owner_id, task_id):
        return []

    async def list_calls(self, owner_id, task_id):
        return []

    async def list_facts(self, owner_id, task_id):
        return []

    async def mark_unknown_calls(self, task_id, token):
        return None

    async def finish_task(self, task_id, token, status, **options):
        self.events.append((status, options))


@pytest.mark.asyncio
async def test_optional_context_is_validated_and_passed_to_store() -> None:
    store = RecordingStore()
    app = create_app(Settings(_env_file=None, DEEPSEEK_API_KEY="offline-key"))
    app.state.pg_store = store
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        old = await client.post("/api/research", json={"goal": " old goal "})
        absent = await client.post(
            "/api/research", json={"goal": "old goal", "decision_context": None}
        )
        assert old.status_code == absent.status_code == 202
        assert store.created[0][2] == store.created[1][2] == {}
        request = {
            "goal": "Choose a framework",
            "decision_context": {
                "use_case": "  Python API  ",
                "must_have": [" MIT ", "ASGI"],
                "preferences": [" Small footprint ", "Familiar API"],
                "candidate_projects": [" Flask ", "FastAPI"],
            },
        }
        accepted = await client.post("/api/research", json=request)
        assert accepted.status_code == 202
        assert accepted.json()["decision_context"]["use_case"] == "Python API"
        context = store.created[-1][2]["decision_context"]
        assert context.must_have == ["MIT", "ASGI"]
        assert context.preferences == ["Small footprint", "Familiar API"]
        assert context.candidate_projects == ["Flask", "FastAPI"]

        invalid_contexts = [
            "Python API",
            [],
            {},
            {"use_case": " "},
            {"use_case": 1},
            {"use_case": "x" * 1001},
            {"use_case": "Python", "unknown": 1},
            {"use_case": "Python", "must_have": ["MIT", " mit "]},
            {"use_case": "Python", "must_have": [1]},
            {"use_case": "Python", "must_have": ["x"] * 13},
            {"use_case": "Python", "must_have": ["x" * 201]},
            {"use_case": "Python", "preferences": ["fast", " FAST "]},
            {"use_case": "Python", "candidate_projects": [" "]},
            {"use_case": "Python", "candidate_projects": ["A", " a "]},
            {"use_case": "Python", "candidate_projects": ["x"] * 9},
            {"use_case": "Python", "preferences": ["x"] * 13},
            {"use_case": "Python", "candidate_projects": "FastAPI"},
        ]
        for context in invalid_contexts:
            invalid = await client.post(
                "/api/research",
                json={"goal": "Choose", "decision_context": context},
            )
            assert invalid.status_code == 422
        for goal in ("", " ", 1, "x" * 4001):
            invalid = await client.post("/api/research", json={"goal": goal})
            assert invalid.status_code == 422
        assert len(store.created) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("recovery_count", [0, 1])
async def test_worker_passes_persisted_context_to_initial_and_recovered_agent(
    recovery_count: int,
) -> None:
    store = RecordingStore()
    settings = Settings(
        _env_file=None,
        P01_DATABASE_URL="postgresql+asyncpg://user@localhost/test",
    )
    observed = []

    class Agent:
        async def run(
            self,
            goal,
            *,
            cancellation,
            task_id,
            on_event,
            call_observer,
            decision_context,
            resume_state=None,
            prior_events=(),
        ):
            observed.append((decision_context, resume_state, prior_events))
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

    runner = WorkerRunner(store, settings, agent_factory=Agent)
    task = SimpleNamespace(
        id="task-1",
        owner_id="owner-1",
        goal="Choose a framework",
        fencing_token=2,
        recovery_count=recovery_count,
        decision_context={
            "use_case": "Python API",
            "must_have": ["MIT"],
            "preferences": [],
            "candidate_projects": ["FastAPI", "Flask"],
        },
    )
    await runner.run_claim(task)
    assert len(observed) == 1
    context, state, history = observed[0]
    assert isinstance(context, DecisionContext)
    assert context.must_have == ["MIT"]
    if recovery_count:
        assert state.decision_context == context
    else:
        assert state is None
    assert history == ()
    assert store.events[0][0] == "failed"
