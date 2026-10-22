"""Fixed V1 three-arm benchmark protocol and redacted attempt records."""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit
from uuid import uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]

from adaptive_research.evaluation.legacy_v1.cases import CASES
from adaptive_research.evaluation.legacy_v1.metrics import (
    duplicate_url_count,
    score_answer,
    urls_in,
)

ARMS = ("baseline", "adaptive-full", "adaptive-browser-only")
MODEL = "deepseek-flash"
PROTOCOL_VERSION = "V1-D7-r12"
_PUBLIC_SOURCE_HOSTS = {
    "github.com",
    "gitlab.com",
    "codeberg.org",
    "bitbucket.org",
    "git.sr.ht",
    "api.github.com",
    "fastapi.tiangolo.com",
    "flask.palletsprojects.com",
}


def schedule(
    cases: tuple[str, ...], arms: tuple[str, ...], repetitions: int
) -> list[tuple[str, str, int]]:
    """Rotate arm order by case and repetition; retain all fixed attempts."""
    return [
        (case, arm, repeat)
        for repeat in range(1, repetitions + 1)
        for index, case in enumerate(cases)
        for arm in (ARMS[(index + repeat - 1 + offset) % 3] for offset in range(3))
        if arm in arms
    ]


def _git_revision(path: str, *, gitlink: bool = False) -> str | None:
    try:
        if gitlink:
            result = subprocess.run(
                ["git", "ls-files", "--stage", "browser-use"],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            pieces = result.stdout.split()
            return (
                pieces[1]
                if result.returncode == 0 and len(pieces) >= 2 and pieces[0] == "160000"
                else None
            )
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _working_tree_fingerprint() -> tuple[bool | None, str | None]:
    """Hash project and upstream changes without persisting their contents."""
    root = REPOSITORY_ROOT
    try:
        digest = hashlib.sha256()
        dirty = False
        for label, checkout in (
            (b"project", root),
            (b"browser-use", root / "browser-use"),
        ):
            diff = subprocess.run(
                [
                    "git",
                    "-c",
                    "submodule.recurse=false",
                    "diff",
                    "--binary",
                    "HEAD",
                    "--",
                ],
                cwd=checkout,
                capture_output=True,
                check=False,
                timeout=15,
            )
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "-z"],
                cwd=checkout,
                capture_output=True,
                check=False,
                timeout=15,
            )
            if diff.returncode or untracked.returncode:
                return None, None
            names = sorted(name for name in untracked.stdout.split(b"\0") if name)
            dirty |= bool(diff.stdout or names)
            digest.update(label + b"\0tracked\0" + diff.stdout)
            for name in names:
                content = (checkout / os.fsdecode(name)).read_bytes()
                digest.update(len(name).to_bytes(8, "big") + name)
                digest.update(len(content).to_bytes(8, "big") + content)
        return dirty, digest.hexdigest()
    except (OSError, subprocess.TimeoutExpired):
        return None, None


def _browser_use_version() -> str | None:
    try:
        return importlib.metadata.version("browser-use")
    except importlib.metadata.PackageNotFoundError:
        return None


