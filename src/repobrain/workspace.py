from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from repobrain.models import QueryResult

WORKSPACE_STATE_FILE_ENV = "REPOBRAIN_WORKSPACE_STATE_FILE"
_STATE_VERSION = 1
_MAX_MANUAL_NOTES = 6
_MAX_RECENT_QUERIES = 6
_MAX_TOP_FILES = 6
_MAX_WARNINGS = 4
_MAX_NEXT_QUESTIONS = 4
_MAX_GLOBAL_EVIDENCE = 5


def workspace_state_file() -> Path:
    override = os.getenv(WORKSPACE_STATE_FILE_ENV)
    if override:
        return Path(override)
    return Path.home() / ".repobrain" / "workspace.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _empty_memory() -> dict[str, Any]:
    return {
        "summary": "",
        "manual_notes": [],
        "recent_queries": [],
        "top_files": [],
        "warnings": [],
        "next_questions": [],
        "updated_at": "",
    }


def _default_state() -> dict[str, Any]:
    return {"version": _STATE_VERSION, "current_repo": "", "projects": []}


def _normalize_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _normalize_memory(memory: Any) -> dict[str, Any]:
    if not isinstance(memory, dict):
        return _empty_memory()
    normalized = _empty_memory()
    normalized["summary"] = str(memory.get("summary", "")).strip()
    normalized["manual_notes"] = _normalize_list(memory.get("manual_notes"))
    normalized["recent_queries"] = _normalize_list(memory.get("recent_queries"))
    normalized["top_files"] = _normalize_list(memory.get("top_files"))
    normalized["warnings"] = _normalize_list(memory.get("warnings"))
    normalized["next_questions"] = _normalize_list(memory.get("next_questions"))
    normalized["updated_at"] = str(memory.get("updated_at", "")).strip()
    return normalized


def _normalize_project(project: Any) -> dict[str, Any] | None:
    if not isinstance(project, dict):
        return None
    repo_root = str(project.get("repo_root", "")).strip()
    if not repo_root:
        return None
    name = str(project.get("name", "")).strip() or Path(repo_root).name or repo_root
    return {
        "name": name,
        "repo_root": repo_root,
        "added_at": str(project.get("added_at", "")).strip(),
        "last_used_at": str(project.get("last_used_at", "")).strip(),
        "memory": _normalize_memory(project.get("memory")),
    }


def load_workspace_state() -> dict[str, Any]:
    path = workspace_state_file()
    if not path.exists():
        return _default_state()
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_state()
    if not isinstance(raw_data, dict):
        return _default_state()

    state = _default_state()
    state["current_repo"] = str(raw_data.get("current_repo", "")).strip()
    projects = raw_data.get("projects", [])
    if isinstance(projects, list):
        normalized_projects = []
        for project in projects:
            normalized = _normalize_project(project)
            if normalized is not None:
                normalized_projects.append(normalized)
        state["projects"] = normalized_projects
    return state


def save_workspace_state(state: dict[str, Any]) -> Path:
    path = workspace_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _STATE_VERSION,
        "current_repo": str(state.get("current_repo", "")).strip(),
        "projects": state.get("projects", []),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _safe_save_workspace_state(state: dict[str, Any]) -> bool:
    try:
        save_workspace_state(state)
        return True
    except OSError:
        # Fall back to in-memory behavior when workspace storage is read-only
        # or temporarily unavailable.
        return False


def _resolve_repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).expanduser().resolve()


def _project_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    projects = state.get("projects")
    if isinstance(projects, list):
        return projects
    state["projects"] = []
    return state["projects"]


