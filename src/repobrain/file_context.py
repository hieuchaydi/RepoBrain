from __future__ import annotations

from pathlib import Path
from typing import Any

from repobrain.models import PatchReviewReport, QueryResult, ReviewReport, ShipReport

_MAX_ATTACHED_FILES = 8


def attach_file_context(payload: object, file_context: dict[str, Any] | None) -> object:
    if not file_context:
        return payload
    payload_dict = _payload_dict(payload)
    payload_dict["file_context"] = file_context
    return payload_dict


def build_file_context(payload: object, *, action_label: str = "result", limit: int = _MAX_ATTACHED_FILES) -> dict[str, Any] | None:
    payload_dict = _payload_dict(payload)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_file(
        file_path: object,
        *,
        source: str,
        role: str = "unknown",
        score: object = None,
        reason: str = "",
        improvement: str = "",
        line_range: str = "",
    ) -> None:
        cleaned = _clean_path(file_path)
        if not cleaned or cleaned in seen:
            return
        seen.add(cleaned)
        role_text = str(role or "unknown")
        entries.append(
            {
                "file_path": cleaned,
                "source": source,
                "role": role_text,
                "score": _coerce_score(score),
                "reason": _compact_text(reason) or _default_reason(source),
                "improvement": _compact_text(improvement) or _improvement_for(role_text, source),
                "line_range": _compact_text(line_range),
            }
        )

    _collect_query_files(payload_dict, add_file)
    _collect_review_files(payload_dict, add_file)
    _collect_patch_review_files(payload_dict, add_file)
    _collect_workspace_query_files(payload_dict, add_file)
    _collect_ship_files(payload_dict, add_file)

    if not entries:
        return None

    ranked = entries[:limit]
    next_steps = _next_steps_for(ranked)
    return {
        "kind": "file_context",
        "action": action_label,
        "summary": (
            f"Auto-attached {len(ranked)} file(s) from {action_label}. "
            "They were added to repo memory so follow-up questions can reuse the same context."
        ),
        "files": ranked,
        "warnings": _context_warnings(ranked),
        "next_steps": next_steps,
        "memory_updated": False,
        "memory_summary": "",
    }


def file_paths_from_context(file_context: dict[str, Any] | None) -> list[str]:
    if not isinstance(file_context, dict):
        return []
    files = file_context.get("files", [])
    if not isinstance(files, list):
        return []
    paths: list[str] = []
    for item in files:
        if isinstance(item, dict):
            path = _clean_path(item.get("file_path"))
            if path:
                paths.append(path)
    return paths


def _payload_dict(payload: object) -> dict[str, Any]:
    if isinstance(payload, dict):
        return dict(payload)
    if hasattr(payload, "to_dict"):
        value = payload.to_dict()
        if isinstance(value, dict):
            return dict(value)
    if isinstance(payload, QueryResult | ReviewReport | PatchReviewReport | ShipReport):
        value = payload.to_dict()
        return dict(value)
    return {}