def _safe_url(value: str) -> str:
    for name in ("DEEPSEEK_API_KEY", "GITHUB_TOKEN"):
        secret = os.getenv(name)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return "[REDACTED_URL]"
        host = parsed.hostname
        if ":" in host:
            host = f"[{host}]"
        port = f":{parsed.port}" if parsed.port else ""
    except ValueError:
        return "[REDACTED_URL]"
    # Other sites can place arbitrary page secrets in the path. Keep the
    # official benchmark source paths; retain only the origin elsewhere.
    path = parsed.path if parsed.hostname in _PUBLIC_SOURCE_HOSTS else ""
    if re.search(
        r"(?i)(?:api[_-]?key|token|secret|password|authorization|cookie|session[_-]?id|private[_-]?key)",
        unquote(path),
    ):
        path = ""
    path = re.sub(
        r"(?i)(?:sk-[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)",
        "[REDACTED]",
        path,
    )
    return urlunsplit((parsed.scheme, host + port, path, "", ""))


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)([\"']?\b(?:api[_-]?key|[\w-]*token|secret|password|authorization|cookie|session[_-]?id|private[_-]?key)\b[\"']?\s*[:=]\s*)"
    r"(\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[^\s,;}]+")
_STANDALONE_SECRET = re.compile(
    r"(?i)\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})\b"
)
_COOKIE_HEADER = re.compile(r"(?i)\b(?:set-cookie|cookie)\s*[:=]\s*[^\r\n]+")
_AUTH_HEADER = re.compile(r"(?i)\b(?:proxy-)?authorization\s*[:=]\s*[^\r\n]+")


def redact(value: Any, *, secrets: tuple[str, ...] = ()) -> Any:
    """Remove credentials and URL query/fragment from all persisted free text."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower() not in {"prompt_tokens", "completion_tokens", "total_tokens"}
            and re.search(
                r"(?i)(api.?key|token|secret|password|authorization|cookie|session.?id|private.?key)",
                key,
            )
            else redact(item, secrets=secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, secrets=secrets) for item in value]
    if not isinstance(value, str):
        return value
    for secret in sorted((part for part in secrets if part), key=len, reverse=True):
        value = value.replace(secret, "[REDACTED]")
    value = _COOKIE_HEADER.sub("Cookie: [REDACTED]", value)
    value = _AUTH_HEADER.sub("Authorization: [REDACTED]", value)
    value = _BEARER.sub("Bearer [REDACTED]", value)
    value = _SECRET_ASSIGNMENT.sub(
        lambda match: (
            match.group(1)
            + (
                f"{match.group(2)[0]}[REDACTED]{match.group(2)[0]}"
                if match.group(2).startswith(('"', "'"))
                else "[REDACTED]"
            )
        ),
        value,
    )
    value = _STANDALONE_SECRET.sub("[REDACTED]", value)
    return re.sub(
        r"https?://[^\s<>\])}\"']+",
        lambda match: _safe_url(match.group()),
        value,
        flags=re.IGNORECASE,
    )


def _utc() -> str:
    return datetime.now(UTC).isoformat()


def _safe_trace(entries: Any) -> list[dict[str, Any]]:
    """Persist step metadata only; upstream traces may contain full page text."""
    safe = []
    for index, entry in enumerate(entries if isinstance(entries, list) else []):
        step: dict[str, Any] = {"step": index + 1}
        if isinstance(entry, dict):
            for key in ("tool", "action", "error_type"):
                value = entry.get(key)
                if isinstance(value, str) and re.fullmatch(r"[a-z_]{1,40}", value):
                    step[key] = value
            if isinstance(entry.get("success"), bool):
                step["success"] = entry["success"]
            actions = entry.get("actions")
            if isinstance(actions, list):
                step["actions"] = [
                    action
                    for action in actions
                    if isinstance(action, str) and re.fullmatch(r"[a-z_]{1,40}", action)
                ]
        else:
            step["content"] = "[REDACTED_PAGE_TEXT]"
        safe.append(step)
    return safe


async def _browser_version(session_factory: Any = None) -> str:
    """Query the same default browser-use session used by both benchmark arms."""
    if session_factory is None:
        from browser_use import BrowserSession

        session_factory = BrowserSession
    session = session_factory()
    try:
        await session.start()
        version = await session.cdp_client.send.Browser.getVersion()
        product = version.get("product")
        if not isinstance(product, str) or not product.strip():
            raise ValueError("browser version is unavailable")
        return product
    finally:
        await session.kill()


async def attempt(
    case: str,
    arm: str,
    repetition: int,
    *,
    baseline=None,
    adaptive=None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Always return one record, including failed and raised attempts."""
    if case not in CASES or arm not in ARMS or repetition < 1:
        raise ValueError("invalid benchmark attempt")
    if baseline is None:
        from adaptive_research.evaluation.legacy_v1.baseline import run_baseline

        baseline = run_baseline
    if adaptive is None:
        from adaptive_research.evaluation.legacy_v1.adaptive import run_adaptive

        adaptive = run_adaptive
    task = CASES[case]
    started = _utc()
    start_clock = asyncio.get_running_loop().time()
    result: dict[str, Any] = {}
    try:
        result = (
            await baseline(task)
            if arm == "baseline"
            else await adaptive(task, browser_only=arm == "adaptive-browser-only")
        )
    except Exception as exc:  # noqa: BLE001 - failures still produce a record
        result = {
            "status": "failed",
            "failure_reason": type(exc).__name__,
            "budget_parity": "mismatched" if arm == "baseline" else "unverified",
        }
    duration = asyncio.get_running_loop().time() - start_clock
    secrets = tuple(
        os.getenv(name, "") for name in ("DEEPSEEK_API_KEY", "GITHUB_TOKEN")
    )
    answer = redact(result.get("answer") or "", secrets=secrets)
    trace = _safe_trace(result.get("trace") or [])
    raw_visited_urls = [
        url
        for url in result.get("urls", [])
        if isinstance(url, str) and _safe_url(url) != "[REDACTED_URL]"
    ]
    visited_urls = [_safe_url(url) for url in raw_visited_urls]
    urls = list(visited_urls)
    urls.extend(
        clean
        for url in result.get("source_urls", [])
        if isinstance(url, str) and (clean := _safe_url(url)) != "[REDACTED_URL]"
    )
    urls.extend(
        clean
        for url in urls_in(answer)
        if (clean := _safe_url(url)) != "[REDACTED_URL]"
    )
    fields = score_answer(case, answer)
    prompt_tokens = result.get("prompt_tokens")
    completion_tokens = result.get("completion_tokens")
    budget_parity = result.get("budget_parity", "unverified")
    status = result.get("status", "failed")
    failure_reason = result.get("failure_reason")
    if prompt_tokens is None or completion_tokens is None:
        budget_parity = "mismatched" if arm == "baseline" else "unverified"
    elif prompt_tokens + completion_tokens > 40_000:
        status = "failed"
        failure_reason = "token_budget_breach"
        budget_parity = "mismatched"
    if result.get("steps", 0) > 30:
        status = "failed"
        failure_reason = "step_budget_breach"
        budget_parity = "mismatched"
    if duration > 900:
        status = "failed"
        failure_reason = "time_budget_breach"
        budget_parity = "mismatched"
    project_dirty, worktree_sha256 = _working_tree_fingerprint()
    return {
        "case": case,
        "arm": arm,
        "repetition": repetition,
        "protocol_version": PROTOCOL_VERSION,
        "task": task,
        "prompt_sha256": hashlib.sha256(task.encode()).hexdigest(),
        "model": MODEL,
        "git_revisions": {
            "project": _git_revision("."),
            "project_dirty": project_dirty,
            "project_worktree_sha256": worktree_sha256,
            "browser_use_gitlink": _git_revision("browser-use", gitlink=True),
            "browser_use_actual_head": _git_revision("browser-use"),
        },
        "browser_use_version": _browser_use_version(),
        "environment": redact(
            environment
            or {
                "os": platform.platform(),
                "python": platform.python_version(),
                "browser": "unverified",
                "network": "unverified",
            },
            secrets=secrets,
        ),
        "started_at": started,
        "ended_at": _utc(),
        "duration_seconds": duration,
        "status": status,
        "answer": answer,
        "source_urls": list(dict.fromkeys(urls)),
        "trace": trace,
        "steps": result.get("steps", 0),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "duplicate_urls": duplicate_url_count(raw_visited_urls),
        "score_fields": fields,
        "coverage": sum(fields.values()) / len(fields),
        "manual_contradiction_note": None,
        "failure_reason": redact(failure_reason, secrets=secrets),
        "upstream_success": result.get("upstream_success"),
        "budget_parity": budget_parity,
    }


def save_record(record: dict[str, Any], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record['case']}_{record['arm']}_r{record['repetition']}.json"
    if path.exists():
        raise FileExistsError(f"attempt record already exists: {path}")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: dict[str, int] = {}
    for row in rows:
        if row["status"] != "completed":
            reason = row.get("failure_reason") or "unspecified"
            failures[reason] = failures.get(reason, 0) + 1
    return {
        "attempts": len(rows),
        "completion_rate": mean(
            row["status"] == "completed"
            and row["coverage"] == 1
            and row["manual_contradiction_note"] == "none"
            for row in rows
        )
        if rows and all(row["manual_contradiction_note"] is not None for row in rows)
        else None,
        "provisional_full_coverage_rate": mean(
            row["status"] == "completed" and row["coverage"] == 1 for row in rows
        )
        if rows
        else None,
        "mean_steps": mean(row["steps"] for row in rows) if rows else None,
        "mean_duplicate_urls": mean(row["duplicate_urls"] for row in rows)
        if rows
        else None,
        "mean_duration_seconds": mean(row["duration_seconds"] for row in rows)
        if rows
        else None,
        "mean_coverage": mean(row["coverage"] for row in rows) if rows else None,
        "mean_prompt_tokens": mean(row["prompt_tokens"] for row in rows)
        if rows and all(row["prompt_tokens"] is not None for row in rows)
        else None,
        "mean_completion_tokens": mean(row["completion_tokens"] for row in rows)
        if rows and all(row["completion_tokens"] is not None for row in rows)
        else None,
        "budget_parity": "verified"
        if rows and all(row["budget_parity"] == "verified" for row in rows)
        else "mismatched",
        "missing_values": {
            field: sum(row[field] is None for row in rows)
            for field in ("prompt_tokens", "completion_tokens")
        },
        "failure_categories": failures,
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep full-system and mechanism comparisons distinct and uncertainty visible."""
    versions = {row.get("protocol_version", "unknown") for row in records}
    arms = {
        arm: _summarize_rows([row for row in records if row["arm"] == arm])
        for arm in ARMS
    }
    by_case = {
        case: {
            arm: _summarize_rows(
                [row for row in records if row["case"] == case and row["arm"] == arm]
            )
            for arm in ARMS
        }
        for case in CASES
    }
    return {
        "arms": arms,
        "by_case": by_case,
        "protocol_version": next(iter(versions)) if len(versions) == 1 else "mixed",
        "comparisons": {
            "full_system_vs_baseline": ["adaptive-full", "baseline"],
            "browser_only_vs_baseline": ["adaptive-browser-only", "baseline"],
        },
        "protocol_complete": {
            (row["case"], row["arm"], row["repetition"]) for row in records
        }
        == set(schedule(tuple(CASES), ARMS, 2))
        and len(records) == 18
        and len(versions) == 1
        and "unknown" not in versions,
        "controlled_advantage_claim_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="perform external provider/browser runs"
    )
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument(
        "--output", type=Path, default=REPOSITORY_ROOT / "data/benchmark"
    )
    parser.add_argument(
        "--summarize",
        type=Path,
        metavar="RUN_DIR",
        help="recompute summary after manual contradiction notes are entered",
    )
    args = parser.parse_args()
    if args.summarize:
        _summarize_directory(args.summarize)
        return
    if not 1 <= args.repetitions <= 2:
        parser.error("repetitions must be 1 or 2")
    cases = (args.case,) if args.case else tuple(CASES)
    arms = (args.arm,) if args.arm else ARMS
    planned = schedule(cases, arms, args.repetitions)
    if not args.live:
        print(
            json.dumps({"mode": "plan", "attempts": planned, "live_runs": 0}, indent=2)
        )
        return
    if not os.getenv("DEEPSEEK_API_KEY"):
        parser.error("DEEPSEEK_API_KEY is required for live attempts")
    if _working_tree_fingerprint()[1] is None:
        parser.error("project working-tree fingerprint is unavailable")
    asyncio.run(_run_live(args.output, planned))


async def _run_live(
    output: Path, planned: list[tuple[str, str, int]], *, run_id: str | None = None
) -> None:
    run_id = run_id or f"{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}-{uuid4().hex[:8]}"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("invalid run ID")
    run_dir = output / run_id
    environment = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "browser": "unverified",
        "network": "unverified",
    }
    try:
        environment["browser"] = await _browser_version()
    except Exception as exc:  # noqa: BLE001 - keep all attempts if browser probe fails
        environment["browser_version_error"] = type(exc).__name__
    records = []
    paths = []
    for case, arm, repetition in planned:
        record = await attempt(case, arm, repetition, environment=environment)
        record["run_id"] = f"{run_id}-{case}-{arm}-r{repetition}"
        path = save_record(record, run_dir)
        records.append(record)
        paths.append(path.name)
        print(json.dumps({"record": str(path), "status": record["status"]}))
    summary = summarize(records)
    summary["smoke_only"] = len(planned) != 18
    summary["raw_records"] = paths
    summary["run_id"] = run_id
    summary_path = run_dir / "summary.json"
    if summary_path.exists():
        raise FileExistsError(f"summary already exists: {summary_path}")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _summarize_directory(run_dir: Path) -> None:
    records = []
    paths = []
    for path in sorted(run_dir.glob("B??_*_r?.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
        paths.append(path.name)
    if not records:
        raise ValueError(f"no raw records in {run_dir}")
    summary = summarize(records)
    summary["smoke_only"] = not summary["protocol_complete"]
    summary["raw_records"] = paths
    summary["run_id"] = run_dir.name
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
