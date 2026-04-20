from __future__ import annotations

from pathlib import Path
from typing import Any

from repobrain.active_repo import write_active_repo
from repobrain.engine.core import RepoBrainEngine
from repobrain.models import QueryResult
from repobrain.ux import build_report
from repobrain.workspace import add_workspace_project, remember_query_result


FIRST_LOOK_QUERIES: tuple[tuple[str, str], ...] = (
    ("query", "Where is the main flow implemented?"),
    ("trace", "Trace the primary request flow from entrypoint to service"),
    ("targets", "Which files should I inspect first before changing this repo?"),
)


def run_first_look(
    repo_root: str | Path,
    *,
    report_output: str | Path | None = None,
    include_report: bool = True,
) -> dict[str, object]:
    root = Path(repo_root).expanduser().resolve()
    engine = RepoBrainEngine(root)
    init_payload = engine.init_workspace(force=False)
    index_payload = engine.index_repository(include_review=True)
    write_active_repo(root)
    workspace = add_workspace_project(root, make_current=True)

    query_runs = [_run_first_look_query(engine, mode=mode, question=question) for mode, question in FIRST_LOOK_QUERIES]
    report_path: Path | None = None
    if include_report:
        report_path = build_report(engine, report_output)

    index_summary = {
        key: index_payload.get(key, 0)
        for key in ("files", "chunks", "symbols", "edges")
    }
    parser_counts = index_payload.get("parsers", {})
    if isinstance(parser_counts, dict):
        index_summary["parsers"] = parser_counts

    payload: dict[str, object] = {
        "kind": "first_look",
        "repo_root": str(root),
        "local_only": True,
        "init": init_payload,
        "index": index_summary,
        "import_assessment": index_payload.get("import_assessment"),
        "review": index_payload.get("review"),
        "queries": query_runs,
        "report_path": str(report_path) if report_path is not None else "",
        "workspace": workspace,
        "next_commands": [
            "repobrain serve-web --open",
            "repobrain chat",
            "repobrain patch-review --format text",
            "repobrain key groq --format text",
        ],
    }
    return payload


def _run_first_look_query(engine: RepoBrainEngine, *, mode: str, question: str) -> dict[str, object]:
    try:
        if mode == "trace":
            result = engine.trace(question)
        elif mode == "targets":
            result = engine.targets(question)
        else:
            result = engine.query(question)
        remember_query_result(engine.config.resolved_repo_root, query=question, result=result)
        return _compact_query_result(result, mode=mode)
    except Exception as exc:
        return {
            "mode": mode,
            "question": question,
            "status": "error",
            "error": str(exc),
        }


def _compact_query_result(result: QueryResult, *, mode: str) -> dict[str, object]:
    return {
        "mode": mode,
        "question": result.query,
        "status": "pass",
        "intent": result.intent.value,
        "confidence": round(result.confidence, 3),
        "confidence_label": result.confidence_label,
        "summary": result.confidence_summary,
        "top_files": [item.to_dict() for item in result.top_files[:5]],
        "edit_targets": [item.to_dict() for item in result.edit_targets[:3]],
        "snippets": [
            {
                "file_path": item.file_path,
                "symbol_name": item.symbol_name,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "score": round(float(item.score), 3),
                "preview": _preview(item.content),
            }
            for item in result.snippets[:3]
        ],
        "warnings": result.warnings[:4],
        "next_questions": result.next_questions[:3],
    }


def _preview(content: Any, *, limit: int = 180) -> str:
    text = " ".join(str(content).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
