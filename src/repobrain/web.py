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
from repobrain.file_context import attach_file_context, build_file_context, file_paths_from_context
from repobrain.provider_setup import (
    configure_gemini_provider,
    configure_groq_provider,
    gemini_config_result_to_text,
    groq_config_result_to_text,
)
from repobrain.ux import build_report, file_context_to_text, payload_to_text
from repobrain.workspace import (
    clear_workspace_notes,
    project_context_hint,
    remember_file_context,
    remember_workspace_note,
    set_current_workspace_project,
    workspace_projects_payload,
    workspace_query_payload,
    workspace_summary_payload,
)


_MISSING = object()


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


def _import_project_payload(repo_path: str) -> tuple[str, str, str, dict[str, object]]:
    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise ValueError("Project path does not exist or is not a directory.")
    engine = _engine_from_repo(repo_root)
    init_payload = engine.init_workspace(force=False)
    stats = engine.index_repository(include_review=True)
    write_active_repo(repo_root)
    message = f"Imported and indexed: {repo_root}"
    index_stats = dict(stats)
    review = index_stats.pop("review", None)
    import_assessment = index_stats.pop("import_assessment", None)
    result_parts = [
        payload_to_text({**init_payload, "active_repo": str(repo_root)}),
        payload_to_text(index_stats),
    ]
    if isinstance(import_assessment, dict):
        result_parts.append(payload_to_text(import_assessment))
    data: dict[str, object] = {
        "index": index_stats,
        "review": review if isinstance(review, dict) else None,
        "import_assessment": import_assessment if isinstance(import_assessment, dict) else None,
    }
    return str(repo_root), message, "\n\n".join(result_parts), data


def _import_and_index(repo_path: str) -> tuple[str, str, str]:
    repo_text, message, result, _ = _import_project_payload(repo_path)
    return repo_text, message, result


def _select_local_directory(initial_dir: str = "") -> Path:
    start_dir = Path(initial_dir).expanduser().resolve() if initial_dir.strip() else Path.cwd()
    if not start_dir.exists() or not start_dir.is_dir():
        start_dir = Path.cwd()

    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - depends on local Python GUI support
        raise RuntimeError(
            "Native folder selection is unavailable in this Python environment. Paste the project path instead."
        ) from exc

    try:
        root = tk.Tk()
    except Exception as exc:  # pragma: no cover - depends on desktop/session GUI support
        raise RuntimeError(
            "Native folder selection is unavailable in this desktop session. Paste the project path instead."
        ) from exc
    root.withdraw()
    try:
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        selected = filedialog.askdirectory(
            parent=root,
            initialdir=str(start_dir),
            title="Choose a project folder for RepoBrain",
            mustexist=True,
        )
    finally:
        root.destroy()

    if not selected:
        raise ValueError("Folder selection was cancelled.")
    selected_path = Path(selected).expanduser().resolve()
    if not selected_path.exists() or not selected_path.is_dir():
        raise ValueError("Selected path does not exist or is not a directory.")
    return selected_path


def _active_engine() -> tuple[Path, RepoBrainEngine]:
    repo_root = read_active_repo()
    if repo_root is None:
        raise ValueError("No active repo yet. Import a project path first.")
    return repo_root, _engine_from_repo(repo_root)


def _report_html(repo_root: Path) -> str:
    engine = _engine_from_repo(repo_root)
    report_path = build_report(engine)
    return report_path.read_text(encoding="utf-8")


def _workspace_snapshot() -> tuple[dict[str, object], dict[str, object] | None]:
    workspace = workspace_projects_payload()
    current_repo = str(workspace.get("current_repo", "")).strip()
    if not current_repo:
        return workspace, None
    try:
        return workspace, workspace_summary_payload(current_repo)
    except ValueError:
        return workspace, None


