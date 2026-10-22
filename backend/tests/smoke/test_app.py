from fastapi.testclient import TestClient

from adaptive_research.api.main import create_app
from adaptive_research.infrastructure.config import Settings


def _app(tmp_path):
    return create_app(
        Settings(
            _env_file=None,
            DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'smoke.db'}",
            DEEPSEEK_API_KEY=None,
        )
    )


def test_app_starts_and_registers_only_requested_research_routes(tmp_path) -> None:
    expected_paths = {
        "/api/research",
        "/api/research/{task_id}",
        "/api/research/{task_id}/events",
        "/api/research/{task_id}/traces",
        "/api/research/{task_id}/cancel",
    }

    with TestClient(_app(tmp_path)) as client:
        schema = client.get("/openapi.json").json()

    research_paths = {
        path for path in schema["paths"] if path.startswith("/api/research")
    }
    assert research_paths == expected_paths
    assert set(schema["paths"]["/api/research"]) == {"get", "post"}
    assert (
        sum(
            len(methods)
            for path, methods in schema["paths"].items()
            if path.startswith("/api/research")
        )
        == 6
    )


def test_unconfigured_provider_and_unknown_tasks_are_truthful(tmp_path) -> None:
    with TestClient(_app(tmp_path)) as client:
        assert client.get("/api/research").json() == []
        assert (
            client.post("/api/research", json={"goal": "Research"}).status_code == 503
        )
        assert client.get("/api/research/task-1").status_code == 404
        assert client.get("/api/research/task-1/traces").status_code == 404
        assert client.post("/api/research/task-1/cancel").status_code == 404
        assert client.get("/api/research/task-1/events").status_code == 404
