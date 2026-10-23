"""Read-only pilot captures retain uncertainty without invoking execution code."""

import asyncio
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from adaptive_research.evaluation.current import build_plan
from adaptive_research.evaluation.pilot_capture import CaptureError, capture_attempt

NOW = datetime(2026, 10, 21, tzinfo=UTC)


@pytest.fixture
def plan():
    return build_plan()


class FakeReadStore:
    def __init__(self, plan, *, status="failed", known="0.01", unknown=1, visible=True):
        self.methods = []
        self.visible = visible
        self.task = SimpleNamespace(
            id="task-1",
            owner_id="owner-1",
            goal=plan["planned_runs"][0]["prompt"],
            status=status,
            cancellation_requested=status == "cancelled",
            fencing_token=2,
            recovery_count=1,
            completion_level="partial" if status == "partial" else "none",
            stop_reason="execution_error",
            error_message="Authorization: Bearer hidden-header",
            created_at=NOW,
            updated_at=NOW,
            report={
                "title": "A bounded report",
                "summary": "sk-abcdefghijklmnop",
                "recommendation": "Bearer hidden-bearer",
                "markdown": "Safe body",
                "findings": [
                    {
                        "name": "Project",
                        "attributes": {"api_key": "hidden-key", "license": "MIT"},
                    }
                ],
                "sources": [
                    "https://user:password@example.org/source?token=hidden-query#hidden-fragment"
                ],
                "raw_html": "<html>hidden-extra</html>",
                "cookie": "hidden-cookie",
            },
        )
        self.events = [
            SimpleNamespace(
                id=1,
                task_id="task-1",
                event_type="step_evaluated",
                step=1,
                message="Cookie: hidden-cookie; session=hidden-session",
                created_at=NOW,
                payload={
                    "prompt_tokens": 4,
                    "completion_tokens": 2,
                    "tool_result": {
                        "tool": "browser",
                        "action": "read",
                        "success": True,
                        "content": "<html>hidden-html</html>",
                        "metadata": {"raw_html": "hidden-raw"},
                    },
                    "decision": {
                        "tool": "browser",
                        "action": "read",
                        "target": "hidden-target",
                        "value": "hidden-value",
                    },
                    "evaluation": {
                        "reason": "<div>hidden-html-reason</div>",
                        "success": False,
                    },
                    "api_key": "hidden-payload-key",
                },
            )
        ]
        self.calls = [
            SimpleNamespace(
                id="call-1",
                task_id="task-1",
                kind="model",
                status="unknown_outcome" if unknown else "completed",
                reported_prompt_tokens=4,
                reported_completion_tokens=2,
                prompt_cache_hit_tokens=0,
                prompt_cache_miss_tokens=4,
                known_cost_cny=None if unknown else Decimal(known),
                started_at=NOW,
                ended_at=NOW,
                provider="deepseek",
                model="deepseek-flash",
                reported_model="deepseek-flash",
                price_revision="verified-price",
                request_body="hidden-request",
                response_body="hidden-response",
            )
        ]
        self.facts = [
            SimpleNamespace(
                id="fact-1",
                task_id="task-1",
                subject="Project",
                claim="It has a license",
                official_source_url="https://example.org/license?key=hidden-query",
                official_identity_basis="repository owner",
                evidence_excerpt="A license",
                evidence_locator="LICENSE:1",
                retrieved_at=NOW,
                machine_admission_status="accepted",
                human_review_status=None,
                reviewed_at=None,
                created_at=NOW,
            )
        ]
        self.cost = SimpleNamespace(
            task_id="task-1",
            known_cost_cny=Decimal(known),
            unknown_attempt_count=unknown,
            updated_at=NOW,
        )

    def check(self, method, owner_id, task_id):
        assert (owner_id, task_id) == ("owner-1", "task-1")
        self.methods.append(method)

    async def get_task(self, owner_id, task_id):
        self.check("get_task", owner_id, task_id)
        return self.task if self.visible else None

    async def list_events(self, owner_id, task_id):
        self.check("list_events", owner_id, task_id)
        return self.events

    async def list_calls(self, owner_id, task_id):
        self.check("list_calls", owner_id, task_id)
        return self.calls

    async def list_facts(self, owner_id, task_id):
        self.check("list_facts", owner_id, task_id)
        return self.facts

    async def get_cost(self, owner_id, task_id):
        self.check("get_cost", owner_id, task_id)
        return self.cost

    def __getattr__(self, name):
        pytest.fail("Unexpected store capability: " + name)


