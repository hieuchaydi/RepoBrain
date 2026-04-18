# Changelog

## Unreleased

### Docs

- Added user experience guide for terminal text output, chat mode, and local report flow
- Fixed and expanded bilingual installation docs, including one-click dashboard usage
- Added production readiness guidance and OSS release gates
- Added release checklist and manual release workflow documentation
- Added MIT `LICENSE`
- Added GitHub Actions CI workflow for Python `3.12` and `3.13`
- Added a release-driven project narrative for `0.1.x` through `1.0.0`
- Added bilingual English/Vietnamese installation instructions
- Added a dedicated run guide with local setup, CLI usage, and troubleshooting
- Added a feature-direction file to capture next moves after the current MVP
- Added repo-level `RULES.md` and `SKILLS.md` to keep feature cycles consistent
- Documented `repobrain chat`, the Windows `chat.cmd` launcher, and parser capability configuration
- Documented optional remote provider SDK installation, `.env` setup, API keys, model options, and local-first safety rules

### Release

- Added a manual GitHub Actions release workflow for wheel/sdist builds
- Kept PyPI publishing behind an explicit `publish = true` workflow input
- Updated CI and release automation to build the React web frontend and package `webapp/dist` with Python artifacts

### Engine

- Added SDK-backed optional OpenAI and Voyage embedding providers
- Added SDK-backed optional Cohere reranker provider
- Added SDK-backed optional Gemini embedding and Gemini Flash reranker providers
- Added ordered Gemini rerank model pools via `GEMINI_MODELS` / `gemini_models` with automatic failover on quota and rate-limit exhaustion
- Added repo-root `.env` loading without overriding existing shell environment variables
- Added `.env.example` with cheap Gemini setup using `gemini-embedding-001` and `gemini-3-flash-preview`
- Added provider model option wiring for `repobrain.toml` and environment overrides
- Added test-surface ranking penalties so runtime queries prefer route/service/source files unless the query asks for tests
- Added confidence downgrade and warnings when non-test queries only find test-file evidence
- Added confidence calibration band tests for grounded vs weak evidence
- Fixed local hash embeddings to use stable `blake2b` slots instead of Python process-randomized `hash()`
- Improved Python and TS/JS named import extraction so `imports_call` edges capture imported bindings and aliases
- Made index reset more Windows-friendly by rebuilding SQLite schema instead of unlinking the database file
- Hardened `indexed()` so empty or partially-created metadata databases are not treated as usable indexes
- Improved lexical score normalization for FTS retrieval
- Expanded default indexing excludes for local virtualenv and pytest temp folders
- Reworked retrieval fusion to combine query variants and source diversity more cleanly
- Made `build_change_context` more compact and planning-oriented
- Added stronger warnings for narrow or single-source evidence
- Added contradiction-aware warnings for mismatched provider or surface evidence
- Added an optional parser adapter layer that prefers tree-sitter when available and falls back to heuristics
- Added parser usage counts to `repobrain index`

### CLI

- Added active repo memory so `repobrain init --repo <path>` lets later commands omit `--repo`
- Added `repobrain serve-web` for a local browser import and query flow
- Reworked the local browser UI into a React TSX frontend with English/Vietnamese interface labels
- Added a light/dark theme toggle and structured diagnostics cards for `doctor` and `provider-smoke` in the React web UI
- Added `--format text` for human-readable terminal output while keeping JSON as default
- Added `repobrain provider-smoke` to validate configured embedding and reranker providers directly
- Added `repobrain report` to generate a local static HTML dashboard
- Added `repobrain report --open` for opening the generated dashboard in the default browser
- Added `repobrain quickstart` for new-user onboarding
- Updated chat mode to use readable text by default with `/json` and `/text` toggles
- Added `report.cmd` as a Windows-friendly one-click local dashboard launcher
- Added `python -m repobrain.cli` entrypoint support for source-tree launchers
- Updated `chat.cmd` to prefer `venv\Scripts\python.exe` or `.venv\Scripts\python.exe` before falling back to global Python
- Added `repobrain chat` for a local interactive question loop
- Added `chat.cmd` as a Windows-friendly one-click local chat launcher
- Expanded `repobrain doctor` output with provider model details and Gemini fallback pool visibility
- Updated the local HTML report to surface provider posture, active reranker model, Gemini fallback pool, and last failover event
- Added a web action for provider smoke checks from the local browser UI

### Security

- Added provider readiness and security posture details to `repobrain doctor`
- Hardened MCP tool validation for unknown tools, invalid arguments, and oversized queries
- Expanded security and run docs with local-transport and remote-provider guidance

## 0.1.0

- Initial RepoBrain MVP
- Local CLI for init, index, query, trace, impact, targets, benchmark, doctor, and serve-mcp
- SQLite metadata store plus persisted vector index
- Python + TS/JS scanning with heuristic symbol extraction
- Hybrid retrieval and evidence-driven edit target ranking
- OSS launch documentation and fixture-backed tests
