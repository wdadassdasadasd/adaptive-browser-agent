# Adaptive Research Agent V1 Specification

## 1. Project positioning

Adaptive Research Agent is an independent research-oriented Agent runtime built
on browser-use. browser-use provides browser execution infrastructure; this
project owns the Agent Loop, Planner, ResearchState, tool routing, Evaluator,
context management, async task runtime, traces, and benchmark.

V1 is a portfolio project for frontend-oriented job applications and a base for
continued Agent engineering work.

## 2. V1 goals

V1 must be deliverable in 7-10 days and demonstrate Python async foundations,
FastAPI, an Agent Loop, tool calling, state management, context engineering,
Agent evaluation, and a reproducible benchmark.

The central engineering questions are how a long-running task replans as it
learns, avoids duplicate research, bounds context growth, and stops at an
appropriate point.

## 3. Non-goals

V1 does not implement:

- LangChain or LangGraph
- Redis, Celery, PostgreSQL, or Alembic
- MCP
- RAG, vector databases, or embedding memory
- vision or multi-tab browsing
- login or credential management
- checkpoint resume or distributed workers
- WebSocket or human-in-the-loop control
- model routing or LLM-as-Judge
- multi-agent runtime
- cost-aware planning
- subgoal DAG execution

These capabilities are deferred rather than permanently prohibited.

## 4. High-level architecture

```text
Vue
  -> FastAPI
  -> TaskManager
  -> ResearchAgent / AgentLoop
  -> Planner / ContextManager / Evaluator / StateReducer / Reporter
  -> ToolRouter
       -> GitHubTool -> GitHub API
       -> BrowserUseAdapter -> browser-use
```

V1 does not require a general-purpose Agent framework around this flow.

## 5. Core Agent Loop

The target loop is:

```text
User Goal
-> initialize high-level subgoals
-> Observe
-> build bounded context
-> Plan one next action
-> route tool
-> Act
-> Evaluate
-> emit AgentEvent
-> reduce ResearchState
-> Replan
-> Stop
-> Report
```

The Planner selects one primary next action per iteration. It must not produce a
fixed browser action script for the entire task up front.

## 6. Planner

One `PlannerService` exposes these conceptual operations:

```text
initialize(goal)
next_step(state, context)
```

`initialize` produces high-level subgoals. `next_step` dynamically selects the
next action from current state and observation. `PlanDecision` must carry:

```text
subgoal_id
reasoning
tool
action
target
element_index
value
expected_result
```

`element_index` and `value` are optional. V1 tool identifiers are `browser`
and `github`.

## 7. ResearchState

The minimum state contains task identity, goal, subgoals, current subgoal,
visited URLs, search history, collected facts, step usage and limit,
prompt/completion token metrics, consecutive no-progress replans, and a
cancellation flag. A new task starts in
`queued`; final states include `partial`. Stop reason and business completion
level are separate from the public task status.

Each subgoal contains `id`, `description`, observable
`completion_criteria`, `priority`, and `status`.
`depends_on` may be retained as a future-facing field, but V1 does not schedule
a dependency DAG.

## 8. ResearchFact

Every fact stores at least `content`, `source_url`, and `source_title`.
`evidence` and `confidence` may be reserved for later use. Every material final
conclusion must be traceable to a source.

## 9. BrowserUseAdapter

`BrowserUseAdapter` is the primary boundary between the project runtime and
browser-use. It must support starting a session, observing, executing an action,
reading session state, and closing the session.

Observation has two modes:

- `light`: default, lower-cost observation
- `deep`: richer page semantics only when the Planner explicitly needs them

V1 browser actions are `navigate`, `click`, `input_text`, `scroll`, `extract`,
`go_back`, and `wait`. Multi-tab operation, vision, upload/download workflows,
and credential handling are excluded.

Element resolution proceeds through a valid element index, exact semantic
match, contains match, normalized text match, then failure and replanning. V1
does not add another LLM element resolver. Implementation must follow the API
present in the checked-out browser-use source; this Spec does not invent an
upstream interface.

## 10. GitHub tool

