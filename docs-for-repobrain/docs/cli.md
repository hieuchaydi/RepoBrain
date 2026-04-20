# CLI

## Commands

Friendly aliases are available for the highest-frequency flows:

- `repobrain start` = `repobrain first-look`
- `repobrain ask` = `repobrain query`
- `repobrain map` = `repobrain trace`
- `repobrain blast` = `repobrain impact`
- `repobrain plan` = `repobrain targets`
- `repobrain check` = `repobrain doctor`
- `repobrain smoke` = `repobrain provider-smoke`
- `repobrain ui` = `repobrain serve-web`

### `repobrain first-look`

Runs the shortest local demo path without requiring a hosted backend or API key.

It performs the day-one flow in one command:

- initializes `.repobrain/` and `repobrain.toml`
- indexes the repo with local providers
- runs a few starter questions
- stores the repo in workspace memory
- writes `.repobrain/report.html` unless `--no-report` is provided

Examples:

```bash
repobrain first-look --format text
repobrain start --repo /path/to/project --format text
repobrain first-look --repo /path/to/project --format text
repobrain first-look --repo /path/to/project --open-report --format text
repobrain demo --repo /path/to/project --no-report --format text
```

Use this command for screenshots, terminal recordings, and first-time GitHub visitors. It is intentionally local-only.

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

Alias: `repobrain ask "<question>"`

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

Alias: `repobrain map "<question>"`

Biases the harness toward route, call-chain, and dependency-flow evidence.

### `repobrain impact "<question>"`

Alias: `repobrain blast "<question>"`

Biases ranking toward affected files and dependency-central code.

### `repobrain targets "<question>"`

Alias: `repobrain plan "<question>"`

Biases ranking toward files that are safest to inspect or edit next.

### `repobrain patch-review`

Reviews the current patch instead of a natural-language question and returns:

- changed files
- adjacent runtime files
- suggested tests
- config surfaces
- risk score, warnings, and next steps

Examples:

```bash
repobrain patch-review --format text
repobrain patch-review --base main --format text
repobrain patch-review --files backend/app/api/auth.py backend/app/services/auth_service.py --format json
```

Rules:

- default mode inspects the current git working tree against `HEAD`
- `--base <ref>` reviews committed diff from `merge-base(<ref>, HEAD)...HEAD`
- `--files <path...>` accepts repo-relative paths and works even outside git
- `--base` and `--files` are mutually exclusive
- the repo must already be indexed with `repobrain index`

### `repobrain benchmark`

Runs the built-in benchmark queries against the current index and reports:

- Recall@3
- MRR
- citation accuracy
- edit-target hit rate

### `repobrain doctor`

Alias: `repobrain check`

Shows:

- repo root
- config path
- provider selection
- active provider models
- reranker model pool when Gemini or Groq failover is configured
- parser capability flags
- current index stats

Supports `--format text` for a compact health check.

### `repobrain provider-smoke`

Alias: `repobrain smoke`

Runs a direct smoke request through the currently configured embedding and reranker providers.

It is useful for:

- validating remote API keys and SDK wiring
- checking which remote reranker model is currently active
- seeing the ordered reranker model pool in one place
- confirming a real provider request works before using it in `index`, `query`, or `ship`

Supports `--format text` and `--format json`.

### `repobrain key gemini`

Saves a Gemini API key and writes the matching provider defaults into the active repo:

- `.env` gets `GEMINI_API_KEY`, Gemini embedding options, and `GEMINI_MODELS`
- `repobrain.toml` gets `embedding = "gemini"` and `reranker = "gemini"` unless disabled
- terminal output redacts the actual key

Examples:

```bash
repobrain key gemini --format text
repobrain key gemini --repo /path/to/project --format text
repobrain key gemini --no-embedding --model-pool gemini-2.5-flash,gemini-3-flash-preview --format text
```

Omit `--api-key` for the secure prompt. Use `--api-key` only in automation where process logs are controlled.

### `repobrain key groq`

Saves a Groq API key and writes the matching reranker defaults into the active repo:

- `.env` gets `GROQ_API_KEY`, `REPOBRAIN_GROQ_RERANK_MODEL`, and `GROQ_MODELS`
- `repobrain.toml` gets `embedding = "local"` and `reranker = "groq"` unless reranking is disabled
- terminal output redacts the actual key

Examples:

```bash
repobrain key groq --format text
repobrain key groq --repo /path/to/project --format text
repobrain key groq --model-pool llama-3.3-70b-versatile,openai/gpt-oss-20b --format text
```

Groq currently backs reranking/scoring only. RepoBrain keeps embeddings local so one Groq key is enough for a working setup.

### `repobrain chat`

