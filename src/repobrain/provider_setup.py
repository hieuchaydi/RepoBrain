from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path

from repobrain.active_repo import write_active_repo
from repobrain.config import RepoBrainConfig


DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_GEMINI_OUTPUT_DIMENSIONALITY = 768
DEFAULT_GEMINI_TASK_TYPE = "SEMANTIC_SIMILARITY"
DEFAULT_GEMINI_RERANK_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_MODEL_POOL = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
)
DEFAULT_GEMINI_MODEL_POOL_TEXT = ",".join(DEFAULT_GEMINI_MODEL_POOL)
DEFAULT_GROQ_RERANK_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_MODEL_POOL = (
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
)
DEFAULT_GROQ_MODEL_POOL_TEXT = ",".join(DEFAULT_GROQ_MODEL_POOL)

GEMINI_ENV_KEYS = {
    "GEMINI_API_KEY",
    "REPOBRAIN_GEMINI_EMBEDDING_MODEL",
    "REPOBRAIN_GEMINI_OUTPUT_DIMENSIONALITY",
    "REPOBRAIN_GEMINI_TASK_TYPE",
    "REPOBRAIN_GEMINI_RERANK_MODEL",
    "GEMINI_MODELS",
}
GROQ_ENV_KEYS = {
    "GROQ_API_KEY",
    "REPOBRAIN_GROQ_RERANK_MODEL",
    "GROQ_MODELS",
}


def _env_quote(value: str) -> str:
    if not value or any(char.isspace() for char in value) or any(char in value for char in "#'\""):
        return json.dumps(value)
    return value


def write_env_values(repo_root: str | Path, updates: dict[str, str]) -> Path:
    root = Path(repo_root).expanduser().resolve()
    env_path = root / ".env"
    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    written_keys: set[str] = set()
    output_lines: list[str] = []

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        key_text = stripped.removeprefix("export ").split("=", 1)[0].strip() if "=" in stripped else ""
        if key_text in updates:
            output_lines.append(f"{key_text}={_env_quote(updates[key_text])}")
            written_keys.add(key_text)
        else:
            output_lines.append(raw_line)

    if output_lines and output_lines[-1].strip():
        output_lines.append("")
    for key, value in updates.items():
        if key not in written_keys:
            output_lines.append(f"{key}={_env_quote(value)}")

    env_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")
    for key, value in updates.items():
        os.environ[key] = value
    return env_path


def _normalize_model_pool(model_pool: str | Iterable[str] | None, primary_model: str) -> list[str]:
    if model_pool is None:
        raw_items: list[str] = []
    elif isinstance(model_pool, str):
        raw_items = [item.strip() for item in model_pool.replace("\n", ",").split(",") if item.strip()]
    else:
        raw_items = [str(item).strip() for item in model_pool if str(item).strip()]

    ordered_items = [primary_model, *raw_items]
    normalized: list[str] = []
    seen: set[str] = set()
    for item in ordered_items:
        if item and item not in seen:
            normalized.append(item)
            seen.add(item)
    return normalized or [DEFAULT_GEMINI_RERANK_MODEL]


def _normalize_output_dimensionality(value: str | int) -> int:
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ValueError("Gemini output dimensionality must be an integer.") from exc


def configure_gemini_provider(
    repo_root: str | Path,
    *,
    api_key: str = "",
    use_embedding: bool = True,
    use_reranker: bool = True,
    embedding_model: str = DEFAULT_GEMINI_EMBEDDING_MODEL,
    output_dimensionality: str | int = DEFAULT_GEMINI_OUTPUT_DIMENSIONALITY,
    task_type: str = DEFAULT_GEMINI_TASK_TYPE,
    rerank_model: str = DEFAULT_GEMINI_RERANK_MODEL,
    model_pool: str | Iterable[str] | None = None,
) -> dict[str, object]:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("Project path does not exist or is not a directory.")

    normalized_embedding_model = str(embedding_model).strip() or DEFAULT_GEMINI_EMBEDDING_MODEL
    normalized_output_dimensionality = _normalize_output_dimensionality(output_dimensionality)
    normalized_task_type = str(task_type).strip() or DEFAULT_GEMINI_TASK_TYPE
    normalized_rerank_model = str(rerank_model).strip() or DEFAULT_GEMINI_RERANK_MODEL
    normalized_model_pool = _normalize_model_pool(model_pool, normalized_rerank_model)

    env_updates: dict[str, str] = {}
    normalized_api_key = str(api_key).strip()
    if normalized_api_key:
        env_updates["GEMINI_API_KEY"] = normalized_api_key
    env_updates.update(
        {
            "REPOBRAIN_GEMINI_EMBEDDING_MODEL": normalized_embedding_model,
            "REPOBRAIN_GEMINI_OUTPUT_DIMENSIONALITY": str(normalized_output_dimensionality),
            "REPOBRAIN_GEMINI_TASK_TYPE": normalized_task_type,
            "REPOBRAIN_GEMINI_RERANK_MODEL": normalized_rerank_model,
            "GEMINI_MODELS": ",".join(normalized_model_pool),
        }
    )
    env_path = write_env_values(root, env_updates)

    config = RepoBrainConfig.load(root)
    config.providers.embedding = "gemini" if use_embedding else "local"
    config.providers.reranker = "gemini" if use_reranker else "local"
    config.providers.options.update(
        {
            "gemini_embedding_model": normalized_embedding_model,
            "gemini_output_dimensionality": normalized_output_dimensionality,
            "gemini_task_type": normalized_task_type,
            "gemini_rerank_model": normalized_rerank_model,
            "gemini_models": normalized_model_pool,
        }
    )
    config_path = config.write_default(force=True)
    write_active_repo(root)

    return {
        "kind": "gemini_config",
        "repo_root": str(root),
        "config_path": str(config_path),
        "env_path": str(env_path),
        "api_key_saved": bool(normalized_api_key),
        "embedding": config.providers.embedding,
        "reranker": config.providers.reranker,
        "gemini_embedding_model": normalized_embedding_model,
        "gemini_output_dimensionality": normalized_output_dimensionality,
        "gemini_task_type": normalized_task_type,
        "gemini_rerank_model": normalized_rerank_model,
        "gemini_models": normalized_model_pool,
        "env_keys": sorted(key for key in env_updates if key in GEMINI_ENV_KEYS),
    }


