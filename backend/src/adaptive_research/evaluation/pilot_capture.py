"""Read-only diagnostic exports of persisted pilot attempts; never submit work.

The caller supplies an owner-scoped store (preferably using a read-only database
role). Only its five read methods are used. This module creates no database,
provider or browser clients and has no live execution entry point.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import unquote, urlsplit, urlunsplit

from adaptive_research.evaluation.current import (
    PROTOCOL_PATH,
    REPOSITORY_ROOT,
    _source_fingerprint,
    load_protocol,
)

TERMINAL = {"completed", "partial", "failed", "cancelled"}
TASK_FIELDS = (
    "id",
    "status",
    "cancellation_requested",
    "fencing_token",
    "recovery_count",
    "completion_level",
    "stop_reason",
    "error_message",
    "created_at",
    "updated_at",
)
CALL_FIELDS = (
    "id",
    "task_id",
    "fencing_token",
    "phase",
    "kind",
    "status",
    "provider",
    "model",
    "price_revision",
    "reported_prompt_tokens",
    "reported_completion_tokens",
    "prompt_cache_hit_tokens",
    "prompt_cache_miss_tokens",
    "provider_created_at",
    "reported_model",
    "system_fingerprint",
    "pricing_error",
    "pricing_tariff",
    "known_cost_cny",
    "failure_type",
    "started_at",
    "ended_at",
)
FACT_FIELDS = (
    "id",
    "task_id",
    "fencing_token",
    "subject",
    "claim",
    "official_source_url",
    "official_identity_basis",
    "evidence_excerpt",
    "evidence_locator",
    "retrieved_at",
    "machine_admission_status",
    "human_review_status",
    "reviewed_at",
    "created_at",
)
REPORT_FIELDS = (
    "task_id",
    "goal",
    "title",
    "summary",
    "comparison",
    "recommendation",
    "sources",
    "markdown",
    "generated_at",
)
_SENSITIVE = re.compile(
    r"(?i)(api.?key|access.?token|refresh.?token|secret|password|authorization|cookie|session.?id|private.?key)"
)
_ASSIGNMENT = re.compile(
    r"(?i)[\"']?\b(?:api[_-]?key|[\w-]*token|secret|password|authorization|cookie|session[_-]?id|private[_-]?key)\b[\"']?\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)
_HEADER = re.compile(
    r"(?im)\b(?:set-cookie|cookie|(?:proxy-)?authorization)\s*[:=][^\r\n]+"
)
_KEY = re.compile(
    r"(?i)\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})\b"
)
_URL = re.compile(r"https?://[^\s<>\])}\"']+", re.IGNORECASE)
_HTML = re.compile(r"<!doctype\b|<!--|</?[A-Za-z][^>]*>", re.IGNORECASE)


class CaptureError(ValueError):
    """The requested diagnostic capture cannot be bound or safely written."""


class ReadOnlyAttemptStore(Protocol):
    async def get_task(self, owner_id: str, task_id: str) -> Any: ...
    async def list_events(self, owner_id: str, task_id: str) -> Any: ...
    async def list_calls(self, owner_id: str, task_id: str) -> Any: ...
    async def list_facts(self, owner_id: str, task_id: str) -> Any: ...
    async def get_cost(self, owner_id: str, task_id: str) -> Any: ...


def _get(record: Any, name: str) -> Any:
    return (
        record.get(name) if isinstance(record, Mapping) else getattr(record, name, None)
    )


def _project(record: Any, names: tuple[str, ...]) -> dict[str, Any]:
    return {name: _get(record, name) for name in names}


def _bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class _Sanitizer:
    def __init__(self, secrets: tuple[str, ...], max_text_chars: int) -> None:
        self.secrets = tuple(sorted((v for v in secrets if v), key=len, reverse=True))
        self.max_text_chars = max_text_chars
        self.truncated_texts = 0
        self.omitted_html = 0
        self.omitted_sensitive_fields = 0

    @staticmethod
    def _url(value: str) -> str:
        try:
            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                return "[URL_OMITTED]"
            host = parsed.hostname
            if ":" in host:
                host = f"[{host}]"
            port = f":{parsed.port}" if parsed.port else ""
            path = "" if _SENSITIVE.search(unquote(parsed.path)) else parsed.path
            return urlunsplit((parsed.scheme, host + port, path, "", ""))
        except ValueError:
            return "[URL_OMITTED]"

    def clean(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value) if value.is_finite() else None
        if isinstance(value, Mapping):
            result = {}
            for key, item in value.items():
                if not isinstance(key, str) or _SENSITIVE.search(key):
                    self.omitted_sensitive_fields += 1
                    continue
                result[self.clean(key)] = self.clean(item)
            return result
        if isinstance(value, (tuple, list)):
            return [self.clean(item) for item in value]
        if not isinstance(value, str):
            return value if value is None or type(value) in {bool, int, float} else None
        for secret in self.secrets:
            value = value.replace(secret, "[REDACTED]")
        if _HTML.search(value):
            self.omitted_html += 1
            return "[RAW_HTML_OMITTED]"
        value = _HEADER.sub("[REDACTED_HEADER]", value)
        value = re.sub(r"(?i)\bBearer\s+[^\s,;}]+", "[REDACTED]", value)
        value = _ASSIGNMENT.sub("[REDACTED_ASSIGNMENT]", value)
        value = _KEY.sub("[REDACTED]", value)
        value = _URL.sub(lambda match: self._url(match.group()), value)
        if len(value) > self.max_text_chars:
            self.truncated_texts += 1
            value = value[: self.max_text_chars] + "[TRUNCATED]"
        return value


def _report(report: Any) -> dict[str, Any] | None:
    if not isinstance(report, Mapping):
        return None
    result = _project(report, REPORT_FIELDS)
    result["findings"] = (
        [
            _project(
                finding,
                (
                    "name",
                    "description",
                    "attributes",
                    "supporting_fact_ids",
                    "source_urls",
                ),
            )
            for finding in report.get("findings", [])
            if isinstance(finding, Mapping)
        ]
        if isinstance(report.get("findings", []), list)
        else []
    )
    return result


def _event(event: Any) -> dict[str, Any]:
    result = _project(
        event, ("id", "task_id", "event_type", "step", "message", "created_at")
    )
    payload = _get(event, "payload")
    payload = payload if isinstance(payload, Mapping) else {}
    result["payload"] = {
        key: payload[key]
        for key in (
            "status",
            "completion_level",
            "stop_reason",
            "cancellation_requested",
            "recovery_count",
            "prompt_tokens",
            "completion_tokens",
        )
        if key in payload
    }
    # Tool bodies, metadata, arguments and browser observations never cross this boundary.
    for name, fields in (
        ("decision", ("subgoal_id", "tool", "action")),
        (
            "tool_result",
            ("tool", "action", "success", "source_url", "error_type", "error_message"),
        ),
        (
            "evaluation",
            ("success", "reason", "subgoal_completed", "should_replan", "error_type"),
        ),
    ):
        if isinstance(payload.get(name), Mapping):
            result["payload"][name] = _project(payload[name], fields)
    result["payload_projection"] = "diagnostic_allowlist_not_raw_trace"
    return result


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() and result >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def _cost_summary(
    task: Any, calls: list[Any] | None, cost: Any, truncated: bool
) -> dict[str, Any]:
    known = _decimal(_get(cost, "known_cost_cny")) if cost is not None else None
    unknown = _get(cost, "unknown_attempt_count") if cost is not None else None
    unknown = unknown if type(unknown) is int and unknown >= 0 else None
    unresolved = [
        str(_get(call, "id"))
        for call in calls or ()
        if _get(call, "status") in {"started", "unknown_outcome"}
        or _get(call, "ended_at") is None
    ]
    unpriced = (
        sum(_decimal(_get(call, "known_cost_cny")) is None for call in calls)
        if calls is not None
        else None
    )
    subtotal = sum(
        (_decimal(_get(call, "known_cost_cny")) or Decimal(0) for call in calls or ()),
        Decimal(0),
    )
    consistent = (
        known == subtotal
        if known is not None and calls is not None and not truncated
        else None
    )
    fully_known = (
        known is not None
        and unknown == 0
        and unpriced == 0
        and not unresolved
        and consistent is True
        and _get(task, "status") in TERMINAL
        and not truncated
    )
    return {
        "currency": "CNY",
        "persisted_known_cost_cny": str(known) if known is not None else None,
        "persisted_unknown_attempt_count": unknown,
        "observed_unpriced_call_count": unpriced,
        "observed_call_known_subtotal_cny": str(subtotal)
        if calls is not None
        else None,
        "observed_unresolved_call_ids": unresolved if calls is not None else None,
        "task_and_call_known_cost_match": consistent,
        "actual_total_cost_cny": str(known) if fully_known else None,
        "cost_completeness": "known" if fully_known else "unknown_or_incomplete",
    }


async def capture_attempt(
    store: ReadOnlyAttemptStore,
    *,
    plan: Mapping[str, Any],
    planned_run_id: str,
    task_id: str,
    case_id: str,
    trial_index: int,
    owner_id: str,
    output_dir: Path,
    root: Path = REPOSITORY_ROOT,
    redact_values: tuple[str, ...] = (),
    max_records: int = 1000,
    max_text_chars: int = 4000,
    read_timeout_seconds: float = 10,
    max_total_bytes: int = 8_000_000,
) -> dict[str, Any]:
    """Export one existing pilot task, including unknown/incomplete persisted state.

    The output directory must be new. The capture is a sequence of bounded reads,
    not an atomic database snapshot or proof of the code used during execution.
    Supply known secret values explicitly for literal redaction; environment and
    credential files are never read by this exporter.
    """

    if not 1 <= max_records <= 10_000 or not 128 <= max_text_chars <= 12_000:
        raise CaptureError("Invalid capture bounds")
    if not 0 < read_timeout_seconds <= 60 or not 1024 <= max_total_bytes <= 32_000_000:
        raise CaptureError("Invalid capture bounds")
    if any(
        not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value)
        for value in (planned_run_id, task_id, owner_id)
    ):
        raise CaptureError("Invalid attempt identity")
    protocol, resources = load_protocol(root)
    if (
        plan.get("artifact_type") != "evaluation_dry_run_plan"
        or plan.get("protocol_version") != protocol["protocol_version"]
        or plan.get("phase") != "pilot"
        or plan.get("execution_allowed") is not False
        or plan.get("status") != "not_live_execution"
        or plan.get("attempts_started") != 0
        or _get(plan.get("fingerprints"), "protocol_sha256") != resources[PROTOCOL_PATH]
    ):
        raise CaptureError("A current-3 pilot dry-run plan is required")
    runs = [
        run
        for run in plan.get("planned_runs", [])
        if isinstance(run, Mapping) and run.get("planned_run_id") == planned_run_id
    ]
    case = next((case for case in protocol["cases"] if case["id"] == case_id), None)
    if (
        len(runs) != 1
        or case_id not in protocol["pilot"]["case_ids"]
        or type(trial_index) is not int
        or trial_index != 1
        or runs[0].get("case_id") != case_id
        or runs[0].get("trial_index") != trial_index
        or case is None
        or runs[0].get("prompt") != case["prompt"]
        or runs[0].get("required_fields") != case["required_fields"]
    ):
        raise CaptureError("Pilot run/case/trial binding does not match")
    if output_dir.exists():
        raise FileExistsError("Capture directory already exists")
    failures: dict[str, str] = {}

    async def read(name: str) -> Any:
        try:
            return await asyncio.wait_for(
                getattr(store, name)(owner_id, task_id), timeout=read_timeout_seconds
            )
        except Exception as exc:  # noqa: BLE001 - retain unavailable reads without exposing exception contents
            failures[name] = type(exc).__name__
            return None

    task = await read("get_task")
    if task is not None and _get(task, "id") != task_id:
        failures["get_task"] = "TaskIdentityMismatch"
        task = None
    reads = {}
    truncated = {}
    if task is not None:
        for name in ("list_events", "list_calls", "list_facts", "get_cost"):
            value = await read(name)
            if name.startswith("list_") and value is not None:
                if not isinstance(value, list):
                    failures[name] = "InvalidReadShape"
                    value = None
                else:
                    truncated[name] = len(value) > max_records
                    value = value[:max_records]
                    if any(_get(row, "task_id") != task_id for row in value):
                        failures[name] = "TaskIdentityMismatch"
                        value = None
            reads[name] = value
        after = await read("get_task")
        stable = (
            after is not None
            and _project(task, TASK_FIELDS) == _project(after, TASK_FIELDS)
            and _get(task, "report") == _get(after, "report")
        )
    else:
        stable = None
    sanitizer = _Sanitizer(redact_values, max_text_chars)
    events, calls, facts = (
        reads.get(name) for name in ("list_events", "list_calls", "list_facts")
    )
    current_source = _source_fingerprint(root)
    planned_source = _get(plan.get("fingerprints"), "source")
    source_version = {
        "plan_id": plan.get("plan_id"),
        "plan_canonical_sha256": _hash(_bytes(dict(plan))),
        "planned_protocol_sha256": resources[PROTOCOL_PATH],
        "planned_source_sha256": _get(planned_source, "sha256"),
        "capture_source_sha256": current_source["sha256"],
        "capture_source_files": current_source["files"],
        "planned_dependency_lock_sha256": _get(
            plan.get("fingerprints"), "dependency_lock_sha256"
        ),
        "capture_dependency_lock_sha256": resources["backend/uv.lock"],
        "planned_source_matches_capture": _get(planned_source, "sha256")
        == current_source["sha256"],
        "execution_source_verified": False,
        "note": "Neither dry-run nor capture hashes prove the source used by an existing task.",
    }
    documents = {
        "task.json": sanitizer.clean(_project(task, TASK_FIELDS))
        if task is not None
        else None,
        "report.json": sanitizer.clean(_report(_get(task, "report"))),
        "events.json": sanitizer.clean([_event(event) for event in events])
        if events is not None
        else None,
        "calls.json": sanitizer.clean([_project(call, CALL_FIELDS) for call in calls])
        if calls is not None
        else None,
        "facts.json": sanitizer.clean([_project(fact, FACT_FIELDS) for fact in facts])
        if facts is not None
        else None,
        "source-version.json": source_version,
    }
    artifacts = {name: _bytes(document) for name, document in documents.items()}
    manifest = {
        "artifact_type": "persisted_pilot_diagnostic_capture",
        "status": "diagnostic_not_release",
        "product_release": "No-Go",
        "formal_acceptance": None,
        "research_quality_passed": None,
        "captured_at": datetime.now(UTC).isoformat(),
        "phase": "pilot",
        "planned_run_id": planned_run_id,
        "task_id": task_id,
        "case_id": case_id,
        "trial_index": trial_index,
        "owner_id_sha256": _hash(owner_id.encode()),
        "task_visibility": "visible"
        if task is not None
        else "unknown_not_visible_or_uncommitted",
        "persisted_task_status": _get(task, "status"),
        "persisted_completion_level": _get(task, "completion_level"),
        "task_terminal": _get(task, "status") in TERMINAL if task is not None else None,
        "goal_matches_planned_prompt": _get(task, "goal") == case["prompt"]
        if task is not None
        else None,
        "snapshot_consistency": "stable_task_record_non_atomic"
        if stable
        else "changed_or_unavailable_non_atomic",
        "read_failures": failures,
        "truncated_collections": truncated,
        "redaction": {
            "truncated_text_count": sanitizer.truncated_texts,
            "omitted_html_count": sanitizer.omitted_html,
            "omitted_sensitive_field_count": sanitizer.omitted_sensitive_fields,
            "boundary": "allowlisted_metadata_and_redacted_report_facts; no raw tool bodies or observations",
        },
        "cost": _cost_summary(
            task,
            calls,
            reads.get("get_cost"),
            any(truncated.values()) or bool(failures) or not stable,
        ),
        "official_source_verification": "not_performed_by_exporter; persisted human status is not independently verified",
        "capture_provider_calls": 0,
        "capture_browser_calls": 0,
        "capture_tasks_submitted": 0,
        "capture_database_writes": 0,
        "artifacts": {
            name: {"sha256": _hash(blob), "bytes": len(blob)}
            for name, blob in artifacts.items()
        },
        "limits": {
            "max_records_per_collection": max_records,
            "max_text_chars": max_text_chars,
            "read_timeout_seconds": read_timeout_seconds,
            "max_total_bytes": max_total_bytes,
        },
        "note": "Diagnostic projection only; preserve original database evidence. No attempt, review, or release success is inferred.",
    }
    manifest = sanitizer.clean(manifest)
    artifacts["manifest.json"] = _bytes(manifest)
    if sum(map(len, artifacts.values())) > max_total_bytes:
        raise CaptureError(
            "Capture exceeds output byte bound; no artifact directory created"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(exist_ok=False)
    for name, blob in artifacts.items():
        with (output_dir / name).open("xb") as stream:
            stream.write(blob)
    return manifest
