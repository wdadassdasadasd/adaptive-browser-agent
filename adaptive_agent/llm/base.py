"""Typed completion and usage boundary shared by adaptive services."""

from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
LLMFailureKind = Literal[
    "configuration", "technical", "rejected", "invalid_response", "structured", "budget"
]


@dataclass(frozen=True)
class LLMCompletion:
    text: str
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class StructuredCompletion[T: BaseModel]:
    value: T
    prompt_tokens: int
    completion_tokens: int


class LLMError(RuntimeError):
    """Safe provider failure with usage from responses already received."""

    def __init__(
        self,
        message: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        *,
        kind: LLMFailureKind,
    ) -> None:
        super().__init__(message)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.kind = kind


class StructuredOutputError(LLMError):
    """The initial and repair responses both failed schema validation."""


@runtime_checkable
class BaseLLMClient(Protocol):
    async def complete(self, prompt: str) -> LLMCompletion:
        """Return text and provider-reported usage."""

        ...

    async def complete_structured(
        self, prompt: str, schema: type[T]
    ) -> StructuredCompletion[T]:
        """Return one validated value and all known usage, including repair."""

        ...

    async def aclose(self) -> None:
        """Release owned network resources."""

        ...
