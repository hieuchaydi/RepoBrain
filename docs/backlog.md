# Backlog

## P0

- add confidence calibration tests with fixed score bands
- deepen tree-sitter symbol extraction once optional parser packages are installed in CI
- improve retrieval fusion beyond simple weighted merging
- align README examples with real fixture outputs

## P1

- richer role detection for routes, callbacks, config, and background workers
- more compact `build_change_context` payload for downstream agent prompts
- expand provider smoke coverage and live-key examples for Gemini, OpenAI, Voyage, and Cohere adapters
- benchmark runner that can target fixture repos independently
- richer interactive chat summaries instead of raw JSON only
- deepen `/map`, `/evidence`, `/focus`, `/summary`, and `/multi` into first-class answer modes instead of mostly retrieval wrappers
- add summary compaction and eviction rules so long-running repo memory stays useful instead of drifting into noisy notes

## P2

- true cross-repo retrieval/index federation instead of per-repo fan-out orchestration
- add a shared multi-repo retrieval layer so `/multi` can rank evidence globally before grouping it back by repo
- graph export for visualization
- IDE-native formatting helpers for citations and evidence blocks
- richer demo assets and benchmark reports
- share visual tokens and brand components across `repobrain report`, `serve-web`, and docs surfaces instead of maintaining the branding separately in each layer

## Deferred

- browser research MCP
- omniretrieval across personal data
- autonomous repo mutation
- hosted dashboard
