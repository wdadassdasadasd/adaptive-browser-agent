"""Deterministic, conservative coverage checks for the frozen V1 cases."""

import re
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    steps: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    duplicate_urls: int = Field(default=0, ge=0)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    result_coverage: float = Field(default=0, ge=0, le=1)


URL_RE = re.compile(r"https?://[^\s<>\])}|`]+", re.IGNORECASE)
VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-.][\w]+)?\b", re.IGNORECASE)
LATEST_VERSION_AFTER_RE = re.compile(
    rf"\b(?:latest|current|newest|most recent)\b[^\n.;]{{0,80}}?(?P<version>{VERSION_RE.pattern})",
    re.IGNORECASE,
)
LATEST_VERSION_BEFORE_RE = re.compile(
    rf"(?P<version>{VERSION_RE.pattern})[^\n.;]{{0,60}}?\b(?:latest|current|newest|most recent)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:20\d\d[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20\d\d)\b",
    re.IGNORECASE,
)
PUBLICATION_DATE_RE = re.compile(
    r"\b(?:published|released|publication date|release date)\b\s*(?:on|:|=)?\s*"
    + DATE_RE.pattern,
    re.IGNORECASE,
)
VERSION_DATE_RE = re.compile(
    VERSION_RE.pattern + r"\s*\(\s*" + DATE_RE.pattern + r"\s*\)",
    re.IGNORECASE,
)
REPOSITORY_HOSTS = {
    "github.com",
    "gitlab.com",
    "codeberg.org",
    "bitbucket.org",
    "git.sr.ht",
}
CHANGE_RE = re.compile(
    r"\b(?:add|adds|added|fix|fixes|fixed|change|changes|changed|"
    r"remove|removes|removed|improve|improves|improved|update|updates|updated|"
    r"introduce|introduces|introduced)\b|(?:新增|修复|修改|移除|改进|更新)",
    re.IGNORECASE,
)
RELEASE_TASK_ECHO_RE = re.compile(
    r"\b(?:two|2)\s+changes?\s+from\s+(?:its|the)\s+release notes\b",
    re.IGNORECASE,
)
RELEASE_TITLE_RE = re.compile(
    r"\b(?:titled|title\s*(?:is|:))\s*(?:(?P<quote>['\"]).*?(?P=quote)|[^\n]*?(?:\.(?=\s|$)|$))",
    re.IGNORECASE | re.MULTILINE,
)
RELEASE_PAGE_TITLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:Release\s+)?v?\d+\.\d+(?:\.\d+)?\s*:.*·\s*GitHub\s*$",
    re.IGNORECASE,
)
UNFINISHED_SECTION_RE = re.compile(
    r"^[ \t]*##[ \t]+Unknown or unfinished[ \t]*\r?\n.*?(?=^[ \t]*##[ \t]+|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def urls_in(text: str) -> list[str]:
    """Return cited HTTP URLs, excluding trailing prose punctuation."""
    return [match.group().rstrip(".,;:\"'") for match in URL_RE.finditer(text)]


def normalized_url(url: str) -> str:
    """Preserve path/query identity while ignoring URL host case and fragment."""
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit(
        (
            parsed.scheme.lower(),
            host.lower() + port,
            parsed.path,
            parsed.query,
            "",
        )
    )


def url_visit_transitions(urls: list[str | None]) -> list[str]:
    """Keep a browser URL once per contiguous visit, including later revisits."""
    visits: list[str] = []
    previous: str | None = None
    for url in urls:
        if not url:
            continue
        current = normalized_url(url)
        if current != previous:
            visits.append(url)
            previous = current
    return visits


def duplicate_url_count(urls: list[str]) -> int:
    normalized = [normalized_url(url) for url in urls]
    return len(normalized) - len(set(normalized))


def _official(url: str, case_id: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    path = urlsplit(url).path.lower()
    if case_id == "B02":
        page = path.strip("/")
        if host == "fastapi.tiangolo.com":
            return page not in {"", "index.html"}
        if host == "flask.palletsprojects.com":
            return bool(page) and not re.fullmatch(
                r"(?:index\.html|en/[^/]+(?:/index\.html)?)", page
            )
        return False
    if case_id == "B03":
        return (
            host == "github.com"
            and path.startswith("/browser-use/browser-use/releases/tag/")
            and VERSION_RE.fullmatch(path.rsplit("/", 1)[-1]) is not None
        )
    if host == "api.github.com":
        segments = path.strip("/").split("/")
        return len(segments) >= 3 and segments[0] == "repos" and all(segments[1:3])
    return host in REPOSITORY_HOSTS and len(path.strip("/").split("/")) >= 2


def _repository(url: str) -> tuple[str, ...]:
    """Identify a cited repository, including GitLab subgroup paths."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    segments = parsed.path.strip("/").split("/")
    if host == "api.github.com" and len(segments) >= 3 and segments[0] == "repos":
        return ("github.com", *segments[1:3])
    if host == "gitlab.com":
        if "-" in segments:
            segments = segments[: segments.index("-")]
        else:
            # Older GitLab issue links omit /-/; they still name the same project.
            for index in range(2, len(segments) - 1):
                if segments[index] == "issues" and segments[index + 1].isdigit():
                    segments = segments[:index]
                    break
        return (host, *segments)
    return (host, *segments[:2])


def _repository_root(url: str) -> bool:
    parsed = urlsplit(url)
    segments = parsed.path.strip("/").split("/")
    if (parsed.hostname or "").lower() == "gitlab.com":
        return len(segments) >= 2 and tuple(segments) == _repository(url)[1:]
    return len(segments) == 2


def score_answer(case_id: str, answer: str) -> dict[str, bool]:
    """Score explicit values co-located with relevant official URLs.

    This conservative rubric does not validate facts against a changing site;
    D7 manual source checks remain necessary.
    """
    if case_id not in {"B01", "B02", "B03"}:
        raise ValueError(f"unknown benchmark case: {case_id}")
    if case_id == "B03":
        answer = UNFINISHED_SECTION_RE.sub("", answer)
    sections = [
        part
        for part in re.split(r"\n\s*\n|(?=^#{1,4}\s)", answer, flags=re.MULTILINE)
        if part.strip()
    ]
    if case_id in {"B01", "B02"}:
        attributable = []
        for part in sections:
            lines = part.splitlines()
            sourced_lines = [
                line
                for line in lines
                if any(_official(url, case_id) for url in urls_in(line))
            ]
            if len(sourced_lines) >= 2 and all(
                len([url for url in urls_in(line) if _official(url, case_id)]) == 1
                for line in sourced_lines
            ):
                chunk = []
                for line in lines:
                    if case_id == "B01" and re.match(
                        r"^\s*(?:(?:[-*+]|\d+[.)])\s+)?[\w.-]+/[\w.-]+\s*:", line
                    ):
                        # A new candidate starts a new attribution block.
                        # Uncited facts about the previous candidate cannot
                        # inherit this candidate's subsequent source URL.
                        chunk = []
                    if (
                        case_id == "B02"
                        and line.lstrip().startswith("#")
                        and "fastapi" in line.casefold()
                        and "flask" in line.casefold()
                        and not urls_in(line)
                    ):
                        continue
                    chunk.append(line)
                    if line in sourced_lines:
                        attributable.append("\n".join(chunk))
                        chunk = []
            else:
                attributable.append(part)
        sections = attributable
    cited = [
        (part, [u for u in urls_in(part) if _official(u, case_id)]) for part in sections
    ]
    if case_id == "B01":
        projects: dict[str, list[str]] = {}
        for part, links in cited:
            repositories = [_repository(url) for url in links if _official(url, "B01")]
            # One paragraph citing multiple repositories cannot attribute the
            # stated license and install command to either candidate.
            if len(set(repositories)) != 1:
                continue
            projects.setdefault("/".join(repositories[0]).lower(), []).append(part)

        def candidate_fields(repository: str, part: str) -> dict[str, bool]:
            prose = URL_RE.sub("", part)
            part_links = [url for url in urls_in(part) if _official(url, "B01")]
            heading = re.search(r"^#{1,4}\s+([^\n]+)", part, re.MULTILINE)
            slug = repository.split("/")[-1]
            heading_matches_repo = bool(
                heading
                and any(
                    len(word) >= 3 and word.casefold() in slug.casefold()
                    for word in re.findall(r"[A-Za-z0-9]+", heading.group(1))
                )
            )
            lead = re.search(r"(?m)^\s*(?:[-*]|\d+[.)])\s+([A-Za-z][\w-]*)", part)
            named_match = re.search(
                r"\b(?:name|project|项目)\b\s*[:：]\s*([\w-]+)",
                prose,
                re.IGNORECASE,
            )
            named = bool(
                named_match
                or heading_matches_repo
                or slug
                and re.search(rf"\b{re.escape(slug)}\b", prose, re.IGNORECASE)
                or lead
                and lead.group(1).casefold() in slug.casefold()
            )
            license_present = bool(
                re.search(
                    r"\blicen[sc]e\b\s*[:：]\s*[A-Za-z][\w .-]+", prose, re.IGNORECASE
                )
                or re.search(
                    r"\b(?:MIT|Apache[- ]?\d+(?:\.\d+)?|BSD[- ]?\d+(?:-Clause)?|"
                    r"GPL[- ]?\d+(?:\.\d+)?|MPL[- ]?\d+(?:\.\d+)?|ISC)\b",
                    prose,
                    re.IGNORECASE,
                )
            )
            aliases = {slug.casefold()}
            prefix = slug.split("-")[0].casefold()
            if prefix not in {"browser", "python", "py", "agent", "web", "tool"}:
                aliases.add(prefix)
            if named_match:
                aliases.add(named_match.group(1).casefold())
            if heading_matches_repo and heading:
                aliases.add(heading.group(1).split()[0].casefold())
            if lead and lead.group(1).casefold() in slug.casefold():
                aliases.add(lead.group(1).casefold())
            install_present = any(
                match.group(1).rstrip(".").casefold().replace("_", "-") in aliases
                for match in re.finditer(
                    r"(?:pip|uv)\s+(?:install|add)\s+(?:--?[\w-]+\s+)*[`\"']?([A-Za-z][\w.-]*)",
                    prose,
                    re.IGNORECASE,
                )
            )
            return {
                "name": named,
                "repository": any(_repository_root(url) for url in part_links),
                "license": license_present,
                "install": install_present,
                "source": bool(part_links),
            }

        ranked = []
        for repository, parts in projects.items():
            part_fields = [candidate_fields(repository, part) for part in parts]
            ranked.append(
                {
                    name: any(values[name] for values in part_fields)
                    for name in ("name", "repository", "license", "install", "source")
                }
            )
        ranked.sort(key=lambda values: sum(values.values()), reverse=True)
        fields: dict[str, bool] = {}
        for index in range(2):
            values = ranked[index] if index < len(ranked) else {}
            for name in ("name", "repository", "license", "install", "source"):
                fields[f"project_{index + 1}_{name}"] = values.get(name, False)
        return fields
    if case_id == "B02":
        fields = {}
        for name, host in (
            ("fastapi", "fastapi.tiangolo.com"),
            ("flask", "flask.palletsprojects.com"),
        ):
            parts = []
            for part, links in cited:
                if {urlsplit(u).hostname for u in links} != {host}:
                    continue
                prose_part = URL_RE.sub("", part)
                first_subject = re.search(
                    r"\b(?:fastapi|flask)\b", prose_part, re.IGNORECASE
                )
                if first_subject and first_subject.group().casefold() == name:
                    parts.append(prose_part)
            prose = "\n".join(parts)
            fields[name + "_name"] = bool(parts)
            fields[name + "_route"] = bool(
                re.search(
                    r"(?:@\w+\.(?:get|route|post)|\broute\b.*(?:decorator|declare|@))",
                    prose,
                    re.IGNORECASE,
                )
            )
            fields[name + "_async"] = bool(
                re.search(
                    r"\basync\b.*\b(?:supported|documented|handler|views?|def)\b|\b(?:supported|documented|handler|views?)\b.*\basync\b",
                    prose,
                    re.IGNORECASE,
                )
            )
            fields[name + "_install"] = bool(
                re.search(
                    rf"(?:pip\s+install|uv\s+add)\s+[`\"']?{name}"
                    r"(?:\[[A-Za-z0-9,_.-]+\])?[`\"']?(?![\w-])",
                    prose,
                    re.IGNORECASE,
                )
            )
            fields[name + "_source"] = bool(parts)
        return fields
    release_parts = [part for part, links in cited if links]
    release_paths = {urlsplit(url).path.lower() for _, links in cited for url in links}
    release_prose = (
        URL_RE.sub("", answer)
        if len(release_paths) == 1
        else "\n".join(URL_RE.sub("", part) for part in release_parts)
    )
    release_prose = RELEASE_TASK_ECHO_RE.sub("", release_prose)
    versions = [
        match.group().casefold().removeprefix("v")
        for match in VERSION_RE.finditer(release_prose)
    ]
    latest_claims_after = {
        match.group("version").casefold().removeprefix("v")
        for match in LATEST_VERSION_AFTER_RE.finditer(release_prose)
    }
    latest_claims_before = {
        match.group("version").casefold().removeprefix("v")
        for match in LATEST_VERSION_BEFORE_RE.finditer(release_prose)
    }
    latest_claims = latest_claims_after or latest_claims_before
    claimed_versions = latest_claims or set(versions[:1])
    cited_tags = {
        match.group().casefold().removeprefix("v")
        for _, links in cited
        for url in links
        if "/releases/tag/" in urlsplit(url).path.lower()
        if (match := VERSION_RE.fullmatch(urlsplit(url).path.rsplit("/", 1)[-1]))
    }
    changes = []
    for line in RELEASE_TITLE_RE.sub("", release_prose).splitlines():
        if RELEASE_PAGE_TITLE_RE.match(line):
            continue
        if re.fullmatch(
            r"\s*#{0,6}\s*changes?\s+(?:in|for|of)\s+(?:this\s+)?release\s*",
            line,
            re.IGNORECASE,
        ):
            continue
        matches = list(CHANGE_RE.finditer(line))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(line)
            detail = re.sub(r"^[\s#*.,:;-]+|[\s#*.,:;-]+$", "", line[match.end() : end])
            detail = re.sub(r"\s+and\s*$", "", detail, flags=re.IGNORECASE)
            if detail and detail.casefold() not in {
                "issue",
                "issues",
                "bug",
                "bugs",
                "docs",
                "documentation",
                "feature",
                "features",
                "support",
                "problem",
                "problems",
            }:
                changes.append(detail.casefold())
    dated_versions = []
    for line in release_prose.splitlines():
        publication_matches = list(PUBLICATION_DATE_RE.finditer(line))
        publication_matches.extend(VERSION_DATE_RE.finditer(line))
        for date_match in publication_matches:
            preceding = list(VERSION_RE.finditer(line[: date_match.end()]))
            if preceding:
                dated_versions.append(
                    preceding[-1].group().casefold().removeprefix("v")
                )
            elif len(set(versions)) == 1:
                # A separate date line is unambiguous only when the answer
                # does not mention another release version.
                dated_versions.append(versions[0])
    publication_date = bool(claimed_versions.intersection(dated_versions))
    return {
        "version": bool(claimed_versions)
        and len(cited_tags) == 1
        and claimed_versions == cited_tags,
        "publication_date": publication_date,
        "change_1": len(set(changes)) >= 1,
        "change_2": len(set(changes)) >= 2,
        "official_release_source": bool(versions or publication_date or changes),
    }
