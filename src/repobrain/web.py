from __future__ import annotations

import json
import mimetypes
import sys
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from repobrain.active_repo import read_active_repo, write_active_repo
from repobrain.engine.core import RepoBrainEngine
from repobrain.ux import build_report, payload_to_text


def _frontend_dir_candidates() -> tuple[Path, ...]:
    module_path = Path(__file__).resolve()
    return (
        module_path.parents[2] / "webapp" / "dist",
        module_path.parents[1] / "webapp" / "dist",
        module_path.with_name("web_frontend"),
    )


def _default_frontend_dir() -> Path:
    for candidate in _frontend_dir_candidates():
        if candidate.exists():
            return candidate
    return _frontend_dir_candidates()[0]


WEB_FRONTEND_DIR = _default_frontend_dir()


def _engine_from_repo(repo_root: Path) -> RepoBrainEngine:
    return RepoBrainEngine(repo_root)


def _frontend_asset_path(asset_name: str) -> Path:
    searched_paths: list[str] = []
    for frontend_dir in dict.fromkeys((WEB_FRONTEND_DIR, *_frontend_dir_candidates())):
        asset_path = frontend_dir / asset_name
        searched_paths.append(str(asset_path))
        if asset_path.exists() and asset_path.is_file():
            return asset_path
    raise FileNotFoundError(
        "React frontend build is missing. Run `npm run build` inside `webapp/` to generate `webapp/dist`."
        f" Looked in: {', '.join(searched_paths)}"
    )


def _import_and_index(repo_path: str) -> tuple[str, str, str]:
    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise ValueError("Project path does not exist or is not a directory.")
    engine = _engine_from_repo(repo_root)
    init_payload = engine.init_workspace(force=False)
    stats = engine.index_repository()
    write_active_repo(repo_root)
    message = f"Imported and indexed: {repo_root}"
    result = payload_to_text({**init_payload, "active_repo": str(repo_root)}) + "\n\n" + payload_to_text(stats)
    return str(repo_root), message, result


def _active_engine() -> tuple[Path, RepoBrainEngine]:
    repo_root = read_active_repo()
    if repo_root is None:
        raise ValueError("No active repo yet. Import a project path first.")
    return repo_root, _engine_from_repo(repo_root)


def _report_html(repo_root: Path) -> str:
    engine = _engine_from_repo(repo_root)
    report_path = build_report(engine)
    return report_path.read_text(encoding="utf-8")


def _action_result(mode: str, query_text: str) -> tuple[str, str, str]:
    repo_root, engine = _active_engine()
    if mode == "trace":
        payload = engine.trace(query_text)
        title = "Trace"
    elif mode == "impact":
        payload = engine.impact(query_text)
        title = "Impact"
    elif mode == "targets":
        payload = engine.targets(query_text)
        title = "Targets"
    else:
        payload = engine.query(query_text)
        title = "Query"
    return str(repo_root), title, payload_to_text(payload)


def _doctor_result() -> tuple[str, str]:
    repo_text, payload = _doctor_payload()
    return repo_text, payload_to_text(payload)


def _review_result() -> tuple[str, str]:
    repo_root, engine = _active_engine()
    return str(repo_root), payload_to_text(engine.review())


def _ship_result() -> tuple[str, str]:
    repo_root, engine = _active_engine()
    return str(repo_root), payload_to_text(engine.ship())


def _baseline_result() -> tuple[str, str]:
    repo_root, engine = _active_engine()
    report = engine.review(compare_baseline=False)
    return str(repo_root), payload_to_text(engine.save_review_baseline(report))


def _index_result() -> tuple[str, str]:
    repo_root, engine = _active_engine()
    return str(repo_root), payload_to_text(engine.index_repository())


def _provider_smoke_result() -> tuple[str, str]:
    repo_text, payload = _provider_smoke_payload()
    return repo_text, payload_to_text(payload)


def _doctor_payload() -> tuple[str, dict[str, object]]:
    repo_root, engine = _active_engine()
    return str(repo_root), engine.doctor()


def _provider_smoke_payload() -> tuple[str, dict[str, object]]:
    repo_root, engine = _active_engine()
    return str(repo_root), engine.provider_smoke()


def _json_response(start_response, status: str, payload: dict[str, object]) -> list[bytes]:
    body = json.dumps(payload).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [body]


def _text_response(start_response, status: str, text: str, content_type: str = "text/plain; charset=utf-8") -> list[bytes]:
    start_response(status, [("Content-Type", content_type)])
    return [text.encode("utf-8")]


def _read_request_fields(environ) -> dict[str, str]:
    size = int(environ.get("CONTENT_LENGTH") or 0)
    if size <= 0:
        return {}
    raw_body = environ["wsgi.input"].read(size)
    if not raw_body:
        return {}
    content_type = str(environ.get("CONTENT_TYPE", "")).lower()
    if "application/json" in content_type:
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items()}
    return {key: values[0] for key, values in parse_qs(raw_body.decode("utf-8")).items()}


def _web_action_payload(
    *,
    repo_text: str,
    title: str,
    result: str,
    message: str,
    report_url: str = "/report",
    data: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "ok": True,
        "active_repo": repo_text,
        "repo_input": repo_text,
        "message": message,
        "title": title,
        "result": result,
        "report_url": report_url,
    }
    if data is not None:
        payload["data"] = data
    return payload


