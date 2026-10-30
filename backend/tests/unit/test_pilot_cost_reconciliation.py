"""Old failed attempts remain immutable while a justified expense is appended."""

import hashlib
import json
from pathlib import Path

import pytest

from adaptive_research.evaluation.pilot_cost_reconciliation import (
    reconcile_pilot_cost,
)
from adaptive_research.evaluation.project_ledger import LedgerError, write_ledger
from tests.unit.test_legacy_entry_guards import install_historical_protocol


def _json(path: Path, value: object) -> str:
    blob = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def _inputs(tmp_path, *, operation="github.get_repository", displayed="0.04"):
    capture = tmp_path / "capture"
    calls_sha = _json(
        capture / "calls.json",
        [
            {
                "id": "model-1",
                "kind": "model",
                "phase": "deepseek.chat_completion",
                "status": "completed",
                "ended_at": "2026-10-22T10:50:00+00:00",
                "known_cost_cny": "0.04139536",
            },
            {
                "id": "tool-1",
                "kind": "tool",
                "phase": operation,
                "status": "failed",
                "ended_at": "2026-10-22T10:50:01+00:00",
                "known_cost_cny": None,
            },
        ],
    )
    manifest_sha = _json(
        capture / "manifest.json",
        {
            "planned_run_id": "run-1",
            "task_id": "task-1",
            "cost": {"persisted_unknown_attempt_count": 1},
            "artifacts": {"calls.json": {"sha256": calls_sha}},
        },
    )
    previous = tmp_path / "previous.json"
    write_ledger(
        entries=[
            {
                "run_id": "run-1",
                "task_id": "task-1",
                "allocation": "pilot",
                "batch_id": None,
                "known_cost_cny": "0.04139536",
                "total_cost_cny": None,
                "unknown_attempt_count": 1,
                "evidence_artifact": {
                    "relative_path": "capture/manifest.json",
                    "sha256": manifest_sha,
                },
                "authorization_reference": "approval:old-pilot",
                "attempt_status": "partial",
            }
        ],
        batches=[],
        output=previous,
    )
    prior_sha = hashlib.sha256(previous.read_bytes()).hexdigest()
    attestation = tmp_path / "attestation.json"
    _json(
        attestation,
        {
            "run_id": "run-1",
            "source": "user_reported_deepseek_console",
            "displayed_cost_cny": displayed,
            "display_decimals": 2,
        },
    )
    return {
        "previous_ledger": previous,
        "expected_previous_sha256": prior_sha,
        "run_id": "run-1",
        "attestation_path": attestation,
        "reconciliation_path": tmp_path / "reconciliation.json",
        "output_ledger": tmp_path / "reconciled-ledger.json",
    }


def test_reconciles_rounded_console_with_fixed_tool_and_retains_original(tmp_path):
    args = _inputs(tmp_path)
    old_blob = args["previous_ledger"].read_bytes()
    result = reconcile_pilot_cost(**args)
    assert result["status"] == "declared_costs_reconciled_offline_only"
    assert result["entries"][0]["total_cost_cny"] == 0.04139536
    assert result["entries"][0]["unknown_attempt_count"] == 0
    assert args["previous_ledger"].read_bytes() == old_blob
    assert (
        json.loads(args["reconciliation_path"].read_text())[
            "provider_invoice_itemized_verified"
        ]
        is False
    )
    with pytest.raises(FileExistsError):
        reconcile_pilot_cost(**args)


@pytest.mark.parametrize(
    ("operation", "displayed", "message"),
    [
        ("mcp.search", "0.04", "zero-cost basis"),
        ("github.get_repository", "0.05", "contradicts"),
    ],
)
def test_unknown_operation_or_conflicting_bill_cannot_be_reconciled(
    tmp_path, operation, displayed, message
):
    args = _inputs(tmp_path, operation=operation, displayed=displayed)
    with pytest.raises(LedgerError, match=message):
        reconcile_pilot_cost(**args)
    assert not args["output_ledger"].exists()


@pytest.fixture(autouse=True)
def explicit_historical_protocol(monkeypatch, tmp_path):
    """These regression fixtures exercise identified current-3 inputs only."""
    install_historical_protocol(monkeypatch, tmp_path)
