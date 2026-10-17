# Troubleshooting RepoBrain

## Server does not start

- Confirm Python is 3.12 or newer.
- For an installed package, run `repobrain --help` and then `repobrain serve-mcp --repo <absolute-path>`.
- For a source checkout, activate its environment or set `PYTHONPATH` to `<checkout>/src`, then run `python -m repobrain serve-mcp --repo <absolute-path>`.
- If stdout does not begin with a JSON banner containing `"transport":"stdio-json"`, verify that the expected RepoBrain installation is being launched.
- Keep diagnostic logging off protocol stdout; a bridge must preserve one JSON object per stdout line.

## Standard MCP client fails during initialization

This RepoBrain revision does not implement standard MCP JSON-RPC initialization, capability negotiation, JSON-RPC IDs, or advertised input schemas. Its accepted messages are `tools/list` and `tools/call` in a custom newline-delimited format. A standard Claude Code, Cursor, or Codex MCP configuration therefore needs a compatible bridge or a future RepoBrain server revision. Installing `repobrain[mcp]` alone does not change the server implementation.

Do not diagnose this as a repository-index problem if the client fails before `tools/list` can be exchanged.

## Wrong repository is analyzed

Pass `--repo <absolute-path>` in the server launch. Without it, RepoBrain can use a saved active repository rather than the current directory. `REPOBRAIN_ACTIVE_REPO_FILE` controls the saved-path file; the default is `~/.repobrain/active_repo.txt`.

Within a running tool session, call `list_workspace_projects` to inspect state. `switch_workspace_project` changes persisted active state, so use it only when authorized.

## Repository has not been indexed

Run, or ask authorization to run:

```bash
repobrain index --repo "/absolute/path/to/project" --format text
```

Indexing writes or replaces `.repobrain/metadata.db`, vectors, and cache data. Confirm `.repobrain/` is ignored by version control.

## Index misses files

- Inspect `[indexing] include`, `exclude`, and `max_file_size_bytes` in the target repository's `repobrain.toml`.
- RepoBrain also honors configured ignore/exclusion behavior and skips oversized/generated/vendor paths.
- Re-index after changing scope.
- Install the optional `tree-sitter` extra for deeper supported-language parsing, then use `repobrain doctor` and re-index.

## Query has weak or exploratory confidence

- Narrow the query to a known route, symbol, provider, callback, job, or file family.
- Use a second tool mode to corroborate evidence, such as `trace_flow` after `search_codebase`.
- Inspect snippets and cited source directly.
- Do not suppress RepoBrain warnings or translate weak evidence into a definitive conclusion.

## `review_patch` fails

- Working-tree and `base` modes require Git and a Git repository.
- Verify `base` exists and has a merge base with `HEAD`.
- `files` must be a non-empty array of repo-relative paths. Absolute paths and paths escaping the repository are rejected.
- Do not pass `base` and `files` together.
- The repository must be indexed first.

## No changed files are reported

Confirm the chosen patch mode and Git state. An empty result means no supported changed files were detected; it does not prove the patch is risk-free. Generated, binary, deleted, or unsupported files may need separate inspection.

## Remote provider errors

Local embedding and reranking are the default. If a remote provider is explicitly enabled:

- install `repobrain[providers]`;
- set the required credential in the target repository's `.env` or process environment;
- run `repobrain doctor --repo <path>` and `repobrain provider-smoke --repo <path>`;
- never print the credential while debugging.

Relevant variables include `GEMINI_API_KEY`, `OPENAI_API_KEY`, `VOYAGE_API_KEY`, `COHERE_API_KEY`, and `GROQ_API_KEY`. Remote providers may receive source-derived text.

## Workspace state errors

Workspace operations persist project registrations, active selection, summaries, and notes. Verify paths still exist and that the user can read/write the workspace state location. Avoid repairing state destructively; collect the error and ask before removing or replacing any state.

## Tool returns `error`

The stdio loop serializes validation and handler failures as `{"error":"..."}` and continues. Fix the arguments or underlying repository condition, then retry once. Repeated errors should be reported with the exact message and the attempted repository/tool scope.
