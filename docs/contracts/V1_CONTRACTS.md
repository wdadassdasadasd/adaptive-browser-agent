# Adaptive Research Agent V1 contracts

Status: **Target contract**, approved 2026-10-08. The readiness audit records
which parts remain skeletons. This document does not mark unimplemented code as
working. `docs/specs/V1_SPEC.md` remains the product source of truth.

## State and stop semantics

Task status is `queued | running | completed | partial | failed | cancelled`.
Creation writes `queued`; execution enters `running` only after a TaskManager
slot is acquired. Only `queued -> running`, `queued -> terminal`, and
`running -> terminal` are valid. Terminal status never changes. A terminal
transition must persist exactly one `task_finished` event and task status in
one transaction. Subsequent cancel requests do not rewrite the terminal row.

Status, completion level, and stop reason answer different questions:

| Situation | API status | Completion level | Stop reason |
| --- | --- | --- | --- |
| Required subgoals completed with sourced evidence, and explicit target count met when present | `completed` | `full` | `goal_satisfied` / `target_count` |
| Budget, time, replan exhaustion, insufficient information, or recoverable failure with usable sourced facts | `partial` | `partial` | Specific limiting reason |
| Same stop with no usable sourced fact, or unhandled execution error | `failed` | `none` | Specific failure reason |
| User requested cancellation, including while queued | `cancelled` | `partial` if facts exist, else `none` | `user_cancelled` |
| Process restarts with a persisted `queued`/`running` row | `partial` if facts exist, else `failed` | `partial` / `none` | `server_restart` |

There is no `interrupted` status and no checkpoint resume. A `partial` report
states what is known and what remains unresolved; `failed` may have no report.
When all subgoals are complete but an explicit target count remains unmet,
`insufficient_info` is the stop reason (`partial` with sourced facts, otherwise
`failed`). A reached hard limit keeps its specific reason.
An explicit count reached while another required subgoal remains unfinished is
not a completion; the loop continues within its bounded limits.
TaskManager owns slot acquisition, cancellation signals, and cleanup; AgentLoop
owns progress and stop decisions; Persistence owns atomic storage. A subgoal
becomes `in_progress` on selection, `completed` only on validated evaluation,
and `failed` only when the task stops without meeting its completion condition.
Technical failures get one bounded retry before evaluation/replan. Semantic
failure or insufficient information never repeats an identical action by
itself. An unhandled exception closes resources, records a terminal failure,
and releases the semaphore.

### Limits

`max_steps=30` and the last 5 trace events are current defaults in
`adaptive_agent/state.py` and `backend/config.py`. D4 AgentLoop enforces the
frozen defaults of 900 seconds wall time, 40,000 provider-reported prompt plus
completion tokens, and at most five consecutive replans without a new sourced
fact or completed subgoal. Progress
resets the `consecutive_no_progress_replans` state counter. Every loop also
checks step count, time,
token usage, and cancellation. Context assembly retains at most five recent
traces and a 12,000-character bounded current view/summary; truncation is
visible to the Planner. Provider-reported tokens are authoritative for the
task budget; character bounds only limit prompt assembly.

## Domain and tool models

All models are Pydantic v2 with `extra="forbid"`. IDs are nonempty strings;
timestamps are UTC; counters are nonnegative. ResearchState is JSON
serializable and contains no browser, HTTP client, task, queue, SQLAlchemy
session, or SSE connection.

