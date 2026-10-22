"""Shared deterministic identity rules for visited sources and searches."""

from urllib.parse import urlsplit, urlunsplit


def normalize_url(value: str) -> str:
    parts = urlsplit(value)
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, "")
    )


def normalize_query(value: str) -> str:
    return " ".join(value.casefold().split())
