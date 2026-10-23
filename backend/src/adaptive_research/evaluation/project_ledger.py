"""Reconcile explicitly declared paid attempts without executing research.

This is an offline evidence index, not a payment authorization or a provider
invoice. Unknown or inconsistent attempts remain visible in a No-Go snapshot.
Only a separately authorized caller may use a successful budget preflight to
decide whether to initiate a future paid call.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from adaptive_research.evaluation.current import REPOSITORY_ROOT, load_protocol

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9:/._-]{3,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SENSITIVE = re.compile(r"(?i)(?:^sk-|bearer|password|api.?key|secret|cookie)")
_MONEY_UNIT = Decimal("0.00000001")


class LedgerError(ValueError):
    """A declaration is ambiguous, unsafe, or exceeds a declared ceiling."""


def _identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise LedgerError(f"{label} needs a bounded public identifier")
    return value


def _reference(value: Any) -> str:
    if (
        not isinstance(value, str)
        or _REFERENCE.fullmatch(value) is None
        or _SENSITIVE.search(value)
    ):
        raise LedgerError("A bounded non-secret authorization reference is required")
    return value


def _artifact(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise LedgerError("An explicit evidence artifact is required")
    path, digest = value.get("relative_path"), value.get("sha256")
    if not isinstance(path, str) or not path.strip() or Path(path).is_absolute():
        raise LedgerError("Evidence artifact path must be relative")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise LedgerError("Evidence artifact SHA-256 must be lowercase hex")
    return {"relative_path": path, "sha256": digest}


def _money(value: Any, label: str) -> tuple[Decimal, float] | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise LedgerError(f"{label} must be an explicit CNY amount or null")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise LedgerError(f"{label} is not a CNY amount") from exc
    try:
        exact_at_storage_precision = amount == amount.quantize(_MONEY_UNIT)
        exact_json_number = Decimal(str(float(amount))) == amount
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise LedgerError(f"{label} cannot be represented exactly") from exc
    if (
        not amount.is_finite()
        or amount < 0
        or not (exact_at_storage_precision and exact_json_number)
    ):
        raise LedgerError(f"{label} cannot be represented exactly at 8 CNY decimals")
    return amount, float(amount)


def _entry(value: Any, allocations: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LedgerError("Each attempt must be an object")
    run_id = _identity(value.get("run_id"), "run_id")
    task_id = _identity(value.get("task_id"), "task_id")
    allocation = value.get("allocation")
    if not isinstance(allocation, str) or allocation not in allocations:
        raise LedgerError("Attempt allocation is not in current-3")
    batch_id = value.get("batch_id")
    if batch_id is not None:
        batch_id = _identity(batch_id, "batch_id")
    known = _money(value.get("known_cost_cny"), "known_cost_cny")
    total = _money(value.get("total_cost_cny"), "total_cost_cny")
    unknown = value.get("unknown_attempt_count")
    if unknown is not None and (type(unknown) is not int or unknown < 0):
        raise LedgerError("Unknown attempt count must be a nonnegative int or null")
    if (unknown is not None and unknown > 0 and total is not None) or (
        total is not None and (known is None or known[0] != total[0])
    ):
        raise LedgerError("Known and unknown expense declarations conflict")
    result = {
        "run_id": run_id,
        "task_id": task_id,
        "allocation": allocation,
        "batch_id": batch_id,
        "known_cost_cny": known[1] if known is not None else None,
        "total_cost_cny": total[1] if total is not None else None,
        "unknown_attempt_count": unknown,
        "evidence_artifact": _artifact(value.get("evidence_artifact")),
        "authorization_reference": _reference(value.get("authorization_reference")),
    }
    if "attempt_status" in value:
        result["attempt_status"] = _identity(value["attempt_status"], "attempt_status")
    if "reconciliation_artifact" in value:
        result["reconciliation_artifact"] = _artifact(value["reconciliation_artifact"])
    return result


def _batch(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LedgerError("Each batch must be an object")
    if not isinstance(value.get("phase"), str) or value["phase"] not in {
        "pilot",
        "formal",
    }:
        raise LedgerError("Only pilot/formal completed batch references are valid")
    return {
        "batch_id": _identity(value.get("batch_id"), "batch_id"),
        "phase": value["phase"],
        "artifact": _artifact(value.get("artifact")),
    }


def _validator(root: Path) -> Any:
    path = root / "scripts/validate_project.py"
    spec = importlib.util.spec_from_file_location("_ledger_protocol_validator", path)
    if spec is None or spec.loader is None:
        raise LedgerError("Current protocol validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_ledger(
    *,
    entries: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    output: Path,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Build a diagnostic snapshot from explicit identities, costs and hashes.

    The authoritative validator reopens every referenced artifact relative to
    ``output.parent``. It cannot establish that all provider-billed attempts
    were declared; reconciliation with provider billing remains manual.
    """

    if not isinstance(entries, list) or not isinstance(batches, list):
        raise LedgerError("Entries and batches must be arrays")
    if len(entries) > 10_000 or len(batches) > 1_000:
        raise LedgerError("Ledger declaration is too large")
    root = root.resolve()
    protocol, resources = load_protocol(root)
    contract = protocol["project_ledger_contract"]
    allocations = set(contract["allocations_cny"])
    normalized = [_entry(value, allocations) for value in entries]
    normalized_batches = [_batch(value) for value in batches]
    if len({item["run_id"] for item in normalized}) != len(normalized):
        raise LedgerError("Duplicate run ID would hide a paid attempt")
    if len({item["batch_id"] for item in normalized_batches}) != len(
        normalized_batches
    ):
        raise LedgerError("Duplicate batch ID")
    known = {allocation: Decimal(0) for allocation in allocations}
    unknown = 0
    missing_unknown_count = False
    for item in normalized:
        amount = item["known_cost_cny"]
        if amount is not None:
            known[item["allocation"]] += Decimal(str(amount))
        if item["unknown_attempt_count"] is None:
            missing_unknown_count = True
        else:
            unknown += item["unknown_attempt_count"]
    declared = {
        "protocol_version": protocol["protocol_version"],
        "batches": normalized_batches,
        "entries": normalized,
    }
    try:
        errors = _validator(root).check_ledger(
            protocol, declared, output.resolve().parent
        )
    except (KeyError, TypeError, ValueError, OSError):
        # Keep the paid-attempt declarations even when referenced batch JSON
        # cannot be interpreted. Never turn validator failure into readiness.
        errors = ["No-Go: batch evidence could not be validated"]
    return {
        **declared,
        "artifact_type": "offline_project_cost_ledger",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "No-Go"
        if errors or unknown or missing_unknown_count
        else "declared_costs_reconciled_offline_only",
        "new_paid_calls_authorized": False,
        "unknown_attempt_count": None if missing_unknown_count else unknown,
        "known_subtotals_cny": {
            name: str(known[name]) for name in contract["allocations_cny"]
        },
        "known_project_subtotal_cny": str(sum(known.values(), Decimal(0))),
        "declared_project_total_cny": (
            str(sum(known.values(), Decimal(0)))
            if not errors and not unknown and not missing_unknown_count
            else None
        ),
        "allocation_limits_cny": contract["allocations_cny"].copy(),
        "project_max_cny": contract["total_max_cny"],
        "protocol_sha256": resources["docs/evaluation/CURRENT_EVAL_PROTOCOL.json"],
        "validation_errors": errors,
        "billing_reconciliation": "not_verified_against_provider_invoice",
        "note": "Only declared attempts are checked; this snapshot does not authorize spending or prove completeness against provider billing.",
    }


