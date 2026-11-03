"""Deterministic offline checks for the current development configuration.

Usage: python scripts/validate_project.py [--root PATH] [--results JSON] [--ledger JSON]
The optional files are completed evidence, not run triggers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_MANIFEST = "docs/archive/R0_PATH_MAP.json"
DESIGN_INDEX = "docs/archive/design-0.3/00_DESIGN_INDEX.md"
DOCS = (
    "AGENTS.md",
    ".agents/skills/agent-failure-triage/SKILL.md",
    ".agents/skills/research-eval/SKILL.md",
    ".agents/skills/research-implementation/SKILL.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "SPEC.md",
    "PLANS.md",
    "docs/README.md",
    "docs/audits/V3_CONFIG_ACCEPTANCE_2026-10-23.md",
    "docs/decisions/DECISION_LOG.md",
    "docs/decisions/V3_CONFIG_MIGRATION_MAP.md",
    "docs/decisions/V3_SPEC_CONTRACT_CHANGE_PROPOSAL.md",
    "docs/design/adr/0006-python-open-source-decision-agent.md",
    "docs/engineering/WORKFLOW.md",
    "docs/engineering/CONFIGURATION.md",
    "docs/engineering/TASK_TEMPLATE.md",
    "docs/features/DECISION-001/spec.md",
    "docs/features/DECISION-001/tasks.md",
    "docs/research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md",
    "docs/testing/STRATEGY.md",
    "docs/archive/target-0.4/SPEC_0.4.md",
    "docs/archive/target-0.4/PLANS_0.4.md",
    "docs/contracts/CURRENT_CONTRACTS.md",
    "docs/contracts/0.5_TARGET_CONTRACTS.md",
    "docs/archive/design-0.3/adr/0004-portfolio-local-runtime.md",
    "docs/design/adr/0005-windows-worker-wsl-postgres.md",
    "docs/archive/design-0.3/adr/0003-langgraph-postgres-lan.md",
    "docs/evaluation/README.md",
    "docs/archive/target-2026-10-18/README.md",
    DESIGN_INDEX,
    "docs/archive/design-0.3/07_AI_CODING_WORKFLOW.md",
    "docs/audits/PREDEV_BASELINE_2026-10-18.md",
    "docs/audits/PREDEV_0_5_VERIFICATION_2026-10-19.md",
    "docs/audits/PREDEV_FINAL_DESIGN_REVIEW_2026-10-19.md",
    "docs/research/AI_CODING_WORKFLOWS.md",
)
SKILLS = ("research-implementation", "agent-failure-triage", "research-eval")
PROTOCOL = "docs/evaluation/CURRENT_EVAL_PROTOCOL.json"
CURRENT_PROTOCOL_VERSION = "draft-m1-3"
ARCHIVED_TARGET_PROTOCOL = "docs/evaluation/G3_EVAL_PROTOCOL.json"
HISTORICAL_PROTOCOL = "docs/evaluation/G2_EVAL_PROTOCOL.json"
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REQUIREMENT = re.compile(r"(?:FR|NFR)-\d{3}")
ACCEPTANCE = re.compile(r"AC-(?:N\d{2}|\d{3})")
STAGE = re.compile(r"P-0[0-4]")
HISTORICAL_HASHES = {
    "docs/archive/target-0.4/SPEC_0.4.md": "31b8e45383ce0b39d665ccfe4e6bd813bd6439248c17b446d6b0f4baedf12847",
    "docs/archive/target-0.4/PLANS_0.4.md": "3741de432b9396d0bc08bcc5a6c685332111dc459af06a3f10efde4a93a60701",
}
ARCHIVED_TARGET_HASHES = {
    "docs/archive/target-2026-10-18/SPEC.md": "80c6f86f44659dd8e5a9764ea2f66e334eeff0ded65a18822077b395b80db28e",
    "docs/archive/target-2026-10-18/PLANS.md": "7238a6e76d5b14e84a8efbfb614f62d4f975a01f9a1bb00d2d7ce68564be909c",
    "docs/evaluation/archive/CURRENT_EVAL_PROTOCOL_current-1.json": "542320be31bd512ed39ed77fa73475d3301cbd9e1f70d9fdd1a4a6e856e2098e",
    "docs/evaluation/archive/CURRENT_EVAL_PROTOCOL_current-2.json": "6fa06e0ff2cb73b6fcf246130da23aa559b9b5256a9ef46d8065496850e7a53f",
}


def archive_path_map(root: Path) -> dict[str, str]:
    manifest = root / ARCHIVE_MANIFEST
    if not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {item["old_path"]: item["new_path"] for item in data["entries"]}


def check_archive_manifest(root: Path) -> list[str]:
    """Freeze historical bytes while allowing relocated active task records to evolve."""

    manifest = root / ARCHIVE_MANIFEST
    if not manifest.is_file():
        return [f"missing archive map: {ARCHIVE_MANIFEST}"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data["version"] != 1 or not isinstance(data["entries"], list):
            return ["archive map: unsupported version or entries"]
        errors: list[str] = []
        seen_old: set[str] = set()
        seen_new: set[str] = set()
        for item in data["entries"]:
            old, new = item["old_path"], item["new_path"]
            if (
                not isinstance(old, str)
                or not isinstance(new, str)
                or old in seen_old
                or new in seen_new
                or Path(old).is_absolute()
                or Path(new).is_absolute()
                or ".." in Path(old).parts
                or ".." in Path(new).parts
            ):
                errors.append(
                    f"archive map: invalid or duplicate path {old!r} -> {new!r}"
                )
                continue
            seen_old.add(old)
            seen_new.add(new)
            target = (root / new).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                errors.append(f"archive map: missing or escaping target {new}")
                continue
            if (root / old).exists():
                errors.append(f"archive map: old path still exists {old}")
            if (
                item["kind"] == "historical"
                and hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]
            ):
                errors.append(f"archive map: changed bytes {new}")
            if item["kind"] not in {"historical", "current_task"}:
                errors.append(f"archive map: invalid kind {new}")
            if (
                item["kind"] == "historical"
                and item.get("old_sha256", item["sha256"]) != item["sha256"]
            ):
                errors.append(f"archive map: historical bytes changed {new}")
        return errors
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [f"archive map unreadable: {exc}"]


def check_archive_git_index(root: Path) -> list[str]:
    """Check that Git will publish the frozen archive bytes from this checkout."""

    if not (root / ".git").exists():
        return []
    try:
        data = json.loads((root / ARCHIVE_MANIFEST).read_text(encoding="utf-8"))
        frozen = {
            item["new_path"]: item["sha256"]
            for item in data["entries"]
            if item["kind"] == "historical"
        }
        frozen.update(ARCHIVED_TARGET_HASHES)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [f"Git index archive check unreadable: {exc}"]

    errors: list[str] = []
    for relative, expected_hash in frozen.items():
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "show", f":{relative}"],
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            return [f"Git index archive check unavailable: {exc}"]
        if result.returncode != 0:
            errors.append(f"Git index missing frozen archive: {relative}")
        elif hashlib.sha256(result.stdout).hexdigest() != expected_hash:
            errors.append(f"Git index frozen archive bytes differ: {relative}")
    return errors


def check_links(root: Path, files: tuple[str, ...] = DOCS) -> list[str]:
    errors: list[str] = []
    moved = archive_path_map(root)
    former = {new: old for old, new in moved.items()}
    for relative in files:
        source = root / relative
        if not source.is_file():
            errors.append(f"missing document: {relative}")
            continue
        for number, line in enumerate(
            source.read_text(encoding="utf-8").splitlines(), 1
        ):
            for match in LINK.finditer(line):
                target = match.group(1).split(maxsplit=1)[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("//"):
                    continue
                local = unquote(parsed.path)
                if not local:
                    continue
                resolved = (source.parent / local).resolve()
                if resolved.is_relative_to(root.resolve()) and resolved.exists():
                    continue
                # Archived documents retain their original bytes and links. Current
                # documents must point directly at the relocated target.
                if relative.startswith("docs/archive/"):
                    original_source = root / former.get(relative, relative)
                    old_target = (original_source.parent / local).resolve()
                    if old_target.is_relative_to(root.resolve()):
                        old_relative = old_target.relative_to(root.resolve()).as_posix()
                        mapped = moved.get(old_relative)
                        if mapped is not None and (root / mapped).exists():
                            continue
                        if old_target.exists():
                            continue
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    errors.append(f"{relative}:{number}: broken local link {target}")
    return errors


def project_document_files(root: Path) -> tuple[str, ...]:
    """Check the repository's root and project docs, excluding upstream checkout."""
    candidates = set(DOCS)
    candidates.update(str(path.relative_to(root)) for path in root.glob("*.md"))
    candidates.update(
        str(path.relative_to(root))
        for path in (root / "docs").rglob("*.md")
        if path.relative_to(root / "docs").parts[0] != "archive"
    )
    return tuple(sorted(candidates))


def check_versions_and_traceability(root: Path) -> list[str]:
    errors: list[str] = []
    paths = {
        name: root / name
        for name in (
            "SPEC.md",
            "PLANS.md",
            "AGENTS.md",
            DESIGN_INDEX,
        )
    }
    if any(not path.is_file() for path in paths.values()):
        return [
            f"missing version pointer: {name}"
            for name, path in paths.items()
            if not path.is_file()
        ]
    texts = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    current_links = (
        "SPEC.md",
        "PLANS.md",
        "CURRENT_CONTRACTS.md",
        "CURRENT_EVAL_PROTOCOL.json",
    )
    for name in ("AGENTS.md", DESIGN_INDEX):
        if not all(link in texts[name] for link in current_links):
            errors.append(f"{name}: missing one or more current entry points")
    if "0.5 目标规格" in texts[DESIGN_INDEX]:
        errors.append("design index: archived target still labeled current")
    for name, expected_hash in HISTORICAL_HASHES.items():
        path = root / name
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected_hash
        ):
            errors.append(f"{name}: historical snapshot missing or modified")
    for name, expected_hash in ARCHIVED_TARGET_HASHES.items():
        path = root / name
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash
        ):
            errors.append(f"{name}: archived target missing or modified")
    spec, plan = texts["SPEC.md"], texts["PLANS.md"]
    if "DEC-M1-01" in plan:
        feature = root / "docs/features/DECISION-001/spec.md"
        if not feature.is_file():
            return errors + ["missing current feature acceptance mapping"]
        feature_text = feature.read_text(encoding="utf-8")
        for number in range(8, 21):
            acceptance = f"DEC-AC-{number:02d}"
            if acceptance not in feature_text or acceptance not in plan:
                errors.append(f"current mapping missing {acceptance}")
        for task in (
            "ENV-M1-01",
            "ENV-M1-02",
            "DEC-M1-01",
            "DEC-M1-02",
            "DEC-M1-03a",
            "DEC-M1-03b",
            "DEC-M1-04",
            "DEC-M1-05",
            "DEC-M1-06",
            "DEC-M1-07",
            "DEC-M1-08b",
        ):
            if task not in plan:
                errors.append(f"current plan missing task {task}")
        errors.extend(check_current_development_plan(plan))
        return errors
    stage_mapping_rows = [
        line for line in plan.splitlines() if re.match(r"^\| P-0[0-4] \|", line)
    ]
    expected = {
        *(f"FR-{i:03d}" for i in range(1, 13)),
        *(f"NFR-{i:03d}" for i in range(1, 11)),
    }
    required_new_stages = {
        "FR-011": "P-03",
        "FR-012": "P-03",
        "NFR-010": "P-02",
    }
    for requirement in sorted(expected):
        suffix = requirement.split("-")[1]
        ac = f"AC-N{suffix[1:]}" if requirement.startswith("NFR") else f"AC-{suffix}"
        row = next(
            (
                line
                for line in spec.splitlines()
                if line.startswith(f"| {requirement} |")
            ),
            "",
        )
        if not row:
            errors.append(f"SPEC: missing mapping row {requirement}")
        elif ac not in row:
            errors.append(f"SPEC: {requirement} missing {ac}")
        if requirement != "FR-008" and requirement not in plan:
            errors.append(f"PLANS: missing {requirement}")
        if requirement != "FR-008" and ac not in plan:
            errors.append(f"PLANS: missing {ac}")
        if requirement != "FR-008" and not any(
            requirement in line and ac in line for line in stage_mapping_rows
        ):
            errors.append(f"PLANS: no stage row maps {requirement} to {ac}")
        if stage_id := required_new_stages.get(requirement):
            if row and stage_id not in STAGE.findall(row):
                errors.append(f"SPEC: {requirement} missing stage {stage_id}")
            if not any(
                line.startswith(f"| {stage_id} |")
                and requirement in line
                and ac in line
                for line in stage_mapping_rows
            ):
                errors.append(f"PLANS: stage {stage_id} must map {requirement} to {ac}")
        if row and requirement != "FR-008":
            for stage_id in STAGE.findall(row):
                if not any(stage_id in line for line in stage_mapping_rows):
                    errors.append(
                        f"SPEC: {requirement} references missing stage {stage_id}"
                    )
    if {f"P-{i:02d}" for i in range(5)} != set(STAGE.findall(plan)):
        errors.append("PLANS: expected P-00 through P-04 stage IDs")
    if "FR-008" not in spec or "首版推迟" not in spec:
        errors.append("SPEC: deferred FR-008 must remain explicit")
    return errors


def check_current_development_plan(plan: str) -> list[str]:
    """Check only the canonical route table, not repeated IDs in task history."""
    expected = [item for stage in DEVELOPMENT_STAGE_SLICES.values() for item in stage]
    rows = re.findall(r"^\|\s*(\d+\.\d+)\s*\|([^|\n]*)\|", plan, re.MULTILINE)
    actual = [slice_id for slice_id, _label in rows]
    errors = []
    if APPROVED_CONFIGURATION_REVISION not in plan:
        errors.append("PLANS: current development configuration revision missing")
    if actual != expected:
        errors.append(
            "PLANS: six-stage slice table missing, duplicated or out of order"
        )
    labels = dict(zip(DEVELOPMENT_STAGE_SLICES, "一二三四五六", strict=True))
    for slice_id, label in rows:
        stage_label = re.match(r"([一二三四五六])\s*(?:[:：]|$)", label.strip())
        if stage_label is None or stage_label[1] != labels.get(slice_id.split(".")[0]):
            errors.append("PLANS: slice ID and stage label differ")
            break
    return errors


def check_skills(root: Path) -> list[str]:
    errors: list[str] = []
    for name in SKILLS:
        path = root / ".agents" / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing Skill: {name}")
            continue
        content = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            errors.append(f"{name}: invalid YAML frontmatter boundary")
            continue
        fields = dict(re.findall(r"^([a-z_-]+):\s*(.+)$", match.group(1), re.MULTILINE))
        if set(fields) != {"name", "description"} or fields.get("name") != name:
            errors.append(
                f"{name}: frontmatter needs matching name and description only"
            )
        if not fields.get("description") or not re.search(
            r"\bUse (?:for|when)\b", fields["description"]
        ):
            errors.append(f"{name}: description needs a trigger boundary")
        if len(content) > 15000:
            errors.append(f"{name}: Skill is too large for a focused entry point")
    return errors


