# V1 Implementation Readiness Audit

Audit date: 2026-10-08 (Asia/Shanghai). Scope: project-owned V1 code, tests,
configuration, docs, and the checked-out browser-use API surface. This is a
readiness audit of the initialization skeleton, not a V1 acceptance result.

## Repository reality and evidence levels

- **Source Confirmed:** `main` tracks `origin/main` with a clean worktree;
  current project commit is `e72572b6`. The browser-use gitlink is
  `7be96ed8` and its `pyproject.toml` declares version `0.13.10`.
- **Test Verified:** `uv run --offline --frozen pytest -q` passed 13 tests;
  `uv run ruff check adaptive_agent backend benchmark tests`,
  `uv run ruff format --check adaptive_agent backend benchmark tests`, and
  `uv lock --check --offline` passed on this date. These checks cover the
  skeleton, not live research.
- **Source Confirmed:** `.env.example`, `.gitignore`, `uv.lock`, and README
  exist. `frontend/` contains only `.gitkeep`; `.github/workflows/` does not
  exist. The requested `.agent/`, `.agents/`, and `.codex/` files do not exist
  in this checkout. Do not regenerate their Skills or Subagents.
- **Source Confirmed:** the ignored local SQLite file has the four expected
  tables and zero rows. It is not a migration test and must not be deleted
  automatically.
- **Unverified:** real Chromium action flow, external DeepSeek/GitHub calls,
  SSE delivery during a running task, report reconstruction, representative
  research tasks, and benchmark outcomes.

## Findings

Severity: P0 blocks V1 correctness or delivery; P1 is a significant
reliability/maintenance risk; P2 is a later improvement. Paths and line numbers
refer to the pre-remediation skeleton.

