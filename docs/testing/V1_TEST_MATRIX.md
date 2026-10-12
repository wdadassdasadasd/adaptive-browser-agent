# V1 requirement, test and acceptance matrix

Revised 2026-10-12 after D5. `docs/specs/V1_SPEC.md` is the product authority;
`docs/contracts/V1_CONTRACTS.md` supplies the approved target fields and
failure semantics. **Target** evidence paths below are not passed tests.
Current source still has no D6 Vue app or complete benchmark runner. The
2026-10-08 Day 01 record reports 18 offline
tests and one five-stage Chromium smoke; these are historical, not D1 results.
Never turn a planned row green from a different layer's result.

## Traceability

Layers: A pure unit, B fake-backed integration, C real controlled Chromium,
D public V1 research acceptance, E same-model benchmark. `Evidence target`
names the artifact or command output required before a row can be verified.

| Requirement / authority | Target behavior | Owner / task | Layer and external observable pass condition | Evidence target; present status |
| --- | --- | --- | --- | --- |
| R01 / Spec §§7,14,17; Contracts State/Events | Serializable ResearchState, legal `AgentEvent -> StateReducer -> ResearchState`, one terminal transition and no runtime objects | `adaptive_agent/state.py`, `events.py`, `state_reducer.py`; T02,T03 | A,B: JSON round trip, invalid transition rejected, duplicate step/fact not applied, terminal state immutable | D2 recheck passed: reducer tests cover step aggregation, source matching, dedup, normalized history, once-only usage, progress, terminal protection, non-pending initialization and inconsistent tool-result rejection. D2 component chain passed; full AgentLoop integration remains unverified. |
| R02 / Spec §§5–6; Contracts Domain | Planner initializes high-level subgoals, selects one next action from current observation/state, never emits an up-front script | `planner.py`, planner prompt; T05 | A,B: changing observed evidence changes next PlanDecision and subgoal selection without fixed action sequence | D3 component verified: changed observation selects browser versus GitHub, bounded context reaches Planner, invalid/unused parameters fail, and Planner→Router fake integration passes. Authenticated provider run remains unverified. |
| R03 / Spec §11; Contracts retries | DeepSeek via httpx with timeout, usage, one temporary retry and one separate structured-output repair | `llm/deepseek.py`; T04 | A: fake transport shows bounded 200/timeout/429/5xx/invalid JSON attempts, exact usage and safe failure; no key in outputs | D2 fake-transport checks passed. In the current D5 recheck, one bounded real `deepseek-flash` authentication call returned nonempty content and 38/14 provider-reported tokens; complete live research remains unverified. See D5 audit. |
| R04 / Spec §9; Contracts Browser | Seven actions, light/deep observation, stale/semantic element resolution, owned BrowserSession | `adapters/browser_use_adapter.py`; T01 | A,C: fake seven-action dispatch and failures; controlled Chromium start→navigate→observe→extract→close and failure cleanup | D1 fake seven-action paths and controlled five-stage Chromium smoke passed; fake startup and action failure cleanup passed. Click/input/scroll/back/wait are not individually real-browser verified. |
| R05 / Spec §10; Contracts Tools | GitHub REST search/get/releases and strict browser/GitHub routing, no arbitrary API host | `tools/github_tool.py`, `router.py`; T06 | A,B: each valid action yields normalized result; unknown action rejected; fake 404/429/5xx observed without extra calls | D3 recheck: seven browser/three GitHub actions, fixed host, 404/429/5xx/timeout, no-call duplicate navigation/search/repository/release, cancellation and closure tested. Public search/get/releases and Chromium navigate/extract succeeded with sources; long releases keep the JSON list shape. |
| R06 / Spec §§12–13; Contracts Tools/State | Technical, semantic, insufficient information distinguished; normalized URL/query dedup; bounded summary | `evaluator.py`, `context_manager.py`, router; T06,T08,T09 | A,B: technical failure skips semantic call, duplicate causes no tool call, last five traces and 12k current view bound prompt | D3 recheck: four outcomes, provider failure mapping, sourced fact rejection, technical retry eligibility, valid bounded JSON, five action/outcome traces, current DOM/deep events and ToolResult→Evaluator→Reducer pass. Authenticated semantic LLM request remains unverified. |
| R07 / Spec §15; Contracts Limits | Stop on 30 steps, 900s, 40k reported tokens, cancellation, target count, completed goal or five no-progress replans | `agent_loop.py`; T07 | A,B: fake clock/usage produce exactly one correct terminal status, reason and completion level; resources close | D4 recheck: four outcomes and frozen limits pass; unmet explicit count with exhausted subgoals returns `partial/insufficient_info`, while reached hard limits keep their reason. Python 3.12/3.13 full suites, public GitHub Agent-domain run, and Chromium smoke passed. Authenticated provider remains unverified; see D4 audit. |
| R08 / Spec §§8,16; Contracts Report | Every material report finding maps to observed ResearchFact and source URL; unknowns stay unknown | `reporter.py`; T10 | A,B: unsupported claim omitted/rejected; Markdown sources match stored facts; partial report names gaps | D4 recheck: fact-ID, source, and subject-name validation reject unsupported findings even without `subject_kind`; report fallback preserves sourced facts, unknowns, count gaps, and failure reasons. Four user-facing outcomes and public report source were checked; see D4 audit. |
| R09 / Spec §17; Contracts Runtime | Prompt task ID, max two active tasks, queued/running cancel, failure observation, slot/subscriber/resource cleanup | `runtime/task_manager.py`; T11 | A,B: third task waits, cancellation during action reaches one terminal event, failure releases slot, disconnect removes only subscriber | Current D5 recheck passed: two running/one queued in real local HTTP; tests prove distinct Agent instances, isolated cancel, exception terminalization, slot reuse and shutdown recovery as `server_restart`. See current D5 matrix. |
| R10 / Spec §18; Contracts Persistence | SQLite writes task/step/fact/trace; atomic terminal status/event; rollback; restart finalization, timeline/report reconstruction | `backend/services/persistence.py`, `backend/db/`; T12 | B: injected write failure leaves neither half-write; fresh app instance returns persisted timeline/report and finalizes unfinished row without resume | Current D5 recheck passed: atomic terminal/rollback, both fact deduplication entry points, report over 64 KB, restart reconstruction and old-schema rejection verified; original database hash unchanged. |
| R11 / Spec §19; Contracts HTTP/SSE | Exactly six routes with 202/200/404/422/503, cancel semantics, ordered persisted replay then live multi-subscriber SSE, disconnect and terminal close | `backend/api/research.py`, schemas, main; T13 | B: HTTP response fields and ordered event IDs match persisted rows; slow client reconnects; task continues after one disconnect | Current D5 recheck passed: real localhost HTTP/SSE path gives specified codes, matching ordered event IDs, disconnect/reconnect and restart; regression closes cancellation, disconnect/SQLite and concurrent terminal response races. Controlled source is simulated; live provider research remains unverified. |
| R12 / Spec §20; Contracts HTTP | Vue goal, Start, Cancel, status, timeline, sourced report, recent tasks through six routes only | `frontend/`; T14 | B/manual UI: type-check/build pass; user can start, see event/report, cancel and reload recent task; no token in browser payload | `npm run type-check --prefix frontend`, build and demo record; app absent |
| R13 / Spec §22 and Done when | Three to five public, unauthenticated candidate/comparison/change tasks complete reliably | Agent, API, UI; T07,T13,T14 | D: each run records goal, task ID, final state, steps, sources, report, failure reason, browser/client cleanup | `docs/audits/V1_DELIVERY_REPORT.md` plus raw redacted run records; unverified |
| R14 / Spec §21; Benchmark Protocol | Same DeepSeek model/cases/budgets, raw records, deterministic coverage; full-system and browser-only comparisons separate | `benchmark/`; T15 | E: 18 runs for B01–B03 × three arms × two repeats, each with raw status/metrics; no unmeasured improvement percentage | `data/benchmark/` redacted JSON and delivery report; protocol only |

