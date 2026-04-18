from __future__ import annotations

import shutil
from pathlib import Path

from repobrain.models import FileEvidence, QueryIntent, QueryPlan, QueryResult, SearchHit
from repobrain.workspace import add_workspace_project, workspace_query_payload


class _FakeStore:
    def indexed(self) -> bool:
        return True


class _FakeEngine:
    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = _FakeStore()

    def query(self, query: str, context: str | None = None) -> QueryResult:
        if self.repo_root.name == "sample_repo_two":
            confidence = 0.73
            snippet_score = 0.94
        else:
            confidence = 0.91
            snippet_score = 0.52
        file_stub = f"{self.repo_root.name}/backend/auth_service.py"
        return QueryResult(
            query=query,
            intent=QueryIntent.LOCATE,
            top_files=[
                FileEvidence(
                    file_path=file_stub,
                    language="python",
                    role="service",
                    score=confidence,
                    reasons=["role_match", "path_overlap"],
                )
            ],
            snippets=[
                SearchHit(
                    chunk_id=1,
                    file_path=file_stub,
                    language="python",
                    role="service",
                    symbol_name="handle_callback",
                    start_line=12,
                    end_line=24,
                    content="def handle_callback(...): return finalize_auth()",
                    score=snippet_score,
                    reasons=["vector", "path_overlap"],
                )
            ],
            call_chain=[],
            dependency_edges=[],
            edit_targets=[],
            confidence=confidence,
            warnings=[],
            next_questions=[],
            plan=QueryPlan(intent=QueryIntent.LOCATE, steps=["planner"], rewritten_queries=[query]),
        )


def test_workspace_query_ranks_repos_by_global_citation_evidence(mixed_repo: Path, tmp_path: Path) -> None:
    second_repo = tmp_path / "sample_repo_two"
    shutil.copytree(mixed_repo, second_repo)

    add_workspace_project(mixed_repo, make_current=True)
    add_workspace_project(second_repo, make_current=False)

    payload = workspace_query_payload(
        "auth callback",
        current_repo=mixed_repo,
        context="Focus: callback handling",
        engine_factory=_FakeEngine,
    )

    assert payload["kind"] == "workspace_query"
    assert payload["context_applied"] is True
    assert payload["results"][0]["name"] == "sample_repo_two"
    assert payload["results"][0]["global_rank"] == 1
    assert payload["results"][0]["evidence_score"] == 0.94
    assert payload["results"][1]["name"] == "sample_repo"
    assert payload["comparison"]["best_match"]["name"] == "sample_repo_two"
    assert payload["comparison"]["best_match"]["global_rank"] == 1
    assert payload["comparison"]["global_evidence"][0]["name"] == "sample_repo_two"
    assert payload["comparison"]["global_evidence"][0]["score"] == 0.94
