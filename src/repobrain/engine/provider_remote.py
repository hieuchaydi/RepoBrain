from __future__ import annotations

import importlib
import os

from repobrain.engine.provider_base import RemoteProviderError, _coerce_embedding, _read_value


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small", client: object | None = None) -> None:
        self.model = model
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        try:
            response = client.embeddings.create(model=self.model, input=texts)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
            raise RemoteProviderError(f"OpenAI embedding request failed: {exc}") from exc

        records = list(_read_value(response, "data", []) or [])
        if records and all(_read_value(record, "index") is not None for record in records):
            records.sort(key=lambda record: int(_read_value(record, "index", 0) or 0))
        vectors = [_coerce_embedding(record) for record in records]
        if len(vectors) != len(texts):
            raise RemoteProviderError("OpenAI embedding response length did not match the requested input length.")
        return vectors

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        if not os.getenv("OPENAI_API_KEY"):
            raise RemoteProviderError("OPENAI_API_KEY is required for the OpenAI embedding provider.")
        try:
            module = importlib.import_module("openai")
            client_factory = getattr(module, "OpenAI")
        except (ImportError, AttributeError) as exc:
            raise RemoteProviderError('Install provider extras with `python -m pip install -e ".[providers]"` to use OpenAI embeddings.') from exc
        self._client = client_factory()
        return self._client


class VoyageEmbeddingProvider:
    name = "voyage"

    def __init__(self, model: str = "voyage-code-3", input_type: str = "document", client: object | None = None) -> None:
        self.model = model
        self.input_type = input_type
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        try:
            response = client.embed(texts, model=self.model, input_type=self.input_type)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
            raise RemoteProviderError(f"Voyage embedding request failed: {exc}") from exc

        embeddings = _read_value(response, "embeddings", [])
        vectors = [[float(value) for value in vector] for vector in embeddings]  # type: ignore[union-attr]
        if len(vectors) != len(texts):
            raise RemoteProviderError("Voyage embedding response length did not match the requested input length.")
        return vectors

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        if not os.getenv("VOYAGE_API_KEY"):
            raise RemoteProviderError("VOYAGE_API_KEY is required for the Voyage embedding provider.")
        try:
            module = importlib.import_module("voyageai")
            client_factory = getattr(module, "Client")
        except (ImportError, AttributeError) as exc:
            raise RemoteProviderError('Install provider extras with `python -m pip install -e ".[providers]"` to use Voyage embeddings.') from exc
        self._client = client_factory()
        return self._client


class CohereReranker:
    name = "cohere"

    def __init__(self, model: str = "rerank-v3.5", client: object | None = None) -> None:
        self.model = model
        self._client = client

    def score(self, query: str, candidate_text: str) -> float:
        if not query.strip() or not candidate_text.strip():
            return 0.0
        client = self._get_client()
        try:
            response = client.rerank(model=self.model, query=query, documents=[candidate_text], top_n=1)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
            raise RemoteProviderError(f"Cohere rerank request failed: {exc}") from exc

        results = list(_read_value(response, "results", []) or [])
        if not results:
            return 0.0
        raw_score = _read_value(results[0], "relevance_score", _read_value(results[0], "score", 0.0))
        return round(float(raw_score or 0.0), 6)

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        if not os.getenv("COHERE_API_KEY"):
            raise RemoteProviderError("COHERE_API_KEY is required for the Cohere reranker.")
        try:
            module = importlib.import_module("cohere")
            client_factory = getattr(module, "Client")
        except (ImportError, AttributeError) as exc:
            raise RemoteProviderError('Install provider extras with `python -m pip install -e ".[providers]"` to use Cohere reranking.') from exc
        self._client = client_factory(os.getenv("COHERE_API_KEY"))
        return self._client