## Current D5 recheck (2026-10-12)

T11–T13 targeted tests: **33 passed**. Affected D4/component tests: **264
passed**. Full offline suites: **294 passed, 1 browser test deselected** on
each of Python 3.12 and 3.13; separately selected Chromium smoke: **1 passed**.
Ruff lint/format, compile, offline lock check and wheel build exited 0. A real
localhost HTTP/SSE user path and one bounded authenticated DeepSeek request
also completed; the report source in that user path came from controlled fake
tools. Two independent read-only reviews found four reproduced and fixed
issues; final read-only rereview found no actionable bugs. D5 is accepted.
Commands, failure-first regressions, request/status/event
records and remaining limits are in `docs/audits/D5_ACCEPTANCE_2026-10-12.md`.

## Execution layers and failure attribution

| Layer | Environment and when | Required scenarios and failure attribution |
| --- | --- | --- |
| A — pure unit | Offline Windows during component work; Linux Python 3.12/3.13 on every CI change | Pydantic validation, legal/illegal transitions, structured parsing/repair, all stop conditions, dedup, context limit and source mapping. Failures are project logic or fixture defects, not external outages. |
| B — fake integration | Offline after D3–D5 boundaries; real asyncio/SQLite temporary database, fake provider/tools/browser | Planner→Router, ToolResult→Evaluator→Reducer, full AgentLoop, API→TaskManager→SQLite, SSE replay/live/multiple clients, cancel, cleanup and restart. Failures identify the responsible boundary before a live run. |
| C — real browser smoke | Opt-in local installed Chromium, controlled loopback page after adapter changes and D7 | Start, navigate, light observe without screenshot, extract expected text, close; force failed navigation/action and assert cleanup. Environmental browser launch errors are recorded as unverified until rerun, never as pass. |
| D — real V1 acceptance | D7, public pages with no login, DeepSeek credential, Chromium and network | Use the fixed B01–B03 prompts as three separately identified V1 full-system acceptance runs, spanning candidate discovery, direct comparison and version/change research. Record goal, task ID, model, final state, steps, source URLs, report, failures and resource closure. These acceptance run IDs are distinct from E's 18 benchmark run IDs. Site/network/provider failures remain failures with attribution. |
| E — benchmark | D7 after D paths, same machine/model/budget and fixed B01–B03 prompts | Two repetitions per case/arm, rotating arm order, raw redacted output including failed attempts. Report full-system vs baseline and browser-only vs baseline separately; unavailable usage is null and may make budget parity unverified. |

