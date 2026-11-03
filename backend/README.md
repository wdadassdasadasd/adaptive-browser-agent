# Adaptive Research Python backend

The backend contains API/application/agent/persistence/Worker and historical evaluation code. Read [SPEC](../SPEC.md), [PLANS](../PLANS.md), [current contracts](../docs/contracts/CURRENT_CONTRACTS.md), [sole protocol](../docs/evaluation/CURRENT_EVAL_PROTOCOL.json) and the [single task record](../docs/features/DECISION-001/tasks.md) before work.

The approved target is independent API/Worker and a new independent Pg cluster in WSL; Windows accesses the UI. Application tables own business state, permissions, stable work/call identities, evidence and cost. LangGraph checkpoints only reference bounded committed data. Ordinary startup validates identity/schema without DDL or checkpoint setup. The planned first business slice is real authentication/raw drafts and minimal supervisor, not research execution; its new entry and migrations are not created by this configuration package.

The RESEARCH-BASELINE-20261103 configuration targets four modes: review, requirements drafting, solution drafting from explicitly confirmed requirements, and their full flow. Inputs may be ideas without a repository, one pinned main repository, or explicitly selected local text/source/diff snapshots. Source code is read only, never executed or changed. Personal drafts stay owner-isolated; later team/project sharing is explicit. Private-source App grants, Task execution permission and read-session permission are distinct. Browser remains zero and deferred, MCP research only. Public-source live work retains all Token/Gateway/funding/minimum-recovery prerequisites.

Memory remains disabled and deferred across manual/automatic, API/CLI, profile/framework, old checkpoint, import/restore/rebuild and background entry points: no candidates, reads, writes, retrieval or injection. Empty active refs must match actual requests; Trace records disabled/not_applicable, null hits/writes and feature_disabled. Case data persists; explicitly selected history follows SourceSet permissions/private ancestry without Memory dereference. 04/17 remain unimplemented/unverified, outside current M1; reserved capacity stays idle. Reopening requires real reuse evidence, independent review and separate approval. Details belong to the [current contracts](../docs/contracts/CURRENT_CONTRACTS.md); Context belongs to 03a and Token qualification to 03b.

The public material index is pending independent preparation; this batch supplies no formal prompts/gold or material-ready verdict. Three raw Agent deliverables (both first requirements and first solution in the full flow), six human final delivery packages and descriptive time comparison have separate gates. REQ covers the full flow, CON review including a no-authoritative-baseline subquestion in both variants, and EXP solution-only; requirements-only termination and editing/revision have focused regressions/pilot observation, not independent formal effect claims.

The target main researcher may delegate independent topics as same-Task Work branches. The application owns assignment/head checks, stable call identities, shared consumers, research-input sealing, quotas and cleanup. Existing AgentLoop and provider code do not thereby implement these contracts. Six program-selected purposes share the bounded pool; document_compile is at most four physical attempts including retries, with first-attempt-only reservation. Local public-template counts, hosted request fit and actual usage/cache/fees remain distinct. See [target prompt contracts](../docs/contracts/PROMPT_CONTRACTS.md); legacy runtime prompt modules are unchanged.

## Checks and qualification

Use the already installed locked environment for scoped offline tests. From `backend`, the focused configuration suite is:

```text
..\.venv\Scripts\python.exe -B -m pytest -q -rs -p no:cacheprovider -p pytest_asyncio.plugin tests/unit/test_validate_project.py tests/unit/test_current_evaluation.py tests/unit/test_pilot_runner.py tests/unit/test_pilot_capture.py tests/unit/test_project_ledger.py tests/unit/test_pilot_cost_reconciliation.py tests/unit/test_legacy_entry_guards.py
```

Record actual command/exit/results and skipped checks. Database integration needs a specifically authorized isolated restricted database; missing DB/skip is not pass. Do not automatically sync/install dependencies, start WSL, migrate, call models/Tokenizer/Browser or use paid tools. Existing Python/Node metadata and old P-01 evidence do not prove the new Linux environment is qualified.

## Historical entry points

The existing SQLite entry is `adaptive_research.api.main:app`; the P-01 Pg entry is `adaptive_research.api.pg_main:app` and Worker is `adaptive_research.worker.runner`. Their source and [dated P-01 task record](../docs/tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md) define actual behaviour. The old launcher can start services and migrate automatically; it must not be used as the new startup or a read-only probe. Old Pg/SQLite data, cost/unknown and authorization evidence stay protected.

The old `evaluation.current`, `pilot_runner`, `pilot_budget --arm` and cost reconciliation understand historical current-3 data. The new sole protocol is draft-m1-3; old execution/arming/reconciliation entry points must reject its use before constructing Settings/client/engine or creating output/ledger writes. Configuration changes do not supply a new runner. Explicit fixed-Git historical read validation is distinct from ledger extension, reservation and execution, each of which retains separate authority.

The 2026-10-22 price book and 10.57 CNY account observation are dated evidence, not current balance, new grant or new-product pricing qualification. Unknown results stop new project outbound; local count, provider usage/cache, price and balance are separate. Independent review, human acceptance and product Go remain separate from tests and from configuration approval.
