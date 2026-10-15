# V1 benchmark protocol

Status: D6 runner, deterministic scorer, and redacted records implemented
(2026-10-12); no 18-run real result exists. Do not report an improvement
percentage before the real runs and raw data exist.

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

Save one redacted JSON record per run under `data/benchmark/` containing case
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
