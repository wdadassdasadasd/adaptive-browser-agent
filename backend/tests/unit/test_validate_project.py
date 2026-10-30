"""Regression tests for deterministic documentation and evaluation gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from scripts import validate_project as validator
from scripts.validate_project import (
    check_archive_git_index,
    check_archive_manifest,
    check_current_materials,
    check_current_protocol,
    check_ledger,
    check_links,
    check_protocol,
    check_results,
    check_versions_and_traceability,
)
from tests.unit.test_legacy_entry_guards import historical_protocol_bytes


def test_archive_manifest_keeps_history_frozen_but_current_tasks_editable(
    tmp_path,
) -> None:
    manifest = tmp_path / "docs/archive/R0_PATH_MAP.json"
    manifest.parent.mkdir(parents=True)
    history = tmp_path / "docs/archive/history.md"
    current = tmp_path / "docs/tasks/current.md"
    current.parent.mkdir(parents=True)
    history.write_text("frozen", encoding="utf-8")
    current.write_text("initial task", encoding="utf-8")
    entries = [
        {
            "old_path": "docs/old-history.md",
            "new_path": "docs/archive/history.md",
            "kind": "historical",
            "sha256": hashlib.sha256(history.read_bytes()).hexdigest(),
        },
        {
            "old_path": "docs/old-task.md",
            "new_path": "docs/tasks/current.md",
            "kind": "current_task",
            "sha256": hashlib.sha256(current.read_bytes()).hexdigest(),
        },
    ]
    manifest.write_text(
        json.dumps({"version": 1, "entries": entries}), encoding="utf-8"
    )
    current.write_text("actual implementation evidence", encoding="utf-8")
    assert check_archive_manifest(tmp_path) == []
    history.write_text("modified history", encoding="utf-8")
    assert any("changed bytes" in error for error in check_archive_manifest(tmp_path))


def test_archive_git_index_detects_normalized_history_before_publish(
    tmp_path, monkeypatch
) -> None:
    history = tmp_path / "docs/archive/history.md"
    history.parent.mkdir(parents=True)
    history.write_bytes(b"original\r\nsecond\n")
    manifest = tmp_path / "docs/archive/R0_PATH_MAP.json"
    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "old_path": "docs/old-history.md",
                        "new_path": "docs/archive/history.md",
                        "kind": "historical",
                        "sha256": hashlib.sha256(history.read_bytes()).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.validate_project.ARCHIVED_TARGET_HASHES", {})
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "core.autocrlf=input", "add", str(history)],
        check=True,
    )
    assert check_archive_manifest(tmp_path) == []
    assert any("Git index" in error for error in check_archive_git_index(tmp_path))

    (tmp_path / ".gitattributes").write_text(
        "docs/archive/history.md -text\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", ".gitattributes"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "--renormalize", str(history)],
        check=True,
    )
    assert check_archive_git_index(tmp_path) == []


def _protocol() -> dict:
    return json.loads(historical_protocol_bytes())


def _current_bundle(tmp_path: Path) -> dict:
    """Copy current configuration only; no execution fixture or hidden text output."""
    root = Path(__file__).resolve().parents[3]
    folder = tmp_path / "docs/evaluation"
    folder.mkdir(parents=True)
    for name in (
        "CURRENT_EVAL_PROTOCOL.json",
        "DECISION_M1_PROTOCOL.json",
        "DISCOVERY_M1_CASES.json",
    ):
        (folder / name).write_bytes((root / "docs/evaluation" / name).read_bytes())
    return json.loads((folder / "CURRENT_EVAL_PROTOCOL.json").read_bytes())


def test_current_configuration_is_separate_from_historical_validator(tmp_path):
    protocol = _current_bundle(tmp_path)
    assert check_current_protocol(protocol, tmp_path) == []
    assert check_protocol(protocol)


def _current_cli_fixture(tmp_path, monkeypatch):
    _current_bundle(tmp_path)
    # These checks own unrelated repository documents, not the three raw inputs.
    for name in (
        "check_links",
        "check_versions_and_traceability",
        "check_skills",
        "check_archive_manifest",
        "check_archive_git_index",
    ):
        monkeypatch.setattr(validator, name, lambda *_args, **_kwargs: [])
    return tmp_path / "docs/evaluation"


def _rebind_current_fixture(folder):
    protocol_path = folder / "CURRENT_EVAL_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_bytes())
    digest = hashlib.sha256(
        (folder / "DISCOVERY_M1_CASES.json").read_bytes()
    ).hexdigest()
    if protocol["materials"]["sha256"] != digest:
        protocol["materials"]["sha256"] = digest
        protocol_path.write_bytes(json.dumps(protocol).encode())
    supplement_path = folder / "DECISION_M1_PROTOCOL.json"
    supplement = json.loads(supplement_path.read_bytes())
    supplement["current_protocol"]["sha256"] = hashlib.sha256(
        protocol_path.read_bytes()
    ).hexdigest()
    supplement_path.write_bytes(json.dumps(supplement).encode())


@pytest.mark.parametrize(
    "filename",
    [
        "CURRENT_EVAL_PROTOCOL.json",
        "DISCOVERY_M1_CASES.json",
        "DECISION_M1_PROTOCOL.json",
    ],
)
@pytest.mark.parametrize(
    "member",
    [
        '"CANARY":0,"CANARY":1',
        '"CANARY":{"nested":0,"nested":1}',
        '"CANARY":{"name":0,"\\u006eame":1}',
        '"CANARY":NaN',
        '"CANARY":Infinity',
        '"CANARY":-Infinity',
        '"CANARY":1e999',
        '"CANARY":-1e999',
    ],
)
def test_current_raw_json_cli_rejects_ambiguous_or_nonfinite_input(
    tmp_path, monkeypatch, capsys, filename, member
):
    folder = _current_cli_fixture(tmp_path, monkeypatch)
    target = folder / filename
    target.write_bytes(b"{" + member.encode() + b"," + target.read_bytes()[1:])
    # Rebinding the supplement itself would decode and erase duplicate members.
    if filename != "DECISION_M1_PROTOCOL.json":
        _rebind_current_fixture(folder)
    assert validator.main(["--root", str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert "CANARY" not in output.out + output.err
    assert "unreadable" in output.err


@pytest.mark.parametrize(
    "filename",
    [
        "CURRENT_EVAL_PROTOCOL.json",
        "DISCOVERY_M1_CASES.json",
        "DECISION_M1_PROTOCOL.json",
    ],
)
def test_current_raw_json_cli_accepts_finite_numbers_and_valid_nested_objects(
    tmp_path, monkeypatch, filename
):
    folder = _current_cli_fixture(tmp_path, monkeypatch)
    target = folder / filename
    target.write_bytes(
        b'{"finite_probe":{"integer":7,"decimal":1.25,"exponent":-2.5e2},'
        + target.read_bytes()[1:]
    )
    _rebind_current_fixture(folder)
    original = validator.check_current_protocol
    observed = []

    def capture(protocol, root):
        if filename == "CURRENT_EVAL_PROTOCOL.json":
            observed.append(protocol["finite_probe"])
        return original(protocol, root)

    monkeypatch.setattr(validator, "check_current_protocol", capture)
    assert validator.main(["--root", str(tmp_path)]) == 0
    if observed:
        values = observed[0]
        assert type(values["integer"]) is int
        assert type(values["decimal"]) is float
        assert type(values["exponent"]) is float
        assert values == {"integer": 7, "decimal": 1.25, "exponent": -250.0}


@pytest.mark.parametrize("case_index", range(6))
def test_current_material_case_variant_must_match_id(tmp_path, case_index):
    _current_bundle(tmp_path)
    materials = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    case = materials["agent_input"]["cases"][case_index]
    case["variant"] = "B" if case["variant"] == "A" else "A"
    assert any("variant" in error for error in check_current_materials(materials))


@pytest.mark.parametrize(
    "item", [{"scorer_only": "CANARY"}, [], None, True, 7, "", " \t"]
)
def test_current_material_output_requirements_reject_nontext_or_blank_items(
    tmp_path, item
):
    _current_bundle(tmp_path)
    materials = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    materials["agent_input"]["cases"][0]["output_requirements"] = ["valid", item]
    errors = check_current_materials(materials)
    assert any("output requirements" in error for error in errors)
    assert "CANARY" not in " ".join(errors)


@pytest.mark.parametrize("autocrlf", ["true", "input", "false"])
@pytest.mark.parametrize(
    "path",
    [
        "docs/evaluation/CURRENT_EVAL_PROTOCOL.json",
        "docs/evaluation/DISCOVERY_M1_CASES.json",
        "docs/evaluation/DECISION_M1_PROTOCOL.json",
    ],
)
def test_current_raw_hash_paths_preserve_git_filtered_bytes(autocrlf, path):
    root = Path(__file__).resolve().parents[3]
    # Read an existing LF blob through Git's actual checkout filter; no Git writes.
    blob = "1ffade6de07ebe3d1e72afb4c44b8677466eca67:docs/evaluation/CURRENT_EVAL_PROTOCOL.json"
    raw = subprocess.check_output(["git", "-C", str(root), "cat-file", "blob", blob])
    filtered = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            f"core.autocrlf={autocrlf}",
            "cat-file",
            "--filters",
            f"--path={path}",
            blob,
        ]
    )
    assert b"\r" not in raw
    assert filtered == raw


@pytest.mark.parametrize(
    "path,value",
    [
        (("formal", "expected_attempts"), 5),
        (("formal", "no_replacements"), False),
        (("timing", "active_start"), "after_reading_the_prompt"),
        (("timing", "active_minutes_per_attempt"), True),
        (("methods", "agent", "external_ai_repair_allowed"), True),
        (("quotas", "case_model", "format_repair_extra_calls"), 1),
        (("quotas", "case_model", "report_reserved_input_tokens"), 131072),
        (("quotas", "case_model", "cumulative_output_reservation_tokens"), 65536),
        (("budget", "planned_total_cny"), "300.00"),
        (("authorization", "paid_execution"), True),
        (("budget", "price_basis", "model_input_uncached_per_million_cny"), "0.00"),
    ],
)
def test_current_validator_rejects_protocol_boundary_drift(tmp_path, path, value):
    protocol = _current_bundle(tmp_path)
    target = protocol
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert check_current_protocol(protocol, tmp_path)


@pytest.mark.parametrize("field", ["quotas", "materials", "timing", "authorization"])
def test_current_validator_fails_closed_on_bad_section_types(tmp_path, field):
    protocol = _current_bundle(tmp_path)
    protocol[field] = []
    assert check_current_protocol(protocol, tmp_path)


def test_current_materials_reject_scorer_input_leak_duplicate_and_incomplete_coverage(
    tmp_path,
):
    _current_bundle(tmp_path)
    materials = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    assert check_current_materials(materials) == []
    changed = deepcopy(materials)
    changed["agent_input"]["cases"][0]["scorer_only"] = {"winner": "leaked"}
    assert check_current_materials(changed)
    changed = deepcopy(materials)
    changed["agent_input"]["cases"][1]["case_id"] = changed["agent_input"]["cases"][0][
        "case_id"
    ]
    assert check_current_materials(changed)
    changed = deepcopy(materials)
    first = next(iter(changed["scorer_only"]["case_rubrics"].values()))
    first["mandatory_hard_condition_ids"].pop()
    assert check_current_materials(changed)
    changed = deepcopy(materials)
    changed["agent_input"]["cases"][0]["case_id"] = []
    assert check_current_materials(changed)
    changed = deepcopy(materials)
    changed["agent_input"]["allowlist_paths"].append("#/scorer_only")
    assert check_current_materials(changed)


def test_current_material_identity_is_not_bypassed_by_valid_structure(tmp_path):
    protocol = _current_bundle(tmp_path)
    material = tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json"
    material.write_bytes(material.read_bytes() + b"\n")
    assert any(
        "SHA-256 mismatch" in error
        for error in check_current_protocol(protocol, tmp_path)
    )


@pytest.mark.parametrize("index", [True, 0, 2, 4, "1"])
def test_clarification_units_require_unique_one_based_question_mapping(tmp_path, index):
    _current_bundle(tmp_path)
    materials = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    first = next(iter(materials["controller_only"]["clarification_cards"].values()))
    first["answer_units"][0]["question_group"] = index
    assert any("question" in error for error in check_current_materials(materials))


def test_pair_equivalence_cannot_silently_drop_a_hard_condition_and_its_rubric(
    tmp_path,
):
    _current_bundle(tmp_path)
    materials = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    case_id = next(iter(materials["controller_only"]["clarification_cards"]))
    materials["controller_only"]["clarification_cards"][case_id]["accepted_conditions"][
        "hard_conditions"
    ].pop()
    materials["scorer_only"]["case_rubrics"][case_id][
        "mandatory_hard_condition_ids"
    ].pop()
    assert any(
        "hard conditions" in error for error in check_current_materials(materials)
    )


@pytest.mark.parametrize(
    "group,field",
    [
        ("timing", "active_intervals_with_start_end_kind_and_actor"),
        (
            "artifacts",
            "ordered_human_revisions_with_parent_ref_sha256_edit_time_and_active_interval_refs",
        ),
        ("audit", "reviewed_report_sha256"),
        ("outcomes", "safety_authority_unknown_stop_state"),
        ("cost", "known_unknown_inflight_reservations"),
    ],
)
def test_attempt_evidence_contract_cannot_drop_auditable_records(
    tmp_path, group, field
):
    protocol = _current_bundle(tmp_path)
    protocol["attempt_record_contract"]["required_fields"][group].remove(field)
    assert any(
        "attempt_record_contract" in error
        for error in check_current_protocol(protocol, tmp_path)
    )


def test_attempt_evidence_contract_rejects_overlapping_time_and_missing_binding(
    tmp_path,
):
    protocol = _current_bundle(tmp_path)
    protocol["attempt_record_contract"]["active_intervals"] = (
        "overlapping intervals allowed"
    )
    protocol["attempt_record_contract"]["audit_binding"] = (
        "the latest report is close enough"
    )
    errors = check_current_protocol(protocol, tmp_path)
    assert any("active_intervals" in error for error in errors)
    assert any("audit_binding" in error for error in errors)


def _refresh_bundle(record: dict, tmp_path: Path) -> None:
    trace = record["trace_artifact"]
    bundle = {
        "task_id": record["task_id"],
        "run_id": record["run_id"],
        "status": record["status"],
        "stop_reason": record["stop_reason"],
        "facts": record["facts"],
        "raw_record_sha256": record["raw_record_sha256"],
        "trace_sha256": trace["sha256"],
        "report_sha256": record["report_artifact"]["sha256"]
        if record["report_artifact"]
        else None,
        "cost": record["cost"],
        "comparison": record["comparison"],
        "manual_source_review": record["manual_source_review"],
    }
    path = tmp_path / record["review_bundle_artifact"]["relative_path"]
    path.write_text(json.dumps(bundle), encoding="utf-8")
    record["review_bundle_artifact"]["sha256"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _record(protocol: dict, case: dict, trial: int, tmp_path: Path) -> dict:
    fields = case["required_fields"]
    stem = f"{case['id']}-{trial}"
    raw_path = tmp_path / f"{stem}.json"
    trace_path = tmp_path / f"{stem}-trace.json"
    bundle_path = tmp_path / f"{stem}-review.json"
    report_path = tmp_path / f"{stem}-report.json"
    raw_path.write_text(json.dumps({"run_id": f"run-{stem}"}), encoding="utf-8")
    trace_path.write_text(
        json.dumps({"calls": [{"kind": "synthetic"}]}), encoding="utf-8"
    )
    report_path.write_text(
        json.dumps({"task_id": f"task-{stem}", "fact_ids": ["fact-1"]}),
        encoding="utf-8",
    )
    report_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest()
    record = {
        "protocol_version": protocol["protocol_version"],
        "phase": "formal",
        "case_id": case["id"],
        "trial_index": trial,
        "task_id": f"task-{case['id']}-{trial}",
        "run_id": f"run-{case['id']}-{trial}",
        "code_revision": "synthetic-revision",
        "prompt_sha256": hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest(),
        "started_at": "2026-10-18T00:00:00Z",
        "ended_at": "2026-10-18T00:01:00Z",
        "status": "completed",
        "completion_level": "full",
        "facts": [
            {
                "fact_id": "fact-1",
                "subject": "synthetic subject",
                "claim": "synthetic claim",
                "official_source_url": "https://example.org/official",
                "official_identity_basis": "synthetic fixture only",
                "evidence_excerpt": "synthetic excerpt",
                "evidence_locator": "synthetic-page-section",
                "retrieved_at": "2026-10-18T00:00:00Z",
                "machine_admission_status": "admitted",
                "human_official_review_status": "verified",
                "reviewer_id": "synthetic-reviewer",
                "source_checked_at": "2026-10-18T00:01:00Z",
                "contradiction_note": "none",
            }
        ],
        "call_attempts": [
            {
                "attempt_id": f"call-{stem}",
                "kind": "model",
                "billable": True,
                "started_at": "2026-10-18T00:00:00Z",
                "ended_at": "2026-10-18T00:00:30Z",
                "outcome": "completed",
                "reported_prompt_tokens": 1,
                "reported_completion_tokens": 1,
                "known_cost_cny": 1,
            }
        ],
        "field_reviews": {
            field: {
                "value": "synthetic value",
                "fact_ids": ["fact-1"],
                "official_source_url": "https://example.org/official",
                "verified_by_human": True,
                "source_checked_at": "2026-10-18T00:01:00Z",
                "reviewer_id": "synthetic-reviewer",
                "evidence_locator": "synthetic-page-section",
                "contradiction_note": "none",
            }
            for field in fields
        },
        "field_coverage": {
            "verified_count": len(fields),
            "required_count": len(fields),
        },
        "claims": [
            {
                "text": "synthetic claim",
                "fact_ids": ["fact-1"],
                "official_source_urls": ["https://example.org/official"],
                "verified_by_human": True,
                "source_checked_at": "2026-10-18T00:01:00Z",
                "reviewer_id": "synthetic-reviewer",
                "evidence_locator": "synthetic-page-section",
                "contradiction_note": "none",
            }
        ],
        "recommendation_review": {
            "text": "synthetic conditional recommendation",
            "use_conditions": ["synthetic use case"],
            "supporting_fact_ids": ["fact-1"],
            "official_source_urls": ["https://example.org/official"],
            "tradeoffs_or_unknowns": "synthetic limitation",
            "rationale_checked_by_human": True,
            "source_checked_at": "2026-10-18T00:01:00Z",
        },
        "official_source_review": True,
        "chain_checks": {"ui": True, "api": True, "persistence": True, "sse": True},
        "persistence_backend": "postgresql",
        "manual_source_review": {
            "reviewer_id": "synthetic-reviewer",
            "reviewed_at": "2026-10-18T00:01:00Z",
            "evidence_note": "synthetic fixture only",
            "report_sha256": report_sha256,
            "second_review_status": "same_reviewer_later",
            "second_reviewer_id": "synthetic-reviewer",
            "second_reviewed_at": "2026-10-18T00:02:00Z",
        },
        "community_supplements": [
            {
                "text": "synthetic community note",
                "source_url": "https://example.net/community",
                "source_role": "community_supplement",
                "verified_by_human": True,
                "source_checked_at": "2026-10-18T00:01:00Z",
                "limitation": "synthetic, not an official fact",
            }
        ]
        if case["id"] == "O03"
        else [],
        "access_checks": {
            "owner_visible": True,
            "other_hidden": True,
            "other_cancel_denied": True,
        },
        "stop_reason": None,
        "usage": {
            "reported_prompt_tokens": 1,
            "reported_completion_tokens": 1,
            "known_lower_bound_tokens": 2,
            "unknown_attempt_count": 0,
        },
        "wall_clock_seconds": 60,
        "duplicate_urls": 0,
        "raw_record_path": raw_path.name,
        "raw_record_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "report_artifact": {
            "relative_path": report_path.name,
            "sha256": report_sha256,
        },
        "trace_artifact": {
            "relative_path": trace_path.name,
            "sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        },
        "review_bundle_artifact": {
            "relative_path": bundle_path.name,
            "sha256": "",
        },
        "cost": {
            "currency": "CNY",
            "known_cost_cny": 1,
            "total_cost_cny": 1,
            "unknown_attempt_count": 0,
            "pricing_basis": "synthetic-pricing-fixture",
            "price_checked_at": "2026-10-18T00:01:00Z",
        },
        "comparison": {
            "cohort_id": "synthetic-cohort",
            "environment_fingerprint": "synthetic-env",
            "upstream_browser_fingerprint": "synthetic-browser",
            "dependency_lock_sha256": "synthetic-lock",
            "model_id": "synthetic-model",
            "budget_fingerprint": "synthetic-budget",
            "scoring_revision": "synthetic-scoring",
            "source_window": "synthetic-window",
            "source_drift": "none",
            "budget_parity": "matched",
        },
    }
    _refresh_bundle(record, tmp_path)
    return record


def _batch(protocol: dict, tmp_path: Path) -> dict:
    return {
        "protocol_version": protocol["protocol_version"],
        "phase": "formal",
        "records": [
            _record(protocol, case, trial, tmp_path)
            for case in protocol["cases"]
            for trial in range(1, 4 if case["id"].startswith("B") else 2)
        ],
    }


def _ledger(protocol: dict, tmp_path: Path) -> dict:
    batches = []
    entries = []
    for phase in ("pilot", "formal"):
        folder = tmp_path / phase
        folder.mkdir(parents=True)
        batch = (
            _batch(protocol, folder)
            if phase == "formal"
            else {
                "protocol_version": protocol["protocol_version"],
                "phase": "pilot",
                "records": [
                    _record(protocol, case, 1, folder) for case in protocol["cases"][:3]
                ],
            }
        )
        if phase == "pilot":
            for record in batch["records"]:
                record["phase"] = "pilot"
                record["run_id"] = "pilot-" + record["run_id"]
                record["task_id"] = "pilot-" + record["task_id"]
                record["access_checks"] = {
                    "owner_visible": None,
                    "other_hidden": None,
                    "other_cancel_denied": None,
                }
                _refresh_bundle(record, folder)
        batch_path = folder / "results.json"
        batch_path.write_text(json.dumps(batch), encoding="utf-8")
        batches.append(
            {
                "batch_id": phase,
                "phase": phase,
                "artifact": {
                    "relative_path": f"{phase}/results.json",
                    "sha256": hashlib.sha256(batch_path.read_bytes()).hexdigest(),
                },
            }
        )
        for record in batch["records"]:
            entries.append(
                {
                    "run_id": record["run_id"],
                    "task_id": record["task_id"],
                    "allocation": phase,
                    "batch_id": phase,
                    "known_cost_cny": record["cost"]["known_cost_cny"],
                    "total_cost_cny": record["cost"]["total_cost_cny"],
                    "unknown_attempt_count": record["cost"]["unknown_attempt_count"],
                    "evidence_artifact": {
                        "relative_path": f"{phase}/{record['raw_record_path']}",
                        "sha256": record["raw_record_sha256"],
                    },
                    "authorization_reference": "synthetic-fixture",
                }
            )
    return {
        "protocol_version": protocol["protocol_version"],
        "batches": batches,
        "entries": entries,
    }


def test_cost_reconciles_call_attempts_and_task_total(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["call_attempts"][0]["known_cost_cny"] = 500
    assert any(
        "invalid cost or unknown-cost semantics" in error
        for error in check_results(protocol, batch, tmp_path)
    )
    first["call_attempts"][0]["known_cost_cny"] = 1
    first["cost"]["total_cost_cny"] = 2
    assert any(
        "invalid cost or unknown-cost semantics" in error
        for error in check_results(protocol, batch, tmp_path)
    )


def test_duplicate_call_and_unreported_usage_are_rejected(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["call_attempts"].append(first["call_attempts"][0].copy())
    first["usage"]["reported_prompt_tokens"] = 0
    findings = check_results(protocol, batch, tmp_path)
    assert any("duplicate attempt ID" in item for item in findings)
    assert any("usage differs from model call attempts" in item for item in findings)


def test_unlisted_cost_without_calls_is_rejected(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["call_attempts"] = []
    first["usage"].update(
        reported_prompt_tokens=0,
        reported_completion_tokens=0,
        known_lower_bound_tokens=0,
    )
    first["cost"].update(known_cost_cny=None, total_cost_cny=99)
    assert any(
        "invalid cost or unknown-cost semantics" in item
        for item in check_results(protocol, batch, tmp_path)
    )


def test_pilot_access_can_be_unverified_but_formal_cannot(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = {
        "protocol_version": protocol["protocol_version"],
        "phase": "pilot",
        "records": [
            _record(protocol, case, 1, tmp_path) for case in protocol["cases"][:3]
        ],
    }
    for record in batch["records"]:
        record["phase"] = "pilot"
        record["access_checks"] = dict.fromkeys(record["access_checks"], None)
    assert not check_results(protocol, batch, tmp_path)
    batch["phase"] = "formal"
    batch["records"][0]["phase"] = "formal"
    assert any(
        "invalid access_checks for formal" in error
        for error in check_results(protocol, batch, tmp_path)
    )


def test_manual_review_is_bound_to_report_bytes(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["manual_source_review"]["report_sha256"] = "0" * 64
    assert any(
        "invalid manual_source_review" in error
        for error in check_results(protocol, batch, tmp_path)
    )
    _refresh_bundle(first, tmp_path)
    first["manual_source_review"]["report_sha256"] = first["report_artifact"]["sha256"]
    path = tmp_path / first["report_artifact"]["relative_path"]
    path.write_text('{"changed": true}', encoding="utf-8")
    assert any(
        "report: artifact SHA-256 mismatch" in error
        for error in check_results(protocol, batch, tmp_path)
    )


def test_project_ledger_reconciles_batches_and_budget(tmp_path: Path) -> None:
    protocol = _protocol()
    ledger = _ledger(protocol, tmp_path)
    assert not check_ledger(protocol, ledger, tmp_path)
    ledger["entries"][0]["total_cost_cny"] = 200
    findings = check_ledger(protocol, ledger, tmp_path)
    assert any("batch attempt cost or identity differs" in item for item in findings)
    assert any("pilot allocation exceeds" in item for item in findings)


def test_project_ledger_keeps_interrupted_and_duplicate_runs(tmp_path: Path) -> None:
    protocol = _protocol()
    ledger = _ledger(protocol, tmp_path)
    interrupted_path = tmp_path / "interrupted.json"
    interrupted_path.write_text('{"run_id": "interrupted"}', encoding="utf-8")
    extra = {
        "run_id": "interrupted",
        "task_id": "interrupted-task",
        "allocation": "diagnostic",
        "batch_id": None,
        "known_cost_cny": None,
        "total_cost_cny": None,
        "unknown_attempt_count": 1,
        "evidence_artifact": {
            "relative_path": interrupted_path.name,
            "sha256": hashlib.sha256(interrupted_path.read_bytes()).hexdigest(),
        },
        "authorization_reference": "synthetic-fixture",
    }
    ledger["entries"].append(extra)
    findings = check_ledger(protocol, ledger, tmp_path)
    assert any("cost unknown" in item for item in findings)
    ledger["entries"].append(extra.copy())
    assert any(
        "duplicate or missing run ID" in item
        for item in check_ledger(protocol, ledger, tmp_path)
    )


def test_project_ledger_rejects_omitted_batch_attempt_and_total_overspend(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    ledger = _ledger(protocol, tmp_path)
    ledger["entries"].pop()
    assert any(
        "omits 1 retained batch" in item
        for item in check_ledger(protocol, ledger, tmp_path)
    )
    ledger = _ledger(protocol, tmp_path / "overspend")
    for entry in ledger["entries"]:
        entry["known_cost_cny"] = 20
        entry["total_cost_cny"] = 20
    findings = check_ledger(protocol, ledger, tmp_path / "overspend")
    assert any("project live-run budget exceeds 299" in item for item in findings)


def test_project_ledger_requires_batch_identity_for_retained_attempt(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    ledger = _ledger(protocol, tmp_path)
    ledger["entries"][0]["batch_id"] = None
    assert any(
        "retained batch attempt needs its batch ID" in item
        for item in check_ledger(protocol, ledger, tmp_path)
    )


def test_link_gate_rejects_missing_local_target(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("[missing](nested/file.md)\n", encoding="utf-8")
    assert "broken local link" in " ".join(check_links(tmp_path, ("doc.md",)))
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/file.md").write_text("# exists\n", encoding="utf-8")
    assert not check_links(tmp_path, ("doc.md",))


def test_current_links_cannot_pass_through_archive_mapping(tmp_path: Path) -> None:
    archive = tmp_path / "docs/archive"
    archive.mkdir(parents=True)
    (archive / "evidence.md").write_text("# evidence\n", encoding="utf-8")
    frozen = archive / "frozen.md"
    frozen.write_text("[evidence](../evidence.md)\n", encoding="utf-8")
    manifest = archive / "R0_PATH_MAP.json"
    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "old_path": "docs/evidence.md",
                        "new_path": "docs/archive/evidence.md",
                        "kind": "historical",
                        "sha256": hashlib.sha256(
                            (archive / "evidence.md").read_bytes()
                        ).hexdigest(),
                    },
                    {
                        "old_path": "docs/legacy/frozen.md",
                        "new_path": "docs/archive/frozen.md",
                        "kind": "historical",
                        "sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    current = tmp_path / "docs/current.md"
    current.write_text("[evidence](evidence.md)\n", encoding="utf-8")

    assert "broken local link" in " ".join(check_links(tmp_path, ("docs/current.md",)))
    assert not check_links(tmp_path, ("docs/archive/frozen.md",))


def _copy_traceability_docs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    for relative in (
        "SPEC.md",
        "docs/archive/target-0.4/SPEC_0.4.md",
        "docs/archive/target-0.4/PLANS_0.4.md",
        "PLANS.md",
        "AGENTS.md",
        "docs/archive/design-0.3/00_DESIGN_INDEX.md",
        "docs/archive/target-2026-10-18/SPEC.md",
        "docs/archive/target-2026-10-18/PLANS.md",
        "docs/evaluation/archive/CURRENT_EVAL_PROTOCOL_current-1.json",
        "docs/evaluation/archive/CURRENT_EVAL_PROTOCOL_current-2.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(root),
                    "show",
                    f"1ffade6de07ebe3d1e72afb4c44b8677466eca67:{relative}",
                ]
            )
            if relative in {"SPEC.md", "PLANS.md", "AGENTS.md"}
            else (root / relative).read_bytes()
        )


def test_traceability_gate_rejects_broken_task_acceptance_mapping(
    tmp_path: Path,
) -> None:
    _copy_traceability_docs(tmp_path)
    plan = tmp_path / "PLANS.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace("FR-001", "FR-999"),
        encoding="utf-8",
    )
    findings = check_versions_and_traceability(tmp_path)
    assert any("no stage row maps FR-001 to AC-001" in item for item in findings)


def test_traceability_gate_requires_new_requirements_on_their_stages(
    tmp_path: Path,
) -> None:
    _copy_traceability_docs(tmp_path)
    spec = tmp_path / "SPEC.md"
    plan = tmp_path / "PLANS.md"
    mappings = (
        ("FR-011", "AC-011", "P-03"),
        ("FR-012", "AC-012", "P-03"),
        ("NFR-010", "AC-N10", "P-02"),
    )
    spec_text = spec.read_text(encoding="utf-8")
    for requirement, ac, stage in mappings:
        if not any(
            line.startswith(f"| {requirement} |") for line in spec_text.splitlines()
        ):
            spec_text += f"\n| {requirement} | test capability | {stage} | {ac} |"
    spec.write_text(spec_text, encoding="utf-8")
    plan_text = plan.read_text(encoding="utf-8")
    plan_text += "".join(
        f"\n| {stage} | {requirement} | {ac} |" for requirement, ac, stage in mappings
    )
    plan.write_text(plan_text, encoding="utf-8")
    assert not check_versions_and_traceability(tmp_path)

    spec.write_text(
        "\n".join(
            line for line in spec_text.splitlines() if not line.startswith("| FR-012 |")
        ),
        encoding="utf-8",
    )
    assert "SPEC: missing mapping row FR-012" in check_versions_and_traceability(
        tmp_path
    )

    spec.write_text(spec_text, encoding="utf-8")
    plan.write_text(
        plan_text.replace("NFR-010", "NFR-999") + "\n| P-03 | NFR-010 | AC-N10 |",
        encoding="utf-8",
    )
    assert "PLANS: stage P-02 must map NFR-010 to AC-N10" in (
        check_versions_and_traceability(tmp_path)
    )


def test_protocol_rejects_aggregate_gate_and_changed_b_prompt() -> None:
    protocol = _protocol()
    protocol["formal"]["aggregate_field_release_threshold"] = 68
    protocol["cases"][0]["prompt"] = "changed after preregistration"
    historical = (
        Path(__file__).resolve().parents[3] / "docs/benchmark/BENCHMARK_PROTOCOL.md"
    ).read_text(encoding="utf-8")
    findings = check_protocol(protocol, historical)
    assert any("aggregate_field_release_threshold" in item for item in findings)
    assert any("B01: prompt differs" in item for item in findings)


def test_protocol_preserves_frozen_fields_and_o_registration() -> None:
    protocol = _protocol()
    frozen = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "docs/evaluation/G2_EVAL_PROTOCOL.json"
        ).read_text(encoding="utf-8")
    )["cases"]
    assert not check_protocol(protocol, frozen_cases=frozen)
    protocol["cases"][3]["required_fields"][0] = "changed_g_field"
    protocol["cases"][8]["community_supplement_required"] = False
    findings = check_protocol(protocol, frozen_cases=frozen)
    assert any("G01: frozen prompt or fields changed" in item for item in findings)
    assert any(
        "O03: community supplement requirement missing" in item for item in findings
    )


def test_protocol_requires_cost_and_descriptive_comparison_contract() -> None:
    protocol = _protocol()
    protocol["result_record_contract"]["cost_required_fields"].remove("total_cost_cny")
    protocol["comparison_policy"]["interpretation"] = "causal_improvement"
    findings = check_protocol(protocol)
    assert any(
        "cost_required_fields missing required evidence" in item for item in findings
    )
    assert any("comparison policy" in item for item in findings)


def test_formal_gate_counts_failures_and_requires_per_attempt_sources(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    assert not check_results(protocol, batch, tmp_path)
    for record in batch["records"]:
        if record["case_id"] == "B01" and record["trial_index"] in (1, 2):
            record["status"] = "failed"
            record["completion_level"] = "none"
            record["field_reviews"]["project_1_name"]["verified_by_human"] = False
            record["field_coverage"]["verified_count"] -= 1
    findings = check_results(protocol, batch, tmp_path)
    assert any("No-Go: B01 has 1/3" in item for item in findings)
    assert not any("full result lacks verified fields" in item for item in findings)


def test_formal_gate_rejects_missing_trial_and_unsupported_full_report(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    batch["records"].pop()
    batch["records"][0]["field_reviews"]["project_1_name"]["official_source_url"] = None
    findings = check_results(protocol, batch, tmp_path)
    assert any(
        "formal batch must retain all 15 distinct attempts" in item for item in findings
    )
    assert any("full result lacks verified fields" in item for item in findings)


def test_formal_gate_rejects_unverified_recommendation_and_owner_leak(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["recommendation_review"]["rationale_checked_by_human"] = False
    first["access_checks"]["other_hidden"] = False
    findings = check_results(protocol, batch, tmp_path)
    assert any("full result needs verified recommendation" in item for item in findings)
    assert any("full result needs owner isolation checks" in item for item in findings)


def test_o03_requires_labeled_community_feedback_and_o_set_three_successes(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    o03 = next(record for record in batch["records"] if record["case_id"] == "O03")
    o03["community_supplements"] = []
    findings = check_results(protocol, batch, tmp_path)
    assert any(
        "O03 full result needs labeled community feedback" in item for item in findings
    )
    assert any("No-Go: O set has 2/3" in item for item in findings)


def test_pilot_requires_three_retained_diagnostics_without_formal_gate(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = {
        "protocol_version": protocol["protocol_version"],
        "phase": "pilot",
        "records": [
            _record(protocol, case, 1, tmp_path) for case in protocol["cases"][:3]
        ],
    }
    for record in batch["records"]:
        record["phase"] = "pilot"
        record["status"] = "failed"
        record["completion_level"] = "none"
        _refresh_bundle(record, tmp_path)
    assert not check_results(protocol, batch, tmp_path)
    batch["records"].pop()
    assert any(
        "pilot batch must retain all 3" in item
        for item in check_results(protocol, batch, tmp_path)
    )


def test_pilot_unknown_or_over_budget_cost_stops_cohort(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = {
        "protocol_version": protocol["protocol_version"],
        "phase": "pilot",
        "records": [
            _record(protocol, case, 1, tmp_path) for case in protocol["cases"][:3]
        ],
    }
    for record in batch["records"]:
        record["phase"] = "pilot"
    first = batch["records"][0]
    first["call_attempts"][0]["known_cost_cny"] = None
    first["cost"].update(unknown_attempt_count=1, total_cost_cny=None)
    _refresh_bundle(first, tmp_path)
    findings = check_results(protocol, batch, tmp_path)
    assert any("pilot cost is incomplete or unknown" in item for item in findings)
    first["call_attempts"][0]["known_cost_cny"] = 48
    first["cost"].update(known_cost_cny=48, unknown_attempt_count=0, total_cost_cny=48)
    _refresh_bundle(first, tmp_path)
    findings = check_results(protocol, batch, tmp_path)
    assert any("pilot exceeds 49 CNY allocation" in item for item in findings)


def test_result_gate_checks_real_trace_hash_and_prompt(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    (tmp_path / first["trace_artifact"]["relative_path"]).write_text(
        '{"calls": []}', encoding="utf-8"
    )
    first["prompt_sha256"] = "0" * 64
    findings = check_results(protocol, batch, tmp_path)
    assert any("trace: artifact SHA-256 mismatch" in item for item in findings)
    assert any("prompt SHA-256 differs" in item for item in findings)


def test_result_gate_rejects_unknown_formal_cost_and_unreviewed_claim(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["cost"]["total_cost_cny"] = None
    first["cost"]["unknown_attempt_count"] = 1
    first["claims"][0]["contradiction_note"] = "source disagrees"
    findings = check_results(protocol, batch, tmp_path)
    assert any("formal batch cost is incomplete" in item for item in findings)
    assert any(
        "full result needs verified material claims" in item for item in findings
    )


def test_result_gate_rejects_artifact_path_escape(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    batch["records"][0]["raw_record_path"] = "../outside.json"
    findings = check_results(protocol, batch, tmp_path)
    assert any("raw record: artifact missing or outside" in item for item in findings)


def test_full_result_requires_linked_admitted_fact_and_second_review(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["field_reviews"]["project_1_name"]["fact_ids"] = ["invented-fact"]
    first["manual_source_review"].update(
        second_review_status="not_done",
        second_reviewer_id=None,
        second_reviewed_at=None,
    )
    findings = check_results(protocol, batch, tmp_path)
    assert any(
        "full field project_1_name lacks verified fact IDs" in item for item in findings
    )
    assert any(
        "full or conflicting attempt needs later second review" in item
        for item in findings
    )


def test_conflicted_failure_also_requires_later_second_review(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    first["status"] = "failed"
    first["completion_level"] = "none"
    first["claims"][0]["contradiction_note"] = "official page disagrees"
    first["manual_source_review"].update(
        second_review_status="not_done",
        second_reviewer_id=None,
        second_reviewed_at=None,
    )
    findings = check_results(protocol, batch, tmp_path)
    assert any(
        "full or conflicting attempt needs later second review" in item
        for item in findings
    )


def test_pilot_rejects_mixed_model_or_scoring_revision(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = {
        "protocol_version": protocol["protocol_version"],
        "phase": "pilot",
        "records": [
            _record(protocol, case, 1, tmp_path) for case in protocol["cases"][:3]
        ],
    }
    for record in batch["records"]:
        record["phase"] = "pilot"
    batch["records"][1]["comparison"]["model_id"] = "different-model"
    findings = check_results(protocol, batch, tmp_path)
    assert any("pilot batch mixes code, model, budget" in item for item in findings)


def test_unknown_billable_call_keeps_cost_unknown(tmp_path: Path) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    call = first["call_attempts"][0]
    call.update(
        outcome="unknown_outcome",
        ended_at=None,
        reported_prompt_tokens=None,
        reported_completion_tokens=None,
        known_cost_cny=None,
    )
    first["usage"]["unknown_attempt_count"] = 1
    first["cost"].update(unknown_attempt_count=1, total_cost_cny=None)
    findings = check_results(protocol, batch, tmp_path)
    assert any("formal batch cost is incomplete" in item for item in findings)
    first["cost"]["total_cost_cny"] = 0
    findings = check_results(protocol, batch, tmp_path)
    assert any("invalid cost or unknown-cost semantics" in item for item in findings)


def test_review_bundle_content_must_match_attempt_even_with_valid_hash(
    tmp_path: Path,
) -> None:
    protocol = _protocol()
    batch = _batch(protocol, tmp_path)
    first = batch["records"][0]
    artifact = first["review_bundle_artifact"]
    path = tmp_path / artifact["relative_path"]
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["facts"] = []
    path.write_text(json.dumps(bundle), encoding="utf-8")
    artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    findings = check_results(protocol, batch, tmp_path)
    assert any("review bundle differs from attempt record" in item for item in findings)
