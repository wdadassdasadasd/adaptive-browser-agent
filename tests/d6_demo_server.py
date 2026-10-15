"""Controlled D6 browser demo only; it never calls DeepSeek or public sites."""

import os
from pathlib import Path

from backend.config import Settings
from backend.main import create_app
from tests.integration.test_agent_loop import (
    FakeBrowser,
    FakeGithub,
    FakeProvider,
    make_loop,
)
from tests.integration.test_research_api import WaitingAgent

database = Path(os.environ["D6_DEMO_DB_PATH"]).resolve()
mode = os.getenv("D6_DEMO_MODE", "mixed")
if mode not in {"mixed", "no_key"}:
    raise ValueError("D6_DEMO_MODE must be mixed or no_key")

settings = Settings(
    _env_file=None,
    DATABASE_URL=f"sqlite+aiosqlite:///{database.as_posix()}",
    DEEPSEEK_API_KEY=None if mode == "no_key" else "D6_FAKE_PROVIDER_ONLY",
)
created = 0


def agent_factory():
    """Complete the first task with fakes; leave later tasks running for UI checks."""

    global created
    created += 1
    if created > 1:
        return WaitingAgent()
    return make_loop(FakeProvider(), FakeGithub(), FakeBrowser())


app = create_app(settings=settings, agent_factory=agent_factory)
