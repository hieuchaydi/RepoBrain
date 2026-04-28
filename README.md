# RepoBrain

Pre-merge safety layer for AI coding agents. Not a visualizer — a gatekeeper.

[![CI](https://github.com/hieuchaydi/RepoBrain/actions/workflows/ci.yml/badge.svg)](https://github.com/hieuchaydi/RepoBrain/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776ab)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-0e7c72)](LICENSE)

RepoBrain is a Python tool that indexes source repositories and serves query results through a consistent local interface. It supports file discovery, trace-oriented lookup, impact-style queries, and ranked edit targets for planning code changes.

Interfaces:

- `repobrain` CLI for indexing, query, trace, review, benchmark, and ship checks
- `repobrain serve-mcp` for stdio MCP integration with editor agents
- `repobrain serve-web` for a local browser UI backed by the same engine

State is written to `.repobrain/` (metadata, vectors, workspace files). Retrieval combines lexical search and local vector search, then reranks candidates and returns scored files with optional snippets. Local mode is the default runtime. Remote providers are optional and only used when configured explicitly.

## RepoBrain vs Other Tools

| Feature | RepoBrain | GitNexus | Greptile |
| --- | --- | --- | --- |
| Primary mode | Pre-merge safety workflow during active code changes | Repository graph exploration and architecture browsing | Hosted code review and PR analysis workflows |
| MCP server for live agent integration | Yes (`repobrain serve-mcp`) | Yes | Yes (hosted MCP endpoint) |
| Blast radius score before edits | Yes (`repobrain blast`) | No built-in pre-edit blast score | PR-focused review signals, not local pre-edit blast scoring |
| Pre-merge ship check gate | Yes (`repobrain ship`) | No equivalent built-in gate | Review feedback pipeline, not local ship gating |
| Patch-review for current diff | Yes (`repobrain patch-review`) | No equivalent built-in local patch gate | Review comments on PRs, not local patch gate workflow |
| Workspace memory for active projects | Yes (`repobrain workspace ...`) | No equivalent built-in workflow memory layer | Organization and PR context, not local workspace memory routing |
| Agent safety gate | Coming soon | Not positioned as an agent safety gate | Not positioned as an agent safety gate |
| Local-first default (no code sent to cloud by default) | Yes | Local mode available | No (API-first hosted workflow) |

## Installation

Full installation instructions are available in [docs-for-repobrain/docs/install.md](docs-for-repobrain/docs/install.md).

## MCP Integration

This is what makes RepoBrain different — it runs inside Claude Code, Cursor, and Codex as a live tool, not as a separate app.

Run the MCP-style transport:

```bash
repobrain serve-mcp
```

MCP tool surface:

- `search_codebase`, `trace_flow`, `analyze_impact`, `suggest_edit_targets`, `build_change_context`
- `review_patch`, `review_codebase`, `assess_ship_readiness`
- `repobrain_search` (supports incremental streaming)
- `repobrain_blast` (single-file blast analysis)
- `repobrain_ship` (ship gate checks)
- `repobrain_gate` (SAFE/WARN/BLOCK safety verdict)
- `repobrain_status` (index health + version)
- workspace tools: `list_workspace_projects`, `track_workspace_project`, `switch_workspace_project`, `read_repo_memory`, `remember_repo_note`, `search_workspace`

## Blast Radius

Before your agent edits a file, RepoBrain tells you exactly how many other files will be affected and assigns a risk score.

Run:

```bash
repobrain blast "What breaks if I change auth callback handling?"
```

Example output (trimmed):

```json
{
  "query": "What breaks if I change auth callback handling?",
  "intent": "impact",
  "top_files": [
    {
      "file_path": "frontend/src/routes/login.ts",
      "score": 3.41
    },
    {
      "file_path": "frontend/src/services/oauth.ts",
      "score": 3.07
    },
    {
      "file_path": "frontend/src/controllers/auth.py",
      "score": 2.82
    }
  ],
  "dependency_edges": [
    "frontend/src/routes/login.ts::githubCallback --imports_call--> handleGitHubCallback"
  ],
  "affected_files": 3,
  "risk_score": "high",
  "confidence": 0.79,
  "warnings": []
}
```

## How To Run

Fast path for most users:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --cache-dir .pip-cache -e .
repobrain first-look --no-report --format text
repobrain query "Where is payment retry logic implemented?"
repobrain trace "Trace login with Google from route to service"
repobrain targets "Which files should I edit to add GitHub login?"
repobrain chat
repobrain report --format text
repobrain serve-web --open
```

Pre-merge checks:

```bash
repobrain review --format text
repobrain ship --format text
repobrain patch-review --format text
```

From outside the target repo, initialize it once and then keep commands short:

```powershell
repobrain first-look --repo "C:\path\to\your-project" --no-report --format text
repobrain init --repo "C:\path\to\your-project" --format text
repobrain review --format text
repobrain baseline --format text
repobrain index --format text
repobrain query "Where is payment retry logic implemented?" --format text
repobrain patch-review --base main --format text
repobrain ship --format text
repobrain report --open
```

Or open the browser UI and import there:

```powershell
repobrain serve-web --open
```

Then paste the project path and click `Import + Index`.
On desktop runs, you can also click `Choose folder` to open the native OS folder picker through the local Python server.
For the one-page audit flow, click `Scan Project Review`.
The browser UI now ships as a React TSX frontend with interface language controls, a light/dark theme toggle, and structured `doctor` / `provider-smoke` diagnostics cards.
You can also switch tracked repos, save repo memory notes, run cross-repo query mode, and trigger `Patch Review` with either a base ref or an explicit file list from the same page.

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --cache-dir .pip-cache -e .
repobrain init
repobrain review --format text
repobrain baseline --format text
repobrain index
repobrain doctor
repobrain query "Where is payment retry logic implemented?" --format text
repobrain ship --format text
repobrain report --format text
```

Optional one-time bootstrap for a brand-new virtualenv:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Optional extras (install only what you need):

```bash
python -m pip install --cache-dir .pip-cache -e ".[dev]"
python -m pip install --cache-dir .pip-cache -e ".[providers]"
python -m pip install --cache-dir .pip-cache -e ".[tree-sitter]"
python -m pip install --cache-dir .pip-cache -e ".[mcp]"
```

On Windows, double-click `chat.cmd` for local chat or `report.cmd` for the visual dashboard. Both launchers prefer the project virtualenv and set `PYTHONPATH=src`.

See the full run guide in [docs-for-repobrain/docs/run.md](docs-for-repobrain/docs/run.md).

Frontend source for the browser UI lives in `webapp/`. The built local assets are generated into `webapp/dist/`, and `repobrain serve-web` serves that React build directly. If `webapp/dist/` is missing, run `npm run build` inside `webapp/` once before starting the Python web server.

### Docker

Build the local image (fast default: core package + prebuilt frontend assets):

```powershell
docker build -t repobrain:local .
```

Build with optional extras:

```powershell
docker build -t repobrain:local --build-arg REPOBRAIN_PIP_EXTRAS=providers,tree-sitter,mcp .
```

Rebuild frontend inside Docker (slower):

```powershell
docker build -t repobrain:local --target runtime-webbuild .
```

Run the web UI:

```powershell
docker run --rm -it -p 8765:8765 -v ${PWD}:/workspace repobrain:local web
```

Run the CLI/chat:

```powershell
docker run --rm -it -v ${PWD}:/workspace repobrain:local cli
```

Docker Compose shortcuts:

```powershell
docker compose up --build repobrain-web
docker compose --profile cli run --rm repobrain-cli
```

Compose with optional extras:

```powershell
$env:REPOBRAIN_DOCKER_EXTRAS="providers,tree-sitter,mcp"
docker compose up --build repobrain-web
```

The web UI includes Gemini and Groq setup panels. After importing a project, paste the provider API key, keep or edit the model pool, and save. RepoBrain writes `.env` and `repobrain.toml` inside the mounted project so Docker and local runs share the same provider setup.

See [docs-for-repobrain/docs/docker.md](docs-for-repobrain/docs/docker.md).

There is also a separate human-friendly documentation frontend in `docs-for-repobrain/` for onboarding, repo reading, and demo prep:

```bash
cd docs-for-repobrain
npm install
npm run dev
```

That app renders a curated command guide, release-state summary, selected repo markdown files, shareable reader URLs, and one-click command copy actions inside a modern light/dark docs UI.

## CLI Surface

```text
repobrain first-look
repobrain start
repobrain demo
repobrain init
repobrain index
repobrain review
repobrain baseline
repobrain query "<question>"
repobrain ask "<question>"
repobrain trace "<question>"
repobrain map "<question>"
repobrain impact "<question>"
repobrain blast "<question>"
repobrain targets "<question>"
repobrain plan "<question>"
repobrain patch-review
repobrain benchmark
repobrain ship
repobrain gate
repobrain check-gate
repobrain doctor
repobrain check
repobrain provider-smoke
repobrain smoke
repobrain key gemini
repobrain key groq
repobrain chat
repobrain report
repobrain report --open
repobrain demo-clean --format text
repobrain serve-web
repobrain ui
repobrain workspace add "<path>"
repobrain workspace list
repobrain workspace use "<project>"
repobrain workspace summary
repobrain workspace remember "<note>"
repobrain workspace clear-notes
repobrain memory add --file "<path>" --note "<note>" --severity critical
repobrain memory show --file "<path>"
repobrain memory log
repobrain memory clear
repobrain quickstart
repobrain release-check --format text
repobrain serve-mcp
```

For human-friendly terminal output, add `--format text` to `review`, `index`, `query`/`ask`, `trace`/`map`, `impact`/`blast`, `targets`/`plan`, `benchmark`, `doctor`/`check`, `provider-smoke`/`smoke`, `gate`, `memory log`, or `report`. JSON remains the default for agents and automation.

Use `--no-memory` on `query`, `trace`, `impact`/`blast`, `targets`/`plan`, `review`, `patch-review`, `ship`, and `gate` when you need to skip memory lookup for a single run.

Friendly aliases keep the CLI short without removing the original command names: `start=first-look`, `ask=query`, `map=trace`, `blast=impact`, `plan=targets`, `check=doctor`, `smoke=provider-smoke`, and `ui=serve-web`.

`repobrain patch-review` reviews the current working tree by default, supports `--base <ref>` for committed diff review, and supports `--files <path...>` for explicit repo-relative patch slices.

For release validation, run `repobrain release-check --format text` before packaging, then `repobrain release-check --require-dist --format text` after `python -m build` to confirm wheel/sdist artifacts include the React frontend assets.

Before a live demo, run `repobrain demo-clean --format text` to remove local test/build clutter such as `pytest_work_*`, root `dist/`, and cache directories while preserving `webapp/dist` for `repobrain serve-web`.

## Example Query Output

```json
{
  "query": "Where is payment retry logic implemented?",
  "intent": "locate",
  "top_files": [
    {
      "file_path": "app/services/retry_handler.py",
      "language": "python",
      "role": "service",
      "score": 3.18,
      "reasons": ["bm25", "reranked", "symbol:enqueue_payment_retry"]
    },
    {
      "file_path": "app/jobs/payment_retry_job.py",
      "language": "python",
      "role": "job",
      "score": 2.74,
      "reasons": ["bm25", "reranked"]
    }
  ],
  "confidence": 0.77
}
```

## Configuration

RepoBrain reads `repobrain.toml` from the repository root.

```toml
[project]
name = "RepoBrain"
repo_roots = ["."]
state_dir = ".repobrain"
context_budget = 12000

[indexing]
exclude = [
  ".git",
  ".venv",
  "venv",
  "__pycache__",
  ".pytest_cache",
  ".pytest_tmp",
  "pytest_tmp",
  "pytest_tmp_run",
  "pytest-cache-files-*",
  "node_modules",
  "dist",
  "build",
  ".repobrain",
]
chunk_max_lines = 80
chunk_overlap_lines = 12

[parsing]
prefer_tree_sitter = true
tree_sitter_languages = ["python", "typescript", "javascript"]

[providers]
embedding = "local"
reranker = "local"
```

Remote providers are opt-in. Install `.[providers]`, set the relevant API key in `.env`, and explicitly change `repobrain.toml` before RepoBrain sends code to Gemini, OpenAI, Voyage, Cohere, or Groq.

For the Gemini path, the CLI can write both `.env` and `repobrain.toml` without echoing the key:

```bash
repobrain key gemini --repo /path/to/your-project --format text
```

Inside `repobrain chat`, use `/key gemini` for the same secure prompt.

Cheap Gemini setup:

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

`gemini_rerank_model` is not locked to a single Gemini release. RepoBrain passes the configured string straight to the Gemini SDK, so you can switch between current supported models such as `gemini-2.5-flash`, `gemini-3-flash-preview`, or `gemini-2.5-flash-preview-09-2025`.

If you want automatic fallback when one Gemini rerank model hits quota or rate limits, set `GEMINI_MODELS` in `.env` as a comma-separated ordered pool. RepoBrain will keep the first healthy model active and move to the next one only for quota/rate-limit exhaustion errors.

For a one-key Groq setup, keep embeddings local and enable Groq reranking:

```bash
repobrain key groq --repo /path/to/your-project --format text
```

Inside `repobrain chat`, use `/key groq` for the same secure prompt.

```toml
[providers]
embedding = "local"
reranker = "groq"
groq_rerank_model = "llama-3.3-70b-versatile"
groq_models = ["llama-3.3-70b-versatile", "openai/gpt-oss-20b"]
```

Groq reranking calls Chat Completions with JSON Object Mode and reads `choices[0].message.content` as `{"score": number}`. If a Groq model hits quota, rate limit, or temporary provider-capacity exhaustion, RepoBrain tries the next model in `GROQ_MODELS`.

Start from `.env.example` and fill the key for the provider you enable.

## Design Principles

- Local-first by default
- Pluggable providers for local or cloud inference
- Evidence before edit suggestion
- Degrade gracefully when tree-sitter or remote SDKs are unavailable
- Keep the repo runnable without heavyweight infrastructure

## Comparison To Naive AI Code Search

| Capability | Naive agent scan | RepoBrain |
| --- | --- | --- |
| File discovery | heuristic guessing | indexed hybrid retrieval |
| Flow tracing | shallow grep | symbol + import + call-edge hints |
| Edit target ranking | implicit intuition | explicit scored suggestions |
| Confidence | rarely stated | explicit score + warnings |
| Transport | chat-only | CLI + stdio MCP-style adapter |

## Docs

- [Vision](docs-for-repobrain/docs/vision.md)
- [Install Guide](docs-for-repobrain/docs/install.md)
- [Docker Setup](docs-for-repobrain/docs/docker.md)
- [Product Spec](docs-for-repobrain/docs/product-spec.md)
- [Production Readiness](docs-for-repobrain/docs/production-readiness.md)
- [Production Gates v1](docs-for-repobrain/docs/production-gates-v1.md)
- [Release Checklist](docs-for-repobrain/docs/release-checklist.md)
- [Architecture](docs-for-repobrain/docs/architecture.md)
- [CLI](docs-for-repobrain/docs/cli.md)
- [User Experience](docs-for-repobrain/docs/ux.md)
- [Run Guide](docs-for-repobrain/docs/run.md)
- [MCP](docs-for-repobrain/docs/mcp.md)
- [Config](docs-for-repobrain/docs/config.md)
- [Contracts](docs-for-repobrain/docs/contracts.md)
- [Evaluation](docs-for-repobrain/docs/evaluation.md)
- [Demo Script](docs-for-repobrain/docs/demo-script.md)
- [Releases](docs-for-repobrain/docs/releases.md)
- [Implementation Plan](docs-for-repobrain/docs/implementation-plan.md)
- [Decision Log](docs-for-repobrain/docs/decision-log.md)
- [Backlog](docs-for-repobrain/docs/backlog.md)
- [Self Review](docs-for-repobrain/docs/self-review.md)
- [Roadmap](docs-for-repobrain/docs/roadmap.md)
- [Model Provider Roadmap](docs-for-repobrain/docs/model-provider-roadmap.md)
- [Security Policy](SECURITY.md)

## Release Track

- `0.1.x`: runnable MVP, local indexing, hybrid retrieval, edit targets
- `0.2.x`: parser quality upgrade, better graph extraction, stronger retrieval fusion
- `0.3.x`: confidence calibration, stronger impact analysis, safer change context
- `0.5.x`: provider adapters and richer MCP ergonomics
- `1.0.0`: trusted local codebase memory product with stable contracts

See the detailed breakdown in [docs-for-repobrain/docs/roadmap.md](docs-for-repobrain/docs/roadmap.md) and [docs-for-repobrain/docs/releases.md](docs-for-repobrain/docs/releases.md).

## 🚀 v1.3 — Early Access

A major update is ready with:
- 🚦 **Agent Safety Gate** — `repobrain gate` returns SAFE/WARN/BLOCK before every commit
- 🔍 **Evidence-Based Confidence Score** — every output includes retrieval strength, recency, signal agreement
- 🧠 **Persistent Workspace Memory** — annotate files once, surfaces notes on every future run
- ⚡ **Faster Blast** — incremental cache, parallel parsing, early vendor skip
- 🤖 **Full MCP Server** — gate, memory, search, status tools ready for Claude Code, Cursor, Codex

This version is currently in **private early access**.

👉 [Open an issue](https://github.com/hieuchaydi/RepoBrain/issues/new?template=early_access.md&title=%5BEarly+Access+Request%5D) to request access. I'll respond personally.

## Status

This repository is a runnable MVP focused on clean architecture, testability, and a strong OSS launch narrative.
