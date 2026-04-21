from __future__ import annotations

from pathlib import Path

import repobrain.workspace as workspace


def _raise_os_error(_state: dict[str, object]) -> Path:
    raise OSError("read-only filesystem")


def test_remember_file_context_falls_back_when_workspace_state_is_read_only(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    monkeypatch.setenv(workspace.WORKSPACE_STATE_FILE_ENV, str(tmp_path / "workspace.json"))
    monkeypatch.setattr(workspace, "save_workspace_state", _raise_os_error)

    payload = workspace.remember_file_context(repo_root, files=["src/app.py"])

    assert payload["repo_root"] == str(repo_root.resolve())
    assert "src/app.py" in payload["top_files"]


def test_remember_workspace_note_reports_non_persisted_message(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    monkeypatch.setenv(workspace.WORKSPACE_STATE_FILE_ENV, str(tmp_path / "workspace.json"))
    monkeypatch.setattr(workspace, "save_workspace_state", _raise_os_error)
    monkeypatch.setattr(
        workspace,
        "load_workspace_state",
        lambda: {
            "version": 1,
            "current_repo": str(repo_root.resolve()),
            "projects": [
                {
                    "name": repo_root.name,
                    "repo_root": str(repo_root.resolve()),
                    "added_at": "",
                    "last_used_at": "",
                    "memory": {},
                }
            ],
        },
    )
    payload = workspace.remember_workspace_note("critical auth thread")

    assert payload["kind"] == "workspace_summary"
    assert "not persisted" in str(payload["message"]).lower()
