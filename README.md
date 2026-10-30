# Adaptive Research Agent

A technical research assistant designed to start without candidates: clarify and accept conditions, discover routes and candidates, investigate a bounded shortlist, and produce traceable evidence and next verification steps.

The current **PREP-BASELINE-20261029** engineering configuration is approved. Read [SPEC](SPEC.md), [PLANS](PLANS.md), [current contracts](docs/contracts/CURRENT_CONTRACTS.md) and the [sole evaluation protocol](docs/evaluation/CURRENT_EVAL_PROTOCOL.json). Actual checks, independent file review, the single 18-item preparation checklist and the proposed first business task live in the [continuous record](docs/features/DECISION-001/tasks.md). Configuration approval is not business implementation or live-run authority.

The target is independent API, Worker/LangGraph stages and a new independent PostgreSQL cluster inside WSL, with Windows accessing the UI. Direct Search/GitHub/Fetch lead; DeepSeek is the single Search/Fetch supplier. Browser stays disabled until connection-layer qualification. The first proposed slice is **DEC-M1-01: real login, persistent raw drafts, owner isolation and minimal supervisor**, with no research calls. Its source and environment package need separate authorization.

Existing source includes Vue/FastAPI/AgentLoop/SQLite and a separate historical Pg API/Worker. [P-01 fake-task48/48](docs/tasks/P01_ACCEPTANCE_2026-10-21.md) applies to the old Windows/Pg topology. Historical r12 attempts and r11 research failures remain No-Go. Offline tests and fake demos do not establish source truth, product value or recovery safety. [Documentation map](docs/README.md), [architecture](docs/architecture/README.md) and [task index](docs/tasks/README.md) distinguish current design from implemented evidence.

## Local checks

Use already installed, locked dependencies. The repository `.nvmrc` and CI declare Node22; local availability is recorded separately. These commands describe checks, not authority to install dependencies or start services:

```powershell
.\.venv\Scripts\python.exe -B scripts/validate_project.py
.\.venv\Scripts\python.exe -B -m pytest -q backend/tests/unit
.\.venv\Scripts\ruff.exe check --config backend/pyproject.toml backend/src backend/tests scripts
```

Review the actual task scope before running integration tests. Real PostgreSQL, WSL, migrations, models, Tokenizer, Browser, purchases and external writes require the relevant qualification and authority. Remote CI status must be observed; local declarations are not evidence it ran.

## Historical implementations

[V1 specification](docs/specs/V1_SPEC.md), [V1 contracts](docs/contracts/V1_CONTRACTS.md), [backend notes](backend/README.md), [P-01 launcher/task package](docs/tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md) and [historical design index](docs/archive/design-0.3/00_DESIGN_INDEX.md) explain existing code. The old launcher can start WSL/Pg and automatically migrate. It is not the new startup path and must not be invoked to discover new environment state.

Historical evaluation protocols are read by explicit fixed Git commit/path/raw SHA and explicit newline transform where required. They are not a second current release rule. The old runner cannot execute the new protocol; this configuration package adds validation and rejection guards, not a new runner or funding system.

Keep credentials server-side, outside prompts/logs/events/diffs. Preserve original SQLite/r12, fee and authorization records, genuine sources and the upstream-owned `browser-use/` checkout. No startup/reset/cleanup may erase those records. Exact cold switch and rollback are in the current contracts and the separately authorized environment package. Commit/push/PR, merge and release each retain their applicable authorization.