| Model | Target fields and invariant |
| --- | --- |
| ResearchState | `task_id: str`, `goal: str`, `status` (default `queued`), `step: int` (default 0), `max_steps: int` (default 30), `subgoals: list[Subgoal]`, `facts: list[ResearchFact]`, `visited_urls: list[str]`, `search_history: list[str]`, `current_subgoal_id: str | None`, `prompt_tokens: int`, `completion_tokens: int`, `consecutive_no_progress_replans: int` (default 0), `cancellation_requested: bool`, `stop_reason: str | None`, `completion_level: none|partial|full`, `created_at`, `updated_at`. `step <= max_steps`; current subgoal ID must refer to an existing subgoal. |
| Subgoal | `id: str`, `description: str`, `completion_criteria: str`, `priority: int`, `status: pending|in_progress|completed|failed`, optional `failure_reason`. Criteria describe observable evidence, not a fixed action script. |
| ResearchFact | Existing `id`, optional `subgoal_id`, nonempty `content`, `source_url`, `source_title`, optional `evidence`, `confidence`, `subject`, and `subject_kind` (`project|change`), `created_at`. A material fact must carry a public HTTP(S) source URL actually observed by a tool. A counted subject must match a complete name in its verbatim evidence, or the exact owner/repository identity in an observed official GitHub repository or release URL. Search-result URLs do not anchor a repository identity. |
| PlanDecision | `subgoal_id`, `reasoning`, `tool`, `action`, optional `target`, optional `element_index`, optional `value`, `expected_result`. `subgoal_id` must exist and be unfinished. Exactly one primary action is selected per iteration. |
| EvaluationResult | `success`, nonempty `reason`, `subgoal_completed`, `should_replan`, `facts: list[ResearchFact]`, `error_type: none|technical|semantic|insufficient_info`. `success=true` requires `error_type=none`; `success=false` requires non-`none`, `subgoal_completed=false`, and `should_replan=true`. Facts are admitted only after source validation. Invalid combinations fail Pydantic validation and become a bounded structured-output failure, not state mutation. |
| Finding | `name`, `description`, `attributes: dict[str,str]`, `source_urls: list[str]`, optional `supporting_fact_ids: list[str]`. Each material claim maps to collected fact IDs and source URLs. |
| ResearchReport | `task_id`, `goal`, `title`, `summary`, `findings`, `comparison`, `recommendation`, `sources`, `markdown`, `generated_at`. Empty comparison/recommendation may say “insufficient evidence”; neither may invent an answer. |

`tool="browser"` actions are `navigate`, `click`, `input_text`, `scroll`,
`extract`, `go_back`, and `wait`. `navigate.target` is an HTTP(S) URL; `click`
requires a valid positive element index or a unique semantic target;
`input_text` additionally requires `value`; `scroll.target` is `up` or `down`
(default `down`) and scrolls one viewport; `extract.target` is the extraction
question and returns bounded clean page Markdown for downstream evaluation;
`go_back` takes no parameters; `wait.value` is seconds in `0..10` (default 1).
Index resolution uses the current observation first, then exact semantic name,
contains match, normalized text match, and finally a structured not-found or
ambiguous result. A stale index is never clicked after a page change.

`tool="github"` actions are `search_repositories` (`target` is query),
`get_repository` (`target=owner/repo`), and `list_releases`
(`target=owner/repo`). No arbitrary GitHub URL or client-supplied API host is
allowed. Browser and GitHub results map to `ToolResult` with `tool`, `action`,
`success`, bounded `content`, optional `source_url`, `error_type` (same four
values), optional `error_message`, and safe `metadata`. Technical errors
include timeout, 429/5xx, and browser navigation failure. A missing, stale,
or ambiguous element is a semantic failure. Duplicate URLs or
normalized queries are semantic no-op results that trigger a different plan.
URL normalization lowercases scheme/host and removes fragments while retaining
path and query; query normalization trims/collapses whitespace and case-folds.
Search queries that failed for a technical reason do not enter the deduplication
history, so a later AgentLoop-owned bounded retry remains possible.

BrowserAction is the validated subset of PlanDecision fields. A
BrowserObservation contains `url`, `title`, bounded DOM text, model-visible
element references, observation level (`light|deep`), and optional error.
BrowserResult contains `success`, `action`, final `url`, bounded `content`,
`error_type`, and optional `error_message`; it maps into ToolResult without
leaking upstream session objects. `light` has no screenshot; `deep` may add
recent event semantics but no vision. Adapter starts, owns, and kills its
BrowserSession even when startup or an action fails.

## Events, reducer, retries, and persistence

AgentEvent has `event_id: UUID string`, `task_id`, `event_type`, `step` (0-based
before the first action), UTC `timestamp`, optional `message`, and JSON
`payload`. The closed V1 types are:

| Event | Required payload | Reducer effect |
| --- | --- | --- |
| `task_queued` | `goal` | Confirms initial queued state. |
| `task_started` | empty | `queued -> running`. |
| `subgoals_initialized` | `subgoals`; optional nonnegative `prompt_tokens`, `completion_tokens` | Sets initial subgoals once and records provider usage from initialization. |
| `step_evaluated` | JSON objects `decision`, `tool_result`, `evaluation`; nonnegative integer `prompt_tokens` and `completion_tokens` | Event `step` equals the current state step (first action 0); reducer increments the step once and updates subgoal, URLs/queries, validated facts, usage, and `consecutive_no_progress_replans`. |
| `cancel_requested` | empty | Sets cancellation flag; terminal transition remains separate. |
| `task_finished` | `status`, `completion_level`, `stop_reason`; optional `report` and nonnegative `prompt_tokens`, `completion_tokens` | Applies one terminal transition and records provider usage not attached to a step, including report generation. |

