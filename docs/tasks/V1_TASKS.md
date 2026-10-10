# Adaptive Research Agent V1 — seven development days

This is the executable **target ledger**, revised 2026-10-09 after the
predevelopment review. D1 starts only after the gate in
`docs/audits/V1_PREDEV_FINAL_REVIEW.md`; dates are relative development days.
The earlier ledger started 2026-10-08 and targeted 2026-10-14. Its Day 01
adapter work and evidence are retained in
`.codex-workflow/lifecycle/20261008-v1-day01/`; the old calendar dates are
historical, not a claim that the revised seven days have already elapsed.

Statuses are `not_started`, `in_progress`, `implemented_unverified`,
`verified`, or `blocked`. A planned command is never a passed check. The
task's acceptance evidence must include the command output and the observable
assertion. Run project-wide offline checks after each day's changes. No task
may weaken or skip a failing test to meet its date.

## Work packages

All effort estimates are **remaining single-developer hours**, including
focused tests. They are planning estimates, not measured completion time.
`P0` blocks V1; `P1` is the reproducible comparison. Commands assume a synced
uv environment. Later-day test paths remain targets until their tasks begin.

| ID / day / priority / hours | Dependencies; responsible files | Implementation boundary and done definition | Planned test command; observable evidence | Risk and failure response; current status |
| --- | --- | --- | --- | --- |
| T01 / D1 / P0 / 1h | Frozen contract; `adaptive_agent/adapters/browser_use_adapter.py`, `tests/unit/test_browser_use_adapter.py`, `tests/smoke/test_browser_use_adapter.py` | Recheck the existing Day 01 adapter against gitlink `7be96ed8`; no rewrite. Seven actions dispatch through checked-out APIs; session closes on success/failure. Real smoke requires only start, navigate, observe, extract, close. | `uv run --offline --locked pytest -q tests/unit/test_browser_use_adapter.py`; `uv run --locked pytest -q -m browser tests/smoke/test_browser_use_adapter.py`. Record real page URL/title/text and closed session. | Status: `verified` for the narrow D1 scope. Local upstream APIs were checked; current fake seven-action coverage and controlled five-stage Chromium smoke passed. Click/input/scroll/back/wait were not individually browser verified; submodule cleanliness remains unverified. |
| T02 / D1 / P0 / 4h | Spec/Contracts; `adaptive_agent/state.py`, `adaptive_agent/events.py`, `tests/unit/test_state.py` | Implement approved queued/partial statuses, subgoal criteria, fact/report/event fields and Pydantic invariants together; state remains JSON serializable and free of runtime objects. | `uv run --offline --locked pytest -q tests/unit/test_state.py`; valid/invalid models and JSON round trip have literal assertions. | Status: `verified` for D1. Fields and validations passed; direct TaskManager test and new ORM task default migrated. URL shape does not prove tool-observed provenance; existing database rows were not rewritten. |
| T03 / D1–D2 / P0 / 3h | T02; `adaptive_agent/state_reducer.py`, `tests/unit/test_state_reducer.py` | Pure `(ResearchState, AgentEvent) -> ResearchState`; reject wrong task, invalid/duplicate steps and terminal mutation; apply facts and usage once. | `uv run --offline --locked pytest -q tests/unit/test_state_reducer.py`; state transitions and serialized result match explicit fixtures. | Status: `verified` for D2 reducer scope. Consecutive step, selected subgoal, observed-source facts, normalized history, usage and no-progress assertions passed in the D2 67-test targeted run. |
| T04 / D2 / P0 / 5h | T02; `adaptive_agent/llm/base.py`, `adaptive_agent/llm/deepseek.py`, `tests/unit/test_deepseek.py` | `httpx.AsyncClient` DeepSeek request, timeout, usage, one temporary technical retry, one separate schema-repair request and close; no extra retry owner. | `uv run --offline --locked pytest -q tests/unit/test_deepseek.py`; fake transport proves 200, timeout, 429/5xx, malformed JSON, exact bounded attempts, redaction. | Status: `verified` for offline fake-transport scope. Real authenticated DeepSeek behavior remains unverified and is not a D2 live-run gate. |
| T05 / D2–D3 / P0 / 4h | T02,T04; `adaptive_agent/planner.py`, `adaptive_agent/prompts/planner.py`, `tests/unit/test_planner.py` | Initialize measurable subgoals, then choose exactly one action using current state and observation; no up-front script. | `uv run --offline --locked pytest -q tests/unit/test_planner.py`; changed state/observation changes the next decision; bad output fails safely. | Status: `verified` for D2 Planner scope. State and observation changes produce different decisions; invalid action and completed subgoal fail safely. Planner→Router integration remains D3. |
| T06 / D3 / P0 / 5h | T01,T02; `adaptive_agent/tools/router.py`, `adaptive_agent/tools/github_tool.py`, router/GitHub tests | Strictly route seven browser and three GitHub actions; normalize ToolResult, suppress equivalent URL/query before calls, use fixed GitHub REST host. | `uv run --offline --locked pytest -q tests/unit/test_tool_router.py tests/unit/test_github_tool.py`; fake endpoints show dispatch, no-call duplicates, 404/429/5xx and invalid action errors. | Rate limit or source ambiguity: surface structured result for replan; no tool-local retry loop. Status: `in_progress` (router skeleton). |
| T08 / D3–D4 / P0 / 4h | T02,T04,T06; `adaptive_agent/evaluator.py`, `adaptive_agent/prompts/evaluator.py`, evaluator tests | Technical evaluation precedes optional semantic LLM comparison; distinguish `none`, `technical`, `semantic`, `insufficient_info`; validate sources. | `uv run --offline --locked pytest -q tests/unit/test_evaluator.py`; technical error avoids semantic call, unsupported fact excluded. | Uncertain evidence: return insufficient information and replan; no benchmark LLM judge. Status: `not_started`. |
| T09 / D3 / P0 / 2h | T02,T03; `adaptive_agent/context_manager.py`, context tests | Deterministic history summary, last five traces and 12,000-character bounded current view with visible truncation. | `uv run --offline --locked pytest -q tests/unit/test_context_manager.py`; long synthetic history does not grow the prompt unboundedly. | Lost context: retain source and avoid-repeat summary, surface truncation. Status: `not_started`. |
| T07 / D4 / P0 / 6h | T03,T05,T06,T08,T09,T10; `adaptive_agent/agent_loop.py`, `tests/integration/test_agent_loop.py` | Bounded observe→decide→act→evaluate→reduce→report loop; 30 steps/900s/40k tokens/five non-progress replans, target count, goal and cancellation stops. | `uv run --offline --locked pytest -q tests/integration/test_agent_loop.py`; fake full/partial/failed/cancel paths each end once with reason and resource cleanup. | Unbounded or invented progress: stop with explicit partial/failed outcome; D4 cannot exit on a happy path alone. Status: `not_started`. |
| T10 / D4 / P0 / 3h | T02,T03; `adaptive_agent/reporter.py`, `adaptive_agent/prompts/reporter.py`, reporter tests | Generate general-purpose sourced ResearchReport after stop; each material finding maps to collected facts and URLs, partial gaps remain visible. | `uv run --offline --locked pytest -q tests/unit/test_reporter.py`; unsupported claims are rejected/omitted, not rendered as facts. | Sparse evidence: publish partial/insufficient conclusion. Status: `not_started`. |
| T11 / D5 / P0 / 5h | T07,T12 interface; `adaptive_agent/runtime/task_manager.py`, task manager tests | Two active tasks, isolated resources, bounded subscriber queues, queued/running cancellation, exception observation and shutdown cleanup. | `uv run --offline --locked pytest -q tests/unit/test_task_manager.py`; third task waits, failure frees slot, disconnect removes one subscriber. | Race or leaked task: reproduce with asyncio events, keep D5 gate closed. Status: `in_progress` (basic semaphore/cancel only). |
| T12 / D5 / P0 / 5h | T02,T03; `backend/services/persistence.py`, `backend/db/`, persistence tests | Persist task/step/fact/trace; atomically commit terminal status and event; reconstruct timeline/report and finalize unfinished rows after restart without deleting DB. | `uv run --offline --locked pytest -q tests/integration/test_database.py tests/integration/test_persistence.py`; rollback leaves neither half-write; new app instance reloads terminal output. | `create_all` cannot migrate old columns: keep existing DB safe, report schema incompatibility explicitly. Status: `in_progress` (tables only). |
| T13 / D5 / P0 / 7h | T11,T12; `backend/main.py`, `backend/api/research.py`, `backend/schemas/research.py`, API/SSE tests | Wire exactly six Spec routes through runtime/service; 202/200/404/422/503, idempotent cancel, persisted replay then live SSE, multi-subscriber, terminal close. | `uv run --offline --locked pytest -q tests/integration/test_research_api.py tests/integration/test_sse.py`; HTTP responses, ordered IDs, reconnect, disconnect and restart are observed. | Slow client/race: bounded queue plus persisted replay, never block task. Status: `in_progress` (placeholder routes). |
| T14 / D6 / P0 / 5h | T13; `frontend/`, frontend API and view tests | Vue 3/TypeScript goal input, Start/Cancel, status, timeline, sourced report and recent tasks consuming only six routes; no credentials in UI. | `npm ci --prefix frontend`; `npm run type-check --prefix frontend`; `npm run build --prefix frontend`; inspect keyboard/demo path and API errors. | Missing package/build blocks D6; do not mark absent frontend as passed. Status: `not_started`. |
| T15 / D6 / P1 / 5h | T07,T10,T13; `benchmark/`, benchmark tests | Run fixed B01–B03 with same DeepSeek model/budgets in baseline, adaptive full and adaptive browser-only arms; keep 18 redacted raw records and deterministic scorer. | `uv run --offline --locked pytest -q tests/unit/test_benchmark.py`; opt-in real runs per `docs/benchmark/BENCHMARK_PROTOCOL.md`; compare arms separately. | Missing usage/credentials or external failure: preserve failed raw record, label budget mismatch, never invent gain. Status: `in_progress` (metrics only). |
| T16 / D6–D7 / P0 / 4h | All applicable tasks; `tests/`, `.github/workflows/ci.yml`, `README.md` | Keep Python 3.12/3.13 offline checks truthful, add required frontend type-check/build when T14 exists, document setup, smoke, live acceptance and benchmark. | `uv lock --check --offline`; `uv run --offline --locked pytest -q`; Ruff check/format check/compileall; frontend commands and actual Actions result. | CI unavailable: report local pass and remote unverified separately. Status: `in_progress` (local Python workflow only). |

