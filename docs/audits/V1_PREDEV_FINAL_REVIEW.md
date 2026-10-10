# V1 predevelopment final review

Review date: **2026-10-09, Asia/Shanghai**. This review ends at the
development-start gate. It does not implement AgentLoop, the working API,
Vue, or benchmark runners. Product authority is `docs/specs/V1_SPEC.md`;
`docs/contracts/V1_CONTRACTS.md` specifies the approved target contract.

## 1. Repository facts and protection of existing work

- Main repository: branch `main`, HEAD
  `e72572b688130b08583c47c75b75120af119e5d4`. Gitlink for browser-use:
  `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`; checked-out
  `browser-use/pyproject.toml:5` declares `0.13.10`, and `uv.lock:245-246`
  resolves the editable package at `0.13.10`. The actual API methods used by
  the adapter exist in `browser-use/browser_use/browser/session.py:727,734,
  1597,2428,2442,2502`, `browser-use/browser_use/tools/service.py:584,
  778,1383,2132`, and `browser-use/browser_use/dom/markdown_extractor.py:23`.
- Plain `git status --short --untracked-files=all` exited 1 because Git could
  not enter `.git/modules/browser-use` (`Permission denied`). `git -C
  browser-use rev-parse HEAD` meets the same restriction; submodule worktree
  cleanliness cannot be certified. `git -c submodule.browser-use.ignore=all
  status --short --untracked-files=all` succeeded and produced the baseline
  below. Ignoring the submodule is a visibility workaround, **not** proof it
  has no local changes.
- Existing Day 01 changes and all lifecycle evidence were retained. This
  review changed only the requested project configuration, targeted tests,
  Spec/Contracts/protocol, README, task ledger, test matrix and this report.
  It did not edit browser-use, reset the database, switch branches, commit,
  push, publish or deploy. The ignored local database exists; no reset command
  was run.

Baseline main-worktree inventory before this review's edits:

```text
 M .gitignore
 M README.md
 M adaptive_agent/adapters/browser_use_adapter.py
 M docs/specs/V1_SPEC.md
 M pyproject.toml
 M tests/unit/test_browser_use_adapter.py
 M tests/unit/test_task_manager.py
?? .codex-workflow/lifecycle/20261008-v1-day01/brief.md
?? .codex-workflow/lifecycle/20261008-v1-day01/delivery.md
?? .codex-workflow/lifecycle/20261008-v1-day01/evidence/day01.txt
?? .codex-workflow/lifecycle/20261008-v1-day01/review.md
?? .codex-workflow/lifecycle/20261008-v1-day01/run.json
?? .codex-workflow/lifecycle/20261008-v1-day01/verification.md
?? .github/workflows/ci.yml
?? docs/audits/V1_READINESS_AUDIT.md
?? docs/benchmark/BENCHMARK_PROTOCOL.md
?? docs/contracts/V1_CONTRACTS.md
?? docs/tasks/V1_TASKS.md
?? docs/testing/V1_TEST_MATRIX.md
?? tests/smoke/test_browser_use_adapter.py
```

### Claim audit

