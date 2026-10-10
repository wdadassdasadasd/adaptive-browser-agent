"""The sole primary application boundary around browser-use."""

import asyncio
import ipaddress
import logging
import socket
from collections.abc import Callable
from typing import Any, Literal
from urllib.parse import urlsplit

from browser_use import ActionResult, BrowserSession, Tools
from browser_use.dom.markdown_extractor import extract_clean_markdown
from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)

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

    @model_validator(mode="after")
    def validate_parameters(self) -> "BrowserAction":
        if self.action == "navigate" and not self.target:
            raise ValueError("navigate requires target URL")
        if self.action in {"click", "input_text"}:
            if self.element_index is None and not (self.target and self.target.strip()):
                raise ValueError(f"{self.action} requires an index or target")
            if self.element_index == 0:
                raise ValueError("interactive element index must be positive")
        if self.action == "input_text" and self.value is None:
            raise ValueError("input_text requires value")
        if self.action == "scroll" and self.target not in {None, "up", "down"}:
            raise ValueError("scroll target must be up or down")
        if self.action == "wait":
            seconds = float(self.value) if self.value is not None else 1.0
            if not 0 <= seconds <= 10:
                raise ValueError("wait seconds must be between 0 and 10")
        return self


class BrowserResult(BaseModel):
    """A bounded, serializable result with no upstream runtime objects."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    action: BrowserActionName
    url: str | None = None
    content: str = Field(default="", max_length=12000)
    error_type: Literal["none", "technical", "semantic", "insufficient_info"] = "none"
    error_message: str | None = None


def _resolve_addresses(host: str) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    return {
        ipaddress.ip_address(result[4][0])
        for result in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    }


class BrowserUseAdapter:
    """Own BrowserSession lifecycle and hide browser-use from upper layers."""

    def __init__(
        self,
        session_factory: Callable[[], BrowserSession] = BrowserSession,
        tools_factory: Callable[[], Tools] = Tools,
        address_resolver: Callable[
            [str], set[ipaddress.IPv4Address | ipaddress.IPv6Address]
        ] = _resolve_addresses,
        allow_loopback_for_smoke: bool = False,
    ) -> None:
        self._session_factory = session_factory
        self._tools_factory = tools_factory
        self._address_resolver = address_resolver
        self._allow_loopback_for_smoke = allow_loopback_for_smoke
        self._session: BrowserSession | None = None
        self._tools: Tools | None = None
        self._observed_url: str | None = None
        self._observed_element_ids: dict[int, tuple[str, int]] = {}

    async def start_session(self) -> None:
        if self._session is not None:
            return
        session = self._session_factory()
        try:
            await session.start()
        except BaseException:
            try:
                await session.kill()
            except Exception as exc:  # noqa: BLE001 - preserve startup failure
                logger.warning(
                    "Browser cleanup after start failed: %s", type(exc).__name__
                )
            raise
        self._session = session

    async def observe(self, level: ObservationLevel = "light") -> Any:
        if level not in ("light", "deep"):
            raise ValueError(f"Unsupported observation level: {level}")
        session = self._require_session()
        current_url = await session.get_current_page_url()
        if current_url != "about:blank":
            await self._validate_url(current_url)
        state = await session.get_browser_state_summary(
            include_screenshot=False,
            cached=False,
            include_recent_events=level == "deep",
        )
        state_url = getattr(state, "url", None)
        if state_url and state_url != "about:blank":
            await self._validate_url(state_url)
        # The upstream target title can lag behind a loaded DOM. Read the live
        # document title when a Page actor is available.
        if hasattr(state, "title") and hasattr(session, "get_current_page"):
            try:
                page = await session.get_current_page()
                if page is not None:
                    live_title = await page.evaluate("() => document.title")
                    if live_title:
                        state.title = live_title
            except Exception as exc:  # noqa: BLE001 - title is optional data
                logger.debug("Live browser title unavailable: %s", type(exc).__name__)
        self._observed_url = getattr(state, "url", None)
        dom_state = getattr(state, "dom_state", None)
        selector_map = getattr(dom_state, "selector_map", {})
        self._observed_element_ids = {
            index: self._node_identity(node) for index, node in selector_map.items()
        }
        return state

    async def execute(self, action: BrowserAction) -> dict[str, Any]:
        session = self._require_session()
        try:
            if action.action != "navigate":
                current_url = await session.get_current_page_url()
                if current_url != "about:blank":
                    await self._validate_url(current_url)
            content = await self._execute_action(session, action)
            if action.action == "extract" and not content.strip():
                return BrowserResult(
                    success=False,
                    action=action.action,
                    error_type="insufficient_info",
                    error_message="Page extraction returned no text",
                ).model_dump()
            url = await session.get_current_page_url()
            if action.action == "navigate" and (
                url == "about:blank" or url.startswith("chrome-error://")
            ):
                raise RuntimeError("Navigation did not reach a page")
            if url != "about:blank":
                await self._validate_url(url)
            return BrowserResult(
                success=True,
                action=action.action,
                url=url,
                content=content[:12000],
            ).model_dump()
        except asyncio.CancelledError:
            raise
        except ValueError:
            return BrowserResult(
                success=False,
                action=action.action,
                error_type="semantic",
                error_message="Invalid or unsafe browser action target",
            ).model_dump()
        except Exception as exc:  # noqa: BLE001 - normalize upstream browser failures
            return BrowserResult(
                success=False,
                action=action.action,
                error_type="technical",
                error_message=f"Browser action failed ({type(exc).__name__})",
            ).model_dump()

    async def _execute_action(
        self, session: BrowserSession, action: BrowserAction
    ) -> str:
        if action.action == "navigate":
            assert action.target is not None
            await self._validate_url(action.target)
            self._invalidate_observation()
            await session.navigate_to(action.target)
            return "Navigated"
        if action.action == "extract":
            content, _ = await extract_clean_markdown(browser_session=session)
            return content
        if action.action == "wait":
            self._invalidate_observation()
            await asyncio.sleep(float(action.value) if action.value is not None else 1)
            return "Waited"

        tools = self._tools or self._tools_factory()
        self._tools = tools
        if action.action in {"click", "input_text"}:
            index = await self._resolve_element_index(session, action)
            self._invalidate_observation()
            if action.action == "click":
                result = await tools.click(index=index, browser_session=session)
            else:
                result = await tools.input(
                    index=index, text=action.value, browser_session=session
                )
            if (result.extracted_content or "").startswith(
                f"Element index {index} not available - page may have changed."
            ):
                raise ValueError("Element disappeared during interaction")
        elif action.action == "scroll":
            if action.element_index not in {None, 0}:
                await self._resolve_element_index(session, action)
            self._invalidate_observation()
            result = await tools.scroll(
                down=action.target != "up",
                pages=1.0,
                index=action.element_index,
                browser_session=session,
            )
        elif action.action == "go_back":
            self._invalidate_observation()
            result = await tools.go_back(browser_session=session)
        else:
            raise ValueError("Unsupported browser action")
        return self._unwrap_result(result)

    @staticmethod
    def _unwrap_result(result: ActionResult) -> str:
        if result.error or result.success is False:
            raise RuntimeError("Upstream browser action failed")
        return result.extracted_content or "Action completed"

    @staticmethod
    def _node_identity(node: Any) -> tuple[str, int]:
        return str(getattr(node, "session_id", None)), node.backend_node_id

    def _invalidate_observation(self) -> None:
        self._observed_url = None
        self._observed_element_ids.clear()

    async def _resolve_element_index(
        self, session: BrowserSession, action: BrowserAction
    ) -> int:
        current_url = await session.get_current_page_url()
        if action.element_index is not None:
            index = action.element_index
            node = await session.get_element_by_index(index)
            if (
                current_url != self._observed_url
                or node is None
                or self._observed_element_ids.get(index) != self._node_identity(node)
            ):
                raise ValueError("Element index is stale or unavailable")
            return index
        state = await session.get_browser_state_summary(
            include_screenshot=False, cached=False
        )
        await self._validate_url(state.url)
        target = action.target or ""
        selector_map = state.dom_state.selector_map
        names = {
            index: [
                node.ax_node.name if node.ax_node else "",
                node.attributes.get("aria-label", ""),
                node.attributes.get("title", ""),
                node.attributes.get("placeholder", ""),
                node.get_all_children_text(max_depth=2),
            ]
            for index, node in selector_map.items()
            if index > 0
        }
        folded = target.casefold()
        normalized = " ".join(folded.split())
        for predicate in (
            lambda text: text.casefold() == folded,
            lambda text: folded in text.casefold(),
            lambda text: normalized in " ".join(text.casefold().split()),
        ):
            matches = [
                index
                for index, candidates in names.items()
                if any(text and predicate(text) for text in candidates)
            ]
            if len(matches) == 1:
                self._observed_url = state.url
                self._observed_element_ids = {
                    key: self._node_identity(node) for key, node in selector_map.items()
                }
                return matches[0]
            if len(matches) > 1:
                raise ValueError("Semantic element target is ambiguous")
        raise ValueError("Semantic element target was not found")

    async def _validate_url(self, url: str) -> None:
        parsed = urlsplit(url)
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("Unsafe URL")
        try:
            addresses = {ipaddress.ip_address(parsed.hostname)}
        except ValueError:
            addresses = await asyncio.to_thread(self._address_resolver, parsed.hostname)
        if not addresses or any(
            not (
                address.is_global
                or (self._allow_loopback_for_smoke and address.is_loopback)
            )
            for address in addresses
        ):
            raise ValueError("Unsafe network target")

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
            self._tools = None
            self._observed_url = None
            self._observed_element_ids.clear()

    def _require_session(self) -> BrowserSession:
        if self._session is None:
            raise RuntimeError("Browser session has not been started")
        return self._session
