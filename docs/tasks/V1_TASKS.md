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
| T05 / D2–D3 / P0 / 4h | T02,T04; `adaptive_agent/planner.py`, `adaptive_agent/prompts/planner.py`, `tests/unit/test_planner.py` | Initialize measurable subgoals, then choose exactly one action using current state and observation; no up-front script. | `uv run --offline --locked pytest -q tests/unit/test_planner.py`; changed state/observation changes the next decision; bad output fails safely. | Status: `verified` for D3 component scope. Bounded context drives one decision, strict parameters reject unused fields, and Planner→Router fake integration covers both tool paths. Authenticated live Planner remains unverified. |
| T06 / D3 / P0 / 5h | T01,T02; `adaptive_agent/tools/router.py`, `adaptive_agent/tools/github_tool.py`, router/GitHub tests | Strictly route seven browser and three GitHub actions; normalize ToolResult, suppress equivalent URL/query before calls, use fixed GitHub REST host. | `uv run --offline --locked pytest -q tests/unit/test_tool_router.py tests/unit/test_github_tool.py`; fake endpoints show dispatch, no-call duplicates, 404/429/5xx and invalid action errors. | Status: `verified` for D3 component scope. Seven-action fake dispatch, three GitHub endpoints, dedup, error mapping and cleanup pass; public GitHub and browser component paths succeeded. No tool-local retry loop. |
| T08 / D3–D4 / P0 / 4h | T02,T04,T06; `adaptive_agent/evaluator.py`, `adaptive_agent/prompts/evaluator.py`, evaluator tests | Technical evaluation precedes optional semantic LLM comparison; distinguish `none`, `technical`, `semantic`, `insufficient_info`; validate sources. | `uv run --offline --locked pytest -q tests/unit/test_evaluator.py`; technical error avoids semantic call, unsupported fact excluded. | Status: `verified` for D3 offline gate. Four outcomes, technical short circuit, evidence/source rejection and ToolResult→Evaluator→Reducer integration pass. Authenticated semantic LLM call remains unverified. |
| T09 / D3 / P0 / 2h | T02,T03; `adaptive_agent/context_manager.py`, context tests | Deterministic history summary, last five traces and 12,000-character bounded current view with visible truncation. | `uv run --offline --locked pytest -q tests/unit/test_context_manager.py`; long synthetic history does not grow the prompt unboundedly. | Status: `verified` for D3 offline gate. Source, completed subgoals and failed-action clues survive long histories; current view and Planner prompt remain bounded with visible truncation. |
| T07 / D4 / P0 / 6h | T03,T05,T06,T08,T09,T10; `adaptive_agent/agent_loop.py`, `tests/integration/test_agent_loop.py` | Bounded observe→decide→act→evaluate→reduce→report loop; 30 steps/900s/40k tokens/five non-progress replans, target count, goal and cancellation stops. | `uv run --offline --locked pytest -q tests/integration/test_agent_loop.py`; fake full/partial/failed/cancel paths each end once with reason and resource cleanup. | Status: `verified` at D4 Agent-domain boundary after fresh recheck. An unmet count with no unfinished subgoal now stops as `partial/insufficient_info`; hard limits retain precedence. Both Python versions, public GitHub Agent-domain run, Chromium smoke, and independent read-only review are recorded in `docs/audits/D4_ACCEPTANCE_2026-10-11.md`. Authenticated DeepSeek and D5 API remain unverified. |
| T10 / D4 / P0 / 3h | T02,T03; `adaptive_agent/reporter.py`, `adaptive_agent/prompts/reporter.py`, reporter tests | Generate general-purpose sourced ResearchReport after stop; each material finding maps to collected facts and URLs, partial gaps remain visible. | `uv run --offline --locked pytest -q tests/unit/test_reporter.py`; unsupported claims are rejected/omitted, not rendered as facts. | Status: `verified` at D4 Agent-domain boundary after fresh recheck. Unsupported subject labels without `subject_kind` are rejected; the report retains sourced facts, explicit count gaps and the stop reason. See D4 audit. |
| T11 / D5 / P0 / 5h | T07,T12 interface; `adaptive_agent/runtime/task_manager.py`, task manager tests | Two active tasks, isolated resources, bounded subscriber queues, queued/running cancellation, exception observation and shutdown cleanup. | `uv run --offline --locked pytest -q tests/unit/test_task_manager.py`; third task waits, failure frees slot, disconnect removes one subscriber. | Current D5 recheck passed: two running/one queued in real local HTTP path; tests cover exception terminalization, slot reuse, distinct Agent instances, cancellation isolation, shutdown and subscribers. Shutdown interruption recovers as `server_restart` with one terminal event. See the current matrix in `docs/audits/D5_ACCEPTANCE_2026-10-12.md`. |
| T12 / D5 / P0 / 5h | T02,T03; `backend/services/persistence.py`, `backend/db/`, persistence tests | Persist task/step/fact/trace; atomically commit terminal status and event; reconstruct timeline/report and finalize unfinished rows after restart without deleting DB. | `uv run --offline --locked pytest -q tests/integration/test_database.py tests/integration/test_persistence.py`; rollback leaves neither half-write; new app instance reloads terminal output. | Current D5 recheck passed: transaction rollback, unique terminal trace, both fact-save deduplication paths, recovery and sourced report reload, including a sourced terminal report over 64 KB. Incompatible original DB hash unchanged; isolated copy reports missing columns. |
| T13 / D5 / P0 / 7h | T11,T12; `backend/main.py`, `backend/api/research.py`, `backend/schemas/research.py`, API/SSE tests | Wire exactly six Spec routes through runtime/service; 202/200/404/422/503, idempotent cancel, persisted replay then live SSE, multi-subscriber, terminal close. | `uv run --offline --locked pytest -q tests/integration/test_research_api.py tests/integration/test_sse.py`; HTTP responses, ordered IDs, reconnect, disconnect and restart are observed. | Current D5 recheck passed: real localhost HTTP/SSE path covers six routes, replay/live/reconnect/restart and 202/200/404/422/503; disconnect cleanup, cancellation race and concurrent terminal response have failure-first regressions. One bounded real DeepSeek authentication call passed; successful live research remains unverified. |
| T14 / D6 / P0 / 5h | T13; `frontend/`, frontend API and view tests | Vue 3/TypeScript goal input, Start/Cancel, status, timeline, sourced report and recent tasks consuming only six routes; no credentials in UI. | `npm ci --prefix frontend`; `npm run type-check --prefix frontend`; `npm run test --prefix frontend`; `npm run build --prefix frontend`; inspect keyboard/demo path and API errors. | 2026-10-14 本地受控伪造验收：20 个交互测试、完整浏览器路径、部分报告未完成事项、初始轨迹失败仍开启 SSE、生命周期事件不误记动作步号、排队到运行轮询同步、断线自动恢复、终态详情有界重试、创建任务不等待列表响应及刷新重连有本次证据。真实 DeepSeek 研究属于 D7。见 D6 复核记录。 |
| T15 / D6 / P1 / 5h | T07,T10,T13; `benchmark/`, benchmark tests | Run fixed B01–B03 with same DeepSeek model/budgets in baseline, adaptive full and adaptive browser-only arms; keep 18 redacted raw records and deterministic scorer. | `uv run --offline --locked pytest -q tests/unit/test_benchmark.py`; opt-in real runs per `docs/benchmark/BENCHMARK_PROTOCOL.md`; compare arms separately. | 2026-10-15 二十五次完整独立只读审查共六十一项发现经复现和修复，最后两处修复的限定范围只读复审无阻断，并恢复 baseline 上游默认 judge；85 个基准测试通过，受控伪造 18 条记录三组各 6、两次失败保留且脱敏；B02 文档首页和 B03 未完成段不作具体字段来源、baseline 超时步骤及 adaptive 时限前已完成动作均保留访问和步骤、GitLab issue 不作第二项目、B03 最新版与官方 tag 对齐、大写 URL 脱敏均有回归。轨迹仅留安全元数据，记录主仓库及上游工作区指纹，达到 token 阈值后跳过额外 judge 请求，30 步耗尽或未执行 done 均记录失败。baseline token parity 为 mismatched；真实 18 次与来源核对属于 D7。 |
| T16 / D6–D7 / P0 / 4h | All applicable tasks; `tests/`, `.github/workflows/ci.yml`, `README.md` | Keep Python 3.12/3.13 offline checks truthful, add required frontend locked install, type-check, tests and build, document setup, smoke, live acceptance and benchmark. | `uv lock --check --offline`; 3.12/3.13 全量离线 pytest；Ruff check/format check/compileall；四条 npm 命令和实际 Actions 结果。 | 2026-10-15 本地 Node 23 锁定安装、类型检查、20 个交互测试、构建均退出 0；最后修复后 Python 3.12/3.13 各 383 passed/1 deselected，Ruff、格式、编译、锁检查退出 0。CI 指定 Node 22；远端 Actions 未验证。见 D6 复核记录。 |

