from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import repobrain.web as web_module
from repobrain.config import RepoBrainConfig
from repobrain.models import ReadinessCheck, ReviewFocus, ReviewReport, ShipReport
from repobrain.ux import _report_html
from repobrain.web import (
    WEB_FRONTEND_DIR,
    _action_result,
    _application,
    _doctor_result,
    _frontend_asset_path,
    _import_and_index,
    _review_result,
)


def test_web_import_and_query_flow(mixed_repo: Path) -> None:
    repo_text, message, result = _import_and_index(str(mixed_repo))

    assert repo_text == str(mixed_repo.resolve())
    assert "Imported and indexed" in message
    assert "RepoBrain Index Complete" in result
    assert "RepoBrain Import Assessment" in result
    assert "Top opinion signals" in result

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
    assert (WEB_FRONTEND_DIR / "index.html").exists()
    assert (WEB_FRONTEND_DIR / "app.js").exists()
    assert (WEB_FRONTEND_DIR / "app.css").exists()

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
    assert "RepoBrain Control Room" in body
    assert "Booting local codebase memory" in body
    assert "/static/app.js" in body
    assert "/static/app.css" in body


def test_frontend_asset_path_supports_installed_wheel_layout(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "repo" / "webapp" / "dist"
    installed_dir = tmp_path / "site-packages" / "webapp" / "dist"
    installed_dir.mkdir(parents=True)
    expected = installed_dir / "index.html"
    expected.write_text("<div id='root'></div>", encoding="utf-8")

    monkeypatch.setattr(web_module, "WEB_FRONTEND_DIR", source_dir)
    monkeypatch.setattr(web_module, "_frontend_dir_candidates", lambda: (source_dir, installed_dir))

    assert _frontend_asset_path("index.html") == expected


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
    assert payload["workspace"]["current_repo"] == str(mixed_repo.resolve())
    assert payload["summary"]["repo_root"] == str(mixed_repo.resolve())


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
    assert "data" in payload


def test_web_import_api_returns_structured_import_assessment(mixed_repo: Path) -> None:
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    request = json.dumps({"repo_path": str(mixed_repo)}).encode("utf-8")
    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/import",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(request),
                "CONTENT_LENGTH": str(len(request)),
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Import + Index"
    assert payload["data"]["import_assessment"]["kind"] == "import_assessment"
    assert payload["data"]["review"]["summary"]
    assert "RepoBrain Import Assessment" in payload["result"]


def test_web_select_folder_api_returns_native_picker_path(tmp_path: Path, monkeypatch) -> None:
    selected = tmp_path / "selected_repo"
    selected.mkdir()
    monkeypatch.setattr(web_module, "_select_local_directory", lambda initial_dir="": selected.resolve())
    app = _application()
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    request = json.dumps({"initial_dir": str(tmp_path)}).encode("utf-8")
    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/select-folder",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(request),
                "CONTENT_LENGTH": str(len(request)),
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    assert status_headers["status"] == "200 OK"
    assert payload["ok"] is True
    assert payload["repo_path"] == str(selected.resolve())
    assert "Import + Index" in payload["message"]


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


def test_web_gemini_config_api_writes_env_and_provider_config(mixed_repo: Path, monkeypatch) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    request = json.dumps(
        {
            "api_key": "test-gemini-key",
            "model_pool": "gemini-2.5-flash,gemini-3-flash-preview",
            "use_embedding": True,
            "use_reranker": True,
        }
    ).encode("utf-8")
    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/providers/gemini",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(request),
                "CONTENT_LENGTH": str(len(request)),
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    config = RepoBrainConfig.load(mixed_repo)

    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Gemini Config"
    assert payload["data"]["kind"] == "gemini_config"
    assert payload["data"]["api_key_saved"] is True
    assert "test-gemini-key" not in payload["result"]
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GEMINI_API_KEY=test-gemini-key"
    assert config.providers.embedding == "gemini"
    assert config.providers.reranker == "gemini"
    assert config.providers.options["gemini_models"] == ["gemini-2.5-flash", "gemini-3-flash-preview"]
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_web_groq_config_api_writes_env_and_provider_config(mixed_repo: Path, monkeypatch) -> None:
    _import_and_index(str(mixed_repo))
    app = _application(default_repo=str(mixed_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    request = json.dumps(
        {
            "api_key": "test-groq-key",
            "model_pool": "llama-3.3-70b-versatile,openai/gpt-oss-20b",
            "use_reranker": True,
        }
    ).encode("utf-8")
    body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/providers/groq",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(request),
                "CONTENT_LENGTH": str(len(request)),
            },
            start_response,
        )
    ).decode("utf-8")

    payload = json.loads(body)
    config = RepoBrainConfig.load(mixed_repo)

    assert status_headers["status"] == "200 OK"
    assert payload["title"] == "Groq Config"
    assert payload["data"]["kind"] == "groq_config"
    assert payload["data"]["api_key_saved"] is True
    assert "test-groq-key" not in payload["result"]
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GROQ_API_KEY=test-groq-key"
    assert config.providers.embedding == "local"
    assert config.providers.reranker == "groq"
    assert config.providers.options["groq_models"] == ["llama-3.3-70b-versatile", "openai/gpt-oss-20b"]
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def test_web_patch_review_api_supports_working_tree_and_files_mode(patch_review_repo: Path) -> None:
    _import_and_index(str(patch_review_repo))
    route_path = patch_review_repo / "backend" / "app" / "api" / "auth.py"
    route_path.write_text(
        route_path.read_text(encoding="utf-8") + "\n\nasync def web_patch_review() -> None:\n    return None\n",
        encoding="utf-8",
    )

    app = _application(default_repo=str(patch_review_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    working_tree_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/patch-review",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(b"{}"),
                "CONTENT_LENGTH": "2",
            },
            start_response,
        )
    ).decode("utf-8")

    working_tree_payload = json.loads(working_tree_body)
    assert status_headers["status"] == "200 OK"
    assert working_tree_payload["title"] == "Patch Review"
    assert "RepoBrain Patch Review" in working_tree_payload["result"]
    assert "RepoBrain Auto-Attached Files" in working_tree_payload["result"]
    assert working_tree_payload["data"]["kind"] == "patch_review"
    assert working_tree_payload["file_context"]["files"]

    files_request = json.dumps({"files": ["backend/app/api/auth.py"]}).encode("utf-8")
    files_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/patch-review",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(files_request),
                "CONTENT_LENGTH": str(len(files_request)),
            },
            start_response,
        )
    ).decode("utf-8")

    files_payload = json.loads(files_body)
    assert status_headers["status"] == "200 OK"
    assert files_payload["data"]["changed_files"][0]["file_path"] == "backend/app/api/auth.py"
    assert "backend/app/api/auth.py" in files_payload["summary"]["top_files"]


