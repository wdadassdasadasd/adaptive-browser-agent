"""Explicit zero-price classification for the pilot's fixed local/read-only tools.

Unknown operations have unknown cost. This allowlist is deliberately narrower
than the ToolRouter vocabulary so a new integration cannot inherit zero cost.
"""

LOCAL_BROWSER_OPERATIONS = frozenset(
    {
        "browser.start_session",
        "browser.observe",
        "browser.navigate",
        "browser.click",
        "browser.input_text",
        "browser.scroll",
        "browser.extract",
        "browser.go_back",
        "browser.wait",
    }
)
PUBLIC_GITHUB_REST_OPERATIONS = frozenset(
    {
        "github.search_repositories",
        "github.get_repository",
        "github.list_releases",
    }
)


def nonbillable_tool_basis(kind: str, operation: str) -> str | None:
    """Return an auditable basis only for the current fixed implementation."""

    if kind != "tool":
        return None
    if operation in LOCAL_BROWSER_OPERATIONS:
        return "local_browser_use_session_v1"
    if operation in PUBLIC_GITHUB_REST_OPERATIONS:
        return "public_github_rest_get_v1"
    return None
