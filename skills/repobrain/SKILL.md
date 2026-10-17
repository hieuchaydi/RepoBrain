---
name: repobrain
description: Uses RepoBrain's grounded repository tools for codebase exploration, symbol discovery, execution-flow tracing, dependency and change-impact analysis, edit targeting, patch review, and pre-merge readiness assessment. Use when a user asks where code lives, how components interact, what a change could affect, which files to edit, whether a patch is risky, or what evidence is still needed before merging.
---

# RepoBrain

Use the RepoBrain tool surface to ground repository analysis in its local index. Do not use this skill for unrelated writing, general web research, or tasks that do not involve a source repository.

This Skill was authored for public RepoBrain 0.5.0 with Python 3.12+. Git is required for working-tree or base-ref patch review. The current stdio-json transport requires a compatible integration or bridge and is not standard MCP JSON-RPC.

## Start safely

1. Identify the intended repository. When multiple projects may be tracked, call `list_workspace_projects`; do not silently switch projects.
2. Prefer non-mutating analysis. `search_codebase`, `trace_flow`, `analyze_impact`, `suggest_edit_targets`, `build_change_context`, `review_patch`, `review_codebase`, `assess_ship_readiness`, `read_repo_memory`, and `search_workspace` are analysis operations, although some may read Git or local index state.
3. Treat `index_repository`, `track_workspace_project`, `switch_workspace_project`, and `remember_repo_note` as state-changing operations. Obtain authorization when the user's request does not already imply creating or changing RepoBrain state.
4. If a query reports that the repository is not indexed, explain that indexing writes `.repobrain/` under the target repository and ask to run `index_repository` when authorization is required.
5. Never edit application source through this skill. RepoBrain returns evidence and recommendations; use separate editing tools only when the user authorizes a change.

## Choose the smallest useful workflow

- Locate code or symbols: call `search_codebase` with a precise natural-language `query`.
- Explain runtime flow: call `trace_flow`; inspect `snippets`, `call_chain`, `dependency_edges`, confidence, and warnings.
- Estimate blast radius: call `analyze_impact`; corroborate important paths with `search_codebase` or `trace_flow`.
- Plan a change: call `suggest_edit_targets` or the more compact `build_change_context`. Verify low-confidence targets before proposing edits.
- Review a patch: call `review_patch` with no arguments for the working tree, with `base`, or with repo-relative `files`. Never pass `base` and `files` together.
- Review repository risk: call `review_codebase` with one of `full`, `security`, `production`, or `quality`.
- Assess merge readiness: use `review_patch`, relevant targeted queries, and `assess_ship_readiness`. Report blockers and missing evidence; never equate a tool status with a guarantee of safety.
- Compare tracked repositories: call `search_workspace` only when the user asks for cross-repository analysis.

For exact arguments and response fields, read [references/mcp-tools.md](references/mcp-tools.md). For multi-step procedures, read [references/workflows.md](references/workflows.md). Load [references/troubleshooting.md](references/troubleshooting.md) only when setup, indexing, transport, provider, Git, or runtime errors occur.

## Interpret evidence

- Separate confirmed tool evidence from inference. Cite repo-relative paths and line spans from returned snippets when available.
- Preserve RepoBrain's confidence label, confidence summary, and warnings. Low or concentrated evidence requires manual verification.
- Treat dependency edges and call chains as static-analysis hints, not proof of every runtime path.
- Treat edit targets as inspection priorities, not permission to modify files.
- Treat patch risk and ship readiness as decision support. Before saying a change appears merge-ready, require relevant tests or checks, a reviewed patch scope, no unresolved blockers, and adequate repository evidence.
- If tools disagree, show the contradiction and recommend the narrowest follow-up query or direct source inspection.
- Never fabricate a tool result, file path, symbol, test result, or merge verdict.

## Protect code and credentials

- RepoBrain is local-first only while its configured embedding and reranking providers are `local`.
- Before using a remote provider, disclose that indexed code or snippets may leave the machine and verify explicit user configuration.
- Never print `.env` contents, API keys, credentials, private source excerpts beyond what the user needs, or full index/cache contents.
- Keep RepoBrain's stdio transport local. Do not expose it as a network service.

## Report results

Lead with the answer, then list supporting files or flows, confidence and warnings, likely impact, and the next verification step. For review tasks, group findings by severity and include evidence, consequence, and recommended validation. State clearly when the MCP connection, index, Git history, provider, or test environment prevents a conclusion.