def _action_payload_result(mode: str, query_text: str) -> tuple[str, str, object]:
    repo_root, engine = _active_engine()
    context = project_context_hint(repo_root)
    if mode == "trace":
        payload = engine.trace(query_text, context=context)
        title = "Trace"
    elif mode == "impact":
        payload = engine.impact(query_text, context=context)
        title = "Impact"
    elif mode == "targets":
        payload = engine.targets(query_text, context=context)
        title = "Targets"
    elif mode == "multi":
        payload = workspace_query_payload(
            query_text,
            current_repo=repo_root,
            context=context,
            engine_factory=_engine_from_repo,
        )
        title = "Cross-Repo Query"
    else:
        payload = engine.query(query_text, context=context)
        title = "Query"
    return str(repo_root), title, payload


def _action_result(mode: str, query_text: str) -> tuple[str, str, str]:
    repo_text, title, payload = _action_payload_result(mode, query_text)
    return repo_text, title, payload_to_text(payload)


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


def _patch_review_payload(*, base: str | None = None, files: list[str] | None = None) -> tuple[str, dict[str, object]]:
    repo_root, engine = _active_engine()
    report = engine.patch_review(base=base, files=files)
    return str(repo_root), report.to_dict()


def _with_file_context(repo_root: str | Path, title: str, payload: object) -> tuple[object, dict[str, object] | None, str]:
    data_payload: object = payload.to_dict() if hasattr(payload, "to_dict") else payload
    file_context = build_file_context(payload, action_label=title)
    paths = file_paths_from_context(file_context)
    result_text = payload_to_text(payload)
    if not file_context or not paths:
        return data_payload, None, result_text

    summary = remember_file_context(
        repo_root,
        files=paths,
        warnings=[str(item) for item in file_context.get("warnings", [])],
        next_questions=[str(item) for item in file_context.get("next_steps", [])],
    )
    file_context["memory_updated"] = True
    file_context["memory_summary"] = str(summary.get("summary", "")).strip()
    attached_payload = attach_file_context(data_payload, file_context)
    return attached_payload, file_context, result_text + "\n\n" + file_context_to_text(file_context)


def _json_response(start_response, status: str, payload: dict[str, object]) -> list[bytes]:
    body = json.dumps(payload).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [body]


def _text_response(start_response, status: str, text: str, content_type: str = "text/plain; charset=utf-8") -> list[bytes]:
    start_response(status, [("Content-Type", content_type)])
    return [text.encode("utf-8")]


def _read_request_fields(environ) -> dict[str, object]:
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
        return {str(key): value for key, value in payload.items()}
    return {key: values[0] for key, values in parse_qs(raw_body.decode("utf-8")).items()}


def _text_field(fields: dict[str, object], name: str, default: str = "") -> str:
    value = fields.get(name, default)
    if isinstance(value, list):
        if not value:
            return default
        value = value[0]
    return str(value).strip()


def _files_field(fields: dict[str, object], name: str = "files") -> list[str] | None:
    value = fields.get(name)
    if value is None:
        return None
    if isinstance(value, list):
        files = [str(item).strip() for item in value if str(item).strip()]
        return files or None
    text = str(value).strip()
    if not text:
        return None
    files = [line.strip() for line in text.splitlines() if line.strip()]
    return files or None


