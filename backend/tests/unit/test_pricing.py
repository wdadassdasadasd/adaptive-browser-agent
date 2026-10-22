"""Offline cost checks; synthetic dates never authorize historical live calls."""

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adaptive_research.infrastructure.pricing import (
    calculate_call_cost,
    load_price_book,
)

_SNAPSHOT = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/DEEPSEEK_CNY_PRICING_2026-10-21.json"
)


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _rehash(book):
    book.pop("snapshot_sha256", None)
    book["snapshot_sha256"] = hashlib.sha256(
        json.dumps(
            book, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return book


def _book_for(start):
    """Move verification only in a synthetic fixture to exercise the calendar."""
    book = deepcopy(load_price_book(_SNAPSHOT))
    verified = start - timedelta(minutes=1)
    book["verified_at"] = verified.isoformat()
    book["valid_until"] = (verified + timedelta(hours=24)).isoformat()
    for source in book["sources"]:
        source["fetched_at"] = verified.isoformat()
    return _rehash(book)


def _args(local="2026-10-21T14:00:00+08:00"):
    start = _utc(local)
    return {
        "model": "deepseek-flash",
        "currency": "CNY",
        "started_at": start,
        "finished_at": start + timedelta(seconds=30),
        "evaluated_at": start + timedelta(seconds=31),
        "prompt_tokens": 1000,
        "prompt_cache_hit_tokens": 400,
        "prompt_cache_miss_tokens": 600,
        "completion_tokens": 100,
        "price_book": _book_for(start),
    }


def test_frozen_artifact_calculates_current_peak_cost():
    args = _args()
    args["price_book"] = load_price_book(_SNAPSHOT)
    result = calculate_call_cost(**args)
    assert result.known_cost_cny == Decimal("0.002016")
    assert result.tariff == "peak"
    assert result.price_revision == args["price_book"]["price_revision"]
    assert result.reason is None


@pytest.mark.parametrize(
    ("local", "tariff", "expected"),
    [
        ("2026-10-21T09:00:00+08:00", "peak", "0.002016"),
        ("2026-10-21T11:59:00+08:00", "peak", "0.002016"),
        ("2026-10-21T12:00:00+08:00", "off_peak", "0.001008"),
        ("2026-10-21T13:59:00+08:00", "off_peak", "0.001008"),
        ("2026-10-21T14:00:00+08:00", "peak", "0.002016"),
        ("2026-10-21T18:00:00+08:00", "off_peak", "0.001008"),
        ("2026-10-24T10:00:00+08:00", "off_peak", "0.001008"),
        # Official makeup work Saturday is still a weekend under the price rule.
        ("2026-10-10T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-01-01T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-02-23T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-04-06T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-05-05T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-06-19T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-09-25T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-10-07T10:00:00+08:00", "off_peak", "0.001008"),
        ("2026-10-08T10:00:00+08:00", "peak", "0.002016"),
    ],
)
def test_verified_calendar_tariffs(local, tariff, expected):
    result = calculate_call_cost(**_args(local))
    assert result.known_cost_cny == Decimal(expected)
    assert result.tariff == tariff


@pytest.mark.parametrize(
    ("hit", "miss", "output", "expected"),
    [(1_000_000, 0, 0, "0.04"), (0, 1_000_000, 0, "2"), (0, 0, 1_000_000, "8")],
)
def test_independent_token_components_and_exact_decimal(hit, miss, output, expected):
    args = _args()
    args.update(
        prompt_tokens=hit + miss,
        prompt_cache_hit_tokens=hit,
        prompt_cache_miss_tokens=miss,
        completion_tokens=output,
    )
    assert calculate_call_cost(**args).known_cost_cny == Decimal(expected)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("08:59:59", "09:00:00"),
        ("11:59:59", "12:00:00"),
        ("13:59:59", "14:00:00"),
        ("17:59:59", "18:00:00"),
        ("08:00:00", "19:00:00"),
    ],
)
def test_crossing_tariffs_is_unknown_even_when_endpoints_are_both_off_peak(start, end):
    args = _args(f"2026-10-21T{start}+08:00")
    args["finished_at"] = _utc(f"2026-10-21T{end}+08:00")
    args["evaluated_at"] = args["finished_at"] + timedelta(seconds=1)
    result = calculate_call_cost(**args)
    assert result.known_cost_cny is None
    assert result.reason == "tariff_boundary_crossed"


