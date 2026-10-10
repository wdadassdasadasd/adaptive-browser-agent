# Day 01 verification

The audit compares the initial clean checkout with actual source and baseline
tests. The target contract is explicitly separate from the current skeleton.
Browser actions use checked-out browser-use APIs and have fake-backed unit
tests plus one opt-in real Chromium test against a controlled local page.
The detailed command observations are in `evidence/day01.txt`.

Remaining unverified: remote CI, live DeepSeek/GitHub calls, all seven actions
on arbitrary public pages, integrated AgentLoop/API/SSE, frontend, benchmark,
and V1 acceptance. The URL gate checks the redirect destination only after
navigation, so the demo must not be offered as a public SSRF-safe service.
