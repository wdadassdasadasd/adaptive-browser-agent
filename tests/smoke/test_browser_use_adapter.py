"""Opt-in real Chromium smoke; excluded from offline CI."""

import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from browser_use import BrowserSession

from adaptive_agent.adapters.browser_use_adapter import BrowserAction, BrowserUseAdapter


class SmokePage(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = b"<html><title>Adaptive Smoke</title><body><h1>Research evidence</h1></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.mark.browser
@pytest.mark.asyncio
async def test_real_browser_start_navigate_observe_extract_close() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), SmokePage)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    adapter = BrowserUseAdapter(
        session_factory=lambda: BrowserSession(headless=True),
        allow_loopback_for_smoke=True,
    )
    try:
        await asyncio.wait_for(adapter.start_session(), timeout=60)
        navigation = await asyncio.wait_for(
            adapter.execute(
                BrowserAction(action="navigate", target=f"http://127.0.0.1:{port}/")
            ),
            timeout=45,
        )
        assert navigation["success"] is True, navigation

        observation = await asyncio.wait_for(adapter.observe("light"), timeout=45)
        assert observation.url.startswith(f"http://127.0.0.1:{port}/")
        assert observation.title == "Adaptive Smoke", (
            observation.dom_state.llm_representation()[:500],
            observation.browser_errors,
        )
        assert observation.screenshot is None

        extraction = await asyncio.wait_for(
            adapter.execute(BrowserAction(action="extract", target="page heading")),
            timeout=45,
        )
        assert extraction["success"] is True, extraction
        assert "Research evidence" in extraction["content"]

        rejected = await adapter.execute(
            BrowserAction(action="navigate", target="file:///etc/passwd")
        )
        assert rejected["success"] is False
        assert rejected["error_type"] == "semantic"
    finally:
        await asyncio.wait_for(adapter.close_session(), timeout=30)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert adapter._session is None