async def export(store, plan, path, **options):
    return await capture_attempt(
        store,
        plan=plan,
        planned_run_id=plan["planned_runs"][0]["planned_run_id"],
        task_id="task-1",
        case_id="B01",
        trial_index=1,
        owner_id="owner-1",
        output_dir=path,
        **options,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", ["failed", "partial", "cancelled", "running", "queued", "completed"]
)
async def test_export_preserves_all_task_outcomes_and_unresolved_cost(
    plan, tmp_path, status
):
    store = FakeReadStore(plan, status=status)
    manifest = await export(store, plan, tmp_path / "attempt")
    assert manifest["status"] == "diagnostic_not_release"
    assert manifest["persisted_task_status"] == status
    assert manifest["product_release"] == "No-Go"
    assert manifest["formal_acceptance"] is manifest["research_quality_passed"] is None
    assert manifest["goal_matches_planned_prompt"] is True
    assert manifest["cost"]["persisted_known_cost_cny"] == "0.01"
    assert manifest["cost"]["actual_total_cost_cny"] is None
    assert manifest["cost"]["persisted_unknown_attempt_count"] == 1
    assert manifest["cost"]["observed_unresolved_call_ids"] == ["call-1"]
    assert store.methods == [
        "get_task",
        "list_events",
        "list_calls",
        "list_facts",
        "get_cost",
        "get_task",
    ]
    assert (
        manifest["capture_provider_calls"]
        == manifest["capture_browser_calls"]
        == manifest["capture_database_writes"]
        == 0
    )
    assert (tmp_path / "attempt/manifest.json").is_file()


@pytest.mark.asyncio
async def test_export_hashes_exact_artifact_bytes_and_preserves_review_uncertainty(
    plan, tmp_path
):
    manifest = await export(FakeReadStore(plan), plan, tmp_path / "attempt")
    for name, metadata in manifest["artifacts"].items():
        blob = (tmp_path / "attempt" / name).read_bytes()
        assert metadata == {
            "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes": len(blob),
        }
    source = json.loads((tmp_path / "attempt/source-version.json").read_bytes())
    assert source["execution_source_verified"] is False
    assert len(source["capture_source_sha256"]) == 64
    facts = json.loads((tmp_path / "attempt/facts.json").read_bytes())
    assert facts[0]["human_review_status"] is None
    assert facts[0]["machine_admission_status"] == "accepted"
    assert "not_performed" in manifest["official_source_verification"]


@pytest.mark.asyncio
async def test_safe_boundary_omits_html_arguments_credentials_and_sensitive_extras(
    plan, tmp_path
):
    store = FakeReadStore(plan)
    store.facts[0].evidence_excerpt = "Literal supplied-secret remains private"
    store.task.report["markdown"] = '{"api_key": "hidden-quoted-key"}'
    await export(store, plan, tmp_path / "attempt", redact_values=("supplied-secret",))
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "attempt").glob("*.json")
    )
    for forbidden in (
        "hidden-",
        "sk-abcdefghijklmnop",
        "supplied-secret",
        "<html>",
        "<div>",
        "user:password",
        "token=",
        "?key=",
        "#hidden-fragment",
    ):
        assert forbidden not in text
    assert "[RAW_HTML_OMITTED]" in text
    assert "https://example.org/source" in text
    assert "repository owner" in text