## High-risk assertions

- Timeout and 429/5xx: provider makes one technical retry at most, then produces a safe technical failure; usage and error contain no credential. Invalid JSON/schema gets one *separate* repair attempt and never mutates state on final failure.
- Duplicate normalized URL/query: no second tool call; existing sourced fact remains; a bounded replan or stop is externally visible.
- Missing, ambiguous or stale browser element: no click/input reaches the stale target; the result is semantic failure and the loop observes again. Cancellation during an action closes BrowserSession and yields one cancelled terminal event.
- Two active tasks hold both slots; a third waits. An exception or cancellation releases a slot and closes the task's browser, HTTP, database and subscriber resources.
- Failed terminal SQLite transaction rolls back both task status and `task_finished` trace; on restart unfinished rows become partial/failed from persisted facts without resuming. Existing local DB is never cleared automatically.
- SSE replay and live events have ordered unique IDs; multiple subscribers see the same events. A slow queue does not block the task, a reconnect catches up from storage, a disconnect removes one subscriber, and terminal event closes streams.
- Secret sentinels in a fake provider/browser response must not appear in logs, stored traces, SSE, report or benchmark JSON. Browser rejects non-HTTP(S), credentialed, loopback/private/link-local targets and DNS answers resolving to them. A fake redirect to a private final URL returns failure; because the check occurs after navigation, this is **not proof of pre-request network isolation** and public deployment remains out of scope.

## Done-when checklist for D7

Each item requires its own evidence in `docs/audits/V1_DELIVERY_REPORT.md`:

1. Three to five representative real tasks run reliably (R13/D).
2. Planner decisions demonstrably depend on current state (R02/A,B,D).
3. GitHub and browser routing both work (R04,R05/B,C,D).
4. Evaluator separates technical, semantic and insufficient information (R06/A,B).
5. URL and query duplicates are suppressed (R06/A,B).
6. Planner context remains bounded across long histories (R06/A).
7. SSE exposes the Agent timeline (R11/B,D).
8. SQLite reloads timeline and report after restart (R10,R11/B).
9. ResearchReport cites collected sources (R08/A,B,D).
10. Baseline and adaptive raw benchmark runs exist (R14/E).
11. Deterministic core logic has meaningful tests (R01–R11/A,B).
12. README supports basic local startup (T16 command and local demo check).

## Commands and evidence labels

After syncing dependencies, offline: `uv lock --check --offline` and
`uv run --offline --locked pytest -q`; static: `uv run --offline --locked ruff
check adaptive_agent backend benchmark tests`, `uv run --offline --locked ruff
format --check adaptive_agent backend benchmark tests`, and `uv run --offline
--locked python -m compileall -q adaptive_agent backend benchmark tests`.
Real Chromium: `uv run --locked pytest -q -m browser
tests/smoke/test_browser_use_adapter.py`. Frontend after T14:
`npm ci --prefix frontend`, `npm run type-check --prefix frontend`,
`npm run build --prefix frontend`. D/E require their run manifests and raw
records, not a pytest count. Reports must label each as **current passed**,
**current failed**, **historical passed**, **source confirmed**, **planned**, or
**unverified with reason**.