def check_protocol(
    protocol: dict,
    historical_prompts: str | None = None,
    registered_g_prompts: str | None = None,
    frozen_cases: list[dict] | None = None,
    archived_target: dict | None = None,
) -> list[str]:
    """Validate explicit historical current-3 inputs, never the new authority."""
    errors: list[str] = []
    if (
        not isinstance(protocol, dict)
        or protocol.get("protocol_version") != "current-3"
    ):
        return ["historical validator requires an explicit current-3 protocol"]
    if (
        protocol.get("protocol_version") != "current-3"
        or protocol.get("status") != "frozen_pending_execution"
        or protocol.get("supersedes")
        != "docs/evaluation/archive/CURRENT_EVAL_PROTOCOL_current-2.json"
    ):
        errors.append("protocol must identify current target, pending execution")
    formal, pilot = protocol.get("formal", {}), protocol.get("pilot", {})
    expected = ["B01", "B02", "B03", "G01", "G02", "G03", "O01", "O02", "O03"]
    cases = protocol.get("cases", [])
    if (
        not isinstance(cases, list)
        or [c.get("id") for c in cases if isinstance(c, dict)] != expected
    ):
        errors.append("protocol case IDs/order must be B01-B03, G01-G03, O01-O03")
        return errors
    if pilot != {
        "case_ids": expected[:3],
        "trials_per_case": 1,
        "excluded_from_formal_release": True,
    }:
        errors.append("pilot must be one B trial per category, separate from formal")
    rules = {
        "trials_per_b_case": 3,
        "trials_per_g_case": 1,
        "trials_per_o_case": 1,
        "required_b_full_successes_per_case": 2,
        "required_g_full_successes_total": 2,
        "required_o_full_successes_total": 3,
        "expected_total_trials": 15,
        "aggregate_field_release_threshold": None,
        "all_attempts_retained": True,
    }
    for key, value in rules.items():
        if formal.get(key) != value:
            errors.append(f"formal rule {key} must be {value!r}")
    if archived_target is not None:
        for key in ("cases", "pilot", "formal"):
            if protocol.get(key) != archived_target.get(key):
                errors.append(f"{key}: frozen archived target changed")
    comparison_policy = protocol.get("comparison_policy", {})
    if (
        comparison_policy.get("interpretation")
        != "descriptive_pairing_only_not_causal_improvement"
        or comparison_policy.get("requires_same_case_prompt_and_fields") is not True
        or comparison_policy.get(
            "record_environment_model_budget_scoring_and_source_drift"
        )
        is not True
        or comparison_policy.get("exclude_pilot_from_formal_denominator") is not True
    ):
        errors.append(
            "comparison policy must preserve paired descriptive pilot/formal boundary"
        )
    cohort_policy = protocol.get("cohort_policy", {})
    if (
        cohort_policy.get(
            "pilot_and_formal_each_freeze_code_model_budget_scoring_environment"
        )
        is not True
        or cohort_policy.get("systemic_pilot_failure")
        != "pause_retain_attempts_restart_full_cohort_or_mark_incomparable"
        or cohort_policy.get("formal_fix_requires_new_complete_batch") is not True
        or cohort_policy.get("release_case_latest_version")
        != "verify_official_page_at_each_attempt_start_and_record_drift"
    ):
        errors.append("cohort policy must freeze comparable batches and retain drift")
    semantics = protocol.get("record_semantics", {})
    if semantics.get("persistence_backend_values") != ["postgresql"]:
        errors.append("current target requires PostgreSQL persistence")
    if not all(
        semantics.get(key)
        for key in (
            "pilot_access_checks",
            "formal_access_checks",
            "pilot_outcome",
            "known_call_cost_sum",
            "unknown_call_cost",
            "report_review_binding",
            "project_ledger",
        )
    ):
        errors.append("current-3 evidence semantics are incomplete")
    budget = protocol.get("execution_budget_cny", {})
    if (
        budget.get("pilot_max") != 49
        or budget.get("diagnostic_max") != 30
        or budget.get("formal_max") != 200
        or budget.get("contingency_max") != 20
        or budget.get("new_live_run_total_strictly_below") != 300
        or budget.get("stop_if_cost_cannot_be_bounded") is not True
    ):
        errors.append("execution budget must preserve 49/30/200/20 and strict <300")
    if protocol.get("paid_execution_requires_separate_authorization") is not True:
        errors.append("paid-run authorization boundary missing")
    full_rules = set(protocol.get("full_success_requires", []))
    for rule in (
        "recommendation_has_explicit_conditions_rationale_and_verified_supporting_facts",
        "owner_can_access_and_other_team_member_cannot_access_or_cancel",
        "ui_api_application_persistence_sse_consistent",
        "community_sources_labeled_supplement_only",
    ):
        if rule not in full_rules:
            errors.append(f"full success rule missing {rule}")
    for case in cases:
        case_id = case["id"]
        expected_size = 5 if case_id.endswith("03") else 10
        fields = case.get("required_fields", [])
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{case_id}: empty prompt")
        if len(fields) != expected_size or len(set(fields)) != expected_size:
            errors.append(f"{case_id}: expected {expected_size} unique fields")
        expected_set = {
            "B": "regression",
            "G": "public_generalization",
            "O": "public_preregistered",
        }[case_id[0]]
        if case.get("set") != expected_set:
            errors.append(f"{case_id}: wrong set")
        if case_id == "O03" and case.get("community_supplement_required") is not True:
            errors.append("O03: community supplement requirement missing")
        if historical_prompts is not None and case_id.startswith("B"):
            historical = re.search(
                rf"^\| {case_id} /[^|]*\| “([^”]+)” \|",
                historical_prompts,
                re.MULTILINE,
            )
            if not historical or case.get("prompt") != historical.group(1):
                errors.append(f"{case_id}: prompt differs from historical benchmark")
        if registered_g_prompts is not None and case_id.startswith("G"):
            registered = re.search(rf"{case_id}：“([^”]+)”", registered_g_prompts)
            if not registered or case.get("prompt") != registered.group(1):
                errors.append(f"{case_id}: prompt differs from public preregistration")
        if frozen_cases is not None and case_id[0] in {"B", "G"}:
            old = next(
                (item for item in frozen_cases if item.get("id") == case_id), None
            )
            if old is None or any(
                case.get(field) != old.get(field)
                for field in ("prompt", "required_fields", "set", "category")
            ):
                errors.append(f"{case_id}: frozen prompt or fields changed")
    contract = protocol.get("result_record_contract", {})
    for key in (
        "required_fields",
        "field_review_required_fields",
        "fact_required_fields",
        "call_attempt_required_fields",
        "claim_required_fields",
        "recommendation_review_required_fields",
        "usage_required_fields",
        "community_supplement_required_fields",
        "trace_artifact_required_fields",
        "report_artifact_required_fields",
        "review_bundle_artifact_required_fields",
        "review_bundle_content_required_fields",
        "cost_required_fields",
        "comparison_required_fields",
        "manual_source_review_required_fields",
    ):
        if not contract.get(key):
            errors.append(f"result contract missing {key}")
    required_contract_fields = {
        "field_review_required_fields": {"fact_ids"},
        "fact_required_fields": {
            "fact_id",
            "subject",
            "claim",
            "official_source_url",
            "official_identity_basis",
            "evidence_excerpt",
            "evidence_locator",
            "retrieved_at",
            "machine_admission_status",
            "human_official_review_status",
            "reviewer_id",
            "source_checked_at",
            "contradiction_note",
        },
        "call_attempt_required_fields": {
            "attempt_id",
            "kind",
            "billable",
            "started_at",
            "ended_at",
            "outcome",
            "reported_prompt_tokens",
            "reported_completion_tokens",
            "known_cost_cny",
        },
        "trace_artifact_required_fields": {"relative_path", "sha256"},
        "report_artifact_required_fields": {"relative_path", "sha256"},
        "review_bundle_artifact_required_fields": {"relative_path", "sha256"},
        "review_bundle_content_required_fields": {
            "task_id",
            "run_id",
            "status",
            "stop_reason",
            "facts",
            "raw_record_sha256",
            "trace_sha256",
            "report_sha256",
            "cost",
            "comparison",
            "manual_source_review",
        },
        "cost_required_fields": {
            "currency",
            "known_cost_cny",
            "total_cost_cny",
            "unknown_attempt_count",
            "pricing_basis",
            "price_checked_at",
        },
        "comparison_required_fields": {
            "cohort_id",
            "environment_fingerprint",
            "upstream_browser_fingerprint",
            "dependency_lock_sha256",
            "model_id",
            "budget_fingerprint",
            "scoring_revision",
            "source_window",
            "source_drift",
            "budget_parity",
        },
        "manual_source_review_required_fields": {
            "reviewer_id",
            "reviewed_at",
            "evidence_note",
            "report_sha256",
            "second_review_status",
        },
    }
    for key, needed in required_contract_fields.items():
        if not needed.issubset(set(contract.get(key, []))):
            errors.append(f"result contract {key} missing required evidence fields")
    for key in (
        "community_supplements",
        "report_artifact",
        "facts",
        "call_attempts",
        "raw_record_sha256",
        "trace_artifact",
        "review_bundle_artifact",
        "cost",
        "comparison",
        "manual_source_review",
        "prompt_sha256",
        "persistence_backend",
    ):
        if key not in contract.get("required_fields", []):
            errors.append(f"result contract missing {key}")
    ledger = protocol.get("project_ledger_contract", {})
    if (
        ledger.get("allocations_cny")
        != {"pilot": 49, "diagnostic": 30, "formal": 200, "contingency": 20}
        or ledger.get("total_max_cny") != 299
        or ledger.get("contingency_requires_explicit_authorization") is not True
        or not ledger.get("unbounded_or_unknown_cost_action")
        or not {
            "run_id",
            "task_id",
            "allocation",
            "batch_id",
            "known_cost_cny",
            "total_cost_cny",
            "unknown_attempt_count",
            "evidence_artifact",
            "authorization_reference",
        }.issubset(set(ledger.get("entry_required_fields", [])))
        or not {"batch_id", "phase", "artifact"}.issubset(
            set(ledger.get("batch_required_fields", []))
        )
    ):
        errors.append("project ledger contract is incomplete")
    return errors