def _find_project_by_repo(state: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    resolved = str(repo_root)
    for project in _project_entries(state):
        if project.get("repo_root") == resolved:
            return project
    return None


def _ensure_project(state: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    project = _find_project_by_repo(state, repo_root)
    if project is not None:
        project["name"] = str(project.get("name", "")).strip() or repo_root.name or str(repo_root)
        project["memory"] = _normalize_memory(project.get("memory"))
        return project
    project = {
        "name": repo_root.name or str(repo_root),
        "repo_root": str(repo_root),
        "added_at": _now_iso(),
        "last_used_at": _now_iso(),
        "memory": _empty_memory(),
    }
    _project_entries(state).append(project)
    return project


def _merge_recent(existing: list[str], additions: list[str], *, limit: int) -> list[str]:
    merged = [item for item in existing if item]
    for item in additions:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        if cleaned in merged:
            merged.remove(cleaned)
        merged.append(cleaned)
    return merged[-limit:]


def _trim_query(query: str, *, limit: int = 120) -> str:
    compact = " ".join(query.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _short_file_list(paths: list[str]) -> str:
    labels = [Path(item).name or item for item in paths if item]
    return ", ".join(labels[:4])


def _compact_preview(text: str, *, limit: int = 160) -> str:
    preview = " ".join(str(text).split())
    if len(preview) <= limit:
        return preview
    return preview[: limit - 3].rstrip() + "..."


def _compose_summary(memory: dict[str, Any]) -> str:
    parts: list[str] = []
    manual_notes = list(memory.get("manual_notes", []))
    if manual_notes:
        parts.append(f"Notes: {'; '.join(manual_notes[-2:])}.")
    recent_queries = list(memory.get("recent_queries", []))
    if recent_queries:
        parts.append(f"Recent asks: {' | '.join(_trim_query(item) for item in recent_queries[-2:])}.")
    top_files = list(memory.get("top_files", []))
    if top_files:
        parts.append(f"Evidence clusters: {_short_file_list(top_files)}.")
    warnings = list(memory.get("warnings", []))
    if warnings:
        parts.append(f"Watch-outs: {'; '.join(warnings[-2:])}.")
    next_questions = list(memory.get("next_questions", []))
    if next_questions:
        parts.append(f"Next thread: {'; '.join(next_questions[-1:])}.")
    return " ".join(part for part in parts if part).strip()


def _project_payload(project: dict[str, Any], current_repo: str) -> dict[str, Any]:
    memory = _normalize_memory(project.get("memory"))
    return {
        "name": project.get("name", ""),
        "repo_root": project.get("repo_root", ""),
        "active": project.get("repo_root", "") == current_repo,
        "added_at": project.get("added_at", ""),
        "last_used_at": project.get("last_used_at", ""),
        "summary": memory.get("summary", ""),
        "manual_notes": list(memory.get("manual_notes", [])),
        "recent_queries": list(memory.get("recent_queries", [])),
        "top_files": list(memory.get("top_files", [])),
        "warnings": list(memory.get("warnings", [])),
        "next_questions": list(memory.get("next_questions", [])),
        "updated_at": memory.get("updated_at", ""),
    }


def _workspace_projects_payload(state: dict[str, Any], *, message: str = "") -> dict[str, Any]:
    current_repo = str(state.get("current_repo", "")).strip()
    projects = [_project_payload(project, current_repo) for project in _project_entries(state)]
    return {
        "kind": "workspace_projects",
        "message": message,
        "current_repo": current_repo,
        "project_count": len(projects),
        "projects": projects,
    }


def _resolve_project_ref(project_ref: str | Path | None, state: dict[str, Any]) -> dict[str, Any] | None:
    projects = _project_entries(state)
    if not projects:
        return None
    if project_ref is None or not str(project_ref).strip():
        current_repo = str(state.get("current_repo", "")).strip()
        if not current_repo:
            return None
        return _find_project_by_repo(state, Path(current_repo).expanduser().resolve())

    ref_text = str(project_ref).strip()
    if any(separator in ref_text for separator in ("/", "\\")) or ref_text.startswith("."):
        candidate = Path(ref_text).expanduser()
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate)
        for project in projects:
            if project.get("repo_root") == resolved:
                return project

    lowered_ref = ref_text.lower()
    matches = [
        project
        for project in projects
        if str(project.get("name", "")).lower() == lowered_ref
        or Path(str(project.get("repo_root", ""))).name.lower() == lowered_ref
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Multiple tracked repos match `{ref_text}`. Use the full path instead.")
    return None


def current_workspace_repo() -> Path | None:
    state = load_workspace_state()
    current_repo = str(state.get("current_repo", "")).strip()
    if not current_repo:
        return None
    path = Path(current_repo).expanduser().resolve()
    if not path.exists():
        return None
    return path


def add_workspace_project(repo_root: str | Path, *, make_current: bool = True) -> dict[str, Any]:
    resolved = _resolve_repo_root(repo_root)
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError("Project path does not exist or is not a directory.")

    state = load_workspace_state()
    project = _ensure_project(state, resolved)
    project["last_used_at"] = _now_iso()
    if make_current:
        state["current_repo"] = str(resolved)
    persisted = _safe_save_workspace_state(state)
    message = f"Tracked repo: {resolved}"
    if make_current:
        message = f"Tracked repo and set active: {resolved}"
    if not persisted:
        message += " (workspace state not persisted: write access unavailable)"
    return _workspace_projects_payload(state, message=message)


def workspace_projects_payload() -> dict[str, Any]:
    return _workspace_projects_payload(load_workspace_state())


def set_current_workspace_project(project_ref: str | Path) -> dict[str, Any]:
    state = load_workspace_state()
    project = _resolve_project_ref(project_ref, state)
    if project is None:
        raise ValueError("Tracked repo not found. Add it first with `repobrain workspace add <path>`.")
    project["last_used_at"] = _now_iso()
    state["current_repo"] = str(project.get("repo_root", "")).strip()
    persisted = _safe_save_workspace_state(state)
    message = f"Active repo switched to: {state['current_repo']}"
    if not persisted:
        message += " (workspace state not persisted: write access unavailable)"
    return _workspace_projects_payload(state, message=message)


def workspace_summary_payload(project_ref: str | Path | None = None, *, message: str = "") -> dict[str, Any]:
    state = load_workspace_state()
    project = _resolve_project_ref(project_ref, state)
    if project is None:
        raise ValueError("No tracked repo selected yet. Add one with `repobrain workspace add <path>`.")
    payload = _project_payload(project, str(state.get("current_repo", "")).strip())
    payload["kind"] = "workspace_summary"
    payload["message"] = message
    return payload


def remember_workspace_note(note: str, project_ref: str | Path | None = None) -> dict[str, Any]:
    cleaned_note = " ".join(str(note).split())
    if not cleaned_note:
        raise ValueError("Note text is required.")

    state = load_workspace_state()
    project = _resolve_project_ref(project_ref, state)
    if project is None:
        raise ValueError("No tracked repo selected yet. Add one with `repobrain workspace add <path>`.")

    memory = _normalize_memory(project.get("memory"))
    memory["manual_notes"] = _merge_recent(memory["manual_notes"], [cleaned_note], limit=_MAX_MANUAL_NOTES)
    memory["updated_at"] = _now_iso()
    memory["summary"] = _compose_summary(memory)
    project["memory"] = memory
    project["last_used_at"] = _now_iso()
    persisted = _safe_save_workspace_state(state)
    message = "Stored repo memory note."
    if not persisted:
        message = "Stored repo memory note in-session only (workspace state not persisted)."
    payload = _project_payload(project, str(state.get("current_repo", "")).strip())
    payload["kind"] = "workspace_summary"
    payload["message"] = message
    return payload


def clear_workspace_notes(project_ref: str | Path | None = None) -> dict[str, Any]:
    state = load_workspace_state()
    project = _resolve_project_ref(project_ref, state)
    if project is None:
        raise ValueError("No tracked repo selected yet. Add one with `repobrain workspace add <path>`.")

    memory = _normalize_memory(project.get("memory"))
    memory["manual_notes"] = []
    memory["updated_at"] = _now_iso()
    memory["summary"] = _compose_summary(memory)
    project["memory"] = memory
    project["last_used_at"] = _now_iso()
    persisted = _safe_save_workspace_state(state)
    message = "Cleared repo memory notes."
    if not persisted:
        message = "Cleared repo memory notes in-session only (workspace state not persisted)."
    payload = _project_payload(project, str(state.get("current_repo", "")).strip())
    payload["kind"] = "workspace_summary"
    payload["message"] = message
    return payload


def remember_query_result(repo_root: str | Path, *, query: str, result: QueryResult) -> dict[str, Any]:
    resolved = _resolve_repo_root(repo_root)
    state = load_workspace_state()
    project = _ensure_project(state, resolved)
    memory = _normalize_memory(project.get("memory"))
    memory["recent_queries"] = _merge_recent(memory["recent_queries"], [_trim_query(query)], limit=_MAX_RECENT_QUERIES)
    memory["top_files"] = _merge_recent(
        memory["top_files"],
        [item.file_path for item in result.top_files[:4]],
        limit=_MAX_TOP_FILES,
    )
    memory["warnings"] = _merge_recent(memory["warnings"], result.warnings[:2], limit=_MAX_WARNINGS)
    memory["next_questions"] = _merge_recent(memory["next_questions"], result.next_questions[:2], limit=_MAX_NEXT_QUESTIONS)
    memory["updated_at"] = _now_iso()
    memory["summary"] = _compose_summary(memory)
    project["memory"] = memory
    project["last_used_at"] = _now_iso()
    state["current_repo"] = str(resolved)
    _safe_save_workspace_state(state)
    return _project_payload(project, state["current_repo"])


def remember_file_context(
    repo_root: str | Path,
    *,
    files: list[str],
    warnings: list[str] | None = None,
    next_questions: list[str] | None = None,
) -> dict[str, Any]:
    resolved = _resolve_repo_root(repo_root)
    cleaned_files = [str(item).strip() for item in files if str(item).strip()]
    if not cleaned_files:
        raise ValueError("At least one file is required to update repo memory.")

    state = load_workspace_state()
    project = _ensure_project(state, resolved)
    memory = _normalize_memory(project.get("memory"))
    memory["top_files"] = _merge_recent(memory["top_files"], cleaned_files[:_MAX_TOP_FILES], limit=_MAX_TOP_FILES)
    memory["warnings"] = _merge_recent(memory["warnings"], list(warnings or [])[:2], limit=_MAX_WARNINGS)
    memory["next_questions"] = _merge_recent(
        memory["next_questions"],
        list(next_questions or [])[:2],
        limit=_MAX_NEXT_QUESTIONS,
    )
    memory["updated_at"] = _now_iso()
    memory["summary"] = _compose_summary(memory)
    project["memory"] = memory
    project["last_used_at"] = _now_iso()
    state["current_repo"] = str(resolved)
    _safe_save_workspace_state(state)
    return _project_payload(project, state["current_repo"])


def project_context_hint(repo_root: str | Path, *, focus: str | None = None) -> str | None:
    state = load_workspace_state()
    project = _find_project_by_repo(state, _resolve_repo_root(repo_root))
    if project is None:
        return f"Focus: {focus}" if focus else None
    memory = _normalize_memory(project.get("memory"))
    parts: list[str] = []
    if focus:
        parts.append(f"Focus: {focus}.")
    summary = str(memory.get("summary", "")).strip()
    if summary:
        parts.append(summary)
    if not parts:
        return None
    context = " ".join(parts).strip()
    if len(context) <= 420:
        return context
    return context[:417].rstrip() + "..."


def _workspace_result_summary(result: QueryResult) -> str:
    top_files = _short_file_list([item.file_path for item in result.top_files[:3]]) or "no files"
    warning = result.warnings[0] if result.warnings else "no major warnings"
    return f"{result.intent.value} via {top_files}; {warning}"


def _workspace_citations(result: QueryResult) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for hit in sorted(result.snippets, key=lambda item: item.score, reverse=True)[:2]:
        preview = _compact_preview(hit.content)
        citations.append(
            {
                "file_path": hit.file_path,
                "language": hit.language,
                "role": hit.role,
                "score": round(hit.score, 3),
                "start_line": hit.start_line,
                "end_line": hit.end_line,
                "symbol_name": hit.symbol_name,
                "reasons": list(hit.reasons[:4]),
                "preview": preview,
            }
        )
    return citations


def _workspace_repo_result_payload(
    *,
    project: dict[str, Any],
    repo_root: Path,
    current_repo_path: Path,
    result: QueryResult,
    memory_summary: str,
) -> dict[str, Any]:
    citations = _workspace_citations(result)
    return {
        "name": project.get("name", repo_root.name),
        "repo_root": str(repo_root),
        "active": repo_root == current_repo_path,
        "confidence": round(result.confidence, 3),
        "evidence_score": 0.0,
        "global_rank": None,
        "intent": result.intent.value,
        "top_files": [item.file_path for item in result.top_files[:3]],
        "warnings": result.warnings[:2],
        "summary": _workspace_result_summary(result),
        "memory_summary": memory_summary,
        "next_questions": result.next_questions[:2],
        "citations": citations,
    }


def _comparison_best_match(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not results:
        return None
    best = results[0]
    return {
        "name": best.get("name"),
        "repo_root": best.get("repo_root"),
        "confidence": best.get("confidence"),
        "evidence_score": best.get("evidence_score"),
        "global_rank": best.get("global_rank"),
        "intent": best.get("intent"),
        "summary": best.get("summary"),
    }


def _comparison_active_rank(results: list[dict[str, Any]]) -> int | None:
    for index, item in enumerate(results, start=1):
        if item.get("active"):
            return index
    return None


def _comparison_shared_hotspots(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hotspots: dict[str, set[str]] = {}
    for item in results:
        repo_name = str(item.get("name", "")).strip()
        top_files = item.get("top_files", [])
        if not repo_name or not isinstance(top_files, list):
            continue
        for path in top_files[:3]:
            label = Path(str(path)).name or str(path)
            hotspots.setdefault(label, set()).add(repo_name)

    shared: list[dict[str, Any]] = []
    for label, repos in hotspots.items():
        if len(repos) < 2:
            continue
        shared.append({"label": label, "count": len(repos), "repos": sorted(repos)})
    shared.sort(key=lambda item: (-int(item.get("count", 0)), str(item.get("label", ""))))
    return shared[:3]


def _citation_scores(citations: Any) -> list[float]:
    if not isinstance(citations, list):
        return []
    scores: list[float] = []
    for citation in citations:
        if not isinstance(citation, dict):
            continue
        try:
            scores.append(float(citation.get("score", 0.0) or 0.0))
        except (TypeError, ValueError):
            continue
    scores.sort(reverse=True)
    return scores


def _workspace_result_sort_key(item: dict[str, Any]) -> tuple[float, float, float, bool]:
    scores = _citation_scores(item.get("citations"))
    first = scores[0] if scores else 0.0
    second = scores[1] if len(scores) > 1 else 0.0
    try:
        confidence = float(item.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return (first, second, confidence, bool(item.get("active")))


def _apply_workspace_global_ranking(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(results, key=_workspace_result_sort_key, reverse=True)
    for index, item in enumerate(ranked, start=1):
        scores = _citation_scores(item.get("citations"))
        fallback_confidence = float(item.get("confidence", 0.0) or 0.0)
        item["evidence_score"] = round(scores[0] if scores else fallback_confidence, 3)
        item["global_rank"] = index
    return ranked


def _comparison_global_evidence(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    global_evidence: list[dict[str, Any]] = []
    for item in results:
        for citation in item.get("citations", []):
            if not isinstance(citation, dict):
                continue
            global_evidence.append(
                {
                    "name": item.get("name"),
                    "repo_root": item.get("repo_root"),
                    "active": item.get("active"),
                    "rank": None,
                    "score": round(float(citation.get("score", 0.0) or 0.0), 3),
                    "file_path": citation.get("file_path"),
                    "language": citation.get("language"),
                    "role": citation.get("role"),
                    "start_line": citation.get("start_line"),
                    "end_line": citation.get("end_line"),
                    "symbol_name": citation.get("symbol_name"),
                    "reasons": list(citation.get("reasons", []))[:4],
                    "preview": citation.get("preview", ""),
                }
            )

    global_evidence.sort(
        key=lambda item: (float(item.get("score", 0.0) or 0.0), bool(item.get("active"))),
        reverse=True,
    )
    for index, item in enumerate(global_evidence, start=1):
        item["rank"] = index
    return global_evidence[:_MAX_GLOBAL_EVIDENCE]


def _comparison_intent_groups(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for item in results:
        intent = str(item.get("intent", "")).strip()
        repo_name = str(item.get("name", "")).strip()
        if not intent or not repo_name:
            continue
        groups.setdefault(intent, []).append(repo_name)

    ranked = [
        {"intent": intent, "count": len(repos), "repos": repos}
        for intent, repos in groups.items()
    ]
    ranked.sort(key=lambda item: (-int(item.get("count", 0)), str(item.get("intent", ""))))
    return ranked


def _workspace_comparison_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    best_match = _comparison_best_match(results)
    active_rank = _comparison_active_rank(results)
    shared_hotspots = _comparison_shared_hotspots(results)
    intent_groups = _comparison_intent_groups(results)
    global_evidence = _comparison_global_evidence(results)

    notes: list[str] = []
    if best_match is not None:
        notes.append(
            "Best evidence currently leans toward "
            f"{best_match['name']} (citation={float(best_match['evidence_score'] or 0.0):.3f}, "
            f"confidence={float(best_match['confidence'] or 0.0):.3f})."
        )
    if active_rank is not None:
        notes.append(f"Active repo ranks #{active_rank} in the current cross-repo pass.")
    if global_evidence:
        leader = global_evidence[0]
        notes.append(
            "Top workspace citation is "
            f"{leader['name']}::{Path(str(leader.get('file_path', ''))).name}"
            f":{leader.get('start_line')}-{leader.get('end_line')} "
            f"({float(leader.get('score', 0.0) or 0.0):.3f})."
        )
    if shared_hotspots:
        hotspot = shared_hotspots[0]
        notes.append(
            f"Shared hotspot: {hotspot['label']} appears across {int(hotspot['count'])} tracked repos."
        )
    if intent_groups:
        leading_intent = intent_groups[0]
        notes.append(
            f"Most repos interpret the ask as `{leading_intent['intent']}` ({int(leading_intent['count'])} repo matches)."
        )

    return {
        "best_match": best_match,
        "active_rank": active_rank,
        "shared_hotspots": shared_hotspots,
        "intent_groups": intent_groups,
        "global_evidence": global_evidence,
        "notes": notes,
    }


def workspace_query_payload(
    query: str,
    *,
    current_repo: str | Path,
    context: str | None,
    engine_factory: Callable[[Path], Any],
    focus: str | None = None,
) -> dict[str, Any]:
    state = load_workspace_state()
    projects = _project_entries(state)
    if not projects:
        raise ValueError("No tracked repos yet. Add one with `repobrain workspace add <path>` or `/add <path>`.")

    current_repo_path = _resolve_repo_root(current_repo)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    context_applied = False

    for project in projects:
        repo_root = Path(str(project.get("repo_root", ""))).expanduser().resolve()
        try:
            engine = engine_factory(repo_root)
            if hasattr(engine, "store") and hasattr(engine.store, "indexed") and callable(engine.store.indexed):
                if not engine.store.indexed():
                    engine.index_repository()
            repo_context = project_context_hint(repo_root, focus=focus) or context
            if repo_context:
                context_applied = True
            result = engine.query(query, context=repo_context)
            memory_payload = remember_query_result(repo_root, query=query, result=result)
            results.append(
                _workspace_repo_result_payload(
                    project=project,
                    repo_root=repo_root,
                    current_repo_path=current_repo_path,
                    result=result,
                    memory_summary=str(memory_payload.get("summary", "")).strip(),
                )
            )
        except Exception as exc:
            errors.append(
                {
                    "name": str(project.get("name", repo_root.name)),
                    "repo_root": str(repo_root),
                    "error": str(exc),
                }
            )

    results = _apply_workspace_global_ranking(results)
    return {
        "kind": "workspace_query",
        "query": query,
        "current_repo": str(current_repo_path),
        "project_count": len(projects),
        "results": results,
        "errors": errors,
        "context_applied": context_applied,
        "comparison": _workspace_comparison_payload(results),
    }
