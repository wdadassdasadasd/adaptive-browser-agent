# D4 Agent Loop and Reporter acceptance — 2026-10-11

The final section, **Fresh D4 recheck**, supersedes the earlier uncommitted
checkpoint below. Earlier test counts and Git statements are historical.

## 00 — Scope and baseline

Scope: T07 Agent Loop and T10 Reporter at the Agent-domain entry point. D5
TaskManager/API/persistence/SSE, D6 frontend, and D7 end-to-end acceptance are
outside this decision. Spec §8, §15–16 and V1 Contracts govern behavior.

At entry, `main` was at `01be22622353e8b5ccc700d04395f98819088442` and
`git -c submodule.recurse=false status --short --branch --ignore-submodules=all`
showed no project modifications. The normal recursive submodule status/diff
could not read `.git/modules/browser-use` (`Permission denied`); no upstream
files were edited. Work stayed in the occupied checkout as requested. No
commit, push, PR, deployment, or external write was performed.

| Requirement | Implementation | D4 decision |
| --- | --- | --- |
| T07 dynamic one-action loop; four outcomes; budgets; cleanup | `adaptive_agent/agent_loop.py`, `goal_count.py`, `state_reducer.py`, provider budget call | **Pass at Agent-domain boundary.** Offline state/usage/cancellation/limits tests and public-source run pass. Authenticated provider and D5 runtime remain unverified. |
| T10 grounded report, unknowns, fallback | `adaptive_agent/reporter.py`, `prompts/reporter.py`, subject fields and evaluator check | **Pass at Agent-domain boundary.** Fact-ID/name/source validation, conservative fallback, and explicit count gaps pass; public report cites the visited source. |

## 01–02 and 06 — Red/green and final checks

Behavior tests were added before the corresponding fixes. Red results included
the missing budget allowance and refusal mapping (2 failures), unmet explicit
count incorrectly returning `goal_satisfied` (1), reused fact ID accepted (1),
Chinese embedded subject and `Find me three projects` missed (2), cancellation
not interrupting a hanging tool (1), missing cleanup timeout (1), and missing
requested-count gap in reports (2). Each passed after repair. A separate
cross-subgoal repeated-action regression passed after the signature fix. No
failing assertion was removed or skipped.

The penultimate format check returned exit 1 for one new assertion at
`tests/integration/test_agent_loop.py:382`. `ruff format` changed that line;
the final `ruff format --check` returned exit 0 with 69 files formatted.

The first restricted-sandbox `uv run --offline --locked pytest ...` attempt
could not start because interpreter/cache access returned `os error 5`. The
commands below ran in the approved executable environment. Exit codes are
from the final run after code repairs.

| Actual command | Exit | Raw result |
| --- | ---: | --- |
| `uv run --offline --locked pytest -q tests/unit/test_reporter.py tests/integration/test_agent_loop.py tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py tests/unit/test_tool_router.py tests/unit/test_github_tool.py tests/unit/test_evaluator.py tests/unit/test_context_manager.py tests/integration/test_d2_component_flow.py tests/integration/test_d3_component_flow.py` | 0 | 187 passed in 2.28s; D4 focus plus D3/D2 dependencies |
| `uv run --isolated --python 3.12 --offline --locked pytest -q` | 0 | 262 passed, 1 deselected in 18.26s |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | 0 | 262 passed, 1 deselected in 12.63s |
| `uv lock --check --offline` | 0 | Resolved 282 packages in 2ms |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0 | 69 files already formatted |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0 | No errors |
| `uv build --offline --wheel` | 0 | Built `dist/adaptive_browser_agent-0.1.0-py3-none-any.whl` |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | No whitespace errors; LF→CRLF advisories |

One browser-marked smoke test remains deselected by the default offline suite;
the prior D3 acceptance includes the explicit browser run. Python type
checking is **未配置**. No D5 API or frontend build was treated as a D4 gate.

## 03 — Controlled real-source execution

After the final Agent-domain changes,
`uv run --offline --locked python -m tests.smoke.d4_agent_domain` exited **0**.
Input goal: **Find one project: FastAPI's official repository**. The controlled
provider selected one `get_repository("fastapi/fastapi")` action; the real
`GitHubTool` requested the public, login-free
`https://api.github.com/repos/fastapi/fastapi`. The Evaluator admitted one
fact only after matching `fastapi/fastapi` in the returned tool content and
matching its source URL. Final result was `completed/full/target_count`, one
step, one `task_finished` event, with the same URL in the fact and report.
The provider call order was `InitialSubgoals`, `PlanDecision`,
`EvaluationResult`, `ReportDraft`. Browser close, owned GitHub HTTP client
close, and provider close were all `true`. Reported fake usage was 40 input
and 20 output tokens; **this is controlled test usage, not a DeepSeek call**.