def _load_current_json(raw: str | bytes) -> object:
    """Decode current inputs without ambiguous keys or non-finite numbers.

    Errors deliberately omit input content. Historical decoding is unchanged.
    """

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate current JSON member")
            result[key] = value
        return result

    def finite_float(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite current JSON number")
        return number

    def reject_constant(_value: str) -> object:
        raise ValueError("nonstandard current JSON constant")

    return json.loads(
        raw,
        object_pairs_hook=unique_object,
        parse_float=finite_float,
        parse_constant=reject_constant,
    )


def _json_equal(actual: object, expected: object) -> bool:
    """JSON policy values compare types as well as values (True is not 1)."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _json_equal(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _json_equal(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


FOCUS_MEMORY_POLICY = {
    "stage": "deferred",
    "required_for_current_m1": False,
    "automatic_read": False,
    "automatic_write": False,
    "import_or_rebuild": False,
    "request_items": 0,
    "request_bytes": 0,
    "dedicated_extraction_calls": 0,
    "reactivation": "separate_approved_followup_after_real_reuse_need_and_review",
    "reserved_capacity": "unchanged_not_reallocated",
}
FOCUS_MEMORY_OBSERVATION = {
    "state": "disabled",
    "applicability": "not_applicable",
    "hits": None,
    "writes": None,
    "reason": "feature_disabled",
    "active_refs": [],
}


# Independent approved-byte anchors for DEV-STAGES-20261104-01.
# The sole protocol/materials keep their original bytes and preparation revision.
# Change only with a separately approved configuration revision and file review.
# No CLI override or self-rebinding from repository content is provided.
APPROVED_CONFIGURATION_REVISION = "DEV-STAGES-20261104-01"
APPROVED_CURRENT_HASHES = {
    "docs/evaluation/CURRENT_EVAL_PROTOCOL.json": "799178fb431656c00c785634ad53df06b62d660a68291b7fab3719bcf8584eda",
    "docs/evaluation/DISCOVERY_M1_CASES.json": "6c37e4ed40d6592465fa64b87b50bc48ed56f2187d27ae4493687e961afff1c0",
    "docs/evaluation/DECISION_M1_PROTOCOL.json": "a7fd10a0c12fa2ff2a4155fe92f080f33eb48c2003897d350eaa5a7f3d0a1888",
}

# Small, independently checked invariants; full prose is protected by raw hashes.
REVIEW_POLICY = {
    "authorization.configuration_only": True,
    "authorization.business_implementation": False,
    "authorization.environment_or_database_write": False,
    "authorization.dependency_install": False,
    "authorization.model_tokenizer_browser_execution": False,
    "authorization.paid_execution": False,
    "authorization.purchase": False,
    "authorization.git_write": False,
    "authorization.real_run_requires_specific_separate_authorization": True,
    "formal.domain_ids": ["requirements", "consistency", "exploration"],
    "formal.case_ids": ["REQ-A", "REQ-B", "CON-A", "CON-B", "EXP-A", "EXP-B"],
    "formal.expected_attempts": 6,
    "formal.agent_attempts": 3,
    "formal.control_attempts": 3,
    "formal.all_attempts_retained": True,
    "formal.no_replacements": True,
    "formal.version_frozen": True,
    "formal.code_templates_tools_quotas_scoring_frozen": True,
    "formal.revealed_failure_kept_not_replaced_by_optimization_slots": True,
    "formal.independent_author_and_non_author_material_review_required": True,
    "methods.agent.external_ai_repair_allowed": False,
    "methods.agent.deliberate_control_output_or_note_copy_allowed": False,
    "methods.control.independent_deep_research.required": False,
    "methods.control.independent_deep_research.sessions_per_task": 1,
    "methods.control.independent_deep_research.ordinary_browsing_or_thinking_is_not_DR": True,
    "methods.control.independent_deep_research.no_extra_DR_or_regeneration_replacing_failure": True,
    "methods.control.independent_deep_research.same_product_and_mode_all_three": True,
    "methods.manual_search.same_pre_registered_engine_list_both_methods": True,
    "methods.manual_search.switching_allowed": True,
    "methods.manual_search.all_owner_actions_count_active_time": True,
    "methods.contamination.record_familiarity_sources_and_knowledge_transfer": True,
    "methods.contamination.no_true_blinding_claim": True,
    "methods.contamination.memory_disabled_frozen_no_memory_effect_claim": True,
    "timing.active_minutes_per_attempt": 120,
    "timing.wall_hours_per_attempt": 24,
    "timing.batch_days": 14,
    "timing.max_extensions": 1,
    "timing.unrevealed_extension_days": 7,
    "timing.revealed_attempt_extension_allowed": False,
    "assignment.seed_bits": 128,
    "assignment.seed_hex_chars": 32,
    "assignment.no_generation_or_reassignment_after_failure": True,
    "common_quality.all_six_final_reports_pass_before_value_computation": True,
    "common_quality.owner_final_and_original_program_outcomes_separate": True,
    "common_quality.machine_structure_check_is_not_semantic_verification": True,
    "common_quality.audits.max_defect_feedback_rounds": 2,
    "common_quality.audits.final_scoring_rounds": 1,
    "common_quality.audits.owner_does_actual_research_and_rewrite": True,
    "common_quality.raw_agent_critical_passes_required": 3,
    "common_quality.raw_agent_gate_separate_from_human_repaired_final": True,
    "quotas.case_model.normal_obligations": 14,
    "quotas.case_model.technical_retry_max": 2,
    "quotas.case_model.technical_retry_per_work_max": 1,
    "quotas.case_model.physical_calls_max": 16,
    "quotas.case_model.normal_input_total": 360448,
    "quotas.case_model.normal_output_total": 61440,
    "quotas.case_model.with_two_max_retries_input_total": 425984,
    "quotas.case_model.with_two_max_retries_output_total": 77824,
    "quotas.case_model.cumulative_input_tokens": 458752,
    "quotas.case_model.cumulative_output_reservation_tokens": 81920,
    "quotas.case_model.format_repair_extra_calls": 0,
    "quotas.case_model.summary_extra_calls": 0,
    "quotas.case_model.model_call_absolute_seconds": 60,
    "quotas.case_model.sdk_implicit_retries": 0,
    "quotas.tools.per_case.search": 12,
    "quotas.tools.per_case.fetch": 24,
    "quotas.tools.per_case.github_data": 32,
    "quotas.tools.per_case.github_control": 64,
    "quotas.tools.per_case.browser_actions": 0,
    "quotas.tools.per_case.browser_http_requests": 0,
    "quotas.tools.counts_include_failures_retries_redirects_and_all_attempts": True,
    "quotas.tools.search_result_count": 5,
    "quotas.tools.search_need_content": False,
    "quotas.tools.extra_curator_or_semantic_judge_calls": 0,
    "quotas.tools.browser_before_network_qualification": 0,
    "quotas.tools.standalone_control_tasks_max": 4,
    "quotas.tools.standalone_control_attempts_per_task_max": 8,
    "quotas.tools.standalone_control_task_seconds": 60,
    "quotas.tools.private_proof_max_seconds": 300,
    "quotas.runtime.global_active_tasks": 2,
    "quotas.runtime.global_queued_tasks": 4,
    "quotas.runtime.nonterminal_task_per_session": 1,
    "quotas.runtime.tasks_per_case": 8,
    "quotas.runtime.read_branches_per_turn": 2,
    "quotas.runtime.global_read_branches": 4,
    "quotas.runtime.model_physical_inflight": 2,
    "quotas.runtime.qualified_browser_physical_inflight": 0,
    "quotas.runtime.lease_seconds": 30,
    "quotas.runtime.heartbeat_seconds": 5,
    "quotas.runtime.recoveries_per_original_task": 1,
    "quotas.runtime.queue_seconds": 300,
    "quotas.runtime.discussion_seconds": 600,
    "quotas.runtime.research_seconds": 2700,
    "quotas.runtime.case_worker_seconds": 3600,
    "quotas.runtime.ordinary_case_wall_seconds": 604800,
    "quotas.runtime.formal_case_wall_seconds": 86400,
    "quotas.bytes.artifact_max": 1048576,
    "quotas.bytes.turn_max": 67108864,
    "quotas.bytes.case_max_shared_across_turns": 67108864,
    "quotas.bytes.project_new_business_max": 1073741824,
    "quotas.bytes.count_actual_uncompressed_copies": True,
    "quotas.bytes.control_safe_receipt_max_bytes": 2048,
    "quotas.bytes.terminal_and_canonical_reserved_before_call": True,
    "budget.model_physical_calls": 116,
    "budget.search_calls": 84,
    "budget.fetch_calls": 168,
    "budget.github_calls": 704,
    "budget.price_basis.conservative_input_tokens_per_physical_slot": 1048576,
    "budget.price_basis.output_tokens_per_physical_slot": 8192,
    "budget.price_basis.price_evidence_max_age_hours": 24,
    "budget.buffer_not_automatic_grant": True,
    "budget.github_data_calls": 224,
    "budget.github_case_control_calls": 448,
    "budget.github_standalone_control_calls": 32,
    "budget.http_calls_max": 1072,
    "budget.dns_attempts_max": 2144,
    "budget.dial_attempts_max": 1072,
    "tracing.run_manifest_max_bytes": 65536,
    "tracing.canonical_records_not_sampled": True,
    "tracing.ui_ordinary_event_cap": 255,
    "tracing.safe_body_not_full_HTTP_wire": True,
    "tracing.no_hidden_chain_of_thought_collection": True,
    "tracing.model_internal_use_not_inferred_from_output": True,
    "tracing.delivery_limits_bytes.report": 65536,
    "tracing.delivery_limits_bytes.artifact_response": 1048576,
    "tracing.delivery_limits_bytes.SSE_frame": 1024,
    "optimization.real_symptom_correction_required_at_least": 1,
    "optimization.real_retest_slots_max": 2,
    "optimization.keep_all_failed_experiments": True,
    "optimization.failed_rigorous_experiment_not_substitute_for_correction": True,
    "historical_evidence.no_new_archive_copy": True,
    "historical_evidence.new_runner_or_ledger_implemented": False,
    "release.technical_verification_human_acceptance_value_M1_Go_release_separate": True,
    "release.this_protocol_not_runtime_permission": True,
    "quotas.case_model.compile_reserve_borrowable": False,
    "quotas.case_model.hidden_judge_extra_calls": 0,
    "protocol_version": "draft-m1-3",
    "preparation_revision": "RESEARCH-BASELINE-20261103",
    "registered_at": "2026-11-03",
    "quotas.case_model.compile_physical_calls_max": 4,
    "quotas.case_model.compile_limit_includes_technical_retries": True,
}

PURPOSE_LIMITS = {
    "clarify": (8192, 2048),
    "research_plan": (16384, 2048),
    "extract": (32768, 4096),
    "evidence_review": (32768, 3072),
    "gap_plan": (16384, 2048),
    "document_compile": (32768, 8192),
}

PURPOSE_MAPPING = {
    "clarify": "organize_human_conditions_and_propose_questions",
    "research_plan": "decompose_questions_assign_work_dependencies_and_acquisition_plan",
    "extract": "source_to_claim_evidence_counterevidence_proposals",
    "evidence_review": "compare_evidence_conflicts_grounded_parent_child_merge_and_question_bound_discussion_or_child_proposal",
    "gap_plan": "evidence_gap_driven_next_work_or_stop",
    "document_compile": "create_or_revise_formal_requirements_solution_or_review_DocumentVersion",
}

REVIEW_CAPABILITIES = [
    {
        "id": "runtime_harness",
        "requirements": ["DEC-AC-08", "DEC-AC-09", "DEC-AC-13", "DEC-AC-14"],
        "tasks": ["DEC-M1-02", "DEC-M1-03b"],
        "evidence": [
            "real_LangGraph_stage_nodes",
            "restricted_Pg_atomicity_and_dual_order_races",
            "stable_obligations_no_completed_unknown_resend",
            "unique_terminal_and_generation_resource_release",
            "immutable_document_versions_current_head_exact_confirmation_dual_order_solution_gates",
            "first_artifact_multidimensional_reservation_no_unsavable_send",
            "same_Task_bounded_nonrecursive_assignment_CAS_and_idempotent_creation",
            "shared_acquisition_per_consumer_authorization_cancel_late_result_and_sealed_research_inputs",
            "shared_14_normal_16_physical_pool_four_physical_compiles_including_retry_first_attempt_only_reservation",
            "full_flow_partial_human_edit_confirmation_linked_Turn_separate_seals_exact_double_draft_package",
            "project_designated_exact_confirmation_policy_account_member_revisions_and_no_approval_revival",
            "single_chain_real_engineering_acceptance_before_dynamic_reintegration_dynamic_still_required",
        ],
    },
    {
        "id": "tools_search_evidence",
        "requirements": ["DEC-AC-10", "DEC-AC-11", "DEC-AC-12", "DEC-AC-15"],
        "tasks": ["DEC-M1-03a", "DEC-M1-03b", "DEC-M1-05"],
        "evidence": [
            "question_basis_source_claim_report_chain",
            "repo_ID_commit_path_blob_UTF8_capture_and_counterevidence",
            "App_installation_proof_and_public_query_disclosure_boundaries",
            "Browser_deferred_zero_not_automatically_complete",
            "bounded_explicit_local_text_code_diff_source_set_and_private_lineage",
        ],
    },
    {
        "id": "context",
        "requirements": ["DEC-AC-18"],
        "tasks": ["DEC-M1-03a", "DEC-M1-03b"],
        "evidence": [
            "protected_conditions_qualifiers_counterevidence",
            "bounded_manifest_selection_and_failure_diagnostics",
            "official_complete_request_tokenizer_qualification",
            "fixed_source_offline_cases_and_natural_authorized_trace_not_extra_call_batch",
            "actual_parent_child_request_preserves_conditions_counterevidence_qualifiers_unknown_and_manifest_match",
            "separate_fixed_local_public_format_hosted_fit_and_original_usage_fee_qualification",
            "legal_token_delta_overflow_protocol_error_business_schema_and_unknown_fee_negative_paths",
        ],
    },
    {
        "id": "tracing_engineering_diagnostics",
        "requirements": ["DEC-AC-13", "DEC-AC-19"],
        "tasks": ["DEC-M1-03b", "DEC-M1-08b"],
        "evidence": [
            "canonical_trace_and_offline_no_send_reconstruction",
            "all_failed_experiments_and_confounding_retained",
            "confirmed_real_defects_addressed_without_requiring_a_manufactured_symptom",
            "actual_request_usage_cost_and_output_version_bindings",
        ],
    },
    {
        "id": "identity_recovery_practice",
        "requirements": ["DEC-AC-15", "DEC-AC-14"],
        "tasks": ["DEC-M1-01", "ENV-M1-01", "ENV-M1-02", "DEC-M1-03b", "DEC-M1-08b"],
        "evidence": [
            "one_real_owner_second_test_identity_object_isolation",
            "continuous_supervisor_identity_qualification",
            "paper_key_independent_source_card_real_restore",
            "owner_actual_key_business_acceptance_and_success_failure_operation_demonstration",
            "controlled_unchanged_data_restart_trusted_operator_no_restore_attestation_not_independent_freshness",
            "all_nonterminal_tasks_and_unsent_reservations_closed_physical_quiescence_known_fees_final_shutdown_receipt",
            "new_CLI_then_explicit_CONTROL_ONLY_current_qualification_then_new_research_grant_idempotent_no_old_grant_revival",
            "abnormal_or_suspected_restore_stays_isolated_unknown_not_cleared_original_Case_caps_deadlines_and_memory_disabled",
            "controlled_rearm_offline_restricted_Pg_and_paid_disabled_process_checks_before_first_public_pilot",
            "local_operator_project_roles_requester_writer_designated_confirmer_no_research_grant",
            "per_eligibility_and_per_confirmation_3072_byte_invalidation_reserves_full_capacity_revoke_then_disable",
            "deny_only_confirmation_revoke_without_source_proof_refresh_or_research_time",
            "same_human_formal_requester_confirmer_cross_identity_tests_not_team_value",
        ],
    },
]
REVIEW_DEFERRED_CAPABILITIES = [
    {
        "id": "automatic_memory",
        "requirements": [
            "DEC-AC-17",
        ],
        "tasks": [
            "DEC-M1-04",
        ],
        "evidence": [
            "owner_original_long_term_preference_admission",
            "report_source_cues_reverify_each_case",
            "expiry_revoke_lineage_conflict_capacity_and_dual_order_send_tests",
            "natural_qualified_report_seeds_no_hidden_setup_call",
            "restore_derived_new_IDs_cannot_revive_old_memory",
        ],
        "required": False,
        "status": "pending_not_completed",
        "reactivation": "separate_approved_followup_after_real_reuse_need_and_review",
    },
]
REVIEW_COVERAGE_POLICY = {
    "single_real_human_owner_plus_second_test_identity": True,
    "MCP_real_integration_required": False,
    "old_9_8_12_independent_execution_batch_required": False,
    "no_additional_setup_or_judge_calls_without_budget_and_authorization": True,
    "browser_not_qualified": "zero_and_capability_pending_not_automatically_completed",
    "formal_materials": "on_demand_independent_preparation; pending_not_blocking_engineering",
    "drafting_modes": "three_pairs_full_review_solution; requirements_only_and_edit_revision_pilot_regression_not_independent_formal_effect",
    "memory": "disabled_all_entrypoints_no_store_snapshot_or_seed_required; deferred_not_completed",
    "private_sources": "required_for_engineering_M1_after_public_real_integration; real_test_uses_existing_requirements_only_pilot",
    "automatic_memory": "deferred_not_required_for_current_M1; reactivation_requires_real_reuse_need_separate_review_and_scope_approval",
}


# Independent semantic policy; never derived from the bundle being validated.
TEAM_DELIVERY_CONTRACT = {
    "configuration_revision": "DEV-STAGES-20261104-01",
    "deployment": {
        "origin": "http://127.0.0.1:8766",
        "accounts_max": 2,
        "project_administration": "explicit_local_operator_CLI",
        "admin_web_UI": False,
        "runtime": "independent_product_API_Worker_Pg_real_LangGraph_no_legacy_AgentLoop",
    },
    "roles": {
        "accept_edit_cancel_continue": "requester",
        "confirm_and_revoke": "single_project_designated_confirmer",
        "requester_may_be_designated_confirmer": True,
        "confirmation_grants_task_budget_or_source_authority": False,
        "private_Draft_automatically_shared": False,
        "CLI_checks": [
            "operator_authority",
            "supervisor_generation",
            "root_lock",
            "shutdown_receipt_and_pending_rearm_invalidation",
        ],
    },
    "confirmation": {
        "binds": [
            "requirements_version",
            "requirements_hash",
            "actor",
            "project_policy_revision",
            "account_approval_eligibility_revision",
            "membership_revision",
        ],
        "invalidated_by": [
            "new_requirements_head",
            "project_confirmer_change",
            "membership_removal",
            "account_disable",
            "explicit_confirmation_revoke",
        ],
        "not_invalidated_by_alone": [
            "logout",
            "auth_session_expiry",
            "credential_rotation",
        ],
        "old_approval_revival_after_swapback_rejoin_reenable": False,
        "no_eligible_confirmer_blocks": [
            "solution_start",
            "solution_send",
            "solution_commit",
        ],
        "requirements_drafting_and_review_without_confirmer": True,
        "solution_checks": ["start", "send_claim", "commit"],
        "earlier_valid_claim_may_remain_inflight": True,
        "late_invalidated_result": "original_Call_permitted_audit_usage_cost_only",
        "reconfirmation": "requester_explicit_linkedTurn_no_old_Task_revival_or_Case_cap_deadline_reset",
        "effective_same_confirmation": "reuse_current_no_duplicate_confirmation_row",
        "revoke_requires": [
            "current_authenticated_designated_confirmer",
            "current_project_Case_authority",
            "expected_confirmation_and_head",
            "operation_body_binding",
        ],
        "revoke_requires_source_body_or_private_proof_refresh": False,
        "revoke_requires_research_grant_or_remaining_research_time": False,
    },
    "safety_reserve": {
        "owners": [
            "Account_approval_eligibility",
            "Membership_eligibility",
            "ProjectApprovalPolicy_eligibility",
            "current_RequirementsConfirmation",
        ],
        "receipt_max_bytes": 2048,
        "event_max_bytes": 1024,
        "next_invalidation_reserve_bytes": 3072,
        "bytes_basis": "actual_persisted_UTF8_envelopes",
        "eligibility_bucket": "existing_non_Case_safety_metadata",
        "confirmation_bucket": "existing_Case_canonical_metadata_and_Case_total",
        "reserve_before_create_activate_or_reconfirm": True,
        "ordinary_creation_bytes_separately_accounted": True,
        "mandatory_invalidation_uses_own_reserve": True,
        "ordinary_full_capacity_blocks_mandatory_invalidation": False,
        "borrow_other_object_reserve": False,
        "increase_pool_or_borrow_disabled_Memory": False,
        "same_operation_same_body": "replay_original_receipt_no_new_bytes",
        "same_operation_different_body": "409",
        "unchanged_policy_new_operation": "no_revision_advance_ordinary_receipt_capacity_or_reject",
        "cleanup": "bounded_root_transaction_permanently_noncurrent_only_exactly_once",
        "temporary_source_unavailability_allows_cleanup": False,
    },
    "delivery": {
        "sequence": [
            "ENV-M1-01",
            "DEC-M1-01",
            "DEC-M1-02-A",
            "DEC-M1-02-B",
            "DEC-M1-02-C-single-core",
            "DEC-M1-03a-offline",
            "ENV-M1-02-and-DEC-M1-03b-qualification",
            "first_public_full_flow_pilot",
            "DEC-M1-02-C-dynamic-reintegration",
            "private_App_sources",
            "second_original_requirements_only_pilot_private_engineering_acceptance",
            "full_restore_engineering_delivery_and_human_acceptance",
        ],
        "first_real_pilot_requires": [
            "single_chain_production_safety_kernel",
            "four_mode_offline_integration",
            "minimum_independent_media_paper_key_real_restore",
            "Gateway_Token_funds_source_qualification",
            "controlled_rearm_offline_restrictedPg_paid_disabled_process_acceptance",
            "exact_real_execution_authorization",
        ],
        "dynamic_and_private_sources_required_for_full_M1": True,
        "single_chain_preview_closes_dynamic_parent_AC": False,
        "fake_and_real_share_application_admission_path": True,
        "pilot_checks": [
            "exact_original_slot_and_mode",
            "actual_request_usage_fee_trace",
            "current_authority_and_immutable_output_bindings",
            "key_business_operation_acceptance",
            "no_effect_score_or_comparison_gate",
        ],
        "new_Case_call_funding_or_deadline_allocation": False,
    },
    "formal_and_value": {
        "same_actual_human_account_may_request_and_confirm": True,
        "cross_identity_qualification": "restrictedPg_and_UI_not_extra_formal_slots_or_team_value",
        "sole_protocol_bytes_changed": False,
        "real_team_and_task_evidence": "pending",
        "technical_verification_human_acceptance_mastery_value_M1_Go_release_separate": True,
    },
}

# Approved P0 delivery policy; immutable semantic expectations, not read from the bundle.
DEVELOPMENT_STAGE_SLICES = {
    "1": ["1.1", "1.2", "1.3"],
    "2": ["2.1", "2.2", "2.3", "2.4"],
    "3": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"],
    "4": ["4.1", "4.2", "4.3", "4.4", "4.5"],
    "5": ["5.1", "5.2", "5.3", "5.4"],
    "6": ["6.1", "6.2", "6.3"],
}
DEVELOPMENT_DELIVERY_POLICY = {
    "configuration_revision": "DEV-STAGES-20261104-01",
    "route_authority": "PLANS.md",
    "progress_authority": "docs/features/DECISION-001/tasks.md",
    "preparation_slice": "P0",
    "preparation_counts_as_development_stage": False,
    "stage_count": 6,
    "slice_count": 26,
    "stage_slice_ids": {
        "1": ["1.1", "1.2", "1.3"],
        "2": ["2.1", "2.2", "2.3", "2.4"],
        "3": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"],
        "4": ["4.1", "4.2", "4.3", "4.4", "4.5"],
        "5": ["5.1", "5.2", "5.3", "5.4"],
        "6": ["6.1", "6.2", "6.3"],
    },
    "stage_start": "explicit_owner_instruction_after_previous_stage_merge; "
    "resume_first_unfinished_slice",
    "slice_sequence": [
        "verify_baseline_and_exact_authority",
        "implement",
        "risk_proportionate_tests",
        "independent_review_and_applicable_security_review",
        "validate_findings_fix_retest_and_affected_rereview",
        "reviewable_owner_acceptance_package",
        "actual_owner_acceptance_and_exact_commit_push_PR_authority",
        "commit_push_create_or_update_same_stage_PR",
        "required_CI_pass",
        "automatically_start_next_slice_in_same_stage",
    ],
    "stage_branch_pattern": "codex/stage-N-*",
    "PRs_per_stage": 1,
    "first_slice_PR": "draft",
    "normal_commits_per_slice": 1,
    "CI_fix_commits": "same_slice; "
    "affected_review_acceptance_and_exact_Git_authority_before_changed_content_submission",
    "stage_merge_requires_separate_owner_authority": True,
    "next_stage_starts_automatically": False,
    "stage_start_grants_environment_paid_or_external_operations": False,
    "existing_exact_authority": "reuse_while_applicable; "
    "do_not_request_generic_continuation",
    "required_engineering_checks": [
        "normal_boundary_failure_and_relevant_regression",
        "real_restricted_Pg_independent_connection_races_for_transaction_or_permission_changes",
        "real_process_evidence_for_process_behavior",
        "independent_review_and_applicable_security_review",
        "mandatory_skipped_or_missing_checks_leave_slice_unaccepted",
        "actual_owner_key_business_acceptance",
        "first_exposure_response_page_SSE_current_read_authorization",
    ],
    "post_integration_slices_defer_earlier_core_safety_tests": False,
    "qualification_after_affected_changes": "reverify_request_Token_permission_and_restore_before_real_calls; "
    "retain_original_diagnostic_allocation",
    "minimum_restore_before_private_real_test": "latest_applicable_schema_and_capture; "
    "not_deferred_to_stage_6",
    "insufficient_diagnostic_or_real_allocation": "outbound_closed_and_affected_AC_pending; "
    "no_automatic_regrant",
    "engineering_completion_label": "M1工程能力验收通过",
    "separate_conclusions": [
        "implementation",
        "technical_verification",
        "independent_review",
        "human_business_acceptance",
        "engineering_M1",
        "raw_quality",
        "owner_mastery",
        "real_value",
        "Go",
        "release",
    ],
}
ON_DEMAND_EVALUATION_POLICY = {
    "trigger": "explicit_owner_request_and_exact_operation_authority",
    "blocks_engineering_acceptance": False,
    "unexecuted_status": "not_evaluated_not_passed",
    "packages": [
        {
            "id": "real_task_effect_observation",
            "evidence": [
                "original_quality",
                "owner_verification_and_repair_burden",
                "actual_use",
            ],
        },
        {
            "id": "matched_real_defect_retest",
            "tasks": ["DEC-M1-06"],
            "requirements": ["DEC-AC-20"],
            "evidence": ["at_least_one_real_symptom_corrected_with_matched_evidence"],
        },
        {
            "id": "formal_six_slot_evaluation",
            "tasks": ["DEC-M1-07"],
            "requirements": ["DEC-AC-16", "DEC-AC-19"],
            "evidence": [
                "complete_six_attempts_and_manual_time_final_quality",
                "all_three_raw_Agent_reports_critical_quality_pass",
                "six_final_human_reports_and_descriptive_time_comparison_no_20pct_gate",
                "display_permission_and_actual_display_separate",
            ],
        },
    ],
    "when_started": "sole_protocol_quality_timing_failure_retention_and_correction_rules_apply",
    "engineering_real_test_slots": [
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
    ],
    "engineering_real_tests_require_effect_score_or_comparison": False,
    "new_pilot_Case_call_funding_or_deadline_allocation": False,
    "optional_effect_runs_automatically_receive_new_pilot_slots": False,
    "all_existing_resource_and_funds_limits_remain_applicable": True,
    "confirmed_real_defects": "must_address_within_approved_scope; "
    "do_not_manufacture_a_defect_or_require_one_for_engineering_completion",
}

MATERIAL_INDEX_PATH = "docs/evaluation/DISCOVERY_M1_CASES.json"
MATERIAL_ROOT = ".tmp/predev-reopen-20261028/config-20261029/review-20261101/research-20261103/materials"
MATERIAL_ROLES = ("inputs", "controller", "scorer")
REVIEW_CASE_PAIRS = {
    "requirements": ["REQ-A", "REQ-B"],
    "consistency": ["CON-A", "CON-B"],
    "exploration": ["EXP-A", "EXP-B"],
}
REVIEW_CASE_IDS = tuple(cid for pair in REVIEW_CASE_PAIRS.values() for cid in pair)
PUBLIC_RUBRIC = [
    "all_critical_claims_correct_and_supported",
    "no_missing_critical_conflicts_or_qualifiers",
    "explicit_unknown_unread_and_scope",
    "no_fabricated_execution_or_authority",
    "actionable_conditional_next_verification",
]
FORMAL_WORKFLOWS = {
    "requirements": {
        "mode": "requirements_to_solution",
        "artifacts": [
            "first_raw_requirements",
            "exact_human_confirmation_and_edits",
            "first_raw_solution",
            "final_requirements_solution_package",
        ],
        "coverage": [
            "ideas_without_repository_allowed",
            "same_preregistered_goal_no_scope_shrink",
        ],
    },
    "consistency": {
        "mode": "review_only",
        "artifacts": ["first_raw_review", "final_review_package"],
        "coverage": [
            "fixed_commit_and_local_text_code_diff",
            "both_variants_include_bounded_question_without_authoritative_baseline",
            "observations_hypotheses_not_invented_conformance",
        ],
    },
    "exploration": {
        "mode": "solution_only",
        "artifacts": [
            "confirmed_existing_requirements",
            "first_raw_solution",
            "final_solution_package",
        ],
        "coverage": ["bounded_evidence_and_implementation_assumption_exploration"],
    },
}
COVERAGE_LIMITS = {
    "requirements_only": "focused_route_terminal_regression_and_one_existing_pilot; "
    "no_independent_formal_quality_or_time_claim",
    "editing_and_revision": "regression_and_pilot_only_no_independent_formal_effect_claim",
    "pair_equivalence": "same_preregistered_goal_scale_material_format_mix; "
    "clarify_cannot_shrink_goal; "
    "substantive_scope_change_retains_slot_partial_noncomparable",
    "alternative_designs": "reasonable_supported_alternatives_allowed_no_single_hidden_design_answer",
    "pilot_allocation": "one_existing_pilot_requirements_only_and_other_full_chain; "
    "no_extra_cases_or_funding",
}
MATERIAL_BYTES_MAX = 1048576


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: object, *, empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (empty or bool(value))
        and all(_nonempty_text(item) for item in value)
    )


def _check_draft_reservations(protocol: dict) -> list[str]:
    """Structural arithmetic only; no runtime execution or real fee qualification."""
    try:
        model = protocol["quotas"]["case_model"]
        stages = model["stages"]
        if (
            not isinstance(stages, list)
            or len(stages) != len(PURPOSE_LIMITS)
            or any(
                not isinstance(s, dict)
                or set(s) != {"id", "max_input_tokens", "max_output_tokens"}
                for s in stages
            )
            or [s["id"] for s in stages] != list(PURPOSE_LIMITS)
            or any(
                not _json_equal(
                    [s["max_input_tokens"], s["max_output_tokens"]],
                    list(PURPOSE_LIMITS[s["id"]]),
                )
                for s in stages
            )
        ):
            return ["draft purpose limits must not restore fixed per-purpose counts"]
        reserve = model["first_attempt_reservation"]
        expected = {
            "eligibility": "first_artifact_whose_first_attempt_has_not_been_sent",
            "normal_calls_per_artifact": 1,
            "input_tokens_per_artifact": 32768,
            "output_tokens_per_artifact": 8192,
            "version_slots_per_artifact": 1,
            "document_envelope_bytes_per_artifact": 81920,
            "canonical_terminal_capacity_required": True,
            "borrowable_by_optional_work": False,
            "refund_or_regrant_after_sent_failure": False,
            "guarantees_success": False,
        }
        mode_counts = {
            "review_only": 1,
            "requirements_only": 1,
            "solution_only": 1,
            "requirements_to_solution": 2,
        }
        documents = protocol["documents"]
        valid = (
            _json_equal(reserve, expected)
            and _json_equal(
                model["mode_obligations"],
                {k: {"first_artifacts": v} for k, v in mode_counts.items()},
            )
            and model["normal_allocation"]
            == "shared_case_pool_no_fixed_per_purpose_counts"
            and _json_equal(model["purpose_mapping"], PURPOSE_MAPPING)
            and not any(
                k in model
                for k in (
                    "compile_reserved_input_tokens",
                    "compile_reserved_output_tokens",
                )
            )
            and model["normal_obligations"] + model["technical_retry_max"]
            == model["physical_calls_max"]
            and model["normal_input_total"]
            + model["technical_retry_max"] * max(s["max_input_tokens"] for s in stages)
            == model["with_two_max_retries_input_total"]
            <= model["cumulative_input_tokens"]
            and model["normal_output_total"]
            + model["technical_retry_max"] * max(s["max_output_tokens"] for s in stages)
            == model["with_two_max_retries_output_total"]
            <= model["cumulative_output_reservation_tokens"]
            and documents["first_full_chain_reserve_slots"]
            * (documents["body_bytes"] + documents["metadata_bytes"])
            == documents["first_full_chain_reserve_bytes"]
            and documents["body_bytes"] + documents["metadata_bytes"]
            == reserve["document_envelope_bytes_per_artifact"]
        )
        return (
            []
            if valid
            else ["draft reservation arithmetic or first-attempt policy mismatch"]
        )
    except (KeyError, TypeError, ValueError, StopIteration, AttributeError):
        return ["draft reservation arithmetic malformed"]


def check_current_policy(protocol: object) -> list[str]:
    """Pure structural/invariant checks for synthetic fixtures, not bundle approval."""
    if not isinstance(protocol, dict):
        return ["current protocol must be an object"]
    errors: list[str] = []
    for path, expected in REVIEW_POLICY.items():
        actual: object = protocol
        for key in path.split("."):
            if not isinstance(actual, dict) or key not in actual:
                errors.append(f"current protocol missing {path}")
                break
            actual = actual[key]
        else:
            if not _json_equal(actual, expected):
                errors.append(f"current protocol policy differs: {path}")
    if not _json_equal(protocol.get("memory"), FOCUS_MEMORY_POLICY):
        errors.append(
            "current Memory policy must disable all entrypoints with exact fields"
        )
    observation = protocol.get("attempt_record_contract", {})
    if not isinstance(observation, dict) or not _json_equal(
        observation.get("memory_observation"), FOCUS_MEMORY_OBSERVATION
    ):
        errors.append(
            "current memory_observation must record disabled, not fake zeroes"
        )
    errors.extend(_check_draft_reservations(protocol))
    errors.extend(_check_resource_arithmetic(protocol))
    try:
        model = protocol["quotas"]["case_model"]
        token = model["token_qualification"]
        fit = token["hosted_fit"]
        local = token["local_format"]
        fee = token["usage_and_fees"]
        if (
            local["count_kind"]
            != "exact_complete_public_format_not_remote_token_or_billing_identity"
            or fit["meaning"]
            != "engineering_estimated_fit_not_zero_overflow_or_all_inputs_proof"
            or fit["legal_nonzero_local_delta"]
            != "record_original_counts_methods_versions_and_delta_continue_only_if_all_other_gates_pass; no_offset_learning_or_limit_expansion"
            or fit["business_output_schema_failure"]
            != "unusable_output_no_extra_repair_call_not_provider_protocol_revocation"
            or not _json_equal(
                fit["revoke_on"],
                [
                    "explicit_context_overflow",
                    "provider_prompt_plus_requested_output_exceeds_context",
                    "completion_exceeds_requested_output",
                    "unsupported_model_mapping",
                    "invalid_provider_protocol_schema",
                ],
            )
            or fee["unknown"]
            != "retain_original_call_reserve_stop_all_project_new_outbound; no_resend"
        ):
            errors.append(
                "Token layers, drift, revocation or unknown-fee policy differs"
            )
        tools = protocol["quotas"]["tools"]
        if any(
            k in tools
            for k in (
                "routes_max",
                "candidate_identity_pool_max",
                "shortlist_max",
                "stage_allocations",
            )
        ):
            errors.append(
                "current document review cannot restore candidate selection quotas"
            )
    except (KeyError, TypeError, AttributeError):
        errors.append("Token or tool policy malformed")
    return errors


def _check_resource_arithmetic(protocol: dict) -> list[str]:
    """Independent declared-cap arithmetic; not observed usage or a funds grant."""
    try:
        budget = protocol["budget"]
        model = protocol["quotas"]["case_model"]
        price = budget["price_basis"]
        worst = (
            Decimal(price["conservative_input_tokens_per_physical_slot"])
            * Decimal(price["model_input_uncached_per_million_cny"])
            + Decimal(price["output_tokens_per_physical_slot"])
            * Decimal(price["model_output_per_million_cny"])
        ) / Decimal(1000000)
        valid = (
            sum(b["model_calls"] for b in budget["batches"])
            == budget["model_physical_calls"]
            and budget["model_physical_calls"] == 7 * model["physical_calls_max"] + 4
            and budget["github_calls"]
            == budget["github_data_calls"]
            + budget["github_case_control_calls"]
            + budget["github_standalone_control_calls"]
            and budget["http_calls_max"]
            == sum(
                budget[k]
                for k in (
                    "model_physical_calls",
                    "search_calls",
                    "fetch_calls",
                    "github_calls",
                )
            )
            and sum(
                Decimal(v)
                for v in protocol["quotas"]["bytes"]["case_buckets_mib"].values()
            )
            == Decimal(64)
            and worst
            == Decimal(price["calculated_worst_model_call_cny"])
            <= Decimal(budget["reserve_per_model_call_cny"])
            and Decimal(budget["model_total_cny"])
            == budget["model_physical_calls"]
            * Decimal(budget["reserve_per_model_call_cny"])
            and Decimal(budget["api_tools_cny"])
            == (budget["search_calls"] + budget["fetch_calls"])
            * Decimal(budget["search_fetch_per_success_cny"])
            and sum(
                Decimal(budget[k])
                for k in (
                    "model_total_cny",
                    "api_tools_cny",
                    "noncall_cny",
                    "unallocated_buffer_cny",
                )
            )
            == Decimal(budget["planned_total_cny"])
            < Decimal(budget["new_spend_strictly_below_cny"])
        )
        return [] if valid else ["current resource or budget arithmetic mismatch"]
    except (KeyError, TypeError, ValueError, AttributeError, InvalidOperation):
        return ["current resource or budget arithmetic malformed"]


def _read_current_bundle(
    root: Path,
) -> tuple[dict[str, bytes], dict[str, object], list[str]]:
    """Capture each bounded file once; hash, parse and chain use these exact bytes."""
    raw: dict[str, bytes] = {}
    parsed: dict[str, object] = {}
    errors: list[str] = []
    for relative, expected in APPROVED_CURRENT_HASHES.items():
        try:
            data = _read_material_bytes(root, root / relative)
            raw[relative] = data
            if hashlib.sha256(data).hexdigest() != expected:
                errors.append(f"current approved raw SHA-256 mismatch: {relative}")
            parsed[relative] = _load_current_json(data)
        except (OSError, ValueError, TypeError, KeyError):
            errors.append(f"current bundle unreadable: {relative}")
    return raw, parsed, errors


def _check_current_bundle(
    raw: dict[str, bytes], parsed: dict[str, object]
) -> list[str]:
    """Validate the captured snapshot; never reread a file for chain comparison."""
    try:
        protocol = parsed[PROTOCOL]
        index = parsed[MATERIAL_INDEX_PATH]
        supplement = parsed["docs/evaluation/DECISION_M1_PROTOCOL.json"]
    except KeyError:
        return ["current bundle incomplete"]
    errors = check_current_policy(protocol)
    errors.extend(check_current_materials(index))
    errors.extend(check_current_supplement(supplement, raw[PROTOCOL]))
    if not isinstance(protocol, dict) or not isinstance(index, dict):
        return errors + ["current bundle chain malformed"]
    ref = protocol.get("materials")
    if (
        not isinstance(ref, dict)
        or ref.get("path") != MATERIAL_INDEX_PATH
        or ref.get("sha256") != hashlib.sha256(raw[MATERIAL_INDEX_PATH]).hexdigest()
        or ref.get("review_status") != index.get("status")
    ):
        errors.append("current material SHA-256 or status reference mismatch")
    return errors


def check_current_protocol(protocol: object, root: Path) -> list[str]:
    """Approved bundle check. A supplied dict must match its captured raw bytes."""
    raw, parsed, errors = _read_current_bundle(root)
    diagnostic_fields_trusted = not errors
    errors.extend(_check_current_bundle(raw, parsed))
    if protocol is not None and not _json_equal(protocol, parsed.get(PROTOCOL)):
        errors.append("current supplied object differs from captured raw bytes")
        if diagnostic_fields_trusted:
            errors.extend(_changed_policy_paths(protocol, parsed.get(PROTOCOL)))
        # Structural diagnostics are useful, but cannot replace raw approval.
        errors.extend(check_current_policy(protocol))
    return errors


def _changed_policy_paths(
    actual: object, approved: object, prefix: str = ""
) -> list[str]:
    """Report approved field names only; never echo changed values or new keys."""
    if _json_equal(actual, approved):
        return []
    if isinstance(approved, dict) and isinstance(actual, dict):
        paths: list[str] = []
        for key, value in approved.items():
            location = f"{prefix}.{key}" if prefix else key
            paths.extend(_changed_policy_paths(actual.get(key), value, location))
        if set(actual) - set(approved):
            paths.append(
                f"current policy differs: {prefix or 'protocol'}.unsupported_fields"
            )
        return paths
    return [f"current policy differs: {prefix or 'protocol'}"]


def check_current_materials(materials: object) -> list[str]:
    try:
        return _check_current_materials(materials)
    except (KeyError, TypeError, ValueError, AttributeError):
        return ["current material index malformed nested types"]


def _check_current_materials(materials: object) -> list[str]:
    """Public index only: no prompt, gold, hidden source locator or arbitrary fields."""
    if not isinstance(materials, dict):
        return ["current materials must be an object"]
    expected_keys = {
        "schema_version",
        "protocol_version",
        "status",
        "pairs",
        "public_rubric_version",
        "public_rubric",
        "packages",
        "review_receipt",
        "readiness",
        "coverage_limits",
    }
    errors: list[str] = []
    if set(materials) != expected_keys:
        errors.append("current material index unsupported fields or scorer leakage")
    for key, expected in {
        "schema_version": "draft-m1-material-index-1",
        "protocol_version": "draft-m1-3",
        "pairs": [
            {"id": k, "case_ids": v, "workflow": FORMAL_WORKFLOWS[k]}
            for k, v in REVIEW_CASE_PAIRS.items()
        ],
        "coverage_limits": COVERAGE_LIMITS,
        "public_rubric_version": "draft-quality-1",
        "public_rubric": PUBLIC_RUBRIC,
        "readiness": {
            "executed": False,
            "formal_seed": None,
            "formal_attempts": 0,
            "provider_calls": 0,
        },
    }.items():
        if not _json_equal(materials.get(key), expected):
            errors.append(f"current material index policy differs: {key}")
    state = materials.get("status")
    if state not in ("pending_independent_material_preparation", "frozen_reviewed"):
        errors.append("current material index status invalid")
    packages = materials.get("packages")
    if not isinstance(packages, list) or len(packages) != 3:
        return errors + ["current material index requires three role bindings"]
    for role, item in zip(MATERIAL_ROLES, packages, strict=True):
        if not isinstance(item, dict) or set(item) != {
            "role",
            "relative_ref",
            "schema_version",
            "sha256",
            "bytes",
        }:
            errors.append("current material role binding malformed")
            continue
        if any(
            not _json_equal(item.get(k), v)
            for k, v in {
                "role": role,
                "relative_ref": f"{MATERIAL_ROOT}/{role}.json",
                "schema_version": f"draft-m1-{role}-1",
            }.items()
        ):
            errors.append("current material role path or identity invalid")
        if state == "pending_independent_material_preparation":
            if item.get("sha256") is not None or item.get("bytes") is not None:
                errors.append("pending materials cannot claim package identities")
        elif (
            not _is_sha256(item.get("sha256"))
            or type(item.get("bytes")) is not int
            or not 0 < item["bytes"] <= MATERIAL_BYTES_MAX
        ):
            errors.append("frozen materials require bounded raw package identity")
    if state == "pending_independent_material_preparation":
        if materials.get("review_receipt") is not None:
            errors.append("pending materials cannot claim independent review")
    elif not _valid_review_receipt(materials.get("review_receipt"), packages):
        errors.append("current material independent review receipt invalid")
    return errors


def _valid_review_receipt(receipt: object, packages: list[object]) -> bool:
    if not isinstance(receipt, dict) or set(receipt) != {
        "report",
        "rereview_report",
        "reviewer_context",
        "reviewer_role",
        "package_sha256",
    }:
        return False
    if (
        not _nonempty_text(receipt["reviewer_context"])
        or receipt["reviewer_role"] != "independent_non_author_material_reviewer"
    ):
        return False
    expected = {
        item["role"]: item["sha256"]
        for item in packages
        if isinstance(item, dict) and item.get("role") in MATERIAL_ROLES
    }
    if not _json_equal(receipt["package_sha256"], expected):
        return False
    for key, filename in (
        ("report", "materials-review.json"),
        ("rereview_report", "materials-rereview.json"),
    ):
        value = receipt[key]
        if key == "rereview_report" and value is None:
            continue
        if not isinstance(value, dict) or set(value) != {
            "relative_ref",
            "sha256",
            "bytes",
        }:
            return False
        if (
            value["relative_ref"]
            != str(Path(MATERIAL_ROOT).parent.as_posix()) + "/" + filename
            or not _is_sha256(value["sha256"])
            or type(value["bytes"]) is not int
            or not 0 < value["bytes"] <= MATERIAL_BYTES_MAX
        ):
            return False
    return True


def check_review_material_package(package: object, role: str) -> list[str]:
    try:
        return _check_review_material_package(package, role)
    except (KeyError, TypeError, ValueError, AttributeError):
        return ["material package malformed nested types"]


def _check_review_material_package(package: object, role: str) -> list[str]:
    """Validate private role structure without printing any private content."""
    if role not in MATERIAL_ROLES or not isinstance(package, dict):
        return ["material package malformed"]
    common = {"schema_version", "protocol_version", "role", "author_context"}
    payload = {
        "inputs": "cases",
        "controller": "clarification_cards",
        "scorer": "case_rubrics",
    }[role]
    allowed = (
        common
        | {payload}
        | ({"source_manifest", "equivalence"} if role == "scorer" else set())
    )
    if (
        set(package) != allowed
        or package.get("schema_version") != f"draft-m1-{role}-1"
        or package.get("protocol_version") != "draft-m1-3"
        or package.get("role") != role
        or not _nonempty_text(package.get("author_context"))
    ):
        return ["material package role schema or isolation invalid"]
    errors: list[str] = []
    if role == "inputs":
        cases = package[payload]
        if (
            not isinstance(cases, list)
            or len(cases) != 6
            or any(not isinstance(c, dict) for c in cases)
        ):
            return ["inputs require six unique cases"]
        if [c.get("case_id") for c in cases] != list(REVIEW_CASE_IDS):
            errors.append("inputs case IDs must be unique complete and ordered")
        for case in cases:
            if set(case) != {
                "case_id",
                "domain_id",
                "variant",
                "prompt",
                "output_requirements",
                "workflow",
            }:
                errors.append("case input unsupported fields or scorer leakage")
            if not _nonempty_text(case.get("prompt")) or not _text_list(
                case.get("output_requirements")
            ):
                errors.append(
                    "case input requires exact prompt and output requirements"
                )
            cid = case.get("case_id")
            if (
                case.get("variant") not in ("A", "B")
                or not isinstance(cid, str)
                or case["variant"] != cid[-1:]
            ):
                errors.append("case variant must match case ID suffix")
            if cid not in REVIEW_CASE_PAIRS.get(case.get("domain_id"), []):
                errors.append("case domain mismatch")
            if not _json_equal(
                case.get("workflow"), FORMAL_WORKFLOWS.get(case.get("domain_id"))
            ):
                errors.append("case workflow coverage mismatch")
    elif role == "controller":
        cards = package[payload]
        if not isinstance(cards, dict) or set(cards) != set(REVIEW_CASE_IDS):
            return ["controller requires six clarification cards"]
        for card in cards.values():
            if (
                not isinstance(card, dict)
                or set(card)
                != {"decisive_questions", "answer_units", "accepted_conditions"}
                or not _text_list(card.get("decisive_questions"))
            ):
                errors.append("controller clarification structure invalid")
                continue
            units = card["answer_units"]
            if (
                not isinstance(units, list)
                or len(units) != len(card["decisive_questions"])
                or any(
                    not isinstance(u, dict)
                    or set(u) != {"question_group", "answer"}
                    or type(u.get("question_group")) is not int
                    or not _nonempty_text(u.get("answer"))
                    for u in units
                )
                or [u["question_group"] for u in units]
                != list(range(1, len(units) + 1))
            ):
                errors.append("answer units require unique one based question mapping")
            accepted = card["accepted_conditions"]
            if (
                not isinstance(accepted, dict)
                or set(accepted) != {"mode", "conditions"}
                or accepted.get("mode") not in ("conformance", "exploration")
                or not _text_list(
                    accepted.get("conditions"),
                    empty=accepted.get("mode") == "exploration",
                )
            ):
                errors.append("accepted condition structure invalid")
    else:
        rubrics = package[payload]
        if not isinstance(rubrics, dict) or set(rubrics) != set(REVIEW_CASE_IDS):
            return ["scorer requires six critical rubrics"]
        sources = package["source_manifest"]
        if (
            not isinstance(sources, list)
            or not sources
            or any(not isinstance(s, dict) for s in sources)
        ):
            return ["scorer source manifest missing"]
        source_ids: set[str] = set()
        for source in sources:
            if (
                set(source)
                != {
                    "id",
                    "capture_sha256",
                    "representation_sha256",
                    "utf8_start",
                    "utf8_end",
                    "quote",
                    "version_identity",
                    "locator",
                }
                or not _nonempty_text(source.get("id"))
                or not _is_sha256(source.get("capture_sha256"))
                or not _is_sha256(source.get("representation_sha256"))
                or type(source.get("utf8_start")) is not int
                or type(source.get("utf8_end")) is not int
                or not 0 <= source["utf8_start"] < source["utf8_end"]
                or any(
                    not _nonempty_text(source.get(k))
                    for k in ("quote", "version_identity", "locator")
                )
            ):
                errors.append("scorer source location identity invalid")
                continue
            if source["id"] in source_ids:
                errors.append("scorer source identity duplicated")
            source_ids.add(source["id"])
        for rubric in rubrics.values():
            if (
                not isinstance(rubric, dict)
                or set(rubric) != {"critical_items", "critical_failures"}
                or not _text_list(rubric.get("critical_failures"))
                or not isinstance(rubric.get("critical_items"), list)
                or not rubric["critical_items"]
            ):
                errors.append("scorer critical coverage missing")
                continue
            ids: set[str] = set()
            for item in rubric["critical_items"]:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"id", "assertion", "source_refs"}
                    or not _nonempty_text(item.get("id"))
                    or not _nonempty_text(item.get("assertion"))
                    or not _text_list(item.get("source_refs"))
                    or not set(item["source_refs"]) <= source_ids
                ):
                    errors.append("scorer critical source reference invalid")
                    continue
                if item["id"] in ids:
                    errors.append("scorer critical identity duplicated")
                ids.add(item["id"])
        equivalence = package["equivalence"]
        if (
            not isinstance(equivalence, dict)
            or set(equivalence) != set(REVIEW_CASE_PAIRS)
            or any(not _nonempty_text(v) for v in equivalence.values())
        ):
            errors.append("scorer pair equivalence evidence missing")
    return errors


def _read_material_bytes(root: Path, target: Path) -> bytes:
    """Reject original path links before resolution and bound a consistent read."""
    if ".." in root.parts or ".." in target.parts:
        raise ValueError("material parent traversal")
    root = Path(os.path.abspath(root))
    target = Path(os.path.abspath(target))
    try:
        relative = target.relative_to(root)
    except ValueError:
        raise ValueError("material path outside root") from None
    # Check every original component, including ancestors of the inspected root.
    cursor = Path(target.anchor)
    for part in target.parts[1:]:
        cursor /= part
        info = cursor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(
            info, "st_file_attributes", 0
        ) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise ValueError("material linked path")
    expected = root.resolve() / relative
    if target.resolve() != expected or not target.resolve().is_relative_to(
        root.resolve()
    ):
        raise ValueError("material resolution mismatch")
    before = target.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MATERIAL_BYTES_MAX:
        raise ValueError("material nonregular or oversized")
    with target.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("material changed identity")
        raw = stream.read(MATERIAL_BYTES_MAX + 1)
        after = os.fstat(stream.fileno())
    current = target.stat()
    # Windows Python 3.12 stat/fstat can expose different ctime semantics.
    # Compare ctime within each API, and shared identity/size/mtime across APIs.
    identities = {
        (i.st_dev, i.st_ino, i.st_size, i.st_mtime_ns)
        for i in (before, opened, after, current)
    }
    if (
        len(raw) > MATERIAL_BYTES_MAX
        or len(identities) != 1
        or before.st_ctime_ns != current.st_ctime_ns
        or opened.st_ctime_ns != after.st_ctime_ns
        or len(raw) != current.st_size
        or not stat.S_ISREG(current.st_mode)
    ):
        raise ValueError("material changed or oversized")
    return raw


def check_review_material_files(
    root: Path,
    material_root: Path,
    index_sha256: str,
    *,
    index_raw: bytes | None = None,
) -> list[str]:
    """Explicit local qualification only; never follows arbitrary manifest paths."""
    errors: list[str] = []
    try:
        if index_raw is None:
            index_raw = _read_material_bytes(root, root / MATERIAL_INDEX_PATH)
        if (
            not _is_sha256(index_sha256)
            or hashlib.sha256(index_raw).hexdigest() != index_sha256
        ):
            return ["materials: index identity mismatch"]
        index = _load_current_json(index_raw)
        if check_current_materials(index):
            return ["materials: public index invalid"]
        if Path(os.path.abspath(material_root)) != Path(
            os.path.abspath(root / MATERIAL_ROOT)
        ):
            return ["materials: noncanonical package root"]
        if index["status"] != "frozen_reviewed":
            return ["materials: not_ready pending independent preparation"]
        packages: dict[str, dict] = {}
        for role, binding in zip(MATERIAL_ROLES, index["packages"], strict=True):
            try:
                raw = _read_material_bytes(root, material_root / f"{role}.json")
                if (
                    len(raw) != binding["bytes"]
                    or hashlib.sha256(raw).hexdigest() != binding["sha256"]
                ):
                    errors.append(f"materials {role}: raw identity mismatch")
                    continue
                package = _load_current_json(raw)
                errors.extend(
                    f"materials {role}: {error}"
                    for error in check_review_material_package(package, role)
                )
                if isinstance(package, dict):
                    packages[role] = package
            except (OSError, ValueError, TypeError):
                errors.append(f"materials {role}: unreadable")
        receipt = index["review_receipt"]
        for key, filename in (
            ("report", "materials-review.json"),
            ("rereview_report", "materials-rereview.json"),
        ):
            binding = receipt[key]
            if binding is None:
                continue
            try:
                raw = _read_material_bytes(root, material_root.parent / filename)
                if (
                    len(raw) != binding["bytes"]
                    or hashlib.sha256(raw).hexdigest() != binding["sha256"]
                ):
                    errors.append("materials review: raw identity mismatch")
                    continue
                report = _load_current_json(raw)
                if (
                    not isinstance(report, dict)
                    or set(report)
                    != {
                        "origin_thread_id",
                        "origin_message_id",
                        "reviewer_context",
                        "reviewer_role",
                        "package_sha256",
                        "conclusion",
                        "limitations",
                    }
                    or report.get("reviewer_context") != receipt["reviewer_context"]
                    or report.get("reviewer_role") != receipt["reviewer_role"]
                    or not _json_equal(
                        report.get("package_sha256"), receipt["package_sha256"]
                    )
                    or report.get("conclusion") != "done_no_open_findings"
                    or not _nonempty_text(report.get("origin_thread_id"))
                    or not _nonempty_text(report.get("origin_message_id"))
                    or not _text_list(report.get("limitations"), empty=True)
                ):
                    errors.append("materials review: original report binding invalid")
            except (OSError, ValueError, TypeError):
                errors.append("materials review: unreadable")
        if any(
            p.get("author_context") == receipt["reviewer_context"]
            for p in packages.values()
        ):
            errors.append(
                "materials review: author cannot independently review own package"
            )
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        errors.append("materials: unreadable or invalid identity")
    return errors


def check_current_supplement(supplement: object, protocol_raw: bytes) -> list[str]:
    """Pure supplement structure and captured-byte chain checks; not bundle approval."""
    if not isinstance(supplement, dict):
        return ["M1 supplement must be an object"]
    errors: list[str] = []
    if (
        supplement.get("protocol_version") != "draft-m1-capabilities-6"
        or supplement.get("role") != "capability_acceptance_reference"
    ):
        errors.append("M1 supplement must reference sole current authority")
    expected = {
        "path": PROTOCOL,
        "version": "draft-m1-3",
        "sha256": hashlib.sha256(protocol_raw).hexdigest(),
    }
    if not _json_equal(supplement.get("current_protocol"), expected):
        errors.append("M1 current protocol raw SHA-256 mismatch")
    if any(
        k in supplement
        for k in (
            "budget",
            "formal",
            "execution_budget_cny",
            "project_ledger",
            "funding",
            "Go",
        )
    ):
        errors.append("M1 supplement cannot define separate funding or release gates")
    for section, names in {
        "authorization": (
            "business_implementation",
            "real_execution",
            "paid_execution",
            "git_write",
        ),
        "results": (
            "implemented",
            "technical_verification",
            "human_business_acceptance",
            "real_quality",
            "owner_time_value",
            "engineering_M1",
            "M1",
            "Go",
            "release",
        ),
    }.items():
        values = supplement.get(section)
        if not isinstance(values, dict) or any(
            values.get(k) is not False for k in names
        ):
            errors.append(f"M1 {section} cannot claim execution or acceptance")
    policy = supplement.get("real_coverage_policy")
    if (
        not isinstance(policy, dict)
        or policy.get("MCP_real_integration_required") is not False
        or policy.get("old_9_8_12_independent_execution_batch_required") is not False
    ):
        errors.append("M1 must not revive superseded integration batches")
    if not _json_equal(supplement.get("real_coverage_policy"), REVIEW_COVERAGE_POLICY):
        errors.append("M1 capability coverage policy differs")
    if not _json_equal(
        supplement.get("team_delivery_contract"), TEAM_DELIVERY_CONTRACT
    ):
        errors.append("M1 team delivery contract differs")
    if not _json_equal(
        supplement.get("development_delivery_policy"), DEVELOPMENT_DELIVERY_POLICY
    ):
        errors.append("M1 development delivery policy differs")
    if not _json_equal(
        supplement.get("on_demand_evaluation"), ON_DEMAND_EVALUATION_POLICY
    ):
        errors.append("M1 on-demand evaluation policy differs")
    capabilities = supplement.get("capabilities")
    if not _json_equal(capabilities, REVIEW_CAPABILITIES):
        errors.append("M1 capability mappings differ")
    if not _json_equal(
        supplement.get("deferred_capabilities"), REVIEW_DEFERRED_CAPABILITIES
    ):
        errors.append("M1 deferred capabilities must remain pending and not required")
    if (
        not isinstance(capabilities, list)
        or len(capabilities) != 5
        or any(
            not isinstance(c, dict)
            or not c.get("requirements")
            or not c.get("tasks")
            or not c.get("evidence")
            for c in capabilities
        )
    ):
        errors.append("M1 capability evidence mapping is incomplete")
    return errors


def read_historical_protocol(
    root: Path,
    *,
    commit: str,
    path: str,
    raw_sha256: str,
    newlines: str = "raw",
) -> tuple[dict, bytes]:
    """Read identified Git bytes only; no checkout, archive copy, or spending.

    The raw hash is checked before the caller's explicit newline transform.
    The returned bytes identify that particular historical representation.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("historical commit must be a full lowercase Git SHA")
    if (
        not isinstance(path, str)
        or not path
        or path.startswith(("/", "-"))
        or "\\" in path
        or ":" in path
        or ".." in Path(path).parts
        or newlines not in {"raw", "lf-to-crlf"}
        or not re.fullmatch(r"[0-9a-f]{64}", raw_sha256)
    ):
        raise ValueError("invalid explicit historical byte identity")
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", f"{commit}:{path}"],
        capture_output=True,
        check=False,
        timeout=15,
    )
    if result.returncode or hashlib.sha256(result.stdout).hexdigest() != raw_sha256:
        raise ValueError("historical protocol unavailable or raw SHA-256 mismatch")
    blob = result.stdout
    if newlines == "lf-to-crlf":
        if b"\r" in blob:
            raise ValueError("LF-to-CRLF requires an LF-only original")
        blob = blob.replace(b"\n", b"\r\n")
    protocol = json.loads(blob)
    if not isinstance(protocol, dict) or check_protocol(protocol):
        raise ValueError(
            "identified bytes are not a valid historical current-3 protocol"
        )
    return protocol, blob