def _bootstrap_payload(default_repo: str = "") -> dict[str, object]:
    active_repo = read_active_repo()
    active_repo_text = str(active_repo) if active_repo else default_repo
    return {
        "ok": True,
        "active_repo": active_repo_text,
        "repo_input": active_repo_text,
        "report_url": "/report",
        "locales": ["en", "vi"],
        "default_mode": "query",
    }


def _serve_frontend_asset(asset_name: str, start_response) -> list[bytes]:
    try:
        asset_path = _frontend_asset_path(asset_name)
    except FileNotFoundError as exc:
        return _text_response(start_response, "500 Internal Server Error", str(exc))
    content_type, _ = mimetypes.guess_type(str(asset_path))
    return _text_response(
        start_response,
        "200 OK",
        asset_path.read_text(encoding="utf-8"),
        content_type or "application/octet-stream",
    )


def _application(default_repo: str = ""):
    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if method == "GET" and path == "/":
            return _serve_frontend_asset("index.html", start_response)

        if method == "GET" and path == "/static/app.js":
            return _serve_frontend_asset("app.js", start_response)

        if method == "GET" and path == "/static/app.css":
            return _serve_frontend_asset("app.css", start_response)

        if method == "GET" and path == "/report":
            try:
                repo_root = read_active_repo()
                if repo_root is None:
                    raise ValueError("No active repo yet. Import a project path first.")
                report_html = _report_html(repo_root)
                return _text_response(start_response, "200 OK", report_html, "text/html; charset=utf-8")
            except Exception as exc:
                return _json_response(start_response, "400 Bad Request", {"ok": False, "error": str(exc)})

        if method == "GET" and path == "/doctor":
            try:
                _, result = _doctor_result()
                return _text_response(start_response, "200 OK", result)
            except Exception as exc:
                return _text_response(start_response, "400 Bad Request", str(exc))

        if method == "GET" and path == "/api/bootstrap":
            return _json_response(start_response, "200 OK", _bootstrap_payload(default_repo=default_repo))

        if method == "GET" and path == "/api/doctor":
            try:
                repo_text, data = _doctor_payload()
                return _json_response(
                    start_response,
                    "200 OK",
                    _web_action_payload(
                        repo_text=repo_text,
                        title="Doctor",
                        result=payload_to_text(data),
                        message="Doctor completed.",
                        data=data,
                    ),
                )
            except Exception as exc:
                return _json_response(start_response, "400 Bad Request", {"ok": False, "error": str(exc)})

        if method == "POST":
            fields = _read_request_fields(environ)
            try:
                if path == "/api/import":
                    repo_text, message, result = _import_and_index(fields.get("repo_path", ""))
                    payload = _web_action_payload(repo_text=repo_text, title="Import + Index", result=result, message=message)
                elif path == "/api/index":
                    repo_text, result = _index_result()
                    payload = _web_action_payload(repo_text=repo_text, title="Index", result=result, message="Active repo re-indexed.")
                elif path == "/api/review":
                    repo_text, result = _review_result()
                    payload = _web_action_payload(repo_text=repo_text, title="Project Review", result=result, message="Project review generated.")
                elif path == "/api/ship":
                    repo_text, result = _ship_result()
                    payload = _web_action_payload(repo_text=repo_text, title="Ship Readiness", result=result, message="Ship gate completed.")
                elif path == "/api/baseline":
                    repo_text, result = _baseline_result()
                    payload = _web_action_payload(repo_text=repo_text, title="Baseline Saved", result=result, message="Baseline snapshot saved.")
                elif path == "/api/provider-smoke":
                    repo_text, data = _provider_smoke_payload()
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Provider Smoke",
                        result=payload_to_text(data),
                        message="Provider smoke completed.",
                        data=data,
                    )
                elif path == "/api/query":
                    query_text = fields.get("query", "").strip()
                    mode = fields.get("mode", "query").strip() or "query"
                    if not query_text:
                        raise ValueError("Query text is required.")
                    repo_text, title, result = _action_result(mode, query_text)
                    payload = _web_action_payload(repo_text=repo_text, title=title, result=result, message=f"{title} completed.")
                else:
                    return _text_response(start_response, "404 Not Found", "Not Found")
                return _json_response(start_response, "200 OK", payload)
            except Exception as exc:
                return _json_response(start_response, "400 Bad Request", {"ok": False, "error": str(exc)})

        return _text_response(start_response, "404 Not Found", "Not Found")

    return app


def serve_web(repo_root: str = "", host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> int:
    default_repo = repo_root.strip()
    if default_repo:
        write_active_repo(default_repo)

    _frontend_asset_path("index.html")
    _frontend_asset_path("app.js")
    _frontend_asset_path("app.css")

    url = f"http://{host}:{port}/"
    if open_browser:
        webbrowser.open(url)
    else:
        sys.stdout.write(f"RepoBrain Web running at {url}\n")
        sys.stdout.flush()

    app = _application(default_repo=default_repo)
    with make_server(host, port, app) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return 0
    return 0