def configure_groq_provider(
    repo_root: str | Path,
    *,
    api_key: str = "",
    use_reranker: bool = True,
    rerank_model: str = DEFAULT_GROQ_RERANK_MODEL,
    model_pool: str | Iterable[str] | None = None,
) -> dict[str, object]:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("Project path does not exist or is not a directory.")

    normalized_rerank_model = str(rerank_model).strip() or DEFAULT_GROQ_RERANK_MODEL
    normalized_model_pool = _normalize_model_pool(model_pool, normalized_rerank_model)

    env_updates: dict[str, str] = {}
    normalized_api_key = str(api_key).strip()
    if normalized_api_key:
        env_updates["GROQ_API_KEY"] = normalized_api_key
    env_updates.update(
        {
            "REPOBRAIN_GROQ_RERANK_MODEL": normalized_rerank_model,
            "GROQ_MODELS": ",".join(normalized_model_pool),
        }
    )
    env_path = write_env_values(root, env_updates)

    config = RepoBrainConfig.load(root)
    # Groq currently backs reranking/scoring only. Keep embeddings local so a
    # single Groq API key is enough for a working remote-rerank setup.
    config.providers.embedding = "local"
    config.providers.reranker = "groq" if use_reranker else "local"
    config.providers.options.update(
        {
            "groq_rerank_model": normalized_rerank_model,
            "groq_models": normalized_model_pool,
        }
    )
    config_path = config.write_default(force=True)
    write_active_repo(root)

    return {
        "kind": "groq_config",
        "repo_root": str(root),
        "config_path": str(config_path),
        "env_path": str(env_path),
        "api_key_saved": bool(normalized_api_key),
        "embedding": config.providers.embedding,
        "reranker": config.providers.reranker,
        "groq_rerank_model": normalized_rerank_model,
        "groq_models": normalized_model_pool,
        "env_keys": sorted(key for key in env_updates if key in GROQ_ENV_KEYS),
    }


def gemini_config_result_to_text(payload: dict[str, object]) -> str:
    models = payload.get("gemini_models", [])
    model_text = ", ".join(str(item) for item in models) if isinstance(models, list) and models else "single model"
    api_key_text = "saved" if payload.get("api_key_saved") else "unchanged"
    return "\n".join(
        [
            "RepoBrain Gemini Config",
            f"Repo: {payload.get('repo_root')}",
            f"Config: {payload.get('config_path')}",
            f"Env: {payload.get('env_path')}",
            f"API key: {api_key_text}",
            f"Embedding: {payload.get('embedding')}",
            f"Reranker: {payload.get('reranker')}",
            f"Rerank model: {payload.get('gemini_rerank_model')}",
            f"Model pool: {model_text}",
            "",
            "Next: run Doctor or Provider Smoke to verify provider readiness.",
        ]
    )


def groq_config_result_to_text(payload: dict[str, object]) -> str:
    models = payload.get("groq_models", [])
    model_text = ", ".join(str(item) for item in models) if isinstance(models, list) and models else "single model"
    api_key_text = "saved" if payload.get("api_key_saved") else "unchanged"
    return "\n".join(
        [
            "RepoBrain Groq Config",
            f"Repo: {payload.get('repo_root')}",
            f"Config: {payload.get('config_path')}",
            f"Env: {payload.get('env_path')}",
            f"API key: {api_key_text}",
            f"Embedding: {payload.get('embedding')}",
            f"Reranker: {payload.get('reranker')}",
            f"Rerank model: {payload.get('groq_rerank_model')}",
            f"Model pool: {model_text}",
            "",
            "Next: run Doctor or Provider Smoke to verify provider readiness.",
        ]
    )