def _nonnegative_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _money(value: object) -> Decimal | None:
    return Decimal(str(value)) if _nonnegative_number(value) else None


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _check_artifact(
    base_dir: Path, relative: object, digest: object, label: str
) -> list[str]:
    if (
        not isinstance(relative, str)
        or not relative.strip()
        or Path(relative).is_absolute()
    ):
        return [f"{label}: artifact path must be relative"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return [f"{label}: artifact SHA-256 must be lowercase hex"]
    base = base_dir.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        return [f"{label}: artifact missing or outside result directory"]
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        return [f"{label}: artifact SHA-256 mismatch"]
    return []


def _check_facts(
    record: dict, contract: dict, label: str
) -> tuple[list[str], set[str], bool]:
    """Check declared fact links; official identity and truth still need a human."""
    errors: list[str] = []
    admitted: set[str] = set()
    conflicting = False
    facts = record.get("facts")
    if not isinstance(facts, list):
        return [f"{label}: facts must be a list"], admitted, conflicting
    seen: set[str] = set()
    for index, fact in enumerate(facts):
        name = f"{label} fact[{index}]"
        if not isinstance(fact, dict) or set(contract["fact_required_fields"]) - set(
            fact
        ):
            errors.append(f"{name}: incomplete fact evidence")
            continue
        fact_id = fact["fact_id"]
        if not isinstance(fact_id, str) or not fact_id or fact_id in seen:
            errors.append(f"{name}: missing or duplicate fact ID")
            continue
        seen.add(fact_id)
        if (
            not all(
                isinstance(fact[key], str) and fact[key].strip()
                for key in (
                    "subject",
                    "claim",
                    "official_source_url",
                    "official_identity_basis",
                    "evidence_excerpt",
                    "evidence_locator",
                )
            )
            or _timestamp(fact["retrieved_at"]) is None
        ):
            errors.append(f"{name}: missing source identity, excerpt, locator or time")
        if fact["machine_admission_status"] not in {
            "admitted",
            "rejected",
            "unknown",
        } or fact["human_official_review_status"] not in {
            "verified",
            "not_verified",
            "contradicted",
        }:
            errors.append(f"{name}: invalid admission or human review status")
        note = fact["contradiction_note"]
        if fact["human_official_review_status"] == "contradicted" or (
            isinstance(note, str) and note != "none"
        ):
            conflicting = True
        if fact["human_official_review_status"] == "verified":
            if (
                fact["machine_admission_status"] != "admitted"
                or not fact["reviewer_id"]
                or _timestamp(fact["source_checked_at"]) is None
                or note != "none"
            ):
                errors.append(
                    f"{name}: verified fact lacks admitted, reviewed evidence"
                )
            else:
                admitted.add(fact_id)
    return errors, admitted, conflicting


def _check_call_attempts(
    record: dict, contract: dict, label: str
) -> tuple[list[str], int, int, Decimal, int]:
    errors: list[str] = []
    unknown_cost = 0
    unknown_model_usage = 0
    known_cost = Decimal(0)
    known_billable_calls = 0
    attempts = record.get("call_attempts")
    if not isinstance(attempts, list):
        return [f"{label}: call_attempts must be a list"], 0, 0, known_cost, 0
    seen: set[str] = set()
    for index, attempt in enumerate(attempts):
        name = f"{label} call[{index}]"
        if not isinstance(attempt, dict) or set(
            contract["call_attempt_required_fields"]
        ) - set(attempt):
            errors.append(f"{name}: incomplete call attempt")
            continue
        attempt_id = attempt["attempt_id"]
        if not isinstance(attempt_id, str) or not attempt_id or attempt_id in seen:
            errors.append(f"{name}: missing or duplicate attempt ID")
            continue
        seen.add(attempt_id)
        start, end = _timestamp(attempt["started_at"]), _timestamp(attempt["ended_at"])
        if (
            attempt["kind"] not in {"model", "tool"}
            or not isinstance(attempt["billable"], bool)
            or attempt["outcome"] not in {"completed", "failed", "unknown_outcome"}
            or start is None
            or (
                attempt["outcome"] == "unknown_outcome"
                and attempt["ended_at"] is not None
            )
            or (
                attempt["outcome"] != "unknown_outcome" and (end is None or end < start)
            )
            or (
                attempt["known_cost_cny"] is not None
                and not _nonnegative_number(attempt["known_cost_cny"])
            )
        ):
            errors.append(f"{name}: invalid call timing, outcome or cost")
        for key in ("reported_prompt_tokens", "reported_completion_tokens"):
            if attempt[key] is not None and not _nonnegative_int(attempt[key]):
                errors.append(f"{name}: invalid reported usage")
        if attempt["billable"] and attempt["known_cost_cny"] is None:
            unknown_cost += 1
        elif attempt["billable"] and _money(attempt["known_cost_cny"]) is not None:
            known_cost += Decimal(str(attempt["known_cost_cny"]))
            known_billable_calls += 1
        elif not attempt["billable"] and attempt["known_cost_cny"] not in {None, 0}:
            errors.append(f"{name}: nonbillable call cannot have a positive cost")
        if (
            attempt["billable"]
            and attempt["outcome"] == "unknown_outcome"
            and attempt["known_cost_cny"] is not None
        ):
            errors.append(f"{name}: unknown outcome cannot claim known cost")
        if attempt["kind"] == "model" and (
            attempt["reported_prompt_tokens"] is None
            or attempt["reported_completion_tokens"] is None
        ):
            unknown_model_usage += 1
    return errors, unknown_cost, unknown_model_usage, known_cost, known_billable_calls


def check_results(protocol: dict, batch: dict, base_dir: Path) -> list[str]:
    """Check pilot/formal records and artifacts; source truth remains manual."""
    errors: list[str] = []
    phase = batch.get("phase")
    if batch.get("protocol_version") != protocol.get(
        "protocol_version"
    ) or phase not in {"pilot", "formal"}:
        errors.append("batch must identify this pilot/formal protocol version")
    records = batch.get("records")
    if not isinstance(records, list):
        return errors + ["batch.records must be a list"]
    contract = protocol["result_record_contract"]
    cases = {case["id"]: case for case in protocol["cases"]}
    seen: set[tuple[str, int]] = set()
    task_ids: set[str] = set()
    run_ids: set[str] = set()
    successes: Counter[str] = Counter()
    for index, record in enumerate(records):
        label = f"record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: object required")
            continue
        missing = set(contract["required_fields"]) - set(record)
        if missing:
            errors.append(f"{label}: missing {', '.join(sorted(missing))}")
            continue
        case_id, trial = record["case_id"], record["trial_index"]
        if (
            case_id not in cases
            or not isinstance(trial, int)
            or isinstance(trial, bool)
            or not 1
            <= trial
            <= (3 if phase == "formal" and str(case_id).startswith("B") else 1)
            or (phase == "pilot" and not str(case_id).startswith("B"))
        ):
            errors.append(f"{label}: invalid case/trial")
            continue
        key = (case_id, trial)
        if key in seen:
            errors.append(f"{label}: duplicate {key}")
        seen.add(key)
        if (
            record["phase"] != phase
            or record["protocol_version"] != protocol["protocol_version"]
        ):
            errors.append(f"{label}: wrong phase/version")
        if record["status"] not in {
            "queued",
            "running",
            "completed",
            "partial",
            "failed",
            "cancelled",
        }:
            errors.append(f"{label}: invalid status")
        elif record["status"] not in {"completed", "partial", "failed", "cancelled"}:
            errors.append(f"{label}: retained attempt must have a terminal status")
        if record["completion_level"] not in {"full", "partial", "none"}:
            errors.append(f"{label}: invalid completion_level")
        elif record["completion_level"] == "full" and record["status"] != "completed":
            errors.append(f"{label}: full completion requires completed status")
        for item in (
            "task_id",
            "run_id",
            "code_revision",
            "started_at",
            "ended_at",
            "raw_record_path",
        ):
            if not isinstance(record[item], str) or not record[item].strip():
                errors.append(f"{label}: {item} required")
        prompt_hash = hashlib.sha256(
            cases[case_id]["prompt"].encode("utf-8")
        ).hexdigest()
        if record["prompt_sha256"] != prompt_hash:
            errors.append(f"{label}: prompt SHA-256 differs from frozen case")
        start, end = _timestamp(record["started_at"]), _timestamp(record["ended_at"])
        if start is None or end is None or end < start:
            errors.append(f"{label}: invalid attempt timestamps")
        if not _nonnegative_number(record["wall_clock_seconds"]):
            errors.append(f"{label}: invalid wall_clock_seconds")
        if not _nonnegative_int(record["duplicate_urls"]):
            errors.append(f"{label}: invalid duplicate_urls")
        errors.extend(
            _check_artifact(
                base_dir,
                record["raw_record_path"],
                record["raw_record_sha256"],
                f"{label} raw record",
            )
        )
        report = record["report_artifact"]
        if report is not None:
            if not isinstance(report, dict) or set(
                contract["report_artifact_required_fields"]
            ) - set(report):
                errors.append(f"{label}: incomplete report artifact")
            else:
                errors.extend(
                    _check_artifact(
                        base_dir,
                        report["relative_path"],
                        report["sha256"],
                        f"{label} report",
                    )
                )
                if report["relative_path"] == record["raw_record_path"]:
                    errors.append(f"{label}: report and raw record must be separate")
        elif record["status"] == "completed" and record["completion_level"] == "full":
            errors.append(f"{label}: full result needs report artifact")
        trace = record["trace_artifact"]
        if not isinstance(trace, dict) or set(
            contract["trace_artifact_required_fields"]
        ) - set(trace):
            errors.append(f"{label}: incomplete trace artifact")
        else:
            errors.extend(
                _check_artifact(
                    base_dir, trace["relative_path"], trace["sha256"], f"{label} trace"
                )
            )
            if trace["relative_path"] == record["raw_record_path"]:
                errors.append(
                    f"{label}: raw record and trace must be separate artifacts"
                )
        review_bundle = record["review_bundle_artifact"]
        if not isinstance(review_bundle, dict) or set(
            contract["review_bundle_artifact_required_fields"]
        ) - set(review_bundle):
            errors.append(f"{label}: incomplete review bundle artifact")
        else:
            bundle_errors = _check_artifact(
                base_dir,
                review_bundle["relative_path"],
                review_bundle["sha256"],
                f"{label} review bundle",
            )
            errors.extend(bundle_errors)
            if review_bundle["relative_path"] in {
                record["raw_record_path"],
                trace.get("relative_path") if isinstance(trace, dict) else None,
                report.get("relative_path") if isinstance(report, dict) else None,
            }:
                errors.append(f"{label}: review bundle must be a separate artifact")
            if not bundle_errors:
                bundle_path = (base_dir / review_bundle["relative_path"]).resolve()
                try:
                    bundle_data = json.loads(bundle_path.read_text(encoding="utf-8"))
                except (OSError, ValueError, UnicodeError):
                    errors.append(f"{label}: review bundle must be readable JSON")
                else:
                    expected_bundle = {
                        "task_id": record["task_id"],
                        "run_id": record["run_id"],
                        "status": record["status"],
                        "stop_reason": record["stop_reason"],
                        "facts": record["facts"],
                        "raw_record_sha256": record["raw_record_sha256"],
                        "trace_sha256": trace.get("sha256")
                        if isinstance(trace, dict)
                        else None,
                        "report_sha256": report.get("sha256")
                        if isinstance(report, dict)
                        else None,
                        "cost": record["cost"],
                        "comparison": record["comparison"],
                        "manual_source_review": record["manual_source_review"],
                    }
                    if not isinstance(bundle_data, dict) or any(
                        bundle_data.get(key) != value
                        for key, value in expected_bundle.items()
                    ):
                        errors.append(
                            f"{label}: review bundle differs from attempt record"
                        )
        if record["persistence_backend"] != "postgresql":
            errors.append(f"{label}: invalid persistence_backend")
        fact_errors, admitted_fact_ids, fact_conflict = _check_facts(
            record, contract, label
        )
        errors.extend(fact_errors)
        (
            call_errors,
            unknown_cost_calls,
            unknown_usage_calls,
            known_call_cost,
            known_billable_calls,
        ) = _check_call_attempts(record, contract, label)
        errors.extend(call_errors)
        manual = record["manual_source_review"]
        if not isinstance(manual, dict) or set(
            contract["manual_source_review_required_fields"]
        ) - set(manual):
            errors.append(f"{label}: incomplete manual_source_review")
        elif (
            not manual.get("reviewer_id")
            or _timestamp(manual.get("reviewed_at")) is None
            or not manual.get("evidence_note")
            or manual.get("report_sha256")
            != (report.get("sha256") if isinstance(report, dict) else None)
            or manual.get("second_review_status")
            not in {"independent", "same_reviewer_later", "not_done"}
        ):
            errors.append(f"{label}: invalid manual_source_review")
        elif manual["second_review_status"] == "not_done":
            if (
                manual["second_reviewer_id"] is not None
                or manual["second_reviewed_at"] is not None
            ):
                errors.append(
                    f"{label}: unfinished second review must have null reviewer/time"
                )
        elif (
            not manual["second_reviewer_id"]
            or (second_time := _timestamp(manual["second_reviewed_at"])) is None
            or second_time <= _timestamp(manual["reviewed_at"])
            or (
                manual["second_review_status"] == "independent"
                and manual["second_reviewer_id"] == manual["reviewer_id"]
            )
            or (
                manual["second_review_status"] == "same_reviewer_later"
                and manual["second_reviewer_id"] != manual["reviewer_id"]
            )
        ):
            errors.append(f"{label}: invalid later second review")
        comparison = record["comparison"]
        if not isinstance(comparison, dict) or set(
            contract["comparison_required_fields"]
        ) - set(comparison):
            errors.append(f"{label}: incomplete comparison record")
        elif not all(
            isinstance(comparison[key], str) and comparison[key].strip()
            for key in contract["comparison_required_fields"]
        ) or comparison["budget_parity"] not in {"matched", "mismatched", "unverified"}:
            errors.append(f"{label}: invalid comparison record")
        cost = record["cost"]
        if not isinstance(cost, dict) or set(contract["cost_required_fields"]) - set(
            cost
        ):
            errors.append(f"{label}: incomplete cost record")
        elif (
            cost["currency"] != "CNY"
            or (
                cost["known_cost_cny"] is not None
                and not _nonnegative_number(cost["known_cost_cny"])
            )
            or (
                known_billable_calls > 0
                and _money(cost["known_cost_cny"]) != known_call_cost
            )
            or (
                known_billable_calls == 0
                and (
                    _money(cost["known_cost_cny"]) != Decimal(0)
                    if unknown_cost_calls == 0
                    else _money(cost["known_cost_cny"]) not in {None, Decimal(0)}
                )
            )
            or (
                cost["total_cost_cny"] is not None
                and not _nonnegative_number(cost["total_cost_cny"])
            )
            or not _nonnegative_int(cost["unknown_attempt_count"])
            or cost["unknown_attempt_count"] != unknown_cost_calls
            or (
                cost["unknown_attempt_count"] > 0 and cost["total_cost_cny"] is not None
            )
            or (
                cost["known_cost_cny"] is not None
                and cost["total_cost_cny"] is not None
                and _money(cost["total_cost_cny"]) is not None
                and _money(cost["known_cost_cny"]) is not None
                and _money(cost["total_cost_cny"]) != _money(cost["known_cost_cny"])
            )
            or (unknown_cost_calls == 0 and cost["total_cost_cny"] is None)
            or (
                cost["known_cost_cny"] is not None
                and (
                    not cost["pricing_basis"]
                    or _timestamp(cost["price_checked_at"]) is None
                )
            )
        ):
            errors.append(f"{label}: invalid cost or unknown-cost semantics")
        for item, values in (("task_id", task_ids), ("run_id", run_ids)):
            value = record[item]
            if isinstance(value, str):
                if value in values:
                    errors.append(f"{label}: duplicate {item}")
                values.add(value)
        reviews = record["field_reviews"]
        fields = set(cases[case_id]["required_fields"])
        if not isinstance(reviews, dict) or set(reviews) != fields:
            errors.append(
                f"{label}: field_reviews must cover exactly the required fields"
            )
            continue
        for field, review in reviews.items():
            if not isinstance(review, dict) or set(
                contract["field_review_required_fields"]
            ) - set(review):
                errors.append(f"{label}: incomplete field review {field}")
            elif review.get("verified_by_human") is True and (
                not review.get("reviewer_id")
                or not review.get("evidence_locator")
                or _timestamp(review.get("source_checked_at")) is None
                or review.get("contradiction_note") is None
            ):
                errors.append(f"{label}: invalid human field review {field}")
            elif not isinstance(review.get("fact_ids"), list) or any(
                not isinstance(fact_id, str) or not fact_id
                for fact_id in review["fact_ids"]
            ):
                errors.append(f"{label}: invalid fact IDs in field {field}")
        verified_count = sum(
            isinstance(review, dict)
            and bool(review.get("value"))
            and bool(review.get("official_source_url"))
            and review.get("verified_by_human") is True
            and bool(review.get("source_checked_at"))
            for review in reviews.values()
        )
        if record["field_coverage"] != {
            "verified_count": verified_count,
            "required_count": len(fields),
        }:
            errors.append(f"{label}: field_coverage does not match reviewed fields")
        claims = record["claims"]
        if not isinstance(claims, list):
            errors.append(f"{label}: claims must be a list")
            claims = []
        for claim in claims:
            if not isinstance(claim, dict) or set(
                contract["claim_required_fields"]
            ) - set(claim):
                errors.append(f"{label}: incomplete claim review")
            elif claim.get("verified_by_human") is True and (
                not claim.get("reviewer_id")
                or not claim.get("evidence_locator")
                or _timestamp(claim.get("source_checked_at")) is None
                or claim.get("contradiction_note") is None
            ):
                errors.append(f"{label}: invalid human claim review")
        conflicting = fact_conflict or any(
            isinstance(item, dict)
            and item.get("contradiction_note") not in {None, "none"}
            for item in [*reviews.values(), *claims]
        )
        if (
            (
                record["status"] == "completed"
                and record["completion_level"] == "full"
                or conflicting
            )
            and isinstance(manual, dict)
            and manual.get("second_review_status") == "not_done"
        ):
            errors.append(
                f"{label}: full or conflicting attempt needs later second review"
            )
        supplements = record["community_supplements"]
        if not isinstance(supplements, list):
            errors.append(f"{label}: community_supplements must be a list")
            supplements = []
        for supplement in supplements:
            if (
                not isinstance(supplement, dict)
                or set(contract["community_supplement_required_fields"])
                - set(supplement)
                or supplement.get("source_role") != "community_supplement"
                or supplement.get("verified_by_human") is not True
                or not supplement.get("source_url")
                or not supplement.get("source_checked_at")
                or not supplement.get("limitation")
            ):
                errors.append(f"{label}: invalid labeled community supplement")
        recommendation = record["recommendation_review"]
        if recommendation is not None and (
            not isinstance(recommendation, dict)
            or set(contract["recommendation_review_required_fields"])
            - set(recommendation)
        ):
            errors.append(f"{label}: incomplete recommendation review")
        usage = record["usage"]
        if not isinstance(usage, dict) or set(contract["usage_required_fields"]) - set(
            usage
        ):
            errors.append(f"{label}: incomplete usage record")
        elif (
            not _nonnegative_int(usage["unknown_attempt_count"])
            or usage["unknown_attempt_count"] != unknown_usage_calls
            or any(
                usage[key] is not None and not _nonnegative_int(usage[key])
                for key in (
                    "reported_prompt_tokens",
                    "reported_completion_tokens",
                    "known_lower_bound_tokens",
                )
            )
            or (
                usage["known_lower_bound_tokens"] is not None
                and usage["known_lower_bound_tokens"]
                < sum(
                    usage[key] or 0
                    for key in ("reported_prompt_tokens", "reported_completion_tokens")
                )
            )
        ):
            errors.append(f"{label}: invalid known/unknown usage")
        else:
            model_calls = [
                call
                for call in (
                    record["call_attempts"]
                    if isinstance(record["call_attempts"], list)
                    else []
                )
                if isinstance(call, dict) and call.get("kind") == "model"
            ]
            known_prompt = sum(
                call.get("reported_prompt_tokens") or 0
                for call in model_calls
                if _nonnegative_int(call.get("reported_prompt_tokens"))
            )
            known_completion = sum(
                call.get("reported_completion_tokens") or 0
                for call in model_calls
                if _nonnegative_int(call.get("reported_completion_tokens"))
            )
            if (
                usage["reported_prompt_tokens"] != known_prompt
                or usage["reported_completion_tokens"] != known_completion
                or usage["known_lower_bound_tokens"] != known_prompt + known_completion
            ):
                errors.append(f"{label}: usage differs from model call attempts")
        chain = record["chain_checks"]
        if (
            not isinstance(chain, dict)
            or set(chain) != {"ui", "api", "persistence", "sse"}
            or not all(isinstance(value, bool) for value in chain.values())
        ):
            errors.append(f"{label}: chain_checks must contain four booleans")
        access = record["access_checks"]
        if (
            not isinstance(access, dict)
            or set(access) != {"owner_visible", "other_hidden", "other_cancel_denied"}
            or not all(
                isinstance(value, bool) or (phase == "pilot" and value is None)
                for value in access.values()
            )
        ):
            errors.append(f"{label}: invalid access_checks for {phase}")
        if record["status"] == "completed" and record["completion_level"] == "full":
            fact_sources = (
                {
                    fact.get("fact_id"): fact.get("official_source_url")
                    for fact in record["facts"]
                    if isinstance(fact, dict)
                    and fact.get("fact_id") in admitted_fact_ids
                }
                if isinstance(record["facts"], list)
                else {}
            )
            if not admitted_fact_ids:
                errors.append(
                    f"{label}: full result needs admitted and human-verified facts"
                )
            for field, review in reviews.items():
                if (
                    not isinstance(review, dict)
                    or not isinstance(review.get("fact_ids"), list)
                    or not review["fact_ids"]
                    or not set(review["fact_ids"]).issubset(admitted_fact_ids)
                ):
                    errors.append(
                        f"{label}: full field {field} lacks verified fact IDs"
                    )
                elif review.get("official_source_url") not in {
                    fact_sources.get(fact_id) for fact_id in review["fact_ids"]
                }:
                    errors.append(
                        f"{label}: full field {field} source differs from facts"
                    )
            for claim in claims:
                if (
                    not isinstance(claim, dict)
                    or not isinstance(claim.get("fact_ids"), list)
                    or not claim["fact_ids"]
                    or not set(claim["fact_ids"]).issubset(admitted_fact_ids)
                ):
                    errors.append(
                        f"{label}: full claim cites missing or unverified fact IDs"
                    )
                elif not set(claim.get("official_source_urls", [])).issubset(
                    {fact_sources.get(fact_id) for fact_id in claim["fact_ids"]}
                ):
                    errors.append(f"{label}: full claim source differs from facts")
            if not claims or not all(
                isinstance(c, dict)
                and c.get("verified_by_human") is True
                and c.get("fact_ids")
                and c.get("official_source_urls")
                and c.get("source_checked_at")
                and c.get("reviewer_id")
                and c.get("evidence_locator")
                and c.get("contradiction_note") == "none"
                for c in claims
            ):
                errors.append(f"{label}: full result needs verified material claims")
            if not all(
                isinstance(r, dict)
                and r.get("value")
                and r.get("official_source_url")
                and r.get("verified_by_human") is True
                and r.get("source_checked_at")
                and r.get("reviewer_id")
                and r.get("evidence_locator")
                and r.get("contradiction_note") == "none"
                for r in reviews.values()
            ):
                errors.append(f"{label}: full result lacks verified fields")
            if record["official_source_review"] is not True:
                errors.append(f"{label}: official source review required")
            if not isinstance(recommendation, dict) or not (
                recommendation.get("text")
                and recommendation.get("use_conditions")
                and recommendation.get("supporting_fact_ids")
                and recommendation.get("official_source_urls")
                and recommendation.get("tradeoffs_or_unknowns")
                and recommendation.get("rationale_checked_by_human") is True
                and recommendation.get("source_checked_at")
            ):
                errors.append(f"{label}: full result needs verified recommendation")
            elif not set(recommendation["supporting_fact_ids"]).issubset(
                admitted_fact_ids.intersection(
                    {
                        fact_id
                        for claim in claims
                        if isinstance(claim, dict)
                        for fact_id in claim.get("fact_ids", [])
                    }
                )
            ):
                errors.append(f"{label}: recommendation cites unreviewed fact IDs")
            if phase == "formal" and (
                not isinstance(access, dict)
                or not all(
                    access.get(name) is True
                    for name in ("owner_visible", "other_hidden", "other_cancel_denied")
                )
            ):
                errors.append(f"{label}: full result needs owner isolation checks")
            if not isinstance(chain, dict) or not all(
                chain.get(name) is True for name in ("ui", "api", "persistence", "sse")
            ):
                errors.append(
                    f"{label}: full result needs four consistent chain checks"
                )
            if cases[case_id].get("community_supplement_required") and not supplements:
                errors.append(
                    f"{label}: O03 full result needs labeled community feedback"
                )
            if (
                not isinstance(manual, dict)
                or not manual.get("reviewer_id")
                or not manual.get("evidence_note")
            ):
                errors.append(f"{label}: full result needs manual source review")
            if not any(error.startswith(f"{label}:") for error in errors):
                successes[case_id] += 1
    expected_keys = (
        {(case, 1) for case in ("B01", "B02", "B03")}
        if phase == "pilot"
        else {
            (case, trial)
            for case in cases
            for trial in range(1, 4 if case.startswith("B") else 2)
        }
    )
    expected_count = 3 if phase == "pilot" else 15
    if seen != expected_keys or len(records) != expected_count:
        errors.append(
            f"{phase} batch must retain all {expected_count} distinct attempts"
        )
    frozen_keys = (
        "cohort_id",
        "environment_fingerprint",
        "upstream_browser_fingerprint",
        "dependency_lock_sha256",
        "model_id",
        "budget_fingerprint",
        "scoring_revision",
    )
    frozen = {
        (
            str(record.get("code_revision")),
            *(str(record.get("comparison", {}).get(key)) for key in frozen_keys),
        )
        for record in records
        if isinstance(record, dict) and isinstance(record.get("comparison"), dict)
    }
    if len(frozen) > 1:
        errors.append(
            f"{phase} batch mixes code, model, budget, scoring or environment"
        )
    if phase == "pilot":
        pilot_costs = [
            record.get("cost", {}).get("total_cost_cny")
            for record in records
            if isinstance(record, dict) and isinstance(record.get("cost"), dict)
        ]
        if len(pilot_costs) != len(records) or any(
            value is None or not _nonnegative_number(value) for value in pilot_costs
        ):
            errors.append("No-Go: pilot cost is incomplete or unknown; pause cohort")
        elif sum(pilot_costs) > 49:
            errors.append("No-Go: pilot exceeds 49 CNY allocation")
        return errors
    total_costs = [
        record.get("cost", {}).get("total_cost_cny")
        for record in records
        if isinstance(record, dict) and isinstance(record.get("cost"), dict)
    ]
    if len(total_costs) != len(records) or any(
        value is None or not _nonnegative_number(value) for value in total_costs
    ):
        errors.append("No-Go: formal batch cost is incomplete or unknown")
    elif sum(total_costs) > 200:
        errors.append("No-Go: formal batch exceeds 200 CNY allocation")
    for case in ("B01", "B02", "B03"):
        if successes[case] < 2:
            errors.append(f"No-Go: {case} has {successes[case]}/3 full successes")
    g_successes = sum(successes[case] for case in ("G01", "G02", "G03"))
    if g_successes < 2:
        errors.append(f"No-Go: G set has {g_successes}/3 full successes")
    o_successes = sum(successes[case] for case in ("O01", "O02", "O03"))
    if o_successes < 3:
        errors.append(f"No-Go: O set has {o_successes}/3 full successes")
    return errors


