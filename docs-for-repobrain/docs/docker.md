# Docker Setup

RepoBrain can run as a local browser UI or as an interactive CLI from one image.

The Docker setup now defaults to a fast build:

- uses prebuilt `webapp/dist` from the repository
- installs core Python package only (`pip install .`)
- allows optional extras through build args when needed

## Build

Fastest default build:

```powershell
docker build -t repobrain:local .
```

Build with optional Python extras:

```powershell
docker build -t repobrain:local --build-arg REPOBRAIN_PIP_EXTRAS=providers,tree-sitter,mcp .
```

Rebuild frontend inside Docker (slower, but fully fresh UI assets):

```powershell
docker build -t repobrain:local --target runtime-webbuild .
```

## Run The Web UI

From the repository root:

```powershell
docker run --rm -it -p 8765:8765 -v ${PWD}:/workspace repobrain:local web
```

Open:

```text
http://127.0.0.1:8765
```

The container uses `/workspace` as the active project by default. Import that path in the UI if it is not already active.

## Run The CLI

```powershell
docker run --rm -it -v ${PWD}:/workspace repobrain:local cli
```

You can also run any RepoBrain command directly:

```powershell
docker run --rm -it -v ${PWD}:/workspace repobrain:local doctor --repo /workspace --format text
docker run --rm -it -v ${PWD}:/workspace repobrain:local index --repo /workspace --format text
docker run --rm -it -v ${PWD}:/workspace repobrain:local query "Where is the main flow implemented?" --repo /workspace --format text
```

## Docker Compose

Web UI:

```powershell
docker compose up --build repobrain-web
```

CLI:

```powershell
docker compose --profile cli run --rm repobrain-cli
```

Compose with optional extras:

```powershell
$env:REPOBRAIN_DOCKER_EXTRAS="providers,tree-sitter,mcp"
docker compose up --build repobrain-web
```

Compose with frontend rebuild target:

```powershell
$env:REPOBRAIN_DOCKER_TARGET="runtime-webbuild"
docker compose up --build repobrain-web
```

## Provider Setup In Docker

The web UI includes Gemini and Groq setup panels. After importing a project, paste the provider API key, keep or edit the model pool, and save the config. RepoBrain writes:

- `.env` with `GEMINI_API_KEY`, Gemini model variables, and `GEMINI_MODELS`
- `repobrain.toml` with `embedding = "gemini"` and `reranker = "gemini"` when the toggles are enabled
- `.env` with `GROQ_API_KEY`, `REPOBRAIN_GROQ_RERANK_MODEL`, and `GROQ_MODELS`
- `repobrain.toml` with `embedding = "local"` and `reranker = "groq"` for one-key Groq reranking

The key stays in the mounted project folder. It is not returned in API responses.

You can also set provider values before starting Compose:

```powershell
$env:GEMINI_API_KEY="your-key"
$env:GROQ_API_KEY="your-key"
docker compose up --build repobrain-web
```

## Entrypoint Modes

- `web`: start `repobrain serve-web` on `0.0.0.0:8765`
- `cli` or `chat`: start `repobrain chat`
- `repobrain <args>`: run the CLI directly
- `shell`: open `/bin/sh`

Environment knobs:

- `REPOBRAIN_REPO`: mounted project path, default `/workspace`
- `REPOBRAIN_WEB_HOST`: default `0.0.0.0`
- `REPOBRAIN_WEB_PORT`: default `8765`
- `GEMINI_API_KEY`: optional Gemini key for remote providers
- `GEMINI_MODELS`: optional comma-separated reranker fallback pool
- `GROQ_API_KEY`: optional Groq key for remote reranking
- `GROQ_MODELS`: optional comma-separated Groq reranker fallback pool
