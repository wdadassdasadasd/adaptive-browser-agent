# D2 code recheck, repair, and acceptance — 2026-10-10

## 00 — Scope and criteria

`HEAD` and the D1 baseline were both `00a425c28b4de099924e7b9535d8745cee53afa2`.
There were no commits after the baseline and no staged changes. At entry, the
unstaged D2 files were `adaptive_agent/llm/{base,deepseek}.py`,
`adaptive_agent/{planner,state_reducer}.py`, `adaptive_agent/prompts/planner.py`,
the Spec, Contracts, task ledger, test matrix, and
`tests/unit/test_state_reducer.py`; `tests/unit/test_deepseek.py` and
`tests/unit/test_planner.py` were untracked. The final worktree also contains
the scoped fixes, tests and this report. The upstream submodule was excluded
from the diff; no upstream source was changed.

Read the root `AGENTS.md`, Spec, Contracts, task ledger and test matrix before
the recheck. Direct interfaces inspected were `ResearchState`, `AgentEvent`,
`PlanDecision`, `EvaluationResult`, the LLM protocol and result types,
`BrowserAction`, `ToolRouter`, FastAPI routes and the placeholder `AgentLoop`.
No D3–D7 implementation was added.

| Requirement | Implementation | Current test evidence | Conclusion |
| --- | --- | --- | --- |
| T03: one consecutive `step_evaluated`, selected subgoal and immutable input | `adaptive_agent/state_reducer.py:162` | `test_state_reducer.py:253,337`; component flow | Pass |
| T03: observed-source facts, normalized URL/query and fact dedup | `state_reducer.py:189-239` | `test_state_reducer.py:337,365,400,432` | Pass within the supplied ToolResult boundary; actual tool provenance is D3/D4 |
| T03: usage once, no-progress count, invalid/duplicate event and terminal protection | `state_reducer.py:43,112,162,244-260` | `test_state_reducer.py:111,243,253,365,422,485,515` | Pass |
| T04: DeepSeek request, structured schema and reported usage | `adaptive_agent/llm/deepseek.py:37-77,98-148` | `test_deepseek.py:45,65,157,178,281`; component flow | Pass with fake transport |
| T04: one technical retry, one separate repair, typed failure and no secret in errors | `adaptive_agent/llm/base.py:9,28`; `deepseek.py:50-72,98-143` | `test_deepseek.py:80,99,118,139,194,212,232,281` | Pass with fake transport |
| T04: cancellation and owned/injected client closure | `deepseek.py:98-148` | `test_deepseek.py:253,272`; component flow | Pass with fake transport |
| T05: observable subgoal criterion, one state/observation-driven action | `adaptive_agent/planner.py:21-74` | `test_planner.py:59,70`; component flow | Pass at D2 component boundary |
| T05: unsupported action/parameters and invalid subgoal fail safely | `planner.py:75-132` | `test_planner.py:103,123,155,176` | Pass |

## 01–02 — Static checks and automated tests

The restricted sandbox returned exit 1 for `uv lock --check --offline` with
“Failed to query Python interpreter / Access denied”. The same command and
subsequent `uv` checks ran in the approved regular execution environment. The
entry checks exited 0: lock resolved 282 packages; Ruff lint passed; Ruff
format reported 56 files formatted; compileall had no errors; Hatch built a
wheel. Entry tests exited 0: 67 targeted tests, then 135 passed and one
opt-in browser test deselected on each of Python 3.12 and 3.13. These entry
passes did not settle the code-review findings below.

Final command results after repair:

| Command | Exit | Actual result |
| --- | ---: | --- |
| `.venv/Scripts/python.exe -m pytest -q tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py tests/unit/test_config.py tests/integration/test_d2_component_flow.py` | 0 | 88 passed |
| `uv run --isolated --python 3.12 --offline --locked pytest -q` | 0 | 154 passed, 1 deselected |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | 0 | 154 passed, 1 deselected |
| `uv lock --check --offline` | 0 | Resolved 282 packages |
| `.venv/Scripts/ruff.exe check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `.venv/Scripts/ruff.exe format --check adaptive_agent backend benchmark tests` | 0 | 57 files already formatted |
| `.venv/Scripts/python.exe -m compileall -q adaptive_agent backend benchmark tests` | 0 | No errors |
| `uv build --offline --wheel` | 0 | `dist/adaptive_browser_agent-0.1.0-py3-none-any.whl` built |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | No whitespace errors; LF→CRLF advisories only |

No Python type checker or frontend build is configured. The current tests
include API placeholder smoke and SQLite table integration checks; full API
integration and E2E research tests do not exist. Their absence is a gap, not a
unit-test pass.

## 03 — Running component and service evidence

`uv run --python 3.12 --offline --locked pytest -q tests/smoke/test_app.py
tests/integration/test_d2_component_flow.py` exited 0 with **3 passed**. The
D2 component scenario input was “Find official FastAPI docs and verify ASGI
support” plus a simulated search-results observation. Two HTTP requests passed
through the actual `DeepSeekClient` JSON parser using `httpx.MockTransport`;
Planner returned one `navigate` decision for
`https://fastapi.tiangolo.com/`; a simulated successful tool/evaluation result
produced step 1, one sourced fact, a completed subgoal, normalized visited URL
and `(11, 5)` step tokens. The test asserted two requests and closure of the
owned HTTP client. These are simulated observations and evidence, not a live
page fetch. The components emitted no application log lines in this test; the
assertions and pytest exit/output are the available execution evidence.