def test_crossing_weekend_clock_boundaries_with_no_tariff_change_is_known():
    args = _args("2026-10-24T08:00:00+08:00")
    args["finished_at"] += timedelta(hours=11)
    args["evaluated_at"] = args["finished_at"]
    assert calculate_call_cost(**args).known_cost_cny == Decimal("0.001008")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("model", "deepseek-chat", "unsupported_model"),
        ("model", "new-silent-model-version", "unsupported_model"),
        ("currency", "USD", "unsupported_currency"),
        ("prompt_tokens", None, "missing_or_invalid_usage"),
        ("prompt_cache_hit_tokens", None, "missing_or_invalid_usage"),
        ("prompt_cache_miss_tokens", None, "missing_or_invalid_usage"),
        ("completion_tokens", None, "missing_or_invalid_usage"),
        ("completion_tokens", -1, "missing_or_invalid_usage"),
        ("completion_tokens", True, "missing_or_invalid_usage"),
        ("completion_tokens", 1.5, "missing_or_invalid_usage"),
        ("prompt_tokens", 999, "cache_split_mismatch"),
    ],
)
def test_unknown_is_never_zero(field, value, reason):
    args = _args()
    args[field] = value
    result = calculate_call_cost(**args)
    assert result.known_cost_cny is None
    assert result.price_revision is None
    assert result.reason == reason


def test_actual_version_name_is_explicitly_supported():
    args = _args()
    args["model"] = "DeepSeek-V4.1-Flash-1017"
    assert calculate_call_cost(**args).known_cost_cny == Decimal("0.002016")


def test_explicit_complete_zero_usage_can_be_zero():
    args = _args()
    for name in (
        "prompt_tokens",
        "prompt_cache_hit_tokens",
        "prompt_cache_miss_tokens",
        "completion_tokens",
    ):
        args[name] = 0
    assert calculate_call_cost(**args).known_cost_cny == Decimal(0)


@pytest.mark.parametrize(
    "local", ["2025-12-31T10:00:00+08:00", "2027-01-01T10:00:00+08:00"]
)
def test_unverified_calendar_year_is_unknown(local):
    result = calculate_call_cost(**_args(local))
    assert result.known_cost_cny is None
    assert result.reason == "unverified_calendar_year"


def test_stale_or_not_yet_verified_snapshot_is_unknown():
    args = _args()
    args["evaluated_at"] = datetime.fromisoformat(args["price_book"]["valid_until"])
    assert calculate_call_cost(**args).reason == "stale_price_book"
    args = _args()
    args["started_at"] -= timedelta(minutes=2)
    assert calculate_call_cost(**args).reason == "before_price_verification"


@pytest.mark.parametrize("field", ["started_at", "finished_at", "evaluated_at"])
def test_naive_timestamps_are_not_interpreted_as_local_time(field):
    args = _args()
    args[field] = args[field].replace(tzinfo=None)
    assert calculate_call_cost(**args).reason == "invalid_utc_timestamps"


def test_reversed_or_future_interval_is_unknown():
    args = _args()
    args["finished_at"] = args["started_at"] - timedelta(seconds=1)
    assert calculate_call_cost(**args).reason == "invalid_time_order"
    args = _args()
    args["evaluated_at"] = args["started_at"]
    assert calculate_call_cost(**args).reason == "invalid_time_order"


@pytest.mark.parametrize(
    "damage", ["digest", "source", "facts", "rate", "calendar", "revision"]
)
def test_invalid_source_or_corrupted_price_book_fails_closed(damage):
    args = _args()
    book = args["price_book"]
    if damage == "digest":
        book["rates_cny_per_million"]["peak"]["output"] = "7"
    else:
        if damage == "source":
            book["sources"][0]["url"] = "https://untrusted.example/pricing"
        elif damage == "facts":
            book["sources"][0]["facts"] = "changed facts without corresponding hash"
        elif damage == "rate":
            book["rates_cny_per_million"]["peak"]["output"] = "Infinity"
        elif damage == "calendar":
            book["calendar"]["holiday_ranges"].pop()
        else:
            book["price_revision"] = ""
        _rehash(book)
    result = calculate_call_cost(**args)
    assert result.known_cost_cny is None
    assert result.reason == "invalid_price_book"


def test_price_book_is_explicit_and_never_mutated():
    args = _args()
    before = deepcopy(args["price_book"])
    calculate_call_cost(**args)
    assert args["price_book"] == before