Starts a local interactive loop. Chat uses text summaries by default. Plain questions run through `query`; slash commands select specific harness modes:

- `/key gemini`
- `/key groq`
- `/summary`
- `/remember <note>`
- `/remember clear`
- `/projects`
- `/add <path>`
- `/use <repo>`
- `/multi <question>`
- `/focus <topic>`
- `/focus`
- `/focus clear`
- `/query <question>`
- `/evidence <question>`
- `/map <question>`
- `/trace <question>`
- `/impact <question>`
- `/targets <question>`
- `/doctor`
- `/provider-smoke`
- `/index`
- `/review`
- `/baseline`
- `/ship`
- `/report`
- `/json`
- `/text`
- `/exit`

### `repobrain workspace`

Manages tracked repos and persisted repo memory outside the interactive chat loop.

Subcommands:

- `repobrain workspace list`
- `repobrain workspace add /path/to/project`
- `repobrain workspace use my-project`
- `repobrain workspace summary [project]`
- `repobrain workspace remember "auth callback is the critical flow"`
- `repobrain workspace clear-notes`

Use this group when you want to keep a lightweight multi-repo registry and carry a few durable notes, hot files, warnings, and follow-up threads between CLI chat, browser UI, and MCP usage.

### `repobrain report`

Generates a local HTML dashboard at `.repobrain/report.html` unless `--output` is provided.

```bash
repobrain report --format text
repobrain report --output ./repobrain-report.html
repobrain report --open
```

The report is local-only and summarizes index status, parser selection, provider mode, and suggested next commands.

It also shows active provider models, reranker pool state, and provider readiness posture from `repobrain doctor`.

Use `--open` when you want RepoBrain to generate the report and ask the operating system to open it in the default browser.

### `repobrain quickstart`

Prints the shortest install -> index -> query path for new users.

### `repobrain release-check`

Inspects release-readiness details for the RepoBrain source tree:

- version alignment across `pyproject.toml`, `src/repobrain/__init__.py`, and `webapp/package.json`
- built React assets under `webapp/dist`
- wheel/sdist contents after `python -m build`

```bash
repobrain release-check --format text
repobrain release-check --require-dist --format text
```

Use `--require-dist` in release automation so missing wheel/sdist artifacts fail the gate instead of showing as a local warning.

### `repobrain demo-clean`

Removes local test/build clutter so the repo is easier to present in a live demo without breaking the browser UI.

- removes root temp directories such as `pytest_work_*`, `pytest_tmp*`, `.tmp-build`, and `dist/`
- removes nested caches such as `__pycache__/` and generated `.repobrain/` state inside sample workspaces
- preserves `webapp/dist/` so `repobrain serve-web` still works after cleanup
- preserves the root `.repobrain/` state unless `--include-state` is passed

```bash
repobrain demo-clean --format text
repobrain demo-clean --dry-run --format text
repobrain demo-clean --keep-dist --include-state --format text
```

### `repobrain serve-mcp`

Runs a stdio JSON transport for grounded query, review, ship, and workspace flows.

Current tool surface:

- `index_repository`
- `search_codebase`
- `trace_flow`
- `analyze_impact`
- `suggest_edit_targets`
- `build_change_context`
- `review_patch`
- `review_codebase`
- `assess_ship_readiness`
- `list_workspace_projects`
- `track_workspace_project`
- `switch_workspace_project`
- `read_repo_memory`
- `remember_repo_note`
- `search_workspace`

For the JSON request/response shape, see [mcp.md](mcp.md).

### `repobrain serve-web`

Alias: `repobrain ui`

Starts a local browser UI for non-terminal import and query flows.

```bash
repobrain serve-web --open
repobrain ui --open
repobrain serve-web --host 127.0.0.1 --port 8765
```

The page lets you:

- paste a project path
- click `Import + Index`
- click `Project review` for the one-page audit view
- run `ask/query`, `map/trace`, `blast/impact`, `plan/targets`, or cross-repo mode
- switch between tracked repos without leaving the page
- store or clear short repo memory notes
- switch the interface between English and Vietnamese
- switch the interface between light and dark themes
- inspect structured `doctor` and `provider-smoke` posture cards without leaving the page
- save a baseline or run the ship gate from the action panel
- open the local report
- reuse the active repo without repeating the path

## Typical Workflow

```bash
repobrain init --repo /path/to/your-project
repobrain review --format text
repobrain index
repobrain ask "Where is auth callback handled?" --format text
repobrain plan "Which files should I edit to add GitHub login?"
repobrain report --format text
repobrain report --open
repobrain release-check --format text
repobrain demo-clean --format text
repobrain ui --open
repobrain chat
```
