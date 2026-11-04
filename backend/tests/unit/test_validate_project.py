"""Regression tests for deterministic documentation and evaluation gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from decimal import Decimal
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


@pytest.mark.parametrize("version", ["review-m1-1", "discovery-m1-1", "current-3"])
def test_previous_protocol_is_not_current_drafting_authority(tmp_path, version):
    protocol = _current_bundle(tmp_path)
    protocol["protocol_version"] = version
    assert any(
        "protocol_version" in e for e in check_current_protocol(protocol, tmp_path)
    )


@pytest.mark.parametrize(
    "path,value",
    [
        (("documents", "versions_per_case"), 17),
        (("documents", "first_full_chain_reserve_bytes"), 81920),
        (("local_materials", "items_per_case_cumulative"), 33),
        (("local_materials", "raw_item_bytes"), 2097152),
        (("quotas", "case_model", "hidden_judge_extra_calls"), 1),
        (("quotas", "case_model", "compile_reserve_borrowable"), True),
        (
            (
                "quotas",
                "case_model",
                "mode_obligations",
                "requirements_to_solution",
                "first_artifacts",
            ),
            3,
        ),
    ],
)
def test_drafting_policy_rejects_scope_and_reservation_expansion(tmp_path, path, value):
    protocol = _current_bundle(tmp_path)
    cursor = protocol
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    assert check_current_protocol(protocol, tmp_path)


def test_draft_arithmetic_recomputed_not_just_declared(tmp_path):
    protocol = _current_bundle(tmp_path)
    assert validator._check_draft_reservations(protocol) == []
    protocol["quotas"]["case_model"]["stages"][-1]["normal_obligations"] = 5
    assert validator._check_draft_reservations(protocol)


@pytest.mark.parametrize("domain", ["requirements", "consistency", "exploration"])
def test_materials_cannot_claim_wrong_mode_coverage(domain):
    package = json.loads(json.dumps(_review_package("inputs")))
    case = next(c for c in package["cases"] if c["domain_id"] == domain)
    case["workflow"]["mode"] = "requirements_only"
    assert validator.check_review_material_package(package, "inputs")


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
def test_current_raw_json_parser_accepts_finite_values_but_freeze_rejects_new_fields(
    tmp_path, monkeypatch, filename
):
    folder = _current_cli_fixture(tmp_path, monkeypatch)
    target = folder / filename
    target.write_bytes(
        b'{"finite_probe":{"integer":7,"decimal":1.25,"exponent":-2.5e2},'
        + target.read_bytes()[1:]
    )
    _rebind_current_fixture(folder)
    decoded = validator._load_current_json(target.read_bytes())["finite_probe"]
    assert decoded == {"integer": 7, "decimal": 1.25, "exponent": -250.0}
    assert type(decoded["integer"]) is int and type(decoded["decimal"]) is float
    assert type(decoded["exponent"]) is float
    # Valid syntax cannot authorize a new current-policy field or raw byte change.
    assert validator.main(["--root", str(tmp_path)]) == 1


@pytest.mark.parametrize("case_index", range(6))
def test_current_material_case_variant_must_match_id(tmp_path, case_index):
    package = _review_package("inputs")
    case = package["cases"][case_index]
    case["variant"] = "B" if case["variant"] == "A" else "A"
    assert any(
        "variant" in error
        for error in validator.check_review_material_package(package, "inputs")
    )


@pytest.mark.parametrize(
    "item", [{"scorer_only": "CANARY"}, [], None, True, 7, "", " \t"]
)
def test_current_material_output_requirements_reject_nontext_or_blank_items(
    tmp_path, item
):
    package = _review_package("inputs")
    package["cases"][0]["output_requirements"] = ["valid", item]
    errors = validator.check_review_material_package(package, "inputs")
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
        (
            (
                "quotas",
                "case_model",
                "first_attempt_reservation",
                "input_tokens_per_artifact",
            ),
            65536,
        ),
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
    protocol = _current_bundle(tmp_path)
    index = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    assert check_current_materials(index) == []
    changed = deepcopy(index)
    changed["scorer_only"] = {"answer": "CANARY"}
    assert check_current_materials(changed)
    changed = deepcopy(index)
    changed["pairs"][1]["case_ids"][0] = changed["pairs"][0]["case_ids"][0]
    assert check_current_materials(changed)
    assert check_current_protocol(protocol, tmp_path) == []
    for role in validator.MATERIAL_ROLES:
        assert (
            validator.check_review_material_package(_review_package(role), role) == []
        )
    inputs = _review_package("inputs")
    inputs["cases"][0]["scorer_only"] = {"hidden": "CANARY"}
    assert validator.check_review_material_package(inputs, "inputs")
    scorer = _review_package("scorer")
    scorer["case_rubrics"]["REQ-A"]["critical_items"] = []
    assert validator.check_review_material_package(scorer, "scorer")


def test_current_material_identity_is_not_bypassed_by_valid_structure(tmp_path):
    protocol = _current_bundle(tmp_path)
    path = tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json"
    path.write_bytes(path.read_bytes() + b" ")
    assert any("SHA-256" in e for e in check_current_protocol(protocol, tmp_path))


@pytest.mark.parametrize("index", [True, 0, 2, 4, "1"])
def test_clarification_units_require_unique_one_based_question_mapping(tmp_path, index):
    package = _review_package("controller")
    package["clarification_cards"]["REQ-A"]["answer_units"][0]["question_group"] = index
    assert validator.check_review_material_package(package, "controller")


def test_pair_equivalence_cannot_silently_drop_a_hard_condition_and_its_rubric(
    tmp_path,
):
    package = _review_package("scorer")
    package["equivalence"].pop("requirements")
    assert validator.check_review_material_package(package, "scorer")


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


def _review_package(role: str) -> dict:
    """Synthetic isolated fixtures, never formal prompts or real source evidence."""
    ids = list(validator.REVIEW_CASE_IDS)
    base = {
        "schema_version": f"draft-m1-{role}-1",
        "protocol_version": "draft-m1-3",
        "role": role,
        "author_context": "synthetic-author",
    }
    if role == "inputs":
        base["cases"] = [
            {
                "case_id": cid,
                "domain_id": domain,
                "variant": cid[-1],
                "prompt": "SYNTHETIC fixture only",
                "output_requirements": ["synthetic output"],
                "workflow": validator.FORMAL_WORKFLOWS[domain],
            }
            for domain, pair in validator.REVIEW_CASE_PAIRS.items()
            for cid in pair
        ]
    elif role == "controller":
        base["clarification_cards"] = {
            cid: {
                "decisive_questions": ["fixture question"],
                "answer_units": [{"question_group": 1, "answer": "fixture answer"}],
                "accepted_conditions": {"mode": "exploration", "conditions": []},
            }
            for cid in ids
        }
    else:
        base.update(
            case_rubrics={
                cid: {
                    "critical_items": [
                        {
                            "id": "K1",
                            "assertion": "synthetic assertion",
                            "source_refs": ["S1"],
                        }
                    ],
                    "critical_failures": ["synthetic critical failure"],
                }
                for cid in ids
            },
            source_manifest=[
                {
                    "id": "S1",
                    "capture_sha256": "a" * 64,
                    "representation_sha256": "b" * 64,
                    "utf8_start": 0,
                    "utf8_end": 7,
                    "quote": "fixture",
                    "version_identity": "synthetic-fixed-version",
                    "locator": "synthetic://source",
                }
            ],
            equivalence={
                domain: "Synthetic equivalence only"
                for domain in validator.REVIEW_CASE_PAIRS
            },
        )
    return base


def _frozen_review_materials(tmp_path: Path) -> tuple[dict, Path, str]:
    _current_bundle(tmp_path)
    folder = tmp_path / "docs/evaluation"
    index_path = folder / "DISCOVERY_M1_CASES.json"
    index = json.loads(index_path.read_bytes())
    index["status"] = "frozen_reviewed"
    material_root = tmp_path / validator.MATERIAL_ROOT
    material_root.mkdir(parents=True)
    hashes = {}
    for role, binding in zip(validator.MATERIAL_ROLES, index["packages"], strict=True):
        raw = json.dumps(_review_package(role)).encode()
        (material_root / f"{role}.json").write_bytes(raw)
        binding.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        hashes[role] = binding["sha256"]
    report = {
        "origin_thread_id": "synthetic-review-thread",
        "origin_message_id": "synthetic-review-message",
        "reviewer_context": "synthetic-independent-reviewer",
        "reviewer_role": "independent_non_author_material_reviewer",
        "package_sha256": hashes,
        "conclusion": "done_no_open_findings",
        "limitations": ["synthetic fixture; not real semantic review"],
    }
    raw = json.dumps(report).encode()
    (material_root.parent / "materials-review.json").write_bytes(raw)
    index["review_receipt"] = {
        "report": {
            "relative_ref": str(Path(validator.MATERIAL_ROOT).parent.as_posix())
            + "/materials-review.json",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "rereview_report": None,
        "reviewer_context": report["reviewer_context"],
        "reviewer_role": report["reviewer_role"],
        "package_sha256": hashes,
    }
    index_path.write_bytes(json.dumps(index).encode())
    protocol_path = folder / "CURRENT_EVAL_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_bytes())
    protocol["materials"]["review_status"] = "frozen_reviewed"
    protocol_path.write_bytes(json.dumps(protocol).encode())
    _rebind_current_fixture(folder)
    return index, material_root, hashlib.sha256(index_path.read_bytes()).hexdigest()


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


def _save_review_index(tmp_path, index):
    folder = tmp_path / "docs/evaluation"
    path = folder / "DISCOVERY_M1_CASES.json"
    path.write_bytes(json.dumps(index).encode())
    protocol_path = folder / "CURRENT_EVAL_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_bytes())
    protocol["materials"]["review_status"] = index["status"]
    protocol_path.write_bytes(json.dumps(protocol).encode())
    _rebind_current_fixture(folder)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_default_is_configuration_only_and_explicit_pending_fails(
    tmp_path, monkeypatch, capsys
):
    _current_cli_fixture(tmp_path, monkeypatch)
    assert validator.main(["--root", str(tmp_path)]) == 0
    assert "MATERIALS_NOT_VERIFIED" in capsys.readouterr().out
    path = tmp_path / validator.MATERIAL_INDEX_PATH
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        validator.main(
            [
                "--root",
                str(tmp_path),
                "--review-material-root",
                str(tmp_path / validator.MATERIAL_ROOT),
                "--review-material-index-sha256",
                digest,
            ]
        )
        == 1
    )
    assert "not_ready" in capsys.readouterr().err


@pytest.mark.parametrize(
    "arguments",
    [
        ["--review-material-root", "missing"],
        ["--review-material-index-sha256", "a" * 64],
    ],
)
def test_review_material_cli_requires_both_arguments(tmp_path, monkeypatch, arguments):
    _current_cli_fixture(tmp_path, monkeypatch)
    assert validator.main(["--root", str(tmp_path), *arguments]) == 1


def test_review_synthetic_frozen_bundle_binds_all_roles_and_original_review(tmp_path):
    index, material_root, digest = _frozen_review_materials(tmp_path)
    assert validator.check_current_materials(index) == []
    assert validator.check_review_material_files(tmp_path, material_root, digest) == []
    assert validator.check_review_material_files(tmp_path, material_root, "0" * 64)
    assert validator.check_review_material_files(tmp_path, tmp_path, digest)


@pytest.mark.parametrize("role", validator.MATERIAL_ROLES)
def test_review_package_missing_or_byte_changed_is_not_ready(tmp_path, role):
    _, folder, digest = _frozen_review_materials(tmp_path)
    target = folder / f"{role}.json"
    target.write_bytes(target.read_bytes() + b" ")
    assert any(
        "identity" in e
        for e in validator.check_review_material_files(tmp_path, folder, digest)
    )
    target.unlink()
    assert any(
        "unreadable" in e
        for e in validator.check_review_material_files(tmp_path, folder, digest)
    )


@pytest.mark.parametrize("role", validator.MATERIAL_ROLES)
@pytest.mark.parametrize(
    "bad",
    [
        '"CANARY":0,"CANARY":1',
        '"CANARY":{"nested":0,"nested":1}',
        '"CANARY":NaN',
        '"CANARY":Infinity',
        '"CANARY":-Infinity',
        '"CANARY":1e999',
    ],
)
def test_review_role_raw_json_rejects_without_leaking_input_even_when_rebound(
    tmp_path, role, bad
):
    index, folder, _ = _frozen_review_materials(tmp_path)
    path = folder / f"{role}.json"
    path.write_bytes(b"{" + bad.encode() + b"," + path.read_bytes()[1:])
    binding = next(x for x in index["packages"] if x["role"] == role)
    binding.update(
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size
    )
    index["review_receipt"]["package_sha256"][role] = binding["sha256"]
    digest = _save_review_index(tmp_path, index)
    errors = validator.check_review_material_files(tmp_path, folder, digest)
    assert any(f"{role}: unreadable" in e for e in errors)
    assert "CANARY" not in " ".join(errors)


def test_review_original_report_not_boolean_or_old_package_binding(tmp_path):
    index, folder, digest = _frozen_review_materials(tmp_path)
    report_path = folder.parent / "materials-review.json"
    report = json.loads(report_path.read_bytes())
    report["package_sha256"]["inputs"] = "f" * 64
    report_path.write_bytes(json.dumps(report).encode())
    index["review_receipt"]["report"].update(
        sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        bytes=report_path.stat().st_size,
    )
    digest = _save_review_index(tmp_path, index)
    assert any(
        "original report binding" in e
        for e in validator.check_review_material_files(tmp_path, folder, digest)
    )
    index["review_receipt"] = {"reviewed": True}
    assert validator.check_current_materials(index)


def test_review_author_cannot_be_own_independent_reviewer(tmp_path):
    index, folder, _ = _frozen_review_materials(tmp_path)
    report_path = folder.parent / "materials-review.json"
    report = json.loads(report_path.read_bytes())
    report["reviewer_context"] = "synthetic-author"
    report_path.write_bytes(json.dumps(report).encode())
    index["review_receipt"]["reviewer_context"] = "synthetic-author"
    index["review_receipt"]["report"].update(
        sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        bytes=report_path.stat().st_size,
    )
    digest = _save_review_index(tmp_path, index)
    assert any(
        "own package" in e
        for e in validator.check_review_material_files(tmp_path, folder, digest)
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("bytes", True),
        ("bytes", 1048577),
        ("sha256", "bad"),
        ("relative_ref", "../../CANARY"),
        ("role", "scorer"),
    ],
)
def test_review_frozen_index_rejects_identity_type_and_arbitrary_path(
    tmp_path, field, value
):
    index, _, _ = _frozen_review_materials(tmp_path)
    index["packages"][0][field] = value
    errors = validator.check_current_materials(index)
    assert errors and "CANARY" not in " ".join(errors)


def test_review_unknown_public_fields_cannot_publish_prompts_or_gold(tmp_path):
    _current_bundle(tmp_path)
    index = json.loads((tmp_path / validator.MATERIAL_INDEX_PATH).read_bytes())
    for field in ("prompt", "scorer_only", "source_manifest", "hidden_locator"):
        changed = deepcopy(index)
        changed[field] = "CANARY"
        assert validator.check_current_materials(changed)


def test_review_oversized_raw_file_is_rejected_before_json(tmp_path):
    _, folder, _ = _frozen_review_materials(tmp_path)
    target = folder / "inputs.json"
    with target.open("wb") as out:
        out.truncate(validator.MATERIAL_BYTES_MAX + 1)
    with pytest.raises(ValueError, match="oversized"):
        validator._read_material_bytes(tmp_path, target)


def test_review_file_identity_changes_fail_closed(tmp_path, monkeypatch):
    _, folder, _ = _frozen_review_materials(tmp_path)
    original = validator.os.fstat
    calls = 0

    def changed(fd):
        nonlocal calls
        calls += 1
        info = original(fd)
        if calls == 2:
            fields = list(info)
            fields[6] += 1
            return validator.os.stat_result(fields)
        return info

    monkeypatch.setattr(validator.os, "fstat", changed)
    with pytest.raises(ValueError):
        validator._read_material_bytes(tmp_path, folder / "inputs.json")


def test_review_windows_cross_api_ctime_difference_is_not_identity_drift(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    _, folder, _ = _frozen_review_materials(tmp_path)
    path = folder / "inputs.json"
    original = validator.os.fstat

    def fstat_with_different_ctime(fd):
        info = original(fd)
        return SimpleNamespace(
            st_dev=info.st_dev,
            st_ino=info.st_ino,
            st_size=info.st_size,
            st_mtime_ns=info.st_mtime_ns,
            st_ctime_ns=123,
        )

    monkeypatch.setattr(validator.os, "fstat", fstat_with_different_ctime)
    assert validator._read_material_bytes(tmp_path, path) == path.read_bytes()


def test_review_original_component_reparse_is_rejected(tmp_path, monkeypatch):
    _, folder, _ = _frozen_review_materials(tmp_path)
    original = Path.lstat

    class Reparse:
        st_mode = 0
        st_file_attributes = 0x400

    def flagged(path, *args, **kwargs):
        return Reparse() if path == folder else original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", flagged)
    with pytest.raises(ValueError, match="linked path"):
        validator._read_material_bytes(tmp_path, folder / "inputs.json")


def test_review_actual_parent_symlink_is_rejected_when_supported(tmp_path):
    _, folder, _ = _frozen_review_materials(tmp_path)
    alias = tmp_path / "material-alias"
    try:
        alias.symlink_to(folder, target_is_directory=True)
    except OSError:
        pytest.skip(
            "OS does not permit creating a symlink; simulated reparse regression is separate"
        )
    with pytest.raises(ValueError, match="linked path"):
        validator._read_material_bytes(tmp_path, alias / "inputs.json")


def test_review_resource_counts_and_budget_are_independent_caps(tmp_path):
    protocol = _current_bundle(tmp_path)
    budget = protocol["budget"]
    assert (
        budget["http_calls_max"]
        == sum(
            budget[k]
            for k in (
                "model_physical_calls",
                "search_calls",
                "fetch_calls",
                "github_calls",
            )
        )
        == 1072
    )
    assert (
        budget["github_calls"]
        == sum(
            budget[k]
            for k in (
                "github_data_calls",
                "github_case_control_calls",
                "github_standalone_control_calls",
            )
        )
        == 704
    )
    assert (
        sum(
            Decimal(x) for x in protocol["quotas"]["bytes"]["case_buckets_mib"].values()
        )
        == 64
    )
    assert Decimal(budget["model_total_cny"]) + Decimal(
        budget["api_tools_cny"]
    ) + Decimal(budget["noncall_cny"]) + Decimal(
        budget["unallocated_buffer_cny"]
    ) == Decimal("296.46")
    protocol["quotas"]["tools"]["routes_max"] = 3
    assert check_current_protocol(protocol, tmp_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("stage", "active"),
        ("required_for_current_m1", True),
        ("automatic_read", True),
        ("automatic_write", True),
        ("automatic_read", 0),
        ("import_or_rebuild", True),
        ("request_items", 1),
        ("request_items", False),
        ("request_bytes", 2048),
        ("dedicated_extraction_calls", 1),
        ("reserved_capacity", "reallocated_to_research"),
        ("manual_read", True),
        ("scope", ["author", "team", "project"]),
    ],
)
def test_focus_memory_cannot_enable_any_entrypoint_or_extra_policy(
    tmp_path, field, value
):
    protocol = _current_bundle(tmp_path)
    protocol["memory"][field] = value
    errors = check_current_protocol(protocol, tmp_path)
    assert any("Memory policy" in error or "memory" in error for error in errors)


@pytest.mark.parametrize(
    "field,value",
    [
        ("hits", 0),
        ("writes", 0),
        ("state", "active"),
        ("active_refs", ["CANARY_OLD_MEMORY"]),
    ],
)
def test_focus_disabled_memory_observation_is_not_fake_zero_evidence(
    tmp_path, field, value
):
    protocol = _current_bundle(tmp_path)
    protocol["attempt_record_contract"]["memory_observation"][field] = value
    errors = check_current_protocol(protocol, tmp_path)
    assert any("memory_observation" in error for error in errors)
    assert "CANARY_OLD_MEMORY" not in " ".join(errors)


def test_focus_current_bundle_keeps_memory_deferred_without_context_dependency(
    tmp_path,
):
    protocol = _current_bundle(tmp_path)
    assert check_current_protocol(protocol, tmp_path) == []
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    assert all(c["id"] != "automatic_memory" for c in supplement["capabilities"])
    context = next(c for c in supplement["capabilities"] if c["id"] == "context")
    assert context["tasks"] == ["DEC-M1-03a", "DEC-M1-03b"]
    assert supplement["deferred_capabilities"][0]["status"] == "pending_not_completed"
    assert supplement["deferred_capabilities"][0]["required"] is False
    assert protocol["memory"]["reserved_capacity"] == "unchanged_not_reallocated"


@pytest.mark.parametrize(
    "drift",
    ["required", "passed", "duplicate", "context_dependency", "missing_deferred"],
)
def test_focus_m1_cannot_complete_or_require_deferred_memory(tmp_path, drift):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    deferred = supplement["deferred_capabilities"][0]
    if drift == "required":
        deferred["required"] = True
    elif drift == "passed":
        deferred["status"] = "passed"
    elif drift == "duplicate":
        supplement["capabilities"].append(deepcopy(deferred))
    elif drift == "context_dependency":
        next(c for c in supplement["capabilities"] if c["id"] == "context")[
            "tasks"
        ].append("DEC-M1-04")
    else:
        del supplement["deferred_capabilities"]
    errors = validator.check_current_supplement(
        supplement, (tmp_path / validator.PROTOCOL).read_bytes()
    )
    assert any("capabilit" in error for error in errors)


def test_focus_materials_reject_old_protocol_index_packages_and_root(tmp_path):
    _current_bundle(tmp_path)
    index = json.loads(
        (tmp_path / "docs/evaluation/DISCOVERY_M1_CASES.json").read_bytes()
    )
    index["protocol_version"] = "draft-m1-1"
    assert check_current_materials(index)
    for role in validator.MATERIAL_ROLES:
        package = _review_package(role)
        package["protocol_version"] = "draft-m1-1"
        assert validator.check_review_material_package(package, role)
    index["protocol_version"] = "draft-m1-3"
    for package in index["packages"]:
        package["relative_ref"] = package["relative_ref"].replace(
            "research-20261103", "focus-20261102"
        )
    assert any(
        "identity" in error or "canonical" in error or "fields" in error
        for error in check_current_materials(index)
    )


def test_focus_old_material_review_receipt_cannot_certify_new_package(tmp_path):
    index, material_root, _ = _frozen_review_materials(tmp_path)
    # A structurally valid reauthored package has different bytes; an old review
    # remains bound to the old package hash even if the public binding is updated.
    package_path = material_root / "inputs.json"
    package = json.loads(package_path.read_bytes())
    package["author_context"] = "new-synthetic-author"
    raw = json.dumps(package).encode()
    package_path.write_bytes(raw)
    index["packages"][0].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    # Keep the public index internally valid so this reaches the original
    # report binding check instead of failing the public-index precondition.
    index["review_receipt"]["package_sha256"]["inputs"] = hashlib.sha256(
        raw
    ).hexdigest()
    assert check_current_materials(index) == []
    index_path = tmp_path / validator.MATERIAL_INDEX_PATH
    index_path.write_bytes(json.dumps(index).encode())
    errors = validator.check_review_material_files(
        tmp_path, material_root, hashlib.sha256(index_path.read_bytes()).hexdigest()
    )
    assert errors == ["materials review: original report binding invalid"]


@pytest.mark.parametrize("filename", list(validator.APPROVED_CURRENT_HASHES))
def test_research_whitespace_change_cannot_rebind_current_approved_bytes(
    tmp_path, filename
):
    protocol = _current_bundle(tmp_path)
    target = tmp_path / filename
    target.write_bytes(target.read_bytes() + b" ")
    _rebind_current_fixture(tmp_path / "docs/evaluation")
    errors = check_current_protocol(protocol, tmp_path)
    assert any("approved raw SHA-256" in error for error in errors)


def test_research_cli_hash_parse_and_chain_use_each_captured_file_once(
    tmp_path, monkeypatch
):
    _current_cli_fixture(tmp_path, monkeypatch)
    original = validator._read_material_bytes
    reads = []

    def capture(root, target):
        reads.append(target.relative_to(root).as_posix())
        return original(root, target)

    monkeypatch.setattr(validator, "_read_material_bytes", capture)
    assert validator.main(["--root", str(tmp_path)]) == 0
    assert sorted(reads) == sorted(validator.APPROVED_CURRENT_HASHES)


def test_research_later_disk_change_does_not_substitute_for_captured_protocol(
    tmp_path, monkeypatch
):
    _current_cli_fixture(tmp_path, monkeypatch)
    original = validator._read_material_bytes
    changed = False

    def capture(root, target):
        nonlocal changed
        raw = original(root, target)
        if target == root / validator.PROTOCOL and not changed:
            changed = True
            target.write_bytes(raw + b" ")
        return raw

    monkeypatch.setattr(validator, "_read_material_bytes", capture)
    # This invocation qualifies only its captured snapshot, not the later disk.
    assert validator.main(["--root", str(tmp_path)]) == 0
    assert validator.main(["--root", str(tmp_path)]) == 1


def test_research_valid_supplied_object_is_not_a_substitute_for_root_bytes(tmp_path):
    protocol = _current_bundle(tmp_path)
    independent = deepcopy(protocol)
    independent["authority"] = "CANARY_NEW_AUTHORITY"
    errors = check_current_protocol(independent, tmp_path)
    assert any("supplied object differs" in error for error in errors)
    assert "CANARY_NEW_AUTHORITY" not in " ".join(errors)


def test_research_unapproved_root_keys_are_not_echoed_as_diagnostic_paths(tmp_path):
    protocol = _current_bundle(tmp_path)
    altered = deepcopy(protocol)
    altered["CANARY_PRIVATE_KEY_NAME"] = "CANARY_PRIVATE_VALUE"
    (tmp_path / validator.PROTOCOL).write_bytes(json.dumps(altered).encode())
    errors = check_current_protocol(protocol, tmp_path)
    assert errors
    assert "CANARY" not in " ".join(errors)


@pytest.mark.parametrize(
    "path,value",
    [
        (("normal_obligations",), 15),
        (("normal_input_total",), 360449),
        (("normal_output_total",), 61441),
        (("physical_calls_max",), 17),
        (("technical_retry_max",), 3),
        (("technical_retry_per_work_max",), 2),
        (("compile_physical_calls_max",), 5),
        (("compile_limit_includes_technical_retries",), False),
        (("summary_extra_calls",), 1),
        (("hidden_judge_extra_calls",), 1),
        (("first_attempt_reservation", "refund_or_regrant_after_sent_failure"), True),
        (("first_attempt_reservation", "guarantees_success"), True),
        (("first_attempt_reservation", "borrowable_by_optional_work"), True),
        (("mode_obligations", "requirements_to_solution", "first_artifacts"), 1),
        (("purpose_mapping", "clarify"), "document_compile"),
        (("stages", 0, "normal_obligations"), 2),
    ],
)
def test_research_structural_negative_fixture_checks_without_hash_short_circuit(
    tmp_path, path, value
):
    protocol = _current_bundle(tmp_path)
    target = protocol["quotas"]["case_model"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    # Pure invariant result is not a current-bundle approval or runtime test.
    assert validator.check_current_policy(protocol)


def test_research_trusted_synthetic_hash_does_not_replace_arithmetic(
    tmp_path, monkeypatch
):
    folder = _current_cli_fixture(tmp_path, monkeypatch)
    path = folder / "CURRENT_EVAL_PROTOCOL.json"
    protocol = json.loads(path.read_bytes())
    protocol["quotas"]["case_model"]["physical_calls_max"] = 17
    path.write_bytes(json.dumps(protocol).encode())
    _rebind_current_fixture(folder)
    # Unit-only alternate trusted fixture: no such override exists in the CLI.
    monkeypatch.setattr(
        validator,
        "APPROVED_CURRENT_HASHES",
        {
            relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
            for relative in validator.APPROVED_CURRENT_HASHES
        },
    )
    assert validator.main(["--root", str(tmp_path)]) == 1


@pytest.mark.parametrize(
    "group,key,value",
    [
        ("local_format", "count_kind", "provider_actual_billable_tokens"),
        ("hosted_fit", "meaning", "exact_remote_count_zero_overflow"),
        ("hosted_fit", "legal_nonzero_local_delta", "reject_every_difference"),
        ("hosted_fit", "business_output_schema_failure", "revoke_supplier_profile"),
        ("hosted_fit", "revoke_on", []),
        ("usage_and_fees", "unknown", "assume_zero_and_retry_new_id"),
    ],
)
def test_research_token_layer_failure_policies_are_structurally_distinct(
    tmp_path, group, key, value
):
    protocol = _current_bundle(tmp_path)
    protocol["quotas"]["case_model"]["token_qualification"][group][key] = value
    errors = validator.check_current_policy(protocol)
    assert any("Token" in error for error in errors)


def test_research_baseline_preserves_legal_delta_and_unattempted_first_reserve(
    tmp_path,
):
    protocol = _current_bundle(tmp_path)
    assert validator.check_current_policy(protocol) == []
    model = protocol["quotas"]["case_model"]
    assert "normal_obligations" not in model["stages"][0]
    assert model["compile_physical_calls_max"] == 4
    assert model["compile_limit_includes_technical_retries"] is True
    assert (
        model["first_attempt_reservation"]["refund_or_regrant_after_sent_failure"]
        is False
    )
    assert "legal_nonzero_local_delta" in model["token_qualification"]["hosted_fit"]


def test_rearm_capability_revision_preserves_sole_protocol_and_pending_results(
    tmp_path,
):
    _current_bundle(tmp_path)
    protocol_raw = (tmp_path / validator.PROTOCOL).read_bytes()
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    assert hashlib.sha256(protocol_raw).hexdigest() == (
        "799178fb431656c00c785634ad53df06b62d660a68291b7fab3719bcf8584eda"
    )
    assert supplement["protocol_version"] == "draft-m1-capabilities-6"
    assert supplement["current_protocol"]["version"] == "draft-m1-3"
    assert validator.check_current_supplement(supplement, protocol_raw) == []
    assert all(value is False for value in supplement["results"].values())


@pytest.mark.parametrize(
    "drift",
    [
        "old_revision",
        "missing_cross_turn",
        "missing_attestation_boundary",
        "missing_task_cleanup",
        "missing_control_only",
        "missing_abnormal_isolation",
        "missing_process_qualification",
        "missing_pre_pilot_dependency",
        "claim_implemented",
        "claim_paid_authority",
    ],
)
def test_rearm_capability_rejects_missing_obligations_or_authority_claims(
    tmp_path, drift
):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    runtime = next(
        c for c in supplement["capabilities"] if c["id"] == "runtime_harness"
    )
    recovery = next(
        c for c in supplement["capabilities"] if c["id"] == "identity_recovery_practice"
    )
    if drift == "old_revision":
        supplement["protocol_version"] = "draft-m1-capabilities-3"
    elif drift == "missing_cross_turn":
        runtime["evidence"].remove(
            "full_flow_partial_human_edit_confirmation_linked_Turn_separate_seals_exact_double_draft_package"
        )
    elif drift == "missing_pre_pilot_dependency":
        recovery["tasks"].remove("DEC-M1-03b")
    elif drift == "claim_implemented":
        supplement["results"]["implemented"] = True
    elif drift == "claim_paid_authority":
        supplement["authorization"]["paid_execution"] = True
    else:
        marker = {
            "missing_attestation_boundary": "trusted_operator",
            "missing_task_cleanup": "nonterminal_tasks",
            "missing_control_only": "CONTROL_ONLY",
            "missing_abnormal_isolation": "abnormal_or_suspected",
            "missing_process_qualification": "paid_disabled_process",
        }[drift]
        recovery["evidence"] = [e for e in recovery["evidence"] if marker not in e]
    # Exercise semantic checks directly: rehashing a fixture is not an approval.
    assert validator.check_current_supplement(
        supplement, (tmp_path / validator.PROTOCOL).read_bytes()
    )


def test_team_delivery_capability_preserves_sole_authority_and_unverified_scope(
    tmp_path,
):
    _current_bundle(tmp_path)
    protocol_raw = (tmp_path / validator.PROTOCOL).read_bytes()
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    assert validator.APPROVED_CONFIGURATION_REVISION == "DEV-STAGES-20261104-01"
    assert supplement["protocol_version"] == "draft-m1-capabilities-6"
    assert validator.check_current_supplement(supplement, protocol_raw) == []
    team = supplement["team_delivery_contract"]
    assert team["safety_reserve"]["next_invalidation_reserve_bytes"] == 3072
    assert team["safety_reserve"]["owners"][-1] == "current_RequirementsConfirmation"
    sequence = team["delivery"]["sequence"]
    assert sequence.index("ENV-M1-02-and-DEC-M1-03b-qualification") < sequence.index(
        "first_public_full_flow_pilot"
    )
    assert (
        sequence.index("first_public_full_flow_pilot")
        < sequence.index("DEC-M1-02-C-dynamic-reintegration")
        < sequence.index("private_App_sources")
    )
    assert all(value is False for value in supplement["results"].values())
    assert all(value is False for value in supplement["authorization"].values())


@pytest.mark.parametrize(
    "path,value",
    [
        (("roles", "confirm_and_revoke"), "any_project_member"),
        (("roles", "accept_edit_cancel_continue"), "confirmer"),
        (("roles", "confirmation_grants_task_budget_or_source_authority"), True),
        (("roles", "private_Draft_automatically_shared"), True),
        (("roles", "CLI_checks"), []),
        (("deployment", "accounts_max"), 3),
        (("deployment", "admin_web_UI"), True),
        (("confirmation", "binds"), ["requirements_hash", "actor"]),
        (("confirmation", "old_approval_revival_after_swapback_rejoin_reenable"), True),
        (("confirmation", "invalidated_by"), ["new_requirements_head"]),
        (("confirmation", "not_invalidated_by_alone"), ["logout"]),
        (("confirmation", "solution_checks"), ["start", "commit"]),
        (("confirmation", "requirements_drafting_and_review_without_confirmer"), False),
        (
            ("confirmation", "revoke_requires_source_body_or_private_proof_refresh"),
            True,
        ),
        (
            (
                "confirmation",
                "revoke_requires_research_grant_or_remaining_research_time",
            ),
            True,
        ),
        (("safety_reserve", "owners"), ["Account_approval_eligibility"]),
        (("safety_reserve", "next_invalidation_reserve_bytes"), "3072"),
        (("safety_reserve", "receipt_max_bytes"), 3072),
        (
            ("safety_reserve", "confirmation_bucket"),
            "existing_non_Case_safety_metadata",
        ),
        (("safety_reserve", "reserve_before_create_activate_or_reconfirm"), 1),
        (("safety_reserve", "ordinary_creation_bytes_separately_accounted"), False),
        (("safety_reserve", "borrow_other_object_reserve"), True),
        (("safety_reserve", "increase_pool_or_borrow_disabled_Memory"), True),
        (
            ("safety_reserve", "ordinary_full_capacity_blocks_mandatory_invalidation"),
            True,
        ),
        (("safety_reserve", "same_operation_same_body"), "charge_and_create_again"),
        (("safety_reserve", "temporary_source_unavailability_allows_cleanup"), True),
        (("delivery", "dynamic_and_private_sources_required_for_full_M1"), False),
        (("delivery", "single_chain_preview_closes_dynamic_parent_AC"), True),
        (("delivery", "fake_and_real_share_application_admission_path"), False),
        (
            ("delivery", "first_real_pilot_requires"),
            ["exact_real_execution_authorization"],
        ),
        (("delivery", "new_Case_call_funding_or_deadline_allocation"), True),
        (
            ("formal_and_value", "same_actual_human_account_may_request_and_confirm"),
            False,
        ),
        (("formal_and_value", "sole_protocol_bytes_changed"), True),
        (("formal_and_value", "real_team_and_task_evidence"), "proven"),
    ],
)
def test_team_delivery_rejects_semantic_drift_without_relying_on_raw_hash(
    tmp_path, path, value
):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    target = supplement["team_delivery_contract"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert "M1 team delivery contract differs" in validator.check_current_supplement(
        supplement, (tmp_path / validator.PROTOCOL).read_bytes()
    )


@pytest.mark.parametrize(
    "drift",
    ["missing_contract", "old_revision", "early_pilot", "missing_confirmation_reserve"],
)
def test_team_delivery_rejects_missing_scope_or_premature_pilot(tmp_path, drift):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    if drift == "missing_contract":
        del supplement["team_delivery_contract"]
    elif drift == "old_revision":
        supplement["protocol_version"] = "draft-m1-capabilities-4"
    elif drift == "missing_confirmation_reserve":
        supplement["team_delivery_contract"]["safety_reserve"]["owners"].remove(
            "current_RequirementsConfirmation"
        )
    else:
        sequence = supplement["team_delivery_contract"]["delivery"]["sequence"]
        pilot = sequence.index("first_public_full_flow_pilot")
        qualification = sequence.index("ENV-M1-02-and-DEC-M1-03b-qualification")
        sequence[pilot], sequence[qualification] = (
            sequence[qualification],
            sequence[pilot],
        )
    assert validator.check_current_supplement(
        supplement, (tmp_path / validator.PROTOCOL).read_bytes()
    )


def test_staged_engineering_acceptance_keeps_live_safety_and_effects_separate(tmp_path):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    delivery = supplement["development_delivery_policy"]
    effects = supplement["on_demand_evaluation"]
    assert delivery["engineering_completion_label"] == "M1工程能力验收通过"
    assert delivery["stage_count"] == 6
    assert delivery["slice_count"] == 26
    assert [len(ids) for ids in delivery["stage_slice_ids"].values()] == [
        3,
        4,
        7,
        5,
        4,
        3,
    ]
    assert delivery["preparation_counts_as_development_stage"] is False
    assert effects["blocks_engineering_acceptance"] is False
    assert effects["unexecuted_status"] == "not_evaluated_not_passed"
    assert effects["engineering_real_test_slots"] == [
        {
            "role": "early_pilot_1",
            "slice": "4.5",
            "sources": "public",
            "mode": "requirements_to_solution",
        },
        {
            "role": "early_pilot_2",
            "slice": "5.4",
            "sources": "private",
            "mode": "requirements_only",
        },
    ]
    required_evidence = {
        evidence
        for capability in supplement["capabilities"]
        for evidence in capability["evidence"]
    }
    assert "canonical_trace_and_offline_no_send_reconstruction" in required_evidence
    assert "all_three_raw_Agent_reports_critical_quality_pass" not in required_evidence
    assert (
        "at_least_one_real_symptom_corrected_with_matched_evidence"
        not in required_evidence
    )
    assert all(value is False for value in supplement["results"].values())
    assert (
        validator.check_current_supplement(
            supplement, (tmp_path / validator.PROTOCOL).read_bytes()
        )
        == []
    )


@pytest.mark.parametrize(
    "drift",
    [
        "missing_slice",
        "duplicate_slice",
        "wrong_stage",
        "extra_stage",
        "P0_counted_as_stage",
        "commit_before_acceptance",
        "automatic_cross_stage",
        "automatic_merge",
        "stage_start_grants_paid_authority",
        "optional_Pg_races",
        "skip_counts_as_pass",
        "later_safety_checks",
        "diagnostic_regrant",
        "restore_deferred_until_stage_6",
        "engineering_M1_claimed",
        "effects_again_required",
        "unexecuted_effect_passes",
        "new_pilot_slot",
        "optional_effect_gets_more_pilots",
        "funding_increase",
        "public_only_private_test",
        "private_test_wrong_mode",
        "formal_evidence_in_engineering",
        "engineered_trace_made_optional",
    ],
)
def test_staged_delivery_rejects_unsafe_execution_or_acceptance_drift(tmp_path, drift):
    _current_bundle(tmp_path)
    supplement = json.loads(
        (tmp_path / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
    )
    delivery = supplement["development_delivery_policy"]
    effects = supplement["on_demand_evaluation"]
    if drift == "missing_slice":
        delivery["stage_slice_ids"]["3"].remove("3.6")
    elif drift == "duplicate_slice":
        delivery["stage_slice_ids"]["3"][5] = "3.5"
    elif drift == "wrong_stage":
        delivery["stage_slice_ids"]["2"].append(delivery["stage_slice_ids"]["3"].pop(0))
    elif drift == "extra_stage":
        delivery["stage_slice_ids"]["7"] = ["7.1"]
    elif drift == "P0_counted_as_stage":
        delivery["preparation_counts_as_development_stage"] = True
    elif drift == "commit_before_acceptance":
        sequence = delivery["slice_sequence"]
        commit = sequence.index("commit_push_create_or_update_same_stage_PR")
        sequence.insert(0, sequence.pop(commit))
    elif drift == "automatic_cross_stage":
        delivery["next_stage_starts_automatically"] = True
    elif drift == "automatic_merge":
        delivery["stage_merge_requires_separate_owner_authority"] = False
    elif drift == "stage_start_grants_paid_authority":
        delivery["stage_start_grants_environment_paid_or_external_operations"] = True
    elif drift in {"optional_Pg_races", "skip_counts_as_pass"}:
        marker = (
            "real_restricted_Pg"
            if drift == "optional_Pg_races"
            else "mandatory_skipped"
        )
        delivery["required_engineering_checks"] = [
            check
            for check in delivery["required_engineering_checks"]
            if marker not in check
        ]
    elif drift == "later_safety_checks":
        delivery["post_integration_slices_defer_earlier_core_safety_tests"] = True
    elif drift == "diagnostic_regrant":
        delivery["insufficient_diagnostic_or_real_allocation"] = "new_diagnostic_pool"
    elif drift == "restore_deferred_until_stage_6":
        delivery["minimum_restore_before_private_real_test"] = "wait_for_stage_6"
    elif drift == "engineering_M1_claimed":
        supplement["results"]["engineering_M1"] = True
    elif drift == "effects_again_required":
        effects["blocks_engineering_acceptance"] = True
    elif drift == "unexecuted_effect_passes":
        effects["unexecuted_status"] = "passed"
    elif drift == "new_pilot_slot":
        effects["engineering_real_test_slots"].append(
            {"role": "extra_engineering_pilot", "slice": "5.4"}
        )
    elif drift == "optional_effect_gets_more_pilots":
        effects["optional_effect_runs_automatically_receive_new_pilot_slots"] = True
    elif drift == "funding_increase":
        effects["new_pilot_Case_call_funding_or_deadline_allocation"] = True
    elif drift == "public_only_private_test":
        effects["engineering_real_test_slots"][1]["sources"] = "public"
    elif drift == "private_test_wrong_mode":
        effects["engineering_real_test_slots"][1]["mode"] = "review_only"
    elif drift == "formal_evidence_in_engineering":
        supplement["capabilities"][3]["evidence"].append(
            "all_three_raw_Agent_reports_critical_quality_pass"
        )
    elif drift == "engineered_trace_made_optional":
        supplement["capabilities"][3]["evidence"].remove(
            "canonical_trace_and_offline_no_send_reconstruction"
        )
    # Test semantic refusal directly; a fixture's recomputed hash grants no authority.
    assert validator.check_current_supplement(
        supplement, (tmp_path / validator.PROTOCOL).read_bytes()
    )


def _staged_plan_text():
    ids = [
        f"{stage}.{number}"
        for stage, count in enumerate([3, 4, 7, 5, 4, 3], start=1)
        for number in range(1, count + 1)
    ]
    labels = dict(zip("123456", "一二三四五六", strict=True))
    return "DEV-STAGES-20261104-01\n" + "\n".join(
        f"| {slice_id} | {labels[slice_id.split('.')[0]]}：可改名 | result |"
        for slice_id in ids
    )


def test_canonical_slice_table_accepts_exact_route_without_task_history():
    assert validator.check_current_development_plan(_staged_plan_text()) == []


def test_canonical_slice_table_does_not_freeze_stage_title_wording():
    plan = _staged_plan_text().replace("可改名", "renamed stage title")
    assert validator.check_current_development_plan(plan) == []


@pytest.mark.parametrize(
    "drift",
    [
        "missing",
        "duplicate",
        "extra",
        "wrong_order",
        "wrong_stage_label",
        "old_revision",
    ],
)
def test_canonical_slice_table_rejects_missing_duplicate_or_wrong_route(drift):
    plan = _staged_plan_text()
    if drift == "missing":
        plan = plan.replace("| 3.6 | 三：可改名 | result |", "")
    elif drift == "duplicate":
        plan = plan.replace("| 3.6 |", "| 3.5 |")
    elif drift == "extra":
        plan += "\n| 7.1 | phase | result |"
    elif drift == "wrong_order":
        plan = plan.replace("| 4.1 |", "| TEMP |")
        plan = plan.replace("| 4.2 |", "| 4.1 |").replace("| TEMP |", "| 4.2 |")
    elif drift == "wrong_stage_label":
        plan = plan.replace("| 4.1 | 四：", "| 4.1 | 五：")
    else:
        plan = plan.replace("DEV-STAGES-20261104-01", "TEAM-BASELINE-20261103-01")
    assert validator.check_current_development_plan(plan)
