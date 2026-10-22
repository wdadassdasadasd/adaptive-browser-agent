"""Check or arm the durable pilot ceiling; checking never touches the database.

Arming is a local database write and must only be invoked after the user has
separately authorized the specified live pilot and CNY limit. This command
does not submit tasks or invoke a provider.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from adaptive_research.infrastructure.config import REPOSITORY_ROOT, Settings
from adaptive_research.infrastructure.pg_store import PgStore, PricingUnavailable
from adaptive_research.infrastructure.pricing import (
    calculate_call_cost,
    load_price_book,
)

DEFAULT_BOOK = REPOSITORY_ROOT / "docs/evaluation/DEEPSEEK_CNY_PRICING_2026-10-22.json"


async def _arm(book: dict, reference: str, cap: Decimal) -> None:
    engine = create_async_engine(Settings().require_postgres_url(), pool_pre_ping=True)
    try:
        store = PgStore(
            async_sessionmaker(engine, expire_on_commit=False),
            price_book=book,
            require_budget=True,
        )
        await store.arm_pilot_budget(
            authorization_reference=reference, phase_max_cny=cap
        )
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--price-book", type=Path, default=DEFAULT_BOOK)
    parser.add_argument("--phase-max-cny", default="49")
    parser.add_argument(
        "--arm",
        action="store_true",
        help="write ceiling to a fresh PostgreSQL application DB",
    )
    parser.add_argument(
        "--authorization-reference",
        help="reference to separately obtained paid-run authorization",
    )
    args = parser.parse_args(argv)
    try:
        cap = Decimal(args.phase_max_cny)
        if not cap.is_finite() or not Decimal(1) <= cap <= Decimal(49):
            raise ValueError("pilot cap out of range")
        path = args.price_book
        if not path.is_absolute():
            path = REPOSITORY_ROOT / path
        book = load_price_book(path)
        now = datetime.now(UTC)
        decision = calculate_call_cost(
            model="deepseek-flash",
            currency="CNY",
            started_at=now,
            finished_at=now,
            evaluated_at=now,
            prompt_tokens=0,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=0,
            completion_tokens=0,
            price_book=book,
        )
        if decision.reason is not None:
            raise PricingUnavailable("CNY price snapshot is not currently verified")
        if args.arm:
            if not args.authorization_reference:
                raise ValueError("explicit authorization reference is required")
            asyncio.run(_arm(book, args.authorization_reference, cap))
        elif args.authorization_reference:
            raise ValueError("authorization reference only applies to --arm")
        print(
            json.dumps(
                {
                    "action": "armed" if args.arm else "offline_check_only",
                    "currency": "CNY",
                    "phase": "pilot",
                    "phase_max_cny": str(cap),
                    "project_max_cny": "299",
                    "price_revision": decision.price_revision,
                    "provider_calls": 0,
                    "tasks_submitted": 0,
                }
            )
        )
        return 0
    except (
        OSError,
        ValueError,
        TypeError,
        InvalidOperation,
        PricingUnavailable,
        SQLAlchemyError,
    ):
        print(
            "Pilot budget check refused; no research task was submitted.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
