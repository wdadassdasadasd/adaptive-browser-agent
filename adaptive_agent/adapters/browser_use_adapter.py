"""The sole primary application boundary around browser-use."""

from collections.abc import Callable
from typing import Any, Literal

from browser_use import BrowserSession
from pydantic import BaseModel, ConfigDict, Field

BrowserActionName = Literal[
    "navigate",
    "click",
    "input_text",
    "scroll",
    "extract",
    "go_back",
    "wait",
]
ObservationLevel = Literal["light", "deep"]


class BrowserAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: BrowserActionName
    target: str | None = None
    element_index: int | None = Field(default=None, ge=0)
    value: str | None = None


class BrowserUseAdapter:
    """Own BrowserSession lifecycle and hide browser-use from upper layers."""

    def __init__(
        self, session_factory: Callable[[], BrowserSession] = BrowserSession
    ) -> None:
        self._session_factory = session_factory
        self._session: BrowserSession | None = None

    async def start_session(self) -> None:
        if self._session is not None:
            return
        session = self._session_factory()
        await session.start()
        self._session = session

    async def observe(self, level: ObservationLevel = "light") -> Any:
        if level not in ("light", "deep"):
            raise ValueError(f"Unsupported observation level: {level}")
        session = self._require_session()
        return await session.get_browser_state_summary(
            include_screenshot=False,
            cached=False,
            include_recent_events=level == "deep",
        )

    async def execute(self, action: BrowserAction) -> dict[str, Any]:
        self._require_session()
        raise NotImplementedError(f"TODO(V1): execute browser action '{action.action}'")

    async def get_session_state(self) -> dict[str, Any]:
        session = self._require_session()
        tabs = await session.get_tabs()
        return {
            "started": True,
            "current_url": await session.get_current_page_url(),
            "tabs": [tab.model_dump(mode="json") for tab in tabs],
        }

    async def close_session(self) -> None:
        session = self._session
        if session is None:
            return
        try:
            await session.kill()
        finally:
            self._session = None

    def _require_session(self) -> BrowserSession:
        if self._session is None:
            raise RuntimeError("Browser session has not been started")
        return self._session
