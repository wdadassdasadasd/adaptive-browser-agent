from fastapi.testclient import TestClient

from backend.main import app


def test_app_starts_and_registers_only_requested_research_routes() -> None:
    expected_paths = {
        "/api/research",
        "/api/research/{task_id}",
        "/api/research/{task_id}/events",
        "/api/research/{task_id}/traces",
        "/api/research/{task_id}/cancel",
    }

    with TestClient(app) as client:
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


def test_placeholder_api_contracts_are_truthful() -> None:
    with TestClient(app) as client:
        assert client.get("/api/research").json() == []
        assert (
            client.post("/api/research", json={"goal": "Research"}).status_code == 501
        )
        assert client.get("/api/research/task-1").status_code == 501
        assert client.get("/api/research/task-1/traces").json() == []
        assert client.post("/api/research/task-1/cancel").status_code == 501

        response = client.get("/api/research/task-1/events")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.content == b""
