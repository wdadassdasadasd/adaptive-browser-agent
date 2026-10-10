import ipaddress
from types import SimpleNamespace
from typing import Any

import pytest
from browser_use import ActionResult
from pydantic import BaseModel, ValidationError

import adaptive_agent.adapters.browser_use_adapter as adapter_module
from adaptive_agent.adapters.browser_use_adapter import BrowserAction, BrowserUseAdapter


class FakeTab(BaseModel):
    target_id: str
    url: str


class FakeBrowserSession:
    def __init__(self) -> None:
        self.started = False
        self.killed = False
        self.observation_options: dict[str, Any] = {}
        self.url = "https://example.com"
        self.navigations: list[str] = []
        self.state: Any = None

    async def start(self) -> None:
        self.started = True

    async def kill(self) -> None:
        self.killed = True

    async def get_browser_state_summary(self, **kwargs: Any) -> Any:
        self.observation_options = kwargs
        return self.state if self.state is not None else {"url": "https://example.com"}

    async def get_tabs(self) -> list[FakeTab]:
        return [FakeTab(target_id="tab-1", url="https://example.com")]

    async def get_current_page_url(self) -> str:
        return self.url

    async def navigate_to(self, url: str) -> None:
        self.navigations.append(url)
        self.url = url

    async def get_element_by_index(self, index: int) -> Any:
        return self.state.dom_state.selector_map.get(index)


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
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()

    result = await adapter.execute(
        BrowserAction(action="navigate", target="https://example.com/research")
    )
    assert result["success"] is True
    assert result["url"] == "https://example.com/research"
    assert session.navigations == ["https://example.com/research"]

    blocked = await adapter.execute(
        BrowserAction(action="navigate", target="http://127.0.0.1/private")
    )
    assert blocked["success"] is False
    assert blocked["error_type"] == "semantic"
    assert session.navigations == ["https://example.com/research"]

    await adapter.close_session()


@pytest.mark.asyncio
async def test_adapter_cleans_up_failed_start() -> None:
    class FailedSession(FakeBrowserSession):
        async def start(self) -> None:
            raise RuntimeError("launch failed")

    session = FailedSession()
    adapter = BrowserUseAdapter(session_factory=lambda: session)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="launch failed"):
        await adapter.start_session()

    assert session.killed is True
    with pytest.raises(RuntimeError, match="has not been started"):
        await adapter.get_session_state()


@pytest.mark.asyncio
async def test_adapter_rejects_invalid_action_parameters() -> None:
    with pytest.raises(ValidationError):
        BrowserAction(action="navigate")
    with pytest.raises(ValidationError):
        BrowserAction(action="click", element_index=0)
    with pytest.raises(ValidationError):
        BrowserAction(action="input_text", element_index=1)
    with pytest.raises(ValidationError):
        BrowserAction(action="click", target="   ")
    with pytest.raises(ValidationError):
        BrowserAction(action="wait", value="11")
    with pytest.raises(ValidationError):
        BrowserAction(action="wait", value="NaN")


@pytest.mark.asyncio
async def test_adapter_dispatches_remaining_actions_and_semantic_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Any]] = []

    class FakeTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            calls.append(("click", index))
            return ActionResult(extracted_content="Clicked")

        async def input(
            self, *, index: int, text: str, browser_session: Any
        ) -> ActionResult:
            calls.append(("input", (index, text)))
            return ActionResult(extracted_content="Typed")

        async def scroll(self, **kwargs: Any) -> ActionResult:
            calls.append(("scroll", kwargs["down"]))
            return ActionResult(extracted_content="Scrolled")

        async def go_back(self, *, browser_session: Any) -> ActionResult:
            calls.append(("go_back", None))
            return ActionResult(extracted_content="Back")

    async def fake_extract(*, browser_session: Any) -> tuple[str, dict[str, Any]]:
        return "# Evidence", {}

    monkeypatch.setattr(adapter_module, "extract_clean_markdown", fake_extract)
    node = SimpleNamespace(
        backend_node_id=42,
        ax_node=SimpleNamespace(name="Search"),
        attributes={},
        get_all_children_text=lambda max_depth: "Search",
    )
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        title="Example",
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        assert (await adapter.execute(BrowserAction(action="click", element_index=1)))[
            "success"
        ]
        assert (
            await adapter.execute(
                BrowserAction(action="input_text", target="Search", value="query")
            )
        )["success"]
        assert (await adapter.execute(BrowserAction(action="scroll", target="up")))[
            "success"
        ]
        assert (await adapter.execute(BrowserAction(action="go_back")))["success"]
        assert (await adapter.execute(BrowserAction(action="wait", value="0")))[
            "success"
        ]
        extracted = await adapter.execute(BrowserAction(action="extract"))
        assert extracted["content"] == "# Evidence"
    finally:
        await adapter.close_session()

    assert calls[:4] == [
        ("click", 1),
        ("input", (1, "query")),
        ("scroll", False),
        ("go_back", None),
    ]


