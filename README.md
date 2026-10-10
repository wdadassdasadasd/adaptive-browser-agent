# Adaptive Research Agent

Adaptive Research Agent is a research-oriented agent runtime built on top of
[`browser-use`](https://github.com/browser-use/browser-use). The outer project
owns domain state, planning and evaluation boundaries, task runtime,
persistence, API contracts, and benchmark scaffolding. The `browser-use/`
submodule remains browser execution infrastructure.

This repository is building V1 from an initialization skeleton. Domain models,
SQLite tables, FastAPI route registration, and basic task concurrency have
offline tests. The BrowserUseAdapter now implements its declared action
boundary; a separate opt-in Chromium smoke test exercises startup, navigation,
observation, extraction, and closure. The AgentLoop, DeepSeek/GitHub calls,
persistence service, working API responses/SSE, reporting, benchmark runners,
and Vue frontend remain V1 work. A green skeleton suite is not V1 acceptance.

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
An empty `DEEPSEEK_API_KEY` is treated as missing. The current placeholder API
starts without credentials; once research execution is wired, creating a task
requires a DeepSeek key and returns 503 without one. `GITHUB_TOKEN` remains
optional for public repository research. Keep `.env` private and never put
credential values in issue reports, traces, SSE events, or benchmark records.

## Run the API

```powershell
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API documentation. The six
V1 research routes are registered, but execution endpoints intentionally return
placeholder responses until the Agent Loop and persistence services are wired.

## Verify the current code

```powershell
uv lock --check --offline
uv run --offline --locked pytest -q
uv run --offline --locked ruff check adaptive_agent backend benchmark tests
uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests
uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests
```

`pytest -q` excludes the real-browser test. To opt in to a local Chromium
smoke using a controlled loopback HTTP page (no API key required):

```powershell
uv run pytest -q -m browser tests/smoke/test_browser_use_adapter.py
```

The smoke enables loopback URLs only in its test adapter instance; the normal
adapter rejects local/private targets, checks the current page before further
observation or interaction, and rejects an unsafe final URL after navigation.
A redirect may reach that destination before the final check, so this is a
trusted localhost demonstration, not a public network-isolated service.
Browser startup depends on an installed Chromium-compatible browser.
The local CI workflow defines offline Python jobs for 3.12 and 3.13; remote
GitHub Actions execution is not yet verified. The Vue build and type-check
gate remains unverified until the frontend package exists and the D6 job is
added. Offline tests, browser smoke, live research, and benchmark runs are
separate evidence levels.

`benchmark/manual_browser_use_smoke.py` is a manual browser-use baseline smoke
script. It performs a real browser and model call and therefore requires the
provider credentials expected by `ChatOpenAI`; it is not part of the automated
test suite or the same-model V1 benchmark.

## Local database preservation

V1 startup uses SQLAlchemy `metadata.create_all` without Alembic. It creates
missing tables and does not automatically clear or delete the local
`data/adaptive_agent.db` file. `create_all` does not migrate existing columns.
If a future schema change is incompatible, stop the app, back up the database,
and plan an explicit data-preserving migration or a deliberate disposable-data
reset. Do not delete an existing database as a routine startup step.

## Project contracts

Product behavior and technical boundaries are defined in
[`docs/specs/V1_SPEC.md`](docs/specs/V1_SPEC.md). Repository-specific working
rules are in [`AGENTS.md`](AGENTS.md). The readiness audit, target contracts,
seven-day task ledger, test matrix, and benchmark protocol are respectively in
`docs/audits/V1_READINESS_AUDIT.md`, `docs/contracts/V1_CONTRACTS.md`,
`docs/tasks/V1_TASKS.md`, `docs/testing/V1_TEST_MATRIX.md`, and
`docs/benchmark/BENCHMARK_PROTOCOL.md`.
