"""Historical fixtures are explicit; the current protocol cannot start old tools."""

from __future__ import annotations

import argparse
import importlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from adaptive_research.evaluation import (
    current,
    pilot_budget,
    pilot_cost_reconciliation,
    pilot_runner,
)
from scripts.validate_project import read_historical_protocol

HISTORICAL_COMMIT = "1ffade6de07ebe3d1e72afb4c44b8677466eca67"
HISTORICAL_RAW_SHA256 = (
    "bc75a1a6d14f7633462538c7c83b79ed5f5bcf0d670997b2000c92caa0002948"
)


def historical_protocol_bytes() -> bytes:
    """Read this LF historical object; never reinterpret the current path."""
    return read_historical_protocol(
        current.REPOSITORY_ROOT,
        commit=HISTORICAL_COMMIT,
        path=current.PROTOCOL_PATH,
        raw_sha256=HISTORICAL_RAW_SHA256,
    )[1]


def make_historical_root(root: Path) -> Path:
    for relative in (
        *current.RESOURCE_PATHS,
        "backend/src/adaptive_research/evaluation/current.py",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            historical_protocol_bytes()
            if relative == current.PROTOCOL_PATH
            else (current.REPOSITORY_ROOT / relative).read_bytes()
        )
    return root


def install_historical_protocol(monkeypatch, tmp_path: Path) -> Path:
    """Only old regression tests opt into these identified protocol bytes."""
    root = make_historical_root(tmp_path / "historical-inputs")
    original_loader = current.load_protocol

    def historical_loader(_root):
        return original_loader(root)

    for name in (
        "current",
        "pilot_runner",
        "pilot_capture",
        "project_ledger",
        "pilot_cost_reconciliation",
    ):
        module = importlib.import_module(f"adaptive_research.evaluation.{name}")
        monkeypatch.setattr(module, "load_protocol", historical_loader)
    return root


def _forbidden(*_args, **_kwargs):
    raise AssertionError("execution dependency or output touched before protocol guard")


@pytest.fixture(params=["new", "malformed", "missing", "array"])
def refused_root(tmp_path, request):
    root = make_historical_root(tmp_path / "root")
    path = root / current.PROTOCOL_PATH
    if request.param == "missing":
        path.unlink()
    else:
        path.write_text(
            "{broken"
            if request.param == "malformed"
            else "[]"
            if request.param == "array"
            else json.dumps({"protocol_version": "discovery-m1-1"}),
            encoding="utf-8",
        )
    return root


@pytest.mark.asyncio
async def test_execute_refuses_before_settings_price_book_or_engine(
    refused_root, monkeypatch, tmp_path
):
    monkeypatch.setattr(pilot_runner, "REPOSITORY_ROOT", refused_root)
    for name in ("Settings", "create_async_engine", "load_price_book"):
        monkeypatch.setattr(pilot_runner, name, _forbidden)
    with pytest.raises(current.ProtocolError):
        await pilot_runner._execute(argparse.Namespace(), {})
    assert not (tmp_path / "output").exists()


@pytest.mark.asyncio
async def test_arm_direct_and_cli_refuse_before_settings_or_engine(
    refused_root, monkeypatch
):
    monkeypatch.setattr(pilot_budget, "REPOSITORY_ROOT", refused_root)
    for name in ("Settings", "create_async_engine", "load_price_book"):
        monkeypatch.setattr(pilot_budget, name, _forbidden)
    with pytest.raises(current.ProtocolError):
        await pilot_budget._arm({}, "approval:test", Decimal(1))
    assert (
        pilot_budget.main(["--arm", "--authorization-reference", "approval:test"]) == 1
    )


def test_reconcile_refuses_before_any_read_or_output(
    refused_root, monkeypatch, tmp_path
):
    monkeypatch.setattr(pilot_cost_reconciliation, "_write_once", _forbidden)
    output = tmp_path / "never" / "ledger.json"
    with pytest.raises(current.ProtocolError):
        pilot_cost_reconciliation.reconcile_pilot_cost(
            previous_ledger=tmp_path / "does-not-exist.json",
            expected_previous_sha256="0" * 64,
            run_id="old-run",
            attestation_path=tmp_path / "attestation.json",
            reconciliation_path=output.parent / "reconciliation.json",
            output_ledger=output,
            root=refused_root,
        )
    assert not output.parent.exists()


def test_historical_identity_requires_exact_raw_hash_and_explicit_newlines():
    root = current.REPOSITORY_ROOT
    with pytest.raises(ValueError, match="SHA-256"):
        read_historical_protocol(
            root,
            commit=HISTORICAL_COMMIT,
            path=current.PROTOCOL_PATH,
            raw_sha256="0" * 64,
        )
    _, raw = read_historical_protocol(
        root,
        commit=HISTORICAL_COMMIT,
        path=current.PROTOCOL_PATH,
        raw_sha256=HISTORICAL_RAW_SHA256,
    )
    _, crlf = read_historical_protocol(
        root,
        commit=HISTORICAL_COMMIT,
        path=current.PROTOCOL_PATH,
        raw_sha256=HISTORICAL_RAW_SHA256,
        newlines="lf-to-crlf",
    )
    assert b"\r" not in raw
    assert crlf == raw.replace(b"\n", b"\r\n")


def test_current_path_is_not_a_legacy_execution_protocol():
    with pytest.raises(current.ProtocolError):
        current.load_protocol(current.REPOSITORY_ROOT)


def test_execute_cli_refuses_without_constructing_any_execution_dependency(
    refused_root, monkeypatch, tmp_path
):
    monkeypatch.setattr(pilot_runner, "REPOSITORY_ROOT", refused_root)
    for name in ("Settings", "create_async_engine", "load_price_book"):
        monkeypatch.setattr(pilot_runner, name, _forbidden)
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    output = tmp_path / "never-output"
    assert (
        pilot_runner.main(
            [
                "--execute",
                "--authorization-reference",
                "test:does-not-authorize",
                "--plan",
                str(plan),
                "--output-dir",
                str(output),
                "--price-book",
                str(tmp_path / "unread-book.json"),
                "--ledger",
                str(tmp_path / "unread-ledger.json"),
                "--ledger-sha256",
                "0" * 64,
            ]
        )
        == 1
    )
    assert not output.exists()


def test_reconciliation_cli_refuses_before_outputs(refused_root, monkeypatch, tmp_path):
    loader = current.load_protocol
    monkeypatch.setattr(
        pilot_cost_reconciliation, "load_protocol", lambda _root: loader(refused_root)
    )
    monkeypatch.setattr(pilot_cost_reconciliation, "_write_once", _forbidden)
    output = tmp_path / "never-output"
    with pytest.raises(current.ProtocolError):
        pilot_cost_reconciliation.main(
            [
                "--previous-ledger",
                str(tmp_path / "unread.json"),
                "--previous-sha256",
                "0" * 64,
                "--run-id",
                "old-run",
                "--attestation",
                str(tmp_path / "unread-attestation.json"),
                "--reconciliation",
                str(output / "reconciliation.json"),
                "--output-ledger",
                str(output / "ledger.json"),
            ]
        )
    assert not output.exists()