@pytest.mark.asyncio
async def test_terminal_capture_keeps_only_safe_budget_preflight_numbers(
    plan, tmp_path
):
    store = FakeReadStore(plan, unknown=0)
    store.events.append(
        SimpleNamespace(
            id=2,
            task_id="task-1",
            event_type="task_finished",
            step=1,
            message="",
            created_at=NOW,
            payload={
                "status": "failed",
                "completion_level": "none",
                "stop_reason": "token_budget",
                "budget_preflight": {
                    "request_kind": "structured",
                    "remaining_tokens": 1168,
                    "prompt_bound": 1200,
                    "output_allowance": -32,
                    "provider_request_started": False,
                    "api_key": "hidden-key",
                },
            },
        )
    )
    store.events.append(
        SimpleNamespace(
            id=3,
            task_id="task-1",
            event_type="task_finished",
            step=1,
            message="",
            created_at=NOW,
            payload={
                "status": "failed",
                "completion_level": "none",
                "stop_reason": "token_budget",
                "budget_preflight": {
                    "request_kind": "structured",
                    "remaining_tokens": "hidden-secret",
                    "prompt_bound": 1200,
                    "output_allowance": -32,
                    "provider_request_started": False,
                },
            },
        )
    )
    await export(store, plan, tmp_path / "attempt")
    events = json.loads((tmp_path / "attempt/events.json").read_bytes())
    assert events[1]["payload"]["budget_preflight"] == {
        "request_kind": "structured",
        "remaining_tokens": 1168,
        "prompt_bound": 1200,
        "output_allowance": -32,
        "provider_request_started": False,
    }
    assert "hidden-key" not in json.dumps(events)
    assert "budget_preflight" not in events[2]["payload"]
    assert "hidden-secret" not in json.dumps(events)


@pytest.mark.asyncio
async def test_unknown_uncommitted_or_invisible_task_remains_unknown(plan, tmp_path):
    store = FakeReadStore(plan, visible=False)
    result = await export(store, plan, tmp_path / "attempt")
    assert result["task_visibility"] == "unknown_not_visible_or_uncommitted"
    assert result["persisted_task_status"] is result["task_terminal"] is None
    assert result["cost"]["persisted_known_cost_cny"] is None
    assert result["cost"]["observed_unpriced_call_count"] is None
    assert store.methods == ["get_task"]
    assert json.loads((tmp_path / "attempt/calls.json").read_bytes()) is None


@pytest.mark.asyncio
async def test_write_once_refuses_existing_directory_before_database_reads(
    plan, tmp_path
):
    output = tmp_path / "attempt"
    output.mkdir()
    (output / "existing.json").write_bytes(b"preserved")
    store = FakeReadStore(plan)
    with pytest.raises(FileExistsError):
        await export(store, plan, output)
    assert store.methods == []
    assert (output / "existing.json").read_bytes() == b"preserved"


@pytest.mark.asyncio
async def test_terminal_known_cost_requires_reconciled_ledger_and_no_unknown_calls(
    plan, tmp_path
):
    store = FakeReadStore(plan, status="completed", unknown=0)
    known = await export(store, plan, tmp_path / "known")
    assert known["cost"]["actual_total_cost_cny"] == "0.01"
    store.cost.known_cost_cny = Decimal("0.02")
    mismatch = await export(store, plan, tmp_path / "mismatch")
    assert mismatch["cost"]["actual_total_cost_cny"] is None
    assert mismatch["cost"]["task_and_call_known_cost_match"] is False


@pytest.mark.asyncio
async def test_read_failure_is_recorded_without_exception_contents(plan, tmp_path):
    store = FakeReadStore(plan, unknown=0)

    async def failed(owner_id, task_id):
        raise RuntimeError("private-database-url")

    store.list_calls = failed
    result = await export(store, plan, tmp_path / "attempt")
    assert result["read_failures"] == {"list_calls": "RuntimeError"}
    assert result["cost"]["actual_total_cost_cny"] is None
    assert "private-database-url" not in json.dumps(result)


