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


def test_build_prompt_pack_from_flow_emits_contract_and_type_prompts() -> None:
    payload = {
        "kind": "flow_assessment",
        "flow_query": "login callback",
        "summary": "Flow audit found weak boundaries in callback handling.",
        "entry_files": ["src/api/auth.py", "src/service/auth_service.py"],
        "edit_targets": ["src/service/token_service.py"],
        "flow_edges": ["src/api/auth.py::login --calls--> src/service/auth_service.py"],
        "input_contracts": ["src/api/auth.py:10-40 -> request payload includes oauth code"],
        "output_contracts": ["src/service/auth_service.py:42-90 -> returns token payload + error object"],
        "type_risks": ["src/service/auth_service.py:42-90 -> Dynamic `any` typing found on a flow boundary."],
        "bottlenecks": ["Trace confidence is weak; flow grounding is still weak."],
        "warnings": ["Evidence is concentrated in one file. Cross-check nearby routes, services, and config."],
        "next_steps": ["Define request schema before token exchange logic."],
    }

    report = build_prompt_pack(
        source="flow",
        repo_root="C:/repo",
        payload=payload,
        style="codex",
        max_prompts=3,
    )

    titles = [item["title"] for item in report["prompts"]]
    assert report["source"] == "flow"
    assert report["count"] == 3
    assert any("Flow contract audit" in title for title in titles)
    assert any("type mismatch" in title.lower() for title in titles)


def test_build_prompt_pack_from_flow_filters_files_by_score_threshold() -> None:
    payload = {
        "kind": "flow_assessment",
        "flow_query": "login callback",
        "summary": "Flow score-based prompt routing",
        "score_threshold": 0.7,
        "file_scores": [
            {"file_path": "src/api/auth.py", "score": 0.82, "role": "route", "sources": ["trace"], "reasons": ["Strong multi-source evidence."]},
            {"file_path": "src/service/auth_service.py", "score": 0.58, "role": "service", "sources": ["trace", "impact"], "reasons": ["Weak contract consistency."]},
            {"file_path": "src/service/token_service.py", "score": 0.41, "role": "service", "sources": ["targets"], "reasons": ["Low confidence edit target."]},
        ],
        "entry_files": ["src/api/auth.py"],
        "edit_targets": ["src/service/auth_service.py", "src/service/token_service.py"],
    }

    report = build_prompt_pack(
        source="flow",
        repo_root="C:/repo",
        payload=payload,
        style="codex",
        max_prompts=5,
    )

    titles = [item["title"] for item in report["prompts"]]
    assert report["source"] == "flow"
    assert report["count"] == 2
    assert any("src/service/auth_service.py" in title for title in titles)
    assert any("src/service/token_service.py" in title for title in titles)
    assert not any("src/api/auth.py" in title for title in titles)
