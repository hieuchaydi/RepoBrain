# CLI

## Commands

### `repobrain init`

Creates:

- `repobrain.toml`
- `.repobrain/`
- `.repobrain/vectors/`
- `.repobrain/cache/`

When `--repo` is provided, RepoBrain remembers that path as the active repo for later commands:

```powershell
repobrain init --repo "C:\path\to\your-project" --format text
repobrain index --format text
repobrain query "Where is payment retry logic implemented?" --format text
```

Explicit `--repo` still works on every command, but after initialization it is no longer required for the normal CLI flow.

### `repobrain index`

Scans the configured repo root, extracts symbols and chunks, and persists metadata plus vectors.

The output includes parser usage counts so teams can see whether files were parsed by `tree_sitter` or the built-in `heuristic` fallback.

### `repobrain review`

Runs a concise repo scan and returns the highest-signal issues first.

It is designed for the MVP flow where users want one page of:

- security risks
- production risks
- missing code-quality guardrails
- what to fix next

Examples:

```bash
repobrain review --format text
repobrain review --focus security --format text
repobrain review --focus quality --format json
```

The review command does not depend on a previously built index. It scans the repo directly and complements `query` rather than replacing it.

### `repobrain query "<question>"`

Runs general retrieval and returns:

- top files
- snippets
- dependency edges
- edit targets
- warnings
- confidence

Add `--format text` for a readable terminal summary:

```bash
repobrain query "Where is auth callback handled?" --format text
```

### `repobrain trace "<question>"`

Biases the harness toward route, call-chain, and dependency-flow evidence.

### `repobrain impact "<question>"`

Biases ranking toward affected files and dependency-central code.

### `repobrain targets "<question>"`

Biases ranking toward files that are safest to inspect or edit next.

### `repobrain benchmark`

Runs the built-in benchmark queries against the current index and reports:

- Recall@3
- MRR
- citation accuracy
- edit-target hit rate

### `repobrain doctor`

Shows:

- repo root
- config path
- provider selection
- active provider models
- Gemini fallback pool when configured
- parser capability flags
- current index stats

Supports `--format text` for a compact health check.

### `repobrain provider-smoke`

Runs a direct smoke request through the currently configured embedding and reranker providers.

It is useful for:

- validating remote API keys and SDK wiring
- checking which Gemini reranker model is currently active
- seeing the ordered Gemini fallback pool in one place
- confirming a real provider request works before using it in `index`, `query`, or `ship`

Supports `--format text` and `--format json`.

### `repobrain chat`

Starts a local interactive loop. Chat uses text summaries by default. Plain questions run through `query`; slash commands select specific harness modes:

- `/trace <question>`
- `/impact <question>`
- `/targets <question>`
- `/doctor`
- `/provider-smoke`
- `/index`
- `/review`
- `/report`
- `/json`
- `/text`
- `/exit`

### `repobrain report`

Generates a local HTML dashboard at `.repobrain/report.html` unless `--output` is provided.

```bash
repobrain report --format text
repobrain report --output ./repobrain-report.html
repobrain report --open
```

The report is local-only and summarizes index status, parser selection, provider mode, and suggested next commands.

It also shows active provider models, Gemini fallback pool state, and provider readiness posture from `repobrain doctor`.

Use `--open` when you want RepoBrain to generate the report and ask the operating system to open it in the default browser.

### `repobrain quickstart`

Prints the shortest install -> index -> query path for new users.

### `repobrain serve-mcp`

Runs a stdio JSON transport with six tools:

- `index_repository`
- `search_codebase`
- `trace_flow`
- `analyze_impact`
- `suggest_edit_targets`
- `build_change_context`

### `repobrain serve-web`

Starts a local browser UI for non-terminal import and query flows.

```bash
repobrain serve-web --open
repobrain serve-web --host 127.0.0.1 --port 8765
```

The page lets you:

- paste a project path
- click `Import + Index`
- click `Scan Project Review` for the one-page audit view
- run `query`, `trace`, `impact`, or `targets`
- switch the interface between English and Vietnamese
- switch the interface between light and dark themes
- inspect structured `doctor` and `provider-smoke` posture cards without leaving the page
- open the local report
- reuse the active repo without repeating the path

## Typical Workflow

```bash
repobrain init --repo /path/to/your-project
repobrain review --format text
repobrain index
repobrain query "Where is auth callback handled?" --format text
repobrain targets "Which files should I edit to add GitHub login?"
repobrain report --format text
repobrain report --open
repobrain serve-web --open
repobrain chat
```