`GitHubTool` uses the GitHub REST API through `httpx.AsyncClient`. `GITHUB_TOKEN`
is optional; public repository research remains available without it.

Use the GitHub API for structured, deterministic repository information and the
browser for information that requires webpage-level semantic understanding.

## 11. LLM provider

Agent business logic depends on a single LLM provider abstraction. The V1
provider is DeepSeek, called through `httpx.AsyncClient`; V1 has no LangChain or
LangGraph dependency.

The provider owns requests, timeouts, response parsing, usage metrics, and
structured-result parsing. A temporary network, rate-limit, or server failure
may be retried once. Structured output follows:

```text
LLM output -> Pydantic validation
invalid -> one repair attempt
still invalid -> standardized failure
```

## 12. Evaluator

One `EvaluatorService` contains two conceptual phases. Technical evaluation
handles deterministic failures such as timeouts, navigation failures, empty
results, and action failures. Semantic evaluation runs only after technical
success and only when an LLM judgment is needed to compare the actual result
with the expected result.

`EvaluationResult` carries `success`, `reason`, `subgoal_completed`,
`should_replan`, `facts`, and `error_type`. `error_type` is one of `none`,
`technical`, `semantic`, or `insufficient_info`.

Runtime LLM semantic evaluation is allowed after technical validation. The
LLM-as-Judge prohibition applies to benchmark scoring only.

## 13. ContextManager

Planner context is bounded and normally contains ResearchState, the current
observation, the latest 3-5 trace steps, and a structured history summary.

Deterministic code maintains the summary of completed subgoals, failed actions,
visited URLs, collected facts, and avoid-repeat information. V1 has no embedding
or vector retrieval.

## 14. AgentEvent and StateReducer

Important state transitions use:

```text
AgentEvent -> StateReducer -> ResearchState
```

V1 uses one generic event model carrying `event_id`, `event_type`, task ID,
0-based step (default 0),
timestamp, optional message, and payload. The same event stream may feed state
updates, trace, persistence, SSE, and benchmark metrics. V1 does not introduce a
class hierarchy for every event type.

## 15. Stop conditions

Hard stops include the maximum step count, maximum runtime, requested
cancellation, and an explicitly requested target count being reached.

Soft stops include completion of required subgoals, sufficient information
coverage, and no meaningful remaining research gap. The Agent must not search
indefinitely. All retry and replan paths must be bounded. The AgentLoop owns
step, elapsed-time, token, cancellation, and non-progress stops. The provider
owns one retry for a temporary technical request failure and one separate
structured-output repair attempt. Semantic and insufficient-information
outcomes return to observation and planning rather than repeating an action.
The V1 defaults are 30 steps, 900 seconds, 40,000 prompt plus completion
tokens, and five consecutive replans without progress. Context retains at most
five recent traces and a 12,000-character current view/summary. These values
were frozen on 2026-10-09 for implementation and acceptance; they do not claim
the current skeleton enforces them. Detailed semantics are in
`docs/contracts/V1_CONTRACTS.md`.

## 16. Reporter

Research iterations collect structured facts rather than continually rewriting
the final report. After the task stops, the Reporter transforms ResearchState,
facts, and sources into a general-purpose `ResearchReport` with at least title,
summary, findings, comparison, recommendation, sources, and a Markdown
representation. The report schema is not GitHub-specific. Findings carry
`name`, `description`, `attributes`, and `source_urls`; material claims must
be supported by collected facts and sources.

## 17. Runtime and TaskManager

Creating a research task through FastAPI returns its task ID promptly. A
lightweight async runtime executes long tasks using `asyncio.create_task`,
`asyncio.Queue`, and `asyncio.Semaphore` with a default maximum of two concurrent
research tasks.

Each task has isolated runtime resources. V1 supports soft cancellation. It does
not support distributed queues, resumable workers, Celery, or Redis. States are
`queued`, `running`, `completed`, `partial`, `failed`, and `cancelled`. A task
may move from `queued` to `running`, and from either nonterminal state to a
terminal state. Terminal states are immutable. After restart, unfinished
in-process tasks are finalized from persisted evidence without resuming.

