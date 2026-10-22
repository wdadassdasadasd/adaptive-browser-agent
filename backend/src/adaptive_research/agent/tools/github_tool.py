"""Small fixed-host GitHub REST client for public repository research."""

import json
import re
from typing import Any

import httpx

from adaptive_research.agent.state import ToolResult

_REPOSITORY = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+\Z")
_BASE = "https://api.github.com"


class GitHubTool:
    def __init__(
        self, token: str | None = None, client: httpx.AsyncClient | None = None
    ) -> None:
        self.token = token
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(timeout=30, follow_redirects=False)

    async def execute(
        self, action: str, target: str | None, value: str | None
    ) -> ToolResult:
        """Call one of three read-only endpoints once and normalize the outcome."""

        if action == "search_repositories":
            if not target or not target.strip():
                return self._error(action, "semantic", "Search query is required")
            url, params = (
                f"{_BASE}/search/repositories",
                {"q": target.strip(), "per_page": 5},
            )
        elif action in {"get_repository", "list_releases"}:
            resource_url = self.resource_url(action, target)
            if resource_url is None:
                return self._error(action, "semantic", "Repository must be owner/repo")
            url, params = resource_url, None
        else:
            return self._error(action, "semantic", "Unsupported GitHub action")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "adaptive-research-agent",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = await self.client.get(
                url, params=params, headers=headers, follow_redirects=False
            )
        except httpx.RequestError:
            return self._error(action, "technical", "GitHub request failed")
        source_url = str(response.request.url)
        if response.status_code == 404:
            return self._error(
                action, "insufficient_info", "GitHub resource not found", source_url
            )
        if (
            response.status_code == 429
            or response.status_code >= 500
            or response.status_code in {401, 403}
        ):
            return self._error(
                action, "technical", f"GitHub HTTP {response.status_code}", source_url
            )
        if response.status_code >= 300:
            return self._error(
                action,
                "semantic" if response.status_code < 500 else "technical",
                f"GitHub HTTP {response.status_code}",
                source_url,
            )
        try:
            data = response.json()
            selected = self._select(action, data)
        except (ValueError, TypeError, KeyError, AttributeError):
            return self._error(
                action, "technical", "Invalid GitHub response", source_url
            )
        content = json.dumps(selected, ensure_ascii=False, separators=(",", ":"))
        metadata = {"status_code": response.status_code}
        if len(content) > 12000:
            for limit in (1000, 500, 250, 100):
                bounded = self._clip_strings(selected, limit)
                content = json.dumps(bounded, ensure_ascii=False, separators=(",", ":"))
                if len(content) <= 12000:
                    metadata["truncated"] = True
                    break
            else:
                return self._error(
                    action,
                    "technical",
                    "GitHub response exceeded content limit",
                    source_url,
                )
        return ToolResult(
            tool="github",
            action=action,
            success=True,
            content=content,
            source_url=source_url,
            metadata=metadata,
        )

    @staticmethod
    def resource_url(action: str, target: str | None) -> str | None:
        """Return the fixed endpoint URL for a valid repository resource."""

        if (
            action not in {"get_repository", "list_releases"}
            or not target
            or not _REPOSITORY.fullmatch(target)
            or target.split("/")[1] in {".", ".."}
        ):
            return None
        suffix = "/releases?per_page=5" if action == "list_releases" else ""
        return f"{_BASE}/repos/{target}{suffix}"

    @staticmethod
    def _clip_strings(value: Any, limit: int) -> Any:
        if isinstance(value, str):
            return value[:limit] + "…" if len(value) > limit else value
        if isinstance(value, list):
            return [GitHubTool._clip_strings(item, limit) for item in value]
        if isinstance(value, dict):
            return {
                key: GitHubTool._clip_strings(item, limit)
                for key, item in value.items()
            }
        return value

    @staticmethod
    def _select(action: str, data: Any) -> Any:
        if action == "search_repositories":
            return {
                "total_count": data["total_count"],
                "items": [
                    {
                        key: item.get(key)
                        for key in (
                            "full_name",
                            "html_url",
                            "description",
                            "stargazers_count",
                        )
                    }
                    for item in data["items"][:5]
                ],
            }
        if action == "get_repository":
            return {
                key: data.get(key)
                for key in (
                    "full_name",
                    "html_url",
                    "description",
                    "stargazers_count",
                    "language",
                    "license",
                    "updated_at",
                    "default_branch",
                )
            }
        return [
            {
                key: item.get(key)
                for key in (
                    "tag_name",
                    "name",
                    "html_url",
                    "published_at",
                    "body",
                    "prerelease",
                )
            }
            for item in data[:5]
        ]

    @staticmethod
    def _error(
        action: str, kind: str, message: str, source_url: str | None = None
    ) -> ToolResult:
        return ToolResult(
            tool="github",
            action=action,
            success=False,
            content="",
            source_url=source_url,
            error_type=kind,
            error_message=message,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