## D1 outcome and D2 handoff (2026-10-10)

D1 is **Pass** for T01 recheck, T02 contract and the explicitly bounded T03
foundation; it does not claim V1 completion. Current Windows evidence is
listed command by command in `docs/testing/V1_TEST_MATRIX.md`: Python
3.12.13 targeted 92 passed, browser 1 passed, full offline 101 passed/1
deselected, all static gates exit 0, and Python 3.13.2 D1-related 97 passed.
No existing local SQLite rows were changed. The main repository inventory was
preserved; submodule cleanliness remains unverified due Git metadata
permissions.
Observed wall-clock D1 interval was 2026-10-09 18:41 to 2026-10-10 00:16
(Asia/Shanghai), about 5h35m including an interruption; active hands-on
time was not measured separately.

Pre-D1 main repository inventory from
`git -c submodule.browser-use.ignore=all status --short --untracked-files=all`
was:

```text
 M .env.example
 M .gitignore
 M README.md
 M adaptive_agent/adapters/browser_use_adapter.py
 M backend/config.py
 M docs/specs/V1_SPEC.md
 M pyproject.toml
 M tests/unit/test_browser_use_adapter.py
 M tests/unit/test_config.py
 M tests/unit/test_task_manager.py
?? .codex-workflow/lifecycle/20261008-v1-day01/
?? .github/workflows/ci.yml
?? docs/audits/
?? docs/benchmark/
?? docs/contracts/
?? docs/tasks/
?? docs/testing/
?? tests/smoke/test_browser_use_adapter.py
```