@pytest.mark.asyncio
async def test_read_timeout_is_bounded_and_unknown_cost_is_retained(plan, tmp_path):
    store = FakeReadStore(plan, unknown=0)

    async def stalled(owner_id, task_id):
        await asyncio.Event().wait()

    store.get_cost = stalled
    result = await export(store, plan, tmp_path / "attempt", read_timeout_seconds=0.01)
    assert result["read_failures"] == {"get_cost": "TimeoutError"}
    assert result["cost"]["persisted_known_cost_cny"] is None
    assert result["cost"]["actual_total_cost_cny"] is None


@pytest.mark.asyncio
async def test_changed_task_snapshot_and_cross_task_rows_are_not_claimed_complete(
    plan, tmp_path
):
    store = FakeReadStore(plan, status="completed", unknown=0)
    original_read = store.get_task
    count = 0

    async def changing(owner_id, task_id):
        nonlocal count
        count += 1
        original = await original_read(owner_id, task_id)
        return (
            original
            if count == 1
            else SimpleNamespace(**{**vars(original), "status": "failed"})
        )

    store.get_task = changing
    result = await export(store, plan, tmp_path / "changed")
    assert result["snapshot_consistency"] == "changed_or_unavailable_non_atomic"
    assert result["cost"]["actual_total_cost_cny"] is None
    store.facts[0].task_id = "someone-elses-task"
    result = await export(store, plan, tmp_path / "mismatch")
    assert result["read_failures"]["list_facts"] == "TaskIdentityMismatch"
    assert json.loads((tmp_path / "mismatch/facts.json").read_bytes()) is None


@pytest.mark.asyncio
async def test_record_and_text_bounds_are_explicit_and_prevent_complete_cost_claim(
    plan, tmp_path
):
    store = FakeReadStore(plan, unknown=0)
    store.events *= 3
    store.task.report["markdown"] = "Long " * 200
    result = await export(
        store, plan, tmp_path / "attempt", max_records=1, max_text_chars=128
    )
    assert result["truncated_collections"]["list_events"] is True
    assert result["redaction"]["truncated_text_count"] >= 1
    assert result["cost"]["actual_total_cost_cny"] is None
    assert len(json.loads((tmp_path / "attempt/events.json").read_bytes())) == 1


@pytest.mark.asyncio
async def test_output_byte_bound_refuses_without_creating_artifact_directory(
    plan, tmp_path
):
    output = tmp_path / "attempt"
    with pytest.raises(CaptureError, match="byte bound"):
        await export(FakeReadStore(plan), plan, output, max_total_bytes=1024)
    assert not output.exists()


@pytest.mark.asyncio
async def test_plan_binding_rejects_changed_prompt_before_reading_store(plan, tmp_path):
    plan["planned_runs"][0]["prompt"] += " Different question."
    store = FakeReadStore(plan)
    with pytest.raises(CaptureError, match="binding"):
        await export(store, plan, tmp_path / "attempt")
    assert not store.methods


@pytest.mark.asyncio
async def test_pg_fact_reader_is_owner_scoped_read_only_and_returns_frozen_records():
    from adaptive_research.infrastructure.pg_store import FactRecord, PgStore

    class Session:
        def __init__(self):
            self.visible = False
            self.statements = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def scalar(self, statement):
            self.statements.append(
                str(statement.compile(compile_kwargs={"literal_binds": True}))
            )
            return "task-1" if self.visible else None

        async def scalars(self, statement):
            self.statements.append(
                str(statement.compile(compile_kwargs={"literal_binds": True}))
            )
            fact = SimpleNamespace(
                **{name: None for name in FactRecord.__dataclass_fields__}
            )
            fact.id, fact.task_id = "fact-1", "task-1"
            return SimpleNamespace(all=lambda: [fact])

    session = Session()
    store = PgStore(lambda: session)
    assert await store.list_facts("other-owner", "task-1") is None
    assert "other-owner" in session.statements[0]
    assert len(session.statements) == 1
    session.visible = True
    facts = await store.list_facts("owner-1", "task-1")
    assert facts[0].id == "fact-1"
    assert all(statement.startswith("SELECT") for statement in session.statements)
    assert "app_fact.task_id = 'task-1'" in session.statements[-1]
    with pytest.raises(FrozenInstanceError):
        facts[0].id = "changed"
