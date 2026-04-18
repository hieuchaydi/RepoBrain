# Contracts

## Public Surface

RepoBrain exposes three public contract layers:

1. CLI commands
2. MCP-style tools over stdio JSON
3. JSON result payloads returned by the engine
4. diagnostic and security posture output from `repobrain doctor`

## CLI Commands

### `repobrain init`

Input:

- `--repo` optional repo path
- `--force` optional overwrite behavior for `repobrain.toml`

Output:

```json
{
  "repo_root": "/abs/path/to/repo",
  "config_path": "/abs/path/to/repo/repobrain.toml",
  "state_dir": "/abs/path/to/repo/.repobrain",
  "active_repo": "/abs/path/to/repo"
}
```

Behavior:

- `init --repo /path/to/repo` stores that repo as the active repo for later CLI commands.
- Later CLI commands use the active repo when `--repo` is omitted.
- If no active repo exists, CLI commands fall back to the current working directory.

### `repobrain index`

Output:

```json
{
  "files": 7,
  "chunks": 16,
  "symbols": 16,
  "edges": 7,
  "parsers": {
    "heuristic": 7
  },
  "repo_root": "/abs/path/to/repo"
}
```

### `repobrain serve-web`

Input:

- `--repo` optional initial repo path
- `--host` optional bind host, default `127.0.0.1`
- `--port` optional bind port, default `8765`
- `--open` optional browser open flag

Behavior:

- starts a local-only browser UI
- serves a static React frontend shell at `/`
- serves JSON API routes under `/api/*`
- import action runs init + index in one step
- query action dispatches to `query`, `trace`, `impact`, or `targets`
- `GET /api/doctor` and `POST /api/provider-smoke` return both the text `result` and a structured `data` payload for the React diagnostics panels
- report route serves the generated local report HTML

### `repobrain query|trace|impact|targets`

All query-like commands return the same top-level schema.

### `repobrain doctor`

Returns repo diagnostics plus provider and security posture data.

Example shape:

```json
{
  "indexed": true,
  "providers": {
    "embedding": "local-hash",
    "reranker": "gemini",
    "embedding_model": "n/a",
    "reranker_model": "gemini-2.5-flash",
    "reranker_models": [
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemini-3-flash-preview"
    ],
    "reranker_last_failover_error": null
  },
  "provider_status": {
    "embedding": {
      "kind": "embedding",
      "configured": "local",
      "active": "local",
      "local_only": true,
      "ready": true,
      "requires_network": false,
      "missing": [],
      "warnings": []
    },
    "reranker": {
      "kind": "reranker",
      "configured": "gemini",
      "active": "gemini",
      "local_only": false,
      "ready": true,
      "requires_network": true,
      "missing": [],
      "warnings": []
    }
  },
  "security": {
    "local_storage_only": true,
    "remote_providers_enabled": false,
    "network_required": false,
    "mcp_transport": "stdio-json"
  },
  "capabilities": {
    "tree_sitter_available": false,
    "tree_sitter_ready": false,
    "parser_preference": "tree_sitter",
    "heuristic_fallback": true,
    "language_parsers": {
      "python": {
        "selected": "heuristic",
        "tree_sitter_enabled": true,
        "heuristic_fallback": true,
        "optional_adapters": [
          {
            "name": "tree_sitter",
            "ready": false,
            "source": "",
            "error": "tree-sitter grammar is not installed"
          }
        ]
      }
    }
  }
}
```

Notes:

- `providers.reranker_model` is the currently active reranker model inside the current process.
- `providers.reranker_models` is the ordered fallback pool when Gemini model failover is configured.
- `providers.reranker_last_failover_error` is process-local diagnostic state and may be `null` when no failover has happened yet.

### `repobrain provider-smoke`

Returns a smoke result for the currently configured embedding and reranker providers.

Example shape:

```json
{
  "repo_root": "/abs/path/to/repo",
  "providers": {
    "embedding": "local-hash",
    "reranker": "gemini",
    "embedding_model": "n/a",
    "reranker_model": "gemini-2.5-flash",
    "reranker_models": [
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemini-3-flash-preview"
    ],
    "reranker_last_failover_error": null
  },
  "provider_status": {},
  "embedding_smoke": {
    "status": "pass",
    "vector_count": 1,
    "dimensions": 256
  },
  "reranker_smoke": {
    "status": "pass",
    "score": 0.73,
    "active_model_before": "gemini-2.5-flash",
    "active_model_after": "gemini-2.5-flash",
    "pool": [
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemini-3-flash-preview"
    ],
    "last_failover_error": null
  }
}
```

