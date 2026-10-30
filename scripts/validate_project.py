"""Deterministic offline checks for the current development configuration.

Usage: python scripts/validate_project.py [--root PATH] [--results JSON] [--ledger JSON]
The optional files are completed evidence, not run triggers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
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
CURRENT_PROTOCOL_VERSION = "discovery-m1-1"
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


def check_current_protocol(protocol: object, root: Path) -> list[str]:
    """Check the approved configuration; this never evaluates a live result.

    Review metadata can be pending. Passing this check does not grant readiness,
    prove semantic source support, execute a case, or authorize spending.
    """
    if not isinstance(protocol, dict):
        return ["current protocol must be an object"]
    errors: list[str] = []
    if protocol.get("status") not in (
        "prepared_pending_material_and_actual_file_review",
        "frozen_pending_qualification_and_execution",
    ):
        errors.append("current configuration status cannot claim execution or Go")

    def require(path: str, expected: object) -> None:
        actual: object = protocol
        for key in path.split("."):
            if not isinstance(actual, dict) or key not in actual:
                errors.append(f"current protocol missing {path}")
                return
            actual = actual[key]
        if not _json_equal(actual, expected):
            errors.append(f"current protocol policy differs: {path}")

    for path, expected in {
        "protocol_version": "discovery-m1-1",
        "preparation_revision": "PREP-BASELINE-20261029",
        "authority": "SPEC.md",
        "authorization.configuration_only": True,
        "authorization.real_run_requires_specific_separate_authorization": True,
        "formal.domain_ids": ["scheduling", "data_migration", "document_processing"],
        "formal.case_ids": ["SCH-A", "SCH-B", "DAT-A", "DAT-B", "DOC-A", "DOC-B"],
        "formal.expected_attempts": 6,
        "formal.agent_attempts": 3,
        "formal.control_attempts": 3,
        "formal.all_attempts_retained": True,
        "formal.no_replacements": True,
        "formal.version_frozen": True,
        "formal.code_templates_tools_quotas_scoring_frozen": True,
        "methods.agent.external_ai_repair_allowed": False,
        "methods.agent.deliberate_control_output_or_note_copy_allowed": False,
        "methods.control.independent_deep_research.required": True,
        "methods.control.independent_deep_research.sessions_per_task": 1,
        "methods.control.independent_deep_research.same_product_and_mode_all_three": True,
        "methods.manual_search.same_pre_registered_engine_list_both_methods": True,
        "methods.manual_search.switching_allowed": True,
        "methods.manual_search.arbitrary_query_count_cap": None,
        "methods.manual_search.all_owner_actions_count_active_time": True,
        "methods.contamination.no_true_blinding_claim": True,
        "timing.active_minutes_per_attempt": 120,
        "timing.wall_hours_per_attempt": 24,
        "timing.batch_days": 14,
        "timing.active_start": "first_actual_display_of_exact_case_prompt",
        "timing.max_extensions": 1,
        "timing.unrevealed_extension_days": 7,
        "timing.revealed_attempt_extension_allowed": False,
        "assignment.algorithm_version": "ARA-EVAL-1",
        "assignment.seed_bits": 128,
        "assignment.seed_hex_chars": 32,
        "assignment.no_generation_or_reassignment_after_failure": True,
        "common_quality.all_six_final_reports_pass_before_value_computation": True,
        "common_quality.median_saving_min": 0.2,
        "common_quality.owner_final_and_original_program_outcomes_separate": True,
        "common_quality.machine_structure_check_is_not_semantic_verification": True,
        "common_quality.audits.max_defect_feedback_rounds": 2,
        "common_quality.audits.final_scoring_rounds": 1,
        "quotas.case_model.normal_obligations": 14,
        "quotas.case_model.technical_retry_max": 2,
        "quotas.case_model.technical_retry_per_work_max": 1,
        "quotas.case_model.physical_calls_max": 16,
        "quotas.case_model.normal_input_total": 360448,
        "quotas.case_model.normal_output_total": 50176,
        "quotas.case_model.with_two_max_retries_input_total": 425984,
        "quotas.case_model.with_two_max_retries_output_total": 66560,
        "quotas.case_model.cumulative_input_tokens": 458752,
        "quotas.case_model.cumulative_output_reservation_tokens": 73728,
        "quotas.case_model.report_reserved_input_tokens": 65536,
        "quotas.case_model.report_reserved_output_tokens": 16384,
        "quotas.case_model.report_reserve_borrowable": False,
        "quotas.case_model.format_repair_extra_calls": 0,
        "quotas.case_model.summary_extra_calls": 0,
        "quotas.case_model.thinking": "disabled_explicit",
        "quotas.tools.counts_include_failures_retries_redirects_and_all_attempts": True,
        "quotas.tools.search_result_count": 5,
        "quotas.tools.search_need_content": False,
        "quotas.tools.routes_max": 3,
        "quotas.tools.candidate_identity_pool_max": 20,
        "quotas.tools.shortlist_max": 3,
        "quotas.tools.extra_curator_or_semantic_judge_calls": 0,
        "quotas.tools.browser_before_network_qualification": 0,
        "quotas.bytes.artifact_max": 1048576,
        "quotas.bytes.turn_max": 67108864,
        "quotas.bytes.case_max_shared_across_turns": 67108864,
        "quotas.bytes.project_new_business_max": 1073741824,
        "quotas.bytes.case_worst_reservation_mib": "57.5",
        "quotas.bytes.seven_cases_and_noncase_reservation_mib": "419.75",
        "quotas.bytes.count_actual_uncompressed_copies": True,
        "budget.model_physical_calls": 116,
        "budget.search_calls": 84,
        "budget.fetch_calls": 168,
        "budget.github_calls": 56,
        "budget.reserve_per_model_call_cny": "2.20",
        "budget.model_total_cny": "255.20",
        "budget.search_fetch_per_success_cny": "0.005",
        "budget.api_tools_cny": "1.26",
        "budget.noncall_cny": "30.00",
        "budget.unallocated_buffer_cny": "10.00",
        "budget.planned_total_cny": "296.46",
        "budget.new_spend_strictly_below_cny": "300.00",
        "budget.buffer_not_automatic_grant": True,
        "budget.price_basis.model_input_uncached_per_million_cny": "2.00",
        "budget.price_basis.model_output_per_million_cny": "8.00",
        "budget.price_basis.conservative_input_tokens_per_physical_slot": 1048576,
        "budget.price_basis.output_tokens_per_physical_slot": 8192,
        "budget.price_basis.calculated_worst_model_call_cny": "2.162688",
        "budget.price_basis.price_evidence_max_age_hours": 24,
        "tracing.run_manifest_max_bytes": 65536,
        "tracing.canonical_records_not_sampled": True,
        "tracing.ui_ordinary_event_cap": 255,
        "tracing.safe_body_not_full_HTTP_wire": True,
        "tracing.no_hidden_chain_of_thought_collection": True,
        "tracing.model_internal_use_not_inferred_from_output": True,
        "optimization.real_symptom_correction_required_at_least": 1,
        "optimization.real_retest_slots_max": 2,
        "optimization.keep_all_failed_experiments": True,
        "optimization.failed_rigorous_experiment_not_substitute_for_correction": True,
    }.items():
        require(path, expected)
    for key in (
        "business_implementation",
        "environment_or_database_write",
        "dependency_install",
        "model_tokenizer_browser_execution",
        "paid_execution",
        "purchase",
        "git_write",
    ):
        require(f"authorization.{key}", False)
    require(
        "attempt_record_contract.scope",
        "declarative_acceptance_contract_not_an_implemented_runner_or_ledger",
    )
    for group, fields in {
        "identity": [
            "slot_id",
            "case_id",
            "domain_id",
            "method",
            "owner_id",
            "batch_id",
            "case_and_linked_turn_ids",
            "protocol_sha256",
            "materials_sha256",
            "code_dirty_tree_and_lock_identity",
            "template_tool_memory_policy_identity",
            "visible_provider_model_mode_and_drift",
        ],
        "timing": [
            "first_display_at",
            "wall_deadline",
            "active_intervals_with_start_end_kind_and_actor",
            "computed_active_seconds",
            "separate_wait_audit_admin_seconds",
            "final_submission_at",
            "stop_at_and_reason",
        ],
        "artifacts": [
            "original_program_or_DR_output_ref_sha256_or_missing_reason",
            "ordered_human_revisions_with_parent_ref_sha256_edit_time_and_active_interval_refs",
            "final_submission_ref_sha256",
        ],
        "audit": [
            "reviewer_identity_and_role",
            "round_and_feedback_time",
            "reviewed_report_sha256",
            "defect_locators",
            "actual_research_contribution_time_cost_and_disclosure",
            "final_dimension_scores_and_pass",
        ],
        "outcomes": [
            "raw_program_status_and_errors",
            "safety_authority_unknown_stop_state",
            "final_human_quality_status",
            "cancel_failure_missing_unexecuted_reason",
            "familiarity_and_source_knowledge_transfer",
            "memory_hits_writes_and_pre_case_identity",
        ],
        "cost": [
            "call_and_transport_identity_refs",
            "local_tokens_provider_usage_cache_and_unknowns",
            "pricing_currency_and_cost_evidence",
            "known_unknown_inflight_reservations",
            "grant_allocation_and_incremental_spend_epoch",
            "comparison_existing_subscription_and_new_purchase_disclosure",
        ],
    }.items():
        require(f"attempt_record_contract.required_fields.{group}", fields)
    for key, value in {
        "active_intervals": "owner intervals ordered and nonoverlapping; every research action belongs to one interval; active_seconds equals sum, pure waits separately in wall time; no cap imputation",
        "revision_chain": "immutable original plus every submitted human revision; parent hashes link in order; edit/research/recheck time included; no replacement after final scoring or revealed failure",
        "audit_binding": "feedback and final scoring bind exact reviewed report hash; new research contribution is disclosed and cannot masquerade as pure defect audit",
        "unavailable": "explicit null or missing_reason; never fabricate zero, successful output or a report hash",
        "integrity": "independent audit recomputes artifact hashes, timing sums, case-slot mapping and paired median before any value pass; all six retained",
        "private_content": "owner-only artifacts; safe public summary refs/codes; no password, cookie, API key or hidden reasoning chain",
    }.items():
        require(f"attempt_record_contract.{key}", value)
    require(
        "quotas.runtime",
        {
            "global_active_tasks": 2,
            "global_queued_tasks": 4,
            "nonterminal_task_per_session": 1,
            "tasks_per_case": 8,
            "read_branches_per_turn": 2,
            "global_read_branches": 4,
            "model_physical_inflight": 2,
            "qualified_browser_physical_inflight": 1,
            "lease_seconds": 30,
            "heartbeat_seconds": 5,
            "recoveries_per_original_task": 1,
            "queue_seconds": 300,
            "discussion_seconds": 600,
            "research_seconds": 2700,
            "case_worker_seconds": 3600,
            "ordinary_case_wall_seconds": 604800,
            "formal_case_wall_seconds": 86400,
        },
    )
    require(
        "quotas.tools.per_case",
        {
            "search": 12,
            "fetch": 24,
            "github": 8,
            "browser_actions": 8,
            "browser_http_requests": 240,
        },
    )
    stages = [
        ("clarify", 2, 8192, 2048),
        ("route_plan", 2, 16384, 2048),
        ("discovery_extract", 2, 32768, 4096),
        ("shortlist_analysis", 3, 32768, 3072),
        ("gap_plan", 1, 16384, 2048),
        ("gap_extract", 2, 32768, 3072),
        ("report", 2, 32768, 8192),
    ]
    require(
        "quotas.case_model.stages",
        [
            {
                "id": name,
                "normal_obligations": count,
                "max_input_tokens": inp,
                "max_output_tokens": out,
            }
            for name, count, inp, out in stages
        ],
    )
    require(
        "quotas.tools.stage_allocations",
        [
            {"stage": "discovery", "search": 6, "fetch": 6, "github": 2},
            {"stage": "shortlist_deep", "search": 3, "fetch": 12, "github": 4},
            {"stage": "gap", "search": 3, "fetch": 6, "github": 2},
        ],
    )
    require(
        "budget.batches",
        [
            {
                "id": "qualification_and_unrelated_health",
                "case_count": 0,
                "model_calls": 4,
                "tool_calls": {"search": 0, "fetch": 0, "github": 0},
                "worst_total_cny": "8.80",
            },
            {
                "id": "early",
                "case_count": 4,
                "roles": [
                    "original_requirement",
                    "changed_conditions_capability",
                    "optimization_retest_1",
                    "optimization_retest_2",
                ],
                "model_calls": 64,
                "tool_calls": {"search": 48, "fetch": 96, "github": 32},
                "worst_total_cny": "141.52",
            },
            {
                "id": "formal_agent",
                "case_count": 3,
                "model_calls": 48,
                "tool_calls": {"search": 36, "fetch": 72, "github": 24},
                "worst_total_cny": "106.14",
            },
        ],
    )
    materials_ref = protocol.get("materials")
    if (
        not isinstance(materials_ref, dict)
        or materials_ref.get("path") != "docs/evaluation/DISCOVERY_M1_CASES.json"
    ):
        return errors + ["current materials reference is missing or noncanonical"]
    try:
        raw = (root / materials_ref["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != materials_ref.get("sha256"):
            errors.append("current material SHA-256 mismatch")
        materials = _load_current_json(raw)
        errors.extend(check_current_materials(materials))
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"current materials unreadable: {type(exc).__name__}")
    try:
        supplement = _load_current_json(
            (root / "docs/evaluation/DECISION_M1_PROTOCOL.json").read_bytes()
        )
        errors.extend(check_current_supplement(supplement, root))
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"current supplement unreadable: {type(exc).__name__}")
    return errors


def check_current_materials(materials: object) -> list[str]:
    """Reject malformed types without printing hidden task material."""
    try:
        return _check_current_materials(materials)
    except (KeyError, TypeError, ValueError, AttributeError):
        return ["current materials have malformed nested types"]


def _check_current_materials(materials: object) -> list[str]:
    """Structural isolation and completeness only; independent review judges content."""
    if not isinstance(materials, dict):
        return ["current materials must be an object"]
    errors: list[str] = []
    ids = {"SCH-A", "SCH-B", "DAT-A", "DAT-B", "DOC-A", "DOC-B"}
    if (
        materials.get("schema_version") != "discovery-m1-cases-1"
        or materials.get("protocol_version") != "discovery-m1-1"
    ):
        errors.append("current material version mismatch")
    ready = materials.get("readiness")
    if not isinstance(ready, dict) or any(
        not _json_equal(ready.get(key), value)
        for key, value in {
            "executed": False,
            "formal_seed": None,
            "formal_attempts": 0,
            "provider_calls": 0,
        }.items()
    ):
        errors.append("configuration materials cannot claim execution or a formal seed")
    agent = materials.get("agent_input")
    controller = materials.get("controller_only")
    scorer = materials.get("scorer_only")
    if not all(isinstance(part, dict) for part in (agent, controller, scorer)):
        return errors + ["materials require separated input/controller/scorer objects"]
    if agent.get("allowlist_paths") != [
        "#/agent_input/cases/{current_case_only}",
        "#/controller_only/clarification_cards/{current_case_only}/answer_units/{current_question_only}",
        "#/controller_only/clarification_cards/{current_case_only}/accepted_conditions (only after owner explicitly accepts)",
    ]:
        errors.append("material input allowlist must exclude gold and other cases")
    cases = agent.get("cases")
    if not isinstance(cases, list) or len(cases) != 6:
        return errors + ["materials require exactly six cases"]
    if any(not isinstance(case, dict) for case in cases):
        return errors + ["material case must be an object"]
    if {case.get("case_id") for case in cases} != ids:
        errors.append("material case IDs must be unique and complete")
    for case in cases:
        if set(case) != {
            "case_id",
            "domain_id",
            "variant",
            "prompt",
            "output_requirements",
        }:
            errors.append("case input contains unsupported fields or scorer leakage")
        if (
            not isinstance(case.get("prompt"), str)
            or not case["prompt"].strip()
            or not isinstance(case.get("output_requirements"), list)
            or not case["output_requirements"]
            or any(
                not isinstance(item, str) or not item.strip()
                for item in case["output_requirements"]
            )
        ):
            errors.append("case input requires exact prompt and output requirements")
        if case.get("variant") not in {"A", "B"}:
            errors.append("case variant must be A or B")
        elif case.get("case_id") in ids and case["variant"] != case["case_id"][-1]:
            errors.append("case variant must match case ID suffix")
    cards, rubrics = controller.get("clarification_cards"), scorer.get("case_rubrics")
    if (
        not isinstance(cards, dict)
        or set(cards) != ids
        or not isinstance(rubrics, dict)
        or set(rubrics) != ids
    ):
        return errors + ["every case needs one clarification card and scorer rubric"]
    sources = materials.get("source_manifest")
    if (
        not isinstance(sources, list)
        or not sources
        or any(not isinstance(source, dict) for source in sources)
    ):
        return errors + ["material source manifest is missing"]
    source_ids = [source.get("id") for source in sources]
    if any(not isinstance(sid, str) or not sid for sid in source_ids) or len(
        set(source_ids)
    ) != len(source_ids):
        errors.append("material source identities are invalid or duplicate")
    for source in sources:
        if not all(
            isinstance(source.get(key), str) and source[key].strip()
            for key in (
                "id",
                "url",
                "title",
                "observed_on",
                "evidence_type",
                "locator",
                "preparation_observation",
                "version_identity",
                "limitations",
            )
        ) or not str(source.get("url", "")).startswith("https://"):
            errors.append("material source lacks attributed observation or limitations")
    for case_id in sorted(ids):
        card, rubric = cards[case_id], rubrics[case_id]
        if not isinstance(card, dict) or not isinstance(rubric, dict):
            errors.append("case card/rubric must be objects")
            continue
        accepted = card.get("accepted_conditions")
        conditions = (
            accepted.get("hard_conditions") if isinstance(accepted, dict) else None
        )
        if (
            not isinstance(conditions, list)
            or len(conditions) != 4
            or any(
                not isinstance(condition, dict)
                or not isinstance(condition.get("id"), str)
                or not isinstance(condition.get("text"), str)
                or not condition["text"].strip()
                for condition in conditions
            )
        ):
            errors.append("case hard conditions are missing")
            continue
        condition_ids = [condition["id"] for condition in conditions]
        if (
            len(set(condition_ids)) != len(condition_ids)
            or rubric.get("mandatory_hard_condition_ids") != condition_ids
        ):
            errors.append("case rubric must cover every hard condition exactly")
        for key in (
            "decisive_claim_topics",
            "critical_failures",
            "feasibility_source_refs",
        ):
            if not isinstance(rubric.get(key), list) or not rubric[key]:
                errors.append(f"case rubric missing {key}")
        refs = rubric.get("feasibility_source_refs")
        if isinstance(refs, list) and any(
            not isinstance(ref, str) or ref not in source_ids for ref in refs
        ):
            errors.append("case rubric source ref is unresolved")
        if (
            not isinstance(card.get("decisive_questions"), list)
            or not card["decisive_questions"]
            or not isinstance(card.get("answer_units"), list)
            or not card["answer_units"]
        ):
            errors.append("case clarification questions and answers missing")
        else:
            questions, units = card["decisive_questions"], card["answer_units"]
            if len(questions) != 3 or any(
                not isinstance(question, str) or not question.strip()
                for question in questions
            ):
                errors.append("case needs three nonempty decisive questions")
            if (
                len(units) != 3
                or any(
                    not isinstance(unit, dict)
                    or set(unit) != {"question_group", "answer"}
                    or type(unit.get("question_group")) is not int
                    or not isinstance(unit.get("answer"), str)
                    or not unit["answer"].strip()
                    for unit in units
                )
                or [unit["question_group"] for unit in units] != [1, 2, 3]
            ):
                errors.append(
                    "answer units must uniquely map questions by one-based 1/2/3 index"
                )
    domains = materials.get("domains")
    expected = {
        "scheduling": {"SCH-A", "SCH-B"},
        "data_migration": {"DAT-A", "DAT-B"},
        "document_processing": {"DOC-A", "DOC-B"},
    }
    if (
        not isinstance(domains, list)
        or len(domains) != 3
        or any(not isinstance(domain, dict) for domain in domains)
    ):
        return errors + ["materials require three equivalence domains"]
    if {domain.get("id") for domain in domains} != set(expected):
        errors.append("material domains must be unique and complete")
    for domain in domains:
        domain_id, pair = domain.get("id"), domain.get("case_ids")
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(not isinstance(cid, str) for cid in pair)
            or set(pair) != expected.get(domain_id, set())
        ):
            errors.append("domain pair mapping is invalid")
        if not isinstance(domain.get("equivalence"), dict) or not domain["equivalence"]:
            errors.append("domain equivalence evidence missing")
        else:
            count = domain["equivalence"].get("hard_condition_count_each")
            if type(count) is not int or count != 4:
                errors.append("equivalence hard-condition count must be integer four")
        if any(
            case.get("domain_id") != domain_id
            for case in cases
            if case.get("case_id") in (pair if isinstance(pair, list) else [])
        ):
            errors.append("case domain mismatch")
    return errors


def check_current_supplement(supplement: object, root: Path) -> list[str]:
    if not isinstance(supplement, dict):
        return ["M1 supplement must be an object"]
    errors: list[str] = []
    if (
        supplement.get("protocol_version") != "discovery-m1-capabilities-1"
        or supplement.get("role") != "capability_acceptance_reference"
    ):
        errors.append("M1 supplement must reference sole current authority")
    expected = {
        "path": PROTOCOL,
        "version": "discovery-m1-1",
        "sha256": hashlib.sha256((root / PROTOCOL).read_bytes()).hexdigest(),
    }
    if supplement.get("current_protocol") != expected:
        errors.append("M1 current protocol raw SHA-256 mismatch")
    if any(
        key in supplement
        for key in (
            "budget",
            "formal",
            "execution_budget_cny",
            "project_ledger",
            "funding",
            "Go",
        )
    ):
        errors.append("M1 supplement cannot define separate funding or release gates")
    authorization = supplement.get("authorization")
    if not isinstance(authorization, dict) or any(
        authorization.get(key) is not False
        for key in (
            "business_implementation",
            "real_execution",
            "paid_execution",
            "git_write",
        )
    ):
        errors.append("M1 configuration cannot grant implementation or execution")
    results = supplement.get("results")
    if not isinstance(results, dict) or any(
        results.get(key) is not False
        for key in (
            "implemented",
            "technical_verification",
            "human_business_acceptance",
            "real_quality",
            "owner_time_value",
            "M1",
            "Go",
            "release",
        )
    ):
        errors.append("M1 configuration cannot report unexecuted business success")
    policy = supplement.get("real_coverage_policy")
    if (
        not isinstance(policy, dict)
        or policy.get("MCP_real_integration_required") is not False
        or policy.get("old_9_8_12_independent_execution_batch_required") is not False
    ):
        errors.append("M1 must not revive superseded real MCP or 9/8/12 gates")
    capabilities = supplement.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or not capabilities
        or any(
            not isinstance(capability, dict)
            or not capability.get("requirements")
            or not capability.get("tasks")
            or not capability.get("evidence")
            for capability in capabilities
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
    args = parser.parse_args(argv)
    root = args.root.resolve()
    history_requested = bool(
        args.historical_commit
        or args.historical_raw_sha256
        or args.historical_only
        or args.historical_path != PROTOCOL
        or args.historical_newlines != "raw"
    )
    errors: list[str] = []
    if not args.historical_only:
        errors.extend(check_links(root, project_document_files(root)))
        errors.extend(check_versions_and_traceability(root))
        errors.extend(check_skills(root))
        errors.extend(check_archive_manifest(root))
        errors.extend(check_archive_git_index(root))
        try:
            protocol = _load_current_json((root / PROTOCOL).read_bytes())
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
        else "offline configuration validation passed; implementation, live quality and source truth remain unverified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
