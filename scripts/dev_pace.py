"""Aggregate explicitly selected Codex rollouts without disclosing their text."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

MAX_FILE = 256 << 20
MAX_LINE = 16 << 20
MAX_TOTAL = 512 << 20
PURPOSES = {"spawn_agent", "followup_task", "wait_agent"}
FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def timestamp(value):
    if type(value) is int:
        return float(value) if 0 <= value < 253_402_300_800 else None
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.timestamp() if parsed.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None


def union_seconds(intervals):
    end = None
    total = 0.0
    for start, stop in sorted(intervals):
        if stop < start:
            raise ValueError("invalid interval")
        total += max(0.0, stop - max(start, end if end is not None else start))
        end = max(stop, end if end is not None else stop)
    return round(total, 3)


def event_identity(thread, event):
    """Deduplicate identity-free records without exposing their contents."""
    return thread, hashlib.sha256(json.dumps(event, sort_keys=True).encode()).digest()


def summarize(paths, outcomes=None):
    if not 1 <= len(paths) <= 200:
        raise ValueError("select 1 to 200 files")
    files, usages, calls, finishes, starts, stops = {}, {}, {}, {}, {}, {}
    threads, parents = set(), set()
    times, tool_intervals, turn_intervals = [], [], []
    unidentified_usage, unidentified_tools = set(), set()
    total_bytes = event_count = 0
    for path in paths:
        digest = hashlib.sha256()
        thread = None
        size = 0
        # Read line-by-line with a hard cap before JSON decoding.
        with Path(path).open("rb") as stream:
            while raw := stream.readline(MAX_LINE + 1):
                size += len(raw)
                total_bytes += len(raw)
                event_count += 1
                if (
                    size > MAX_FILE
                    or len(raw) > MAX_LINE
                    or total_bytes > MAX_TOTAL
                    or event_count > 500_000
                ):
                    raise ValueError("rollout limit exceeded")
                digest.update(raw)
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise TypeError("invalid event")
                payload = event.get("payload", {})
                if not isinstance(payload, dict):
                    raise TypeError("invalid payload")
                kind = event.get("type")
                at = timestamp(event.get("timestamp"))
                if at is not None:
                    times.append(at)
                if kind == "session_meta":
                    thread = payload.get("id")
                    if not isinstance(thread, str) or not thread:
                        raise ValueError("missing session identity")
                    threads.add(thread)
                    source = payload.get("source")
                    if isinstance(source, dict):
                        spawn = source.get("subagent", {})
                        if isinstance(spawn, dict):
                            spawn = spawn.get("thread_spawn", {})
                            if isinstance(spawn, dict):
                                parent = spawn.get("parent_thread_id")
                                if isinstance(parent, str):
                                    parents.add((thread, parent))
                    continue
                if thread is None:
                    raise ValueError("session metadata must precede events")
                if kind == "token_usage_record":
                    response = payload.get("response_id")
                    if not isinstance(response, str) or not response:
                        unidentified_usage.add(event_identity(thread, event))
                        continue
                    usage = payload.get("usage")
                    if not isinstance(usage, dict):
                        raise ValueError("invalid usage")
                    values = tuple(usage.get(field) for field in FIELDS)
                    if any(
                        v is not None and (type(v) is not int or v < 0) for v in values
                    ):
                        raise ValueError("invalid token count")
                    inp, cached, output, reasoning = values
                    if (inp is not None and cached is not None and cached > inp) or (
                        output is not None
                        and reasoning is not None
                        and reasoning > output
                    ):
                        raise ValueError("inconsistent token count")
                    if response in usages and usages[response] != values:
                        raise ValueError("conflicting response usage")
                    usages[response] = values
                if kind == "response_item":
                    item_kind = payload.get("type")
                    identity = payload.get("call_id")
                    tool_kinds = (
                        "function_call",
                        "custom_tool_call",
                        "function_call_output",
                        "custom_tool_call_output",
                    )
                    if item_kind in tool_kinds and (
                        not isinstance(identity, str) or not identity
                    ):
                        unidentified_tools.add(event_identity(thread, event))
                    elif isinstance(identity, str) and identity:
                        key = (thread, identity)
                        if item_kind in ("function_call", "custom_tool_call"):
                            name = payload.get("name")
                            if not isinstance(name, str):
                                raise TypeError("invalid tool name")
                            name = name.split(".")[-1]
                            item = (name if name in PURPOSES else "other", at)
                            if key in calls and calls[key] != item:
                                raise ValueError("conflicting tool call")
                            calls[key] = item
                        elif item_kind in (
                            "function_call_output",
                            "custom_tool_call_output",
                        ):
                            previous = finishes.get(key)
                            finishes[key] = (
                                max(at, previous)
                                if at is not None and previous is not None
                                else at
                                if at is not None
                                else previous
                            )
                if kind == "event_msg":
                    turn = payload.get("turn_id")
                    if not isinstance(turn, str):
                        continue
                    key = (thread, turn)
                    if payload.get("type") == "task_started":
                        start = timestamp(payload.get("started_at"))
                        if start is None:
                            start = at
                        if start is not None:
                            starts[key] = min(start, starts.get(key, start))
                    elif payload.get("type") in ("task_complete", "turn_aborted"):
                        start = timestamp(payload.get("started_at"))
                        if start is not None:
                            starts[key] = min(start, starts.get(key, start))
                        stop = timestamp(payload.get("completed_at"))
                        if stop is None:
                            stop = at
                        if stop is not None:
                            stops[key] = max(stop, stops.get(key, stop))
        files[digest.hexdigest()] = size
    for key, (_, start) in calls.items():
        stop = finishes.get(key)
        if start is not None and stop is not None:
            tool_intervals.append((start, stop))
    for key, start in starts.items():
        if key in stops:
            turn_intervals.append((start, stops[key]))
    totals, coverage = {}, {}
    for index, field in enumerate(FIELDS):
        known = [v[index] for v in usages.values() if v[index] is not None]
        complete = bool(usages) and len(known) == len(usages) and not unidentified_usage
        totals[field] = sum(known) if complete else None
        coverage[field] = {"known_subtotal": sum(known), "records": len(known)}
    inp, cached, output = (totals[k] for k in FIELDS[:3])
    uncached = inp - cached if inp is not None and cached is not None else None
    totals["uncached_input_tokens"] = uncached
    totals["uncached_input_plus_output_tokens"] = (
        uncached + output if uncached is not None and output is not None else None
    )
    if outcomes is None:
        outcomes = dict.fromkeys(
            ("review_findings", "rework_rounds", "missing_required_checks")
        )
    if any(v is not None and (type(v) is not int or v < 0) for v in outcomes.values()):
        raise ValueError("invalid reported outcome")
    counts = Counter(name for name, _ in calls.values())
    orphans = len(finishes.keys() - calls.keys())
    call_gaps = bool(orphans or unidentified_tools)
    return {
        "schema_version": 1,
        "scope": "explicit files only; not proof that every child or request was captured",
        "files": [
            {"sha256": key, "bytes": value} for key, value in sorted(files.items())
        ],
        "threads": len(threads),
        "parent_links": len(parents),
        "parents_outside_selection": len({p for _, p in parents if p not in threads}),
        "calls": {
            name: None if call_gaps else counts[name]
            for name in sorted(PURPOSES | {"other"})
        },
        "known_request_counts": {
            name: counts[name] for name in sorted(PURPOSES | {"other"})
        },
        "call_coverage": {
            "identified_requests": len(calls),
            "identified_outputs": len(finishes),
            "orphan_outputs": orphans,
            "unidentified_tool_records": len(unidentified_tools),
        },
        "usage_records": len(usages),
        "unidentified_usage_records": len(unidentified_usage),
        "tokens": totals,
        "token_coverage": coverage,
        "timing": {
            "observed_window_seconds": round(max(times) - min(times), 3)
            if times
            else None,
            "completed_turn_union_seconds": union_seconds(turn_intervals)
            if turn_intervals
            else None,
            "observed_tool_union_seconds": union_seconds(tool_intervals)
            if tool_intervals
            else None,
            "unpaired_tool_calls": None
            if unidentified_tools
            else len(calls) - len(tool_intervals) + orphans,
            "unpaired_turns": len(starts.keys() ^ stops.keys()),
            "effective_work_seconds": None,
            "human_wait_seconds": None,
            "attribution": "unknown; tool intervals overlap child work; turn time may include human waits",
        },
        "reported_outcomes": outcomes,
        "fees": None,
        "comparison": "not assessed; require comparable task scope, risk and capture coverage",
    }


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Arguments refused; use --help for supported options.\n")


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument("rollouts", nargs="+", type=Path)
    for name in ("review-findings", "rework-rounds", "missing-required-checks"):
        parser.add_argument("--" + name, type=int)
    args = parser.parse_args()
    outcomes = {
        k: getattr(args, k)
        for k in ("review_findings", "rework_rounds", "missing_required_checks")
    }
    try:
        result = summarize(args.rollouts, outcomes)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        parser.exit(
            1,
            "Rollout aggregation refused; check selected files, limits and event structure.\n",
        )
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
