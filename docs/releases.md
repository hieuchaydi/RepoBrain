# Releases

## Release Philosophy

RepoBrain should evolve like an engine product, not like a random collection of experiments. Each release line must answer one clear question:

- `0.1.x`: does the product run and feel coherent?
- `0.2.x`: does retrieval quality improve in a measurable way?
- `0.3.x`: can downstream agents trust the outputs more?
- `0.5.x`: is it easy to integrate into real workflows?
- `1.0.0`: are the contracts stable enough to depend on?

## `0.1.x` MVP Line

Theme:

- get the local-first thesis working end to end

User value:

- index a repo
- ask grounded codebase questions
- get edit targets instead of vague advice

Must-have:

- CLI commands work locally
- storage exists under `.repobrain/`
- output schema is consistent
- docs explain the product clearly

## `0.2.x` Retrieval Quality Line

Theme:

- move from useful heuristic engine to stronger structural retrieval

Must-have:

- optional tree-sitter adapters with heuristic fallback
- better symbol boundaries
- better reranking and graph extraction
- benchmark improvements on acceptance queries

## `0.3.x` Trust Line

Theme:

- make RepoBrain safer for planning and code-change workflows

Must-have:

- more honest confidence
- contradiction handling
- better impact analysis
- stronger change-context packaging

## `0.5.x` Integration Line

Theme:

- make RepoBrain easy to embed in real agent workflows

Must-have:

- clearer provider integration with SDK-backed optional adapters, including Gemini cheap mode
- Gemini rerank model pools with quota-exhaustion failover for higher uptime under shared API limits
- local report/dashboard visibility for provider posture and Gemini fallback state
- a direct provider smoke command for live-key validation before release
- a React TSX browser frontend with bilingual English/Vietnamese UI
- a light/dark web theme and structured diagnostics cards for doctor/provider smoke posture
- live-key smoke guidance for remote providers
- richer MCP examples
- smoother CLI ergonomics, including local interactive chat
- stronger troubleshooting and operational docs

## `1.0.0` Stable Product Line

Theme:

- a dependable local codebase memory product with stable interfaces

Must-have:

- stable output contracts
- mature parsing strategy
- clear release discipline
- benchmark-backed trust story

## Release Rule

Do not cut a new version because code changed. Cut a new version because a user-facing capability became meaningfully more complete or more trustworthy.

## Release Automation

RepoBrain has a manual GitHub Actions workflow at `.github/workflows/release.yml`.

- Run it with `publish = false` to build and inspect release artifacts.
- Run it with `publish = true` only after release notes, version, URLs, tests, and smoke checks are complete.
- Use [release-checklist.md](release-checklist.md) as the human gate before publishing.
