# Adaptive Research Agent Repository Guide

## Project intent

This repository builds Adaptive Research Agent on top of browser-use. Treat
`browser-use/` as browser execution infrastructure. Project-owned code belongs
primarily in `adaptive_agent/`, `backend/`, `frontend/`, `benchmark/`, and
`tests/`.

V1 has a 7-10 day delivery window. Prefer the simplest clear, testable design
that satisfies the frozen requirements. Follow the Python range in
`pyproject.toml` and use `uv` for environment and dependency commands.
Prioritize correct operation, clear boundaries, testability, and explainability
before extensibility.

## Source of truth

`docs/specs/V1_SPEC.md` is the source of truth for V1 product behavior and
technical contracts. Before changing Agent behavior, Agent Loop, Planner,
Evaluator, ResearchState, ContextManager, tool routing, BrowserUseAdapter,
runtime or TaskManager, persistence, public FastAPI APIs, benchmark behavior,
or V1 scope, read the relevant Spec sections.

For typos, comments, formatting, obvious local bugs, and changes that cannot
affect those contracts, inspect only the context needed for the task. When the
user changes a requirement, follow the latest request and update the matching
Spec facts in the same change.

## Architecture boundaries

Keep the main dependency direction:

```text
Frontend -> FastAPI -> TaskManager -> AgentLoop
    -> Planner / ContextManager / Evaluator / StateReducer
    -> ToolRouter -> GitHubTool / BrowserUseAdapter
    -> external APIs / browser-use
```

Avoid reverse dependencies. In particular:

- `browser_use` must not depend on `adaptive_agent`.
- Planner must not own database persistence or `BrowserSession` lifecycle.
- FastAPI routes must call service or runtime layers rather than browser-use
  internals.

## browser-use boundary

Treat `browser-use/` as upstream infrastructure. For integrations, inspect the
checked-out source and use its real API; do not rely on remembered interfaces.
Prefer, in order: existing upstream APIs, adaptation in `BrowserUseAdapter`,
then a minimal upstream patch only when V1 cannot reasonably be implemented by
the adapter.

Do not place ResearchState, Planner, Evaluator, ContextManager, TaskManager,
Reporter, or research workflow policy in browser-use. Additional rules within
the upstream Python package remain authoritative for its own source.

When inspecting or adapting browser-use, preserve its applicable conventions:
use `uv`, keep Pydantic v2 boundaries type-safe, do not replace unfamiliar
model names, use descriptive action names and docstrings, and return structured
`ActionResult` values where appropriate. Do not add demonstration files inside
the submodule; use focused project tests or temporary inline checks.

For any explicitly authorized upstream change, run the smallest relevant
browser-use tests and the project-level adapter tests. Keep browser lifecycle
ownership in the adapter or runtime layer, and disclose behavior that could not
be verified.

## State and model boundaries

`ResearchState` is serializable Agent domain state. Do not store infrastructure
objects such as `BrowserSession`, `asyncio.Task`, `asyncio.Queue`, HTTP clients,
SQLAlchemy sessions, or SSE connections in it.

Route important state changes through:

```text
AgentEvent -> StateReducer -> ResearchState
```

Keep the reducer small and traceable; V1 is not an event-sourcing system. Keep
Agent domain models, API schemas, and database ORM models conceptually separate
with straightforward mappings. Do not add mapper, repository, base-class, or
factory frameworks without a current need.

## Scope and failure handling

Solve the requested problem without unrelated refactors, opportunistic TODOs,
V2 work, or abstractions for hypothetical requirements. Record non-blocking
issues instead of expanding the patch.

Distinguish temporary technical failures from semantic or decision failures.
Technical failures may receive a small bounded retry. Goal mismatch,
insufficient information, and poor decisions return to observe, evaluate, and
replan. Never add unbounded retries.

## Development workflow

Use targeted exploration, the smallest coherent implementation, focused
validation, and fixes for failures caused by the change. Preserve unrelated
working-tree changes. Do not switch branches, reset, rebase, delete user work,
or make broad Git changes unless explicitly requested. Do not commit
automatically.

When behavior changes, add meaningful regression coverage. Prioritize state
transitions, structured-output parsing, stop conditions, deduplication, error
branches, cancellation, async resource lifecycle, and persistence. Keep browser
integration tests to necessary smoke coverage; do not mirror implementation
logic merely to raise coverage.

## Completion

A feature task is complete when the requested behavior is implemented, relevant
checks have run, failures caused by the change are fixed, scope stayed within
the request, and material unverified behavior is disclosed. Never claim a
check passed without evidence.

## V1 scope guard

Use `docs/specs/V1_SPEC.md` for the exact V1 scope. Without explicit approval,
do not add LangChain, LangGraph, Redis, Celery, PostgreSQL, Alembic, a vector
database, RAG, MCP, vision, multi-agent runtime, WebSocket, human-in-the-loop,
model routing, or LLM-as-Judge. Preserve natural extension points when useful,
but do not implement deferred capabilities.
