# MCP

RepoBrain ships a lightweight stdio JSON transport that mirrors an MCP-style tool surface. It is designed as a practical local adapter for agents and can be upgraded to the official MCP SDK later without changing engine semantics.

## Tools

### `index_repository`

Rebuilds the local index.

### `search_codebase`

Input:

```json
{"query": "Where is payment retry logic implemented?"}
```

Output includes grounded snippets, top files, dependency edges, edit targets, confidence, warnings, and next questions.

### `trace_flow`

Input:

```json
{"query": "Trace login with Google from route to service"}
```

Output biases toward flow and call-chain evidence.

### `analyze_impact`

Input:

```json
{"query": "What breaks if I change auth callback handling?"}
```

Output biases toward affected files and dependency edges.

### `suggest_edit_targets`

Input:

```json
{"query": "Which files should I edit to add GitHub login?"}
```

Output returns ranked files with rationales.

### `build_change_context`

Returns a compact payload meant for a planning agent that needs grounded edit targets without raw chunk noise.

### `list_workspace_projects`

Returns the tracked RepoBrain workspace plus the active repo.

### `track_workspace_project`

Input:

```json
{"repo": "/path/to/project", "activate": true}
```

Tracks another repo in the shared workspace and can switch the MCP session to it immediately.

### `switch_workspace_project`

Input:

```json
{"project": "my-project"}
```

Switches the active repo for the MCP session and the shared workspace registry.

### `read_repo_memory`

Returns the persisted summary memory for the active repo or a selected tracked repo.

### `remember_repo_note`

Input:

```json
{"note": "Auth callback is the critical integration thread."}
```

Stores a manual note inside the repo memory so later queries can reuse the thread.

### `search_workspace`

Input:

```json
{"query": "Where is auth callback handled across my repos?"}
```

Fans a grounded query out across every tracked repo and compares the strongest evidence per project.

The result now includes:

- `comparison.best_match`: the repo currently leading the cross-repo pass
- `comparison.active_rank`: where the active repo landed in the ranking
- `comparison.shared_hotspots`: repeated file hotspots across tracked repos
- `results[].citations`: short per-repo citation blocks with file path, line span, and preview text

## Stdio Protocol

Request examples:

```json
{"method": "tools/list"}
{"method": "tools/call", "name": "search_codebase", "arguments": {"query": "Where is payment retry logic implemented?"}}
```

Response examples:

```json
{"tools": [{"name": "search_codebase", "description": "Retrieve grounded snippets and ranked files for a natural-language code query."}]}
{"result": {"query": "Where is payment retry logic implemented?", "intent": "locate"}}
```
