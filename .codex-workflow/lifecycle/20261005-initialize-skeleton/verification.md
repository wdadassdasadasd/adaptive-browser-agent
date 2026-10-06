# Verification

- `uv lock --check`: passed; 282 packages resolved.
- `uv run pytest -q`: passed; 13 tests.
- `uv run ruff check adaptive_agent backend benchmark tests`: passed.
- `uv run ruff format --check adaptive_agent backend benchmark tests`: passed;
  52 files already formatted.
- Python `compileall`: passed.
- `uv build` to a temporary directory: passed; source distribution and wheel
  produced.
- Real Uvicorn startup: passed; OpenAPI returned exactly the six requested
  research operations and `GET /api/research` returned HTTP 200 with `[]`.
- Forbidden V1 stack/import scan: no project-source matches.
- browser-use boundary scan: only the adapter and opt-in manual baseline smoke
  script import browser-use.
- Upstream browser-use checkout: clean and pinned to
  `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`.

Real Chromium and external DeepSeek, GitHub, and OpenAI calls were not exercised
because the network-backed research flow remains explicit `TODO(V1)` work.
