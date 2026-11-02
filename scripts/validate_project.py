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
CURRENT_PROTOCOL_VERSION = "draft-m1-2"
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


REVIEW_POLICY = {
    "protocol_version": "draft-m1-2",
    "status": "prepared_pending_material_and_actual_file_review",
    "registered_at": "2026-11-02",
    "preparation_revision": "FOCUS-BASELINE-20261102",
    "authority": "SPEC.md",
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
    "formal.execution_order": "serial_two_rounds_per_assignment",
    "formal.all_attempts_retained": True,
    "formal.no_replacements": True,
    "formal.version_frozen": True,
    "formal.code_templates_tools_quotas_scoring_frozen": True,
    "formal.revealed_failure_kept_not_replaced_by_optimization_slots": True,
    "formal.in_batch_fix": "retain_failed_slot; any replacement comparison requires separately "
    "authorized complete new batch",
    "formal.case_scope": "all linked Turns share original case time, tool/model/resource caps "
    "and authorization; no reset on input revision or new work identity",
    "formal.independent_author_and_non_author_material_review_required": True,
    "methods.agent.allowed": [
        "this_product",
        "registered_manual_search_engines",
        "owner_reads_original_sources",
        "owner_rewrites",
    ],
    "methods.agent.external_ai_repair_allowed": False,
    "methods.agent.deliberate_control_output_or_note_copy_allowed": False,
    "methods.control.ordinary_ai": "pre_registered_ordinary_AI_and_manual_repository_reading_search; "
    "actual_products_modes_and_new_fees_recorded",
    "methods.control.independent_deep_research.required": False,
    "methods.control.independent_deep_research.sessions_per_task": 1,
    "methods.control.independent_deep_research.preferred_product": "pre_registered_if_used; "
    "no_automatic_purchase_or_product_swap",
    "methods.control.independent_deep_research.actual_account_region_entry_mode_quota": "unverified",
    "methods.control.independent_deep_research.ordinary_browsing_or_thinking_is_not_DR": True,
    "methods.control.independent_deep_research.no_extra_DR_or_regeneration_replacing_failure": True,
    "methods.control.independent_deep_research.same_product_and_mode_all_three": True,
    "methods.control.independent_deep_research.insufficient_quota": "pause_and_discuss_no_auto_purchase_or_product_swap",
    "methods.manual_search.same_pre_registered_engine_list_both_methods": True,
    "methods.manual_search.switching_allowed": True,
    "methods.manual_search.arbitrary_query_count_cap": None,
    "methods.manual_search.all_owner_actions_count_active_time": True,
    "methods.manual_search.actual_names_and_availability": "must_register_before_reveal_not_assumed",
    "methods.contamination.record_familiarity_sources_and_knowledge_transfer": True,
    "methods.contamination.no_true_blinding_claim": True,
    "methods.contamination.memory_disabled_frozen_no_memory_effect_claim": True,
    "methods.contamination.formal_memory_initial_snapshot": "not_applicable_feature_disabled; no_store_snapshot_or_seed_required",
    "methods.contamination.implementation_author_exposed_to_gold": "not_independent_holdout; "
    "retain_exposed_slot_and_report_contamination",
    "timing.active_minutes_per_attempt": 120,
    "timing.wall_hours_per_attempt": 24,
    "timing.batch_days": 14,
    "timing.active_start": "first_actual_display_of_exact_case_prompt",
    "timing.active_components": [
        "reading_prompt",
        "clarification_and_acceptance",
        "prompt_interaction",
        "search",
        "reading_outputs",
        "original_source_review",
        "reading_audit_defects",
        "rechecking",
        "rewriting",
    ],
    "timing.pure_wait": "separate_from_active_but_in_wall_clock_including_audit_wait",
    "timing.end": "immutable_final_owner_submission_hash; "
    "final_audit_must_finish_within_wall_deadline",
    "timing.max_extensions": 1,
    "timing.unrevealed_extension_days": 7,
    "timing.extension_eligible": ["confirmed_service_outage", "free_quota_refresh"],
    "timing.extension_request": "before_original_batch_deadline",
    "timing.revealed_attempt_extension_allowed": False,
    "timing.project_admin_and_independent_audit_time": "separately_disclose; "
    "do_not_move_actual_research_work_out_of_active_clock",
    "timing.reveal": "disclosure_committed_is_permission_not_actual_display; "
    "separate_display_ack_client_clock_basis_server_ack_and_owner_timing",
    "timing.uncertain_first_display": "retain_earliest_possible_exposure_and_timing_uncertain; "
    "no_valid_paired_saving; "
    "no_slot_replacement_or_clock_reset",
    "assignment.algorithm_version": "ARA-EVAL-1",
    "assignment.seed_bits": 128,
    "assignment.seed_hex_chars": 32,
    "assignment.seed_encoding": "lowercase_hex_literal_UTF8_not_decoded_bytes",
    "assignment.seed_creation": "once_via_CSPRNG_after_protocol_and_material_hashes_frozen; "
    "no_redraw; not_generated_in_preparation",
    "assignment.digest": 'SHA256(UTF8("ARA-EVAL-1\\n" + seed + "\\n" + domain_id + "\\n" + '
    "label)) with actual LF characters",
    "assignment.labels": ["order", "assignment", "first"],
    "assignment.domain_order": "sort_by_hex_digest(label=order),then_domain_id",
    "assignment.variant_assignment": "last_digest_byte(label=assignment)&1 == 0 means "
    "A=agent/B=control; 1 means reverse",
    "assignment.first_method": "sort_domains_by_digest(label=first),then_id; "
    "first_two_agent_first,last_one_control_first",
    "assignment.round_1": "domain_order; assigned_first_method_case",
    "assignment.round_2": "domain_order_cyclic_left_shift_one; opposite_method_case",
    "assignment.record": [
        "seed",
        "protocol_sha256",
        "materials_sha256",
        "all_digests",
        "variant_assignment",
        "six_slot_order",
    ],
    "assignment.no_generation_or_reassignment_after_failure": True,
    "common_quality.mandatory_dimensions": [
        "accepted_scope_basis_unknowns_and_provenance_faithful",
        "all_critical_claims_correct_and_supported",
        "all_critical_conflicts_and_qualifiers_present",
        "subject_version_capture_and_UTF8_locator_correct",
        "unread_failure_partial_and_coverage_honest",
        "recommendations_distinguish_observation_inference_and_suggestion",
        "no_fabricated_execution_or_authority_and_actionable_next_verification",
    ],
    "common_quality.all_six_final_reports_pass_before_value_computation": True,
    "common_quality.median_saving_min": None,
    "common_quality.pair_saving_formula": "(control_active_seconds-agent_active_seconds)/control_active_seconds",
    "common_quality.aggregate": "descriptive_median_of_exactly_three_registered_heterogeneous_pairs; "
    "negative_savings_not_clipped; "
    "no_population_or_per_mode_effect_inference",
    "common_quality.missing_or_zero_baseline": "comparison_inconclusive_no_imputation_no_denominator_change",
    "common_quality.owner_final_and_original_program_outcomes_separate": True,
    "common_quality.machine_structure_check_is_not_semantic_verification": True,
    "common_quality.adequate_no_winner": "not_applicable_to_document_review; "
    "missing_documents_do_not_prove_absence; "
    "required_critical_gaps_are_partial",
    "common_quality.audits.max_defect_feedback_rounds": 2,
    "common_quality.audits.final_scoring_rounds": 1,
    "common_quality.audits.allowed_feedback": "defect_type_and_original_report_locator_only",
    "common_quality.audits.new_research_contribution": "must_disclose_actual_contribution_time_and_any_new_cost; "
    "not_pure_audit",
    "common_quality.audits.owner_does_actual_research_and_rewrite": True,
    "common_quality.raw_agent_critical_passes_required": 3,
    "common_quality.raw_agent_gate_separate_from_human_repaired_final": True,
    "common_quality.noncritical_results": "itemized_findings_and_omissions; "
    "no_composite_score_or_unbounded_recall_denominator",
    "common_quality.all_assigned_outcomes_retained": [
        "not_started",
        "started",
        "completed",
        "partial",
        "failed",
        "cancelled",
        "missing",
        "unscorable",
    ],
    "common_quality.three_result_axes": [
        "original_program_outcome",
        "original_immutable_report_source_review",
        "owner_final_submission_quality",
    ],
    "common_quality.real_user_or_team_value": "pending_no_real_task_evidence; "
    "controlled_materials_not_real_value_acceptance",
    "quotas.case_model.stages": [
        {
            "id": "clarify",
            "normal_obligations": 2,
            "max_input_tokens": 8192,
            "max_output_tokens": 2048,
        },
        {
            "id": "research_plan",
            "normal_obligations": 2,
            "max_input_tokens": 16384,
            "max_output_tokens": 2048,
        },
        {
            "id": "extract",
            "normal_obligations": 3,
            "max_input_tokens": 32768,
            "max_output_tokens": 4096,
        },
        {
            "id": "evidence_review",
            "normal_obligations": 2,
            "max_input_tokens": 32768,
            "max_output_tokens": 3072,
        },
        {
            "id": "gap_plan",
            "normal_obligations": 1,
            "max_input_tokens": 16384,
            "max_output_tokens": 2048,
        },
        {
            "id": "document_compile",
            "normal_obligations": 4,
            "max_input_tokens": 32768,
            "max_output_tokens": 8192,
        },
    ],
    "quotas.case_model.normal_obligations": 14,
    "quotas.case_model.technical_retry_max": 2,
    "quotas.case_model.technical_retry_per_work_max": 1,
    "quotas.case_model.technical_retry_eligibility": "only_known_transient_and_explicit_same_work_request_phase_caps; "
    "unknown/schema invalid not retryable",
    "quotas.case_model.physical_calls_max": 16,
    "quotas.case_model.normal_input_total": 360448,
    "quotas.case_model.normal_output_total": 61440,
    "quotas.case_model.with_two_max_retries_input_total": 425984,
    "quotas.case_model.with_two_max_retries_output_total": 77824,
    "quotas.case_model.cumulative_input_tokens": 458752,
    "quotas.case_model.cumulative_output_reservation_tokens": 81920,
    "quotas.case_model.format_repair_extra_calls": 0,
    "quotas.case_model.summary_extra_calls": 0,
    "quotas.case_model.thinking": "disabled_explicit",
    "quotas.case_model.output_limit": "explicit_per_stage",
    "quotas.case_model.tokenizer": "official_complete_request_matching_template_is_formal_admission_gate",
    "quotas.case_model.qualification_diagnostic": "separate_limited_authorized_path_not_circular_formal_prerequisite",
    "quotas.case_model.model_call_absolute_seconds": 60,
    "quotas.case_model.sdk_implicit_retries": 0,
    "quotas.case_model.qualification_profile": "official_supported_full_request_converter_template_tokenizer_hashes_and_fields; "
    "no_character_ratio_substitute; "
    "matching_evidence_pending_paid_off",
    "quotas.case_model.usage_mapping": "local_full_request_count_equals_prompt_tokens_under_frozen_qualification; "
    "hit_plus_miss_equals_prompt; "
    "total_equals_prompt_plus_completion; "
    "output_not_reencoded_to_prove_tokens",
    "quotas.case_model.qualification_revocation": "root_result_transaction_revokes_profile_revision; "
    "final_send_checks_current_revision; "
    "in_flight_original_call_settlement_only",
    "quotas.tools.per_case.search": 12,
    "quotas.tools.per_case.fetch": 24,
    "quotas.tools.per_case.github_data": 32,
    "quotas.tools.per_case.github_control": 64,
    "quotas.tools.per_case.browser_actions": 0,
    "quotas.tools.per_case.browser_http_requests": 0,
    "quotas.tools.counts_include_failures_retries_redirects_and_all_attempts": True,
    "quotas.tools.search_result_count": 5,
    "quotas.tools.search_need_content": False,
    "quotas.tools.unused_allocation": "no_automatic_expansion; "
    "stable_case_limits_include_linked_turns",
    "quotas.tools.extra_curator_or_semantic_judge_calls": 0,
    "quotas.tools.browser_before_network_qualification": 0,
    "quotas.tools.standalone_control_tasks_max": 4,
    "quotas.tools.standalone_control_attempts_per_task_max": 8,
    "quotas.tools.standalone_control_task_seconds": 60,
    "quotas.tools.private_proof_max_seconds": 300,
    "quotas.tools.private_proof": "fresh_restricted_App_installation_token_receipt_plus_stable_repo_identity_and_contents_probe; "
    "public_200_is_not_proof",
    "quotas.tools.outbound_disclosure": "whole_final_search_query_or_Fetch_URL_with_purpose_and_private_ancestor_lineage; "
    "public_words_do_not_declassify_combinations",
    "quotas.tools.browser_integration": "deferred_zero",
    "quotas.tools.mcp": "research_only",
    "quotas.tools.diagnostic_allocation": "all_profiles_turns_restarts_and_retries_share_one_exact_human_approved_total; "
    "no_auto_reallocation",
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
    "quotas.bytes.case_worst_reservation_mib": "64",
    "quotas.bytes.seven_cases_and_noncase_reservation_mib": "466.25",
    "quotas.bytes.count_actual_uncompressed_copies": True,
    "quotas.bytes.wal_indexes_checkpoints_backups": "separate_physical_qualification_not_covered_by_business_cap",
    "quotas.bytes.case_buckets_mib.model_requests_responses_manifests": "13",
    "quotas.bytes.case_buckets_mib.search": "1.5",
    "quotas.bytes.case_buckets_mib.github_fetch_capture_and_copies": "34.5",
    "quotas.bytes.case_buckets_mib.claim_relations": "4",
    "quotas.bytes.case_buckets_mib.stage_derived": "2",
    "quotas.bytes.case_buckets_mib.accepted_input": "3",
    "quotas.bytes.case_buckets_mib.tool_requests": "1",
    "quotas.bytes.case_buckets_mib.transport_metadata": "2",
    "quotas.bytes.case_buckets_mib.other_canonical_metadata": "2",
    "quotas.bytes.case_buckets_mib.terminal_memory_suggestions_control_receipts": "1",
    "quotas.bytes.project_metadata_max_mib": "32",
    "quotas.bytes.control_safe_receipt_max_bytes": 2048,
    "quotas.bytes.terminal_and_canonical_reserved_before_call": True,
    "budget.currency": "CNY_only_after_actual_account_qualification",
    "budget.cost_epoch": "2026-10-28_this_reopen_started",
    "budget.owner_attestation": "no_project_new_spend_outside_repository_since_cost_epoch; "
    "warehouse_and_historical_unknown_not_set_zero",
    "budget.model_physical_calls": 116,
    "budget.search_calls": 84,
    "budget.fetch_calls": 168,
    "budget.github_calls": 704,
    "budget.reserve_per_model_call_cny": "2.20",
    "budget.model_total_cny": "255.20",
    "budget.search_fetch_per_success_cny": "0.005",
    "budget.api_tools_cny": "1.26",
    "budget.noncall_cny": "30.00",
    "budget.unallocated_buffer_cny": "10.00",
    "budget.planned_total_cny": "296.46",
    "budget.new_spend_strictly_below_cny": "300.00",
    "budget.batches": [
        {
            "id": "qualification_and_unrelated_health",
            "case_count": 0,
            "model_calls": 4,
            "tool_calls": {
                "search": 0,
                "fetch": 0,
                "github_data": 0,
                "github_control": 32,
            },
            "worst_total_cny": "8.80",
        },
        {
            "id": "early",
            "case_count": 4,
            "roles": [
                "early_pilot_1",
                "early_pilot_2",
                "optimization_retest_1",
                "optimization_retest_2",
            ],
            "model_calls": 64,
            "tool_calls": {
                "search": 48,
                "fetch": 96,
                "github_data": 128,
                "github_control": 256,
            },
            "worst_total_cny": "141.52",
        },
        {
            "id": "formal_agent",
            "case_count": 3,
            "model_calls": 48,
            "tool_calls": {
                "search": 36,
                "fetch": 72,
                "github_data": 96,
                "github_control": 192,
            },
            "worst_total_cny": "106.14",
        },
    ],
    "budget.price_basis.model_input_uncached_per_million_cny": "2.00",
    "budget.price_basis.model_output_per_million_cny": "8.00",
    "budget.price_basis.conservative_input_tokens_per_physical_slot": 1048576,
    "budget.price_basis.output_tokens_per_physical_slot": 8192,
    "budget.price_basis.calculated_worst_model_call_cny": "2.162688",
    "budget.price_basis.qualification": "exact_model_template_fields_currency_tariff_and_complete_billable_basis_required; "
    "snapshot_not_locked_quote",
    "budget.price_basis.price_evidence_max_age_hours": 24,
    "budget.noncall_includes": [
        "backup_media",
        "paper_key_and_verification_cards",
        "new_comparison_subscription_or_session_charges",
        "any_other_new_project_fee",
        (
            "any_control_endpoint_fee_if_not_proven_free_requires_requalification; "
            "no_hidden_fee"
        ),
    ],
    "budget.existing_subscription_without_new_spend": "disclose_separately_not_fabricate_new_fee",
    "budget.buffer_not_automatic_grant": True,
    "budget.funds_price_history_unknown_inflight_balance_grants_unclosed": "paid_disabled",
    "budget.github_data_calls": 224,
    "budget.github_case_control_calls": 448,
    "budget.github_standalone_control_calls": 32,
    "budget.http_calls_max": 1072,
    "budget.dns_attempts_max": 2144,
    "budget.dial_attempts_max": 1072,
    "tracing.storage": "PostgreSQL_canonical_business_records_and_read_only_join_view_no_external_upload",
    "tracing.chain": [
        "input_revision_review_question_and_basis",
        "plan_work_attempt",
        "call",
        "source_representation_and_private_ancestor_lineage",
        "claim_relations",
        "context_manifest",
        "exact_safe_business_request_body",
        "response_usage_cost_reservation",
        "report_hash",
    ],
    "tracing.run_manifest_max_bytes": 65536,
    "tracing.manifest_counts_in": "stage_derived_2MiB_case_bucket",
    "tracing.freeze": [
        "code_and_dirty_tree",
        "dependency_lock",
        "schema",
        "template",
        "selector",
        "tokenizer",
        "public_model_identity",
        "pricing",
        "protocol",
        "materials",
    ],
    "tracing.unknown_cloud_weights_or_backend": "null_not_claimed_frozen",
    "tracing.canonical_records_not_sampled": True,
    "tracing.ui_ordinary_event_cap": 255,
    "tracing.safe_body_not_full_HTTP_wire": True,
    "tracing.no_hidden_chain_of_thought_collection": True,
    "tracing.reconstruction": "offline_read_only_artifact_integrity_relationship_selector_timing_usage_arithmetic; "
    "no_network_framework_replay_or_tokenizer_execution",
    "tracing.diagnostic_categories": [
        "not_collected",
        "unrecognized",
        "unbound",
        "not_selected",
        "cropped",
        "summary_distortion",
        "output_not_reflected",
    ],
    "tracing.model_internal_use_not_inferred_from_output": True,
    "tracing.delivery": "current_account_credential_auth_session_sup_generation_membership_purpose_share_source_proof_lineage_checked_per_bounded_response_page_SSE_frame; "
    "cursor_not_authority; logout_blocks_read_not_independent_Task",
    "tracing.delivery_limits_bytes.report": 65536,
    "tracing.delivery_limits_bytes.artifact_response": 1048576,
    "tracing.delivery_limits_bytes.SSE_frame": 1024,
    "tracing.revoke_delivery": "revoke_first_blocks_unclaimed_delivery; "
    "one_already_claimed_bounded_response_or_frame_may_arrive; "
    "no_instant_recall",
    "optimization.real_symptom_correction_required_at_least": 1,
    "optimization.real_retest_slots_max": 2,
    "optimization.sequence": [
        "original_trace_evidence",
        "preregister_falsifiable_observable_target",
        "minimal_change",
        "fixed_source_offline_regression_and_nonregression_AC",
        "independent_review",
        "separately_authorized_matched_real_retest",
    ],
    "optimization.changed_conditions_case": "same_case_A_report1_then_owner_accepted_B_linked_turn_report2_shared_caps_not_optimization_benefit",
    "optimization.keep_all_failed_experiments": True,
    "optimization.failed_rigorous_experiment_not_substitute_for_correction": True,
    "optimization.source_model_drift": "record_versions_hashes_and_confounding; "
    "no_direct_causal_claim_if_change_affects_symptom",
    "qualification.statuses": "pending_actual_evidence_not_satisfied_by_this_JSON",
    "qualification.before_first_pilot": [
        "safe_WSL_cold_cutover_and_new_Pg_cluster_roles",
        "official_tokenizer_and_gateway",
        "all_history_unknown_inflight_cost_reconciliation",
        "exact_service_side_grant_and_sufficient_balance",
        "independent_backup_media_paper_key_source_card_and_real_restore",
    ],
    "qualification.before_formal_reveal": [
        (
            "three_local_material_packages_and_exact_independent_original_review_bound_to_index; "
            "no_gold_in_worker_context"
        ),
        "all_method_eligibility_modes_and_engine_list",
        "code_template_policy_scoring_hash_freeze",
        "batch_and_slot_authorizations",
        "unrelated_service_health_check",
    ],
    "qualification.browser_unqualified": "disabled_zero",
    "qualification.global_unknown": "stop_all_project_new_outbound_keep_progress_and_reservations; "
    "later_settlement_never_auto_reopens; "
    "owner_separate_restore_approval_required",
    "historical_evidence.base_commit": "1ffade6de07ebe3d1e72afb4c44b8677466eca67",
    "historical_evidence.protocol_path": "docs/evaluation/CURRENT_EVAL_PROTOCOL.json",
    "historical_evidence.preparation_path": "data/evaluation/decision-m1-1/preparation.json",
    "historical_evidence.read_policy": "explicit_commit_path_raw_sha_and_explicit_newline_transform_only_no_auto_guess",
    "historical_evidence.old_execution_rules": "B/G/O_15_and_M1_9_8_12_are_historical_only",
    "historical_evidence.old_preparation": "materials_not_real_runs; "
    "referenced_sources_licenses_authorizations_cost_and_run_evidence_preserved",
    "historical_evidence.no_new_archive_copy": True,
    "historical_evidence.new_runner_or_ledger_implemented": False,
    "historical_evidence.previous_configuration.commit": "d4b906fb6a441c13583f052377283ec0c28bf5a2",
    "historical_evidence.previous_configuration.protocol_path": "docs/evaluation/CURRENT_EVAL_PROTOCOL.json",
    "historical_evidence.previous_configuration.protocol_raw_sha256": "98b832d33777c7aa045dd249ed005c1f915e55f3609d5872a5d62e58398111f0",
    "historical_evidence.previous_configuration.material_path": "docs/evaluation/DISCOVERY_M1_CASES.json",
    "historical_evidence.previous_configuration.material_raw_sha256": "5e448068f84dc491c0559b082b30e78886ed319e22112f11d6860aa529a51409",
    "release.current_state": "No-Go",
    "release.technical_verification_human_acceptance_value_M1_Go_release_separate": True,
    "release.this_protocol_not_runtime_permission": True,
    "attempt_record_contract.scope": "declarative_acceptance_contract_not_an_implemented_runner_or_ledger",
    "attempt_record_contract.required_fields.identity": [
        "slot_id",
        "case_id",
        "domain_id",
        "method",
        "owner_id",
        "team_id",
        "project_id",
        "requester_accepted_by_and_actual_actor",
        "batch_id",
        "case_and_linked_turn_ids",
        "protocol_sha256",
        "materials_sha256",
        "code_dirty_tree_and_lock_identity",
        "template_tool_memory_policy_identity",
        "visible_provider_model_mode_and_drift",
    ],
    "attempt_record_contract.required_fields.timing": [
        "disclosure_committed_at",
        "display_ack_and_clock_basis",
        "earliest_possible_exposure_and_timing_uncertain",
        "first_display_at",
        "wall_deadline",
        "active_intervals_with_start_end_kind_and_actor",
        "computed_active_seconds",
        "separate_wait_audit_admin_seconds",
        "final_submission_at",
        "stop_at_and_reason",
    ],
    "attempt_record_contract.required_fields.artifacts": [
        "original_program_or_DR_output_ref_sha256_or_missing_reason",
        "ordered_human_revisions_with_parent_ref_sha256_edit_time_and_active_interval_refs",
        "final_submission_ref_sha256",
        "mode_and_all_required_first_raw_document_refs_hashes_or_missing_reasons",
        "exact_requirements_confirmation_and_version_head_changes",
        "final_delivery_package_document_refs_hashes_and_confirmation",
    ],
    "attempt_record_contract.required_fields.audit": [
        "reviewer_identity_and_role",
        "round_and_feedback_time",
        "reviewed_report_sha256",
        "defect_locators",
        "actual_research_contribution_time_cost_and_disclosure",
        "final_dimension_scores_and_pass",
    ],
    "attempt_record_contract.required_fields.outcomes": [
        "raw_program_status_and_errors",
        "safety_authority_unknown_stop_state",
        "final_human_quality_status",
        "cancel_failure_missing_unexecuted_reason",
        "familiarity_and_source_knowledge_transfer",
        "memory_disabled_not_applicable_null_hits_writes_feature_disabled_and_empty_active_refs",
        "raw_agent_critical_quality_status",
        "assigned_slot_denominator_including_unstarted_and_missing",
    ],
    "attempt_record_contract.required_fields.cost": [
        "call_and_transport_identity_refs",
        "local_tokens_provider_usage_cache_and_unknowns",
        "pricing_currency_and_cost_evidence",
        "known_unknown_inflight_reservations",
        "grant_allocation_and_incremental_spend_epoch",
        "comparison_existing_subscription_and_new_purchase_disclosure",
    ],
    "attempt_record_contract.active_intervals": "owner intervals ordered and nonoverlapping; "
    "every research action belongs to one interval; "
    "active_seconds equals sum, pure waits "
    "separately in wall time; no cap imputation",
    "attempt_record_contract.revision_chain": "immutable original plus every submitted human "
    "revision; parent hashes link in order; "
    "edit/research/recheck time included; no "
    "replacement after final scoring or revealed "
    "failure",
    "attempt_record_contract.audit_binding": "feedback and final scoring bind exact reviewed "
    "report hash; new research contribution is "
    "disclosed and cannot masquerade as pure defect "
    "audit",
    "attempt_record_contract.unavailable": "explicit null or missing_reason; never fabricate "
    "zero, successful output or a report hash",
    "attempt_record_contract.integrity": "independent_audit_recomputes_artifact_hashes_timing_sums_all_six_slots_and_three_pair_descriptive_median; "
    "raw_agent_quality_is_separate",
    "attempt_record_contract.private_content": "current_team_project_and_source_purpose_permissions_on_derived_artifacts; "
    "private_Draft_and_Memory_author_isolation; "
    "no_secrets_or_hidden_reasoning",
    "memory": FOCUS_MEMORY_POLICY,
    "attempt_record_contract.memory_observation": FOCUS_MEMORY_OBSERVATION,
    "documents": {
        "versions_per_case": 16,
        "body_bytes": 65536,
        "metadata_bytes": 16384,
        "bucket": "stage_derived_2MiB_actual_copies",
        "first_full_chain_reserve_slots": 2,
        "first_full_chain_reserve_bytes": 163840,
        "snapshot": "bounded_refs_only_report_64KiB_no_inline_two_documents",
        "versions": "immutable_author_parent_hash_known_lineage; "
        "raw_private_Draft_separate",
        "confirmation": "exact_current_requirements_version_hash_actor_CAS; "
        "every_new_requirement_head_clears_current_confirmation_in_same_root_transaction; "
        "history_immutable",
        "solution_gates": "start_send_commit_current_requirement_head_and_confirmation_and_target_solution_parent_head_CAS; "
        "stale_derived_from_refs; "
        "late_original_Call_audit_usage_cost_only",
        "editing": "explicit_save_or_AI_commit_not_keystrokes; "
        "bounded_UI_memory_no_localStorage; logout_identity_switch_clears; "
        "conflict_visible_no_silent_overwrite",
    },
    "local_materials": {
        "items_per_case_cumulative": 32,
        "metadata_request_bytes": 16384,
        "raw_item_bytes": 1048576,
        "decoded_utf8_bytes": 524288,
        "absolute_receive_seconds": 30,
        "transport": "raw_application_octet_stream_not_multipart; "
        "application_stream_actual_bytes_limit_before_default_body_parser; "
        "reject_nonidentity_ContentEncoding; "
        "headers_request_line_buffers_pending_real_qualification",
        "admission": "current_session_sup_case_project_retain_use_and_reserve_before_body; "
        "no_DB_lock_while_receiving; "
        "commit_rechecks_current_gates_set_version_actual_bytes; "
        "atomic_body_hash_capture",
        "source_set": "seal_successes_failures_unread_before_model_use; "
        "no_fake_capture; safe_errors; "
        "only_determinate_unused_reserve_released",
        "capture_bucket": "shared_github_fetch_capture_and_copies_34.5MiB; "
        "case64MiB_project1GiB; no_all_maxima_guarantee",
        "identity": "explicit_File_API_selection_not_filesystem_bridge; "
        "no_path_open_execution_diff_apply_zip_binary_parser; "
        "unknown_diff_base_not_verified_commit; "
        "no_atomic_worktree_or_symlink_proof",
        "privacy": "current_author_project_retention_use_model_share_public_disclosure; "
        "known_private_ancestry_survives_edits_imports_exports_new_ID; "
        "local_unknown_origin_not_GitHub_App_proof_or_global_copy_detector; "
        "known_private_GitHub_ancestors_still_require_App_proof",
    },
    "formal.workflow_coverage": {
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
    },
    "formal.coverage_limits": {
        "requirements_only": "focused_route_terminal_regression_and_one_existing_pilot; "
        "no_independent_formal_quality_or_time_claim",
        "editing_and_revision": "regression_and_pilot_only_no_independent_formal_effect_claim",
        "pair_equivalence": "same_preregistered_goal_scale_material_format_mix; "
        "clarify_cannot_shrink_goal; "
        "substantive_scope_change_retains_slot_partial_noncomparable",
        "alternative_designs": "reasonable_supported_alternatives_allowed_no_single_hidden_design_answer",
        "pilot_allocation": "one_existing_pilot_requirements_only_and_other_full_chain; "
        "no_extra_cases_or_funding",
    },
    "common_quality.raw_full_chain": "both_first_raw_requirements_and_first_raw_solution_must_pass; "
    "human_edits_do_not_rewrite_raw_failure",
    "common_quality.final_package": "each_slot_final_snapshot_binds_all_required_document_versions_hashes_and_confirmation; "
    "full_chain_scores_both_documents",
    "quotas.case_model.compile_reserved_input_tokens": 131072,
    "quotas.case_model.compile_reserved_output_tokens": 32768,
    "quotas.case_model.compile_reserve_borrowable": False,
    "quotas.case_model.mode_obligations": {
        "review_only": {"first_artifacts": 1, "semantic_revisions_max": 3},
        "requirements_only": {"first_artifacts": 1, "semantic_revisions_max": 3},
        "solution_only": {"first_artifacts": 1, "semantic_revisions_max": 3},
        "requirements_to_solution": {"first_artifacts": 2, "semantic_revisions_max": 2},
    },
    "quotas.case_model.first_artifact_reservation": "atomic_compile_token_version_slot_80KiB_envelope_and_canonical_terminal_before_optional_edit_or_stage_write; "
    "reserve_to_used_once; no_send_if_unsavable",
    "quotas.case_model.revision_and_mode_changes": "same_case_caps_and_original_purpose; "
    "changed_requirements_need_new_confirmation_and_use_remaining_compiles; "
    "no_unlimited_first_solution_guarantee; "
    "accepted_mode_change_atomically_reserves_missing_first_obligations_or_rejects; "
    "no_auto_new_case",
    "quotas.case_model.hidden_judge_extra_calls": 0,
    "historical_evidence.previous_review_configuration": {
        "revision": "REVIEW-BASELINE-20261101",
        "manifest_path": ".tmp/predev-reopen-20261028/config-20261029/review-20261101/snapshots/final-02/manifest.json",
        "manifest_raw_sha256": "582636a65e3dc0b0405f1fd0ce232935d649c49b6202660eccbdbf50f0ee9768",
        "protocol_raw_sha256": "234fbaa98a8e889103f0537582cedba71575519d7a342685e559bafac75be557",
        "material_raw_sha256": "763129484b2bfbc6c0eedda13b680a1ae00a2b649319da2d3aac79227b2563e5",
        "read_policy": "explicit_existing_snapshot_manifest_path_raw_hash; "
        "not_a_HEAD_Git_object; "
        "no_old_index_overwrite_or_runner_extension",
    },
    "historical_evidence.previous_draft_configuration": {
        "revision": "DRAFT-BASELINE-20261102",
        "manifest_path": ".tmp/predev-reopen-20261028/config-20261029/review-20261101/draft-20261102/snapshots/final-01/manifest.json",
        "manifest_raw_sha256": "6c9b4b59a8362033745be68239fe846cac79d4cdd62b392def922f7ef9952faf",
        "protocol_raw_sha256": "2628db01d144cfefb7c8db55e62ac67243beb93c5d8b9a74273446ada34e33b6",
        "material_raw_sha256": "f1a93cef17832629cc0a14f906d6295a17561bfc5e458f945d18610e026f4fc1",
        "read_policy": "explicit_existing_snapshot_manifest_path_raw_hash; not_a_HEAD_Git_object; no_old_index_overwrite_or_runner_extension",
    },
}


