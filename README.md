# Adaptive Research Agent

Adaptive Research Agent is a research-oriented agent runtime built on top of
[`browser-use`](https://github.com/browser-use/browser-use). The outer project
owns domain state, planning and evaluation boundaries, task runtime,
persistence, API contracts, and benchmark scaffolding. The `browser-use/`
submodule remains browser execution infrastructure.

This repository currently contains the V1 initialization skeleton. The package
layout, domain contracts, SQLite schema, FastAPI routes, task concurrency, and
browser adapter lifecycle are runnable and tested. Research execution, external
DeepSeek and GitHub calls, browser actions, reporting, benchmarks, and the Vue
frontend remain explicit `TODO(V1)` work.

## Requirements

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)
- Git with submodule support

## Setup

Clone with the browser-use submodule:

```powershell
git clone --recurse-submodules <repository-url>
cd adaptive-browser-agent
```

For an existing clone, initialize the submodule before installing dependencies:

```powershell
git submodule update --init --recursive
uv sync --dev
```

Copy `.env.example` to `.env` only when configuration overrides are needed.
DeepSeek and GitHub credentials are not required for application startup while
their integrations remain unimplemented.

## Run the API

```powershell
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API documentation. The six
V1 research routes are registered, but execution endpoints intentionally return
placeholder responses until the Agent Loop and persistence services are wired.

## Verify the skeleton

```powershell
uv lock --check
uv run pytest -q
uv run ruff check adaptive_agent backend benchmark tests
uv run ruff format --check adaptive_agent backend benchmark tests
uv run python -m compileall -q adaptive_agent backend benchmark tests
```

`benchmark/manual_browser_use_smoke.py` is a manual browser-use baseline smoke
script. It performs a real browser and model call and therefore requires the
provider credentials expected by `ChatOpenAI`; it is not part of the automated
test suite.

## Local database resets

V1 intentionally uses SQLAlchemy `metadata.create_all` without Alembic. During
this pre-release phase, schema changes are applied by deleting the local
`data/adaptive_agent.db` file and restarting the API. Do not use that reset for
data that must be retained.

## Project contracts

Product behavior and technical boundaries are defined in
[`docs/specs/V1_SPEC.md`](docs/specs/V1_SPEC.md). Repository-specific working
rules are in [`AGENTS.md`](AGENTS.md).
