# RepoBrain
![alt text](image.png)
RepoBrain is a local-first codebase memory engine for AI coding assistants. It indexes a repository, extracts symbols and lightweight dependency edges, combines lexical and semantic retrieval, and returns grounded evidence about where logic lives, how flows connect, and which files are safest to inspect before code is changed.


## Overview

<p>
  <a href="#overview-english"><strong>Read in English</strong></a> |
  <a href="#overview-tieng-viet"><strong>Đọc bằng Tiếng Việt</strong></a>
</p>

<details open>
<summary id="overview-english"><strong>English</strong></summary>

RepoBrain exists to make coding agents less reckless.

Most AI coding failures do not start at code generation. They start earlier, when the agent reads the wrong files, misses a route-to-service or job-to-handler flow, or sounds confident without enough evidence.

RepoBrain focuses on that pre-generation step:

- index the repository into local metadata, chunks, symbols, and edges
- retrieve grounded evidence with BM25, embeddings, and reranking
- trace likely flow across route, service, job, and config surfaces
- rank edit targets with explicit rationale instead of hidden intuition
- scan a repo and produce a concise project review with the most important risks first
- lower confidence and emit warnings when evidence is weak or contradictory

The product is intentionally local-first and conservative. It ships as a CLI, a browser-based local UI, a local report/dashboard, and a stdio MCP-style adapter for tools such as Cursor, Codex, and Claude Code.

</details>

<details>
<summary id="overview-tieng-viet"><strong>Tiếng Việt</strong></summary>

RepoBrain được tạo ra để giúp AI coding assistant bớt "đoán mò" hơn.

Phần lớn lỗi của AI không bắt đầu ở bước sinh code, mà bắt đầu sớm hơn: đọc sai file, bỏ sót luồng route -> service -> job, hoặc trả lời rất tự tin dù bằng chứng còn mỏng.

RepoBrain tập trung vào đúng bước trước khi generate:

- index repo thành metadata cục bộ, chunks, symbols và dependency edges
- truy xuất bằng chứng có grounding bằng BM25, embedding và reranking
- trace luồng khả dĩ giữa route, service, background job và config
- xếp hạng file nên inspect hoặc edit với lý do rõ ràng
- tự hạ confidence và cảnh báo khi bằng chứng yếu hoặc mâu thuẫn

Sản phẩm được thiết kế theo hướng local-first và thận trọng. RepoBrain hiện có CLI, giao diện web local, report/dashboard local, và adapter stdio MCP để gắn vào Cursor, Codex, Claude Code hoặc workflow agent tương tự.

</details>

## Why RepoBrain

When coding agents fail, the root cause is usually not "bad code generation". It is bad context.

RepoBrain focuses on the step before generation:

- Find the right files.
- Surface the most relevant symbols and snippets.
- Trace likely route -> service -> job flows.
- Rank edit targets with evidence instead of intuition.
- Downgrade confidence when the evidence is weak or contradictory.

This makes RepoBrain useful both as:

- a CLI you can run locally against any repo
- a stdio MCP-style tool adapter for Cursor, Codex, and Claude Code

## What Ships In `0.1.x`

- Python package under `src/repobrain`
- Local SQLite metadata store in `.repobrain/metadata.db`
- Persisted vector index in `.repobrain/vectors/`
- Python + TypeScript/JavaScript support
- Hybrid retrieval with BM25 + local hash embeddings + reranking
- Grounding harness with planner, retriever, file selector, evidence collector, edit-target scorer, and self-check
- Markdown docs for architecture, CLI, MCP, config, evaluation, demos, releases, and run guides

## Current Unreleased Track

This unreleased track now maps most closely to the `0.5.x` integration line: it bundles provider adapters, provider smoke checks, a React browser UI, and release-facing diagnostics into one local workflow.

- Interactive local chat loop through `repobrain chat`
- Saved review baselines through `repobrain baseline`
- Windows one-click launcher through `chat.cmd`
- Windows one-click dashboard launcher through `report.cmd`
- Human-readable terminal output through `--format text`
- Local HTML status dashboard through `repobrain report` or `repobrain report --open`
- Production ship gate through `repobrain ship`
- Live provider access checks through `repobrain provider-smoke`
- Active repo memory: run `repobrain init --repo <path>` once, then omit `--repo`
- Local browser UI through `repobrain serve-web --open`
- React TSX local browser UI with English/Vietnamese interface toggle, light/dark theme, structured diagnostics cards, tracked workspace switching, repo memory notes, and cross-repo query mode with leaders, shared hotspots, and citation previews
- Persisted workspace memory shared across CLI chat, browser UI, and MCP tools
- Concise repo scan through `repobrain review --format text`
- Optional SDK-backed Gemini/OpenAI/Voyage/Cohere provider adapters
- Gemini rerank model pools through `GEMINI_MODELS` with automatic failover on quota/rate-limit exhaustion
- Optional tree-sitter parser adapter layer with heuristic fallback
- Parser usage stats in `repobrain index`
- Richer parser capability reporting in `repobrain doctor`

