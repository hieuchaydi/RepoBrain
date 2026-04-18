from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from repobrain.engine.core import RepoBrainEngine
from repobrain.mcp_server import RepoBrainMCPServer


def test_mcp_server_rejects_missing_query(mixed_repo) -> None:
    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    with pytest.raises(ValueError):
        server._validate_tool_call("search_codebase", {})


def test_mcp_server_rejects_unknown_tool(mixed_repo) -> None:
    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    with pytest.raises(ValueError):
        server._validate_tool_call("unknown_tool", {})


def test_mcp_server_accepts_review_focus(mixed_repo) -> None:
    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    payload = server._validate_tool_call("review_codebase", {"focus": "security"})

    assert payload == {"focus": "security"}


def test_mcp_server_accepts_ship_baseline_label(mixed_repo) -> None:
    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    payload = server._validate_tool_call("assess_ship_readiness", {"baseline_label": "release-1"})

    assert payload == {"baseline_label": "release-1"}


def test_mcp_server_exposes_workspace_tools(mixed_repo) -> None:
    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    tool_names = {tool["name"] for tool in server.list_tools()}

    assert "list_workspace_projects" in tool_names
    assert "switch_workspace_project" in tool_names
    assert "remember_repo_note" in tool_names
    assert "search_workspace" in tool_names


def test_mcp_server_can_track_switch_and_remember_workspace_repo(mixed_repo: Path, tmp_path: Path) -> None:
    second_repo = tmp_path / "sample_repo_two"
    shutil.copytree(mixed_repo, second_repo)

    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    tracked = server.tools["track_workspace_project"].handler({"repo": str(mixed_repo), "activate": True})
    assert tracked["current_repo"] == str(mixed_repo.resolve())

    tracked_second = server.tools["track_workspace_project"].handler({"repo": str(second_repo), "activate": False})
    assert tracked_second["project_count"] >= 2

    switched = server.tools["switch_workspace_project"].handler({"project": str(second_repo)})
    assert switched["current_repo"] == str(second_repo.resolve())
    assert server.engine.config.resolved_repo_root == second_repo.resolve()

    summary = server.tools["remember_repo_note"].handler({"note": "auth callback is the long-term thread"})
    assert summary["repo_root"] == str(second_repo.resolve())
    assert "auth callback is the long-term thread" in summary["manual_notes"]


def test_mcp_workspace_search_returns_structured_comparison(mixed_repo: Path, tmp_path: Path) -> None:
    second_repo = tmp_path / "sample_repo_two"
    shutil.copytree(mixed_repo, second_repo)

    engine = RepoBrainEngine(mixed_repo)
    server = RepoBrainMCPServer(engine)

    server.tools["track_workspace_project"].handler({"repo": str(mixed_repo), "activate": True})
    server.tools["track_workspace_project"].handler({"repo": str(second_repo), "activate": False})

    payload = server.tools["search_workspace"].handler({"query": "auth callback"})

    assert payload["kind"] == "workspace_query"
    assert payload["comparison"]["best_match"]["name"] in {"sample_repo", "sample_repo_two"}
    assert isinstance(payload["comparison"]["global_evidence"], list)
    assert "shared_hotspots" in payload["comparison"]
    assert "global_rank" in payload["results"][0]
    assert isinstance(payload["results"][0]["citations"], list)