## D1 acceptance evidence (2026-10-09–10, Windows)

**D1: Pass for the requested foundation; V1 remains incomplete.** The
Python 3.12.13 and 3.13.2 checks below were current at the D1 handoff and are
historical relative to the later changeset review. The pre-change
3.12.13 result (`20 passed, 1 deselected`) and 2026-10-08 Day 01 record
(`18 passed`, one browser smoke) are historical baselines only.

| Order | Command | Environment | Exit | D1 result |
| ---: | --- | --- | ---: | --- |
| 1 | `uv run --offline --locked pytest -q tests/unit/test_state.py tests/unit/test_state_reducer.py tests/unit/test_browser_use_adapter.py` | Windows, Python 3.12.13 | 0 | 92 passed |
| 2 | `uv run --locked pytest -q -m browser tests/smoke/test_browser_use_adapter.py` | Windows, Python 3.12.13, local Chromium and loopback HTTP page | 0 | 1 passed |
| 3 | `uv run --offline --locked pytest -q` | Windows, Python 3.12.13 | 0 | 101 passed, 1 browser test deselected |
| 4 | `uv lock --check --offline` | Windows, uv 0.11.28 | 0 | Resolved 282 packages |
| 5 | `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | Windows, locked toolchain | 0 | All checks passed |
| 6 | `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | Windows, locked toolchain | 0 | 54 files already formatted |
| 7 | `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | Windows, Python 3.12.13 | 0 | No error output |
| 8 | `git diff --check --ignore-submodules=all` | Windows, main repository | 0 | No whitespace errors; LF→CRLF advisory warnings only |
| Additional | `uv run --isolated --python 3.13 --offline --locked pytest -q tests/unit/test_state.py tests/unit/test_state_reducer.py tests/unit/test_browser_use_adapter.py tests/unit/test_task_manager.py tests/integration/test_database.py` | Windows, Python 3.13.2 | 0 | 97 passed |

During red→green work, T02 tests first reported 17 failures/23 passes against
the skeleton (including one test setup error corrected before implementation),
the new ORM default test failed on `pending`, and T03 tests failed on the
old reducer signature. A later malformed-URL test failed before its validator
fix. One intermediate Ruff format gate exited 1 on a newly edited error
message; the reducer was formatted and the entire eight-command gate then
reran with exit 0 throughout. No failing test was skipped or removed.

T01's fake tests exercise navigate, click, input_text, scroll, extract,
go_back and wait. The real Chromium test exercises session start, navigate,
light observe (no screenshot), extraction of “Research evidence” from a page
titled “Adaptive Smoke”, rejection of an unsafe navigation, and close
(`adapter._session is None`). Fake startup failure calls `kill`; fake
execution failure and successful paths call `close_session` in `finally`
and confirm cleanup. Real click, input_text, scroll, go_back and wait were not
individually exercised. The checked-out browser-use source exposes the called
session, Tools and Markdown extraction APIs; its Git metadata permission error
still prevents certifying submodule cleanliness.

One post-change Chromium rerun passed but emitted a Windows
`PytestUnraisableExceptionWarning` from asyncio's proactor pipe transport
destructor (`ValueError: I/O operation on closed pipe`). A subsequent
`PYTHONTRACEMALLOC=1` rerun passed without the warning. The adapter's
session-close assertions passed in both runs; the intermittent lower-level
transport warning remains unattributed and is not evidence that every browser
process or pipe was closed.

T02 validates URL syntax and rejects obvious private literal hosts; it does
not establish that a tool actually observed a source. D2 owns these T03
`step_evaluated` behaviors and passing tests: increment exactly one
consecutive step; update the selected subgoal; admit only source-validated
facts without duplicate application; merge normalized visited URLs and search
queries; add prompt/completion usage once; and increment or reset
`consecutive_no_progress_replans` from actual fact/subgoal progress. The D1
reducer validates the payload and step rule, then explicitly raises
`NotImplementedError` for an otherwise valid evaluated step.

## Current changeset follow-up (2026-10-10, Windows)

The adapter review added regression tests for disappearing or stale elements,
unsafe current and observed pages, failed action cleanup of observation state,
and browser error-page classification. After those fixes, the full offline
suite passed on Python 3.12.13 and 3.13.2 with **113 passed, 1 browser test
deselected** on each. The controlled Chromium smoke passed **1 test**. The
locked Ruff check, Ruff format check (54 files), Python compile check, and
`uv lock --check --offline` each exited 0. The separate changeset acceptance
report records findings and remaining limits.

A further current-changeset review added source URL cases for `localhost.` and
`sub.localhost`. The test failed on the accepted worktree and passed after the
source validator rejected those aliases. A `NaN` wait-value check passed before
any adapter edit, confirming the existing 0–10 second guard. Following the URL
fix, locked offline suites again passed on Python 3.12.13 and 3.13.2 with
**113 passed, 1 browser test deselected** each; the controlled Chromium smoke
passed **1 test**. Ruff check, Ruff format check (54 files), and compileall
exited 0. This validates the current changeset's documented D1 foundation,
not full V1 execution.

With read-only access to the nested Git metadata,
`git -C browser-use status --short --untracked-files=all` returned no changes
and `rev-parse HEAD` matched the tracked gitlink `7be96ed8`. This is new
evidence; the earlier D1 and predevelopment reports correctly recorded that
their restricted checks could not certify the submodule at that time.

## Historical D2 offline exit evidence (2026-10-10, Windows)

The restricted sandbox blocked `uv` interpreter queries and asyncio loop
startup. These commands were run in the approved regular execution environment
against the earlier D2 working tree after formatting. They precede the
independent recheck below. A live credential or public research task was not
used.

| Command | Exit | Historical result |
| --- | ---: | --- |
| `uv run --offline --locked pytest -q tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py` | 0 | 67 passed; reducer aggregation, provider fake-transport paths and dynamic Planner checks. |
| `uv run --offline --locked pytest -q` | 0 | 135 passed, 1 opt-in browser test deselected. |
| `uv lock --check --offline` | 0 | Resolved 282 packages. |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0 | All checks passed. |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0 | 56 files already formatted. |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0 | No error output. |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | No whitespace errors; LF→CRLF advisories only. |

The first D2 static gate reported three Ruff errors and seven files requiring
formatting. Safe import correction and formatting were applied only to D2
files; all six commands above were rerun afterward. The D2 evidence is offline
unit/fake-backed verification, not D7 real research acceptance or benchmark
evidence.

## D2 scoped recheck evidence (2026-10-10, Windows)

The earlier 67/135 counts above are historical D2 handoff results, not the
final recheck. The following commands were rerun after scoped fixes in the
approved regular execution environment because the restricted sandbox denied
`uv` interpreter access. The full stage record and traceability table are in
`docs/audits/D2_ACCEPTANCE_2026-10-10.md`.

| Command | Exit | Actual result |
| --- | ---: | --- |
| `.venv/Scripts/python.exe -m pytest -q tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py tests/unit/test_config.py tests/integration/test_d2_component_flow.py` | 0 | 88 passed. |
| `uv run --isolated --python 3.12 --offline --locked pytest -q` | 0 | 154 passed, 1 browser test deselected. |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | 0 | 154 passed, 1 browser test deselected. |
| `uv run --python 3.12 --offline --locked pytest -q tests/smoke/test_app.py tests/integration/test_d2_component_flow.py` | 0 | 3 passed; API placeholder behavior and D2 component chain only. |
| `uv lock --check --offline` | 0 | Resolved 282 packages. |
| `.venv/Scripts/ruff.exe check adaptive_agent backend benchmark tests` | 0 | All checks passed. |
| `.venv/Scripts/ruff.exe format --check adaptive_agent backend benchmark tests` | 0 | 57 files already formatted. |
| `.venv/Scripts/python.exe -m compileall -q adaptive_agent backend benchmark tests` | 0 | No errors. |
| `uv build --offline --wheel` | 0 | Built `adaptive_browser_agent-0.1.0-py3-none-any.whl`. |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | No whitespace errors; line-ending advisories only. |

Python type checking is not configured; `frontend/package.json`, API
integration tests and E2E tests are absent. No DeepSeek key or `.env` was
available, so an authenticated request was not run. These gaps are not passes.

## D3 final component recheck (2026-10-10, Windows)

The D3 acceptance record in `docs/audits/D3_ACCEPTANCE_2026-10-10.md` maps
T05/T06/T08/T09 to implementation, red-to-green regressions, two verified
read-only review sessions, public component calls, and business scenarios.
The final D3 targeted suite exited 0 with **122 passed**. The locked offline
full suites exited 0 on Python 3.12 and 3.13 with **213 passed, 1 browser test
deselected** each. The separately selected API placeholder, fake component and
controlled Chromium cases exited 0 with **4 passed**. `uv lock --check
--offline`, Ruff lint, Ruff format (63 files), compileall, and offline wheel
build each exited 0. No type checker, frontend build, full API integration, or
research E2E command is configured. An authenticated DeepSeek request was not
run. T05/T06/T08/T09 and the bounded D3 component gate passed; complete V1
business execution remains unverified.
