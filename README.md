# Adaptive Research Agent

A document-to-deliverable assistant for development teams. The first product slice drafts requirements and engineering designs from ideas or existing materials, and retains evidence-based document review. Four modes are review-only, requirements-only, solution-only from explicitly confirmed requirements, and the full requirements → human confirmation → solution flow. Ideas may have no repository; inputs can include one pinned main GitHub repository, permitted public evidence, and explicitly selected local text, source code or diff snapshots. It does not verify code execution or automatically approve designs.

The **FOCUS-BASELINE-20261102** 28-file configuration plan under FOCUS-20261102-01 is approved. Read [SPEC](SPEC.md), [PLANS](PLANS.md), [current contracts](docs/contracts/CURRENT_CONTRACTS.md) and the [sole evaluation protocol](docs/evaluation/CURRENT_EVAL_PROTOCOL.json). Actual implementation/check/review status and the single 18-item checklist live in the [continuous record](docs/features/DECISION-001/tasks.md). Earlier deliveries attest their original reviewed bytes, not this revision. Approval is not business or live-run authority.

The target is independent API, Worker/LangGraph and a new independent PostgreSQL cluster in WSL, with a Windows UI. GitHub document reading leads; DeepSeek Search/Fetch supplies permitted public gap evidence. Browser stays zero with real integration deferred; MCP remains research. The first separate business slice is **DEC-M1-01: real login, persistent personal raw drafts, owner isolation and minimal supervisor**, without InputRevision, research Task or calls. Team/project/source grants follow in later slices.

The seven-to-eight-week window prioritizes the requirements-to-solution flow and the owner's explanation. The old 92–136h vertical-slice and 130–194h full-scope estimates do not promise delivery of this expanded scope; actual owner effort is unknown, not zero, and the ≤20h/week limit is unchanged. It does not promise the complete first stage or M1. Live public-model work still needs supervisor, exact-request/Token qualification, complete funding and minimum independent recovery qualification. Until then, offline substitutes must be labelled. Private sources and full recovery coverage retain their prerequisites. Memory is deferred outside current M1, remains unimplemented/unverified and is not counted as a pass.

Current M1 disables every Memory feature entry, including manual/automatic, API/CLI, profile/framework preload, old checkpoint refs, import/restore/rebuild and background paths. No candidate extraction, reads, writes, retrieval or model injection are allowed; empty active Memory refs must match actual requests. Trace uses disabled/not_applicable and null hits/writes with feature_disabled. Case evidence and documents persist; explicitly selected historical reports use current SourceSet permission/private-ancestry checks without resolving Memory refs. Complete Context belongs to 03a, Token qualification to 03b; 04 is not a current prerequisite. Reopening needs real reuse evidence, independent review and separate approval; reserved Memory capacity is not reassigned.

## Local checks

Use already installed tools within the actual task scope:

```powershell
.\.venv\Scripts\python.exe -B scripts/validate_project.py
git diff --check
```

The [test strategy](docs/testing/STRATEGY.md) names the focused suite. The public material index remains pending independent preparation: this batch creates no new formal prompts/gold. Default validation checks configuration, not material readiness, semantic source truth, real value or personal mastery. Database, WSL, dependencies, services, models, Tokenizer, Browser, purchases and external writes retain separate authorization. CI declarations do not prove a remote run.

## Historical implementations

Current code still includes Vue/FastAPI/AgentLoop/SQLite and the historical Pg API/Worker. [V1 specification](docs/specs/V1_SPEC.md), [V1 contracts](docs/contracts/V1_CONTRACTS.md), [backend notes](backend/README.md), [P-01 fake-task48/48](docs/tasks/P01_ACCEPTANCE_2026-10-21.md) and [task index](docs/tasks/README.md) define their evidence boundaries. Historical r11/r12 failures and P-02 No-Go remain. Offline tests cannot establish new-product source truth or recovery safety.

The [old launcher](docs/tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md) can start services and migrate; it is not a new startup path or read-only environment probe. Historical protocols are read by explicit fixed Git commit/path/raw SHA and explicit newline transform where required. Old runners reject the new protocol; configuration adds validation, not a new runner or funding system.

Keep credentials server-side, outside prompts/logs/events/diffs. Preserve SQLite/r12, fees, authorizations, genuine sources and upstream-owned browser-use. Cold switch and rollback follow the current contracts and separately authorized environment package. Commit/push/PR, merge and release each retain separate authority.
