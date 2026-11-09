"""Print a bounded current-state index from the sole task record; never authority.

Usage from any directory: python <repository>/scripts/dev_context.py
The snapshot must be the last non-whitespace content in tasks.md. Budgets count
the raw body between marker lines, including its original line endings.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = "docs/features/DECISION-001/tasks.md"
RECORD = ROOT / RECORD_PATH
START = "<!-- dev-current:start -->"
END = "<!-- dev-current:end -->"
MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 6000
MAX_SNAPSHOT_LINES = 60
MAX_OUTPUT_BYTES = 8192


def render_context(raw: bytes) -> str:
    """Extract the latest complete EOF snapshot, preserving history off-context."""
    if len(raw) > MAX_RECORD_BYTES:
        raise ValueError("task record exceeds the bounded read limit")
    lines = raw.decode("utf-8-sig").splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == START]
    if not starts:
        raise ValueError("current snapshot is missing")
    start = starts[-1]
    ends = [i for i in range(start + 1, len(lines)) if lines[i].rstrip("\r\n") == END]
    if len(ends) != 1:
        raise ValueError("current snapshot is incomplete")
    end = ends[0]
    if "".join(lines[end + 1 :]).strip():
        raise ValueError("new content follows the snapshot; refresh it first")
    body_lines = lines[start + 1 : end]
    raw_body = "".join(body_lines)
    if (
        not raw_body.strip()
        or len(raw_body.encode("utf-8")) > MAX_SNAPSHOT_BYTES
        or len(body_lines) > MAX_SNAPSHOT_LINES
    ):
        raise ValueError("current snapshot is empty or exceeds its context budget")
    body = "\n".join(raw_body.splitlines()).strip()
    output = (
        "Development index only; verify original human authority before actions.\n"
        "Workspace/evidence changes are not detected; inspect Git and sources.\n"
        f"source={RECORD_PATH}:{start + 2}\n"
        f"record_sha256={hashlib.sha256(raw).hexdigest()}\n\n{body}\n"
    )
    if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError("rendered index exceeds its output budget")
    return output


def main() -> int:
    try:
        with RECORD.open("rb") as stream:
            raw = stream.read(MAX_RECORD_BYTES + 1)
        output = render_context(raw)
    except (OSError, UnicodeError, ValueError):
        print(
            f"DEV_CONTEXT_UNAVAILABLE: inspect {RECORD_PATH}; refresh a complete "
            "EOF dev-current snapshot (<=6000 UTF-8 bytes, <=60 lines). "
            "No current-state conclusion was emitted.",
            file=sys.stderr,
        )
        return 1
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    raise SystemExit(main())
