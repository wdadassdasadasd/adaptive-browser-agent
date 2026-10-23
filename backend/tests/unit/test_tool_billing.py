"""Unknown integrations must not inherit the pilot's explicit zero-cost tools."""

import pytest

from adaptive_research.infrastructure.tool_billing import nonbillable_tool_basis


@pytest.mark.parametrize(
    ("operation", "basis"),
    [
        ("browser.start_session", "local_browser_use_session_v1"),
        ("browser.extract", "local_browser_use_session_v1"),
        ("github.search_repositories", "public_github_rest_get_v1"),
        ("github.get_repository", "public_github_rest_get_v1"),
    ],
)
def test_fixed_pilot_tools_have_explicit_basis(operation, basis):
    assert nonbillable_tool_basis("tool", operation) == basis


@pytest.mark.parametrize(
    ("kind", "operation"),
    [
        ("model", "deepseek.chat_completion"),
        ("tool", "mcp.search"),
        ("tool", "browser.cloud_search"),
        ("tool", "github.create_issue"),
        ("browser", "browser.extract"),
    ],
)
def test_unapproved_operations_keep_unknown_cost(kind, operation):
    assert nonbillable_tool_basis(kind, operation) is None
