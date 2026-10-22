"""Offline token pricing from a frozen, explicitly verified CNY price book.

This module neither fetches prices nor authorizes paid execution. A known result
is a calculation against the cited snapshot, not a provider invoice. Persist it
with its price revision; do not silently recalculate old attempts with new prices.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

_BEIJING = timezone(timedelta(hours=8))
_SOURCES = {
    "pricing": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing/",
    "usage": "https://api-docs.deepseek.com/api/create-chat-completion/",
    "calendar": "https://www.gov.cn/zhengce/content/202511/content_7047090.htm",
}


@dataclass(frozen=True)
class CostDecision:
    known_cost_cny: Decimal | None
    price_revision: str | None
    tariff: str | None
    reason: str | None


def load_price_book(path: Path) -> dict[str, Any]:
    """Read an explicitly selected local artifact; never discover or refresh it."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("price book must be an object")
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _utc(value: datetime) -> bool:
    return isinstance(value, datetime) and value.utcoffset() == timedelta(0)


def _timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if not _utc(result):
        raise ValueError("timestamps must be aware UTC")
    return result


def _validate_book(book: Mapping[str, Any]) -> tuple[datetime, datetime, set[date]]:
    if not isinstance(book, Mapping):
        raise TypeError("price book must be an object")
    if book["schema_version"] != 1 or book["provider"] != "deepseek":
        raise ValueError("unsupported price book")
    if (
        not isinstance(book["price_revision"], str)
        or not book["price_revision"].strip()
    ):
        raise ValueError("missing price revision")
    if book["snapshot_sha256"] != _digest(
        {key: value for key, value in book.items() if key != "snapshot_sha256"}
    ):
        raise ValueError("snapshot digest mismatch")
    if (
        book["currency"] != "CNY"
        or book["request_model"] != "deepseek-flash"
        or book["provider_models"] != ["deepseek-flash", "DeepSeek-V4.1-Flash-1017"]
        or book["unit_tokens"] != 1_000_000
        or book["timezone"] != "UTC+08:00"
        or book["peak_weekdays"] != [0, 1, 2, 3, 4]
        or book["peak_windows"] != [["09:00", "12:00"], ["14:00", "18:00"]]
    ):
        raise ValueError("unsupported pricing semantics")
    verified = _timestamp(book["verified_at"])
    expires = _timestamp(book["valid_until"])
    if not timedelta(0) < expires - verified <= timedelta(hours=24):
        raise ValueError("verification window must be at most 24 hours")
    sources = book["sources"]
    if not isinstance(sources, list) or len(sources) != len(_SOURCES):
        raise ValueError("missing provenance")
    if {source["id"] for source in sources} != set(_SOURCES):
        raise ValueError("missing provenance")
    for source in sources:
        if (
            source["url"] != _SOURCES[source["id"]]
            or not isinstance(source["facts"], str)
            or not source["facts"].strip()
            or source["facts_sha256"]
            != hashlib.sha256(source["facts"].encode("utf-8")).hexdigest()
            or _timestamp(source["fetched_at"]) != verified
        ):
            raise ValueError("unverified provenance")
    calendar = book["calendar"]
    if calendar["year"] != 2026 or calendar["weekend_makeup_is_peak"] is not False:
        raise ValueError("unsupported calendar")
    holidays: set[date] = set()
    for start, end in calendar["holiday_ranges"]:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.year != 2026 or last.year != 2026 or last < first:
            raise ValueError("invalid calendar range")
        while first <= last:
            if first in holidays:
                raise ValueError("overlapping holiday range")
            holidays.add(first)
            first += timedelta(days=1)
    if not holidays or len(calendar["holiday_ranges"]) != 7:
        raise ValueError("incomplete calendar")
    for tariff in ("peak", "off_peak"):
        for component in ("cache_hit", "cache_miss", "output"):
            raw = book["rates_cny_per_million"][tariff][component]
            if not isinstance(raw, str):
                raise TypeError("rates must be decimal strings")
            rate = Decimal(raw)
            if (
                not rate.is_finite()
                or not Decimal("0.000001") <= rate <= Decimal(1_000_000)
                or rate.as_tuple().exponent < -6
            ):
                raise ValueError("invalid rate")
    return verified, expires, holidays