def test_web_workspace_use_memory_and_multi_query_flow(mixed_repo: Path, tmp_path: Path) -> None:
    second_repo = tmp_path / "sample_repo_two"
    shutil.copytree(mixed_repo, second_repo)

    _import_and_index(str(mixed_repo))
    _import_and_index(str(second_repo))
    app = _application(default_repo=str(second_repo))
    status_headers: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        status_headers["status"] = status
        status_headers["headers"] = headers

    remember_request = json.dumps({"note": "auth callback is the main thread"}).encode("utf-8")
    remember_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/workspace/remember",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(remember_request),
                "CONTENT_LENGTH": str(len(remember_request)),
            },
            start_response,
        )
    ).decode("utf-8")
    remember_payload = json.loads(remember_body)
    assert status_headers["status"] == "200 OK"
    assert remember_payload["summary"]["manual_notes"] == ["auth callback is the main thread"]

    use_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/workspace/use",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(json.dumps({"project": str(mixed_repo)}).encode("utf-8")),
                "CONTENT_LENGTH": str(len(json.dumps({"project": str(mixed_repo)}).encode("utf-8"))),
            },
            start_response,
        )
    ).decode("utf-8")
    use_payload = json.loads(use_body)
    assert status_headers["status"] == "200 OK"
    assert use_payload["active_repo"] == str(mixed_repo.resolve())
    assert use_payload["workspace"]["current_repo"] == str(mixed_repo.resolve())

    multi_request = json.dumps({"mode": "multi", "query": "auth callback"}).encode("utf-8")
    multi_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/query",
                "CONTENT_TYPE": "application/json",
                "wsgi.input": io.BytesIO(multi_request),
                "CONTENT_LENGTH": str(len(multi_request)),
            },
            start_response,
        )
    ).decode("utf-8")
    multi_payload = json.loads(multi_body)
    assert status_headers["status"] == "200 OK"
    assert multi_payload["title"] == "Cross-Repo Query"
    assert "RepoBrain Cross-Repo Query" in multi_payload["result"]
    assert "RepoBrain Auto-Attached Files" in multi_payload["result"]
    assert "sample_repo_two" in multi_payload["result"]
    assert multi_payload["data"]["kind"] == "workspace_query"
    assert multi_payload["file_context"]["files"]
    assert multi_payload["data"]["comparison"]["best_match"]["name"] in {"sample_repo", "sample_repo_two"}
    assert isinstance(multi_payload["data"]["comparison"]["global_evidence"], list)
    assert "global_rank" in multi_payload["data"]["results"][0]
    assert isinstance(multi_payload["data"]["results"][0]["citations"], list)


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
    assert "Reranker model pool:" in html
    assert "gemini-2.5-flash, gemini-3-flash-preview" in html
    assert "429 Resource exhausted" in html
