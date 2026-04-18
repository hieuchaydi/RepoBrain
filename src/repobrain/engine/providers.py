from __future__ import annotations

import hashlib
import importlib
import importlib.util
import math
import os
import re
from dataclasses import dataclass
from typing import Protocol

from repobrain.config import RepoBrainConfig

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(item * item for item in left))
    right_norm = math.sqrt(sum(item * item for item in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class RerankerProvider(Protocol):
    name: str

    def score(self, query: str, candidate_text: str) -> float:
        ...


class LocalHashEmbeddingProvider:
    name = "local-hash"

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            tokens = tokenize(text)
            if not tokens:
                vectors.append(vector)
                continue
            for token in tokens:
                slot = self._stable_slot(token)
                vector[slot] += 1.0
            total = sum(vector) or 1.0
            vectors.append([item / total for item in vector])
        return vectors

    def _stable_slot(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dimensions


class LocalLexicalReranker:
    name = "local-lexical"

    def score(self, query: str, candidate_text: str) -> float:
        query_tokens = set(tokenize(query))
        candidate_tokens = tokenize(candidate_text)
        if not query_tokens or not candidate_tokens:
            return 0.0
        overlap = sum(1 for token in candidate_tokens if token in query_tokens)
        coverage = overlap / max(len(query_tokens), 1)
        density = overlap / max(len(candidate_tokens), 1)
        return round((coverage * 0.75) + (density * 8.0), 6)


class RemoteProviderError(RuntimeError):
    pass


def _read_value(item: object, name: str, default: object | None = None) -> object | None:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _coerce_embedding(item: object) -> list[float]:
    embedding = _read_value(item, "embedding")
    if embedding is None:
        embedding = _read_value(item, "values")
    if embedding is None:
        raise RemoteProviderError("Remote embedding response did not include an embedding vector.")
    return [float(value) for value in embedding]  # type: ignore[union-attr]


def _env_or_option(options: dict[str, object], key: str, env_name: str, default: str) -> str:
    value = options.get(key) or os.getenv(env_name) or default
    return str(value)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_or_option_list(options: dict[str, object], key: str, env_name: str) -> list[str]:
    raw = options.get(key)
    if raw is None:
        raw = os.getenv(env_name)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return _split_csv(str(raw))


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _merge_primary_model(primary_model: str, models: list[str]) -> list[str]:
    return _ordered_unique([primary_model, *models])


def _env_or_option_int(options: dict[str, object], key: str, env_name: str, default: int) -> int:
    value = options.get(key) or os.getenv(env_name) or default
    return int(value)


def _clamp_score(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _parse_score(text: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return round(_clamp_score(float(match.group(0))), 6)


def _exc_text(exc: Exception) -> str:
    return " ".join(str(exc).split()).strip()


def _is_gemini_quota_or_rate_limit_error(exc: Exception) -> bool:
    text = _exc_text(exc).lower()
    patterns = (
        "429",
        "resource_exhausted",
        "resource exhausted",
        "quota",
        "rate limit",
        "rate_limit",
        "too many requests",
        "exceeded your current quota",
        "quota exceeded",
    )
    return any(pattern in text for pattern in patterns)


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


@dataclass(slots=True)
class ProviderBundle:
    embedder: EmbeddingProvider
    reranker: RerankerProvider


@dataclass(slots=True)
class ProviderStatus:
    kind: str
    configured: str
    active: str
    local_only: bool
    ready: bool
    requires_network: bool
    missing: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "configured": self.configured,
            "active": self.active,
            "local_only": self.local_only,
            "ready": self.ready,
            "requires_network": self.requires_network,
            "missing": self.missing,
            "warnings": self.warnings,
        }


def build_provider_bundle(config: RepoBrainConfig) -> ProviderBundle:
    embedding_name = config.providers.embedding.lower()
    reranker_name = config.providers.reranker.lower()
    options = config.providers.options

    if embedding_name == "local":
        embedder: EmbeddingProvider = LocalHashEmbeddingProvider()
    elif embedding_name == "gemini":
        embedder = GeminiEmbeddingProvider(
            model=_env_or_option(options, "gemini_embedding_model", "REPOBRAIN_GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
            output_dimensionality=_env_or_option_int(options, "gemini_output_dimensionality", "REPOBRAIN_GEMINI_OUTPUT_DIMENSIONALITY", 768),
            task_type=_env_or_option(options, "gemini_task_type", "REPOBRAIN_GEMINI_TASK_TYPE", "SEMANTIC_SIMILARITY"),
        )
    elif embedding_name == "openai":
        embedder = OpenAIEmbeddingProvider(
            model=_env_or_option(options, "openai_embedding_model", "REPOBRAIN_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
    elif embedding_name == "voyage":
        embedder = VoyageEmbeddingProvider(
            model=_env_or_option(options, "voyage_embedding_model", "REPOBRAIN_VOYAGE_EMBEDDING_MODEL", "voyage-code-3"),
            input_type=_env_or_option(options, "voyage_input_type", "REPOBRAIN_VOYAGE_INPUT_TYPE", "document"),
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {config.providers.embedding}")

    if reranker_name == "local":
        reranker: RerankerProvider = LocalLexicalReranker()
    elif reranker_name == "gemini":
        gemini_models = _env_or_option_list(options, "gemini_models", "GEMINI_MODELS")
        primary_model = _env_or_option(options, "gemini_rerank_model", "REPOBRAIN_GEMINI_RERANK_MODEL", "gemini-2.5-flash")
        reranker = GeminiReranker(
            model=primary_model,
            models=_merge_primary_model(primary_model, gemini_models),
        )
    elif reranker_name == "cohere":
        reranker = CohereReranker(
            model=_env_or_option(options, "cohere_rerank_model", "REPOBRAIN_COHERE_RERANK_MODEL", "rerank-v3.5")
        )
    else:
        raise ValueError(f"Unsupported reranker provider: {config.providers.reranker}")

    return ProviderBundle(embedder=embedder, reranker=reranker)


def _sdk_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False


def _provider_status(kind: str, configured: str) -> ProviderStatus:
    normalized = configured.lower()
    if normalized == "local":
        return ProviderStatus(
            kind=kind,
            configured=configured,
            active="local",
            local_only=True,
            ready=True,
            requires_network=False,
            missing=[],
            warnings=[],
        )

    missing: list[str] = []
    warnings: list[str] = []
    active = normalized
    requires_network = True

    if normalized == "gemini" and kind in {"embedding", "reranker"}:
        if not os.getenv("GEMINI_API_KEY"):
            missing.append("GEMINI_API_KEY")
        if not _sdk_available("google.genai"):
            missing.append("google-genai-sdk")
    elif kind == "embedding" and normalized == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            missing.append("OPENAI_API_KEY")
        if not _sdk_available("openai"):
            missing.append("openai-sdk")
    elif kind == "embedding" and normalized == "voyage":
        if not os.getenv("VOYAGE_API_KEY"):
            missing.append("VOYAGE_API_KEY")
        if not _sdk_available("voyageai"):
            missing.append("voyageai-sdk")
    elif kind == "reranker" and normalized == "cohere":
        if not os.getenv("COHERE_API_KEY"):
            missing.append("COHERE_API_KEY")
        if not _sdk_available("cohere"):
            missing.append("cohere-sdk")
    else:
        warnings.append(f"Unknown {kind} provider configured: {configured}")

    ready = not missing and not warnings
    if not ready and normalized in {"gemini", "openai", "voyage", "cohere"}:
        warnings.append("Remote provider is configured but not fully ready. RepoBrain will fail if this provider path is used.")

    return ProviderStatus(
        kind=kind,
        configured=configured,
        active=active,
        local_only=False,
        ready=ready,
        requires_network=requires_network,
        missing=missing,
        warnings=warnings,
    )


def inspect_provider_status(config: RepoBrainConfig) -> dict[str, dict[str, object]]:
    embedding_status = _provider_status("embedding", config.providers.embedding)
    reranker_status = _provider_status("reranker", config.providers.reranker)
    return {
        "embedding": embedding_status.to_dict(),
        "reranker": reranker_status.to_dict(),
    }
