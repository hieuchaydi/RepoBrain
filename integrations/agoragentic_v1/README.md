# RepoBrain x Agoragentic v1 (Thin CLI Adapter)

This folder contains a local-first, self-hosted, educational-only v1 package for the first Agoragentic listing discussed in issue #9.

## Scope

- One capability: repository/context retrieval.
- Input: `query` + optional `repo_scope` + optional `top_k` + optional `include_snippets`.
- Output: ranked context results (`path`, `score`, `source`, `confidence`, optional `snippet`) plus metadata.
- Runtime model: adapter runs near RepoBrain as a CLI tool (no hosted vendor layer required).
- Example payloads in this folder illustrate schema shape only; calls are not restricted to a single canned case.

## Folder Layout

- `adapter/local_provider_adapter.py`: local CLI adapter.
- `payloads/agoragentic_quickstart_payload.json`: scaffold for provider registration.
- `payloads/agoragentic_capability_payload.json`: single tightened manifest plus Agoragentic wrapper fields (`pricing_model`, `category`, `delivery_method`, `runtime`, `tags`, `sandbox_probe_input`, `execution`).

## Run Adapter Locally

From repository root:

```bash
python integrations/agoragentic_v1/adapter/local_provider_adapter.py --repo-root . --health --pretty
```

Run retrieval with inline flags:

```bash
python integrations/agoragentic_v1/adapter/local_provider_adapter.py \
  --repo-root . \
  --query "Where is payment retry logic implemented?" \
  --top-k 8 \
  --include-snippets \
  --pretty
```

Run retrieval with JSON payload file:

```bash
python integrations/agoragentic_v1/adapter/local_provider_adapter.py \
  --repo-root . \
  --request-file request.json \
  --pretty
```

Run retrieval with stdin JSON:

```bash
cat request.json | python integrations/agoragentic_v1/adapter/local_provider_adapter.py --repo-root . --pretty
```

## Agoragentic Payload Prep

1. Register provider using `payloads/agoragentic_quickstart_payload.json`.
2. Publish the first free retrieval listing using `payloads/agoragentic_capability_payload.json`.
3. Keep `mode` as `educational_only` for v1.

## Notes

- `repo_scope` is standardized for v1 as a local filesystem path identity (local-first only).
- If target repo is not indexed yet, adapter auto-indexes before query.
- Snippets are optional and truncated to 420 chars with a trailing ellipsis when they exceed the adapter limit.
- This package intentionally avoids broader runtime/platform changes.
