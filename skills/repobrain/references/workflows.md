# RepoBrain Workflows

Use only the steps needed for the user's question. Every workflow assumes the agent has access to RepoBrain's verified tool surface through a compatible integration.

## 1. Repository discovery and indexing

1. Establish the intended repository. Call `list_workspace_projects` if the active project is ambiguous.
2. If necessary and authorized, call `track_workspace_project` with `activate: false`; activate only when the user wants the session switched.
3. Try the requested read-only analysis. If RepoBrain reports a missing index, explain that `index_repository` replaces/writes local `.repobrain/` state.
4. Call `index_repository` only with appropriate authorization.
5. Repeat the original query and report the selected repository explicitly.

Do not index secrets directories, generated output, dependencies, or unrelated repositories. Recommend updating `repobrain.toml` exclusions if the scan scope is unsafe.

## 2. Code search and execution tracing

1. Begin with `search_codebase` for the feature, symbol, route, job, or behavior.
2. Use `trace_flow` with a concrete entrypoint and destination when the user asks "how" or requests a call chain.
3. Compare snippet line spans with dependency edges. A textual hit without structural support is still useful but weaker.
4. Report the likely entrypoint, intermediate files/symbols, terminal operation, confidence, and warnings.
5. If evidence is concentrated in one file or role, inspect the cited source directly or issue a narrower follow-up query.

## 3. Dependency and impact analysis

1. Phrase `analyze_impact` around one proposed behavior change, not a broad migration.
2. Record top files, roles, dependency edges, and warnings.
3. Use `trace_flow` to validate important runtime paths and `search_codebase` to look for config, tests, callbacks, jobs, or consumers not represented in the first result.
4. Classify evidence as direct (returned snippet/path), structural hint (edge), or inferred risk.
5. Return a bounded blast-radius assessment; do not claim completeness when confidence or structural support is limited.

## 4. Locate edit targets

1. Call `build_change_context` for a compact planner payload or `suggest_edit_targets` when the full result is useful.
2. Check target rationales against snippets and roles.
3. Add relevant tests and config surfaces discovered with focused searches.
4. Present primary edit targets, files to inspect but probably not edit, validation targets, and unresolved questions.
5. Do not modify any file unless the user separately authorizes implementation.

## 5. Patch review

1. Select exactly one scope:
   - no arguments for working-tree changes;
   - `base` for committed branch changes relative to the merge base;
   - repo-relative `files` for an explicit slice.
2. Call `review_patch` and inspect changed files, unsupported files, adjacent runtime files, suggested tests, config surfaces, risk, and warnings.
3. Query high-risk changed symbols or adjacent files with `search_codebase`, `trace_flow`, or `analyze_impact`.
4. Inspect the actual diff and run relevant tests using the host agent's ordinary tools when authorized; RepoBrain does not execute those tests through this tool surface.
5. Report findings by severity with file evidence, consequence, and a concrete validation or fix.

An empty patch result is not a clean review; it means no supported changes were detected in the selected scope.

## 6. Pre-merge readiness

1. Define the branch or working-tree scope.
2. Run `review_patch` for that scope.
3. Run `review_codebase` with the focus relevant to the change; use `full` for a broad production gate.
4. Run targeted flow and impact checks for high-risk behavior.
5. Run `assess_ship_readiness`, preserving its blockers, checks, history, and missing-evidence signals.
6. Verify relevant unit, integration, lint, type, build, and security checks outside RepoBrain when available.
7. Conclude with one of:
   - evidence supports merge readiness, with named checks and residual risks;
   - not ready, with blockers;
   - insufficient evidence, with the exact missing checks.

Never state "safe to merge" solely from a high readiness score or the absence of tool findings.

## 7. Cross-repository investigation

1. List projects and verify the intended scope.
2. Use `search_workspace` with optional context only when comparison across tracked repositories is requested.
3. Report the globally ranked evidence and group conclusions by repository.
4. Use repository-specific tools after switching only with user authorization, because switching persists active state.
5. Do not copy private source excerpts from one repository into another or expose more content than the user's question requires.

## Recommended response structure

1. Conclusion
2. Evidence (`path:line`, symbol, or tool field)
3. Impact or risk
4. Confidence and RepoBrain warnings
5. Verification performed
6. Remaining uncertainty and next action
