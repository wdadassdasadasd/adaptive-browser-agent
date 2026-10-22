"""Explicitly armed, serial B01-B03 pilot runner over the product API.

Importing this module or omitting --execute never starts a task. The API and
PostgreSQL budget must already be running; this command does not arm them.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import ipaddress
import json
import os
import re
import sys
import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.evaluation.current import (
    PROTOCOL_PATH,
    REPOSITORY_ROOT,
    _source_fingerprint,
    load_protocol,
)
from adaptive_research.evaluation.pilot_capture import capture_attempt
from adaptive_research.evaluation.project_ledger import (
    assert_declared_reservation_fits,
    extend_ledger,
)
from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_store import PgStore
from adaptive_research.infrastructure.pricing import (
    calculate_call_cost,
    load_price_book,
)

OWNER_ID = "p01-local-owner"
TERMINAL = frozenset({"completed", "partial", "failed", "cancelled"})


class PilotRunError(ValueError):
    """The cohort must stop without starting another paid task."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _rooted(path: Path) -> Path:
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def _encoded(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def _existing_or_write(path: Path, value: Any) -> None:
    if path.exists():
        if path.read_bytes() != _encoded(value):
            raise PilotRunError("Existing pilot journal does not match this cohort")
    else:
        _write_once(path, value)


def _local_api_url(value: str) -> str:
    parsed = urlsplit(value)
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError as exc:
        raise PilotRunError("Pilot API URL must be a numeric loopback host") from exc
    if (
        parsed.scheme != "http"
        or not address.is_loopback
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise PilotRunError("Pilot API URL must be an unadorned local HTTP origin")
    return value.rstrip("/")


def _validate_plan(plan: Mapping[str, Any], root: Path) -> None:
    protocol, resources = load_protocol(root)
    fingerprint = plan.get("fingerprints")
    if not isinstance(fingerprint, Mapping):
        raise PilotRunError("Pilot plan has no frozen fingerprints")
    source = fingerprint.get("source")
    runs = plan.get("planned_runs")
    if (
        plan.get("artifact_type") != "evaluation_dry_run_plan"
        or plan.get("phase") != "pilot"
        or plan.get("protocol_version") != protocol["protocol_version"]
        or plan.get("execution_allowed") is not False
        or plan.get("attempts_started") != 0
        or fingerprint.get("protocol_sha256") != resources[PROTOCOL_PATH]
        or fingerprint.get("dependency_lock_sha256") != resources["backend/uv.lock"]
        or not isinstance(source, Mapping)
        or source.get("sha256") != _source_fingerprint(root)["sha256"]
        or not isinstance(runs, list)
        or len(runs) != 3
        or not all(isinstance(run, Mapping) for run in runs)
        or [run.get("case_id") for run in runs] != protocol["pilot"]["case_ids"]
    ):
        raise PilotRunError("Pilot plan is stale or differs from current-3")
    for run, case in zip(runs, protocol["cases"][:3], strict=True):
        if (
            not isinstance(run, Mapping)
            or not isinstance(run.get("planned_run_id"), str)
            or not re.fullmatch(r"[a-f0-9-]{36}", run["planned_run_id"])
            or run.get("trial_index") != 1
            or run.get("prompt") != case["prompt"]
            or run.get("prompt_sha256") != _sha(case["prompt"].encode("utf-8"))
            or run.get("required_fields") != case["required_fields"]
        ):
            raise PilotRunError("Pilot case binding differs from current-3")


def _validate_budget(
    budget: Any, book: Mapping[str, Any], reference: str, *, require_armed: bool
) -> None:
    if (
        budget is None
        or (require_armed and budget.status != "armed")
        or budget.phase != "pilot"
        or budget.authorization_reference != reference
        or budget.price_book_sha256 != book.get("snapshot_sha256")
        or budget.price_revision != book.get("price_revision")
        or budget.phase_max_cny > 49
        or budget.project_max_cny >= 300
    ):
        raise PilotRunError(
            "Pilot budget is absent, halted or bound to another authorization"
        )
    now = _utc_now()
    priced = calculate_call_cost(
        model="deepseek-flash",
        currency="CNY",
        started_at=now,
        finished_at=now,
        evaluated_at=now,
        prompt_tokens=0,
        prompt_cache_hit_tokens=0,
        prompt_cache_miss_tokens=0,
        completion_tokens=0,
        price_book=book,
    )
    if priced.reason is not None:
        raise PilotRunError("CNY price snapshot is no longer verified")


async def _reconcile_owner_tasks(
    store: PgStore,
    plan: Mapping[str, Any],
    ledger: Mapping[str, Any],
    output_dir: Path,
) -> None:
    """Refuse a fresh cohort if the local owner has unledgered paid tasks."""

    entries = {
        entry["task_id"]: entry
        for entry in ledger["entries"]
        if isinstance(entry, Mapping) and isinstance(entry.get("task_id"), str)
    }
    current = {
        task.id
        for run in plan["planned_runs"]
        if (
            task := await store.get_task_by_idempotency_key(
                OWNER_ID, run["planned_run_id"]
            )
        )
        is not None
    }
    if current - entries.keys() and not (output_dir / "session.json").exists():
        raise PilotRunError("An existing pilot task has no preserved cohort journal")
    for task in await store.list_tasks(OWNER_ID):
        entry = entries.get(task.id)
        if entry is None:
            if task.id not in current:
                raise PilotRunError("Application database has an unledgered task")
            continue
        cost = await store.get_cost(OWNER_ID, task.id)
        if (
            cost is None
            or entry.get("known_cost_cny") is None
            or Decimal(str(entry["known_cost_cny"])) != cost.known_cost_cny
            or entry.get("unknown_attempt_count") != cost.unknown_attempt_count
        ):
            raise PilotRunError("Application cost differs from the project ledger")


async def run_pilot(
    *,
    plan: Mapping[str, Any],
    output_dir: Path,
    client: httpx.AsyncClient,
    store: PgStore,
    price_book: Mapping[str, Any],
    authorization_reference: str,
    prior_ledger: Path,
    expected_prior_ledger_sha256: str,
    root: Path = REPOSITORY_ROOT,
    poll_seconds: float = 1.0,
    task_timeout_seconds: float = 930.0,
    redact_values: tuple[str, ...] = (),
    capture: Callable[..., Awaitable[dict[str, Any]]] = capture_attempt,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> dict[str, Any]:
    """Run or resume a single serial cohort, retaining ambiguous attempts."""

    if not 0 < poll_seconds <= 30 or not 1 <= task_timeout_seconds <= 1200:
        raise PilotRunError("Invalid pilot polling bounds")
    _validate_plan(plan, root)
    if not re.fullmatch(r"[A-Za-z0-9:/._-]{4,128}", authorization_reference):
        raise PilotRunError("A separately approved authorization reference is required")
    _validate_budget(
        await store.get_budget(),
        price_book,
        authorization_reference,
        require_armed=False,
    )
    if not re.fullmatch(r"[0-9a-f]{64}", expected_prior_ledger_sha256):
        raise PilotRunError("An exact preceding project ledger hash is required")
    ledger_root = prior_ledger.resolve().parent
    if not output_dir.resolve().is_relative_to(ledger_root):
        raise PilotRunError("Pilot output must stay under the project ledger directory")
    if _sha(prior_ledger.read_bytes()) != expected_prior_ledger_sha256:
        raise PilotRunError("Project ledger has changed since authorization")
    initial_ledger = json.loads(prior_ledger.read_text(encoding="utf-8"))
    if (
        initial_ledger.get("artifact_type") != "offline_project_cost_ledger"
        or initial_ledger.get("status") != "declared_costs_reconciled_offline_only"
        or initial_ledger.get("validation_errors")
        or initial_ledger.get("unknown_attempt_count") != 0
    ):
        raise PilotRunError("Project ledger is not a clean declared baseline")
    await _reconcile_owner_tasks(store, plan, initial_ledger, output_dir)
    if (output_dir / "paused.json").exists():
        raise PilotRunError(
            "This pilot cohort is paused; preserve it and plan a new cohort"
        )
    session = {
        "plan_sha256": _sha(_encoded(dict(plan))),
        "protocol_version": plan["protocol_version"],
        "price_book_sha256": price_book["snapshot_sha256"],
        "authorization_reference": authorization_reference,
        "prior_ledger_name": prior_ledger.name,
        "prior_ledger_sha256": expected_prior_ledger_sha256,
        "run_ids": [run["planned_run_id"] for run in plan["planned_runs"]],
    }
    _existing_or_write(output_dir / "session.json", session)
    completed: list[dict[str, Any]] = []
    latest_ledger = prior_ledger
    for run in plan["planned_runs"]:
        run_id = run["planned_run_id"]
        case_id = run["case_id"]
        run_dir = output_dir / run_id
        _existing_or_write(
            run_dir / "intent.json",
            {
                "run_id": run_id,
                "case_id": case_id,
                "prompt_sha256": run["prompt_sha256"],
            },
        )
        task = await store.get_task_by_idempotency_key(OWNER_ID, run_id)
        if task is None:
            latest = json.loads(latest_ledger.read_text(encoding="utf-8"))
            await _reconcile_owner_tasks(store, plan, latest, output_dir)
            assert_declared_reservation_fits(
                entries=latest["entries"],
                batches=latest["batches"],
                output=latest_ledger,
                allocation="pilot",
                reserve_cny=Decimal(1),
                authorization_reference=authorization_reference,
                root=root,
            )
            _validate_budget(
                await store.get_budget(),
                price_book,
                authorization_reference,
                require_armed=True,
            )
            try:
                response = await client.post(
                    "/api/research",
                    json={"goal": run["prompt"]},
                    headers={"Idempotency-Key": run_id},
                )
            except httpx.RequestError as exc:
                task = await store.get_task_by_idempotency_key(OWNER_ID, run_id)
                if task is None:
                    raise PilotRunError(
                        "Submission outcome is uncertain; stop and reconcile"
                    ) from exc
                task_id = task.id
            else:
                if response.status_code != 202:
                    raise PilotRunError(
                        f"Research submission refused: HTTP {response.status_code}"
                    )
                try:
                    task_id = response.json()["id"]
                except (KeyError, TypeError, ValueError) as exc:
                    raise PilotRunError(
                        "Research API returned invalid task identity"
                    ) from exc
        else:
            task_id = task.id
        if not isinstance(task_id, str) or not task_id:
            raise PilotRunError("Research API returned no task identity")
        persisted = await store.get_task_by_idempotency_key(OWNER_ID, run_id)
        if (
            persisted is None
            or persisted.id != task_id
            or persisted.goal != run["prompt"]
        ):
            raise PilotRunError(
                "Submitted task differs from durable idempotency record"
            )
        _existing_or_write(
            run_dir / "submitted.json", {"run_id": run_id, "task_id": task_id}
        )
        deadline = clock() + task_timeout_seconds
        while persisted.status not in TERMINAL and clock() < deadline:
            await pause(poll_seconds)
            persisted = await store.get_task_by_idempotency_key(OWNER_ID, run_id)
            if persisted is None:
                raise PilotRunError("Submitted task is no longer visible")
        timed_out = (
            persisted.status not in TERMINAL
            or (run_dir / "timeout-cancel.json").exists()
        )
        if persisted.status not in TERMINAL:
            try:
                response = await client.post(f"/api/research/{task_id}/cancel")
                cancel_status: int | None = response.status_code
            except httpx.RequestError:
                cancel_status = None
            _existing_or_write(
                run_dir / "timeout-cancel.json",
                {"task_id": task_id, "http_status": cancel_status},
            )
            persisted = await store.get_task_by_idempotency_key(OWNER_ID, run_id)
        capture_dir = run_dir / "capture"
        if capture_dir.exists():
            manifest = json.loads(
                (capture_dir / "manifest.json").read_text(encoding="utf-8")
            )
            if (
                manifest.get("planned_run_id") != run_id
                or manifest.get("task_id") != task_id
            ):
                raise PilotRunError("Existing capture belongs to another attempt")
        else:
            manifest = await capture(
                store,
                plan=plan,
                planned_run_id=run_id,
                task_id=task_id,
                case_id=case_id,
                trial_index=1,
                owner_id=OWNER_ID,
                output_dir=capture_dir,
                root=root,
                redact_values=redact_values,
            )
        manifest_path = capture_dir / "manifest.json"
        if not manifest_path.is_file():
            raise PilotRunError("Capture manifest was not durably written")
        manifest_blob = manifest_path.read_bytes()
        if json.loads(manifest_blob) != manifest:
            raise PilotRunError("Capture manifest changed during ledger binding")
        cost = manifest.get("cost") or {}
        entry = {
            "run_id": run_id,
            "task_id": task_id,
            "allocation": "pilot",
            "batch_id": None,
            "known_cost_cny": cost.get("persisted_known_cost_cny"),
            "total_cost_cny": cost.get("actual_total_cost_cny"),
            "unknown_attempt_count": cost.get("persisted_unknown_attempt_count"),
            "evidence_artifact": {
                "relative_path": manifest_path.resolve()
                .relative_to(ledger_root)
                .as_posix(),
                "sha256": _sha(manifest_blob),
            },
            "authorization_reference": authorization_reference,
            "attempt_status": persisted.status,
        }
        next_ledger = prior_ledger.parent / f"ledger-after-{run_id}.json"
        prior_digest = _sha(latest_ledger.read_bytes())
        if next_ledger.exists():
            recorded = json.loads(next_ledger.read_text(encoding="utf-8"))
            if (
                recorded.get("previous_ledger_artifact")
                != {"relative_path": latest_ledger.name, "sha256": prior_digest}
                or not recorded.get("entries")
                or recorded["entries"][-1]["run_id"] != run_id
                or recorded["entries"][-1]["task_id"] != task_id
                or recorded["entries"][-1]["evidence_artifact"]
                != entry["evidence_artifact"]
            ):
                raise PilotRunError("Existing project ledger snapshot differs")
            await _reconcile_owner_tasks(store, plan, recorded, output_dir)
        else:
            recorded = extend_ledger(
                previous=latest_ledger,
                expected_previous_sha256=prior_digest,
                new_entries=[entry],
                new_batches=[],
                output=next_ledger,
                root=root,
            )
        latest_ledger = next_ledger
        completed.append(
            {"run_id": run_id, "task_id": task_id, "status": persisted.status}
        )
        if (
            timed_out
            or persisted.status != "completed"
            or manifest.get("cost", {}).get("cost_completeness") != "known"
            or manifest.get("snapshot_consistency") != "stable_task_record_non_atomic"
            or recorded.get("status") == "No-Go"
        ):
            result = {"status": "paused_no_go", "retained": completed}
            _existing_or_write(output_dir / "paused.json", result)
            return result
    result = {"status": "pilot_attempts_captured_review_pending", "retained": completed}
    _existing_or_write(output_dir / "attempts-captured.json", result)
    return result


async def _execute(args: argparse.Namespace, plan: dict[str, Any]) -> dict[str, Any]:
    root = REPOSITORY_ROOT
    book = load_price_book(args.price_book)
    settings = Settings()
    if (
        settings.deepseek_model != plan["public_config_preview"]["model_id"]
        or settings.max_steps != 30
        or settings.recent_trace_count != 5
    ):
        raise PilotRunError("Runtime settings differ from the pilot plan")
    database_url = settings.require_postgres_url()
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        store = PgStore(
            async_sessionmaker(engine, expire_on_commit=False),
            price_book=book,
            require_budget=True,
        )
        secrets = tuple(
            value
            for value in (
                settings.deepseek_api_key.get_secret_value()
                if settings.deepseek_api_key
                else None,
                settings.github_token.get_secret_value()
                if settings.github_token
                else None,
                make_url(database_url).password,
            )
            if value
        )
        async with httpx.AsyncClient(
            base_url=_local_api_url(args.api_url), timeout=15, trust_env=False
        ) as client:
            return await run_pilot(
                plan=plan,
                output_dir=args.output_dir,
                client=client,
                store=store,
                price_book=book,
                authorization_reference=args.authorization_reference,
                prior_ledger=args.ledger,
                expected_prior_ledger_sha256=args.ledger_sha256,
                root=root,
                redact_values=secrets,
            )
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="requires separately authorized paid pilot",
    )
    parser.add_argument("--authorization-reference")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--price-book", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--ledger-sha256")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)
    if not args.execute:
        print(
            "Offline only: no task submitted. Use evaluation.current for a dry-run plan."
        )
        return 0
    if not all(
        (
            args.authorization_reference,
            args.plan,
            args.output_dir,
            args.price_book,
            args.ledger,
            args.ledger_sha256,
        )
    ):
        print(
            "Pilot execution requires plan, output, price book, prior ledger/hash and separate authorization reference.",
            file=sys.stderr,
        )
        return 1
    try:
        args.plan = _rooted(args.plan)
        args.output_dir = _rooted(args.output_dir)
        args.price_book = _rooted(args.price_book)
        args.ledger = _rooted(args.ledger)
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = asyncio.run(_execute(args, plan))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] == "pilot_attempts_captured_review_pending" else 2
    except (OSError, ValueError, KeyError, TypeError, httpx.HTTPError) as exc:
        print(
            f"Pilot stopped before the next submission: {type(exc).__name__}.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