| Existing claim | Current classification and evidence |
| --- | --- |
| README says domain models, tables, route registration and basic concurrency have tests (`README.md:9-15`) | **Current command verified only for skeleton scope:** offline suite below passes. `tests/smoke/test_app.py` asserts placeholder behavior; `backend/api/research.py:19-64` still returns 501/empty paths. |
| README says adapter supports declared actions and five-stage real smoke (`README.md:10-13`) | **Source confirmed** by `adaptive_agent/adapters/browser_use_adapter.py:176-231`, fake action tests and current Chromium smoke. Real click/input/scroll/back/wait are **not individually browser verified**. |
| Old readiness audit reports clean tree, 13 tests, no CI and no browser action (`V1_READINESS_AUDIT.md:9-24,37,45-49`) | **Historical pre-Day-01 snapshot**, superseded by the baseline inventory, current 20-test run, existing untracked CI and current adapter. The old report remains untouched for provenance. |
| Day 01 evidence reports 18 offline passes, one browser pass, lock and Ruff passes (`.codex-workflow/lifecycle/20261008-v1-day01/evidence/day01.txt:3-10`) | **Historical command record** from 2026-10-08, not automatically a current result. Current reruns appear in the validation table below. |
| Task ledger labels T01 `verified` (`V1_TASKS.md` historical row 17) | **Verified only to its narrow acceptance**: fake dispatch of seven actions and five real stages; the revised ledger names the scope and schedules a D1 recheck. |
| Test matrix says 18 offline and one Chromium smoke (`V1_TEST_MATRIX.md` historical lines 3-15) | **Historical command record**. The revised matrix separates current offline, current browser, planned integrations and missing live evidence. |
| README and task ledger list startup/CI/frontend/benchmark steps | FastAPI lifespan with an **in-memory** SQLite DB and `/docs` returned 200 in a local TestClient smoke; the README's long-running uvicorn server command was not separately exercised. Remote Actions, Vue build, live DeepSeek/GitHub, research tasks and benchmark are **unverified**. No frontend package or runners exist yet. |

Current skeleton blockers remain at `adaptive_agent/agent_loop.py:34`,
`planner.py:15`, `llm/deepseek.py:23`, `state_reducer.py:15`,
`tools/github_tool.py:23`, `backend/services/persistence.py:20-58`, and
`backend/api/research.py:19-64`. These are assigned to D1–D6, not fixed
during predevelopment.

## 2. Targeted research and decisions

All references were viewed on **2026-10-09**. Installed local versions came
from `importlib.metadata`: FastAPI 0.142.2, Pydantic 2.13.5,
pydantic-settings 2.15.0, SQLAlchemy 2.1.3, httpx 0.28.1, pytest 9.1.1,
Ruff 0.16.10 and browser-use 0.13.10. Versions of external documentation
may advance independently of this lockfile.