def _tariff(at: datetime, holidays: set[date]) -> str:
    if at.weekday() >= 5 or at.date() in holidays:
        return "off_peak"
    clock = at.time()
    return (
        "peak"
        if time(9) <= clock < time(12) or time(14) <= clock < time(18)
        else "off_peak"
    )


def calculate_call_cost(
    *,
    model: str,
    currency: str,
    started_at: datetime,
    finished_at: datetime,
    prompt_tokens: int | None,
    prompt_cache_hit_tokens: int | None,
    prompt_cache_miss_tokens: int | None,
    completion_tokens: int | None,
    price_book: Mapping[str, Any],
    evaluated_at: datetime,
) -> CostDecision:
    """Return exact Decimal token cost only when every required fact is known.

    All timestamps must be aware UTC database timestamps. The closed request
    interval must fit one tariff: finishing exactly at a tariff change is unknown.
    Missing usage, ambiguous time, expired evidence and unsupported models return
    null cost, never an estimated zero. Search/Fetch fees are outside this book.
    """

    def unknown(reason: str) -> CostDecision:
        return CostDecision(None, None, None, reason)

    try:
        verified, expires, holidays = _validate_book(price_book)
    except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
        return unknown("invalid_price_book")
    if currency != "CNY":
        return unknown("unsupported_currency")
    if model not in price_book["provider_models"]:
        return unknown("unsupported_model")
    if not all(_utc(value) for value in (started_at, finished_at, evaluated_at)):
        return unknown("invalid_utc_timestamps")
    if finished_at < started_at or evaluated_at < finished_at:
        return unknown("invalid_time_order")
    try:
        local_start = started_at.astimezone(_BEIJING)
        local_end = finished_at.astimezone(_BEIJING)
    except (ValueError, OverflowError):
        return unknown("unverified_calendar_year")
    if local_start.year != 2026 or local_end.year != 2026:
        return unknown("unverified_calendar_year")
    if evaluated_at < verified or started_at < verified:
        return unknown("before_price_verification")
    if evaluated_at >= expires or finished_at >= expires:
        return unknown("stale_price_book")
    tokens = (
        prompt_tokens,
        prompt_cache_hit_tokens,
        prompt_cache_miss_tokens,
        completion_tokens,
    )
    if any(type(value) is not int or value < 0 for value in tokens):
        return unknown("missing_or_invalid_usage")
    if prompt_tokens != prompt_cache_hit_tokens + prompt_cache_miss_tokens:
        return unknown("cache_split_mismatch")
    tariff = _tariff(local_start, holidays)
    # Endpoints alone are insufficient: 08:00..19:00 crosses both peak windows.
    cursor = local_start.date()
    while cursor <= local_end.date():
        for hour in (0, 9, 12, 14, 18):
            boundary = datetime.combine(cursor, time(hour), tzinfo=_BEIJING)
            if local_start < boundary <= local_end:
                before = boundary - timedelta(microseconds=1)
                if _tariff(before, holidays) != _tariff(boundary, holidays):
                    return unknown("tariff_boundary_crossed")
        cursor += timedelta(days=1)
    if _tariff(local_end, holidays) != tariff:
        return unknown("tariff_boundary_crossed")
    rates = price_book["rates_cny_per_million"][tariff]
    with localcontext() as context:
        context.prec = max(28, max(len(str(value)) for value in tokens) + 20)
        cost = (
            Decimal(prompt_cache_hit_tokens) * Decimal(rates["cache_hit"])
            + Decimal(prompt_cache_miss_tokens) * Decimal(rates["cache_miss"])
            + Decimal(completion_tokens) * Decimal(rates["output"])
        ) / Decimal(1_000_000)
    return CostDecision(cost, price_book["price_revision"], tariff, None)
