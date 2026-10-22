# Adaptive Research Agent

Start with the [documentation map](docs/README.md) for the four current
authorities, the [task index](docs/tasks/README.md), and the
[architecture map](docs/architecture/README.md).

Adaptive Research Agent is a public technical research Agent project built on
[`browser-use`](https://github.com/browser-use/browser-use). Its
[current specification](SPEC.md), [plan](PLANS.md), [contracts](docs/contracts/CURRENT_CONTRACTS.md)
and [evaluation protocol](docs/evaluation/CURRENT_EVAL_PROTOCOL.json) define the
portfolio target. The default V1 entry preserves Vue, FastAPI, an in-process
AgentLoop and SQLite. P-01 adds a separate PostgreSQL API and independent Worker
under the same backend package. The `browser-use/` submodule is upstream-owned.

The historical [D7 report](docs/archive/v1-audits/V1_DELIVERY_REPORT.md) records 18 real
r12 attempts and three separate UI tasks with no complete research success.
Those records remain immutable and No-Go. Offline tests and a controlled fake
demo verify code paths, not live source quality. The product remains No-Go;
individual implementation and acceptance states are in the [task index](docs/tasks/README.md).
See the [historical design index](docs/archive/design-0.3/00_DESIGN_INDEX.md) for archived plans.

The confirmed first-release target is a Windows API, independent Worker,
existing AgentLoop and browser with PostgreSQL in WSL. It includes a full local
admin UI for five accounts including the administrator, a two-running/eight-
queued capacity simulation, one safe Worker recovery, and one encrypted
removable-media backup and independent restore. B01 open-source tool selection
is the first interview demonstration. [ADR-0005](docs/design/adr/0005-windows-worker-wsl-postgres.md)
records the decision and the two-week fake-task stop gate. The current
[`current-3` evaluation protocol](docs/evaluation/CURRENT_EVAL_PROTOCOL.json)
retains all nine frozen prompts and the 15-attempt release gate. The V1 commands
below do not exercise the separate P-01 development path or the P-02 pilot;
their implementation and actual acceptance states are recorded separately.

The [P-01 task record](docs/tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md),
[measured acceptance evidence](docs/tasks/P01_ACCEPTANCE_2026-10-21.md)
and [local environment probe](docs/audits/PREDEV_ENV_SETUP_2026-10-20.md)
record the prepared dependencies and the WSL lifecycle requirement. The
isolated development database is not used by V1. P-01 migrations now create its
application ledger; disposable PostgreSQL databases are used for integration tests.
The [P-02 to P-04 task package](docs/tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md),
[P-02 offline pilot preparation](docs/tasks/P02_PILOT_PREP_2026-10-21.md),
[offline source-review workflow](docs/evaluation/REVIEW_WORKFLOW.md), and
[delivery checklist](docs/audits/PREDEV_DELIVERY_CHECKLIST_2026-10-20.md)
define the remaining research-quality, evaluation, and interview handoff work.
The [predevelopment finalization record](docs/audits/PREDEV_SEVEN_CORE_FINALIZATION_2026-10-20.md)
lists the checks actually run and the remaining No-Go gates.

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
uv --directory backend sync --dev
```

Copy `.env.example` to `.env` only when configuration overrides are needed.
An empty `DEEPSEEK_API_KEY` is treated as missing: the API can start and list
tasks, but creating a task returns 503 until the server has a DeepSeek key.
`GITHUB_TOKEN` is optional for public repository research. Keep credentials
server-side and never put their values in browser settings, issue reports,
traces, SSE events, or benchmark records.

## Run the P-01 PostgreSQL development path

Configure the ignored root `.env` with `P01_DATABASE_URL` pointing to the isolated
WSL PostgreSQL application database. Keep the V1 `DATABASE_URL` separate. From
the repository root, the local launcher maintains WSL, checks PostgreSQL, applies
versioned migrations, starts the API on loopback and restarts a failed Worker:

```powershell
./scripts/start-p01.ps1
```

Use the frontend command below in another terminal. This development path uses
one synthetic local owner; five-account sessions are P-03 work. Actual stage
acceptance belongs to the [P-01 task record](docs/tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md).
Starting a real research task requires separate cost authorization. The
`-ControlledTestWorker` launcher option is reserved for the local measurement
fixture and executes no provider or browser calls.

## Run the existing V1 code locally with an isolated database

Choose a new disposable SQLite path for local checks so an existing
`data/adaptive_agent.db` is not changed. In PowerShell, from the repository
root:

```powershell
$env:DATABASE_URL = "sqlite+aiosqlite:///./data/local-demo.db"
uv --directory backend run uvicorn adaptive_research.api.main:app --host 127.0.0.1 --port 8000
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
uv --directory backend run uvicorn tests.d6_demo_server:app --host 127.0.0.1 --port 8000
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
uv --directory backend lock --check --offline
uv --directory backend run --offline --locked pytest -q
uv --directory backend run --offline --locked ruff check --config pyproject.toml src tests migrations ../scripts
uv --directory backend run --offline --locked ruff format --check --config pyproject.toml src tests migrations ../scripts
uv --directory backend run --offline --locked python -m compileall -q src tests migrations ../scripts
npm ci --prefix frontend
npm run type-check --prefix frontend
npm run build --prefix frontend
npm run test --prefix frontend
```

`pytest -q` excludes the real-browser test. To opt in to a local Chromium
smoke using a controlled loopback HTTP page (no API key required):

```powershell
uv --directory backend run pytest -q -m browser tests/smoke/test_browser_use_adapter.py
```

The smoke enables loopback URLs only in its test adapter instance; the normal
adapter rejects local/private targets, checks the current page before further
observation or interaction, and rejects an unsafe final URL after navigation.
A redirect may reach that destination before the final check, so this is a
trusted localhost demonstration, not a public network-isolated service.
Browser startup depends on an installed Chromium-compatible browser.
The CI workflow has offline Python jobs for 3.12 and 3.13, a PostgreSQL 16
integration job, and a locked frontend install, type check, test and build job.
A local green run is not evidence
that remote GitHub Actions executed. Offline tests, controlled browser smoke,
fake-backed UI checks, live research, and protocol benchmark runs are separate
evidence levels.

## Historical V1 benchmark

The commands below describe the historical V1 runner, not the current portfolio
release gate. Read [`docs/benchmark/BENCHMARK_PROTOCOL.md`](docs/benchmark/BENCHMARK_PROTOCOL.md)
before inspecting it. The runner's default invocation prints the
fixed B01–B03, three-arm, two-repetition plan without making provider calls:

```powershell
uv --directory backend run --offline --locked python -m adaptive_research.evaluation.legacy_v1.runner
```

Only with separate authorization for live execution and its cost, a server-side
`DEEPSEEK_API_KEY`, installed Chromium, and network access, run the historical
18-attempt protocol:

```powershell
uv --directory backend run --locked python -m adaptive_research.evaluation.legacy_v1.runner --live
```

Each attempt is retained as a redacted JSON file under
`data/benchmark/<run-id>/`, including failures, with a `summary.json` for
separate baseline versus full-system and baseline versus browser-only results.
`--case`, `--arm` and `--repetitions` select a bounded smoke subset; its
summary is marked protocol-incomplete. Missing token usage is recorded as
`null`, and an unverified common budget is flagged as a mismatch. Do not
report an improvement percentage from smoke or fake data. The 18 r12 runs and
three separate public UI acceptance tasks are preserved historical failures.
After source spot-checking, add `manual_contradiction_note` (`none` or a
description) to each raw record and run
`uv --directory backend run --locked python -m adaptive_research.evaluation.legacy_v1.runner --summarize ../data/benchmark/<run-id>`.
Completion rate remains `null` until every note is set. The upstream baseline
cannot enforce the token cap before each call, so its budget comparison is
marked mismatched even when observed totals fall below 40,000.

`backend/src/adaptive_research/evaluation/legacy_v1/manual_browser_use_smoke.py` is a legacy ChatOpenAI smoke script,
not the same-model V1 baseline or an automated benchmark test.

## Local database preservation

V1 startup uses SQLAlchemy `metadata.create_all` without Alembic. It creates
missing tables and does not automatically clear or delete the local
`data/adaptive_agent.db` file. `create_all` does not migrate existing columns.
If a future schema change is incompatible, stop the app, back up the database,
and plan an explicit data-preserving migration or a deliberate disposable-data
reset. Do not delete an existing database as a routine startup step.

## Project contracts

The only current development entry points are [SPEC.md](SPEC.md),
[PLANS.md](PLANS.md), [current contracts](docs/contracts/CURRENT_CONTRACTS.md),
and [current evaluation protocol](docs/evaluation/CURRENT_EVAL_PROTOCOL.json).
Repository rules are in [AGENTS.md](AGENTS.md). Existing V1 behavior is documented
by the [V1 specification](docs/specs/V1_SPEC.md) and
[V1 contracts](docs/contracts/V1_CONTRACTS.md), subject to source and tests.
The [archived target](docs/archive/target-2026-10-18/SPEC.md), older protocols,
audits, and benchmark records are evidence from earlier decisions, not
instructions for new business development. Dependency installation, paid live
runs, deployment, commits, and pushes require separate authorization.