## 18. Persistence

V1 uses SQLAlchemy 2.x, `AsyncSession`, aiosqlite, and SQLite. It persists at
least research tasks, research steps, research facts, and Agent traces.

V1 uses `metadata.create_all` and does not introduce Alembic. The persistence
layer supports creating a task, updating status, saving steps/facts/traces,
reading a task, listing recent tasks, and rebuilding the timeline and report for
display. Complex query infrastructure is out of scope.

## 19. FastAPI public API

The V1 public API is fixed to:

```text
POST /api/research
GET  /api/research
GET  /api/research/{task_id}
GET  /api/research/{task_id}/events
GET  /api/research/{task_id}/traces
POST /api/research/{task_id}/cancel
```

The events endpoint uses Server-Sent Events. V1 does not expose separate CRUD
APIs for facts, sources, or steps. The fixed routes' request/response, errors,
idempotent cancellation, persisted SSE replay, disconnect, terminal close,
and cleanup semantics are in `docs/contracts/V1_CONTRACTS.md`.

## 20. Frontend

The Vue V1 supports research goal input, Start, Cancel, task status, Agent
timeline, research report, and a minimal recent-tasks view.

A complex administration interface, model settings center, prompt management
UI, benchmark dashboard, and login system are excluded. The frontend is not the
primary V1 innovation.

## 21. Benchmark

The baseline is the unmodified browser-use Agent. Comparisons should hold the
model, task, and approximate step budget constant where practical.

V1 records completion rate, average steps, duplicate URLs, token usage, latency,
and result coverage. Coverage is scored deterministically against predefined
expected fields; V1 does not use LLM-as-Judge. Report improvement percentages
only after measuring a real baseline. Report the full-system comparison with
GitHub API access separately from a browser-only tool-controlled comparison.
Do not attribute tool advantages to planning or replanning.

## 22. Acceptance scenarios

V1 must reliably complete 3-5 representative public research tasks spanning
candidate discovery, direct comparison, and version or change research. Tasks
may use public official documentation and must not require authenticated sites.

## 23. Deliverables

V1 delivery includes:

- a working Adaptive Research Agent and BrowserUseAdapter
- a DeepSeek provider and GitHub tool
- an async TaskManager
- the FastAPI API and SSE timeline
- SQLite persistence
- a basic Vue UI
- a benchmark runner
- tests for deterministic core behavior
- README instructions for basic local startup

## 24. Done when

V1 is complete when all of the following are true:

- 3-5 representative tasks run reliably.
- Planner decisions demonstrably use current state to choose each next step.
- GitHub and browser tool routing both work.
- Evaluator distinguishes technical failure, semantic failure, and insufficient
  information.
- Duplicate URLs and queries have an explicit suppression mechanism.
- Planner context does not grow with the full unbounded history.
- SSE exposes the Agent timeline.
- SQLite task records can be reloaded for timeline and report display.
- The final ResearchReport cites its sources.
- Baseline and adaptive benchmark runs are available.
- Core deterministic logic has meaningful tests.
- README instructions support basic local startup.

Unstable external sites or networks must be reported separately from project
logic failures; external failures are never evidence of a passing run.

## 25. V1 contract and security clarification (2026-10-08)

`docs/contracts/V1_CONTRACTS.md` records the approved target models and
error/stop semantics. This clarification supersedes the skeleton names
`pending`, AgentEvent `type`, `new_facts`, and Finding `title`/`content`.
Models, consumers, storage mappings, and tests must change together; this
document does not claim that the target is already implemented.

Webpage text is untrusted task data and cannot override Agent instructions.
Credentials must never enter reports, logs, persisted traces, or SSE payloads.
Browser navigation must reject non-HTTP(S) schemes and local/private targets
and check final URLs after redirects. Research facts require source validation.
Browser sessions and HTTP clients must close on success, failure, and cancel.
Until redirect and network isolation are independently verified, V1 is a
trusted localhost demo and is not approved for public deployment.
