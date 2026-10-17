# Usage Examples

These examples describe expected agent behavior, not fabricated RepoBrain outputs.

## Locate a feature

User prompt:

> Find where password reset tokens are generated and validated.

Expected behavior:

1. Confirm the target repository if ambiguous.
2. Call `search_codebase` with the requested behavior.
3. If results identify likely entrypoints but not the full path, call `trace_flow` with the discovered symbol names.
4. Answer with cited paths and line spans from returned snippets, confidence, warnings, and any remaining gap.

## Trace execution

User prompt:

> Trace checkout from the HTTP route through payment capture and receipt creation.

Expected behavior:

1. Call `trace_flow` with the entrypoint and intended terminal operations.
2. Correlate `call_chain`, `dependency_edges`, snippets, and file roles.
3. Mark edges as likely static-analysis paths rather than guaranteed runtime behavior.
4. Suggest direct inspection when role diversity or confidence is weak.

## Assess change impact

User prompt:

> What could break if I change the OAuth callback payload format?

Expected behavior:

1. Call `analyze_impact` for callback payload consumers.
2. Use `search_codebase` for serializers, tests, configuration, and downstream integrations if the first result does not cover them.
3. Separate directly evidenced files from inferred risks.
4. Return affected surfaces, likely regression tests, confidence, and unresolved questions.

## Plan edits without changing code

User prompt:

> Tell me which files I should change to add exponential retry backoff. Do not edit anything.

Expected behavior:

1. Call `build_change_context` or `suggest_edit_targets`.
2. Verify target rationales against supporting snippets.
3. Report primary edit targets, adjacent tests/config, and evidence quality.
4. Make no source edits.

## Review the current patch

User prompt:

> Review my uncommitted changes for regressions and missing tests.

Expected behavior:

1. Call `review_patch` with `{}`.
2. Query high-risk changed behavior with `trace_flow` or `analyze_impact`.
3. Inspect the actual diff and run relevant tests through ordinary host tools if the user has authorized review commands.
4. Report concrete findings first. Treat “no supported changed files” as insufficient scope, not approval.

## Review a branch against main

User prompt:

> Review this branch against main and tell me whether it is ready to merge.

Expected behavior:

1. Call `review_patch` with `{"base":"main"}`.
2. Call `review_codebase` with a relevant focus and `assess_ship_readiness`.
3. Run or inspect relevant project checks outside RepoBrain where available.
4. Conclude “supported,” “not ready,” or “insufficient evidence,” naming blockers and residual risk. Never offer an unconditional safety guarantee.

## Handle a missing index

User prompt:

> Where is billing proration implemented?

Expected behavior when the query reports no index:

1. Explain that RepoBrain needs a local index and that indexing writes `.repobrain/` state.
2. Obtain authorization if the request did not already imply indexing.
3. Call `index_repository` and retry the original query.
4. Report any indexing exclusions or parser limitations relevant to the result.

## Handle an unavailable MCP connection

User prompt:

> Use RepoBrain to assess this patch.

Expected behavior when tools are unavailable:

1. State that RepoBrain evidence could not be collected.
2. Check whether the current integration supports RepoBrain's newline-delimited stdio JSON protocol or has a compatible bridge.
3. Provide the verified startup command and protocol probe from `mcp-config.example.json`.
4. Do not imitate or invent tool output. Offer a clearly labeled non-RepoBrain review only if the user wants a fallback.
