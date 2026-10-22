---
name: research-implementation
description: Implement an explicitly authorized Adaptive Research Agent business task from the current specification, plan, and contracts through scoped verification and acceptance evidence. Use for business-code work; design-only preparation has its own scope.
---

# Authorized research implementation

Use this skill only when the user has authorized a specific implementation task. Locate the repository root. Check `AGENTS.md` and the four current entry points: `SPEC.md`, `PLANS.md`, `docs/contracts/CURRENT_CONTRACTS.md`, and `docs/evaluation/CURRENT_EVAL_PROTOCOL.json`. Archived designs are historical. Read only relevant requirements, source, and tests. Existing behavior remains governed by `docs/specs/V1_SPEC.md` and `docs/contracts/V1_CONTRACTS.md` until an authorized task changes it.

1. Identify the authorized Task ID, linked requirement and acceptance IDs, affected modules, current behavior, and smallest contract change. If requested behavior conflicts with an applicable clause, identify both and obtain a design decision before changing behavior.
2. Reproduce material bugs where feasible. Plan the state, API, event, persistence, browser lifecycle, ownership, and compatibility impact actually touched. For target work, read [ADR-0005](../../../docs/design/adr/0005-windows-worker-wsl-postgres.md): Windows API/Worker and WSL PostgreSQL application tables own business truth; call attempts and fencing are durable, while any later checkpoint only assists execution recovery. P-01's two-week gate pauses paid pilot on failure. Keep `browser-use/` upstream-owned; prefer project adapter changes before an explicitly authorized upstream patch.
3. Implement within the authorized scope, with meaningful regression tests for behavior changes. Preserve unrelated work and original benchmark records. Use the applicable risk level and checks in `docs/archive/design-0.3/07_AI_CODING_WORKFLOW.md`.
4. Review the scoped diff against the requirement and architecture boundaries, then run the relevant offline checks. Record exact commands, exit codes, evidence, skipped checks, and remaining risk. A real model/browser evaluation requires separate explicit cost and execution authorization.
5. Report each acceptance criterion as verified, implemented but unverified, blocked, or failed, based on actual evidence. Include changed files and unresolved findings. Commit, push, PR, merge, and deployment require their own authorization.

Completion means the authorized task has a traceable scoped diff, relevant test evidence, and an honest acceptance state; implementation alone is not acceptance.
