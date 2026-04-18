from __future__ import annotations

import io
import json
from pathlib import Path

from repobrain.models import ReadinessCheck, ReviewFocus, ReviewReport, ShipReport
from repobrain.ux import _report_html
from repobrain.web import _action_result, _application, _doctor_result, _import_and_index, _review_result


def test_web_import_and_query_flow(mixed_repo: Path) -> None:
    repo_text, message, result = _import_and_index(str(mixed_repo))

    assert repo_text == str(mixed_repo.resolve())
    assert "Imported and indexed" in message
    assert "RepoBrain Index Complete" in result

    active_repo, title, query_result = _action_result("query", "Where is payment retry logic implemented?")
    assert active_repo == str(mixed_repo.resolve())
    assert title == "Query"
    assert "RepoBrain Result" in query_result

    doctor_repo, doctor_result = _doctor_result()
    assert doctor_repo == str(mixed_repo.resolve())
    assert "RepoBrain Doctor" in doctor_result
    assert "Provider models:" in doctor_result

    review_repo, review_result = _review_result()
    assert review_repo == str(mixed_repo.resolve())
    assert "RepoBrain Review" in review_result


def test_web_home_page_serves_react_shell(mixed_repo: Path) -> None:
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/",
                "wsgi.input": io.BytesIO(b""),
                "CONTENT_LENGTH": "0",
            },
            start_response,
        )
    ).decode("utf-8")

    assert status_headers["status"] == "200 OK"
    assert '<div id="root">' in body
    assert "Loading local interface" in body
    assert "/static/app.js" in body
    assert "/static/app.css" in body


def test_web_bootstrap_api_returns_active_repo(mixed_repo: Path) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/api/bootstrap",
                "wsgi.input": io.BytesIO(b""),
                "CONTENT_LENGTH": "0",
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["ok"] is True
    assert payload["active_repo"] == str(mixed_repo.resolve())
    assert "vi" in payload["locales"]


def test_web_review_api_renders_project_review_payload(mixed_repo: Path) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/review",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(b"{}"),
                "CONTENT_LENGTH": "2",
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Project Review"
    assert "RepoBrain Review" in payload["result"]


def test_web_doctor_api_renders_structured_doctor_payload(mixed_repo: Path) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/api/doctor",
                "wsgi.input": io.BytesIO(b""),
                "CONTENT_LENGTH": "0",
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Doctor"
    assert payload["data"]["indexed"] is True
    assert "reranker_model" in payload["data"]["providers"]


def test_web_ship_api_renders_ship_gate_payload(mixed_repo: Path) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/ship",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(b"{}"),
                "CONTENT_LENGTH": "2",
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Ship Readiness"
    assert "RepoBrain Ship Gate" in payload["result"]


def test_web_provider_smoke_api_renders_provider_smoke(mixed_repo: Path) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/provider-smoke",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(b"{}"),
                "CONTENT_LENGTH": "2",
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Provider Smoke"
    assert "RepoBrain Provider Smoke" in payload["result"]
    assert payload["data"]["embedding_smoke"]["status"] == "pass"
    assert "pool" in payload["data"]["reranker_smoke"]


def test_report_html_renders_provider_pool_details() -> None:
    doctor = {
        "indexed": True,
        "stats": {"files": 3, "chunks": 4, "symbols": 5, "edges": 6},
        "providers": {
            "embedding": "local-hash",
            "reranker": "gemini",
            "embedding_model": "n/a",
            "reranker_model": "gemini-3-flash-preview",
            "reranker_models": ["gemini-2.5-flash", "gemini-3-flash-preview"],
            "reranker_last_failover_error": "429 Resource exhausted",
        },
        "provider_status": {
            "embedding": {"active": "local", "ready": True, "requires_network": False, "warnings": []},
            "reranker": {"active": "gemini", "ready": True, "requires_network": True, "warnings": []},
        },
        "security": {"local_storage_only": True, "remote_providers_enabled": True},
        "capabilities": {"language_parsers": {}},
    }
    review = ReviewReport(
        repo_root="repo",
        focus=ReviewFocus.FULL,
        readiness="promising",
        score=8.1,
        summary="Looks good overall.",
    )
    ship = ShipReport(
        repo_root="repo",
        status="ready",
        score=8.4,
        summary="Ready with some caveats.",
        checks=[ReadinessCheck(name="providers", status="pass", summary="Provider posture looks healthy.")],
        doctor=doctor,
        review=review,
    )

    html = _report_html(doctor, review, ship)

    assert "Provider Posture" in html
    assert "Gemini fallback pool:" in html
    assert "gemini-2.5-flash, gemini-3-flash-preview" in html
    assert "429 Resource exhausted" in html
