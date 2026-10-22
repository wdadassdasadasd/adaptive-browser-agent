"""Pilot orchestration stays serial, resumable and fail-closed offline."""

import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from adaptive_research.evaluation import pilot_runner
from adaptive_research.evaluation.current import build_plan
from adaptive_research.evaluation.project_ledger import write_ledger
from adaptive_research.infrastructure.pricing import load_price_book

BOOK = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/DEEPSEEK_CNY_PRICING_2026-10-21.json"
)


class FakeStore:
    def __init__(self, book):
        self.budget = SimpleNamespace(
            status="armed",
            phase="pilot",
            authorization_reference="approved-test",
            price_book_sha256=book["snapshot_sha256"],
            price_revision=book["price_revision"],
            phase_max_cny=Decimal(49),
            project_max_cny=Decimal(299),
        )
        self.tasks = {}
        self.known_cost_cny = Decimal(0)

    async def get_budget(self):
        return self.budget

    async def get_task_by_idempotency_key(self, owner_id, key):
        assert owner_id == pilot_runner.OWNER_ID
        return self.tasks.get(key)

    async def list_tasks(self, owner_id):
        assert owner_id == pilot_runner.OWNER_ID
        return list(self.tasks.values())

    async def get_cost(self, owner_id, task_id):
        assert owner_id == pilot_runner.OWNER_ID
        assert any(task.id == task_id for task in self.tasks.values())
        return SimpleNamespace(
            known_cost_cny=self.known_cost_cny, unknown_attempt_count=0
        )


@pytest.fixture
def cohort(monkeypatch):
    book = load_price_book(BOOK)
    fixed = datetime.fromisoformat(book["verified_at"]) + timedelta(minutes=10)
    monkeypatch.setattr(pilot_runner, "_utc_now", lambda: fixed)
    return build_plan(), book, FakeStore(book)


def fake_client(store, *, ambiguous=False, task_status="completed"):
    submissions = []

    def handle(request):
        assert request.url.host == "127.0.0.1"
        assert request.method == "POST"
        if request.url.path.endswith("/cancel"):
            return httpx.Response(200, json={"cancelled": False})
        run_id = request.headers["Idempotency-Key"]
        prompt = json.loads(request.content)["goal"]
        submissions.append(run_id)
        store.tasks[run_id] = SimpleNamespace(
            id=f"task-{len(store.tasks) + 1}", goal=prompt, status=task_status
        )
        if ambiguous:
            raise httpx.ConnectError("synthetic lost response", request=request)
        return httpx.Response(202, json={"id": store.tasks[run_id].id})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle),
        base_url="http://127.0.0.1:8000",
        trust_env=False,
    )
    return client, submissions


def fake_capture(*, known=True):
    async def capture(store, *, output_dir, planned_run_id, task_id, **kwargs):
        output_dir.mkdir()
        manifest = {
            "planned_run_id": planned_run_id,
            "task_id": task_id,
            "cost": {
                "cost_completeness": "known" if known else "unknown_or_incomplete",
                "persisted_known_cost_cny": "0",
                "actual_total_cost_cny": "0" if known else None,
                "persisted_unknown_attempt_count": 0 if known else 1,
            },
            "snapshot_consistency": "stable_task_record_non_atomic",
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return manifest

    return capture


def ledger_args(tmp_path):
    path = tmp_path / "project-ledger-initial.json"
    write_ledger(entries=[], batches=[], output=path)
    return {
        "prior_ledger": path,
        "expected_prior_ledger_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


@pytest.mark.asyncio
async def test_serial_three_attempts_resume_without_new_submissions(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store)
    async with client:
        result = await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            **ledger,
            capture=fake_capture(),
        )
        assert result["status"] == "pilot_attempts_captured_review_pending"
        assert submissions == [run["planned_run_id"] for run in plan["planned_runs"]]
        resumed = await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            **ledger,
            capture=fake_capture(),
        )
    assert resumed == result
    assert len(submissions) == 3
    assert len(list((tmp_path / "cohort").glob("*/intent.json"))) == 3


@pytest.mark.asyncio
async def test_unknown_cost_pauses_before_next_submission(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store)
    async with client:
        result = await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            **ledger,
            capture=fake_capture(known=False),
        )
    assert result["status"] == "paused_no_go"
    assert len(submissions) == 1
    assert (tmp_path / "cohort/paused.json").is_file()
    ledgers = list(tmp_path.glob("ledger-after-*.json"))
    assert len(ledgers) == 1
    assert json.loads(ledgers[0].read_text(encoding="utf-8"))["status"] == "No-Go"
    async with fake_client(store)[0] as retry_client:
        with pytest.raises(pilot_runner.PilotRunError, match="paused"):
            await pilot_runner.run_pilot(
                plan=plan,
                output_dir=tmp_path / "cohort",
                client=retry_client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                **ledger,
            )


