from __future__ import annotations

import os
import subprocess
import shutil
import uuid
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"
_TMPDIR_CLEANUP_PATCHED = False


def pytest_configure(config: pytest.Config) -> None:
    _patch_pytest_tmpdir_cleanup()
    if getattr(config.option, "basetemp", None) is not None:
        return
    config.option.basetemp = str(Path.cwd() / f"pytest_work_run_{os.getpid()}_{uuid.uuid4().hex[:8]}")


def _patch_pytest_tmpdir_cleanup() -> None:
    global _TMPDIR_CLEANUP_PATCHED
    if _TMPDIR_CLEANUP_PATCHED:
        return
    try:
        import _pytest.tmpdir as pytest_tmpdir
    except ImportError:
        return

    original_cleanup = pytest_tmpdir.cleanup_dead_symlinks

    def safe_cleanup_dead_symlinks(root: Path) -> None:
        try:
            original_cleanup(root)
        except PermissionError:
            return

    pytest_tmpdir.cleanup_dead_symlinks = safe_cleanup_dead_symlinks
    _TMPDIR_CLEANUP_PATCHED = True


def _copy_fixture(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def _git_run(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


@pytest.fixture()
def mixed_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "sample_repo"
    repo_root.mkdir()
    _copy_fixture(FIXTURES / "python_service", repo_root / "backend")
    _copy_fixture(FIXTURES / "ts_app", repo_root / "frontend")
    return repo_root


@pytest.fixture()
def patch_review_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "patch_review_repo"
    (repo_root / "backend" / "app" / "api").mkdir(parents=True)
    (repo_root / "backend" / "app" / "services").mkdir(parents=True)
    (repo_root / "backend" / "app" / "config").mkdir(parents=True)
    (repo_root / "backend" / "tests").mkdir(parents=True)

    (repo_root / ".gitignore").write_text(".repobrain/\n__pycache__/\n", encoding="utf-8")
    (repo_root / "backend" / "app" / "api" / "auth.py").write_text(
        "from backend.app.config.settings import CALLBACK_URL, load_auth_settings\n"
        "from backend.app.services.auth_service import AuthService\n\n"
        "router = {'prefix': '/auth'}\n\n"
        "async def auth_callback(code: str) -> dict[str, object]:\n"
        "    settings = load_auth_settings()\n"
        "    service = AuthService()\n"
        "    return await service.handle_google_callback(code, CALLBACK_URL, settings)\n",
        encoding="utf-8",
    )
    (repo_root / "backend" / "app" / "services" / "auth_service.py").write_text(
        "class AuthService:\n"
        "    async def handle_google_callback(self, code: str, callback_url: str, settings: dict[str, str]) -> dict[str, object]:\n"
        "        return {'code': code, 'callback_url': callback_url, 'provider': settings['provider']}\n",
        encoding="utf-8",
    )
    (repo_root / "backend" / "app" / "config" / "settings.py").write_text(
        "CALLBACK_URL = 'https://example.test/callback'\n\n"
        "def load_auth_settings() -> dict[str, str]:\n"
        "    return {'provider': 'google', 'callback_url': CALLBACK_URL}\n",
        encoding="utf-8",
    )
    (repo_root / "backend" / "tests" / "test_auth_flow.py").write_text(
        "from backend.app.api.auth import auth_callback\n\n"
        "def test_auth_callback_smoke() -> None:\n"
        "    assert auth_callback\n",
        encoding="utf-8",
    )

    _git_run(repo_root, "init")
    _git_run(repo_root, "checkout", "-b", "main")
    _git_run(repo_root, "config", "user.email", "repobrain-tests@example.com")
    _git_run(repo_root, "config", "user.name", "RepoBrain Tests")
    _git_run(repo_root, "add", ".")
    _git_run(repo_root, "commit", "-m", "test fixture")
    return repo_root


@pytest.fixture(autouse=True)
def isolate_active_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPOBRAIN_ACTIVE_REPO_FILE", str(tmp_path / "active_repo.txt"))
    monkeypatch.setenv("REPOBRAIN_WORKSPACE_STATE_FILE", str(tmp_path / "workspace.json"))
    for name in (
        "GEMINI_API_KEY",
        "GEMINI_MODELS",
        "REPOBRAIN_GEMINI_EMBEDDING_MODEL",
        "REPOBRAIN_GEMINI_OUTPUT_DIMENSIONALITY",
        "REPOBRAIN_GEMINI_RERANK_MODEL",
        "REPOBRAIN_GEMINI_TASK_TYPE",
        "OPENAI_API_KEY",
        "REPOBRAIN_OPENAI_EMBEDDING_MODEL",
        "VOYAGE_API_KEY",
        "REPOBRAIN_VOYAGE_EMBEDDING_MODEL",
        "REPOBRAIN_VOYAGE_INPUT_TYPE",
        "COHERE_API_KEY",
        "REPOBRAIN_COHERE_RERANK_MODEL",
        "GROQ_API_KEY",
        "REPOBRAIN_GROQ_RERANK_MODEL",
        "GROQ_MODELS",
    ):
        monkeypatch.delenv(name, raising=False)
