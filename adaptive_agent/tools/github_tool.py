"""GitHub REST API client boundary."""

from typing import Any

import httpx


class GitHubTool:
    def __init__(
        self,
        token: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.token = token
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url="https://api.github.com", timeout=30
        )

    async def execute(
        self, action: str, target: str | None, value: str | None
    ) -> dict[str, Any]:
        raise NotImplementedError("TODO(V1): implement GitHub REST API actions")

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