@pytest.mark.asyncio
async def test_adapter_rejects_stale_index_without_clicking() -> None:
    calls: list[int] = []

    class FakeTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            calls.append(index)
            return ActionResult(extracted_content="Clicked")

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        session.url = "https://example.com/changed"
        result = await adapter.execute(BrowserAction(action="click", element_index=1))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert calls == []


@pytest.mark.asyncio
async def test_adapter_rejects_reused_node_id_from_new_document() -> None:
    clicks: list[int] = []

    class FakeTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            clicks.append(index)
            return ActionResult(extracted_content="Clicked")

    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(
            selector_map={1: SimpleNamespace(session_id="old", backend_node_id=42)}
        ),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        session.state.dom_state.selector_map[1] = SimpleNamespace(
            session_id="new", backend_node_id=42
        )
        result = await adapter.execute(BrowserAction(action="click", element_index=1))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert clicks == []


@pytest.mark.asyncio
@pytest.mark.parametrize("action_name", ["click", "input_text"])
async def test_adapter_classifies_upstream_disappeared_element_as_semantic(
    action_name: str,
) -> None:
    class DisappearingTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            return ActionResult(
                extracted_content=(
                    f"Element index {index} not available - page may have changed. "
                    "Try refreshing browser state."
                )
            )

        async def input(
            self, *, index: int, text: str, browser_session: Any
        ) -> ActionResult:
            return await self.click(index=index, browser_session=browser_session)

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=DisappearingTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        action = BrowserAction(action=action_name, element_index=1, value="query")
        result = await adapter.execute(action)
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"


@pytest.mark.asyncio
async def test_adapter_rejects_stale_scroll_element_without_scrolling() -> None:
    calls: list[int] = []

    class FakeTools:
        async def scroll(self, **kwargs: Any) -> ActionResult:
            calls.append(kwargs["index"])
            return ActionResult(extracted_content="Scrolled")

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        session.url = "https://example.com/changed"
        result = await adapter.execute(BrowserAction(action="scroll", element_index=1))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("intervening_action", ["scroll", "wait"])
async def test_adapter_requires_fresh_observation_after_page_may_change(
    intervening_action: str,
) -> None:
    clicks: list[int] = []

    class FakeTools:
        async def scroll(self, **kwargs: Any) -> ActionResult:
            return ActionResult(extracted_content="Scrolled")

        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            clicks.append(index)
            return ActionResult(extracted_content="Clicked")

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        action = BrowserAction(action=intervening_action, value="0")
        assert (await adapter.execute(action))["success"] is True
        result = await adapter.execute(BrowserAction(action="click", element_index=1))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert clicks == []


@pytest.mark.asyncio
async def test_failed_navigation_action_invalidates_observed_indices() -> None:
    clicks: list[int] = []

    class FakeTools:
        async def go_back(self, *, browser_session: Any) -> ActionResult:
            raise RuntimeError("back navigation failed after page change")

        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            clicks.append(index)
            return ActionResult(extracted_content="Clicked")

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        failed = await adapter.execute(BrowserAction(action="go_back"))
        result = await adapter.execute(BrowserAction(action="click", element_index=1))
    finally:
        await adapter.close_session()

    assert failed["success"] is False
    assert failed["error_type"] == "technical"
    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert clicks == []


