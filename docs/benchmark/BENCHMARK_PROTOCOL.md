# V1 benchmark protocol

Protocol revision: **V1-D7-r12 (2026-10-16)**. Before any formal D7 benchmark
attempt, a real B01 UI diagnostic failed after subgoal initialization because
the Planner requested unsupported actions (`browser/search` and a malformed
GitHub repository target). The Planner prompt now enumerates the existing
tool actions and target forms, and one bounded correction handles an invalid
action contract. Real acceptance also exposed all-or-nothing fact rejection,
release facts whose subject is anchored by an official repository URL, and a
premature target-count stop; those Adaptive behaviors were corrected before
the formal batch. The initialization prompt now keeps 1–3 high-level,
tool-agnostic evidence subgoals after real runs showed over-specific
browser-display criteria. This changes Adaptive internals, so the revision is
explicit; the three fixed case prompts, Expected Fields,
scoring rules, arms, and budgets below are unchanged. The failed UI diagnostic
and bounded direct diagnostics are not benchmark attempts. Formal comparisons
must use one code fingerprint and this revision across all three arms. The
first real r3 batch is retained as a historical failed batch: its raw JSON
omitted an explicit per-attempt `run_id`, which r4 adds before saving each
record. This identifier change does not alter the prompts, scoring or Agent
behavior; r4 received a separate complete three-arm batch. The r4 batch
exposed a project-count inconsistency: Evaluator admitted an exact official
repository URL as identity evidence, while the quantity check ignored it.
r5 shares that identity rule between both components and receives another
complete three-arm batch. The r4 batch also showed a browser kill exceeding
the previous five-second cleanup allowance; r5 allows 20 seconds and awaits
the cancelled close briefly before returning a bounded failure. Historical
r3/r4 records remain untouched. A scoped read-only review of r5 found that a
GitHub non-repository route could anchor a project name and that a `change`
fact could incorrectly use the project-only URL identity exception. r6 limits
that exception to recognized repository/release routes and project facts; it
requires a complete new three-arm batch. Historical r5 records also remain
untouched. A second scoped read-only review found that other GitHub site
namespaces (`sponsors`, `apps`, `issues`, `pulls`) could still be mistaken for
repository owners. r7 excludes these and other reserved site routes
case-insensitively, with failure-first tests. Fixed case prompts, Expected
Fields, scoring rules, budgets, and arms remained unchanged through r7. The
DeepSeek account returned HTTP 402 `Insufficient Balance` during r6. After
balance was restored, r7 ran all 18 real attempts. Manual inspection found
that B03 full-r1 received publication-date credit for the previous version's
date, although the latest version's date was absent. r8 changes only that
scoring attribution: a publication date must belong to the claimed release
version. The fixed prompts, Expected Fields, arms, and budgets are unchanged.
The r7 records and their original scoring fields remain preserved; a complete
new three-arm r8 batch is required before comparing the corrected rule. The
r8 batch exposed another scoring false positive: a release title containing
"fixes" counted as a change even when no release-note change was stated.
r9 excludes quoted release titles from change extraction. The original r8
records and scores remain preserved; r9 requires a complete new three-arm
batch. The complete r9 batch then exposed a B01 attribution error: an
uncited Selenium license sentence in a comparison paragraph inherited the
next candidate's repository URL. r10 starts a new attribution block at an
explicit repository subject, so that sentence cannot score the next license.
The r9 raw records and original scores remain preserved; r10 receives a new
complete three-arm batch. Fixed prompts, Expected Fields, arms, and budgets
remain unchanged. An independent effective read-only review of the r10 staged
diff found two more scoring false positives: a bulleted repository subject did
not cut off the previous candidate's uncited license, and an unquoted release
title with change verbs counted as two release-note changes. r11 extends the
candidate boundary to bulleted/numbered subjects and excludes unquoted release
titles from change extraction. Both findings were reproduced by failing tests
before the fix. The r10 records, manual checks, and original scores are
preserved; r11 requires a new complete three-arm batch. Fixed case text,
Expected Fields, arms, and budgets are unchanged.