T03 remains `in_progress` on D2's critical path. A valid
`step_evaluated` currently raises an explicit `NotImplementedError`.
D2 must add tests and implementation for consecutive step application,
selected subgoal status, source-validated fact admission and deduplication,
normalized visited URL/search query updates, once-only token accumulation,
and increment/reset of `consecutive_no_progress_replans`. D2 must prove
duplicate events cannot apply the same fact or usage twice. The D1 URL
validator establishes shape, not tool-observed provenance.

## D2 outcome (2026-10-10)

**Historical D2 handoff before the independent recheck:** T03 reducer aggregation,
T04 fake-backed DeepSeek requests and T05 dynamic Planner decisions are
implemented and verified at their D2 boundaries. New tests were observed
failing before implementation (T03: four failures; T04: missing provider
result interface; T05: four constructor failures). After fixes and formatting,
the D2 targeted command passed **67 tests** and the full offline suite passed
**135 tests with one opt-in browser test deselected**. The lock, Ruff check,
Ruff format check and compileall commands each exited 0; exact commands are in
`docs/testing/V1_TEST_MATRIX.md`.

The restricted Windows sandbox denied `uv` interpreter queries and hung while
creating an asyncio event loop. The same required `uv` commands completed in
the approved regular execution environment. No authenticated DeepSeek call,
real research task, Planner→Router integration, or browser smoke is claimed by
this D2 evidence. D3–D7 work retains its planned status.

## D2 recheck and repair (2026-10-10)

