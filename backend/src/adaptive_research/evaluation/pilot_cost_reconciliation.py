"""Append a bounded cost reconciliation without changing the original capture.

This is offline only. A rounded console display can corroborate calculated
model cost, but it is not an itemized provider invoice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from adaptive_research.evaluation.current import REPOSITORY_ROOT, load_protocol
from adaptive_research.evaluation.project_ledger import LedgerError, build_ledger
from adaptive_research.infrastructure.tool_billing import nonbillable_tool_basis


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _read_artifact(base: Path, value: dict[str, str]) -> tuple[Path, bytes]:
    path = (base / value["relative_path"]).resolve()
    if not path.is_relative_to(base.resolve()):
        raise LedgerError("Reconciliation artifact escapes the ledger directory")
    blob = path.read_bytes()
    if _sha(blob) != value["sha256"]:
        raise LedgerError("Reconciliation input SHA-256 mismatch")
    return path, blob


def _write_once(path: Path, value: dict[str, Any]) -> bytes:
    blob = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(blob)
    return blob


def reconcile_pilot_cost(
    *,
    previous_ledger: Path,
    expected_previous_sha256: str,
    run_id: str,
    attestation_path: Path,
    reconciliation_path: Path,
    output_ledger: Path,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Reclassify only fully observed fixed tools with a rounding-consistent bill."""

    # Validate the active legacy protocol before creating any output. The
    # current discovery protocol has no implementation in this historical tool.
    load_protocol(root)
    base = previous_ledger.resolve().parent
    if any(
        path.resolve().parent != base
        for path in (attestation_path, reconciliation_path, output_ledger)
    ):
        raise LedgerError("All reconciliation files must share the ledger directory")
    if reconciliation_path.exists() or output_ledger.exists():
        raise FileExistsError("Reconciliation outputs are write-once")
    previous_blob = previous_ledger.read_bytes()
    if _sha(previous_blob) != expected_previous_sha256:
        raise LedgerError("Previous ledger SHA-256 mismatch")
    previous = json.loads(previous_blob)
    if previous.get("artifact_type") != "offline_project_cost_ledger":
        raise LedgerError("Previous file is not a project ledger")
    entries = previous.get("entries")
    if not isinstance(entries, list):
        raise LedgerError("Previous ledger has no attempt entries")
    matches = [entry for entry in entries if entry.get("run_id") == run_id]
    if len(matches) != 1:
        raise LedgerError("Run ID must identify exactly one retained attempt")
    original = matches[0]
    if (
        original.get("allocation") != "pilot"
        or original.get("batch_id") is not None
        or original.get("total_cost_cny") is not None
        or type(original.get("unknown_attempt_count")) is not int
        or original["unknown_attempt_count"] < 1
        or "reconciliation_artifact" in original
    ):
        raise LedgerError("Attempt is not an unreconciled pilot stop")
    _, manifest_blob = _read_artifact(base, original["evidence_artifact"])
    manifest = json.loads(manifest_blob)
    if (
        manifest.get("task_id") != original["task_id"]
        or manifest.get("planned_run_id") != run_id
        or manifest.get("cost", {}).get("persisted_unknown_attempt_count")
        != original["unknown_attempt_count"]
    ):
        raise LedgerError("Original capture and ledger disagree")
    capture_dir = (base / original["evidence_artifact"]["relative_path"]).parent
    calls_blob = (capture_dir / "calls.json").read_bytes()
    if _sha(calls_blob) != manifest["artifacts"]["calls.json"]["sha256"]:
        raise LedgerError("Original call capture SHA-256 mismatch")
    calls = json.loads(calls_blob)
    if not isinstance(calls, list) or len({call.get("id") for call in calls}) != len(
        calls
    ):
        raise LedgerError("Call capture is missing or has duplicate IDs")
    model_total = Decimal(0)
    reclassified: list[dict[str, str]] = []
    for call in calls:
        if call.get("status") not in {"completed", "failed"} or not call.get(
            "ended_at"
        ):
            raise LedgerError("Unresolved call cannot be reconciled")
        if call.get("kind") == "model":
            try:
                amount = Decimal(str(call["known_cost_cny"]))
            except (InvalidOperation, KeyError, TypeError) as exc:
                raise LedgerError("Model call cost is unknown") from exc
            if not amount.is_finite() or amount < 0:
                raise LedgerError("Model call cost is invalid")
            model_total += amount
        elif call.get("kind") == "tool" and call.get("known_cost_cny") is None:
            basis = nonbillable_tool_basis("tool", call.get("phase", ""))
            if basis is None:
                raise LedgerError("Tool operation has no verified zero-cost basis")
            reclassified.append(
                {"call_id": call["id"], "operation": call["phase"], "basis": basis}
            )
        else:
            raise LedgerError("Call has an unsupported expense classification")
    if len(reclassified) != original["unknown_attempt_count"] or model_total != Decimal(
        str(original["known_cost_cny"])
    ):
        raise LedgerError("Reclassified calls do not match the original total")
    attestation_blob = attestation_path.read_bytes()
    attestation = json.loads(attestation_blob)
    if (
        attestation.get("run_id") != run_id
        or attestation.get("source") != "user_reported_deepseek_console"
        or attestation.get("display_decimals") != 2
    ):
        raise LedgerError("A run-bound two-decimal console attestation is required")
    try:
        displayed = Decimal(str(attestation["displayed_cost_cny"]))
    except (InvalidOperation, KeyError, TypeError) as exc:
        raise LedgerError("Console display amount is invalid") from exc
    if model_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != displayed:
        raise LedgerError("Calculated model cost contradicts the console display")
    reconciliation = {
        "artifact_type": "pilot_cost_reconciliation",
        "created_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "task_id": original["task_id"],
        "previous_ledger_artifact": {
            "relative_path": previous_ledger.name,
            "sha256": expected_previous_sha256,
        },
        "original_capture_artifact": original["evidence_artifact"],
        "original_calls_sha256": _sha(calls_blob),
        "attestation_artifact": {
            "relative_path": attestation_path.name,
            "sha256": _sha(attestation_blob),
        },
        "model_calculated_cost_cny": str(model_total),
        "console_display_cny": str(displayed),
        "console_display_decimals": 2,
        "reclassified_tool_calls": reclassified,
        "original_unknown_call_count": original["unknown_attempt_count"],
        "reconciled_total_cny": str(model_total),
        "remaining_unknown_call_count": 0,
        "provider_invoice_itemized_verified": False,
        "limitation": "User-reported rounded console display, not an itemized provider invoice; original database and capture remain unchanged.",
    }
    updated = {
        **original,
        "total_cost_cny": str(model_total),
        "unknown_attempt_count": 0,
        "reconciliation_artifact": {
            "relative_path": reconciliation_path.name,
            "sha256": _sha(
                (
                    json.dumps(reconciliation, ensure_ascii=False, indent=2) + "\n"
                ).encode()
            ),
        },
    }
    next_entries = [updated if item["run_id"] == run_id else item for item in entries]
    _write_once(reconciliation_path, reconciliation)
    snapshot = build_ledger(
        entries=next_entries,
        batches=previous.get("batches", []),
        output=output_ledger,
        root=root,
    )
    if snapshot["status"] != "declared_costs_reconciled_offline_only":
        raise LedgerError("Reconciled ledger still has unknown or invalid costs")
    snapshot["previous_ledger_artifact"] = reconciliation["previous_ledger_artifact"]
    snapshot["billing_reconciliation"] = "user_attested_rounded_console_not_itemized"
    _write_once(output_ledger, snapshot)
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-ledger", type=Path, required=True)
    parser.add_argument("--previous-sha256", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attestation", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--output-ledger", type=Path, required=True)
    args = parser.parse_args(argv)
    reconcile_pilot_cost(
        previous_ledger=args.previous_ledger,
        expected_previous_sha256=args.previous_sha256,
        run_id=args.run_id,
        attestation_path=args.attestation,
        reconciliation_path=args.reconciliation,
        output_ledger=args.output_ledger,
    )
    print(
        "Offline reconciliation written; itemized provider invoice remains unverified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
