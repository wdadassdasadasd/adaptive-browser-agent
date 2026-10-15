# Adaptive Research Agent

Adaptive Research Agent is a research-oriented agent runtime built on top of
[`browser-use`](https://github.com/browser-use/browser-use). The outer project
owns research state, planning, evaluation, task runtime, persistence, the
FastAPI contract, Vue frontend, and benchmark harness. The `browser-use/`
submodule remains browser execution infrastructure. Local checks and a
controlled fake-provider demonstration do not replace D7's public research
acceptance runs or 18 real benchmark runs.

## Requirements

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)
- Git with submodule support
- Node.js 22 and npm for the frontend

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
An empty `DEEPSEEK_API_KEY` is treated as missing: the API can start and list
tasks, but creating a task returns 503 until the server has a DeepSeek key.
`GITHUB_TOKEN` is optional for public repository research. Keep credentials
server-side and never put their values in browser settings, issue reports,
traces, SSE events, or benchmark records.

## Run locally with an isolated database

Choose a new disposable SQLite path for local checks so an existing
`data/adaptive_agent.db` is not changed. In PowerShell, from the repository
root:

```powershell
$env:DATABASE_URL = "sqlite+aiosqlite:///./data/local-demo.db"
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Its `/api`
requests are proxied to the local API; the browser does not need a provider
key. Open `http://127.0.0.1:8000/docs` to inspect the fixed six research
routes. With a real server-side DeepSeek key, enter a goal, select Start, watch
the status and timeline, then open a sourced report or cancel a running task.
Refresh to reload recent tasks and persisted history. A controlled fake-provider
path can verify the local UI and runtime without claiming live research success;
the repository includes an acceptance-only server for that path:

```powershell
New-Item -ItemType Directory -Force .pytest_cache/d6-demo | Out-Null
$env:D6_DEMO_DB_PATH = Join-Path (Get-Location).Path '.pytest_cache/d6-demo/demo.db'
uv run uvicorn tests.d6_demo_server:app --host 127.0.0.1 --port 8000
```

Use a fresh path when repeating the demo. With the Vite command above running,
the first task completes using fake provider/browser/GitHub results; later tasks
wait so you can test Cancel and SSE interruption. To check restart recovery,
stop the API with a waiting task open, set `$env:D6_DEMO_MODE = 'no_key'`, and
restart the same command with the same database path. The old task becomes
`failed/server_restart`; a new submission returns 503. This demo never calls
DeepSeek or public sites. The observed D6 results are in the acceptance record.

## Verify the code

```powershell
uv lock --check --offline
uv run --offline --locked pytest -q
uv run --offline --locked ruff check adaptive_agent backend benchmark tests
uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests
uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests
npm ci --prefix frontend
npm run type-check --prefix frontend
npm run build --prefix frontend
npm run test --prefix frontend
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
The CI workflow has offline Python jobs for 3.12 and 3.13 plus a locked
frontend install, type check, test and build job. A local green run is not evidence
that remote GitHub Actions executed. Offline tests, controlled browser smoke,
fake-backed UI checks, live research, and protocol benchmark runs are separate
evidence levels.

## Benchmark

Read [`docs/benchmark/BENCHMARK_PROTOCOL.md`](docs/benchmark/BENCHMARK_PROTOCOL.md)
before collecting live results. The runner's default invocation prints the
fixed B01–B03, three-arm, two-repetition plan without making provider calls:

```powershell
uv run --offline --locked python -m benchmark.runner
```

With a server-side `DEEPSEEK_API_KEY`, installed Chromium, and network access,
explicitly run the 18-attempt protocol:

```powershell
uv run --locked python -m benchmark.runner --live
```

Each attempt is retained as a redacted JSON file under
`data/benchmark/<run-id>/`, including failures, with a `summary.json` for
separate baseline versus full-system and baseline versus browser-only results.
`--case`, `--arm` and `--repetitions` select a bounded smoke subset; its
summary is marked protocol-incomplete. Missing token usage is recorded as
`null`, and an unverified common budget is flagged as a mismatch. Do not
report an improvement percentage from smoke or fake data. The 18 real runs
and three public full-system acceptance tasks are D7 deliverables.
After source spot-checking, add `manual_contradiction_note` (`none` or a
description) to each raw record and run
`uv run --locked python -m benchmark.runner --summarize data/benchmark/<run-id>`.
Completion rate remains `null` until every note is set. The upstream baseline
cannot enforce the token cap before each call, so its budget comparison is
marked mismatched even when observed totals fall below 40,000.

`benchmark/manual_browser_use_smoke.py` is a legacy ChatOpenAI smoke script,
not the same-model V1 baseline or an automated benchmark test.

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
