from __future__ import annotations

from pathlib import Path

from repobrain.cleanup import cleanup_demo_artifacts


def test_cleanup_demo_artifacts_removes_temp_outputs_and_preserves_runtime_assets(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    root_state = project_root / ".repobrain"
    build_dist = project_root / "dist"
    pytest_dir = project_root / "pytest_work_manual_001"
    random_tmp = project_root / "tmpabc123"
    nested_cache = project_root / "smoke_workspace" / "sample_repo" / "__pycache__"
    nested_state = project_root / "smoke_workspace" / "sample_repo" / ".repobrain"
    web_dist = project_root / "webapp" / "dist"

    for directory in (root_state, build_dist, pytest_dir, random_tmp, nested_cache, nested_state, web_dist):
        directory.mkdir(parents=True, exist_ok=True)
    (root_state / "keep.json").write_text("{}", encoding="utf-8")
    (build_dist / "artifact.whl").write_text("wheel", encoding="utf-8")
    (pytest_dir / "data.txt").write_text("tmp", encoding="utf-8")
    (random_tmp / "leftover.txt").write_text("tmp", encoding="utf-8")
    (nested_cache / "module.pyc").write_text("pyc", encoding="utf-8")
    (nested_state / "metadata.db").write_text("db", encoding="utf-8")
    (web_dist / "index.html").write_text("<html></html>", encoding="utf-8")

    payload = cleanup_demo_artifacts(project_root)

    assert payload["status"] == "pass"
    assert not build_dist.exists()
    assert not pytest_dir.exists()
    assert not random_tmp.exists()
    assert not nested_cache.exists()
    assert not nested_state.exists()
    assert root_state.exists()
    assert web_dist.exists()
    assert any(item["path"].endswith(".repobrain") for item in payload["preserved"] if isinstance(item, dict))


def test_cleanup_demo_artifacts_dry_run_keeps_files_in_place(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    build_dist = project_root / "dist"
    build_dist.mkdir(parents=True, exist_ok=True)
    (build_dist / "artifact.whl").write_text("wheel", encoding="utf-8")

    payload = cleanup_demo_artifacts(project_root, dry_run=True)

    assert payload["status"] == "pass"
    assert build_dist.exists()
    assert payload["removed_count"] == 1
    assert str(build_dist.resolve()) in payload["removed"]