Notes:

- `embedding_smoke.status` and `reranker_smoke.status` are independent.
- A provider-smoke call may pass for one provider and fail for the other.
- For Gemini pools, `active_model_after` shows where the process ended after any failover attempt.

## Query Result Schema

```json
{
  "query": "Which files should I edit to add GitHub login?",
  "intent": "change",
  "top_files": [
    {
      "file_path": "frontend/src/services/oauth.ts",
      "language": "typescript",
      "role": "service",
      "score": 4.24,
      "reasons": ["bm25", "path_overlap", "symbol:handleGitHubCallback"]
    }
  ],
  "snippets": [
    {
      "chunk_id": 12,
      "file_path": "frontend/src/services/oauth.ts",
      "language": "typescript",
      "role": "service",
      "symbol_name": "handleGitHubCallback",
      "start_line": 6,
      "end_line": 9,
      "content": "export async function handleGitHubCallback(...)",
      "score": 2.13,
      "reasons": ["bm25", "reranked", "path_overlap"]
    }
  ],
  "call_chain": [
    "frontend/src/routes/login.ts::githubCallback --imports_call--> handleGitHubCallback"
  ],
  "dependency_edges": [
    {
      "source_file": "frontend/src/routes/login.ts",
      "source_symbol": "githubCallback",
      "target": "handleGitHubCallback",
      "edge_type": "imports_call",
      "target_file": null
    }
  ],
  "edit_targets": [
    {
      "file_path": "frontend/src/services/oauth.ts",
      "score": 4.49,
      "rationale": "Contains business logic connected to the query."
    }
  ],
  "confidence": 0.82,
  "warnings": [],
  "next_questions": [],
  "plan": {
    "intent": "change",
    "steps": [
      "planner",
      "retriever",
      "file_selector",
      "evidence_collector",
      "edit_target_scorer",
      "self_check"
    ],
    "rewritten_queries": [
      "Which files should I edit to add GitHub login?"
    ]
  }
}
```

## MCP Tool Contracts

### `index_repository`

Arguments:

```json
{}
```

Returns index stats.

### `search_codebase`

Arguments:

```json
{"query": "Where is payment retry logic implemented?"}
```

Returns full query result schema.

### `trace_flow`

Arguments:

```json
{"query": "Trace login with Google from route to service"}
```

Returns full query result schema with trace-biased intent.

### `analyze_impact`

Arguments:

```json
{"query": "What breaks if I change auth callback handling?"}
```

Returns full query result schema with impact-biased intent.

### `suggest_edit_targets`

Arguments:

```json
{"query": "Which files should I edit to add GitHub login?"}
```

Returns full query result schema with change-biased intent.

### `build_change_context`

Returns a compact subset intended for planning agents:

```json
{
  "query": "Which files should I edit to add GitHub login?",
  "intent": "change",
  "top_files": [],
  "edit_targets": [],
  "warnings": [],
  "confidence": 0.82,
  "plan_steps": ["planner", "retriever", "file_selector"]
}
```

### `chat`

`repobrain chat` is a CLI-only interactive mode. It is not part of the MCP tool surface. It dispatches plain text to `query` and slash commands to `trace`, `impact`, `targets`, `doctor`, or `index`.

## Storage Contract

`.repobrain/metadata.db` tables:

- `files`
- `symbols`
- `chunks`
- `chunk_fts`
- `edges`

`.repobrain/vectors/chunks.jsonl` stores one JSON object per chunk:

```json
{"chunk_id": 12, "vector": [0.0, 0.125, 0.0]}
```

## Backward Compatibility Rule

For v1, additive fields are allowed. Renaming or removing top-level output keys should be treated as a breaking change.

## MCP Validation Rule

- unknown tools must be rejected
- non-object `arguments` must be rejected
- tools that require `query` must reject missing or empty values
- oversized `query` values must be rejected before reaching engine logic