def _clean_path(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("\\", "/")
    lowered = text.lower()
    if text.startswith(".repobrain/") or "/node_modules/" in lowered or "/dist/" in lowered:
        return ""
    if text.startswith("venv/") or text.startswith(".tmp_") or text.startswith("pytest_work"):
        return ""
    return text


def _compact_text(value: object, *, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _coerce_score(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


def _line_range(item: dict[str, Any]) -> str:
    start = item.get("start_line")
    end = item.get("end_line")
    if start is None or end is None:
        return ""
    return f"{start}-{end}"


def _reasons_text(item: dict[str, Any]) -> str:
    reasons = item.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        return ", ".join(str(reason) for reason in reasons[:4])
    return ""


def _collect_query_files(payload: dict[str, Any], add_file) -> None:
    if not {"query", "top_files"}.issubset(payload):
        return
    for item in _dict_items(payload.get("edit_targets")):
        add_file(
            item.get("file_path"),
            source="edit_target",
            score=item.get("score"),
            reason=item.get("rationale", ""),
            improvement=item.get("rationale", ""),
        )
    for item in _dict_items(payload.get("top_files")):
        add_file(
            item.get("file_path"),
            source="top_file",
            role=str(item.get("role", "unknown")),
            score=item.get("score"),
            reason=_reasons_text(item),
        )
    for item in _dict_items(payload.get("snippets")):
        symbol = item.get("symbol_name")
        add_file(
            item.get("file_path"),
            source="citation",
            role=str(item.get("role", "unknown")),
            score=item.get("score"),
            reason=f"Snippet evidence{f' in {symbol}' if symbol else ''}.",
            line_range=_line_range(item),
        )


def _collect_review_files(payload: dict[str, Any], add_file) -> None:
    if "findings" not in payload:
        return
    for finding in _dict_items(payload.get("findings")):
        recommendation = str(finding.get("recommendation", "") or finding.get("summary", ""))
        severity = str(finding.get("severity", "unknown"))
        category = str(finding.get("category", "review"))
        title = str(finding.get("title", "review finding"))
        file_paths = finding.get("file_paths", [])
        if not isinstance(file_paths, list):
            continue
        for path in file_paths:
            add_file(
                path,
                source="review_finding",
                reason=f"{severity} {category}: {title}",
                improvement=recommendation,
            )


def _collect_patch_review_files(payload: dict[str, Any], add_file) -> None:
    if payload.get("kind") != "patch_review" and "changed_files" not in payload:
        return
    for item in _dict_items(payload.get("changed_files")):
        status = str(item.get("status", "changed"))
        symbols = item.get("symbols", [])
        symbol_text = f" symbols: {', '.join(str(symbol) for symbol in symbols[:3])}" if isinstance(symbols, list) and symbols else ""
        add_file(
            item.get("file_path"),
            source="changed_file",
            role=str(item.get("role", "unknown")),
            reason=f"{status} file in current patch.{symbol_text}",
            improvement=_improvement_for(str(item.get("role", "unknown")), "changed_file"),
        )
    for source, key in (
        ("adjacent_file", "adjacent_files"),
        ("suggested_test", "suggested_tests"),
        ("config_surface", "config_surfaces"),
    ):
        for item in _dict_items(payload.get(key)):
            add_file(
                item.get("file_path"),
                source=source,
                role=str(item.get("role", "unknown")),
                score=item.get("score"),
                reason=_reasons_text(item),
            )


def _collect_workspace_query_files(payload: dict[str, Any], add_file) -> None:
    if payload.get("kind") != "workspace_query":
        return
    comparison = payload.get("comparison", {})
    if isinstance(comparison, dict):
        for item in _dict_items(comparison.get("global_evidence")):
            add_file(
                item.get("file_path"),
                source="workspace_citation",
                role=str(item.get("role", "unknown")),
                score=item.get("score"),
                reason=f"{item.get('name', 'workspace')} citation rank #{item.get('rank', '?')}.",
                line_range=_line_range(item),
            )
    for result in _dict_items(payload.get("results")):
        for path in result.get("top_files", []) if isinstance(result.get("top_files"), list) else []:
            add_file(path, source="workspace_top_file", reason=f"Top file in {result.get('name', 'workspace repo')}.")
        for citation in _dict_items(result.get("citations")):
            add_file(
                citation.get("file_path"),
                source="workspace_citation",
                role=str(citation.get("role", "unknown")),
                score=citation.get("score"),
                reason=_reasons_text(citation),
                line_range=_line_range(citation),
            )


def _collect_ship_files(payload: dict[str, Any], add_file) -> None:
    review = payload.get("review")
    if isinstance(review, dict):
        _collect_review_files(review, add_file)


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _default_reason(source: str) -> str:
    return {
        "changed_file": "Changed in the current patch.",
        "adjacent_file": "Structurally or semantically adjacent to the changed files.",
        "suggested_test": "Likely regression test coverage for this change.",
        "config_surface": "Configuration or environment surface related to this change.",
        "review_finding": "Mentioned by project review.",
        "edit_target": "Ranked as an edit target.",
        "top_file": "Ranked as a top evidence file.",
        "citation": "Cited as supporting evidence.",
    }.get(source, "Surfaced by RepoBrain evidence.")


def _improvement_for(role: str, source: str) -> str:
    if source == "suggested_test" or role == "test":
        return "Run this test and add focused assertions for the changed behavior and failure path."
    if source == "config_surface" or role == "config":
        return "Verify env defaults, required settings, secret handling, and callback or provider wiring."
    if source == "adjacent_file":
        return "Inspect this runtime neighbor before merging; it may break even if it was not edited."
    if source == "changed_file":
        return "Review the exact patch here first, then confirm validation, errors, and regression coverage."
    if role == "route":
        return "Check request validation, auth/permission boundaries, error responses, and service delegation."
    if role == "service":
        return "Check business invariants, idempotency, retry/fallback behavior, and exception handling."
    if role == "job":
        return "Check scheduling assumptions, retry policy, idempotency, and operational logging."
    return "Open this file, verify the surrounding flow, and add or update tests before changing behavior."


def _context_warnings(files: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    roles = {str(item.get("role", "unknown")) for item in files}
    sources = {str(item.get("source", "")) for item in files}
    if len(files) == 1:
        warnings.append("Evidence is concentrated in one file; inspect neighbors before editing.")
    if "config" in roles or "config_surface" in sources:
        warnings.append("Config or environment files are involved; verify local defaults and deployment settings.")
    if "suggested_test" not in sources and "test" not in roles:
        warnings.append("No test file was auto-attached; add or locate regression coverage manually.")
    return warnings


def _next_steps_for(files: list[dict[str, Any]]) -> list[str]:
    first_path = str(files[0].get("file_path", "")) if files else ""
    first_name = Path(first_path).name if first_path else "the top attached file"
    steps = [
        f"Start with {first_name}; verify the surrounding call path before editing.",
        "Use the attached files as the next focus context for follow-up questions.",
    ]
    if any(item.get("source") == "suggested_test" or item.get("role") == "test" for item in files):
        steps.append("Run the attached tests after changes and add assertions for uncovered paths.")
    else:
        steps.append("Add a focused regression test if the change affects behavior.")
    return steps
