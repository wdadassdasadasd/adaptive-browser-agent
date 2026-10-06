"""DeepSeek HTTP client skeleton."""

import httpx


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None,
        model: str = "deepseek-chat",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url="https://api.deepseek.com/v1", timeout=60
        )

    async def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required for DeepSeek requests")
        raise NotImplementedError("TODO(V1): call the DeepSeek chat completions API")

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
