# Verified RepoBrain Tool Reference

This reference reflects `src/repobrain/mcp_server.py` at RepoBrain `0.5.0`, commit `2b43d9d`. The server returns a wrapper object containing either `result` or `error`. Its `tools/list` response exposes names and descriptions only; argument rules are enforced internally rather than advertised as JSON Schema.

Only the 14 tools registered in that public source file are documented here. Private v1.3 early-access tool names mentioned in the project README are intentionally excluded because they are absent from the audited public registration table.

All `query` values must be non-empty strings no longer than 2,000 characters.

## Query result shape

`search_codebase`, `trace_flow`, `analyze_impact`, and `suggest_edit_targets` return the same top-level structure:

- `query`, `intent`
- `top_files[]`: `file_path`, `language`, `role`, `score`, `reasons`
- `snippets[]`: chunk and line metadata, content, score, and reasons
- `call_chain[]`
- `dependency_edges[]`
- `edit_targets[]`: path, score, and rationale
- `confidence`, `confidence_label`, `confidence_summary`
- `warnings[]`, `next_questions[]`
- `plan`: intent, steps, and rewritten queries

## `index_repository`

Purpose: Scan the selected repository, parse supported files, replace the metadata store, and persist vectors.

- Required arguments: none
- Optional arguments: none; supplied arguments are discarded
- Expected output: index statistics including file/chunk/symbol/edge counts, parser counts, and `repo_root`
- Side effects: writes the configured `.repobrain/` state; replaces the existing index
- Common errors: unreadable repository, filesystem errors, provider failures

```json
{"method":"tools/call","name":"index_repository","arguments":{}}
```

## `search_codebase`

Purpose: Retrieve ranked files and grounded snippets for a natural-language repository question.

- Required: `query` (string)
- Optional: none
- Output: query result shape with automatically classified intent
- Common errors: missing/empty/oversized query; repository not indexed

```json
{"method":"tools/call","name":"search_codebase","arguments":{"query":"Where is payment retry logic implemented?"}}
```

## `trace_flow`

Purpose: Bias retrieval toward likely execution flow, calls, imports, and dependency edges.

- Required: `query` (string)
- Optional: none
- Output: query result shape with `intent: "trace"`
- Common errors: missing index; weak or single-role evidence; missing/oversized query

```json
{"method":"tools/call","name":"trace_flow","arguments":{"query":"Trace OAuth login from route to service"}}
```

## `analyze_impact`

Purpose: Estimate files and structural edges affected by a proposed change.

- Required: `query` (string)
- Optional: none
- Output: query result shape with `intent: "impact"`
- Common errors: missing index; insufficient structural edges; missing/oversized query

```json
{"method":"tools/call","name":"analyze_impact","arguments":{"query":"What breaks if callback validation changes?"}}
```

## `suggest_edit_targets`

Purpose: Rank files to inspect or edit for a requested change.

- Required: `query` (string)
- Optional: none
- Output: query result shape with `intent: "change"`; `edit_targets` is the primary field
- Common errors: missing index; limited structural support; missing/oversized query

```json
{"method":"tools/call","name":"suggest_edit_targets","arguments":{"query":"Which files should change to add GitHub login?"}}
```

## `build_change_context`

Purpose: Produce a compact planning payload derived from change-target analysis.

- Required: `query` (string)
- Optional: none
- Output: `query`, `intent`, compact `top_files`, enriched `edit_targets`, `supporting_snippets`, warnings, risk notes, confidence fields, evidence summary, next questions, and plan steps
- Common errors: missing index; missing/oversized query

```json
{"method":"tools/call","name":"build_change_context","arguments":{"query":"Plan the safest place to add retry backoff"}}
```

## `review_patch`

Purpose: Review changed files and find adjacent runtime files, tests, configuration surfaces, and risk warnings.

- Required: none
- Optional: `base` (string) or `files` (non-empty array of repo-relative paths)
- Constraint: `base` and `files` are mutually exclusive
- Output: `kind`, `repo_root`, `mode`, `base_ref`, `changed_files`, `adjacent_files`, `suggested_tests`, `config_surfaces`, `risk_score`, `risk_label`, `summary`, `warnings`, and `next_steps`
- Common errors: repository not indexed; invalid base ref; Git missing or target not a Git repository; absolute or escaping file paths; empty `files`