The complete r11 batch exposed one more B03 scoring false positive: its
GitHub page title appeared once as a Findings heading and again in the
Comparison section, so one actual described change scored as two. r12 excludes
version-prefixed GitHub page titles from change extraction. A failure-first
test reproduces the r11 answer. A scoped read-only pre-batch review also found
that `+` candidate bullets could inherit a previous license, unquoted titles
with semicolons could count as release-note changes, and valid changes in
Comparison or a version-prefixed change heading could be missed. Four more
failure-first tests cover those cases; r12 accepts all Markdown candidate
bullets, excludes the whole unquoted title sentence, and counts distinct
change claims in the answer while skipping only GitHub page titles. The r11
raw records, manual checks, and original scores stay intact; r12 requires
another complete three-arm batch. Fixed case text, Expected Fields, arms, and
budgets are unchanged. A final scoped read-only review found that a genuine
version-prefixed change ending in `· GitHub SSO` was also being skipped; its
failure-first regression tightened the page-title exclusion to lines ending
exactly in `· GitHub` before the r12 batch.

Status: D6 runner, deterministic scorer, and redacted records implemented
(2026-10-12). Real r3/r4/r5/r6/r7/r8/r9/r10/r11 batches are retained as D7 attempts; r12 is the
current code revision. Report only actual measured results and do not
infer an improvement from failed or budget-mismatched runs.

## Fixed cases and Expected Fields

Each case uses public unauthenticated sources. The exact prompts below are
fixed for both arms; the scorer checks field presence **with an attributable
source URL**, not a model's opinion. Values from changing sites are retained
in raw output and manually spot-checked, but no LLM grades them.

| ID / category | Fixed task prompt | Expected Fields |
| --- | --- | --- |
| B01 / candidate discovery | “Find two publicly documented Python browser-automation projects suitable for researching web pages. For each, give its name, official repository URL, license, and documented installation command. Cite official sources.” | Two distinct names; two official repository URLs; two licenses; two install commands; source URL for each item. |
| B02 / direct comparison | “Compare FastAPI and Flask for a small Python HTTP API using their official documentation. Explain how each declares a route, whether async handlers are documented, and how each is installed. Cite the exact official pages.” | Both project names; route declaration for each; async-handler statement for each; install command for each; official source URLs. |
| B03 / version/change research | “Find the latest public release of browser-use/browser-use and summarize its version, publication date, and two changes from its release notes. Cite the official release page.” | Version; publication date; two distinct changes; official release URL. |

Coverage is `sourced_expected_fields_present / total_expected_fields` for each
case. A field is present only when the output explicitly provides a value and
an official supporting URL; vague prose or a bare URL scores zero. Completion
is full field coverage with no obvious contradiction in a manual evidence
spot-check. A contradiction is logged separately and makes the run fail; the
spot-check is deterministic source inspection, not LLM-as-Judge. Count steps,
duplicate normalized URLs, prompt/completion tokens, wall-clock seconds, and
failure reason. Missing usage data is `null`/Unverified, never zero.

## Arms and fairness

1. **Baseline:** unmodified checked-out browser-use `Agent` with its
   `ChatDeepSeek(model="deepseek-flash")` and standard browser tools.
2. **Adaptive full system:** V1 Agent with browser and GitHub API tools.
3. **Adaptive browser-only mechanism:** same V1 Agent with GitHub tool disabled
   by the benchmark harness; this arm is compared with Baseline to discuss
   planning/replanning/deduplication mechanisms without GitHub API advantage.

The full-system result measures the complete product. Never attribute its
GitHub advantage to the Planner. The mechanism comparison still differs in
architecture and prompts, so report it as evidence rather than causal proof.
All arms use the same case text, DeepSeek model, machine/OS, Chromium version,
network connection, and source availability window. Run the arms in rotating
order across repetitions to reduce temporal bias. Do not change prompts or
Expected Fields after viewing results without versioning the protocol.