| ID | Severity | Problem and trigger | Code evidence | Impact | Recommendation / level |
| --- | --- | --- | --- | --- | --- |
| A-01 | P0 | Starting research cannot execute the Agent loop. | `adaptive_agent/agent_loop.py:31-34` raises `NotImplementedError`. | No Observe→Plan→Act→Evaluate→Report path. | Implement a bounded loop after contracts; Source Confirmed. |
| A-02 | P0 | Every browser action is unimplemented. | `adaptive_agent/adapters/browser_use_adapter.py:56-58`; `tests/unit/test_browser_use_adapter.py:69` expects that failure. | Day 01 is not verified despite lifecycle tests. | Implement the seven declared actions through checked-out upstream APIs, then run real-browser smoke; Source Confirmed. |
| A-03 | P0 | Planning, evaluation, context, report, and DeepSeek requests are placeholders. | `adaptive_agent/planner.py:12-15`, `evaluator.py:10-38`, `context_manager.py:13-19`, `reporter.py:7-12`, `llm/deepseek.py:20-23`. | Research cannot learn, stop semantically, or produce a sourced report. | Implement in dependency order with fake-backed tests; Source Confirmed. |
| A-04 | P0 | GitHub tool and persistence methods cannot execute. | `adaptive_agent/tools/github_tool.py:20-23`; `backend/services/persistence.py:19-58`. | Structured repository research and history display fail. | Implement narrow GitHub operations and SQLite round trips; Source Confirmed. |
| A-05 | P0 | Public API routes are placeholders although six paths are registered. | `backend/api/research.py:26-64`: create/get/cancel return 501, events is empty, list/traces return empty. | No usable API or SSE timeline. | Wire routes through TaskManager and persistence; Source Confirmed. |
| A-06 | P0 | Required UI and benchmark runners are absent. | `frontend/.gitkeep`; `benchmark/baseline.py:4-5`, `adaptive.py:4-5`. | V1 cannot be demonstrated or compared. | Build the minimal Vue view and fixed-case runners after the backend path; Source Confirmed. |
| A-07 | P0 | Stop, partial-result, restart, and budget semantics are not decision complete. | `docs/specs/V1_SPEC.md:149-155,164-176`; `adaptive_agent/state.py:36-42,69-86`; `backend/config.py:27-37`. | Long tasks may stop incorrectly or remain `running` after restart. | Define terminal mapping, separate stop reason/completion, and bound all loops; Source Confirmed. Numeric limits beyond existing `max_steps=30` are Proposed. |
| A-08 | P1 | Requested contract differs from code: `queued/partial`, `event_id/event_type`, `facts`, and Finding fields. | `adaptive_agent/state.py:36-42,100-124`; `events.py:11-19`; `docs/specs/V1_SPEC.md:59-72,117-124`. | Docs, parsed LLM output, reducer, persistence, and clients could diverge. | Treat latest user-approved fields as target; migrate model and consumers together; Source Confirmed. |
| A-09 | P1 | Event-to-state ownership is only documented, not implemented. | `adaptive_agent/state_reducer.py:7-16` accepts decision/evaluation rather than AgentEvent; `events.py:11-19` has an open string type. | Important state changes can bypass one traceable path. | Define minimal event vocabulary and pure reducer; Source Confirmed. |
| A-10 | P1 | Task event queue has one consumer and no terminal/bounded lifecycle; task exceptions are not consumed. | `adaptive_agent/runtime/task_manager.py:18-24,44-75`. | Competing SSE clients can split events, memory can grow, and failures may leave stale API state. | Use per-subscriber delivery or persisted replay; add failure/shutdown tests; Source Confirmed. |
| A-11 | P1 | Browser startup may leak a partially started session: ownership is assigned only after `start()` succeeds. | `adaptive_agent/adapters/browser_use_adapter.py:39-44`. | Failed startup can leave Chromium/CDP resources. | Kill the local session in the startup exception path; add regression coverage; Source Confirmed. |
| A-12 | P1 | URL and prompt-injection boundaries are not enforced by the project adapter. | `adaptive_agent/adapters/browser_use_adapter.py:21-27,56-58`; upstream `browser_use/browser/watchdogs/security_watchdog.py:28-65,213-245` allows unrestricted URLs when domain lists are unset. | Untrusted page instructions and unsafe destinations could affect a public service. | Validate inputs and redirects, redact secrets, restrict V1 to a trusted localhost demo; public-deployment protection remains Unverified. |
| A-13 | P1 | Existing tests verify shapes/placeholders but not core failures or resources. | `tests/unit/test_state.py`, `test_task_manager.py`, `test_browser_use_adapter.py`; `tests/smoke/test_app.py:33-50` asserts 501/empty SSE. | A green suite does not imply a working agent. | Add meaningful state, retry, cancel, cleanup, persistence, SSE, and real-browser smoke tests as features land; Test Verified scope limit. |
| A-14 | P1 | No repository CI workflow and no runnable frontend build. | `.github/workflows/` absent; `frontend/.gitkeep`. | Offline checks are not enforced on change. | Add Python CI now; add frontend build gate when the frontend exists; Source Confirmed. |
| A-15 | P1 | Benchmark comparison may attribute GitHub API access to planning quality. | `docs/specs/V1_SPEC.md:206-214`; `benchmark/metrics.py:6-16`. | Mechanism claim would be confounded. | Report full-system and browser-only controlled comparisons separately; Proposed protocol. |
| A-16 | P2 | No configured type checker or deployment package is present. | `pyproject.toml`; README. | Lower static coverage and no public release path. | Keep localhost demo boundary; do not add tools or deployment work solely to fill files; Source Confirmed. |
| A-17 | P2 | Requested plan/agent configuration paths are absent. | `.agent/`, `.agents/`, `.codex/` absent in checkout. | Named ExecPlan/scout workflows cannot be assumed. | Use `docs/tasks/V1_TASKS.md` as the verified task ledger; record absence without recreating those assets; Source Confirmed. |

## Component contract inventory

