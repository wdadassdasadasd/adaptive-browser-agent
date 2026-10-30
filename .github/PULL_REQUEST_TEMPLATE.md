## What / Why

<!-- State the user-visible change or defect and why it matters. -->

## Requirement / Task / AC IDs and affected components

<!-- Link the approved requirement, task package, AC, and issue if any. Name affected modules, dependency/milestone scope and important design decisions. -->

## Behavior / contract changes

<!-- Include API, event, state, persistence, or UI compatibility changes; write None if not applicable. -->

## Tests executed, CI, and verification evidence

<!-- For each AC, mark verified, partial, or pending within this PR's scope. Give commands, exit codes, evidence links, and the actual CI result. State skipped checks and why. Offline/Mock results do not prove real Agent success. -->

## Business acceptance

<!-- Give runnable entry points, key changes, human acceptance steps/expected behavior, actual human decision, and unverified items. Separate technical checks from business acceptance; pending human acceptance stays pending. -->

## Agent task evidence, if applicable

<!-- Link task/run IDs, version, redacted trace, accepted fact IDs, report hash, human source review, actual/unknown usage and cost. Write Not run when no real task was authorized. -->

## Review and approvals

<!-- State independent reviewer/context and specialty, original requirement/AC, reviewed base/content, full task diff (committed/staged/unstaged/task-owned new files), verified findings, fixes, retests/re-review and final-content consistency. Ordinary behavior changes require independent review; security boundaries need scoped security review. State actual Commit/Push/PR authorizations after a reviewable handoff; merge/release approval is separate. For shared config and project adaptation, identify each repository/version/review scope separately. -->

## Risks / limitations / rollback

<!-- Include unverified behavior and the safe rollback path. -->

## Delivery and release status

<!-- Distinguish code ready to commit/merge from product Go. State the current stage decision and the evidence still needed for release. -->

## Reviewer checklist

- [ ] Diff matches the approved scope and contains no secrets or historical data edits.
- [ ] Architecture and contract impact, failure paths, permissions, tests, and acceptance evidence were checked.
- [ ] Independent review applies to the final task content; fixes were verified, retested and re-reviewed where behavior changed.
- [ ] Technical validation and human business acceptance are reported separately.
- [ ] Remaining unknowns, cost and rollback are explicit; approved protocol changes and their compatibility are identified, while historical evidence and byte identities remain protected.
