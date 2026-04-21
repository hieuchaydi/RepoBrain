from __future__ import annotations

import importlib.util
import math
import os
import re
from collections.abc import Iterable
from typing import Protocol


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
    if isinstance(embedding, (str, bytes, bytearray)) or not isinstance(embedding, Iterable):
        raise RemoteProviderError("Remote embedding response included a non-iterable embedding vector.")

    try:
        return [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise RemoteProviderError("Remote embedding response included non-numeric embedding values.") from exc


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
    if isinstance(value, int):
        return value
    return int(str(value).strip())


def _clamp_score(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _parse_score(text: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return round(_clamp_score(float(match.group(0))), 6)


def _exc_text(exc: Exception) -> str:
    return " ".join(str(exc).split()).strip()


def _is_quota_or_rate_limit_error(exc: Exception) -> bool:
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


def _sdk_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False
