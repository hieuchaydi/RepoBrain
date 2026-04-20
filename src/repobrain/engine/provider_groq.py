from __future__ import annotations

import importlib
import json
import os

from repobrain.engine.provider_base import (
    RemoteProviderError,
    _clamp_score,
    _exc_text,
    _is_quota_or_rate_limit_error,
    _parse_score,
    _read_value,
)


def _is_groq_pool_failover_error(exc: Exception) -> bool:
    if _is_quota_or_rate_limit_error(exc):
        return True
    text = _exc_text(exc).lower()
    patterns = (
        "503",
        "service unavailable",
        "temporarily unavailable",
        "overloaded",
        "capacity",
        "try again later",
    )
    return any(pattern in text for pattern in patterns)


def _groq_client() -> object:
    if not os.getenv("GROQ_API_KEY"):
        raise RemoteProviderError("GROQ_API_KEY is required for the Groq reranker.")
    try:
        module = importlib.import_module("groq")
        client_factory = getattr(module, "Groq")
    except (ImportError, AttributeError) as exc:
        raise RemoteProviderError('Install provider extras with `python -m pip install -e ".[providers]"` to use Groq reranking.') from exc
    return client_factory(api_key=os.getenv("GROQ_API_KEY"))


def _groq_choice_content(response: object) -> str:
    choices = list(_read_value(response, "choices", []) or [])
    if not choices:
        raise RemoteProviderError("Groq rerank response did not include any choices.")
    message = _read_value(choices[0], "message")
    content = _read_value(message, "content", "") if message is not None else ""
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            value = _read_value(item, "text", _read_value(item, "content", ""))
            if value is not None:
                parts.append(str(value))
        return "".join(parts).strip()
    return str(content or "").strip()


def _parse_groq_score(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        raise RemoteProviderError("Groq rerank response was empty.")
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _parse_score(stripped)

    if isinstance(payload, int | float):
        return round(_clamp_score(float(payload)), 6)
    if not isinstance(payload, dict):
        raise RemoteProviderError("Groq rerank response JSON was not an object.")

    raw_score = payload.get("score", payload.get("relevance_score", payload.get("relevance")))
    nested_result = payload.get("result")
    if raw_score is None and isinstance(nested_result, dict):
        raw_score = nested_result.get("score", nested_result.get("relevance_score"))
    if raw_score is None:
        raise RemoteProviderError("Groq rerank response JSON did not include a `score` field.")
    return round(_clamp_score(float(raw_score)), 6)


class GroqReranker:
    name = "groq"

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict code-evidence reranker. "
                    "Return only valid JSON in the form {\"score\": number}. "
                    "The score must be between 0 and 1."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Score how relevant this code evidence is to the query.\n\n"
                    f"Query:\n{query}\n\nEvidence:\n{candidate_text[:4000]}"
                ),
            },
        ]
        failures: list[str] = []
        models_to_try = self.models[self._active_model_index :] + self.models[: self._active_model_index]

        for index, model_name in enumerate(models_to_try):
            try:
                response = client.chat.completions.create(  # type: ignore[attr-defined]
                    model=model_name,
                    messages=messages,
                    temperature=0,
                    response_format={"type": "json_object"},
                )
            except Exception as exc:  # pragma: no cover - depends on remote SDK/runtime behavior
                if _is_groq_pool_failover_error(exc):
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
                        "Groq rerank request hit quota/rate-limit/provider exhaustion across the configured model pool. "
                        f"Tried: {tried}. Details: {details}"
                    ) from exc
                raise RemoteProviderError(f"Groq rerank request failed with model `{model_name}`: {exc}") from exc

            self._active_model_index = self.models.index(model_name)
            self.model = model_name
            return _parse_groq_score(_groq_choice_content(response))

        raise RemoteProviderError("Groq rerank request failed before any configured model could return a score.")

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        self._client = _groq_client()
        return self._client