@pytest.mark.asyncio
async def test_adapter_rejects_private_final_url_after_redirect() -> None:
    class RedirectingSession(FakeBrowserSession):
        async def navigate_to(self, url: str) -> None:
            self.navigations.append(url)
            self.url = "http://127.0.0.1/private"

    session = RedirectingSession()
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()
    try:
        result = await adapter.execute(
            BrowserAction(action="navigate", target="https://example.com/redirect")
        )
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert result["url"] is None
    assert session.navigations == ["https://example.com/redirect"]
    assert session.killed is True


@pytest.mark.asyncio
async def test_adapter_classifies_browser_error_page_as_navigation_failure() -> None:
    class ErrorPageSession(FakeBrowserSession):
        async def navigate_to(self, url: str) -> None:
            self.navigations.append(url)
            self.url = "chrome-error://chromewebdata/"

    session = ErrorPageSession()
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()
    try:
        result = await adapter.execute(
            BrowserAction(action="navigate", target="https://example.com/unavailable")
        )
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "technical"


@pytest.mark.asyncio
async def test_adapter_does_not_interact_with_unsafe_current_page() -> None:
    clicks: list[int] = []

    class FakeTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            clicks.append(index)
            return ActionResult(extracted_content="Clicked")

    node = SimpleNamespace(backend_node_id=42)
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url=session.url,
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
    )
    await adapter.start_session()
    try:
        await adapter.observe()
        session.url = "http://127.0.0.1/private"
        result = await adapter.execute(BrowserAction(action="click", element_index=1))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert clicks == []


@pytest.mark.asyncio
async def test_adapter_does_not_observe_unsafe_current_page() -> None:
    class UnsafeSession(FakeBrowserSession):
        def __init__(self) -> None:
            super().__init__()
            self.url = "http://127.0.0.1/private"
            self.observation_count = 0

        async def get_browser_state_summary(self, **kwargs: Any) -> Any:
            self.observation_count += 1
            return await super().get_browser_state_summary(**kwargs)

    session = UnsafeSession()
    adapter = BrowserUseAdapter(session_factory=lambda: session)  # type: ignore[arg-type]
    await adapter.start_session()
    try:
        with pytest.raises(ValueError, match="Unsafe network target"):
            await adapter.observe()
    finally:
        await adapter.close_session()

    assert session.observation_count == 0


@pytest.mark.asyncio
async def test_adapter_rejects_unsafe_url_reached_during_observation() -> None:
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url="http://127.0.0.1/private",
        dom_state=SimpleNamespace(selector_map={}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()
    try:
        with pytest.raises(ValueError, match="Unsafe network target"):
            await adapter.observe()
    finally:
        await adapter.close_session()


@pytest.mark.asyncio
async def test_adapter_does_not_resolve_target_on_unsafe_page() -> None:
    clicks: list[int] = []

    class FakeTools:
        async def click(self, *, index: int, browser_session: Any) -> ActionResult:
            clicks.append(index)
            return ActionResult(extracted_content="Clicked")

    node = SimpleNamespace(
        backend_node_id=42,
        ax_node=SimpleNamespace(name="Search"),
        attributes={},
        get_all_children_text=lambda max_depth: "Search",
    )
    session = FakeBrowserSession()
    session.state = SimpleNamespace(
        url="http://127.0.0.1/private",
        dom_state=SimpleNamespace(selector_map={1: node}),
    )
    adapter = BrowserUseAdapter(
        session_factory=lambda: session,  # type: ignore[arg-type]
        tools_factory=FakeTools,  # type: ignore[arg-type]
        address_resolver=lambda host: {ipaddress.ip_address("93.184.216.34")},
    )
    await adapter.start_session()
    try:
        result = await adapter.execute(BrowserAction(action="click", target="Search"))
    finally:
        await adapter.close_session()

    assert result["success"] is False
    assert result["error_type"] == "semantic"
    assert clicks == []