**D2 module: Pass for the bounded D2 exit criteria after repair.** The recheck
used the actual `00a425c2` working-tree diff, not the earlier ledger result.
T03 now rejects non-pending initialization and inconsistent tool outcomes;
T04 now sends its JSON schema, exposes machine-readable failure kinds, and
defaults to the currently documented `deepseek-flash` model; T05 rejects
parameterized `go_back` and malformed GitHub repository targets. Every defect
was reproduced by a failing regression test before its fix. The D2 component
chain test covers provider parsing → Planner → Reducer with simulated tool
evidence and owned HTTP client closure. The final Python 3.12 targeted suite
passed **86 tests**; full offline suites passed **152 tests with one opt-in
browser test deselected** on both Python 3.12 and 3.13. Static checks and wheel
build passed; exact commands and stage evidence are in
`docs/audits/D2_ACCEPTANCE_2026-10-10.md`.

No DeepSeek key or `.env` was available, so an authenticated request was not
run. The Agent Loop and research API remain placeholders; complete V1 business
acceptance is **not ready**. Independent review could not be claimed because
the effective parent permission mode is writable and a separate read-only
reviewer was not verifiable; the main agent completed the scoped line-evidence
review. D3–D7 work retains its planned status.

The final D2 acceptance pass found two more boundary defects: Planner allowed
`element_index=0` with a semantic click target, and an injected DeepSeek HTTP
client without `base_url` could not resolve the request path. Both were
reproduced with failing tests and repaired. The `.env.example` model setting
was also aligned with the runtime default. Final scoped tests passed **88**;
the full offline suite passed **154** with one opt-in browser test deselected on
both Python 3.12 and 3.13. The lock check, Ruff checks, compileall and wheel
build exited 0. See `docs/audits/D2_ACCEPTANCE_2026-10-10.md` for commands and
scope limits.

## Daily exit gates and capacity

| Day | Hours | Gate; dependency risk and response |
| --- | ---: | --- |
| D1 | 7 | Freeze contract, recheck T01, pass T02 and reducer foundation. If existing Day 01 smoke cannot rerun, retain historical evidence and explicitly flag current real-browser gap. |
| D2 | 8 | Reducer and provider error/usage paths pass; Planner selects from state. Provider uncertainty blocks D3 integration. |
| D3 | 12 | Both tool paths, four evaluator types, dedup and context bounds pass offline; this exceeds one eight-hour day by four hours. |
| D4 | 10 | Fake complete/partial/failed/cancel research loop and sourced report pass; this exceeds capacity by two hours. |
| D5 | 17 | Concurrency, SQLite rollback/restart, six API routes and SSE pass; this exceeds capacity by nine hours and is the largest integration risk. |
| D6 | 14 | Vue type-check/build, complete CI gate and benchmark scorer/raw-record path pass; this exceeds capacity by six hours. |
| D7 | 9 | Full regression, controlled Chromium, three separately recorded public acceptance runs using B01–B03 prompts, 18 same-model benchmark runs, defect fixes and delivery report; no green skeleton test substitutes for a live run. |

After D1, D2–D7 still total about **70 hours plus 3 hours of buffer**. One
developer at eight hours for the six remaining days has 48 hours, a **25-hour
shortfall** including buffer. The seven-day guarantee remains No-Go. A
10-day single-developer schedule remains the credible V1 baseline if daily
gates remain evidence-based; alternatively, add about 25 hours of independent
capacity without parallel
writes to shared model, API schema, database or CI files. Scope-compliant
reduction is three rather than five live tasks, the minimum Vue view and the
fixed three benchmark cases; core tests and real acceptance remain required.

Critical path: T01 confirmation → T02/T03/T04/T05 → T06/T08/T09 → T07/T10
→ T11/T12/T13 → T14/T15 → D7 acceptance. T04/T06 and T09/T10 can be worked
in parallel after their interfaces freeze; shared files and mutable browser,
database and benchmark environments stay serial. At each stopping point,
record Progress, Surprises & Discoveries, Decision Log and Outcomes in the
task ledger or day's evidence. A missed gate changes the schedule/status,
never the meaning of `verified`.

## Changeset review follow-up (2026-10-10)

The later adapter review and current local checks are recorded in
`docs/audits/CURRENT_CHANGESET_ACCEPTANCE.md` and
`docs/testing/V1_TEST_MATRIX.md`. Read-only nested Git inspection confirmed
the browser-use submodule has no local changes at the tracked gitlink; the D1
handoff above remains a dated record of its earlier permission limit.
T03 `step_evaluated` aggregation and all later V1 tasks retain their existing
in-progress or planned status.