def check_ledger(protocol: dict, ledger: dict, base_dir: Path) -> list[str]:
    """Reconcile retained batches and every declared paid attempt across phases."""
    errors: list[str] = []
    contract = protocol["project_ledger_contract"]
    if ledger.get("protocol_version") != protocol["protocol_version"]:
        errors.append("ledger must use current protocol version")
    batches = ledger.get("batches")
    entries = ledger.get("entries")
    if not isinstance(batches, list) or not isinstance(entries, list):
        return errors + ["ledger needs batches and entries arrays"]
    batch_records: dict[str, dict] = {}
    batch_evidence: dict[str, tuple[Path, str]] = {}
    batch_ids: set[str] = set()
    for index, batch in enumerate(batches):
        label = f"ledger batch[{index}]"
        if not isinstance(batch, dict) or set(contract["batch_required_fields"]) - set(
            batch
        ):
            errors.append(f"{label}: incomplete batch reference")
            continue
        batch_id = batch["batch_id"]
        artifact = batch["artifact"]
        if not isinstance(batch_id, str) or not batch_id or batch_id in batch_ids:
            errors.append(f"{label}: duplicate or missing batch ID")
            continue
        batch_ids.add(batch_id)
        if batch["phase"] not in {"pilot", "formal"}:
            errors.append(f"{label}: invalid phase")
            continue
        if not isinstance(artifact, dict):
            errors.append(f"{label}: invalid batch artifact")
            continue
        artifact_errors = _check_artifact(
            base_dir, artifact.get("relative_path"), artifact.get("sha256"), label
        )
        errors.extend(artifact_errors)
        if artifact_errors:
            continue
        batch_path = (base_dir / artifact["relative_path"]).resolve()
        try:
            data = json.loads(batch_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            errors.append(f"{label}: unreadable batch JSON")
            continue
        if not isinstance(data, dict):
            errors.append(f"{label}: batch JSON must be an object")
            continue
        if data.get("phase") != batch["phase"]:
            errors.append(f"{label}: batch phase mismatch")
        errors.extend(check_results(protocol, data, batch_path.parent))
        for record in data.get("records", []):
            if not isinstance(record, dict):
                continue
            run_id = record.get("run_id")
            if not isinstance(run_id, str) or run_id in batch_records:
                errors.append(f"{label}: duplicate run ID across batches")
                continue
            batch_records[run_id] = {**record, "batch_id": batch_id}
            raw_path = record.get("raw_record_path")
            if isinstance(raw_path, str):
                batch_evidence[run_id] = (
                    (batch_path.parent / raw_path).resolve(),
                    record.get("raw_record_sha256"),
                )

    seen: set[str] = set()
    totals = {allocation: Decimal(0) for allocation in contract["allocations_cny"]}
    for index, entry in enumerate(entries):
        label = f"ledger entry[{index}]"
        if not isinstance(entry, dict) or set(contract["entry_required_fields"]) - set(
            entry
        ):
            errors.append(f"{label}: incomplete attempt")
            continue
        run_id, allocation = entry["run_id"], entry["allocation"]
        if not isinstance(run_id, str) or not run_id or run_id in seen:
            errors.append(f"{label}: duplicate or missing run ID")
            continue
        seen.add(run_id)
        if allocation not in totals:
            errors.append(f"{label}: invalid allocation")
            continue
        if not isinstance(entry["task_id"], str) or not entry["task_id"]:
            errors.append(f"{label}: missing task ID")
        if (
            not isinstance(entry["authorization_reference"], str)
            or not entry["authorization_reference"].strip()
        ):
            errors.append(f"{label}: missing per-run authorization reference")
        artifact = entry["evidence_artifact"]
        if not isinstance(artifact, dict):
            errors.append(f"{label}: invalid evidence artifact")
        else:
            errors.extend(
                _check_artifact(
                    base_dir,
                    artifact.get("relative_path"),
                    artifact.get("sha256"),
                    label,
                )
            )
        reconciliation_artifact = entry.get("reconciliation_artifact")
        if reconciliation_artifact is not None:
            if not isinstance(reconciliation_artifact, dict):
                errors.append(f"{label}: invalid reconciliation artifact")
            else:
                reconciliation_errors = _check_artifact(
                    base_dir,
                    reconciliation_artifact.get("relative_path"),
                    reconciliation_artifact.get("sha256"),
                    f"{label} reconciliation",
                )
                errors.extend(reconciliation_errors)
                if not reconciliation_errors:
                    try:
                        reconciliation = json.loads(
                            (
                                base_dir / reconciliation_artifact["relative_path"]
                            ).read_text(encoding="utf-8")
                        )
                        previous_ref = reconciliation["previous_ledger_artifact"]
                        attestation_ref = reconciliation["attestation_artifact"]
                        chain_errors = []
                        for name, reference in (
                            ("previous ledger", previous_ref),
                            ("attestation", attestation_ref),
                        ):
                            chain_errors.extend(
                                _check_artifact(
                                    base_dir,
                                    reference.get("relative_path"),
                                    reference.get("sha256"),
                                    f"{label} {name}",
                                )
                            )
                        errors.extend(chain_errors)
                        if chain_errors:
                            raise ValueError("Reconciliation chain is incomplete")
                        previous = json.loads(
                            (base_dir / previous_ref["relative_path"]).read_text(
                                encoding="utf-8"
                            )
                        )
                        original = next(
                            item
                            for item in previous["entries"]
                            if item["run_id"] == run_id
                        )
                        if (
                            reconciliation.get("artifact_type")
                            != "pilot_cost_reconciliation"
                            or reconciliation.get("run_id") != run_id
                            or reconciliation.get("task_id") != entry["task_id"]
                            or reconciliation.get("original_capture_artifact")
                            != entry["evidence_artifact"]
                            or original["evidence_artifact"]
                            != entry["evidence_artifact"]
                            or original["task_id"] != entry["task_id"]
                            or original["total_cost_cny"] is not None
                            or original["unknown_attempt_count"]
                            != reconciliation.get("original_unknown_call_count")
                            or len(reconciliation.get("reclassified_tool_calls", []))
                            != original["unknown_attempt_count"]
                            or Decimal(str(reconciliation.get("reconciled_total_cny")))
                            != _money(entry["total_cost_cny"])
                            or Decimal(
                                str(reconciliation.get("model_calculated_cost_cny"))
                            )
                            != _money(entry["known_cost_cny"])
                            or reconciliation.get("remaining_unknown_call_count") != 0
                            or entry["unknown_attempt_count"] != 0
                        ):
                            errors.append(
                                f"{label}: reconciliation conflicts with original"
                            )
                    except (
                        OSError,
                        ValueError,
                        KeyError,
                        TypeError,
                        StopIteration,
                        InvalidOperation,
                    ):
                        errors.append(f"{label}: unreadable reconciliation chain")
        known = _money(entry["known_cost_cny"])
        total = _money(entry["total_cost_cny"])
        unknown = entry["unknown_attempt_count"]
        if (
            not _nonnegative_int(unknown)
            or (unknown > 0 and total is not None)
            or (unknown == 0 and total is None)
            or (known is not None and total is not None and known != total)
            or (known is None and total is not None)
        ):
            errors.append(f"{label}: invalid known/unknown cost")
        if total is None:
            errors.append(f"No-Go: {label} cost unknown; stop new paid calls")
        else:
            totals[allocation] += total
        batch_id = entry["batch_id"]
        if batch_id is not None:
            record = batch_records.get(run_id)
            if record is None or record["batch_id"] != batch_id:
                errors.append(f"{label}: batch attempt missing or mismatched")
            else:
                if allocation != record["phase"] or any(
                    entry[key] != record_value
                    for key, record_value in (
                        ("task_id", record["task_id"]),
                        ("known_cost_cny", record["cost"]["known_cost_cny"]),
                        ("total_cost_cny", record["cost"]["total_cost_cny"]),
                        (
                            "unknown_attempt_count",
                            record["cost"]["unknown_attempt_count"],
                        ),
                    )
                ):
                    errors.append(f"{label}: batch attempt cost or identity differs")
                expected = batch_evidence.get(run_id)
                if (
                    isinstance(artifact, dict)
                    and expected
                    and (
                        (base_dir / artifact.get("relative_path", "")).resolve()
                        != expected[0]
                        or artifact.get("sha256") != expected[1]
                    )
                ):
                    errors.append(f"{label}: evidence differs from batch raw record")
        elif run_id in batch_records:
            errors.append(f"{label}: retained batch attempt needs its batch ID")
        elif allocation in {"pilot", "formal"}:
            # An interrupted attempt remains charged even if no completed batch exists.
            pass
    missing = set(batch_records) - seen
    if missing:
        errors.append(f"ledger omits {len(missing)} retained batch attempt(s)")
    for allocation, limit in contract["allocations_cny"].items():
        if totals[allocation] > Decimal(limit):
            errors.append(f"No-Go: {allocation} allocation exceeds {limit} CNY")
    if sum(totals.values()) > Decimal(contract["total_max_cny"]):
        errors.append("No-Go: project live-run budget exceeds 299 CNY")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--results", type=Path, help="completed historical result batch JSON"
    )
    parser.add_argument("--ledger", type=Path, help="completed historical ledger JSON")
    parser.add_argument(
        "--historical-commit", help="full Git commit for explicit read-only history"
    )
    parser.add_argument("--historical-path", default=PROTOCOL)
    parser.add_argument("--historical-raw-sha256")
    parser.add_argument(
        "--historical-newlines", choices=("raw", "lf-to-crlf"), default="raw"
    )
    parser.add_argument(
        "--historical-only",
        action="store_true",
        help="check identified historical evidence only, never current readiness",
    )
    parser.add_argument(
        "--review-material-root",
        type=Path,
        help="explicit canonical draft-m1 material package root; never a run trigger",
    )
    parser.add_argument(
        "--review-material-index-sha256",
        help="exact public index raw SHA-256 required with package root",
    )
    args = parser.parse_args(argv)
    root = Path(os.path.abspath(args.root))
    history_requested = bool(
        args.historical_commit
        or args.historical_raw_sha256
        or args.historical_only
        or args.historical_path != PROTOCOL
        or args.historical_newlines != "raw"
    )
    errors: list[str] = []
    material_requested = (
        args.review_material_root is not None
        or args.review_material_index_sha256 is not None
    )
    if material_requested and (
        args.historical_only
        or args.review_material_root is None
        or args.review_material_index_sha256 is None
    ):
        errors.append(
            "materials: paired arguments required and incompatible with historical-only"
        )
    raw: dict[str, bytes] = {}
    if not args.historical_only:
        errors.extend(check_links(root, project_document_files(root)))
        errors.extend(check_versions_and_traceability(root))
        errors.extend(check_skills(root))
        errors.extend(check_archive_manifest(root))
        errors.extend(check_archive_git_index(root))
        raw, parsed, bundle_errors = _read_current_bundle(root)
        errors.extend(bundle_errors)
        errors.extend(_check_current_bundle(raw, parsed))
    if (
        material_requested
        and not args.historical_only
        and args.review_material_root is not None
        and args.review_material_index_sha256 is not None
        and MATERIAL_INDEX_PATH in raw
    ):
        errors.extend(
            check_review_material_files(
                root,
                args.review_material_root,
                args.review_material_index_sha256,
                index_raw=raw[MATERIAL_INDEX_PATH],
            )
        )
    if args.results or args.ledger or history_requested:
        if not (
            args.historical_commit
            and args.historical_raw_sha256
            and (args.results or args.ledger)
        ):
            errors.append(
                "historical results/ledger require explicit commit, path, raw SHA-256 and an evidence file"
            )
        else:
            try:
                historical, blob = read_historical_protocol(
                    root,
                    commit=args.historical_commit,
                    path=args.historical_path,
                    raw_sha256=args.historical_raw_sha256,
                    newlines=args.historical_newlines,
                )
                digest = hashlib.sha256(blob).hexdigest()
                if args.results:
                    batch = json.loads(args.results.read_text(encoding="utf-8"))
                    if (
                        "protocol_sha256" in batch
                        and batch["protocol_sha256"] != digest
                    ):
                        errors.append("historical results protocol SHA-256 mismatch")
                    else:
                        errors.extend(
                            check_results(
                                historical, batch, args.results.resolve().parent
                            )
                        )
                if args.ledger:
                    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
                    if ledger.get("protocol_sha256") != digest:
                        errors.append(
                            "historical ledger protocol SHA-256 mismatch; choose the exact historical representation"
                        )
                    else:
                        errors.extend(
                            check_ledger(
                                historical, ledger, args.ledger.resolve().parent
                            )
                        )
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                subprocess.SubprocessError,
            ) as exc:
                errors.append(f"historical evidence unreadable: {type(exc).__name__}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"offline validation failed: {len(errors)} finding(s)", file=sys.stderr)
        return 1
    print(
        "historical evidence validation passed; no current readiness or spending authorization"
        if args.historical_only
        else "offline configuration validation passed; "
        + (
            "MATERIAL_STRUCTURE_VERIFIED_NOT_RUNTIME_PERMISSION"
            if material_requested
            else "MATERIALS_NOT_VERIFIED"
        )
        + "; implementation, live quality and source truth remain unverified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