def write_ledger(
    *,
    entries: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    output: Path,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Create one immutable-on-write snapshot; never replace earlier evidence."""

    snapshot = build_ledger(entries=entries, batches=batches, output=output, root=root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return snapshot


def extend_ledger(
    *,
    previous: Path,
    expected_previous_sha256: str,
    new_entries: list[dict[str, Any]],
    new_batches: list[dict[str, Any]],
    output: Path,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Carry every prior declaration into a new write-once snapshot.

    Both files must share a directory because evidence paths are relative to
    the ledger. The caller pins the previous exact bytes; this is not a
    substitute for a durable application ledger or a provider invoice.
    """

    if (
        not isinstance(expected_previous_sha256, str)
        or _SHA256.fullmatch(expected_previous_sha256) is None
    ):
        raise LedgerError("A previous ledger SHA-256 is required")
    if previous.resolve().parent != output.resolve().parent:
        raise LedgerError("Ledger snapshots must share an evidence directory")
    if not isinstance(new_entries, list) or not isinstance(new_batches, list):
        raise LedgerError("New entries and batches must be arrays")
    blob = previous.read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected_previous_sha256:
        raise LedgerError("Previous ledger SHA-256 mismatch")
    try:
        earlier = json.loads(blob)
    except (UnicodeError, ValueError) as exc:
        raise LedgerError("Previous ledger is unreadable") from exc
    if not isinstance(earlier, dict) or earlier.get("artifact_type") != (
        "offline_project_cost_ledger"
    ):
        raise LedgerError("Previous file is not a project ledger")
    protocol, resources = load_protocol(root.resolve())
    if (
        earlier.get("protocol_version") != protocol["protocol_version"]
        or earlier.get("protocol_sha256")
        != resources["docs/evaluation/CURRENT_EVAL_PROTOCOL.json"]
        or not isinstance(earlier.get("entries"), list)
        or not isinstance(earlier.get("batches"), list)
    ):
        raise LedgerError("Previous ledger does not match the current protocol")
    snapshot = build_ledger(
        entries=[*earlier["entries"], *new_entries],
        batches=[*earlier["batches"], *new_batches],
        output=output,
        root=root,
    )
    snapshot["previous_ledger_artifact"] = {
        "relative_path": previous.name,
        "sha256": expected_previous_sha256,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return snapshot


def assert_declared_reservation_fits(
    *,
    entries: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    output: Path,
    allocation: str,
    reserve_cny: Decimal,
    authorization_reference: str,
    root: Path = REPOSITORY_ROOT,
) -> None:
    """Fail closed on declared costs; separate paid authorization is still required.

    Call immediately before a separately authorized paid attempt, using the
    latest full ledger and a conservative reservation. This cannot establish
    that an undeclared provider charge does not exist.
    """

    _reference(authorization_reference)
    if not isinstance(reserve_cny, Decimal):
        raise LedgerError("A positive explicit CNY reservation is required")
    reservation = _money(reserve_cny, "reserve_cny")
    if reservation is None or reservation[0] <= 0:
        raise LedgerError("A positive explicit CNY reservation is required")
    snapshot = build_ledger(entries=entries, batches=batches, output=output, root=root)
    if snapshot["status"] != "declared_costs_reconciled_offline_only":
        raise LedgerError("Ledger has unresolved or invalid paid attempts; No-Go")
    limits = snapshot["allocation_limits_cny"]
    if not isinstance(allocation, str) or allocation not in limits:
        raise LedgerError("Unknown allocation")
    spent = Decimal(snapshot["known_subtotals_cny"][allocation])
    project_spent = Decimal(snapshot["known_project_subtotal_cny"])
    if project_spent + reservation[0] > Decimal(snapshot["project_max_cny"]):
        raise LedgerError("Project ceiling cannot cover the next reservation")
    if spent + reservation[0] > Decimal(limits[allocation]):
        raise LedgerError("Allocation ceiling cannot cover the next reservation")
