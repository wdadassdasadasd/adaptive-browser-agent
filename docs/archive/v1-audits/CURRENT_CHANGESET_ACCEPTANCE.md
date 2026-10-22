# Current Git changeset acceptance (2026-10-10)

## Boundary and verdict

This review covers the worktree changes present at intake: 16 modified tracked
files, 16 untracked files, and the `browser-use` submodule. The acceptance
target is the documented D1/T02/T03 foundation and current configuration,
tests, CI source, and preparation documents. It is **locally accepted for that
stage**, not accepted as a complete V1 product. No push, deployment, database
reset, or upstream submodule edit was made.

The earlier review did not create a commit. This follow-up rechecks the same
changeset for the requested Chinese commit; the final commit ID is reported in
the handoff.

`docs/specs/V1_SPEC.md` is the product authority;
`docs/contracts/V1_CONTRACTS.md` specifies the target contract. Dated readiness
and predevelopment audits remain historical records. The D1 test table in
`docs/testing/V1_TEST_MATRIX.md` is historical relative to this follow-up.

## Confirmed defects and repairs

The behavioral regressions below failed before their respective fixes and
passed afterward; C-06 is a documentation correction. Paths and line numbers
refer to the reviewed worktree.

| ID | Severity | Trigger and effect | Repair and regression evidence |
| --- | --- | --- | --- |
| C-01 | P1 | The checked-out upstream `click` and `input` return an `ActionResult` containing “Element index … not available” when the node vanishes between lookup and use. The adapter treated that content as success. | `adaptive_agent/adapters/browser_use_adapter.py:211-224` maps this known upstream result to a semantic failure; `tests/unit/test_browser_use_adapter.py:280` covers both actions. |
| C-02 | P1 | An index could appear unchanged after a document/session swap when its backend node ID was reused, permitting a click on the wrong document. | The observed identity now includes the CDP session ID and backend node ID (`browser_use_adapter.py:249-267`); `test_browser_use_adapter.py:244` reproduces the collision. |
| C-03 | P1 | Element-targeted scroll bypassed stale-index validation. Scroll, wait, and a failed navigation action could leave an older observation eligible for the next click. | Scroll validates its index and all potentially page-changing actions invalidate the observation before upstream execution (`browser_use_adapter.py:193-253`); regressions are at `test_browser_use_adapter.py:320`, `:353`, and `:391`. |
| C-04 | P1 | A session already on an unsafe URL could be observed or clicked before the adapter checked its final URL. A semantic lookup could also consume a newly unsafe page. | Current and observed URLs are checked before exposing page state or invoking an action (`browser_use_adapter.py:116-155`, `:271-274`); regressions are at `test_browser_use_adapter.py:479`, `:511`, `:535`, and `:554`. A redirect may still contact an unsafe destination before post-navigation validation. |
| C-05 | P2 | A Chromium `chrome-error://` page after a requested navigation was classified as an unsafe target instead of a technical navigation failure. | `browser_use_adapter.py:164-168` classifies it as technical; `test_browser_use_adapter.py:455` covers the result. |
| C-06 | P2 | The new Spec clarification appeared as §25 before §§22–24, and current D1 evidence text could be mistaken for the latest test run. | The Spec section is in numeric order; README and test/task ledgers distinguish dated evidence from this follow-up. Historical audit files were preserved. |
| C-07 | P2 | `ResearchFact` accepted `http://localhost./` and subdomains of `.localhost` as public source URLs because the validator checked only the exact `localhost` spelling. | `adaptive_agent/state.py` now rejects those local-host aliases; `tests/unit/test_state.py::test_facts_evaluation_and_report_use_approved_fields` failed before the fix and passed after it. This remains a syntax check, not proof that a tool observed the source or that DNS resolves publicly. |

## Local acceptance evidence

| Check | Result |
| --- | --- |
| `uv run --offline --locked pytest -q` on Python 3.12.13 | Exit 0; 113 passed, 1 browser test deselected. |
| `uv run --isolated --python 3.13 --offline --locked pytest -q` | Exit 0; 113 passed, 1 browser test deselected. |
| `.venv\Scripts\python.exe -m pytest -q -m browser tests/smoke/test_browser_use_adapter.py` | Exit 0; 1 controlled Chromium smoke passed. |
| `uv lock --check --offline` | Exit 0; resolved 282 packages. |
| Locked CI configuration construction (`Settings(_env_file=None)`) | Exit 0. |
| Locked Ruff check, Ruff format check, Python compile check | Exit 0 for each; format check reported 54 files already formatted. |
| `git diff --check --ignore-submodules=all`; untracked text scan | Exit 0; 16 untracked files inspected as UTF-8 with no trailing whitespace or NUL. Git emitted only LF/CRLF conversion warnings. |
| `git -C browser-use status --short --untracked-files=all` and `rev-parse HEAD` | No submodule changes; HEAD is tracked gitlink `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`. |

The state/event/reducer models, queued ORM default, blank-credential handling,
TaskManager failure-slot behavior, CI source, and all untracked preparation
documents were checked against their declared stage. The offline suite includes
their current regression tests. The controlled browser test verifies startup,
navigation, observation, extraction, unsafe navigation rejection, and closure.
This follow-up reran the Python 3.12 and 3.13 locked offline suites (113 passed,
1 deselected on each), the controlled Chromium smoke (1 passed), Ruff check,
Ruff format check, compileall, and `uv lock --check --offline` after C-07. The
added `NaN` wait-parameter test passed before any production change and records
an already enforced boundary rather than a repaired defect.

## Explicitly unverified or unfinished

- T03 `step_evaluated` aggregation is still intentionally unimplemented and
  raises `NotImplementedError` for a valid evaluated step. The task ledger
  retains its `in_progress` status.
- Real-browser click, input, scroll, back, and wait were not individually
  exercised; their dispatch and failure branches have fake-backed tests.
- GitHub Actions has not run remotely. The frontend package, integrated
  AgentLoop/API/SSE, live DeepSeek/GitHub research, complete V1 acceptance
  tasks, and same-model benchmark runs do not yet exist or remain unverified.
- The URL checks do not establish pre-request redirect or network isolation.
  The documented deployment boundary remains a trusted localhost demo.