@pytest.mark.asyncio
async def test_ambiguous_http_response_reconciles_by_durable_key(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store, ambiguous=True)
    async with client:
        result = await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            **ledger,
            capture=fake_capture(),
        )
    assert result["status"] == "pilot_attempts_captured_review_pending"
    assert len(submissions) == 3


@pytest.mark.asyncio
async def test_stale_plan_or_budget_refuses_before_any_submission(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store)
    async with client:
        stale = dict(plan)
        stale["fingerprints"] = {**plan["fingerprints"], "source": {"sha256": "0" * 64}}
        with pytest.raises(pilot_runner.PilotRunError, match="stale"):
            await pilot_runner.run_pilot(
                plan=stale,
                output_dir=tmp_path / "stale",
                client=client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                **ledger,
            )
        store.budget.status = "halted"
        with pytest.raises(pilot_runner.PilotRunError, match="budget"):
            await pilot_runner.run_pilot(
                plan=plan,
                output_dir=tmp_path / "halted",
                client=client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                **ledger,
            )
    assert submissions == []


@pytest.mark.asyncio
async def test_prior_ledger_hash_mismatch_refuses_before_submission(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    ledger["prior_ledger"].write_text("{}", encoding="utf-8")
    client, submissions = fake_client(store)
    async with client:
        with pytest.raises(pilot_runner.PilotRunError, match="changed"):
            await pilot_runner.run_pilot(
                plan=plan,
                output_dir=tmp_path / "cohort",
                client=client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                **ledger,
            )
    assert submissions == []


@pytest.mark.asyncio
async def test_unledgered_owner_task_refuses_before_submission(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    store.tasks["other-key"] = SimpleNamespace(
        id="task-other", goal="another paid task", status="completed"
    )
    client, submissions = fake_client(store)
    async with client:
        with pytest.raises(pilot_runner.PilotRunError, match="unledgered task"):
            await pilot_runner.run_pilot(
                plan=plan,
                output_dir=tmp_path / "cohort",
                client=client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                **ledger,
            )
    assert submissions == []


@pytest.mark.asyncio
async def test_resume_refuses_changed_application_cost(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store)
    async with client:
        await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            capture=fake_capture(),
            **ledger,
        )
        store.known_cost_cny = Decimal("0.5")
        with pytest.raises(pilot_runner.PilotRunError, match="cost differs"):
            await pilot_runner.run_pilot(
                plan=plan,
                output_dir=tmp_path / "cohort",
                client=client,
                store=store,
                price_book=book,
                authorization_reference="approved-test",
                capture=fake_capture(),
                **ledger,
            )
    assert len(submissions) == 3


@pytest.mark.asyncio
async def test_timeout_requests_cancel_captures_and_pauses(cohort, tmp_path):
    plan, book, store = cohort
    ledger = ledger_args(tmp_path)
    client, submissions = fake_client(store, task_status="running")
    ticks = iter((0.0, 2.0))

    async def no_sleep(_seconds):
        return None

    async with client:
        result = await pilot_runner.run_pilot(
            plan=plan,
            output_dir=tmp_path / "cohort",
            client=client,
            store=store,
            price_book=book,
            authorization_reference="approved-test",
            capture=fake_capture(known=False),
            clock=lambda: next(ticks),
            pause=no_sleep,
            task_timeout_seconds=1,
            **ledger,
        )
    assert result["status"] == "paused_no_go"
    assert len(submissions) == 1
    first = tmp_path / "cohort" / plan["planned_runs"][0]["planned_run_id"]
    assert json.loads((first / "timeout-cancel.json").read_text())["http_status"] == 200
    assert (first / "capture/manifest.json").is_file()


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:8000",
        "http://example.org:8000",
        "http://127.0.0.1:8000/path",
        "http://user@127.0.0.1:8000",
    ],
)
def test_live_api_origin_must_be_plain_loopback(value):
    with pytest.raises(pilot_runner.PilotRunError):
        pilot_runner._local_api_url(value)


def test_cli_without_execute_is_inert(capsys):
    assert pilot_runner.main([]) == 0
    assert "no task submitted" in capsys.readouterr().out