The FastAPI smoke exercised a running app through `TestClient`. `GET
/api/research` returned `[]`; `POST /api/research` with
`{"goal":"Research"}` returned 501; the research GET and cancel routes also
returned 501, while the placeholder event stream returned an empty 200 SSE
response. `AgentLoop.run` still raises `NotImplementedError`. No
`DEEPSEEK_API_KEY` environment value or `.env` file was present, so no
authenticated DeepSeek request was made. No credential was printed or stored.

## 04 — Code review and verified repairs

The effective parent filesystem permission was `workspace-write`; no native
independent reviewer with verifiable read-only effective permissions was
available. **Independent review was not completed or claimed.** The main
agent reviewed the explicit D2 diff, new tests and direct interfaces, then
reproduced each finding with a failing test before repair:

| Finding and root cause | File/line evidence | RED → GREEN evidence |
| --- | --- | --- |
| Planner accepted parameters for `go_back` and malformed GitHub repository targets because `_validate_action` only checked action names and nonempty targets. | `adaptive_agent/planner.py:75-132` | Four new cases failed, then `test_planner.py:155` passed; valid `owner/repo` passes at line 176. |
| Reducer accepted non-pending initial subgoals and contradictory ToolResult `success/error_type`, allowing an invalid event to change state. | `adaptive_agent/state_reducer.py:43,112-132` | Three new cases failed, then `test_state_reducer.py:111,422` passed. |
| Structured requests and repair supplied no JSON field schema, leaving the model unable to use the validator's requirements. | `adaptive_agent/llm/deepseek.py:37-53` | Schema prompt test failed, then `test_deepseek.py:178` passed. |
| Provider failures lacked a machine-readable category; temporary failures, rejection and malformed responses all surfaced as generic `LLMError`. | `adaptive_agent/llm/base.py:28-43`; `deepseek.py:77-143` | Eight classification cases failed, then all DeepSeek tests passed. |
| Client/config defaults used `deepseek-chat`, absent from the current official model list. | `adaptive_agent/llm/deepseek.py:21`; `backend/config.py:43` | Config default test failed, then `test_config.py:29` passed. Both defaults are now `deepseek-flash`; the benchmark protocol name was aligned. |
| Planner accepted a click with `element_index=0` when a semantic target was also present, though the browser adapter rejects that index. | `adaptive_agent/planner.py`; `adaptive_agent/adapters/browser_use_adapter.py:44` | New `test_planner.py` parameter failed, then passed after Planner rejected index 0. |
| Injected HTTP clients without `base_url` could not resolve the relative DeepSeek endpoint. | `adaptive_agent/llm/deepseek.py` | New `test_deepseek.py` case failed with `ValueError: unknown url type`, then passed with the fixed absolute provider endpoint. |
| `.env.example` still selected retired `deepseek-chat`, overriding the corrected runtime default for users who copy the sample. | `.env.example:9`; `backend/config.py:43` | Example value aligned to `deepseek-flash`; config default remains covered by `test_config.py`. |

The model-name decision follows DeepSeek's [current first-call model list](https://api-docs.deepseek.com/)
and [change log](https://api-docs.deepseek.com/updates/). The documented
`/chat/completions` path, `response_format: json_object`, and 429/5xx
classification were checked against the [chat API](https://api-docs.deepseek.com/api/create-chat-completion/)
and [error codes](https://api-docs.deepseek.com/quick_start/error_codes/).
Actual authenticated compatibility remains unverified.

## 05 — Business scenarios at the available D2 boundary

| User scenario | Expected | Actual |
| --- | --- | --- |
| Research the official FastAPI documentation from search results | Observable subgoal, one relevant next action, sourced step, closed HTTP client | Component scenario passed; one `navigate`, one simulated sourced fact, completed subgoal, client closed |
| Observation or state changes | Planner reconsiders and returns one current action | `test_planner.py:70` passed; `navigate` changed to `extract` as inputs changed |
| Model emits unsupported or malformed action | Safe failure, no fallback action or state mutation | `test_planner.py:103,123,155` passed with `ValueError` |
| Provider times out, returns 429/5xx, or malformed JSON | Bounded retry/repair, typed safe failure, known usage retained | `test_deepseek.py:80,99,118,157,194,212,232` passed |
| Duplicate fact/step or failed search with no progress | No duplicate state/token application; no-progress counter advances only on replan | `test_state_reducer.py:253,337,365,432` passed |

There is no complete research UI or Agent Loop. Complete V1 business
acceptance is **not ready**; no full user task or end-to-end result is claimed.

## 06 — Decision and remaining risks

- **T03:** Pass at the D2 Reducer boundary after repair.
- **T04:** Pass at the D2 offline provider boundary after repair; authenticated
  DeepSeek behavior remains unverified because no key was available.
- **T05:** Pass at the D2 Planner boundary after repair; Planner→Router and
  real observation integration remain D3 work.
- **D2 module acceptance:** **Pass** for the frozen D2 exit criteria and the
  executable component chain.
- **Complete V1 business acceptance:** **Not ready** because Agent Loop, API
  execution and frontend are placeholders or absent.

Remaining risks: no independently permission-isolated review was possible;
provider/model behavior was checked against current docs and fake transport but
not an authenticated request; component ToolResult evidence was simulated;
the Planner's public return type does not expose its provider usage, so D4
Agent Loop integration must account for those tokens without changing the D2
decision contract. API integration, E2E and live research acceptance remain
future gates. No push or deployment was made. This report documents the D2
changes before the requested local Git commit.
