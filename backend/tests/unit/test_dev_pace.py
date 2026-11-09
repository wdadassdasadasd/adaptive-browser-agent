"""Exercise aggregate evidence, overlap and private-text refusal."""

import json
import sys

import pytest

from scripts import dev_pace


def record(kind, payload, sec=0):
    return {
        "type": kind,
        "timestamp": f"2026-11-04T00:00:{sec:02d}Z",
        "payload": payload,
    }


def rollout(tmp_path, events, name="a.jsonl", thread="t"):
    path = tmp_path / name
    events = [record("session_meta", {"id": thread}), *events]
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


def usage(**overrides):
    return record(
        "token_usage_record",
        {
            "response_id": "r",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 80,
                "output_tokens": 15,
                "reasoning_output_tokens": 5,
                **overrides,
            },
        },
    )


def test_resume_and_cumulative_snapshots_are_not_extra_usage(tmp_path):
    a = rollout(
        tmp_path,
        [
            usage(),
            record(
                "event_msg",
                {
                    "type": "token_count",
                    "info": {"total_token_usage": {"input_tokens": 9999}},
                },
            ),
        ],
    )
    b = rollout(tmp_path, [usage()], name="resume.jsonl")
    result = dev_pace.summarize([a, b, a])
    assert result["usage_records"] == 1
    assert result["tokens"]["uncached_input_plus_output_tokens"] == 35
    assert result["tokens"]["reasoning_output_tokens"] == 5


def test_parallel_tools_count_once_and_union_not_sum(tmp_path):
    events = []
    for call, start, end in [("a", 1, 6), ("b", 3, 9)]:
        events += [
            record(
                "response_item",
                {
                    "type": "function_call",
                    "call_id": call,
                    "name": "collaboration.wait_agent",
                    "arguments": "SECRET",
                },
                start,
            ),
            record(
                "response_item",
                {"type": "function_call_output", "call_id": call, "output": "SECRET"},
                end,
            ),
        ]
    result = dev_pace.summarize([rollout(tmp_path, events)] * 2)
    assert result["calls"]["wait_agent"] == 2
    assert result["timing"]["observed_tool_union_seconds"] == 8
    assert "SECRET" not in json.dumps(result)
    assert result["timing"]["effective_work_seconds"] is None


def test_missing_metrics_remain_unknown(tmp_path):
    result = dev_pace.summarize([rollout(tmp_path, [usage(cached_input_tokens=None)])])
    assert result["tokens"]["uncached_input_plus_output_tokens"] is None
    assert result["reported_outcomes"]["rework_rounds"] is None
    assert result["fees"] is None


def test_no_usage_is_not_zero(tmp_path):
    assert dev_pace.summarize([rollout(tmp_path, [])])["tokens"]["input_tokens"] is None


def test_conflicting_response_is_refused(tmp_path):
    with pytest.raises(ValueError, match="conflicting"):
        dev_pace.summarize([rollout(tmp_path, [usage(), usage(output_tokens=16)])])


@pytest.mark.parametrize("bad", [True, -1, 1.5, "secret"])
def test_invalid_token_counts_are_refused(tmp_path, bad):
    with pytest.raises(ValueError):
        dev_pace.summarize([rollout(tmp_path, [usage(input_tokens=bad)])])


def test_inconsistent_cache_is_refused(tmp_path):
    with pytest.raises(ValueError):
        dev_pace.summarize([rollout(tmp_path, [usage(cached_input_tokens=101)])])


def test_line_cap_before_decode(tmp_path, monkeypatch):
    path = rollout(tmp_path, [usage()])
    monkeypatch.setattr(dev_pace, "MAX_LINE", 12)
    with pytest.raises(ValueError, match="limit"):
        dev_pace.summarize([path])


def test_turn_overlap_and_child_scope(tmp_path):
    events = [
        record("event_msg", {"type": "task_started", "turn_id": "a"}, 1),
        record("event_msg", {"type": "task_complete", "turn_id": "a"}, 6),
    ]
    a = rollout(tmp_path, events)
    b = rollout(
        tmp_path,
        [
            record(
                "session_meta",
                {
                    "id": "child",
                    "source": {"subagent": {"thread_spawn": {"parent_thread_id": "t"}}},
                },
            ),
            record("event_msg", {"type": "task_started", "turn_id": "b"}, 3),
            record("event_msg", {"type": "task_complete", "turn_id": "b"}, 8),
        ],
        "b.jsonl",
        "child",
    )
    result = dev_pace.summarize([a, b])
    assert result["parent_links"] == 1
    assert result["parents_outside_selection"] == 0
    assert result["timing"]["completed_turn_union_seconds"] == 7


