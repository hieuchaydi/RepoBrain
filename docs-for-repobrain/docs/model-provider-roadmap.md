# Model Provider Roadmap

This note captures the next provider step after the Docker and Gemini setup work.

## Current Target: Groq

Groq is now implemented first as a reranker/scoring provider with local embeddings. The first UI list should keep tracking these fast hosted text model families:

- Groq Llama 3.1 8B Instant
- Groq Llama 3.3 70B Versatile
- Groq Qwen 3 32B

## Intended UX

- Groq has a provider setup panel similar to the Gemini panel.
- The user can set the API key and model pool from the browser or CLI.
- Local providers remain the default.
- Provider keys are stored in `.env`; responses do not echo keys back.
- Provider selection is stored in `repobrain.toml`.
- Doctor shows active model, fallback status, and provider readiness.

## Engineering Notes

- Provider abstractions stay compatible with the existing `EmbeddingProvider` and `RerankerProvider` contracts.
- Groq is introduced as a generation-backed reranker, not an embedding provider.
- Test coverage includes missing API key, model selection persistence, CLI setup, web setup, JSON score parsing, and model-pool failover.
- Gemini fallback behavior remains unchanged while Groq has its own `GROQ_MODELS` pool.

## Follow-Up Model Families

After Groq, consider a general model registry that can describe provider capabilities:

- provider id
- display name
- model id
- task support: embedding, rerank, scoring, chat
- latency/cost hint
- requires network
- required environment variables
