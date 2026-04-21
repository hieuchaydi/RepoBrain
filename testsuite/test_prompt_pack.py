from __future__ import annotations

import pytest

from repobrain.prompt_pack import build_prompt_pack


def test_build_prompt_pack_from_review_respects_limit() -> None:
    payload = {
        "summary": "Review surfaced critical risks.",
        "findings": [
            {
                "severity": "high",
                "category": "security",
                "title": "Missing auth guard",
                "summary": "Write endpoint is reachable without an auth check.",
                "recommendation": "Add middleware-level auth guard.",
                "file_paths": ["src/api/auth.py"],
            },
            {
                "severity": "low",
                "category": "quality",
                "title": "Duplicate branch logic",
                "summary": "Two branches repeat the same condition chain.",
                "recommendation": "Extract helper for shared branch logic.",
                "file_paths": ["src/service/auth_service.py"],
            },
        ],
    }

    report = build_prompt_pack(
        source="review",
        repo_root="C:/repo",
        payload=payload,
        style="codex",
        max_prompts=1,
    )

    assert report["kind"] == "prompt_pack"
    assert report["source"] == "review"
    assert report["style"] == "codex"
    assert report["count"] == 1
    first = report["prompts"][0]
    assert "Missing auth guard" in first["title"]
    assert "prompt_text" in first


def test_build_prompt_pack_from_patch_review_emits_multiple_prompt_types() -> None:
    payload = {
        "summary": "Patch touches auth callback wiring.",
        "mode": "working_tree",
        "risk_label": "high",
        "risk_score": 0.72,
        "changed_files": [{"file_path": "src/api/auth.py"}],
        "suggested_tests": [{"file_path": "tests/test_auth.py"}],
        "config_surfaces": [{"file_path": "repobrain.toml"}],
        "warnings": ["Auth callback path changed without explicit regression test coverage."],
    }

    report = build_prompt_pack(
        source="patch-review",
        repo_root="C:/repo",
        payload=payload,
        style="generic",
        max_prompts=3,
    )

    assert report["count"] == 3
    titles = [item["title"] for item in report["prompts"]]
    assert any("Reduce patch risk" in title for title in titles)
    assert any("regression test gaps" in title.lower() for title in titles)
    assert any("config touchpoints" in title.lower() for title in titles)


def test_build_prompt_pack_rejects_invalid_source_or_style() -> None:
    with pytest.raises(ValueError):
        build_prompt_pack(source="unknown", repo_root="C:/repo", payload={})

    with pytest.raises(ValueError):
        build_prompt_pack(source="review", repo_root="C:/repo", payload={}, style="invalid")