def test_aborted_turn_with_integer_endpoints_contributes_to_observed_time(tmp_path):
    events = [
        record(
            "event_msg",
            {
                "type": "turn_aborted",
                "turn_id": "ended",
                "started_at": 1793750401,
                "completed_at": 1793750408,
            },
            8,
        ),
        record("event_msg", {"type": "turn_aborted", "turn_id": "unknown"}, 9),
    ]
    timing = dev_pace.summarize([rollout(tmp_path, events)])["timing"]
    assert timing["completed_turn_union_seconds"] == 7
    assert timing["unpaired_turns"] == 1


def test_cli_failure_does_not_echo_bad_payload(tmp_path, monkeypatch, capsys):
    path = tmp_path / "bad.jsonl"
    path.write_text("SECRET not JSON", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["dev_pace", str(path)])
    with pytest.raises(SystemExit) as exc:
        dev_pace.main()
    output = capsys.readouterr()
    assert exc.value.code == 1
    assert output.out == ""
    assert "SECRET" not in output.err


def test_cli_bad_tool_shape_has_no_traceback(tmp_path, monkeypatch, capsys):
    path = rollout(
        tmp_path,
        [
            record(
                "response_item",
                {"type": "function_call", "call_id": "a", "name": ["SECRET"]},
            )
        ],
    )
    monkeypatch.setattr(sys, "argv", ["dev_pace", str(path)])
    with pytest.raises(SystemExit):
        dev_pace.main()
    output = capsys.readouterr()
    assert output.out == "" and "SECRET" not in output.err


def test_unpaired_intervals_and_missing_response_identity(tmp_path):
    row = usage()
    del row["payload"]["response_id"]
    path = rollout(
        tmp_path,
        [
            row,
            record(
                "response_item",
                {"type": "function_call", "call_id": "a", "name": "wait_agent"},
                1,
            ),
        ],
    )
    result = dev_pace.summarize([path])
    assert result["unidentified_usage_records"] == 1
    assert result["tokens"]["input_tokens"] is None
    assert result["timing"]["unpaired_tool_calls"] == 1
    assert result["timing"]["observed_tool_union_seconds"] is None


def test_total_input_cap(tmp_path, monkeypatch):
    path = rollout(tmp_path, [usage()])
    monkeypatch.setattr(dev_pace, "MAX_TOTAL", 5)
    with pytest.raises(ValueError, match="limit"):
        dev_pace.summarize([path])


def test_custom_tools_are_included_without_contents(tmp_path):
    events = [
        record(
            "response_item",
            {
                "type": "custom_tool_call",
                "call_id": "c",
                "name": "functions.exec",
                "input": "SECRET",
            },
            1,
        ),
        record(
            "response_item",
            {"type": "custom_tool_call_output", "call_id": "c", "output": "SECRET"},
            4,
        ),
    ]
    result = dev_pace.summarize([rollout(tmp_path, events)])
    assert result["calls"]["other"] == 1
    assert result["timing"]["observed_tool_union_seconds"] == 3
    assert "SECRET" not in json.dumps(result)


def test_bad_cli_option_value_is_private(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dev_pace", "--review-findings", "SECRET", "a"])
    with pytest.raises(SystemExit) as exc:
        dev_pace.main()
    output = capsys.readouterr()
    assert exc.value.code == 2
    assert output.out == "" and "SECRET" not in output.err


@pytest.mark.parametrize("at", [None, "2026-11-04T00:00:01Z"])
def test_orphan_output_is_unknown_not_zero(tmp_path, at):
    event = record(
        "response_item", {"type": "function_call_output", "call_id": "orphan"}
    )
    event["timestamp"] = at
    result = dev_pace.summarize([rollout(tmp_path, [event])])
    assert result["call_coverage"]["orphan_outputs"] == 1
    assert result["calls"]["wait_agent"] is None
    assert result["timing"]["unpaired_tool_calls"] == 1


@pytest.mark.parametrize(
    "kind", ["function_call", "custom_tool_call", "function_call_output"]
)
def test_missing_call_identity_preserves_gap(tmp_path, kind):
    event = record("response_item", {"type": kind, "name": "spawn_agent"})
    result = dev_pace.summarize([rollout(tmp_path, [event])] * 2)
    assert result["call_coverage"]["unidentified_tool_records"] == 1
    assert result["calls"]["spawn_agent"] is None
    assert result["timing"]["unpaired_tool_calls"] is None


def test_unidentified_usage_is_deduplicated_across_resume(tmp_path):
    event = usage()
    del event["payload"]["response_id"]
    first = rollout(tmp_path, [event])
    resumed = rollout(tmp_path, [event], "resumed.jsonl")
    result = dev_pace.summarize([first, first, resumed])
    assert result["unidentified_usage_records"] == 1
    assert result["tokens"]["input_tokens"] is None
