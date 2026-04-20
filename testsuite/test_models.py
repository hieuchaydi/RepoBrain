from __future__ import annotations

from repobrain.models import (
    EditTarget,
    FileEvidence,
    PatchReviewChange,
    PatchReviewReport,
    QueryIntent,
    QueryPlan,
    QueryResult,
    SearchHit,
)


def test_query_result_to_dict_preserves_contract_shape() -> None:
    result = QueryResult(
        query="Where is auth callback handling?",
        intent=QueryIntent.TRACE,
        top_files=[FileEvidence(file_path="src/auth.py", language="python", role="route", score=2.71828, reasons=["bm25"])],
        snippets=[
            SearchHit(
                chunk_id=1,
                file_path="src/auth.py",
                language="python",
                role="route",
                symbol_name="auth_callback",
                start_line=10,
                end_line=24,
                content="def auth_callback(...): pass",
                score=1.61803,
                reasons=["bm25", "reranked"],
            )
        ],
        call_chain=["src/auth.py::auth_callback --calls--> src/service.py::exchange_token"],
        dependency_edges=[{"source_file": "src/auth.py", "target": "exchange_token", "edge_type": "calls"}],
        edit_targets=[EditTarget(file_path="src/auth.py", score=3.14159, rationale="entrypoint")],
        confidence=0.9348,
        warnings=[],
        next_questions=[],
        plan=QueryPlan(intent=QueryIntent.TRACE, steps=["planner", "retriever"], rewritten_queries=["auth callback flow"]),
        confidence_label="strong",
        confidence_summary="Strong grounding.",
    )

    payload = result.to_dict()
    assert payload["intent"] == "trace"
    assert payload["confidence"] == 0.935
    assert payload["plan"]["intent"] == "trace"
    assert payload["top_files"][0]["file_path"] == "src/auth.py"
    assert payload["snippets"][0]["symbol_name"] == "auth_callback"
    assert payload["edit_targets"][0]["rationale"] == "entrypoint"


def test_patch_review_report_to_dict_includes_kind_and_risk_rounding() -> None:
    report = PatchReviewReport(
        repo_root="C:/repo",
        mode="working_tree",
        base_ref=None,
        changed_files=[
            PatchReviewChange(
                file_path="src/auth.py",
                status="modified",
                exists=True,
                supported=True,
                language="python",
                role="route",
                symbols=["auth_callback"],
            )
        ],
        risk_score=0.6666,
        risk_label="high",
        summary="High risk patch.",
    )

    payload = report.to_dict()
    assert payload["kind"] == "patch_review"
    assert payload["risk_score"] == 0.667
    assert payload["changed_files"][0]["status"] == "modified"
