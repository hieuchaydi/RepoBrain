# Configuration

RepoBrain reads `repobrain.toml` from the repository root.

## Project

```toml
[project]
name = "RepoBrain"
repo_roots = ["."]
state_dir = ".repobrain"
context_budget = 12000
```

- `name`: display name in logs and docs
- `repo_roots`: reserved for future multi-root support
- `state_dir`: local storage location
- `context_budget`: default token or character budget for future context packers

## Indexing

```toml
[indexing]
include = []
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
max_file_size_bytes = 200000
chunk_max_lines = 80
chunk_overlap_lines = 12
```

- `include`: optional allowlist globs
- `exclude`: denylist patterns plus ignore files; virtualenvs and test temp folders should stay excluded
- `max_file_size_bytes`: skip very large generated files
- `chunk_max_lines`: maximum lines per chunk
- `chunk_overlap_lines`: overlap for fallback window chunks

## Parsing

```toml
[parsing]
prefer_tree_sitter = true
tree_sitter_languages = ["python", "typescript", "javascript"]
```

- `prefer_tree_sitter`: use optional tree-sitter adapters when the runtime and grammar packages are installed
- `tree_sitter_languages`: languages that are allowed to use the optional parser path

The built-in heuristic parser always remains available as the fallback. This keeps RepoBrain runnable without optional native parser packages.

## Providers

```toml
[providers]
embedding = "local"
reranker = "local"
```

Supported values today:

- `embedding`: `local`, `gemini`, `openai`, `voyage`
- `reranker`: `local`, `gemini`, `cohere`

Local is the default. Remote providers are optional, explicit, and require SDK extras plus credentials.

Install remote provider SDKs only when you need them:

```bash
python -m pip install -e ".[providers]"
```

Remote embedding example:

```toml
[providers]
embedding = "openai"
reranker = "local"
openai_embedding_model = "text-embedding-3-small"
```

Gemini setup:

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

`gemini_rerank_model` is a pass-through string. RepoBrain does not restrict you to one Gemini text model, so you can point it at any currently supported Gemini rerank-capable text model your account can access, for example `gemini-3-flash-preview` or `gemini-2.5-flash-preview-09-2025`.

If `gemini_models` or `GEMINI_MODELS` is configured, RepoBrain treats it as an ordered fallback pool for Gemini reranking. When the active Gemini model returns a quota or rate-limit exhaustion error, RepoBrain automatically retries with the next model in the pool. Non-quota failures still surface immediately so bad model names or auth/config issues do not get hidden.

Voyage embedding plus Cohere reranking example:

```toml
[providers]
embedding = "voyage"
reranker = "cohere"
voyage_embedding_model = "voyage-code-3"
voyage_input_type = "document"
cohere_rerank_model = "rerank-v3.5"
```

Environment variables:

- `GEMINI_API_KEY`: required when `embedding = "gemini"` or `reranker = "gemini"`
- `REPOBRAIN_GEMINI_EMBEDDING_MODEL`: optional override for Gemini embedding model
- `REPOBRAIN_GEMINI_OUTPUT_DIMENSIONALITY`: optional override for Gemini embedding dimensions
- `REPOBRAIN_GEMINI_TASK_TYPE`: optional override for Gemini embedding task type
- `REPOBRAIN_GEMINI_RERANK_MODEL`: optional override for Gemini rerank model
- `GEMINI_MODELS`: optional comma-separated fallback pool for Gemini rerank model failover
- `OPENAI_API_KEY`: required when `embedding = "openai"`
- `VOYAGE_API_KEY`: required when `embedding = "voyage"`
- `COHERE_API_KEY`: required when `reranker = "cohere"`
- `REPOBRAIN_OPENAI_EMBEDDING_MODEL`: optional override for OpenAI embedding model
- `REPOBRAIN_VOYAGE_EMBEDDING_MODEL`: optional override for Voyage embedding model
- `REPOBRAIN_VOYAGE_INPUT_TYPE`: optional override for Voyage input type
- `REPOBRAIN_COHERE_RERANK_MODEL`: optional override for Cohere rerank model

Security rule: RepoBrain never sends code to a remote provider unless `repobrain.toml` explicitly selects a remote provider.

RepoBrain loads `.env` from the repo root automatically and does not override environment variables that are already set by the shell. Start from `.env.example` for a safe template.