REVIEW_CAPABILITIES = [
    {
        "id": "runtime_harness",
        "requirements": [
            "DEC-AC-08",
            "DEC-AC-09",
            "DEC-AC-13",
            "DEC-AC-14",
        ],
        "tasks": [
            "DEC-M1-02",
            "DEC-M1-03b",
        ],
        "evidence": [
            "real_LangGraph_stage_nodes",
            "restricted_Pg_atomicity_and_dual_order_races",
            "stable_obligations_no_completed_unknown_resend",
            "unique_terminal_and_generation_resource_release",
            "immutable_document_versions_current_head_exact_confirmation_dual_order_solution_gates",
            "first_artifact_multidimensional_reservation_no_unsavable_send",
        ],
    },
    {
        "id": "tools_search_evidence",
        "requirements": [
            "DEC-AC-10",
            "DEC-AC-11",
            "DEC-AC-12",
            "DEC-AC-15",
        ],
        "tasks": [
            "DEC-M1-03a",
            "DEC-M1-03b",
            "DEC-M1-05",
        ],
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
        "requirements": [
            "DEC-AC-18",
        ],
        "tasks": [
            "DEC-M1-03a",
            "DEC-M1-03b",
        ],
        "evidence": [
            "protected_conditions_qualifiers_counterevidence",
            "bounded_manifest_selection_and_failure_diagnostics",
            "official_complete_request_tokenizer_qualification",
            "fixed_source_offline_cases_and_natural_authorized_trace_not_extra_call_batch",
        ],
    },
    {
        "id": "evaluation_tracing_optimization",
        "requirements": [
            "DEC-AC-16",
            "DEC-AC-19",
            "DEC-AC-20",
        ],
        "tasks": [
            "DEC-M1-06",
            "DEC-M1-07",
            "DEC-M1-08b",
        ],
        "evidence": [
            "complete_six_attempts_and_manual_time_final_quality",
            "canonical_trace_and_offline_no_send_reconstruction",
            "at_least_one_real_symptom_corrected_with_matched_evidence",
            "all_failed_experiments_and_confounding_retained",
            "all_three_raw_Agent_reports_critical_quality_pass",
            "six_final_human_reports_and_descriptive_time_comparison_no_20pct_gate",
            "display_permission_and_actual_display_separate",
        ],
    },
    {
        "id": "identity_recovery_practice",
        "requirements": [
            "DEC-AC-15",
            "DEC-AC-14",
        ],
        "tasks": [
            "DEC-M1-01",
            "ENV-M1-01",
            "ENV-M1-02",
            "DEC-M1-08b",
        ],
        "evidence": [
            "one_real_owner_second_test_identity_object_isolation",
            "continuous_supervisor_identity_qualification",
            "paper_key_independent_source_card_real_restore",
            "owner_actual_read_explain_edit_debug_regress_and_business_acceptance",
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
    "formal_materials": "pending_independent_preparation_no_new_gold_this_configuration_batch",
    "drafting_modes": "three_pairs_full_review_solution; requirements_only_and_edit_revision_pilot_regression_not_independent_formal_effect",
    "memory": "disabled_all_entrypoints_no_store_snapshot_or_seed_required; deferred_not_completed",
    "private_sources": "retained_scope_after_prioritized_public_vertical_slice_not_claimed_complete",
    "automatic_memory": "deferred_not_required_for_current_M1; reactivation_requires_real_reuse_need_separate_review_and_scope_approval",
}


MATERIAL_INDEX_PATH = "docs/evaluation/DISCOVERY_M1_CASES.json"
MATERIAL_ROOT = ".tmp/predev-reopen-20261028/config-20261029/review-20261101/focus-20261102/materials"
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
    """Recompute the approved arithmetic; never qualifies runtime or funds."""
    try:
        model = protocol["quotas"]["case_model"]
        stages = model["stages"]
        inputs = sum(s["normal_obligations"] * s["max_input_tokens"] for s in stages)
        outputs = sum(s["normal_obligations"] * s["max_output_tokens"] for s in stages)
        calls = sum(s["normal_obligations"] for s in stages)
        compile_stage = next(s for s in stages if s["id"] == "document_compile")
        retries = model["technical_retry_max"]
        worst_in = inputs + retries * max(s["max_input_tokens"] for s in stages)
        worst_out = outputs + retries * max(s["max_output_tokens"] for s in stages)
        documents = protocol["documents"]
        valid = (
            (calls, inputs, outputs)
            == (
                model["normal_obligations"],
                model["normal_input_total"],
                model["normal_output_total"],
            )
            and calls + retries == model["physical_calls_max"]
            and worst_in
            == model["with_two_max_retries_input_total"]
            <= model["cumulative_input_tokens"]
            and worst_out
            == model["with_two_max_retries_output_total"]
            <= model["cumulative_output_reservation_tokens"]
            and compile_stage["normal_obligations"] * compile_stage["max_input_tokens"]
            == model["compile_reserved_input_tokens"]
            and compile_stage["normal_obligations"] * compile_stage["max_output_tokens"]
            == model["compile_reserved_output_tokens"]
            and documents["first_full_chain_reserve_slots"]
            * (documents["body_bytes"] + documents["metadata_bytes"])
            == documents["first_full_chain_reserve_bytes"]
            and all(
                m["first_artifacts"] + m["semantic_revisions_max"]
                == compile_stage["normal_obligations"]
                for m in model["mode_obligations"].values()
            )
        )
        return [] if valid else ["draft reservation arithmetic mismatch"]
    except (KeyError, TypeError, ValueError, StopIteration, AttributeError):
        return ["draft reservation arithmetic malformed"]


def check_current_protocol(protocol: object, root: Path) -> list[str]:
    """Validate configuration policy, never real readiness, execution or funding."""
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
    contamination = (
        protocol.get("methods", {}).get("contamination")
        if isinstance(protocol.get("methods"), dict)
        else None
    )
    if (
        isinstance(contamination, dict)
        and "memory_policy_frozen_data_changes_and_hits_disclosed" in contamination
    ):
        errors.append(
            "current Memory cannot restore active snapshot or hit obligations"
        )
    errors.extend(_check_draft_reservations(protocol))
    tools = (
        protocol.get("quotas", {}).get("tools")
        if isinstance(protocol.get("quotas"), dict)
        else None
    )
    if isinstance(tools, dict) and any(
        key in tools
        for key in (
            "routes_max",
            "candidate_identity_pool_max",
            "shortlist_max",
            "stage_allocations",
        )
    ):
        errors.append(
            "current document review cannot restore candidate selection quotas"
        )
    material_ref = protocol.get("materials")
    if (
        not isinstance(material_ref, dict)
        or material_ref.get("path") != MATERIAL_INDEX_PATH
    ):
        return errors + ["current materials reference is missing or noncanonical"]
    try:
        raw = _read_material_bytes(root, root / MATERIAL_INDEX_PATH)
        if len(raw) > MATERIAL_BYTES_MAX:
            raise ValueError("oversized index")
        if hashlib.sha256(raw).hexdigest() != material_ref.get("sha256"):
            errors.append("current material SHA-256 mismatch")
        index = _load_current_json(raw)
        errors.extend(check_current_materials(index))
        if isinstance(index, dict) and material_ref.get("review_status") != index.get(
            "status"
        ):
            errors.append("current material readiness reference mismatch")
    except (OSError, ValueError, TypeError):
        errors.append("current materials unreadable")
    try:
        raw = _read_material_bytes(
            root, root / "docs/evaluation/DECISION_M1_PROTOCOL.json"
        )
        if len(raw) > MATERIAL_BYTES_MAX:
            raise ValueError("oversized supplement")
        errors.extend(check_current_supplement(_load_current_json(raw), root))
    except (OSError, ValueError, TypeError):
        errors.append("current supplement unreadable")
    return errors


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
        "protocol_version": "draft-m1-2",
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
        or package.get("protocol_version") != "draft-m1-2"
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
    root: Path, material_root: Path, index_sha256: str
) -> list[str]:
    """Explicit local qualification only; never follows arbitrary manifest paths."""
    errors: list[str] = []
    try:
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


def check_current_supplement(supplement: object, root: Path) -> list[str]:
    if not isinstance(supplement, dict):
        return ["M1 supplement must be an object"]
    errors: list[str] = []
    if (
        supplement.get("protocol_version") != "draft-m1-capabilities-2"
        or supplement.get("role") != "capability_acceptance_reference"
    ):
        errors.append("M1 supplement must reference sole current authority")
    expected = {
        "path": PROTOCOL,
        "version": "draft-m1-2",
        "sha256": hashlib.sha256((root / PROTOCOL).read_bytes()).hexdigest(),
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
    elif material_requested:
        errors.extend(
            check_review_material_files(
                root, args.review_material_root, args.review_material_index_sha256
            )
        )
    if not args.historical_only:
        errors.extend(check_links(root, project_document_files(root)))
        errors.extend(check_versions_and_traceability(root))
        errors.extend(check_skills(root))
        errors.extend(check_archive_manifest(root))
        errors.extend(check_archive_git_index(root))
        try:
            protocol = _load_current_json(_read_material_bytes(root, root / PROTOCOL))
            errors.extend(check_current_protocol(protocol, root))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"current protocol unreadable: {type(exc).__name__}")
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
