from __future__ import annotations

import os
from dataclasses import dataclass

from repobrain.config import RepoBrainConfig
from repobrain.engine.provider_base import (
    EmbeddingProvider,
    RerankerProvider,
    _env_or_option,
    _env_or_option_int,
    _env_or_option_list,
    _merge_primary_model,
    _sdk_available,
)
from repobrain.engine.provider_gemini import GeminiEmbeddingProvider, GeminiReranker
from repobrain.engine.provider_groq import GroqReranker
from repobrain.engine.provider_local import LocalHashEmbeddingProvider, LocalLexicalReranker
from repobrain.engine.provider_remote import CohereReranker, OpenAIEmbeddingProvider, VoyageEmbeddingProvider


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
    elif reranker_name == "groq":
        groq_models = _env_or_option_list(options, "groq_models", "GROQ_MODELS")
        primary_model = _env_or_option(options, "groq_rerank_model", "REPOBRAIN_GROQ_RERANK_MODEL", "llama-3.3-70b-versatile")
        reranker = GroqReranker(
            model=primary_model,
            models=_merge_primary_model(primary_model, groq_models),
        )
    elif reranker_name == "cohere":
        reranker = CohereReranker(
            model=_env_or_option(options, "cohere_rerank_model", "REPOBRAIN_COHERE_RERANK_MODEL", "rerank-v3.5")
        )
    else:
        raise ValueError(f"Unsupported reranker provider: {config.providers.reranker}")

    return ProviderBundle(embedder=embedder, reranker=reranker)


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
    elif kind == "reranker" and normalized == "groq":
        if not os.getenv("GROQ_API_KEY"):
            missing.append("GROQ_API_KEY")
        if not _sdk_available("groq"):
            missing.append("groq-sdk")
    else:
        warnings.append(f"Unknown {kind} provider configured: {configured}")

    ready = not missing and not warnings
    if not ready and normalized in {"gemini", "openai", "voyage", "cohere", "groq"}:
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