An earlier controlled Chromium Agent-domain run navigated to and extracted
`https://fastapi.tiangolo.com/`, then completed `target_count` in two steps
with that official URL in the report. The browser session was `None` after
close; GitHub and provider closed. Browser-use logged a page-readiness timeout
warning before successful extraction, and Windows occasionally emitted an
asyncio proactor pipe destructor warning after process exit. OS-level pipe
closure remains unverified. No `.env` or `DEEPSEEK_API_KEY` was available;
authenticated DeepSeek behavior and actual provider token usage remain
**unverified**.

## 04 — Independent read-only review

Native `codex -s read-only -a never --strict-config review --uncommitted`
ran against the D4 diff. Its startup reported `sandbox: read-only`,
`approval: never`, session `01a12974-06b2-7812-9099-9d99e7ecacad`; the
earlier review session was `01a12962-c0b2-7fb3-930f-2e6aab956d23` with
the same effective mode. The reviewer could not use uv cache in its read-only
environment but ran `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`
for the focused scope: 77 passed. Main-agent final checks above supersede
that snapshot. Both reviews supplied file/line evidence; the root verified
findings with failing regressions before fixes.

| Finding and reviewed line | Verification and repair |
| --- | --- |
| Cancellation during cleanup could bypass finalization, `agent_loop.py:283–286` (earlier snapshot) | Shielded bounded close; external cancellation test asserts one terminal event and all closes. |
| Unexpected execution error after facts was mislabeled partial, `agent_loop.py:367–370` (earlier snapshot) | `_terminal_outcome` maps execution/cleanup errors to failed; regression asserts reason and report. |
| Singular `repository` count missed, `goal_count.py:43–45` | Added form and parser regression. |
| `FastAPI2` evidence could count as `FastAPI`, `evaluator.py:129–133` | Complete-name matcher shared by Evaluator and count; both regressions pass. |
| In-flight cancellation waited for wall limit, `agent_loop.py:188–194` | Race work against cancellation event; hanging-tool regression verifies prompt `cancelled/user_cancelled`. |
| Hung close prevented terminal state, `agent_loop.py:308–313` | Bounded cleanup attempt; timeout yields `failed/cleanup_error`; no claim that a hung external resource closed. |
| Chinese subject embedded in prose rejected, `goal_count.py:151–159` | Literal complete Chinese name is accepted in prose; ASCII name boundaries remain strict. |
| `Find me three projects` ignored, `goal_count.py:125–128` | Recognize common `me` request wording; keep `Python 3 projects` ambiguity suppression. |
| Colliding model fact IDs omitted evidence, `reporter.py:43` | Reducer rejects a reused ID for different evidence before report generation. |
| Same browser question for another subgoal suppressed, `agent_loop.py:231–238` | Add subgoal ID to failed-action signature; two-subgoal regression observes two real tool calls. |

Root verification also found that all initialized subgoals could be complete
while an explicit object count was still unmet; a red regression exposed
`goal_satisfied` after one of two requested projects. The loop now requires
the explicit count, and the report states the requested and verified counts.
One final red regression also showed that a cancellation signal received
during provider closure could leave `completed`; the loop now checks the
signal before emitting the terminal event and returns `cancelled`.

## 05 — User-facing acceptance

| Goal and expectation | Observed result and difference |
| --- | --- |
| Find one FastAPI repository: answer with visited source | Public GitHub action produced one verified identity, `completed/full/target_count`, and the report cited exactly the visited API URL. No difference at D4 boundary. |
| Find two projects when only one is sourced: show gap | Controlled partial path stops at `max_steps`; report retains the one sourced fact and says `Requested 2 project(s); verified 1.` |
| Tool/model failure without facts: explain failure | Controlled failure produces `failed/none`, no invented finding, and a readable stop reason. |
| Cancel during a blocked action: stop and clean up | Cancellation signal interrupts the blocked tool, produces `cancelled/user_cancelled` once, and closes normal resources. |

## Remaining limits and Git delivery state

