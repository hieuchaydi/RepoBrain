from __future__ import annotations

from repobrain.engine.provider_base import (
    _clamp_score,
    _coerce_embedding,
    _exc_text,
    _env_or_option,
    _env_or_option_int,
    _env_or_option_list,
    _is_quota_or_rate_limit_error,
    _merge_primary_model,
    _ordered_unique,
    _parse_score,
    _read_value,
    _sdk_available,
    _split_csv,
    RemoteProviderError,
    cosine_similarity,
    tokenize,
)


def test_tokenize_and_similarity_behave_deterministically() -> None:
    assert tokenize("Auth callback: LoginHandler_v2") == ["auth", "callback", "loginhandler_v2"]
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([], [1.0]) == 0.0


def test_score_helpers_clamp_and_parse() -> None:
    assert _clamp_score(-0.4) == 0.0
    assert _clamp_score(1.3) == 1.0
    assert _parse_score("score=0.87") == 0.87
    assert _parse_score("no score here") == 0.0
    assert _parse_score("1.4") == 1.0


def test_option_helpers_read_env_and_options(monkeypatch) -> None:
    monkeypatch.setenv("REPOBRAIN_MODELS", "m1,m2")
    monkeypatch.setenv("REPOBRAIN_DIM", "768")

    assert _split_csv("a, b, ,c") == ["a", "b", "c"]
    assert _ordered_unique(["a", "b", "a"]) == ["a", "b"]
    assert _merge_primary_model("main", ["fallback", "main"]) == ["main", "fallback"]

    assert _env_or_option({}, "model", "REPOBRAIN_MODEL", "local") == "local"
    assert _env_or_option({"model": "remote"}, "model", "REPOBRAIN_MODEL", "local") == "remote"
    assert _env_or_option_list({}, "models", "REPOBRAIN_MODELS") == ["m1", "m2"]
    assert _env_or_option_list({"models": "one,two"}, "models", "REPOBRAIN_MODELS") == ["one", "two"]
    assert _env_or_option_list({"models": ["x", "y"]}, "models", "REPOBRAIN_MODELS") == ["x", "y"]
    assert _env_or_option_list({}, "models", "REPOBRAIN_NOT_SET") == []
    assert _env_or_option_int({}, "dim", "REPOBRAIN_DIM", 32) == 768
    assert _env_or_option_int({"dim": "256"}, "dim", "REPOBRAIN_DIM", 32) == 256


def test_embedding_and_rate_limit_helpers() -> None:
    assert _coerce_embedding({"embedding": [1, 2, 3]}) == [1.0, 2.0, 3.0]
    assert _coerce_embedding({"values": [0, 5]}) == [0.0, 5.0]
    assert _is_quota_or_rate_limit_error(RuntimeError("429 too many requests"))
    assert not _is_quota_or_rate_limit_error(RuntimeError("unexpected parse error"))


def test_read_value_and_exc_text_helpers() -> None:
    class Holder:
        value = "from-attr"

    assert _read_value({"value": "from-dict"}, "value") == "from-dict"
    assert _read_value(Holder(), "value") == "from-attr"
    assert _read_value(Holder(), "missing", "fallback") == "fallback"
    assert _exc_text(RuntimeError("  quota   exceeded   ")) == "quota exceeded"


def test_embedding_error_and_sdk_detection() -> None:
    try:
        _coerce_embedding({"unexpected": [1, 2]})
        raise AssertionError("Expected _coerce_embedding to raise for invalid payload")
    except RemoteProviderError:
        pass

    assert _sdk_available("json")
    assert not _sdk_available("repobrain_this_module_does_not_exist")
