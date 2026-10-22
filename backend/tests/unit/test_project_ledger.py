"""Project ledger checks declared attempts and refuses unsafe reservations."""

import hashlib
from decimal import Decimal

import pytest

from adaptive_research.evaluation.project_ledger import (
    LedgerError,
    assert_declared_reservation_fits,
    build_ledger,
    extend_ledger,
    write_ledger,
)


def _evidence(tmp_path):
    path = tmp_path / "attempt.json"
    blob = b'{"attempt":"retained"}\n'
    path.write_bytes(blob)
    return {
        "relative_path": path.name,
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def _entry(tmp_path, **changes):
    result = {
        "run_id": "pilot-B01-1",
        "task_id": "task-1",
        "allocation": "pilot",
        "batch_id": None,
        "known_cost_cny": "0.12500001",
        "total_cost_cny": "0.12500001",
        "unknown_attempt_count": 0,
        "evidence_artifact": _evidence(tmp_path),
        "authorization_reference": "approval:pilot-1",
        "attempt_status": "completed",
    }
    result.update(changes)
    return result


def _build(tmp_path, entries, batches=None):
    return build_ledger(
        entries=entries,
        batches=batches or [],
        output=tmp_path / "project-ledger.json",
    )


def test_known_attempt_retains_exact_amount_and_does_not_grant_authorization(tmp_path):
    result = _build(tmp_path, [_entry(tmp_path)])
    assert result["validation_errors"] == []
    assert result["status"] == "declared_costs_reconciled_offline_only"
    assert result["known_subtotals_cny"]["pilot"] == "0.12500001"
    assert result["known_project_subtotal_cny"] == "0.12500001"
    assert result["declared_project_total_cny"] == "0.12500001"
    assert result["new_paid_calls_authorized"] is False
    assert result["billing_reconciliation"] == "not_verified_against_provider_invoice"


def test_interrupted_unknown_attempt_is_written_but_blocks_new_paid_call(tmp_path):
    entry = _entry(
        tmp_path,
        known_cost_cny="0.01",
        total_cost_cny=None,
        unknown_attempt_count=1,
        attempt_status="interrupted",
    )
    output = tmp_path / "project-ledger.json"
    result = write_ledger(entries=[entry], batches=[], output=output)
    assert output.exists()
    assert result["entries"][0]["attempt_status"] == "interrupted"
    assert result["entries"][0]["total_cost_cny"] is None
    assert result["unknown_attempt_count"] == 1
    assert result["known_project_subtotal_cny"] == "0.01"
    assert result["declared_project_total_cny"] is None
    assert result["status"] == "No-Go"
    assert any("cost unknown" in error for error in result["validation_errors"])
    with pytest.raises(LedgerError, match="No-Go"):
        assert_declared_reservation_fits(
            entries=[entry],
            batches=[],
            output=tmp_path / "next.json",
            allocation="pilot",
            reserve_cny=Decimal(1),
            authorization_reference="approval:pilot-2",
        )
    with pytest.raises(FileExistsError):
        write_ledger(entries=[entry], batches=[], output=output)


def test_duplicate_run_or_batch_identity_is_rejected(tmp_path):
    first = _entry(tmp_path)
    second = _entry(tmp_path, task_id="task-2")
    with pytest.raises(LedgerError, match="Duplicate run ID"):
        _build(tmp_path, [first, second])
    batches = [
        {
            "batch_id": "pilot-batch-1",
            "phase": "pilot",
            "artifact": _evidence(tmp_path),
        }
    ] * 2
    with pytest.raises(LedgerError, match="Duplicate batch ID"):
        _build(tmp_path, [], batches)


@pytest.mark.parametrize("reference", [None, "", "sk-abcdefghijklmnop", "password=hi"])
def test_missing_or_secret_like_authorization_reference_is_rejected(
    tmp_path, reference
):
    with pytest.raises(LedgerError, match="authorization reference"):
        _build(tmp_path, [_entry(tmp_path, authorization_reference=reference)])


def test_artifact_hash_mismatch_is_retained_as_no_go(tmp_path):
    evidence = _evidence(tmp_path)
    evidence["sha256"] = "0" * 64
    entry = _entry(tmp_path, evidence_artifact=evidence)
    result = _build(tmp_path, [entry])
    assert result["status"] == "No-Go"
    assert result["declared_project_total_cny"] is None
    assert any("SHA-256 mismatch" in item for item in result["validation_errors"])
    with pytest.raises(LedgerError, match="No-Go"):
        assert_declared_reservation_fits(
            entries=[entry],
            batches=[],
            output=tmp_path / "next.json",
            allocation="pilot",
            reserve_cny=Decimal(1),
            authorization_reference="approval:pilot-2",
        )


def test_allocation_and_project_subtotals_include_all_phases(tmp_path):
    entries = [
        _entry(
            tmp_path,
            run_id="pilot-1",
            allocation="pilot",
            known_cost_cny=49,
            total_cost_cny=49,
        ),
        _entry(
            tmp_path,
            run_id="diagnostic-1",
            allocation="diagnostic",
            known_cost_cny=30,
            total_cost_cny=30,
        ),
        _entry(
            tmp_path,
            run_id="formal-1",
            allocation="formal",
            known_cost_cny=199,
            total_cost_cny=199,
        ),
        _entry(
            tmp_path,
            run_id="contingency-1",
            allocation="contingency",
            known_cost_cny=20,
            total_cost_cny=20,
        ),
    ]
    result = _build(tmp_path, entries)
    assert result["validation_errors"] == []
    assert result["known_project_subtotal_cny"] == "298.0"
    assert result["project_max_cny"] == 299
    with pytest.raises(LedgerError, match="Allocation ceiling"):
        assert_declared_reservation_fits(
            entries=entries,
            batches=[],
            output=tmp_path / "next.json",
            allocation="pilot",
            reserve_cny=Decimal("0.01"),
            authorization_reference="approval:pilot-2",
        )
    with pytest.raises(LedgerError, match="Project ceiling"):
        assert_declared_reservation_fits(
            entries=entries,
            batches=[],
            output=tmp_path / "next.json",
            allocation="formal",
            reserve_cny=Decimal("1.01"),
            authorization_reference="approval:formal-2",
        )


def test_overspent_allocation_remains_no_go_even_with_known_cost(tmp_path):
    result = _build(
        tmp_path,
        [_entry(tmp_path, known_cost_cny=50, total_cost_cny=50)],
    )
    assert result["status"] == "No-Go"
    assert result["declared_project_total_cny"] is None
    assert any(
        "pilot allocation exceeds 49" in error for error in result["validation_errors"]
    )


def test_cost_conflict_and_missing_unknown_count_are_rejected(tmp_path):
    incomplete = _build(tmp_path, [_entry(tmp_path, total_cost_cny=None)])
    assert incomplete["status"] == "No-Go"
    assert incomplete["entries"][0]["total_cost_cny"] is None
    assert incomplete["validation_errors"]
    missing_count = _build(tmp_path, [_entry(tmp_path, unknown_attempt_count=None)])
    assert missing_count["status"] == "No-Go"
    assert missing_count["unknown_attempt_count"] is None
    with pytest.raises(LedgerError, match="represented exactly"):
        _build(tmp_path, [_entry(tmp_path, known_cost_cny="1e999999")])


def test_malformed_batch_evidence_is_retained_as_no_go(tmp_path):
    batch_path = tmp_path / "batch.json"
    blob = b'{"phase":"pilot","records":null}\n'
    batch_path.write_bytes(blob)
    batch = {
        "batch_id": "pilot-batch-1",
        "phase": "pilot",
        "artifact": {
            "relative_path": batch_path.name,
            "sha256": hashlib.sha256(blob).hexdigest(),
        },
    }
    result = _build(tmp_path, [], [batch])
    assert result["status"] == "No-Go"
    assert result["validation_errors"]


def test_reservation_is_only_declared_budget_check(tmp_path):
    assert (
        assert_declared_reservation_fits(
            entries=[_entry(tmp_path)],
            batches=[],
            output=tmp_path / "project-ledger.json",
            allocation="pilot",
            reserve_cny=Decimal(1),
            authorization_reference="approval:pilot-2",
        )
        is None
    )
    with pytest.raises(LedgerError, match="positive"):
        assert_declared_reservation_fits(
            entries=[],
            batches=[],
            output=tmp_path / "project-ledger.json",
            allocation="pilot",
            reserve_cny=Decimal(0),
            authorization_reference="approval:pilot-2",
        )
    with pytest.raises(LedgerError, match="represented exactly"):
        assert_declared_reservation_fits(
            entries=[],
            batches=[],
            output=tmp_path / "project-ledger.json",
            allocation="pilot",
            reserve_cny=Decimal("NaN"),
            authorization_reference="approval:pilot-2",
        )


def test_reservation_refuses_missing_unknown_count(tmp_path):
    incomplete = _entry(tmp_path)
    incomplete["unknown_attempt_count"] = None
    snapshot = _build(tmp_path, [incomplete])
    assert snapshot["status"] == "No-Go"
    assert snapshot["unknown_attempt_count"] is None
    with pytest.raises(LedgerError, match="No-Go"):
        assert_declared_reservation_fits(
            entries=[incomplete],
            batches=[],
            output=tmp_path / "project-ledger.json",
            allocation="pilot",
            reserve_cny=Decimal(1),
            authorization_reference="approval:pilot-2",
        )


def test_untrusted_allocation_and_batch_phase_fail_closed(tmp_path):
    with pytest.raises(LedgerError, match="allocation"):
        _build(tmp_path, [_entry(tmp_path, allocation={"pilot": True})])
    with pytest.raises(LedgerError, match="pilot/formal"):
        _build(
            tmp_path,
            [],
            [
                {
                    "batch_id": "batch-1",
                    "phase": ["pilot"],
                    "artifact": _evidence(tmp_path),
                }
            ],
        )


def test_write_once_ledger_chain_keeps_prior_interrupted_attempt(tmp_path):
    prior = tmp_path / "ledger-1.json"
    interrupted = _entry(
        tmp_path,
        known_cost_cny=0,
        total_cost_cny=None,
        unknown_attempt_count=1,
        attempt_status="interrupted",
    )
    write_ledger(entries=[interrupted], batches=[], output=prior)
    prior_hash = hashlib.sha256(prior.read_bytes()).hexdigest()
    next_path = tmp_path / "ledger-2.json"
    result = extend_ledger(
        previous=prior,
        expected_previous_sha256=prior_hash,
        new_entries=[_entry(tmp_path, run_id="pilot-B02-1", task_id="task-2")],
        new_batches=[],
        output=next_path,
    )
    assert len(result["entries"]) == 2
    assert result["entries"][0]["attempt_status"] == "interrupted"
    assert result["previous_ledger_artifact"] == {
        "relative_path": prior.name,
        "sha256": prior_hash,
    }
    assert result["status"] == "No-Go"
    assert next_path.is_file()
    with pytest.raises(LedgerError, match="Duplicate run ID"):
        extend_ledger(
            previous=prior,
            expected_previous_sha256=prior_hash,
            new_entries=[interrupted],
            new_batches=[],
            output=tmp_path / "duplicate.json",
        )


def test_ledger_chain_rejects_tamper_and_cross_directory(tmp_path):
    prior = tmp_path / "ledger-1.json"
    write_ledger(entries=[_entry(tmp_path)], batches=[], output=prior)
    correct = hashlib.sha256(prior.read_bytes()).hexdigest()
    with pytest.raises(LedgerError, match="SHA-256 mismatch"):
        extend_ledger(
            previous=prior,
            expected_previous_sha256="0" * 64,
            new_entries=[],
            new_batches=[],
            output=tmp_path / "ledger-2.json",
        )
    with pytest.raises(LedgerError, match="share an evidence directory"):
        extend_ledger(
            previous=prior,
            expected_previous_sha256=correct,
            new_entries=[],
            new_batches=[],
            output=tmp_path / "other/ledger-2.json",
        )