| Reference (version/commit) | Concrete adoption | Deliberate exclusion and reason |
| --- | --- | --- |
| Local browser-use source and [tracked upstream commit](https://github.com/browser-use/browser-use/tree/7be96ed8bafa8dfe1eef228b59cf5c884b8b2431) gitlink `7be96ed8`, declared version 0.13.10; local `browser/session.py`, `tools/service.py` (checked-out HEAD identity unverified due Git metadata permissions) | Keep `BrowserSession.start/kill`, `get_browser_state_summary`, `navigate_to`, `get_element_by_index` and Tools calls behind the existing adapter; test lifecycle and actual five-stage smoke. | Do not put research state/loop policy in upstream or patch it for this preparation. Its post-navigation checks are not network isolation. |
| [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/) and [async tests](https://fastapi.tiangolo.com/advanced/async-tests/), applied to installed 0.142.2 | Own DB/runtime startup and disposal in lifespan; use HTTPX ASGI transport with explicit lifespan handling in D5 integration tests. | No direct browser-use calls in route functions and no new task-queue framework. |
| [Pydantic v2 models](https://pydantic.dev/docs/validation/2.0/usage/models/) and [settings](https://pydantic.dev/docs/validation/latest/api/pydantic_settings/), applied to 2.13.5/2.15.0 | Validate structured boundaries with approved target models; normalize blank credential inputs to missing without printing values. | Do not reuse API schema or ORM classes as ResearchState; keep explicit, small mappings. |
| [SQLAlchemy async 2.1](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html), applied to 2.1.3 | Use one `AsyncSession` per task/transaction, atomic terminal status plus trace, explicit rollback and engine disposal. `create_all` only creates missing tables. | No Alembic or automatic DB deletion in V1; existing data must survive startup. |
| [uv lock/sync](https://docs.astral.sh/uv/concepts/projects/sync/), [uv GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/) and [Actions permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax); local uv 0.11.28, `setup-uv@v10.2.0` | CI now targets Python 3.12 and 3.13 with `UV_PYTHON`, locked sync, offline checks after sync and `contents: read`; no runtime secrets injected into PR checks. | An absent frontend build is not a pass. No deployment token or write permission is needed. Remote Actions result remains unverified. |
| [Vue TypeScript guidance](https://vuejs.org/guide/typescript/overview), target Vue 3; frontend not yet installed | D6 must run both `vue-tsc` type checking and Vite build against the six-route API contract. | No generated client/framework or UI management console for a six-route V1. |
| OpenAI [PLANS.md long-task practice](https://developers.openai.com/cookbook/articles/codex_exec_plans), archived 2025-10-07 article | Keep progress, discoveries, decision changes and observed outcomes in the task/evidence ledger. | Do not import its model/commit instructions or create another plan framework; repository rules prohibit automatic commits. |

## 3. Problems, fixes and residual limits

Severity: P0 blocks an explicit V1 delivery condition; P1 materially affects
reliability or a truthful gate. File lines are current unless labeled
pre-fix. Verification names a command or later acceptance result, not a guess.

| ID / severity | Trigger, evidence and impact | Repair or decision; verification |
| --- | --- | --- |
| CFG-01 / P1 | Python 3.13 is supported by `pyproject.toml:6` and README, but pre-fix `.github/workflows/ci.yml:18-20` used only 3.12. A 3.13 regression could pass CI. | `.github/workflows/ci.yml:13-31` now has a 3.12/3.13 matrix, `UV_PYTHON`, pinned uv 0.11.28 and `uv sync --locked --dev`; CI invokes lock, settings, Ruff, compile and offline tests. Locked offline pytest passed locally on both 3.12 and isolated 3.13; **remote Linux Actions have not run**. |
| CFG-02 / P0 final gate | `frontend/package.json` does not exist and `.github/workflows/ci.yml:45-46` has no Vue job. Missing frontend could otherwise be mistaken for passing CI. | Explicitly classify frontend build/type-check **unverified** now. T14/T16 add a required non-skipping `npm ci`, `type-check` and build job on D6; a missing package then blocks D6. |
| CFG-03 / P1 | Pre-fix `README.md:80-85` directed manual deletion of the SQLite DB for schema changes, risking loss of local evidence. `backend/db/session.py:22-28` only calls `create_all`. | `README.md:89-96` now states startup never clears the DB, `create_all` cannot migrate columns, and incompatible changes require an explicit backup and preservation decision. D5 restart test proves persisted output. No DB deletion was performed. |
| CFG-04 / P1 boundary | Adapter validates requested URL before navigation and final URL afterward (`browser_use_adapter.py:153-157,186-187,283-303`). A redirect can contact a private address before final validation. Public SSRF isolation is unproved. | New `tests/unit/test_browser_use_adapter.py:244` verifies private final URL returns semantic failure and cleanup; it passed. README/Spec/matrix retain **trusted localhost only**. Pre-request redirect/network isolation is not claimed or introduced in predevelopment. |
| CFG-05 / P1 | Blank `.env.example` credentials previously parsed as `SecretStr('')`; later missing-key checks could treat them as present. Pre-fix targeted test failed on whitespace key. | `backend/config.py:24-30` maps blank/whitespace credentials to `None`; `tests/unit/test_config.py:16-25` passes without exposing a value. `.env.example:1-4` and README describe required vs optional keys. |
| DOC-01 / P1 | Contracts called 900s/40k tokens/five no-progress/12k context *proposed*, while test matrix and benchmark treated them as fixed. Different implementers could choose different stops. | User chose to freeze current numbers. `V1_SPEC.md:219-224`, `V1_CONTRACTS.md:39-47` and `BENCHMARK_PROTOCOL.md:46-51` now agree and say the current skeleton does **not** yet enforce them. D2–D4 tests must prove implementation. |
| DOC-02 / P1 | Historical `V1_READINESS_AUDIT.md:9-24,37` says tree clean/no CI/no browser actions; those claims are stale after Day 01. | Preserve old file as dated history. This report and the revised task/test ledgers distinguish current source, current commands, historical commands and planned work. Reconcile any later contract change in Spec first. |
| PATH-01 / P0 | Starting D1 with the old `adaptive_agent/state.py:36-41,69-86`, `events.py:11-19` and `state_reducer.py:7-16` would leave queued/partial, event IDs and reducer transitions inconsistent with Spec §25 and Contracts. Agent state and consumers could diverge. | T02–T03 change models/events/reducer together; A-layer JSON, invalid-transition, duplicate-step and terminal-immutability tests are the D1/D2 gate. Not implemented in this review. |
| PATH-02 / P0 | A research request reaches `adaptive_agent/planner.py:15`, `llm/deepseek.py:23`, `tools/github_tool.py:23` or `agent_loop.py:34`, all still placeholders. No actual research report can be produced. | T04–T10 implement in dependency order; A/B tests prove provider retry/repair, state-dependent plan, strict routing, failures, bounded loop and sourced report before live tasks. Not implemented in this review. |
| PATH-03 / P0 | `backend/services/persistence.py:20-58` and `backend/api/research.py:19-64` remain placeholders; task creation/history/SSE cannot satisfy the six-route contract. `runtime/task_manager.py:19-75` lacks multi-subscriber terminal handling. | T11–T13 implement async runtime, atomic SQLite writes/restart and API/SSE; B-layer cancel, rollback, replay, multi-client and resource tests close the D5 gate. Not implemented in this review. |
| PATH-04 / P0 | `frontend/package.json` is absent; `benchmark/baseline.py:4-5` and `adaptive.py:4-5` are placeholders. A green Python suite cannot provide UI or comparable raw runs. | T14–T16 add the minimal Vue app, required CI job and fixed-case same-model runners; D6 type-check/build and E-layer 18 records are required, with D7 live tasks. Not implemented in this review. |
| ENV-01 / P1 | Ordinary Git submodule status cannot read `.git/modules/browser-use`, so a normal clean-tree claim is unsupported. | Preserve the gitlink/source version and main-repo status workaround. A host with Git metadata access must confirm submodule cleanliness before an upstream change or final reproducibility claim; none is authorized here. |
| CAP-01 / P0 seven-day promise | `docs/tasks/V1_TASKS.md:44-58` estimates 77h work plus 3h buffer; single developer × 7 × 8h = 56h. D5 alone estimates 17h. | Seven-day guarantee is **No-Go** at current capacity. Add about 24 independent hours without concurrent shared-file writes, or use 10 single-developer days within `V1_SPEC.md:13-16`'s 7–10 day window. Verify capacity by actual daily exit times; do not remove core tests, real tasks or raw benchmark runs to fabricate feasibility. |

## 4. Requirement → task → test → acceptance trace

The complete row-level observable conditions and evidence targets are in
`docs/testing/V1_TEST_MATRIX.md`. The following links each required capability
to the responsible work and final proof. A/B/C/D/E have the layer meanings
defined in that file; **none of the target-only rows is claimed implemented**.

| ID | Capability | Task | Test layer and final observable evidence |
| --- | --- | --- | --- |
| R01 | ResearchState, AgentEvent, pure legal reducer transitions, serialization | T02,T03 | A/B: model round trip and invalid/duplicate/terminal transition results |
| R02 | Observation-dependent one-step Planner | T05 | A/B/D: changed state changes next decision; live trace shows replanning |
| R03 | DeepSeek timeout/usage/one retry/one repair | T04 | A: fake HTTP transport attempt count, usage and safe failure |
| R04 | Seven browser actions and session lifecycle | T01 | A/C: fake seven-action paths plus controlled real five-stage and cleanup smoke |
| R05 | GitHub REST and strict tool routing | T06 | A/B/D: valid action results, invalid/duplicate calls suppressed |
| R06 | Failure classification, deduplication, bounded context | T06,T08,T09 | A/B: distinct errors, no repeat call, bounded prompt |
| R07 | Step/time/token/cancel/no-progress/target/goal stops | T07 | A/B/D: one terminal event, exact status/reason and resource closure |
| R08 | Sourced general ResearchReport | T10 | A/B/D: each material claim maps to fact and URL |
| R09 | TaskManager concurrency, cancellation, exception cleanup | T11 | A/B: two slots, queued cancel, released slot and closed resources |
| R10 | SQLite atomic writes, rollback, restart, reconstruction | T12 | B: no half-write; fresh app reloads terminal timeline/report |
| R11 | Six routes and replay/live/multi-client SSE | T13 | B/D: HTTP status/schema and ordered event replay/terminal close |
| R12 | Minimal Vue workflow | T14 | B/manual: goal/start/cancel/timeline/report/recent tasks; type-check/build |
| R13 | Three to five real public research tasks | T07,T13,T14 | D: per-task ID, status, sources, steps, report and cleanup |
| R14 | Same-model baseline/full/browser-only benchmark | T15 | E: 18 raw redacted runs, deterministic coverage and separate comparisons |

Spec §24 has **12 Done-when bullets**. The revised matrix turns each into
an individually evidenced D7 checklist, including the six-route SSE timeline,
reloadable SQLite reports, sourced output, actual baseline/adaptive data and
local startup. A green skeleton suite, fake integration, browser smoke, real
task success and benchmark result are five different evidence classes.

## 5. Seven-day capacity and critical path

| Day | Work and hours | Exit gate and risk |
| --- | --- | --- |
| D1 | T01/T02/T03 foundation, 7h | Freeze models/events, confirm adapter against checked-out API; preserve Day 01 rather than redo it. |
| D2 | Reducer/provider/Planner, 8h | Bounded DeepSeek retries/repair and state-based decision tests pass. |
| D3 | Router/GitHub/Evaluator/Context, 12h | Both tool paths and all failure classes pass; 4h above capacity. |
| D4 | Loop/Reporter, 10h | Fake complete/partial/failed/cancel closure; 2h above capacity. |
| D5 | TaskManager/SQLite/API/SSE, 17h | Atomic restart and concurrent SSE/cancel paths; 9h above capacity and largest integration risk. |
| D6 | Vue/CI/benchmark runner, 14h | Build/type-check, complete offline gate, raw-record scorer; 6h above capacity. |
| D7 | Real/browser/benchmark/regression/report, 9h | Three separately identified acceptance runs using fixed B01–B03 prompts, plus 18 benchmark runs with raw data; 1h above capacity. |

Critical path: contract/T01 → T02/T03/T04/T05 → T06/T08/T09 → T07/T10 →
T11/T12/T13 → T14/T15 → D7. Provider and tool research can proceed in
parallel after interfaces freeze, as can context and report work. Shared
models, API schema, DB, CI and live browser/benchmark resources remain serial.
The fixed 18 benchmark runs alone can consume up to 4.5 hours at the 900s
limit, before real tasks, checks, investigation or report writing. The only
Spec-compliant scope savings assumed are three rather than five live tasks,
the minimum Vue screen and the three fixed benchmark cases. A failed daily
gate changes the schedule and evidence status, never the acceptance standard.

## 6. Environment, actual checks and remaining verification

Current Windows tools: uv 0.11.28; project `.venv` Python 3.12.13;
system Python 3.13.2; Node 23.11.1/npm 10.9.2. `.env` is absent and neither
`DEEPSEEK_API_KEY` nor `GITHUB_TOKEN` is set in the current process (presence
only was checked; no value was printed). A Chromium-compatible executable is
present and the controlled local smoke passed. D2 live provider work needs a
DeepSeek key and network access; GitHub token is optional for public API use.
D7 needs DeepSeek/GitHub/public-site connectivity, installed Chromium and a
recorded model/browser version. D6 needs an actual frontend package/lockfile
and successful Node install/type-check/build. CI must run on Linux for both
Python versions before it can be called remotely verified.

Commands below are this review's **actual** results. A restricted initial
attempt of each `uv` command exited 1 with `Failed to query Python
interpreter / 拒绝访问 (os error 5)`; the same checks were rerun with interpreter
access. That sandbox error is not a stale lock or failing test.

| Command | Exit code and raw result |
| --- | --- |
| `uv lock --check --offline` | 0; `Resolved 282 packages in 2ms` |
| `uv run --offline --locked python -c "from backend.config import Settings; Settings(_env_file=None); print('settings-ok')"` | 0; `settings-ok`; no credential value printed |
| `uv run --offline --locked pytest -q tests/unit/test_config.py tests/unit/test_browser_use_adapter.py` | 0; `9 passed in 0.93s` |
| `uv run --offline --locked pytest -q` | 0; `20 passed, 1 deselected in 1.90s` (Python 3.12 final rerun) |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` before cache population | 1; missing cached Pillow 12.3.0 `cp313` wheel; tests did not start |
| `python -m pytest -q` on system Python 3.13 without project dependencies | 1; collection errors for missing `browser_use`, not a V1 test failure |
| `uv run --isolated --python 3.13 --locked pytest -q` | 0 after locked wheels downloaded; `20 passed, 1 deselected in 15.80s` |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | 0 from populated cache; `20 passed, 1 deselected in 5.58s` |
| `uv run --isolated --python 3.13 --offline --locked ruff check adaptive_agent backend benchmark tests` | 0; `All checks passed!` |
| `uv run --isolated --python 3.13 --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0; `53 files already formatted` |
| `uv run --isolated --python 3.13 --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0; no command output after isolated install |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0; `All checks passed!` |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | First run exit 1, requested a blank line in `backend/config.py`; after that fix exit 0, `53 files already formatted` |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0; no output |
| `uv run --locked pytest -q -m browser tests/smoke/test_browser_use_adapter.py` | 0; `1 passed in 3.52s` on final controlled loopback rerun; not live-task acceptance |
| `DATABASE_URL=sqlite+aiosqlite:///:memory:` with `uv run --offline --locked python -c "...TestClient(app)...GET /docs..."` | 0; `docs_status= 200`; app lifespan ran without touching the local DB file |
| `git diff --check --ignore-submodules=all` | 0; only LF→CRLF warnings on working-copy paths |
| `.venv\\Scripts\\python.exe -m pytest -q tests/unit/test_config.py::test_blank_credentials_are_treated_as_missing` before fix | 1; expected `SecretStr('**********') is None` assertion failure, no raw value printed; after fix config file suite passed 2 tests |
| `.venv\\Scripts\\python.exe -m pytest -q tests/unit/test_browser_use_adapter.py::test_adapter_rejects_private_final_url_after_redirect` | 0; `1 passed in 1.03s` |
| Python `import yaml` to parse CI locally | 1; `ModuleNotFoundError: No module named 'yaml'`; no dependency was installed solely to inspect the workflow |

The source workflow now names the checks above and uses `permissions:
contents: read` with `persist-credentials: false`; a remote GitHub Actions
run is **unverified** because this workflow is still an untracked local file.
Frontend build/type-check, real DeepSeek/GitHub calls, complete research tasks
and benchmark are **unverified**. Windows locked offline pytest passed on both
declared Python versions; Linux CI execution remains unverified.
No improvement percentage is supported. The local SQLite file was not
automatically cleared; D5 must prove restart recovery with a temporary DB.

## 7. Gate conclusion and handoff

**Conditional Go for D1 development**: configuration, numeric contract,
traceability and offline baseline are now reviewable; the browser's narrow
controlled smoke passed. Start with **T01's one-hour evidence/API recheck,
then T02 domain models and AgentEvent**, followed by T03 reducer. Record each
daily exit gate before starting its dependent tasks. Before claiming a
seven-day commitment, supply roughly 24 additional independent work hours;
at the confirmed single-developer eight-hour capacity, **seven-day full V1 is
No-Go** and the 10-day Spec window is the credible planning baseline.

Full V1 delivery remains conditional on a usable DeepSeek credential,
external network, Linux CI evidence for both Python versions, a D6 frontend
build, D7 public task records, 18 real same-model benchmark raw records and
all 12 Spec Done-when checks. This review does not claim any of those future
results. Public deployment remains outside V1's trusted localhost boundary.