Two repetitions per case per arm are fixed (18 total runs). Each run has at
most 30 Agent steps, 900 seconds, and a 40,000 prompt+completion token budget.
The runtime/step/token numbers beyond the currently implemented 30-step
default are **Frozen V1 defaults (2026-10-09)**. The harness
must stop and record a budget breach rather than silently allowing an arm extra
work. If upstream usage is
not observable enough to enforce the same token cap, mark that comparison
budget-mismatched and avoid a controlled-mechanism claim.

## Run record and reporting

Save one redacted JSON record per run under `data/benchmark/` containing a
unique per-attempt `run_id`, case
and arm IDs, repetition, exact task/prompt hash, model, source git commits and
project and checked-out browser-use working-tree dirty flag/content SHA-256,
environment and browser versions, UTC start/end, status, redacted answer, observed
source URLs, safe step/action metadata trace, tokens or null, duplicate URL count, scorer fields,
manual contradiction note, and failure category. Keep the raw result and
failed attempts; do not replace them with a best run. Never save API keys,
cookies, authorization headers, or unrelated page secrets. Free-form extracted
page text is omitted from persisted traces; upstream `success` is recorded
separately and does not override protocol completion. The summarized
table reports completion rate, mean steps, duplicate URLs, tokens, latency,
and coverage per arm, with each run linked to its raw record. With only two
repetitions, describe variability and avoid significance claims.

`benchmark/manual_browser_use_smoke.py` currently uses `ChatOpenAI`; it is a
separate legacy manual smoke script, not the same-model benchmark baseline.
The benchmark runner must use checked-out `ChatDeepSeek` for the baseline.
External network, provider, or site failures are retained as failures with
their reason and are not counted as successful tests.

## D6 runner commands and D7 completion

`python -m benchmark.runner` prints the rotating 18-attempt plan without
external calls. `python -m benchmark.runner --live` executes it with
`DEEPSEEK_API_KEY` set server-side. `--case`, `--arm`, and `--repetitions`
select a smoke subset that remains protocol-incomplete. Each invocation uses
a unique `data/benchmark/<run-id>/` directory and writes one JSON record per
attempt plus `summary.json`. Failures are retained. A missing token total is
`null`; no null value is interpreted as zero.

The checked-out upstream Agent exposes usage after a step. The D6 baseline
aborts its step callback at 40,000 observed tokens before a post-step judge
request, and records an overshoot, but cannot
guarantee a pre-call cap. Baseline comparisons therefore remain
`budget_parity=mismatched`, even if measured totals stay below the limit.
No controlled advantage claim is allowed from these records.
Before live attempts, the harness starts the same default browser-use session
used by the arms, reads `Browser.getVersion` over CDP, closes the probe session,
and writes its product/version into each attempt's environment. If the probe
fails, attempts are still retained with `browser=unverified` and a
`browser_version_error`; browser-version fairness cannot then be claimed.
Duplicate URL counts use the sequence of observed page visits, collapsing
consecutive observations of the same normalized URL; a later return after
visiting another URL counts as a revisit. A failed browser action with no
observed URL is not a visit. The baseline interleaves upstream history's
pre-step page URLs with page URLs observed by its post-step callback, aligned
by the number of saved upstream history entries even if a step times out, and
uses the same contiguous-visit rule, since one page can produce multiple actions.
For raw records, URLs on the benchmark's official source hosts retain their
paths after credential-pattern redaction; other sites retain only the origin
to avoid persisting unknown secrets in page paths. URL duplicate counts use
visit URLs in memory before this persistence redaction, normalize only
scheme/host case, and remove fragments while retaining path/query case and
trailing slashes.

For D7, inspect each answer against its cited source and set each raw record's
`manual_contradiction_note` to `none` or a concise contradiction description.
Then run `python -m benchmark.runner --summarize data/benchmark/<run-id>` to
recompute the summary. Until every record has a note, the completion rate is
`null`; provisional full coverage is labeled separately. The deterministic
scorer checks explicit sourced fields, not factual truth on changing sites.