StateReducer is pure and deterministic: `(ResearchState, AgentEvent) ->
ResearchState`. It rejects wrong task IDs, repeated step numbers, invalid
event payloads/transitions, and overflow. Trace persistence stores `event_id` in
the existing JSON payload alongside event data; SQLite trace row ID remains a
separate replay cursor. The terminal trace JSON stores report, completion
level, and stop reason, avoiding a schema migration; GET reconstructs these
from the latest terminal event. The task status and terminal trace must commit
atomically. Existing local SQLite data is preserved; `metadata.create_all`
does not migrate columns.

Exactly one layer owns each recovery mechanism: the DeepSeek provider retries
a temporary network/429/5xx request once; its structured parser may make one
repair request after Pydantic failure, counted separately. Browser adapter and
GitHub tool surface normalized technical errors without their own retry loop.
AgentLoop checks the remaining task budget before permitting a provider retry,
and performs bounded re-observe/replan after an evaluated failure. No semantic
error or insufficient-info result is retried as the same action.

D2 provider interface: `complete(prompt)` returns `LLMCompletion(text,
prompt_tokens, completion_tokens)`; `complete_structured(prompt, schema)`
returns `StructuredCompletion(value, prompt_tokens, completion_tokens)` after
Pydantic validation. Usage sums the provider-reported values for successful
initial and repair responses; structured failure carries usage already
reported by the provider. A repair request has its own single temporary
technical retry. Missing usage is a provider response failure, never an
estimated zero. `PlannerService.initialize(goal)` returns subgoals for a
`subgoals_initialized` event; `next_step(state, observation, context="")`
returns one validated decision without modifying ResearchState.

The D2 provider uses `deepseek-flash` by default; `DEEPSEEK_MODEL` may override
it. `LLMError.kind` is `configuration | technical | rejected |
invalid_response | structured`; cancellation propagates as
`asyncio.CancelledError`. Structured requests include the Pydantic JSON schema
in both the initial request and the single repair request.

## HTTP, SSE, and security

The six routes in the Spec are the entire V1 public API. `POST /api/research`
accepts `{"goal": nonempty string}` and returns 202 with task ID, queued
status, timestamps, and null report/stop reason. List and GET return task
status, goal, timestamps, optional error, completion level, stop reason, and
optional ResearchReport. Traces return persisted AgentEvents in order with
event IDs. Bad input returns 422; unknown task ID returns 404; valid reads and
cancel return 200. A missing DeepSeek key prevents starting a task and returns
503 with a non-secret message; it never creates a false queued task.

`POST /cancel` requests soft cancellation for queued/running tasks. It returns
`{"task_id": ..., "cancelled": true}` for newly requested, already requested,
or already cancelled tasks. Other terminal states return `cancelled=false`
without modification. SSE frames are `id: <event_id>`,
`event: <event_type>`, `data: <JSON AgentEvent>`, blank line. A subscriber first
receives persisted ordered traces, then live events without duplicate IDs;
the stream ends after `task_finished`. A disconnect removes only that
subscriber, never cancels the task. Per-subscriber queues are bounded; a slow
client reconnects for persisted replay rather than blocking the Agent.

The frontend consumes these six routes only. It never receives a provider or
GitHub token. Persisted Trace/SSE payloads have bounded size and redact
credentials. Webpage text is untrusted input and cannot be promoted to system
instructions or final facts without evaluation and a source URL. Direct
browser navigation rejects `file:`, `javascript:`, browser-internal schemes,
credentials in URLs, loopback, private/link-local/multicast/unspecified
addresses, and DNS answers resolving to them. Final navigated URLs are checked
again after redirects. The checked-out upstream watchdog checks configured
domain restrictions but its redirect check is post-navigation; V1 remains a
trusted localhost demo, not a public SSRF-safe service. Sessions, HTTP clients,
DB sessions, tasks, and SSE subscriptions close in `finally` paths.
