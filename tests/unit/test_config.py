import pytest
from pydantic import ValidationError

from backend.config import Settings


def test_recent_trace_count_defaults_to_bounded_v1_window() -> None:
    settings = Settings(_env_file=None)

    assert settings.recent_trace_count == 5

    with pytest.raises(ValidationError):
        Settings(_env_file=None, RECENT_TRACE_COUNT=10)
