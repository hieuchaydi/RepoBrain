from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from repobrain.engine.core import RepoBrainEngine
from repobrain.workspace import load_workspace_state

DEFAULT_TOP_K = 8
MAX_TOP_K = 20
MAX_QUERY_LENGTH = 2000
SNIPPET_MAX_CHARS = 420


def _compact_text(value: str, *, limit: int = SNIPPET_MAX_CHARS) -> str:
    compact = " ".join(str(value).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _parse_request(payload: dict[str, Any]) -> tuple[str, str | None, int, bool]:
    query = str(payload.get("query", "")).strip()
    if not query:
        raise ValueError("`query` is required.")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"`query` exceeds maximum length of {MAX_QUERY_LENGTH} characters.")

    repo_scope_raw = str(payload.get("repo_scope", "")).strip()
    repo_scope = repo_scope_raw or None

    top_k_raw = payload.get("top_k", DEFAULT_TOP_K)
    try:
        top_k = int(top_k_raw)
    except (TypeError, ValueError):
        raise ValueError("`top_k` must be an integer.") from None
    if top_k < 1 or top_k > MAX_TOP_K:
        raise ValueError(f"`top_k` must be between 1 and {MAX_TOP_K}.")

    include_snippets = bool(payload.get("include_snippets", True))
    return query, repo_scope, top_k, include_snippets


class EngineRegistry:
    def __init__(self, default_repo_root: Path) -> None:
        self.default_repo_root = default_repo_root.resolve()
        self._engines: dict[Path, RepoBrainEngine] = {}

    def _resolve_repo_scope(self, repo_scope: str | None) -> Path:
        if not repo_scope:
            return self.default_repo_root

        candidate = Path(repo_scope).expanduser()
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()

        state = load_workspace_state()
        projects = state.get("projects", [])
        if not isinstance(projects, list):
            raise ValueError(f"Unknown `repo_scope`: {repo_scope}")

        lowered = repo_scope.lower()
        matches: list[Path] = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            repo_root = str(project.get("repo_root", "")).strip()
            if not repo_root:
                continue
            name = str(project.get("name", "")).strip().lower()
            repo_name = Path(repo_root).name.lower()
            if lowered in {name, repo_name, repo_root.lower()}:
                matches.append(Path(repo_root).expanduser().resolve())

        unique_matches: list[Path] = []
        seen: set[str] = set()
        for match in matches:
            text = str(match)
            if text in seen:
                continue
            unique_matches.append(match)
            seen.add(text)

        if len(unique_matches) == 1:
            return unique_matches[0]
        if len(unique_matches) > 1:
            raise ValueError(f"Ambiguous `repo_scope`: {repo_scope}. Use a full path.")

        raise ValueError(f"Unknown `repo_scope`: {repo_scope}")

    def _ensure_index(self, engine: RepoBrainEngine) -> None:
        if not engine.store.indexed():
            engine.index_repository()

    def get_engine(self, repo_scope: str | None) -> tuple[RepoBrainEngine, Path]:
        repo_root = self._resolve_repo_scope(repo_scope)
        engine = self._engines.get(repo_root)
        if engine is None:
            engine = RepoBrainEngine(repo_root)
            self._engines[repo_root] = engine
        self._ensure_index(engine)
        return engine, repo_root


def _normalize_response(result: Any, *, include_snippets: bool, top_k: int) -> dict[str, Any]:
    snippets_by_file: dict[str, str] = {}
    for hit in result.snippets:
        if hit.file_path not in snippets_by_file:
            snippets_by_file[hit.file_path] = _compact_text(hit.content)

    normalized_results: list[dict[str, Any]] = []
    for item in result.top_files[:top_k]:
        payload: dict[str, Any] = {
            "path": item.file_path,
            "score": round(float(item.score), 3),
            "source": "repobrain-local",
            "confidence": round(float(result.confidence), 3),
        }
        if include_snippets:
            payload["snippet"] = snippets_by_file.get(item.file_path, "")
        normalized_results.append(payload)

    return {
        "results": normalized_results,
        "metadata": {
            "provider": "repobrain-local",
            "mode": "educational_only",
        },
    }


def _health_payload(repo_root: Path) -> dict[str, Any]:
    return {
        "ok": True,
        "provider": "repobrain-local",
        "mode": "educational_only",
        "repo_root": str(repo_root),
    }


def _load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.request_file and args.query:
        raise ValueError("Use either `--request-file` or `--query`, not both.")

    if args.request_file:
        if args.request_file == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.request_file).read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request payload must be a JSON object.")
        return payload

    if args.query:
        return {
            "query": args.query,
            "repo_scope": args.repo_scope,
            "top_k": args.top_k,
            "include_snippets": args.include_snippets,
        }

    raw_stdin = sys.stdin.read().strip()
    if not raw_stdin:
        raise ValueError(
            "No request provided. Use `--query`, `--request-file`, or pipe a JSON body via stdin."
        )
    try:
        payload = json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload from stdin: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request payload must be a JSON object.")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Thin Agoragentic CLI adapter for RepoBrain retrieval v1.")
    parser.add_argument("--repo-root", default=".", help="Default repository root used when repo_scope is omitted.")
    parser.add_argument("--request-file", help="JSON request file path. Use '-' to read request JSON from stdin.")
    parser.add_argument("--query", help="Natural-language retrieval query.")
    parser.add_argument("--repo-scope", default=None, help="Optional repo/workspace filter when using --query.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help=f"Result limit when using --query (1..{MAX_TOP_K}).")
    parser.add_argument(
        "--include-snippets",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include or omit matched snippets when using --query.",
    )
    parser.add_argument("--health", action="store_true", help="Print adapter health payload and exit.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def _emit(payload: dict[str, Any], *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    default_repo_root = Path(args.repo_root).expanduser().resolve()
    if not default_repo_root.exists() or not default_repo_root.is_dir():
        _emit({"error": f"Invalid repo root: {default_repo_root}"}, pretty=args.pretty)
        return 1

    if args.health:
        _emit(_health_payload(default_repo_root), pretty=args.pretty)
        return 0

    try:
        payload = _load_payload(args)
        query, repo_scope, top_k, include_snippets = _parse_request(payload)

        registry = EngineRegistry(default_repo_root)
        engine, _ = registry.get_engine(repo_scope)
        result = engine.query(query, limit=top_k)

        response = _normalize_response(
            result,
            include_snippets=include_snippets,
            top_k=top_k,
        )
        _emit(response, pretty=args.pretty)
        return 0
    except ValueError as exc:
        _emit({"error": str(exc)}, pretty=args.pretty)
        return 2
    except RuntimeError as exc:
        _emit({"error": str(exc)}, pretty=args.pretty)
        return 3
    except Exception as exc:  # pragma: no cover
        _emit({"error": f"Internal error: {exc}"}, pretty=args.pretty)
        return 99


if __name__ == "__main__":
    raise SystemExit(main())
