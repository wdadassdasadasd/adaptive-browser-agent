# Delivery

## Run

```powershell
git submodule update --init --recursive
uv sync --dev
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Copy `.env.example` to `.env` when configuration overrides are needed.
DeepSeek and GitHub credentials are not required for startup because their
external calls remain unimplemented.

## Verified

- Dependency lock is current.
- Tests: 13 passed.
- Ruff check and format check: passed.
- Compileall, package build, database initialization, FastAPI lifespan, and
  live OpenAPI request: passed.
- Upstream browser-use checkout is clean at the expected commit.

## Known limits

Research execution, persistence CRUD, browser action dispatch, DeepSeek/GitHub
calls, prompts, report generation, and benchmark runners are explicit
`TODO(V1)` items. The preserved browser-use baseline smoke script is manual and
requires valid credentials plus a working browser environment.

SQLite migrations are not included in this skeleton. Delete
`data/adaptive_agent.db` after schema changes to rebuild the local development
database on the next startup.
