from __future__ import annotations

from repobrain.models import (
    Chunk,
    Edge,
    EditTarget,
    FileEvidence,
    ParsedDocument,
    PatchReviewChange,
    PatchReviewReport,
    QueryIntent,
    QueryPlan,
    QueryResult,
    ReadinessCheck,
    ReviewDelta,
    ReviewFinding,
    ReviewFocus,
    ReviewReport,
    ReviewSeverity,
    SearchHit,
    ShipReport,
    Symbol,
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


def test_review_and_ship_payloads_include_nested_contracts() -> None:
    delta = ReviewDelta(
        baseline_label="baseline",
        baseline_saved_at="2026-04-20T10:00:00Z",
        status="improved",
        baseline_score=6.04,
        current_score=7.26,
        score_delta=1.22,
        baseline_readiness="needs_hardening",
        current_readiness="promising",
        new_findings=["new warning"],
        resolved_findings=["old warning"],
    )
    finding = ReviewFinding(
        severity=ReviewSeverity.HIGH,
        category="security",
        title="Missing auth guard",
        summary="Write endpoint appears unguarded",
        file_paths=["src/api/auth.py"],
        recommendation="Add middleware",
    )
    report = ReviewReport(
        repo_root="C:/repo",
        focus=ReviewFocus.FULL,
        readiness="needs_hardening",
        score=7.04,
        summary="Needs hardening.",
        findings=[finding],
        next_steps=["Protect write routes"],
        stats={"indexed": True},
        category_counts={"security": 1},
        severity_counts={"high": 1},
        delta=delta,
    )
    ship = ShipReport(
        repo_root="C:/repo",
        status="warn",
        score=7.49,
        summary="Ship with caution.",
        checks=[ReadinessCheck(name="review", status="warn", summary="Needs hardening")],
        blockers=["coverage below target"],
        highlights=["local mode is healthy"],
        next_steps=["add tests"],
        doctor={"indexed": True},
        review=report,
        benchmark={"recall_at_3": 0.66},
        history={"trend": "up"},
    )

    delta_payload = delta.to_dict()
    report_payload = report.to_dict()
    ship_payload = ship.to_dict()

    assert delta_payload["baseline_score"] == 6.0
    assert delta_payload["current_score"] == 7.3
    assert report_payload["focus"] == "full"
    assert report_payload["findings"][0]["severity"] == "high"
    assert ship_payload["score"] == 7.5
    assert ship_payload["checks"][0]["name"] == "review"
    assert ship_payload["review"]["delta"]["status"] == "improved"


def test_document_shapes_and_simple_contracts() -> None:
    symbol = Symbol(name="auth_callback", kind="function", start_line=4, end_line=19, signature="def auth_callback()")
    chunk = Chunk(
        file_path="src/auth.py",
        language="python",
        role="route",
        start_line=4,
        end_line=19,
        content="def auth_callback(): pass",
        search_text="auth callback",
    )
    edge = Edge(source_file="src/auth.py", source_symbol="auth_callback", target="exchange_token", edge_type="calls")
    parsed = ParsedDocument(
        file_path="src/auth.py",
        language="python",
        role="route",
        content="def auth_callback(): pass",
        symbols=[symbol],
        imports=["service.exchange_token"],
        edges=[edge],
        chunks=[chunk],
        hints=["provider:github"],
    )

    assert symbol.kind == "function"
    assert chunk.role == "route"
    assert edge.edge_type == "calls"
    assert parsed.parser_name == "heuristic"
    assert parsed.symbols[0].name == "auth_callback"
