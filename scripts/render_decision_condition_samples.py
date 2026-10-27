"""Render the DEC-T04-01 synthetic fixtures without network or provider calls."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import runpy
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / ".tmp/decision-condition-reports",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(root / "backend/src"))
    fixtures = runpy.run_path(
        str(root / "backend/tests/unit/test_decision_condition_changes.py")
    )
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "mode": "synthetic_offline_no_provider_no_source_verification",
        "files": {},
    }
    lines = [
        "# DEC-T04-01 synthetic offline reports",
        "",
        (
            "AtlasAPI and BirchAPI are fictional fixtures. URLs use .invalid. "
            "No network, provider, official-source check, or real research was performed. "
            "These files exercise the existing decision/report code only. "
            "Human business acceptance is PENDING; P-02 and r12 remain No-Go."
        ),
        "",
        "| Scenario | Hard conditions | Machine candidate | Raw output |",
        "| --- | --- | --- | --- |",
    ]
    for name, _, report in asyncio.run(fixtures["build_sample_reports"]()):
        for extension, content in (
            ("md", report.markdown + "\n"),
            ("json", report.model_dump_json(indent=2) + "\n"),
        ):
            target = args.output / f"{name}.{extension}"
            target.write_bytes(content.encode("utf-8"))
            manifest["files"][target.name] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
        decision = report.decision
        assert decision is not None
        winner = next(
            (
                item.label
                for item in decision.candidates
                if decision.recommendation
                and item.candidate_id == decision.recommendation.candidate_id
            ),
            "None; see decision gap",
        )
        lines.append(
            f"| {name} | {' + '.join(decision.must_have)} | {winner} | "
            f"[Markdown]({name}.md), [JSON]({name}.json) |"
        )
    (args.output / "README.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    (args.output / "manifest.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    )
    print("3 synthetic report pairs rendered; no provider or network calls")


if __name__ == "__main__":
    main()
