---
name: agent-failure-triage
description: Diagnose a failed Adaptive Research Agent task from raw traces, persisted events, report, usage, and source version. Use for call-level failure investigation and root-cause hypotheses; routine test failures without an agent trace need ordinary debugging.
---

# Agent failure triage

Start with the task/run ID and exact code version. Read `AGENTS.md`, the contract applicable to that run, and `docs/archive/design-0.3/07_AI_CODING_WORKFLOW.md`. Existing code may still be V1 while `SPEC.md` is a future target; use archived contracts only for runs made under them. Keep r12 and other benchmark records immutable. Work from redacted local evidence; avoid copying secrets or untrusted page text into prompts or reports.

1. Assemble the input goal, task status, report, persisted application events and call-attempt ledger, action/tool results, planner and evaluator decisions, model usage and budgets, and cleanup outcome. Mark a started call without a returned result as `unknown_outcome` and its billable cost unknown until observed; do not infer success or zero. When a run used checkpoints, inspect them and recovery attempts separately from application facts. Mark missing sources and their effect on confidence.
2. Align these records by run ID, step, and time. Identify the first observable divergence from the expected data flow, then distinguish technical failure, unsupported action, insufficient evidence, goal mismatch, premature stop, and reporting or scoring errors. An earlier symptom is not automatically the cause.
3. For each candidate root cause, cite specific event or file-and-line evidence, alternative explanations, and a focused reproduction or falsification test. Compare source behavior with the current contract; classify facts as verified, inferred, or unverified.
4. Produce a concise timeline, impact on the requested output, ranked falsifiable hypotheses, next diagnostic action, and any safe bounded workaround. For an optimization claim, link the failed call to the focused change, offline regression and authorized real recheck; keep comparisons descriptive unless stronger evidence exists. Do not change business code or rerun paid models unless the current task explicitly authorizes those actions.

Completion means another engineer can reproduce or disprove the leading hypothesis from named records and can see exactly where evidence is still missing.
