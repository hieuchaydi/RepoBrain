# Run Guide

## Requirements

- Python `3.12+`
- a local repository you want RepoBrain to index

## Install

For the full bilingual installation guide, see [install.md](install.md).

### Linux or macOS

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev,tree-sitter,mcp]"
```

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,tree-sitter,mcp]"
```

## First Run

From the root of the repo you want to analyze:

```bash
repobrain init
repobrain index
repobrain doctor
repobrain provider-smoke
```

From anywhere else, point RepoBrain at the project once:

```powershell
repobrain init --repo "C:\path\to\your-project" --format text
repobrain index --format text
repobrain query "Where is payment retry logic implemented?" --format text
repobrain report --open
```

`init --repo` stores that project as the active repo, so later CLI commands can omit `--repo`.

What this creates:

- `repobrain.toml`
- `.repobrain/metadata.db`
- `.repobrain/vectors/chunks.jsonl`
- `.repobrain/cache/`

## Ask Questions

```bash
repobrain query "Where is payment retry logic implemented?"
repobrain trace "Trace login with Google from route to service"
repobrain impact "What breaks if I change auth callback handling?"
repobrain targets "Which files should I edit to add GitHub login?"
```

For a friendlier terminal view:

```bash
repobrain query "Where is payment retry logic implemented?" --format text
repobrain doctor --format text
repobrain provider-smoke --format text
```

## One-Click Local Chat

On Windows, use the repo-root launcher:

```powershell
.\chat.cmd
```

The launcher sets `PYTHONPATH=src`, prefers the project virtualenv, creates `.repobrain/` if needed, indexes the repo on the first run, and then opens `repobrain chat`.

You can also start the same loop directly:

```bash
repobrain chat
```

Useful chat commands:

- `/trace <question>`
- `/impact <question>`
- `/targets <question>`
- `/doctor`
- `/index`
- `/report`
- `/json`
- `/text`
- `/exit`

## Local HTML Report

Generate a local dashboard:

```bash
repobrain report --format text
repobrain report --open
```

Default output:

- `.repobrain/report.html`

The report is static HTML. It does not start a server and does not send code outside your machine.

On Windows, non-terminal users can double-click:

```powershell
.\report.cmd
```

The report launcher uses the same virtualenv detection as `chat.cmd`, creates local state when needed, generates `.repobrain/report.html`, and opens it in the default browser.

## Local Browser UI

Run:

```bash
repobrain serve-web --open
```

Default URL:

- `http://127.0.0.1:8765/`

Web import flow:

1. Paste the project path into the form.
2. Click `Import + Index`.
3. Wait for indexing to finish.
4. Ask grounded questions from the same page.
5. Open the report directly from the browser UI when needed.

This UI is local-only. It does not upload source code or require a hosted backend.

The current browser UI is a React TSX frontend with English/Vietnamese interface switching, a light/dark theme toggle, and structured diagnostics cards for `doctor` and `provider-smoke`. Frontend source lives in `webapp/`, and the Python server now serves the React build directly from `webapp/dist/`.

If `webapp/dist/` is missing, run:

```bash
cd webapp
npm run build
```

## Run The MCP-Style Transport

```bash
repobrain serve-mcp
```

This starts a stdio JSON transport for tools such as:

- `index_repository`
- `search_codebase`
- `trace_flow`
- `analyze_impact`
- `suggest_edit_targets`
- `build_change_context`

Security note:

- `serve-mcp` is designed for local stdio usage
- tool calls validate required arguments and reject oversized queries
- do not expose this transport as a network-facing service

## Development Loop

If you are working on RepoBrain itself:

```bash
python -m pip install -e ".[dev,tree-sitter,mcp]"
python -m compileall src
python -m pytest -q
repobrain release-check --format text
```

Pytest is configured to use a fresh `.pytest_tmp_run_*` folder for each run so old locked temp folders such as `pytest_tmp/` do not block normal local runs on Windows.

After building release artifacts with `python -m build`, run:

```bash
repobrain release-check --require-dist --format text
```

This checks version alignment, `webapp/dist` presence, and whether the wheel/sdist include the React frontend assets.

## Manual Smoke Flow

1. Create or pick a small sample repo.
2. Run `repobrain init --repo /path/to/sample`.
3. Run `repobrain index`.
4. Run one locate query, one trace query, and one targets query without repeating `--repo`.
5. Confirm the output has:
   - `top_files`
   - `snippets`
   - `edit_targets`
   - `confidence`
   - `warnings`

## Troubleshooting

### `Repository has not been indexed yet`

Run:

```bash
repobrain index
```

### Remote provider errors

If you switch away from `local` providers in `repobrain.toml`, install the optional provider SDKs and configure the required API keys:

```bash
python -m pip install -e ".[providers]"
```

Required keys by provider:

- `GEMINI_API_KEY` for `embedding = "gemini"` or `reranker = "gemini"`
- `OPENAI_API_KEY` for `embedding = "openai"`
- `VOYAGE_API_KEY` for `embedding = "voyage"`
- `COHERE_API_KEY` for `reranker = "cohere"`

Use `repobrain doctor` to inspect provider readiness and security posture before indexing or querying with remote providers.

Use `repobrain provider-smoke` when you want one direct request through the configured embedding and reranker providers before trusting them in normal workflows.

The current default path remains local-first. RepoBrain only sends code to a remote provider after you explicitly select that provider in `repobrain.toml`.

### Gemini setup

Create `.env` from the template:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then set:

```toml
[providers]
embedding = "gemini"
reranker = "gemini"
gemini_embedding_model = "gemini-embedding-001"
gemini_output_dimensionality = 768
gemini_task_type = "SEMANTIC_SIMILARITY"
gemini_rerank_model = "gemini-2.5-flash"
gemini_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"]
```

Run:

```bash
python -m pip install -e ".[providers]"
repobrain doctor --format text
repobrain index --format text
```

You can also swap the rerank model string directly, for example:

- `REPOBRAIN_GEMINI_RERANK_MODEL=gemini-2.5-flash`
- `REPOBRAIN_GEMINI_RERANK_MODEL=gemini-3-flash-preview`
- `REPOBRAIN_GEMINI_RERANK_MODEL=gemini-2.5-flash-preview-09-2025`

For automatic failover when one Gemini model runs out of quota, set an ordered pool in `.env`:

```env
GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3.1-flash-lite-preview,gemini-3-flash-preview
```

RepoBrain will retry with the next model only for Gemini quota or rate-limit exhaustion errors. Invalid model names, auth failures, or other request errors still fail fast so you can see the real problem.

### Parser depth looks shallow

RepoBrain always keeps the built-in heuristic parser available. For deeper symbol boundaries, install optional parser packages:

```bash
python -m pip install -e ".[tree-sitter]"
```

Then run:

```bash
repobrain doctor
repobrain index
```

`doctor` shows parser readiness by language, and `index` reports parser usage counts such as `heuristic` or `tree_sitter`.
