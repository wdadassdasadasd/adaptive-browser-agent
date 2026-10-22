"""Conservative extraction and verification of explicit research quantities."""

import re
from collections import defaultdict
from collections.abc import Iterable
from urllib.parse import urlsplit

from adaptive_research.agent.state import ResearchFact

_EN_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twenty-one": 21,
    "twenty-two": 22,
    "twenty-three": 23,
    "twenty-four": 24,
    "twenty-five": 25,
    "twenty-six": 26,
    "twenty-seven": 27,
    "twenty-eight": 28,
    "twenty-nine": 29,
    "thirty": 30,
}
_EN_WORDS = "|".join(sorted(_EN_NUMBERS, key=len, reverse=True))
_EN_PATTERN = re.compile(
    rf"\b(?P<count>\d{{1,2}}|{_EN_WORDS})\b(?!\.\d)"
    r"(?:\s+[a-z][a-z-]*){0,8}\s+"
    r"(?P<noun>projects?|repository|repositories|candidates?|tools?|changes?)\b",
    re.IGNORECASE,
)
_ZH_PATTERN = re.compile(
    r"(?P<count>\d{1,2}|[一二三四五六七八九十两]{1,3})\s*[个项条]?"
    r"[^\d一二三四五六七八九十两，。；;]{0,12}"
    r"(?P<noun>项目|仓库|候选|工具|更新|变化|改动)"
)
_PROJECT_NOUNS = {
    "project",
    "projects",
    "repository",
    "repositories",
    "candidate",
    "candidates",
    "tool",
    "tools",
    "项目",
    "仓库",
    "候选",
    "工具",
}
_COUNT_CUES = {
    "find",
    "list",
    "identify",
    "compare",
    "summarize",
    "give",
    "select",
    "show",
    "describe",
    "research",
    "need",
    "me",
    "and",
    "plus",
    "top",
    "least",
    "exactly",
}


def _number(raw: str) -> int | None:
    text = raw.casefold()
    if text.isdecimal():
        value = int(text)
    elif text in _EN_NUMBERS:
        value = _EN_NUMBERS[text]
    elif text in {"十", "两"}:
        value = 10 if text == "十" else 2
    else:
        digits = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "两": 2,
        }
        if text.startswith("十") and len(text) == 2:
            value = 10 + digits.get(text[1], 100)
        elif "十" in text and len(text) == 3:
            value = digits.get(text[0], 100) * 10 + digits.get(text[2], 100)
        elif text.endswith("十") and len(text) == 2:
            value = digits.get(text[0], 100) * 10
        else:
            value = digits.get(text, 100)
    return value if 1 <= value <= 30 else None


def parse_goal_targets(goal: str) -> dict[str, int]:
    """Return unambiguous requested object counts by supported object kind."""

    found: dict[str, set[int]] = defaultdict(set)
    for pattern in (_EN_PATTERN, _ZH_PATTERN):
        for match in pattern.finditer(goal):
            if pattern is _EN_PATTERN:
                preceding = re.search(r"([A-Za-z-]+)\s*$", goal[: match.start()])
                if preceding and preceding.group(1).casefold() not in _COUNT_CUES:
                    continue
            count = _number(match.group("count"))
            if count is None:
                continue
            kind = (
                "project"
                if match.group("noun").casefold() in _PROJECT_NOUNS
                else "change"
            )
            found[kind].add(count)
    return {
        kind: next(iter(counts)) for kind, counts in found.items() if len(counts) == 1
    }


def subject_in_evidence(subject: str, evidence: str) -> bool:
    """Require the complete subject name, allowing ordinary surrounding prose."""

    words = subject.split()
    if not words:
        return False
    first, last = words[0][0], words[-1][-1]
    ascii_name_characters = r"[A-Za-z0-9_-]"
    left = (
        rf"(?<!{ascii_name_characters})"
        if first.isascii() and (first.isalnum() or first in "_-")
        else ""
    )
    right = (
        rf"(?!{ascii_name_characters})"
        if last.isascii() and (last.isalnum() or last in "_-")
        else ""
    )
    name = r"\s+".join(re.escape(word) for word in words)
    return re.search(left + name + right, evidence, flags=re.IGNORECASE) is not None


def subject_matches_repository_url(subject: str, source_url: str) -> bool:
    """Match a repository identity against its exact official GitHub URL."""

    parsed = urlsplit(source_url)
    if parsed.scheme != "https":
        return False
    segments = parsed.path.strip("/").split("/")
    if parsed.hostname == "api.github.com":
        segments = segments[1:] if segments[0] == "repos" else []
    elif parsed.hostname == "github.com":
        if segments[0].casefold() in {
            "about",
            "account",
            "apps",
            "codespaces",
            "collections",
            "dashboard",
            "enterprise",
            "events",
            "explore",
            "features",
            "issues",
            "login",
            "marketplace",
            "new",
            "notifications",
            "orgs",
            "organizations",
            "pulls",
            "search",
            "security",
            "settings",
            "signup",
            "sponsors",
            "stars",
            "topics",
            "trending",
            "users",
        }:
            return False
    else:
        return False
    repository_or_release = (
        len(segments) == 2
        or (len(segments) == 3 and segments[2] == "releases")
        or (
            len(segments) == 5
            and segments[2:4] == ["releases", "tag"]
            and bool(segments[4])
        )
    )
    return repository_or_release and subject.casefold() == (
        f"{segments[0]}/{segments[1]}".casefold()
    )


def verified_subject_counts(facts: Iterable[ResearchFact]) -> dict[str, int]:
    """Count distinct subjects whose name is present in admitted source evidence."""

    subjects: dict[str, set[str]] = defaultdict(set)
    for fact in facts:
        if not fact.subject or not fact.subject_kind or not fact.evidence:
            continue
        normalized = " ".join(fact.subject.split()).casefold()
        if normalized and (
            subject_in_evidence(fact.subject, fact.evidence)
            or (
                fact.subject_kind == "project"
                and subject_matches_repository_url(fact.subject, fact.source_url)
            )
        ):
            subjects[fact.subject_kind].add(normalized)
    return {kind: len(names) for kind, names in subjects.items()}


def targets_met(targets: dict[str, int], facts: Iterable[ResearchFact]) -> bool:
    """Require every unambiguous requested object count to be reached."""

    if not targets:
        return False
    counts = verified_subject_counts(facts)
    return all(counts.get(kind, 0) >= count for kind, count in targets.items())
