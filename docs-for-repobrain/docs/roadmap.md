# Roadmap

## `0.1.x` Foundation

Goal:

- prove the local-first thesis with a working CLI and MCP-style tool surface

Includes:

- local indexing and `.repobrain/` storage
- Python + TS/JS heuristic scanning
- FTS plus vector retrieval
- evidence snippets, top files, edit targets, warnings, benchmark harness
- core docs for product, architecture, contracts, and evaluation

Exit criteria:

- a user can clone, install, index a repo, and ask grounded questions in under 10 minutes

## `0.2.x` Retrieval Quality

Goal:

- make results feel less heuristic and more structurally aware

Includes:

- optional tree-sitter parser adapter with heuristic fallback
- better route/job/config extraction
- improved retrieval fusion and reranking
- richer benchmark suites across public fixture repos

Exit criteria:

- top-file accuracy and trace quality noticeably improve on real multi-file queries

## `0.3.x` Trust And Change Planning

Goal:

- make the harness safer and more honest for downstream coding agents

Includes:

- stronger confidence calibration
- contradiction and low-evidence detection
- better impact analysis and dependency centrality
- tighter `build_change_context` outputs

Exit criteria:

- low-evidence queries warn consistently instead of sounding confident

## `0.5.x` Ecosystem And Integrations

Goal:

- make RepoBrain easier to plug into real developer workflows

Includes:

- stronger provider adapters for OpenAI, Voyage, Cohere, and Groq
- richer MCP ergonomics and examples
- better CLI polish, including the local `repobrain chat` loop
- more realistic fixtures and demo assets

Exit criteria:

- the repo can serve as a reliable local retrieval layer for external agents

## `1.0.0` Trusted Repo Memory

Goal:

- ship a stable local codebase memory product with reliable contracts

Includes:

- stable public output schema
- mature parser fallback plus optional deep parsers
- benchmark-backed retrieval confidence
- polished onboarding and contributor experience

Exit criteria:

- breaking changes become rare and contracts are ready to support outside adopters

## Deferred Beyond `1.0`

- Browser Search + Extraction MCP
- Cross-repo workspace memory
- Local omniretrieval across PDFs, notes, email, and browser history
- Autonomous code mutation
- Hosted SaaS dashboard
