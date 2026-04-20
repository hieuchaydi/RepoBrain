from __future__ import annotations

import os

from repobrain.engine.provider_base import (
    RemoteProviderError,
    _coerce_embedding,
    _exc_text,
    _is_quota_or_rate_limit_error,
    _parse_score,
    _read_value,
)


def _is_gemini_quota_or_rate_limit_error(exc: Exception) -> bool:
    return _is_quota_or_rate_limit_error(exc)


def _gemini_client() -> object:
    if not os.getenv("GEMINI_API_KEY"):
        raise RemoteProviderError("GEMINI_API_KEY is required for the Gemini provider.")
    try:
        from google import genai  # type: ignore[attr-defined]
    except ImportError as exc:
        raise RemoteProviderError('Install provider extras with `python -m pip install -e ".[providers]"` to use Gemini providers.') from exc
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _gemini_embed_config(output_dimensionality: int, task_type: str) -> object:
    payload = {"output_dimensionality": output_dimensionality, "task_type": task_type}
    try:
        from google.genai import types  # type: ignore[attr-defined]

        return types.EmbedContentConfig(**payload)
    except (ImportError, AttributeError, TypeError):
        return payload


class GeminiEmbeddingProvider:
    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
        task_type: str = "SEMANTIC_SIMILARITY",
        client: object | None = None,
    ) -> None:
        self.model = model
        self.output_dimensionality = output_dimensionality
        self.task_type = task_type
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        config = _gemini_embed_config(self.output_dimensionality, self.task_type)
        try:
            response = client.models.embed_content(model=self.model, contents=texts, config=config)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
            raise RemoteProviderError(f"Gemini embedding request failed: {exc}") from exc

        records = list(_read_value(response, "embeddings", []) or [])
        vectors = [_coerce_embedding(record) for record in records]
        if len(vectors) != len(texts):
            raise RemoteProviderError("Gemini embedding response length did not match the requested input length.")
        return vectors

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        self._client = _gemini_client()
        return self._client


class GeminiReranker:
    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        models: list[str] | None = None,
        client: object | None = None,
    ) -> None:
        configured_models = [item for item in (models or [model]) if item]
        if not configured_models:
            configured_models = [model]
        self.models = configured_models
        self.model = configured_models[0]
        self._active_model_index = 0
        self.last_failover_error: str | None = None
        self._client = client

    def score(self, query: str, candidate_text: str) -> float:
        if not query.strip() or not candidate_text.strip():
            return 0.0
        client = self._get_client()
        prompt = (
            "Score how relevant this code evidence is to the query. "
            "Return only one decimal number between 0 and 1.\n\n"
            f"Query:\n{query}\n\nEvidence:\n{candidate_text[:4000]}"
        )
        failures: list[str] = []
        models_to_try = self.models[self._active_model_index :] + self.models[: self._active_model_index]

        for index, model_name in enumerate(models_to_try):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)  # type: ignore[attr-defined]
            except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
                if _is_gemini_quota_or_rate_limit_error(exc):
                    failures.append(f"{model_name}: {_exc_text(exc)}")
                    if index < len(models_to_try) - 1:
                        next_model = models_to_try[index + 1]
                        self._active_model_index = self.models.index(next_model)
                        self.model = next_model
                        self.last_failover_error = _exc_text(exc)
                        continue
                    tried = ", ".join(self.models)
                    details = " | ".join(failures)
                    raise RemoteProviderError(
                        "Gemini rerank request hit quota/rate-limit exhaustion across the configured model pool. "
                        f"Tried: {tried}. Details: {details}"
                    ) from exc
                raise RemoteProviderError(f"Gemini rerank request failed with model `{model_name}`: {exc}") from exc

            self._active_model_index = self.models.index(model_name)
            self.model = model_name
            return _parse_score(str(_read_value(response, "text", "")))

        raise RemoteProviderError("Gemini rerank request failed before any configured model could return a score.")

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        self._client = _gemini_client()
        return self._client