Current working tree:

```json
{"method":"tools/call","name":"review_patch","arguments":{}}
```

Committed changes relative to a merge base:

```json
{"method":"tools/call","name":"review_patch","arguments":{"base":"main"}}
```

Explicit paths:

```json
{"method":"tools/call","name":"review_patch","arguments":{"files":["src/auth/service.py","tests/test_auth.py"]}}
```

## `review_codebase`

Purpose: Scan repository production, security, and code-quality gaps.

- Required: none
- Optional: `focus`, one of `full`, `security`, `production`, `quality`; default `full`
- Output: repository root, focus, readiness, score, summary, findings, next steps, statistics, category/severity counts, and optional baseline delta
- Common errors: invalid focus; scan or filesystem failure

```json
{"method":"tools/call","name":"review_codebase","arguments":{"focus":"security"}}
```

## `assess_ship_readiness`

Purpose: Run the ship gate across review findings, index health, parser posture, providers, benchmarks, and optional baseline history.

- Required: none
- Optional: `baseline_label` (string), default `baseline`
- Output: repository root, status, score, summary, checks, blockers, highlights, next steps, doctor payload, review payload, optional benchmark, and history
- Common errors: runtime review/provider/index failures; absent baseline is represented in the returned evidence rather than proving safety

```json
{"method":"tools/call","name":"assess_ship_readiness","arguments":{"baseline_label":"baseline"}}
```

## `list_workspace_projects`

Purpose: List tracked projects and the active repository.

- Required arguments: none
- Optional arguments: none; supplied arguments are discarded
- Output: workspace registry payload with active/current repository and tracked projects
- Common errors: corrupt or unreadable workspace state

```json
{"method":"tools/call","name":"list_workspace_projects","arguments":{}}
```

## `track_workspace_project`

Purpose: Add a repository to shared workspace state and optionally activate it.

- Required: `repo` (non-empty path string)
- Optional: `activate` (boolean), default `true`
- Output: updated workspace payload
- Side effects: persists workspace state; when activated, changes the MCP session engine and saved active repository
- Common errors: missing/invalid path; state-write failure

```json
{"method":"tools/call","name":"track_workspace_project","arguments":{"repo":"/absolute/path/to/project","activate":false}}
```

## `switch_workspace_project`

Purpose: Switch the MCP session and shared active repository to a tracked project.

- Required: `project` (non-empty project name or reference accepted by RepoBrain workspace logic)
- Optional: none
- Output: updated workspace payload
- Side effects: changes session target and saved active repository
- Common errors: unknown project; selected project does not resolve to a repository

```json
{"method":"tools/call","name":"switch_workspace_project","arguments":{"project":"payments-service"}}
```

## `read_repo_memory`

Purpose: Read persisted summary memory for the active or selected tracked repository.

- Required: none
- Optional: `project` (string); omitted or blank selects the active repository
- Output: workspace summary payload
- Common errors: unknown project; unreadable workspace state

```json
{"method":"tools/call","name":"read_repo_memory","arguments":{}}
```

## `remember_repo_note`

Purpose: Persist a manual note in repository memory.

- Required: `note` (non-empty string)
- Optional: `project` (string); omitted selects the active repository
- Output: updated repository-memory payload
- Side effects: writes workspace memory
- Common errors: missing note; unknown project; state-write failure

```json
{"method":"tools/call","name":"remember_repo_note","arguments":{"note":"OAuth callback is a critical integration surface."}}
```

## `search_workspace`

Purpose: Run a grounded query across all tracked repositories and rank evidence across projects.

- Required: `query` (string)
- Optional: `context` (string), default empty
- Output: per-project results plus comparison data such as best match, active rank, global evidence, and shared hotspots
- Common errors: missing/oversized query; no usable tracked projects; one or more repositories unavailable or unindexed

```json
{"method":"tools/call","name":"search_workspace","arguments":{"query":"Where are OAuth callbacks handled?","context":"Focus on provider callbacks"}}
```

## Protocol errors

- Unknown name: `Unknown tool: <name>`
- Non-object arguments: `` `arguments` must be a JSON object. ``
- Unsupported request method: `Unsupported method: <method>`
- Handler and validation failures are serialized as `{"error":"..."}`; the process normally continues reading subsequent lines.