## How To Run

Full bilingual installation instructions are available in [docs/install.md](docs/install.md).

Fast path for end users:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev,tree-sitter,mcp]"
repobrain init
repobrain review --format text
repobrain baseline --format text
repobrain index
repobrain query "Where is payment retry logic implemented?"
repobrain trace "Trace login with Google from route to service"
repobrain targets "Which files should I edit to add GitHub login?"
repobrain ship --format text
repobrain chat
repobrain report --format text
repobrain serve-web --open
```

From outside the target repo, initialize it once and then keep commands short:

```powershell
repobrain init --repo "C:\path\to\your-project" --format text
repobrain review --format text
repobrain baseline --format text
repobrain index --format text
repobrain query "Where is payment retry logic implemented?" --format text
repobrain ship --format text
repobrain report --open
```

Or open the browser UI and import there:

```powershell
repobrain serve-web --open
```

Then paste the project path and click `Import + Index`.
For the one-page audit flow, click `Scan Project Review`.
The browser UI now ships as a React TSX frontend with English/Vietnamese interface labels, a light/dark theme toggle, and structured `doctor` / `provider-smoke` diagnostics cards.

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,tree-sitter,mcp]"
repobrain init
repobrain review --format text
repobrain baseline --format text
repobrain index
repobrain doctor
repobrain query "Where is payment retry logic implemented?" --format text
repobrain ship --format text
repobrain report --format text
```

Run the MCP-style transport:

```bash
repobrain serve-mcp
```

On Windows, double-click `chat.cmd` for local chat or `report.cmd` for the visual dashboard. Both launchers prefer the project virtualenv and set `PYTHONPATH=src`.

See the full run guide in [docs/run.md](docs/run.md).

Frontend source for the browser UI lives in `webapp/`. The built local assets are generated into `webapp/dist/`, and `repobrain serve-web` serves that React build directly. If `webapp/dist/` is missing, run `npm run build` inside `webapp/` once before starting the Python web server.

There is also a separate human-friendly documentation frontend in `docs-for-repobrain/` for onboarding, repo reading, and demo prep:

```bash
cd docs-for-repobrain
npm install
npm run dev
```

That app renders a curated command guide, release-state summary, selected repo markdown files, shareable reader URLs, and one-click command copy actions inside a modern light/dark docs UI.

## CLI Surface

```text
repobrain init
repobrain index
repobrain review
repobrain baseline
repobrain query "<question>"
repobrain trace "<question>"
repobrain impact "<question>"
repobrain targets "<question>"
repobrain benchmark
repobrain ship
repobrain doctor
repobrain provider-smoke
repobrain chat
repobrain report
repobrain report --open
repobrain demo-clean --format text
repobrain serve-web
repobrain workspace list
repobrain workspace summary
repobrain quickstart
repobrain release-check --format text
repobrain serve-mcp
```

For human-friendly terminal output, add `--format text` to `review`, `index`, `query`, `trace`, `impact`, `targets`, `benchmark`, `doctor`, `provider-smoke`, or `report`. JSON remains the default for agents and automation.

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

Remote providers are opt-in. Install `.[providers]`, set the relevant API key in `.env`, and explicitly change `repobrain.toml` before RepoBrain sends code to Gemini, OpenAI, Voyage, or Cohere.

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

Start from `.env.example` and fill `GEMINI_API_KEY`.

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

- [Vision](docs/vision.md)
- [Install Guide](docs/install.md)
- [Product Spec](docs/product-spec.md)
- [Production Readiness](docs/production-readiness.md)
- [Release Checklist](docs/release-checklist.md)
- [Architecture](docs/architecture.md)
- [CLI](docs/cli.md)
- [User Experience](docs/ux.md)
- [Run Guide](docs/run.md)
- [MCP](docs/mcp.md)
- [Config](docs/config.md)
- [Contracts](docs/contracts.md)
- [Evaluation](docs/evaluation.md)
- [Demo Script](docs/demo-script.md)
- [Releases](docs/releases.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Decision Log](docs/decision-log.md)
- [Backlog](docs/backlog.md)
- [Self Review](docs/self-review.md)
- [Vietnamese Review](docs/review-vi.md)
- [Roadmap](ROADMAP.md)
- [Feature Direction](feat.md)
- [Security Policy](SECURITY.md)
- [Repo Rules](RULES.md)
- [Repo Skills](SKILLS.md)

## Release Track

- `0.1.x`: runnable MVP, local indexing, hybrid retrieval, edit targets
- `0.2.x`: parser quality upgrade, better graph extraction, stronger retrieval fusion
- `0.3.x`: confidence calibration, stronger impact analysis, safer change context
- `0.5.x`: provider adapters and richer MCP ergonomics
- `1.0.0`: trusted local codebase memory product with stable contracts

See the detailed breakdown in [ROADMAP.md](ROADMAP.md) and [docs/releases.md](docs/releases.md).

## Status

This repository is a runnable MVP focused on clean architecture, testability, and a strong OSS launch narrative.
