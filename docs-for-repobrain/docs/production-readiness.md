# Production Readiness

RepoBrain is still pre-`1.0`, but it now has a concrete path toward being safe to open-source and use as a local retrieval layer.

## Current Readiness

Status: alpha, open-source ready after the remaining gates below are complete.

What is ready:

- Local-first indexing and retrieval
- CLI and local chat loop
- Human-readable terminal output through `--format text`
- Active repo memory after `repobrain init --repo <path>` for shorter daily CLI usage
- Saved review baselines through `repobrain baseline`
- Production ship gate through `repobrain ship`
- Static local HTML status report through `repobrain report`
- Local browser UI through `repobrain serve-web`
- One-click Windows launchers for chat and local dashboard flows
- Stdio JSON MCP-style adapter
- Tree-sitter optional parser path with heuristic fallback
- Stable local vector hashing
- Basic provider and security diagnostics
- SDK-backed optional provider adapters for Gemini embeddings/reranking, OpenAI embeddings, Voyage embeddings, Cohere reranking, and Groq reranking
- Regression tests for parser fallback, retrieval warnings, MCP validation, index health, and launcher behavior
- MIT license and package metadata
- CI workflow for Python `3.12` and `3.13`
- Manual release workflow that builds wheel/sdist artifacts and can publish with explicit approval
- Release artifact inspection through `repobrain release-check`

What is not production-grade yet:

- Confidence scores are calibrated by rules, not by a large benchmark set
- Graph edges are useful hints, not guaranteed runtime truth
- Remote provider paths are SDK-backed but still need live-key smoke testing outside CI
- There is no published package yet
- Benchmarks are fixture-based and need more real-world repos

## Open-Source Release Gates

Before the first public GitHub release:

- Run the full test suite on Windows and Linux.
- Confirm `repobrain doctor` reports local providers ready and parser fallback available.
- Confirm `repobrain index` excludes `venv`, `.repobrain`, caches, build outputs, and generated files.
- Confirm `repobrain query`, `trace`, `impact`, `targets`, `benchmark`, `chat`, and `serve-mcp` all start successfully.
- Confirm `repobrain init --repo <path>` lets `repobrain index` and `repobrain query` run without repeating `--repo`.
- Confirm `repobrain baseline` saves `.repobrain/reviews/baseline.json` and `repobrain ship` reflects delta status on the next run.
- Confirm `repobrain report` generates `.repobrain/report.html`.
- Confirm `repobrain serve-web --open` starts a local browser UI and the import form can index a sample repo.
- Confirm `repobrain report --open` and `report.cmd` open the generated dashboard on Windows.
- Confirm at least one command with `--format text` is readable for non-agent users.
- If enabling remote providers, copy `.env.example` to `.env`, run `repobrain doctor --format text`, and run one live-key smoke query for the selected provider.
- Replace placeholder GitHub URLs in `pyproject.toml` if the final repository URL is different.
- Run the manual release workflow once with `publish = false` and inspect the built wheel/sdist artifact.
- Run `repobrain release-check --require-dist --format text` against the built artifact directory before tagging.
- Add a short demo GIF or terminal recording to the README.
- Tag the first release as `v0.1.0`, `v0.2.0`, or `v0.5.0` depending on the release line. The current provider-plus-browser integration track now maps most closely to `v0.5.0`.

## Runtime Safety Gates

RepoBrain should preserve these rules before production use:

- Do not send code to remote providers unless the user explicitly configures them.
- Keep `.repobrain/` local and ignored by default.
- Treat MCP input as untrusted.
- Warn when retrieval evidence is weak, narrow, or contradictory.
- Never mutate source files in v1.

## Quality Gates

Minimum quality bar for a public release:

- `python -m compileall src tests` passes.
- `python -m pytest -q` passes.
- Built-in benchmark returns non-zero recall and edit-target hit rate.
- At least one runtime-flow query ranks source files above test files unless the query asks for tests.
- Runtime-flow queries warn and lower confidence when evidence only appears in test files.
- Low-evidence queries return warnings and lower confidence than grounded queries.
- `build_change_context` returns compact payloads with warnings and confidence.

## Recommended Next Milestones

### `0.2.x`

- Improve role detection for frameworks and fixtures.
- Expand benchmark cases beyond the current sample repos.
- Add graph-edge tests for default imports, namespace imports, aliases, and relative imports.

### `0.3.x`

- Add fixed confidence calibration bands.
- Add contradiction tests across provider, route, job, and config surfaces.
- Improve warning wording for downstream agents.

### `0.5.x`

- Add live-key smoke tests and examples for Gemini, OpenAI, Voyage, Cohere, and Groq provider adapters.
- Add richer MCP examples for Cursor, Codex, and Claude Code.
- Validate the wheel/sdist contents after the frontend-aware release workflow build.

## Release Decision

RepoBrain is ready to open-source when:

- CI is green.
- README quickstart works from a clean clone.
- `docs/install.md` and `docs/production-readiness.md` are accurate.
- At least one demo scenario can be reproduced in under five minutes.
- Known limitations are documented instead of hidden.
