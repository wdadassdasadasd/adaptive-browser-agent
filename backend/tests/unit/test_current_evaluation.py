"""Offline plans preserve the frozen cohort without importing execution code."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from adaptive_research.evaluation.current import (
    CASE_IDS,
    PROTOCOL_PATH,
    REPOSITORY_ROOT,
    RESOURCE_PATHS,
    ProtocolError,
    build_plan,
    main,
    write_plan,
)


@pytest.fixture
def evaluation_root(tmp_path):
    for relative in (
        *RESOURCE_PATHS,
        "backend/src/adaptive_research/evaluation/current.py",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPOSITORY_ROOT / relative).read_bytes())
    return tmp_path


def test_default_plan_preserves_pilot_prompts_fields_and_unknown_cost(
    evaluation_root,
) -> None:
    protocol_bytes = (evaluation_root / PROTOCOL_PATH).read_bytes()
    protocol = json.loads(protocol_bytes)
    plan = build_plan(evaluation_root)
    assert plan["phase"] == "pilot"
    assert plan["concurrency"] == 1
    assert plan["planned_run_count"] == 3
    assert [run["case_id"] for run in plan["planned_runs"]] == list(CASE_IDS[:3])
    for run, case in zip(plan["planned_runs"], protocol["cases"], strict=False):
        assert run["prompt"] == case["prompt"]
        assert run["required_fields"] == case["required_fields"]
        assert (
            run["prompt_sha256"]
            == hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest()
        )
        assert run["trial_index"] == 1
        assert run["status"] == "planned_not_started"
        assert "task_id" not in run and "run_id" not in run
    assert (
        plan["fingerprints"]["protocol_sha256"]
        == hashlib.sha256(protocol_bytes).hexdigest()
    )
    assert plan["public_config_preview"]["phase_max_cny"] == 49
    assert plan["project_max_cny"] == 299
    assert plan["estimated_cost_cny"] is None
    assert plan["actual_cost_cny"] is None
    assert plan["pricing_basis"] is None
    assert plan["product_release"] == "No-Go"
    assert plan["execution_allowed"] is False
    assert (
        plan["attempts_started"] == plan["provider_calls"] == plan["browser_calls"] == 0
    )


def test_formal_plan_has_nine_b_three_g_three_o_in_frozen_order(
    evaluation_root,
) -> None:
    plan = build_plan(evaluation_root, phase="formal")
    expected = [
        (case, trial)
        for case in CASE_IDS
        for trial in range(1, (3 if case.startswith("B") else 1) + 1)
    ]
    assert [
        (run["case_id"], run["trial_index"]) for run in plan["planned_runs"]
    ] == expected
    assert len({run["planned_run_id"] for run in plan["planned_runs"]}) == 15
    assert plan["public_config_preview"]["phase_max_cny"] == 200
    assert plan["planned_runs"][-1]["community_supplement_required"] is True


@pytest.mark.parametrize(
    "mutation", ["prompt", "fields", "trials", "budget", "authorization"]
)
def test_changed_frozen_protocol_is_refused(evaluation_root, mutation) -> None:
    protocol_file = evaluation_root / PROTOCOL_PATH
    protocol = json.loads(protocol_file.read_bytes())
    if mutation == "prompt":
        protocol["cases"][0]["prompt"] += " Changed question."
    elif mutation == "fields":
        protocol["cases"][6]["required_fields"][0] = "different_field"
    elif mutation == "trials":
        protocol["formal"]["trials_per_b_case"] = 2
    elif mutation == "budget":
        protocol["execution_budget_cny"]["pilot_max"] = 50
    else:
        protocol["paid_execution_requires_separate_authorization"] = False
    protocol_file.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(ProtocolError, match="validation failed"):
        build_plan(evaluation_root)


def test_config_fingerprint_changes_only_for_explicit_public_preview(
    evaluation_root, monkeypatch
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-provider-sentinel")
    monkeypatch.setenv("GITHUB_TOKEN", "secret-github-sentinel")
    monkeypatch.setenv("P01_DATABASE_URL", "secret-database-sentinel")
    (evaluation_root / ".env").write_text(
        "NEVER_READ=secret-file-sentinel", encoding="utf-8"
    )
    read_bytes = Path.read_bytes

    def guard(path):
        if path.name == ".env":
            pytest.fail("Dry-run must not read .env")
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guard)
    default = build_plan(evaluation_root)
    different_model = build_plan(evaluation_root, model="explicit-public-model")
    assert (
        default["fingerprints"]["source"] == different_model["fingerprints"]["source"]
    )
    assert (
        default["fingerprints"]["config_sha256"]
        != different_model["fingerprints"]["config_sha256"]
    )
    encoded = json.dumps([default, different_model])
    assert "secret-provider-sentinel" not in encoded
    assert "secret-github-sentinel" not in encoded
    assert "secret-database-sentinel" not in encoded
    assert "secret-file-sentinel" not in encoded


def test_lock_and_code_fingerprints_bind_the_bytes_on_disk(evaluation_root) -> None:
    before = build_plan(evaluation_root)
    lock = evaluation_root / "backend/uv.lock"
    source = evaluation_root / "backend/src/adaptive_research/evaluation/current.py"
    lock.write_bytes(lock.read_bytes() + b"\n# offline fingerprint fixture\n")
    source.write_bytes(source.read_bytes() + b"\n# offline fingerprint fixture\n")
    after = build_plan(evaluation_root)
    assert (
        after["fingerprints"]["dependency_lock_sha256"]
        == hashlib.sha256(lock.read_bytes()).hexdigest()
    )
    assert (
        before["fingerprints"]["dependency_lock_sha256"]
        != after["fingerprints"]["dependency_lock_sha256"]
    )
    assert (
        before["fingerprints"]["source"]["sha256"]
        != after["fingerprints"]["source"]["sha256"]
    )


def test_write_once_cli_output_is_a_plan_and_never_replaces_evidence(
    evaluation_root, tmp_path, capsys
) -> None:
    output = tmp_path / "artifacts/plan.json"
    assert main(["--root", str(evaluation_root), "--output", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["execution_allowed"] is False
    assert summary["planned_run_count"] == 3
    original = output.read_bytes()
    plan = json.loads(original)
    assert plan["artifact_type"] == "evaluation_dry_run_plan"
    assert plan["status"] == "not_live_execution"
    with pytest.raises(FileExistsError):
        write_plan(plan, output)
    assert output.read_bytes() == original
    assert main(["--root", str(evaluation_root), "--output", str(output)]) == 1
    assert output.read_bytes() == original


def test_cli_stdout_defaults_to_a_plan_and_rejects_execute(
    evaluation_root, capsys
) -> None:
    assert main(["--root", str(evaluation_root)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["status"] == "not_live_execution"
    assert plan["provider_calls"] == 0
    with pytest.raises(SystemExit) as error:
        main(["--execute"])
    assert error.value.code == 2
    assert "unrecognized arguments: --execute" in capsys.readouterr().err


def test_missing_repository_resources_refuses_without_output(tmp_path, capsys) -> None:
    output = tmp_path / "never-created.json"
    assert main(["--root", str(tmp_path), "--output", str(output)]) == 1
    assert not output.exists()
    assert "no attempt was started" in capsys.readouterr().err


def test_dry_run_does_not_import_clients_or_open_network_sockets() -> None:
    script = r"""
import importlib.abc
import json
import socket
import sys

class RefuseExecutionImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        forbidden = (
            "httpx", "sqlalchemy", "asyncpg", "browser_use",
            "adaptive_research.agent", "adaptive_research.api",
            "adaptive_research.worker", "adaptive_research.infrastructure",
        )
        if any(fullname == name or fullname.startswith(name + ".") for name in forbidden):
            raise AssertionError("Execution dependency imported: " + fullname)
        return None

def refuse_socket(*args, **kwargs):
    raise AssertionError("Dry-run attempted a network socket")

socket.socket = refuse_socket
sys.meta_path.insert(0, RefuseExecutionImports())
from adaptive_research.evaluation.current import build_plan
plan = build_plan()
assert plan["provider_calls"] == plan["browser_calls"] == plan["attempts_started"] == 0
print(json.dumps({"execution_allowed": plan["execution_allowed"], "count": plan["planned_run_count"]}))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "backend/src")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"execution_allowed": False, "count": 3}
