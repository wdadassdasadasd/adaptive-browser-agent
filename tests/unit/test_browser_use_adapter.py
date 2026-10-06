from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from adaptive_agent.adapters.browser_use_adapter import BrowserAction, BrowserUseAdapter


class FakeTab(BaseModel):
    target_id: str
    url: str


class FakeBrowserSession:
    def __init__(self) -> None:
        self.started = False
        self.killed = False
        self.observation_options: dict[str, Any] = {}

    async def start(self) -> None:
        self.started = True

    async def kill(self) -> None:
        self.killed = True

    async def get_browser_state_summary(self, **kwargs: Any) -> dict[str, str]:
        self.observation_options = kwargs
        return {"url": "https://example.com"}

    async def get_tabs(self) -> list[FakeTab]:
        return [FakeTab(target_id="tab-1", url="https://example.com")]

    async def get_current_page_url(self) -> str:
        return "https://example.com"


@pytest.mark.asyncio
async def test_adapter_owns_lifecycle_and_disables_screenshots() -> None:
    session = FakeBrowserSession()
    adapter = BrowserUseAdapter(session_factory=lambda: session)  # type: ignore[arg-type]

    await adapter.start_session()
    observation = await adapter.observe("deep")
    state = await adapter.get_session_state()
    await adapter.close_session()

    assert observation == {"url": "https://example.com"}
    assert session.observation_options == {
        "include_screenshot": False,
        "cached": False,
        "include_recent_events": True,
    }
    assert state["current_url"] == "https://example.com"
    assert session.killed is True


@pytest.mark.asyncio
async def test_adapter_validates_action_names_before_execution() -> None:
    with pytest.raises(ValidationError):
        BrowserAction(action="screenshot")

    with pytest.raises(ValueError, match="Unsupported observation level"):
        await BrowserUseAdapter(session_factory=FakeBrowserSession).observe("full")  # type: ignore[arg-type]

    session = FakeBrowserSession()
    adapter = BrowserUseAdapter(session_factory=lambda: session)  # type: ignore[arg-type]
    await adapter.start_session()

    with pytest.raises(NotImplementedError, match=r"TODO\(V1\)"):
        await adapter.execute(
            BrowserAction(action="navigate", target="https://example.com")
        )

    await adapter.close_session()
