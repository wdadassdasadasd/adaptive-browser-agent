# Architecture

- `adaptive_agent/` owns domain state, the future Observe/Plan/Act/Evaluate/Replan loop, tool routing, LLM clients, and runtime task primitives.
- `backend/` owns configuration, the FastAPI transport boundary, SQLAlchemy models/session lifecycle, and persistence interfaces.
- `browser-use/` is accessed by application code through `BrowserUseAdapter`; no upstream source changes are authorized.
- Durable state belongs in SQLite tables; runtime tasks, queues, browser sessions, traces, and final reports do not belong in `ResearchState`.
- API handlers are honest placeholders: no simulated research success. Startup creates tables with `Base.metadata.create_all`; rollback is removal of the new outer skeleton and database file.
