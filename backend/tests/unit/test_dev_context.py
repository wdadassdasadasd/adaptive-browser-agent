"""Developer handoff stays bounded and rejects stale or incomplete summaries."""

import hashlib

import pytest

from scripts import dev_context


def snapshot(body="Stage 1.1; review pending"):
    return f"{dev_context.START}\n{body}\n{dev_context.END}\n".encode()


def test_current_uses_last_snapshot_without_printing_history():
    history = b"historical details\n" * 20000
    raw = history + snapshot("old") + snapshot("current")
    output = dev_context.render_context(raw)
    assert "current" in output
    assert "historical details" not in output
    assert "\nold\n" not in output
    assert len(output.encode("utf-8")) < dev_context.MAX_OUTPUT_BYTES
    assert f"record_sha256={hashlib.sha256(raw).hexdigest()}" in output


@pytest.mark.parametrize(
    "raw",
    [
        b"history without a current snapshot",
        b"<!-- dev-current:start -->\nunclosed",
        snapshot() + b"\nnew work without a refreshed current snapshot",
        snapshot() + b"<!-- dev-current:start -->\nnew unclosed snapshot",
    ],
)
def test_missing_incomplete_or_stale_snapshot_fails(raw):
    with pytest.raises(ValueError):
        dev_context.render_context(raw)


@pytest.mark.parametrize(
    "body",
    ["", " ", "x\n" * 61, "中" * 2001],
    ids=["empty", "blank", "line-overflow", "utf8-overflow"],
)
def test_snapshot_limits_count_utf8_bytes_and_lines(body):
    with pytest.raises(ValueError):
        dev_context.render_context(snapshot(body))


@pytest.mark.parametrize(
    "body",
    [
        "\n" * 61 + "old state",
        "old state" + "\n" * 61,
        " " * 6001 + "old state",
        "old state" + " " * 6001,
    ],
    ids=["leading-lines", "trailing-lines", "leading-spaces", "trailing-spaces"],
)
def test_raw_snapshot_overflow_is_rejected_before_trimming(body):
    with pytest.raises(ValueError):
        dev_context.render_context(snapshot(body))


@pytest.mark.parametrize(
    "body",
    ["x" * 5999, "中" * 1999 + "xx", "\n".join(["x"] * 60)],
    ids=["ascii-limit", "utf8-limit", "line-limit"],
)
def test_exact_raw_byte_and_line_limits_are_accepted(body):
    # snapshot() adds the final LF, included in the raw body budget.
    assert dev_context.render_context(snapshot(body))


def test_crlf_and_utf8_bom_preserve_current_text_and_source_line():
    raw = (
        b"\xef\xbb\xbf"
        + b"history\r\n"
        + snapshot("已实现，未验收").replace(b"\n", b"\r\n")
    )
    output = dev_context.render_context(raw)
    assert "已实现，未验收" in output
    assert "tasks.md:3" in output
    assert "\r" not in output


def test_cli_failure_does_not_emit_an_old_snapshot(tmp_path, monkeypatch, capsys):
    record = tmp_path / "tasks.md"
    record.write_bytes(snapshot("stale state") + b"later evidence")
    monkeypatch.setattr(dev_context, "RECORD", record)
    assert dev_context.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "DEV_CONTEXT_UNAVAILABLE" in captured.err
    assert "stale state" not in captured.err


def test_cli_reads_a_bounded_amount(tmp_path, monkeypatch, capsys):
    record = tmp_path / "tasks.md"
    record.write_bytes(b"x" * (dev_context.MAX_RECORD_BYTES + 1))
    monkeypatch.setattr(dev_context, "RECORD", record)
    assert dev_context.main() == 1
    assert capsys.readouterr().out == ""
