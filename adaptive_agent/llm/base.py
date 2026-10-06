"""Minimal async LLM protocol used by adaptive services."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class BaseLLMClient(Protocol):
    async def complete(self, prompt: str) -> str:
        """Return one text completion."""

        ...

    async def aclose(self) -> None:
        """Release owned network resources."""

        ...