## D5 outcome (2026-10-12)

The current independent D5 recheck has 33 targeted tests passed, 264 affected
D4/unit tests passed, and 294 passed with one browser test deselected on each
of Python 3.12 and 3.13. The selected Chromium smoke passed. A real localhost
service backed by isolated SQLite passed the HTTP/SSE user path and restart;
the original incompatible database hash remained unchanged. A bounded real
DeepSeek authentication request succeeded, while successful live research is
unverified. Two independent read-only reviews found four reproducible
issues, fixed with failing-then-passing regressions; a final read-only review
found no actionable bugs. D5 is **accepted**. Exact evidence and the
historical prior result are separated in `docs/audits/D5_ACCEPTANCE_2026-10-12.md`.
D6 frontend and D7 acceptance are outside this decision.

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

## D3 component outcome (2026-10-10)

The first implementation checkpoint had 56 targeted and 200 full offline tests
passing, but lacked independent review, so that checkpoint did not exit D3.
The scoped recheck reproduced and repaired duplicate GitHub resource requests,
oversized release result shape, and nine independently reviewed interface and
context defects. Final D3 plus Reducer tests passed **122**; Python 3.12 and
3.13 full offline suites each passed **213**, with one opt-in browser test
deselected. Public GitHub and Chromium component paths, including deep browser
context, returned sourced results and closed their owned sessions/clients.
Native Codex review twice reported an effective `read-only` sandbox; all nine
findings were independently reproduced and fixed with red-to-green tests.
**T05, T06, T08, T09 and the bounded D3 exit gate pass.** The live Windows
browser run emitted an intermittent proactor pipe-destructor warning despite
session reset; OS pipe closure remains unverified. See
`docs/audits/D3_ACCEPTANCE_2026-10-10.md` for exact commands, scenarios and
remaining D4/V1 limits.

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