The 40,000-token request cap is enforced for the real DeepSeek client by
conservative prompt allowance and `max_tokens`; usage returned on successful
and known failed calls is accumulated. A generic injected provider without a
budget-aware method can exceed the limit within one response, and unavailable
usage from a failed remote request cannot be reconstructed. Cleanup has a
separate bounded grace period; a hanging external close is reported as
`cleanup_error`, so actual closure of that degraded resource cannot be
asserted. D5 must wire `AgentRunResult` into runtime/API/persistence/SSE; D6
and D7 acceptance remain open. No real DeepSeek credential or call was used.

Final Git status is `main...origin/main` with D4 source, tests, Spec,
Contracts, task matrix, test matrix, and this audit modified or untracked;
index remains empty. No commit or push was made.

## Fresh D4 recheck after requested independent review

Baseline remained `01be22622353e8b5ccc700d04395f98819088442` on `main`.
Only the D4 source, tests, Spec, Contracts, task/test matrix, and this audit
were modified or untracked; the index was empty at entry. Normal recursive
Git status still could not read `.git/modules/browser-use` (`Permission
denied`), so status checks used `--ignore-submodules=all`. The gitlink remained
`7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`; upstream files were not
changed. The initial restricted `uv lock --check --offline` returned exit 1
(`Failed to query Python interpreter: os error 5`) even with a workspace uv
cache. The approved executable environment returned exit 0. A restricted
direct Agent run stalled before entering Agent code: a Python traceback showed
Windows asyncio blocked in `_fallback_socketpair` during event-loop creation.
The same controlled run exited 0 in the approved environment.

### Requirement → code → current test → evidence

| Requirement | Code | Current test or probe | Decision |
| --- | --- | --- | --- |
| One action per observe/plan/execute/evaluate/reduce iteration; bounded technical retry | `agent_loop.py`, Planner, Router, Evaluator, Reducer | `test_agent_loop.py`, D3 component tests | **T07 pass.** The focused suite passed 196 tests; no repeated semantic tool call. |
| 30 steps, 900 seconds, 40,000 reported input plus output tokens, five no-progress replans | `agent_loop.py`, `llm/deepseek.py` | Frozen-limit, fake-clock, fake-usage, budgeted Chinese prompt tests | **T07 pass.** Both full Python suites passed; actual DeepSeek provider usage remains unverified without a credential. |
| Explicit count, goal, cancellation, terminal mapping once | `agent_loop.py`, `goal_count.py`, `state_reducer.py` | Four direct outcomes, exhausted-subgoal count regression, terminal-event assertions | **T07 pass.** Unmet count stops `partial/insufficient_info`; a reached hard limit keeps its reason. |
| Browser, GitHub HTTP, and provider cleanup | `agent_loop.py`, `browser_use_adapter.py`, `github_tool.py` | Cancellation/error/timeout integration tests; public GitHub run; Chromium smoke | **T07 pass at Agent-domain boundary.** Normal close flags and adapter session closure were observed. A timed-out external close cannot be proven closed. |
| Findings grounded in admitted facts and observed URLs; unknowns explicit | `evaluator.py`, `reporter.py`, `state_reducer.py` | Subject-without-kind regression, Reporter tests, four direct reports, public source run | **T10 pass.** Unsupported subject labels are rejected; partial and failed reports state gaps without invented findings. |

The independent review ran `codex -s read-only -a never --strict-config review
--uncommitted` against the D4 working-tree diff. Its startup reported
`sandbox: read-only`, `approval: never`, session
`01a12b5a-1141-73a1-84bb-b23a6a160f15`; exit was 0. The first sandboxed
startup failed before review because it could not open Codex's local state DB.
The reviewer identified three issues with file/line evidence:

| Finding | Reproduction before repair | Repair and result |
| --- | --- | --- |
| `agent_loop.py:181–189`: completed subgoals with unmet count fell into a second invalid plan and `failed/execution_error` | `test_unmet_count_with_no_unfinished_subgoal_stops_as_partial` failed | Stop `partial/insufficient_info` after hard limits; the new test and existing `max_steps` priority test pass. |
| `llm/deepseek.py:126–132`: escaped JSON bytes prematurely rejected a Chinese prompt | `test_budgeted_chinese_prompt_uses_utf8_request_size` failed with `LLMError(kind=budget)` before HTTP | Bound the UTF-8 JSON request without ASCII escapes; fake transport receives one capped request and the test passes. |
| `evaluator.py:131–136`: unsupported `subject` passed when `subject_kind` was absent | `test_uncounted_subject_must_also_appear_in_observed_evidence` admitted the fact | Check every supplied subject against observed evidence; the test passes. |