`TODO` means the class or method exists but its V1 behavior does not. Inputs
and outputs below describe the currently declared Python surface, not a claim
of runtime success.

| Component | Current code | Declared input → output | Dependencies / boundary | Test evidence and missing contract |
| --- | --- | --- | --- | --- |
| AgentLoop | TODO | goal → ResearchReport | Planner, Evaluator, Reducer, ContextManager, Router, Reporter | No loop tests; cancellation/stop/event ownership missing. |
| Planner | partial/TODO | goal → ResearchState; state+context → PlanDecision | Domain models; must not own browser/DB | Only model-shape tests; subgoal initialization missing. |
| Evaluator | TODO | state+decision+observation → EvaluationResult | Domain and future LLM provider | No technical/semantic/error tests. |
| ResearchState | model exists | durable fields → validated model | Domain only | Basic field test; status/invariants incomplete. |
| StateReducer | TODO | state+decision+evaluation → state | Domain; intended AgentEvent input | No reducer tests; signature contradicts event route. |
| ContextManager | TODO | state+recent traces → string | Domain/events | Config window test only; budget undefined. |
| ToolRouter | partial | PlanDecision → dict | BrowserUseAdapter/GitHubTool | No dispatch/error tests; duplicated validation risk. |
| BrowserUseAdapter | lifecycle only | BrowserAction → dict; observe → upstream dataclass | checked-out browser-use `BrowserSession` | Fake lifecycle tests pass; no action/smoke. |
| LLMProvider | TODO | prompt → string | `httpx.AsyncClient` | No request/usage/repair test; usage output missing. |
| TaskManager | partial | task factory/event → task/queue | asyncio primitives | Two unit tests pass; restart/SSE/failure handling absent. |
| Reporter | TODO | ResearchState → ResearchReport | Domain facts | No source validation test. |
| Persistence | ORM exists; service TODO | task/step/fact/trace CRUD | SQLAlchemy AsyncSession | Table creation test passes; no data round trip. |
| FastAPI | route stubs | six routes → placeholder schemas/SSE | intended TaskManager/service | Route registration tests pass; real HTTP behavior absent. |
| SSE | empty stream | task ID → StreamingResponse | intended event persistence/runtime | No events, replay, disconnect, or termination tests. |
| Frontend | absent | goal/status/timeline/report/recent tasks | intended six APIs | No package or build. |
| Benchmark | metrics model only | case ID → TODO runner | browser-use baseline/AgentLoop | Metrics shape test only; cases and protocol absent. |

There is no observed reverse import from browser-use into project code. The
current router delegates rather than replans; the evaluator is one service;
and ResearchState contains no runtime objects. These are source observations,
not proof of future integrated behavior.

## Spec conflicts and unresolved verification

- The Spec lists `PlanDecision.subgoal`, while the Pydantic model already uses
  `subgoal_id`. The approved target is `subgoal_id`.
- The Spec says `EvaluationResult.new_facts`; the approved target is `facts`.
  Current tests assert `new_facts`, so they must migrate with the model.
- The Spec says runtime LLM semantic evaluation is conditional and Benchmark
  LLM-as-Judge is excluded. These are distinct uses and are not contradictory.
- Upstream `BrowserSession.start()`, `kill()`, `get_browser_state_summary()`,
  `navigate_to()`, `get_current_page()`, and `get_element_by_index()` exist in
  the checked-out source. This establishes API availability, not real-browser
  compatibility of the adapter.
- No live browser, DeepSeek, GitHub, representative task, or baseline run was
  executed for this audit. No improvement percentage can be reported.

Day 01 remediation after this readiness snapshot: T01 now has seven action
dispatches, startup failure cleanup, URL input checks, five adapter unit
tests, and a real Chromium smoke covering start/navigation/observation/
extraction/close. Six adapter unit tests and that smoke passed; see
`docs/testing/V1_TEST_MATRIX.md`.
The remaining P0 findings still block V1 end-to-end delivery.
