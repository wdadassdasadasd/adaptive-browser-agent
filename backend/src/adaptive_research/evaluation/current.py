"""Prepare a serial current-3 evaluation plan without starting any attempt.

This repository-local entry needs its frozen protocol and offline validator.
It does not read .env, import execution clients, or provide a live-run option.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4, uuid5

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL = "deepseek-flash"
PROTOCOL_PATH = "docs/evaluation/CURRENT_EVAL_PROTOCOL.json"
CASE_IDS = ("B01", "B02", "B03", "G01", "G02", "G03", "O01", "O02", "O03")
PUBLIC_DEFAULTS = {
    "max_steps": 30,
    "max_seconds": 900,
    "max_tokens": 40_000,
    "recent_trace_count": 5,
}
RESOURCE_PATHS = (
    PROTOCOL_PATH,
    "scripts/validate_project.py",
    "docs/benchmark/BENCHMARK_PROTOCOL.md",
    "docs/archive/design-0.3/05_TEST_AND_EVALUATION.md",
    "docs/evaluation/G2_EVAL_PROTOCOL.json",
    "docs/evaluation/G3_EVAL_PROTOCOL.json",
    "backend/pyproject.toml",
    "backend/uv.lock",
    "backend/src/adaptive_research/infrastructure/config.py",
)


class ProtocolError(ValueError):
    """The approved repository protocol cannot safely produce a plan."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(data: Any) -> bytes:
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def load_protocol(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Reuse the authoritative offline validator and frozen source comparisons."""

    root = root.resolve()
    missing = [name for name in RESOURCE_PATHS if not (root / name).is_file()]
    if missing:
        raise ProtocolError("Repository protocol/validator resources are missing")
    blobs = {name: (root / name).read_bytes() for name in RESOURCE_PATHS}
    try:
        protocol = json.loads(blobs[PROTOCOL_PATH])
        frozen = json.loads(blobs["docs/evaluation/G2_EVAL_PROTOCOL.json"])
        archived = json.loads(blobs["docs/evaluation/G3_EVAL_PROTOCOL.json"])
        spec = importlib.util.spec_from_file_location(
            "_current_evaluation_offline_validator",
            root / "scripts/validate_project.py",
        )
        if spec is None or spec.loader is None:
            raise ProtocolError("Repository offline validator cannot be loaded")
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        errors = validator.check_protocol(
            protocol,
            blobs["docs/benchmark/BENCHMARK_PROTOCOL.md"].decode("utf-8"),
            blobs["docs/archive/design-0.3/05_TEST_AND_EVALUATION.md"].decode("utf-8"),
            frozen["cases"],
            archived,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProtocolError("Invalid current-3 protocol structure") from exc
    if errors:
        raise ProtocolError("Current-3 validation failed: " + "; ".join(errors))
    return protocol, {name: _sha256(blob) for name, blob in blobs.items()}


def _source_fingerprint(root: Path) -> dict[str, Any]:
    paths: set[Path] = set()
    for relative, suffixes in (
        ("backend/src/adaptive_research", {".py"}),
        ("backend/migrations", {".py", ".ini"}),
        ("frontend/src", {".ts", ".vue", ".css"}),
        ("scripts", {".py", ".ps1"}),
    ):
        directory = root / relative
        if directory.is_dir():
            paths.update(
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix in suffixes
            )
    files = {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(paths)
    }
    return {"sha256": _sha256(_canonical(files)), "files": files}


def build_plan(
    root: Path = REPOSITORY_ROOT,
    *,
    phase: str = "pilot",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Return planned runs only; an actual execution manifest must be refrozen later."""

    if phase not in {"pilot", "formal"}:
        raise ProtocolError("Phase must be pilot or formal")
    if not isinstance(model, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model
    ):
        raise ProtocolError("Model must be a public model identifier")
    root = root.resolve()
    protocol, resources = load_protocol(root)
    # Recheck the schedule explicitly; protocol validation owns all scoring rules.
    if tuple(case["id"] for case in protocol["cases"]) != CASE_IDS:
        raise ProtocolError("Current-3 case order changed")
    schedule = [
        (case, trial)
        for case in protocol["cases"]
        if phase == "formal" or case["id"] in protocol["pilot"]["case_ids"]
        for trial in range(
            1, (3 if phase == "formal" and case["id"].startswith("B") else 1) + 1
        )
    ]
    if len(schedule) != (3 if phase == "pilot" else 15):
        raise ProtocolError("Current-3 trial count changed")
    plan_id = uuid4()
    public_config = {
        "model_id": model,
        "concurrency": 1,
        "phase": phase,
        "agent_limits_preview": PUBLIC_DEFAULTS.copy(),
        "phase_max_cny": protocol["execution_budget_cny"][f"{phase}_max"],
        "project_max_cny": protocol["project_ledger_contract"]["total_max_cny"],
    }
    return {
        "artifact_type": "evaluation_dry_run_plan",
        "protocol_version": protocol["protocol_version"],
        "status": "not_live_execution",
        "product_release": "No-Go",
        "execution_allowed": False,
        "attempts_started": 0,
        "provider_calls": 0,
        "browser_calls": 0,
        "concurrency": 1,
        "plan_id": str(plan_id),
        "created_at": datetime.now(UTC).isoformat(),
        "phase": phase,
        "planned_run_count": len(schedule),
        "planned_runs": [
            {
                "planned_run_id": str(uuid5(plan_id, f"{phase}:{case['id']}:{trial}")),
                "case_id": case["id"],
                "trial_index": trial,
                "status": "planned_not_started",
                "prompt": case["prompt"],
                "prompt_sha256": _sha256(case["prompt"].encode("utf-8")),
                "required_fields": list(case["required_fields"]),
                "community_supplement_required": case.get(
                    "community_supplement_required", False
                ),
            }
            for case, trial in schedule
        ],
        "fingerprints": {
            "protocol_sha256": resources[PROTOCOL_PATH],
            "dependency_lock_sha256": resources["backend/uv.lock"],
            "config_sha256": _sha256(_canonical(public_config)),
            "config_source_sha256": resources[
                "backend/src/adaptive_research/infrastructure/config.py"
            ],
            "resources": resources,
            "source": _source_fingerprint(root),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            "upstream_browser_revision": None,
            "actual_browser_environment": None,
        },
        "public_config_preview": public_config,
        "runtime_config_source": "explicit dry-run parameters; .env is not read",
        "freeze_state": "preview_only_must_refreeze_before_live",
        "pricing_basis": None,
        "estimated_cost_cny": None,
        "actual_cost_cny": None,
        "budget_limits_cny": protocol["project_ledger_contract"][
            "allocations_cny"
        ].copy(),
        "project_max_cny": 299,
        "paid_execution_requires_separate_authorization": True,
        "prerequisites_unverified": [
            "P-01 stage acceptance",
            "explicit live-run and cost authorization",
            "verified model/pricing and enforceable remaining budget",
            "frozen actual runtime/upstream browser configuration",
            "manual official-source review and report hash binding",
        ],
        "result_validation_entry": "python scripts/validate_project.py --results PATH --ledger PATH",
        "note": "This plan is not an attempt record, result batch, authorization, or release decision.",
    }


def write_plan(plan: dict[str, Any], output: Path) -> None:
    """Create the explicitly requested plan artifact, refusing existing evidence."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plan, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="No --execute option is available; all invocations are offline.",
    )
    parser.add_argument("--phase", choices=("pilot", "formal"), default="pilot")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help="public model name for this preview only"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="repository containing frozen evaluation resources",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="create a new dry-run plan JSON; never overwrites an existing file",
    )
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.root, phase=args.phase, model=args.model)
        if args.output is not None:
            write_plan(plan, args.output)
            print(
                json.dumps(
                    {
                        "output": str(args.output.resolve()),
                        "status": plan["status"],
                        "planned_run_count": plan["planned_run_count"],
                        "execution_allowed": False,
                    }
                )
            )
        else:
            print(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ProtocolError) as exc:
        print(
            f"Dry-run refused ({type(exc).__name__}); no attempt was started.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