def _bool_field(fields: dict[str, object], name: str, default: bool = False) -> bool:
    value = fields.get(name, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _configure_gemini_payload(fields: dict[str, object]) -> tuple[str, dict[str, object], str]:
    repo_hint = _text_field(fields, "repo_path")
    if repo_hint:
        repo_root = Path(repo_hint).expanduser().resolve()
        if not repo_root.exists() or not repo_root.is_dir():
            raise ValueError("Project path does not exist or is not a directory.")
    else:
        repo_root, _ = _active_engine()

    api_key = _text_field(fields, "api_key")
    use_embedding = _bool_field(fields, "use_embedding", True)
    use_reranker = _bool_field(fields, "use_reranker", True)
    embedding_model = _text_field(fields, "embedding_model", "gemini-embedding-001") or "gemini-embedding-001"
    output_dimensionality = _text_field(fields, "output_dimensionality", "768") or "768"
    task_type = _text_field(fields, "task_type", "SEMANTIC_SIMILARITY") or "SEMANTIC_SIMILARITY"
    rerank_model = _text_field(fields, "rerank_model", "gemini-2.5-flash") or "gemini-2.5-flash"
    model_pool_text = _text_field(fields, "model_pool", "")
    data = configure_gemini_provider(
        repo_root,
        api_key=api_key,
        use_embedding=use_embedding,
        use_reranker=use_reranker,
        embedding_model=embedding_model,
        output_dimensionality=output_dimensionality,
        task_type=task_type,
        rerank_model=rerank_model,
        model_pool=model_pool_text,
    )
    return str(repo_root), data, gemini_config_result_to_text(data)


def _configure_groq_payload(fields: dict[str, object]) -> tuple[str, dict[str, object], str]:
    repo_hint = _text_field(fields, "repo_path")
    if repo_hint:
        repo_root = Path(repo_hint).expanduser().resolve()
        if not repo_root.exists() or not repo_root.is_dir():
            raise ValueError("Project path does not exist or is not a directory.")
    else:
        repo_root, _ = _active_engine()

    api_key = _text_field(fields, "api_key")
    use_reranker = _bool_field(fields, "use_reranker", True)
    rerank_model = _text_field(fields, "rerank_model", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
    model_pool_text = _text_field(fields, "model_pool", "")
    data = configure_groq_provider(
        repo_root,
        api_key=api_key,
        use_reranker=use_reranker,
        rerank_model=rerank_model,
        model_pool=model_pool_text,
    )
    return str(repo_root), data, groq_config_result_to_text(data)


def _web_action_payload(
    *,
    repo_text: str,
    title: str,
    result: str,
    message: str,
    report_url: str = "/report",
    data: object | None = None,
    file_context: dict[str, object] | None = None,
    workspace: dict[str, object] | None = None,
    summary: dict[str, object] | None | object = _MISSING,
) -> dict[str, object]:
    if workspace is None or summary is _MISSING:
        inferred_workspace, inferred_summary = _workspace_snapshot()
        if workspace is None:
            workspace = inferred_workspace
        if summary is _MISSING:
            summary = inferred_summary
    payload: dict[str, object] = {
        "ok": True,
        "active_repo": repo_text,
        "repo_input": repo_text,
        "message": message,
        "title": title,
        "result": result,
        "report_url": report_url,
        "workspace": workspace,
        "summary": summary,
    }
    if data is not None:
        payload["data"] = data
    if file_context is not None:
        payload["file_context"] = file_context
    return payload


def _bootstrap_payload(default_repo: str = "") -> dict[str, object]:
    active_repo = read_active_repo()
    active_repo_text = str(active_repo) if active_repo else default_repo
    workspace, summary = _workspace_snapshot()
    return {
        "ok": True,
        "active_repo": active_repo_text,
        "repo_input": active_repo_text,
        "report_url": "/report",
        "locales": ["en", "vi", "zh"],
        "default_mode": "query",
        "workspace": workspace,
        "summary": summary,
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

        if method == "GET" and path == "/api/workspace":
            workspace, summary = _workspace_snapshot()
            return _json_response(start_response, "200 OK", {"ok": True, "workspace": workspace, "summary": summary})

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
                if path == "/api/select-folder":
                    selected = _select_local_directory(_text_field(fields, "initial_dir"))
                    return _json_response(
                        start_response,
                        "200 OK",
                        {
                            "ok": True,
                            "repo_path": str(selected),
                            "message": "Folder selected. Click Import + Index to build the local index.",
                        },
                    )
                if path == "/api/import":
                    repo_text, message, result, data = _import_project_payload(_text_field(fields, "repo_path"))
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Import + Index",
                        result=result,
                        message=message,
                        data=data,
                    )
                elif path == "/api/index":
                    repo_text, result = _index_result()
                    payload = _web_action_payload(repo_text=repo_text, title="Index", result=result, message="Active repo re-indexed.")
                elif path == "/api/review":
                    repo_root, engine = _active_engine()
                    report = engine.review()
                    data, file_context, result = _with_file_context(repo_root, "Project Review", report)
                    payload = _web_action_payload(
                        repo_text=str(repo_root),
                        title="Project Review",
                        result=result,
                        message="Project review generated.",
                        data=data,
                        file_context=file_context,
                    )
                elif path == "/api/ship":
                    repo_root, engine = _active_engine()
                    report = engine.ship()
                    data, file_context, result = _with_file_context(repo_root, "Ship Readiness", report)
                    payload = _web_action_payload(
                        repo_text=str(repo_root),
                        title="Ship Readiness",
                        result=result,
                        message="Ship gate completed.",
                        data=data,
                        file_context=file_context,
                    )
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
                elif path == "/api/providers/gemini":
                    repo_text, data, result = _configure_gemini_payload(fields)
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Gemini Config",
                        result=result,
                        message="Gemini provider configuration saved.",
                        data=data,
                    )
                elif path == "/api/providers/groq":
                    repo_text, data, result = _configure_groq_payload(fields)
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Groq Config",
                        result=result,
                        message="Groq provider configuration saved.",
                        data=data,
                    )
                elif path == "/api/patch-review":
                    base = _text_field(fields, "base") or None
                    files = _files_field(fields, "files")
                    repo_text, data = _patch_review_payload(base=base, files=files)
                    data, file_context, result = _with_file_context(repo_text, "Patch Review", data)
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Patch Review",
                        result=result,
                        message="Patch review completed.",
                        data=data,
                        file_context=file_context,
                    )
                elif path == "/api/workspace/use":
                    project = _text_field(fields, "project")
                    if not project:
                        raise ValueError("Project selection is required.")
                    workspace = set_current_workspace_project(project)
                    repo_text = str(workspace.get("current_repo", "")).strip()
                    if not repo_text:
                        raise ValueError("Workspace switch did not produce an active repo.")
                    write_active_repo(repo_text)
                    summary = workspace_summary_payload(repo_text)
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Workspace",
                        result=payload_to_text(summary),
                        message="Active repo switched.",
                        workspace=workspace,
                        summary=summary,
                    )
                elif path == "/api/workspace/remember":
                    note = _text_field(fields, "note")
                    if not note:
                        raise ValueError("Note text is required.")
                    summary = remember_workspace_note(note)
                    repo_text = str(summary.get("repo_root", "")).strip()
                    workspace, _ = _workspace_snapshot()
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Repo Memory",
                        result=payload_to_text(summary),
                        message="Repo memory note saved.",
                        workspace=workspace,
                        summary=summary,
                    )
                elif path == "/api/workspace/clear-notes":
                    summary = clear_workspace_notes()
                    repo_text = str(summary.get("repo_root", "")).strip()
                    workspace, _ = _workspace_snapshot()
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title="Repo Memory",
                        result=payload_to_text(summary),
                        message="Repo memory notes cleared.",
                        workspace=workspace,
                        summary=summary,
                    )
                elif path == "/api/query":
                    query_text = _text_field(fields, "query")
                    mode = _text_field(fields, "mode", "query") or "query"
                    if not query_text:
                        raise ValueError("Query text is required.")
                    repo_text, title, action_data = _action_payload_result(mode, query_text)
                    action_data, file_context, result = _with_file_context(repo_text, title, action_data)
                    payload = _web_action_payload(
                        repo_text=repo_text,
                        title=title,
                        result=result,
                        message=f"{title} completed.",
                        data=action_data if isinstance(action_data, dict) else None,
                        file_context=file_context,
                    )
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
        sys.stdout.write(f"RepoBrain Workbench running at {url}\n")
        sys.stdout.flush()

    app = _application(default_repo=default_repo)
    with make_server(host, port, app) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return 0
    return 0
