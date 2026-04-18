from __future__ import annotations

import os

from repobrain.config import RepoBrainConfig, load_env_file


def test_load_env_file_reads_values_without_overriding_existing_env(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODELS", raising=False)
    monkeypatch.delenv("REPOBRAIN_GEMINI_RERANK_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# RepoBrain local secrets",
                "GEMINI_API_KEY=from-file",
                "GEMINI_MODELS=gemini-2.5-flash,gemini-3-flash-preview",
                "export REPOBRAIN_GEMINI_RERANK_MODEL='gemini-3-flash-preview'",
                'EXISTING_VALUE="from-env-file"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING_VALUE", "already-set")

    loaded = load_env_file(tmp_path)

    assert loaded == env_file
    assert os.environ["GEMINI_API_KEY"] == "from-file"
    assert os.environ["GEMINI_MODELS"] == "gemini-2.5-flash,gemini-3-flash-preview"
    assert os.environ["REPOBRAIN_GEMINI_RERANK_MODEL"] == "gemini-3-flash-preview"
    assert os.environ["EXISTING_VALUE"] == "already-set"


def test_config_load_reads_repo_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GEMINI_API_KEY=loaded-by-config\n", encoding="utf-8")

    RepoBrainConfig.load(tmp_path)

    assert os.environ["GEMINI_API_KEY"] == "loaded-by-config"