The three new regressions first produced **3 failed**. After the fixes they
produced **3 passed**. A first Python 3.12 full rerun exposed the existing
hard-limit precedence assertion (**1 failed, 264 passed, 1 deselected**);
moving the exhausted-subgoal check after hard limits made both competing
tests pass. No assertion was removed or skipped.

### Current commands and results

| Command | Exit | Observed result |
| --- | ---: | --- |
| `uv run --offline --locked pytest -q tests/unit/test_reporter.py tests/integration/test_agent_loop.py tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py tests/unit/test_tool_router.py tests/unit/test_github_tool.py tests/unit/test_evaluator.py tests/unit/test_context_manager.py tests/integration/test_d2_component_flow.py tests/integration/test_d3_component_flow.py tests/unit/test_goal_count.py tests/unit/test_loop_usage.py` | 0 | 196 passed |
| `uv run --isolated --python 3.12 --offline --locked pytest -q` | 0 | 265 passed, 1 browser test deselected |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | 0 | 265 passed, 1 browser test deselected |
| `uv lock --check --offline` | 0 | Resolved 282 packages |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0 | 69 files already formatted |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0 | No errors |
| `uv build --offline --wheel` | 0 | Built `dist/adaptive_browser_agent-0.1.0-py3-none-any.whl` |
| `uv run --offline --locked python -m tests.smoke.d4_agent_domain` | 0 | Public GitHub Agent-domain chain completed |
| `uv run --locked pytest -q -m browser tests/smoke/test_browser_use_adapter.py` | 0 | 1 passed; final run had no warning |

Python type checking remains **未配置**. The initial Chromium smoke passed one
test but emitted an intermittent Windows proactor pipe destructor warning after
the assertion that `adapter._session is None`; a diagnostic tracemalloc run
and the final run each passed one test without the warning. OS-level pipe
closure remains unverified. No D5 API or D6 frontend check was counted as a
D4 gate.

### Real-source and user-facing acceptance

The final public run used **Find one project: FastAPI's official repository**.
One `get_repository("fastapi/fastapi")` action read
`https://api.github.com/repos/fastapi/fastapi`. The admitted fact and report
both cited that URL. The result was `completed/full/target_count`, one step,
one terminal event, and `github/browser/provider` close flags all `true`.
The provider call order was `InitialSubgoals`, `PlanDecision`,
`EvaluationResult`, `ReportDraft`; its 40 input and 20 output tokens were
**controlled fake usage**, not a DeepSeek measurement. The real Chromium smoke
started, navigated, observed, extracted, and closed a browser session.

| User goal and expected answer | Actual output and decision |
| --- | --- |
| Research FastAPI: sourced completed answer | `completed/full/goal_satisfied`; one FastAPI finding cites the GitHub API URL; one terminal event, one tool call, all normal resources closed. **Pass.** |
| Find two projects: retain known fact and show missing count | At a one-step limit: `partial/partial/max_steps`; without that limit: `partial/partial/insufficient_info`. Both direct runs kept one sourced FastAPI finding, said `Requested 2 project(s); verified 1.`, emitted one terminal event, and closed normal resources. **Pass.** |
| Unexpected tool failure: explain failure without invented evidence | `failed/none/execution_error`; no verified findings or sources, unresolved FastAPI subgoal named; one terminal event, all normal resources closed. **Pass.** |
| Cancel during action: stop without false completion | `cancelled/none/user_cancelled`; no verified findings, unresolved subgoal named; one terminal event, one tool call, all normal resources closed. **Pass.** |

No `.env` or `DEEPSEEK_API_KEY` was available, so authenticated DeepSeek
requests, provider-reported real usage, and the end-to-end business API remain
unverified. Generic injected providers without a budget-aware method can
exceed the cap inside one response; unavailable remote usage cannot be
reconstructed. D5 must wire AgentRunResult to runtime/API/persistence/SSE;
D6 frontend and D7 full-system acceptance remain open. **T07 and T10 pass at
the D4 Agent-domain boundary**, including the required public-source and
Chromium gates. Git staging and commit checks are recorded by the delivery
response after this audit snapshot.
