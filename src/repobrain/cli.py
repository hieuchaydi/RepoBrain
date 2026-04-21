from __future__ import annotations

import argparse
import getpass
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

# Allow direct script execution from a source checkout:
# `python src/repobrain/cli.py ...`
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    src_root = Path(__file__).resolve().parents[1]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from repobrain.active_repo import read_active_repo, resolve_repo_root, write_active_repo
from repobrain.cleanup import cleanup_demo_artifacts
from repobrain.file_context import attach_file_context, build_file_context, file_paths_from_context
from repobrain.prompt_pack import SOURCE_CHOICES as PROMPT_SOURCE_CHOICES
from repobrain.prompt_pack import STYLE_CHOICES as PROMPT_STYLE_CHOICES
from repobrain.workspace import (
    add_workspace_project,
    clear_workspace_notes,
    project_context_hint,
    remember_file_context,
    remember_query_result,
    remember_workspace_note,
    set_current_workspace_project,
    workspace_projects_payload,
    workspace_query_payload,
    workspace_summary_payload,
)


if TYPE_CHECKING:
    from repobrain.engine.core import RepoBrainEngine
    from repobrain.models import QueryResult, ReviewFocus


REVIEW_FOCUS_CHOICES = ("full", "security", "production", "quality")
# Keep these defaults in sync with repobrain.provider_setup.
DEFAULT_GEMINI_MODEL_POOL_TEXT = "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3-flash-preview"
DEFAULT_GROQ_MODEL_POOL_TEXT = "llama-3.3-70b-versatile,openai/gpt-oss-20b"


@dataclass
class ChatSessionState:
    focus: str | None = None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repobrain", description="Local-first codebase memory and grounding harness.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create RepoBrain state directories and a default repobrain.toml.")
    init_parser.add_argument("--repo", default=None)
    init_parser.add_argument("--force", action="store_true")
    _add_format_argument(init_parser)

    index_parser = subparsers.add_parser("index", help="Index the repository into .repobrain/metadata.db and vectors.")
    index_parser.add_argument("--repo", default=None)
    _add_format_argument(index_parser)

    for command, aliases, help_text in (
        ("query", ("ask",), "Ask a grounded question and return cited files."),
        ("trace", ("map",), "Map a likely flow through routes, services, or jobs."),
        ("impact", ("blast",), "Estimate impacted files and dependency edges."),
        ("targets", ("plan",), "Plan likely edit targets with evidence."),
    ):
        command_parser = subparsers.add_parser(command, aliases=list(aliases), help=help_text)
        command_parser.add_argument("query")
        command_parser.add_argument("--repo", default=None)
        _add_format_argument(command_parser)

    review_parser = subparsers.add_parser("review", help="Scan the repo and summarize the biggest security, production, and code-quality gaps.")
    review_parser.add_argument("--repo", default=None)
    review_parser.add_argument("--focus", choices=REVIEW_FOCUS_CHOICES, default=REVIEW_FOCUS_CHOICES[0])
    _add_format_argument(review_parser)

    baseline_parser = subparsers.add_parser("baseline", help="Save the current project review as a named baseline snapshot.")
    baseline_parser.add_argument("--repo", default=None)
    baseline_parser.add_argument("--label", default="baseline")
    baseline_parser.add_argument("--focus", choices=REVIEW_FOCUS_CHOICES, default=REVIEW_FOCUS_CHOICES[0])
    _add_format_argument(baseline_parser)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the built-in benchmark cases against the current index.")
    benchmark_parser.add_argument("--repo", default=None)
    _add_format_argument(benchmark_parser)

    patch_review_parser = subparsers.add_parser(
        "patch-review",
        help="Review the current patch and surface adjacent files, tests, config touchpoints, and risk warnings.",
    )
    patch_review_parser.add_argument("--repo", default=None)
    patch_review_parser.add_argument("--base", default=None)
    patch_review_parser.add_argument("--files", nargs="+", default=None)
    _add_format_argument(patch_review_parser)

    ship_parser = subparsers.add_parser("ship", help="Run the production-readiness gate across index health, review findings, providers, parsers, and benchmark.")
    ship_parser.add_argument("--repo", default=None)
    ship_parser.add_argument("--baseline-label", default="baseline")
    _add_format_argument(ship_parser)

    prompt_parser = subparsers.add_parser(
        "prompt",
        help="Generate focused fix prompts from review, ship, patch-review, or import evidence.",
    )
    prompt_parser.add_argument("--repo", default=None)
    prompt_parser.add_argument("--source", choices=PROMPT_SOURCE_CHOICES, default="review")
    prompt_parser.add_argument("--style", choices=PROMPT_STYLE_CHOICES, default="generic")
    prompt_parser.add_argument("--max-prompts", type=int, default=6)
    prompt_parser.add_argument("--focus", choices=REVIEW_FOCUS_CHOICES, default=REVIEW_FOCUS_CHOICES[0])
    prompt_parser.add_argument("--baseline-label", default="baseline")
    prompt_parser.add_argument("--base", default=None)
    prompt_parser.add_argument("--files", nargs="+", default=None)
    _add_format_argument(prompt_parser)

    doctor_parser = subparsers.add_parser("doctor", aliases=["check"], help="Inspect local RepoBrain configuration and index health.")
    doctor_parser.add_argument("--repo", default=None)
    _add_format_argument(doctor_parser)

    smoke_parser = subparsers.add_parser(
        "provider-smoke",
        aliases=["smoke"],
        help="Run a live smoke check through the configured embedding and reranker providers.",
    )
    smoke_parser.add_argument("--repo", default=None)
    _add_format_argument(smoke_parser)

    key_parser = subparsers.add_parser("key", help="Configure provider API keys and provider defaults.")
    key_subparsers = key_parser.add_subparsers(dest="key_provider", required=True)
    gemini_key_parser = key_subparsers.add_parser("gemini", help="Save a Gemini API key and enable Gemini providers.")
    gemini_key_parser.add_argument("--repo", default=None)
    gemini_key_parser.add_argument("--api-key", default=None, help="Gemini API key. Omit to prompt without echo.")
    gemini_key_parser.add_argument("--no-embedding", action="store_true", help="Keep embedding provider local.")
    gemini_key_parser.add_argument("--no-reranker", action="store_true", help="Keep reranker provider local.")
    gemini_key_parser.add_argument("--embedding-model", default="gemini-embedding-001")
    gemini_key_parser.add_argument("--output-dimensionality", default="768")
    gemini_key_parser.add_argument("--task-type", default="SEMANTIC_SIMILARITY")
    gemini_key_parser.add_argument("--rerank-model", default="gemini-2.5-flash")
    gemini_key_parser.add_argument("--model-pool", default=DEFAULT_GEMINI_MODEL_POOL_TEXT)
    _add_format_argument(gemini_key_parser)
    groq_key_parser = key_subparsers.add_parser("groq", help="Save a Groq API key and enable Groq reranking.")
    groq_key_parser.add_argument("--repo", default=None)
    groq_key_parser.add_argument("--api-key", default=None, help="Groq API key. Omit to prompt without echo.")
    groq_key_parser.add_argument("--no-reranker", action="store_true", help="Keep reranker provider local.")
    groq_key_parser.add_argument("--rerank-model", default="llama-3.3-70b-versatile")
    groq_key_parser.add_argument("--model-pool", default=DEFAULT_GROQ_MODEL_POOL_TEXT)
    _add_format_argument(groq_key_parser)

    chat_parser = subparsers.add_parser("chat", help="Start an interactive local RepoBrain question loop.")
    chat_parser.add_argument("--repo", default=None)

    workspace_parser = subparsers.add_parser("workspace", help="Manage tracked repos and persisted repo memory.")
    workspace_subparsers = workspace_parser.add_subparsers(dest="workspace_command", required=True)

    workspace_list_parser = workspace_subparsers.add_parser("list", help="List tracked repos and show the active one.")
    _add_format_argument(workspace_list_parser)

    workspace_add_parser = workspace_subparsers.add_parser("add", help="Track a repo for later chat and cross-repo queries.")
    workspace_add_parser.add_argument("repo")
    workspace_add_parser.add_argument("--no-activate", action="store_true", help="Track the repo without making it active.")
    _add_format_argument(workspace_add_parser)

    workspace_use_parser = workspace_subparsers.add_parser("use", help="Switch the active tracked repo.")
    workspace_use_parser.add_argument("project")
    _add_format_argument(workspace_use_parser)

    workspace_summary_parser = workspace_subparsers.add_parser("summary", help="Show stored summary memory for a tracked repo.")
    workspace_summary_parser.add_argument("project", nargs="?")
    _add_format_argument(workspace_summary_parser)

    workspace_remember_parser = workspace_subparsers.add_parser("remember", help="Persist a manual note for a tracked repo.")
    workspace_remember_parser.add_argument("note")
    workspace_remember_parser.add_argument("--project", default=None)
    _add_format_argument(workspace_remember_parser)

    workspace_clear_parser = workspace_subparsers.add_parser("clear-notes", help="Clear manual notes for a tracked repo.")
    workspace_clear_parser.add_argument("--project", default=None)
    _add_format_argument(workspace_clear_parser)

    report_parser = subparsers.add_parser("report", help="Generate a local HTML status report.")
    report_parser.add_argument("--repo", default=None)
    report_parser.add_argument("--output", default=None)
    report_parser.add_argument("--baseline-label", default="baseline")
    report_parser.add_argument("--open", action="store_true", dest="open_report", help="Open the generated report in the default browser.")
    _add_format_argument(report_parser)

    release_parser = subparsers.add_parser("release-check", help="Inspect release versions, frontend assets, and built wheel/sdist contents.")
    release_parser.add_argument("--repo", default=None)
    release_parser.add_argument("--require-dist", action="store_true", help="Fail if wheel and sdist artifacts are missing.")
    _add_format_argument(release_parser)

    clean_parser = subparsers.add_parser("demo-clean", help="Remove local test/build clutter while keeping the built browser UI ready for demos.")
    clean_parser.add_argument("--repo", default=None)
    clean_parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting anything.")
    clean_parser.add_argument("--keep-dist", action="store_true", help="Preserve root dist/ artifacts.")
    clean_parser.add_argument("--include-state", action="store_true", help="Also remove the root .repobrain workspace state.")
    _add_format_argument(clean_parser)

    first_look_parser = subparsers.add_parser(
        "first-look",
        aliases=["start"],
        help="Run the lowest-friction local demo: init, index, starter questions, and an optional report.",
    )
    _add_first_look_arguments(first_look_parser)

    demo_parser = subparsers.add_parser("demo", help="Alias for `first-look`, optimized for a shareable local demo run.")
    _add_first_look_arguments(demo_parser)

    subparsers.add_parser("quickstart", help="Print the shortest path from install to first query.")

    mcp_parser = subparsers.add_parser("serve-mcp", help="Serve RepoBrain tools over a stdio JSON transport.")
    mcp_parser.add_argument("--repo", default=None)

    web_parser = subparsers.add_parser(
        "serve-web",
        aliases=["ui"],
        help="Serve a local browser UI for import, index, and query flows.",
    )
    web_parser.add_argument("--repo", default=None)
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8765)
    web_parser.add_argument("--open", action="store_true", dest="open_browser", help="Open the browser UI after the server starts.")
    return parser


def _add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format. Defaults to json.")


def _add_first_look_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=None)
    parser.add_argument("--report-output", default=None, help="Optional output path for the generated HTML report.")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation and only print the first-look summary.")
    parser.add_argument("--open-report", action="store_true", help="Open the generated local HTML report after the run.")
    _add_format_argument(parser)


def _canonical_command(command: str) -> str:
    return {
        "ask": "query",
        "map": "trace",
        "blast": "impact",
        "plan": "targets",
        "check": "doctor",
        "smoke": "provider-smoke",
        "start": "first-look",
        "ui": "serve-web",
    }.get(command, command)


def _dump(payload: object, output_format: str = "json") -> None:
    from repobrain.ux import payload_to_json, payload_to_text

    if output_format == "text":
        print(payload_to_text(payload, styled=True))
        return
    print(payload_to_json(payload))


def _resolve_gemini_api_key(api_key: str | None) -> str:
    return _resolve_provider_api_key(api_key, provider_label="Gemini")


def _resolve_groq_api_key(api_key: str | None) -> str:
    return _resolve_provider_api_key(api_key, provider_label="Groq")


def _resolve_provider_api_key(api_key: str | None, *, provider_label: str) -> str:
    if api_key is not None:
        resolved = api_key.strip()
    else:
        try:
            resolved = getpass.getpass(f"{provider_label} API key: ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            print()
            raise ValueError(f"{provider_label} API key was not provided.") from exc
    if not resolved:
        raise ValueError(f"{provider_label} API key was empty.")
    return resolved


def _warn_if_using_active_repo(args: argparse.Namespace, repo_root: Path) -> None:
    if getattr(args, "repo", None) or getattr(args, "command", "") == "init":
        return

    cwd = Path.cwd().resolve()
    if repo_root == cwd:
        return

    sys.stderr.write(
        "RepoBrain notice: using the saved active repo "
        f"`{repo_root}` instead of the current directory `{cwd}`. "
        "Pass `--repo .` to use the current directory or run `repobrain workspace use <repo>` to switch.\n"
    )


def _configure_gemini_key(
    repo_root: str | Path,
    *,
    api_key: str | None,
    use_embedding: bool = True,
    use_reranker: bool = True,
    embedding_model: str = "gemini-embedding-001",
    output_dimensionality: str = "768",
    task_type: str = "SEMANTIC_SIMILARITY",
    rerank_model: str = "gemini-2.5-flash",
    model_pool: str = DEFAULT_GEMINI_MODEL_POOL_TEXT,
) -> dict[str, object]:
    from repobrain.provider_setup import configure_gemini_provider

    return configure_gemini_provider(
        repo_root,
        api_key=_resolve_gemini_api_key(api_key),
        use_embedding=use_embedding,
        use_reranker=use_reranker,
        embedding_model=embedding_model,
        output_dimensionality=output_dimensionality,
        task_type=task_type,
        rerank_model=rerank_model,
        model_pool=model_pool,
    )


def _configure_groq_key(
    repo_root: str | Path,
    *,
    api_key: str | None,
    use_reranker: bool = True,
    rerank_model: str = "llama-3.3-70b-versatile",
    model_pool: str = DEFAULT_GROQ_MODEL_POOL_TEXT,
) -> dict[str, object]:
    from repobrain.provider_setup import configure_groq_provider

    return configure_groq_provider(
        repo_root,
        api_key=_resolve_groq_api_key(api_key),
        use_reranker=use_reranker,
        rerank_model=rerank_model,
        model_pool=model_pool,
    )


def _chat_key_payload(raw_query: str, repo_root: Path) -> dict[str, object]:
    command_tail = raw_query.removeprefix("/key").strip()
    api_key: str | None = None
    provider = "gemini"
    if command_tail:
        provider, _, value = command_tail.partition(" ")
        api_key = value.strip() or None
    provider = provider.lower()
    if provider == "gemini":
        return _configure_gemini_key(repo_root, api_key=api_key)
    if provider == "groq":
        return _configure_groq_key(repo_root, api_key=api_key)
    raise ValueError("Use `/key gemini` or `/key groq`.")


def _build_and_remember_file_context(repo_root: Path, payload: object, *, action_label: str) -> dict[str, object] | None:
    file_context = build_file_context(payload, action_label=action_label)
    paths = file_paths_from_context(file_context)
    if not file_context or not paths:
        return None
    summary = remember_file_context(
        repo_root,
        files=paths,
        warnings=[str(item) for item in file_context.get("warnings", [])],
        next_questions=[str(item) for item in file_context.get("next_steps", [])],
    )
    file_context["memory_updated"] = True
    file_context["memory_summary"] = str(summary.get("summary", "")).strip()
    return file_context


def _dump_with_file_context(repo_root: Path, payload: object, output_format: str, *, action_label: str) -> None:
    file_context = _build_and_remember_file_context(repo_root, payload, action_label=action_label)
    if output_format == "text":
        _dump(payload, output_format)
        if file_context:
            print()
            _dump(file_context, output_format)
        return
    _dump(attach_file_context(payload, file_context), output_format)


def _chat_focus_status(state: ChatSessionState) -> str:
    return f"Active focus: {state.focus}" if state.focus else "Active focus: none"


def _chat_context(repo_root: Path, state: ChatSessionState) -> str | None:
    return project_context_hint(repo_root, focus=state.focus)


def _handle_focus_command(raw_query: str, state: ChatSessionState) -> str:
    focus_value = raw_query.removeprefix("/focus").strip()
    if not focus_value:
        return _chat_focus_status(state)
    if focus_value.lower() in {"clear", "none", "off", "reset"}:
        state.focus = None
        return "Focus cleared."
    state.focus = focus_value
    return _chat_focus_status(state)


def _review_focus(value: str) -> "ReviewFocus":
    from repobrain.models import ReviewFocus

    return ReviewFocus(value)


def _run_chat_query(engine: "RepoBrainEngine", query: str, *, state: ChatSessionState, mode: str = "query") -> "QueryResult":
    context = _chat_context(engine.config.resolved_repo_root, state)
    if mode == "trace":
        result = engine.trace(query, context=context)
    elif mode == "impact":
        result = engine.impact(query, context=context)
    elif mode == "targets":
        result = engine.targets(query, context=context)
    else:
        result = engine.query(query, context=context)
    remember_query_result(engine.config.resolved_repo_root, query=query, result=result)
    return result


def _chat(engine: "RepoBrainEngine") -> int:
    from repobrain.engine.core import RepoBrainEngine
    from repobrain.ux import build_report, chat_help_text, chat_intro, chat_prompt, render_cli_wordmark

    output_format = "text"
    current_engine = engine
    repo_root = current_engine.config.resolved_repo_root
    add_workspace_project(repo_root, make_current=True)
    session_state = ChatSessionState()
    print(render_cli_wordmark())
    print()
    print(chat_intro(repo_root, styled=True))
    print()
    while True:
        try:
            raw_query = input(chat_prompt(repo_root)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw_query:
            continue
        lowered = raw_query.lower()
        if lowered in {"/exit", "exit", "quit", ":q"}:
            return 0
        if lowered == "/help":
            print(chat_help_text(styled=True))
            continue
        if lowered == "/focus" or raw_query.startswith("/focus "):
            print(_handle_focus_command(raw_query, session_state))
            continue
        if lowered == "/key" or raw_query.startswith("/key "):
            try:
                payload = _chat_key_payload(raw_query, repo_root)
                current_engine = RepoBrainEngine(repo_root)
                _dump(payload, output_format)
            except Exception as exc:
                _dump({"error": str(exc), "hint": "Use `/key gemini` or `/key groq` to add a provider API key."}, output_format)
            continue
        if lowered == "/projects":
            _dump(workspace_projects_payload(), output_format)
            continue
        if lowered == "/summary":
            _dump(workspace_summary_payload(repo_root), output_format)
            continue
        if lowered == "/remember clear":
            _dump(clear_workspace_notes(repo_root), output_format)
            continue
        if lowered.startswith("/remember "):
            _dump(remember_workspace_note(raw_query.removeprefix("/remember ").strip(), repo_root), output_format)
            continue
        if lowered.startswith("/add "):
            added_repo = Path(raw_query.removeprefix("/add ").strip()).expanduser().resolve()
            _dump(add_workspace_project(added_repo), output_format)
            write_active_repo(added_repo)
            continue
        if lowered.startswith("/use "):
            project_ref = raw_query.removeprefix("/use ").strip()
            payload = set_current_workspace_project(project_ref)
            selected_repo = Path(str(payload.get("current_repo", ""))).expanduser().resolve()
            current_engine = RepoBrainEngine(selected_repo)
            repo_root = selected_repo
            write_active_repo(selected_repo)
            print(chat_intro(repo_root, styled=True))
            print()
            _dump(payload, output_format)
            continue
        if lowered.startswith("/multi "):
            multi_query = raw_query.removeprefix("/multi ").strip()
            payload = workspace_query_payload(
                multi_query,
                current_repo=repo_root,
                context=_chat_context(repo_root, session_state),
                engine_factory=RepoBrainEngine,
                focus=session_state.focus,
            )
            _dump(payload, output_format)
            continue
        if lowered == "/json":
            output_format = "json"
            print("Output mode: json")
            continue
        if lowered == "/text":
            output_format = "text"
            print("Output mode: text")
            continue

        try:
            if lowered == "/doctor":
                _dump(current_engine.doctor(), output_format)
            elif lowered == "/provider-smoke":
                _dump(current_engine.provider_smoke(), output_format)
            elif lowered == "/index":
                _dump(current_engine.index_repository(), output_format)
            elif lowered == "/review":
                _dump(current_engine.review(), output_format)
            elif lowered == "/baseline":
                report = current_engine.review(compare_baseline=False)
                _dump(current_engine.save_review_baseline(report), output_format)
            elif lowered == "/ship":
                _dump(current_engine.ship(), output_format)
            elif lowered == "/report":
                report_path = build_report(current_engine)
                print(f"RepoBrain report written to: {report_path}")
            elif raw_query.startswith("/evidence "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/evidence ").strip(), state=session_state), output_format)
            elif raw_query.startswith("/map "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/map ").strip(), state=session_state, mode="trace"), output_format)
            elif raw_query.startswith("/query "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/query ").strip(), state=session_state), output_format)
            elif raw_query.startswith("/trace "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/trace ").strip(), state=session_state, mode="trace"), output_format)
            elif raw_query.startswith("/impact "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/impact ").strip(), state=session_state, mode="impact"), output_format)
            elif raw_query.startswith("/targets "):
                _dump(_run_chat_query(current_engine, raw_query.removeprefix("/targets ").strip(), state=session_state, mode="targets"), output_format)
            else:
                _dump(_run_chat_query(current_engine, raw_query, state=session_state), output_format)
        except Exception as exc:
            _dump({"error": str(exc), "hint": "Run /index if the repository has not been indexed yet."}, output_format)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    args.command = _canonical_command(args.command)

    if args.command == "quickstart":
        from repobrain.ux import quickstart_text

        print(quickstart_text(styled=True))
        return 0
    if args.command == "workspace":
        workspace_format = getattr(args, "format", "json")
        if args.workspace_command == "list":
            _dump(workspace_projects_payload(), workspace_format)
            return 0
        if args.workspace_command == "add":
            payload = add_workspace_project(args.repo, make_current=not args.no_activate)
            if not args.no_activate:
                write_active_repo(Path(args.repo).expanduser().resolve())
            _dump(payload, workspace_format)
            return 0
        if args.workspace_command == "use":
            payload = set_current_workspace_project(args.project)
            write_active_repo(Path(str(payload.get("current_repo", ""))).expanduser().resolve())
            _dump(payload, workspace_format)
            return 0
        if args.workspace_command == "summary":
            _dump(workspace_summary_payload(args.project), workspace_format)
            return 0
        if args.workspace_command == "remember":
            _dump(remember_workspace_note(args.note, args.project), workspace_format)
            return 0
        if args.workspace_command == "clear-notes":
            _dump(clear_workspace_notes(args.project), workspace_format)
            return 0
        parser.error(f"Unsupported workspace command: {args.workspace_command}")
        return 2

    if args.command == "release-check":
        from repobrain.release import inspect_release_artifacts

        project_root = Path(args.repo).expanduser().resolve() if args.repo else Path.cwd()
        payload = inspect_release_artifacts(project_root, require_dist=args.require_dist)
        _dump(payload, getattr(args, "format", "json"))
        return 1 if payload.get("status") == "fail" else 0
    if args.command == "demo-clean":
        project_root = Path(args.repo).expanduser().resolve() if args.repo else Path.cwd()
        payload = cleanup_demo_artifacts(
            project_root,
            dry_run=args.dry_run,
            include_dist=not args.keep_dist,
            include_state=args.include_state,
        )
        _dump(payload, getattr(args, "format", "json"))
        return 0

    repo_root = resolve_repo_root(getattr(args, "repo", None), prefer_active=args.command != "init")
    _warn_if_using_active_repo(args, repo_root)
    if args.command == "patch-review" and args.base and args.files:
        parser.error("`patch-review` accepts either `--base` or `--files`, not both.")
        return 2
    if args.command == "prompt":
        if args.source == "patch-review" and args.base and args.files:
            parser.error("`prompt --source patch-review` accepts either `--base` or `--files`, not both.")
            return 2
        if args.source != "patch-review" and (args.base or args.files):
            parser.error("`--base` and `--files` are only supported with `prompt --source patch-review`.")
            return 2

    if args.command == "serve-mcp":
        from repobrain.mcp_server import serve_mcp

        return serve_mcp(str(repo_root))
    if args.command == "serve-web":
        from repobrain.web import serve_web

        explicit_repo = getattr(args, "repo", None)
        initial_repo = ""
        if explicit_repo:
            initial_repo = str(Path(explicit_repo).expanduser().resolve())
        else:
            active_repo = read_active_repo()
            if active_repo is not None:
                initial_repo = str(active_repo)
        return serve_web(repo_root=initial_repo, host=args.host, port=args.port, open_browser=args.open_browser)
    if args.command == "key":
        if args.key_provider == "gemini":
            try:
                payload = _configure_gemini_key(
                    repo_root,
                    api_key=args.api_key,
                    use_embedding=not args.no_embedding,
                    use_reranker=not args.no_reranker,
                    embedding_model=args.embedding_model,
                    output_dimensionality=args.output_dimensionality,
                    task_type=args.task_type,
                    rerank_model=args.rerank_model,
                    model_pool=args.model_pool,
                )
            except ValueError as exc:
                parser.error(str(exc))
                return 2
            _dump(payload, getattr(args, "format", "json"))
            return 0
        if args.key_provider == "groq":
            try:
                payload = _configure_groq_key(
                    repo_root,
                    api_key=args.api_key,
                    use_reranker=not args.no_reranker,
                    rerank_model=args.rerank_model,
                    model_pool=args.model_pool,
                )
            except ValueError as exc:
                parser.error(str(exc))
                return 2
            _dump(payload, getattr(args, "format", "json"))
            return 0
        parser.error(f"Unsupported key provider: {args.key_provider}")
        return 2

    from repobrain.engine.core import RepoBrainEngine

    engine = RepoBrainEngine(repo_root)
    output_format = getattr(args, "format", "json")

    if args.command in {"first-look", "demo"}:
        from repobrain.first_look import run_first_look

        if args.open_report and args.no_report:
            parser.error("`--open-report` cannot be used with `--no-report`.")
            return 2
        payload = run_first_look(
            repo_root,
            report_output=args.report_output,
            include_report=not args.no_report,
        )
        report_path = str(payload.get("report_path", "")).strip()
        if args.open_report and report_path:
            webbrowser.open(Path(report_path).expanduser().resolve().as_uri())
        _dump(payload, output_format)
        return 0

    if args.command == "init":
        payload = engine.init_workspace(force=args.force)
        write_active_repo(repo_root)
        payload["active_repo"] = str(repo_root)
        _dump(payload, output_format)
        return 0
    if args.command == "index":
        _dump(engine.index_repository(), output_format)
        return 0
    if args.command == "query":
        _dump_with_file_context(repo_root, engine.query(args.query), output_format, action_label="query")
        return 0
    if args.command == "trace":
        _dump_with_file_context(repo_root, engine.trace(args.query), output_format, action_label="trace")
        return 0
    if args.command == "impact":
        _dump_with_file_context(repo_root, engine.impact(args.query), output_format, action_label="impact")
        return 0
    if args.command == "targets":
        _dump_with_file_context(repo_root, engine.targets(args.query), output_format, action_label="targets")
        return 0
    if args.command == "benchmark":
        _dump(engine.benchmark(), output_format)
        return 0
    if args.command == "patch-review":
        _dump_with_file_context(
            repo_root,
            engine.patch_review(base=args.base, files=args.files),
            output_format,
            action_label="patch-review",
        )
        return 0
    if args.command == "prompt":
        _dump(
            engine.prompt_pack(
                source=args.source,
                focus=_review_focus(args.focus),
                baseline_label=args.baseline_label,
                base=args.base,
                files=args.files,
                style=args.style,
                max_prompts=args.max_prompts,
            ),
            output_format,
        )
        return 0
    if args.command == "ship":
        _dump_with_file_context(repo_root, engine.ship(baseline_label=args.baseline_label), output_format, action_label="ship")
        return 0
    if args.command == "doctor":
        _dump(engine.doctor(), output_format)
        return 0
    if args.command == "provider-smoke":
        _dump(engine.provider_smoke(), output_format)
        return 0
    if args.command == "review":
        _dump_with_file_context(
            repo_root,
            engine.review(focus=_review_focus(args.focus)),
            output_format,
            action_label="review",
        )
        return 0
    if args.command == "baseline":
        report = engine.review(focus=_review_focus(args.focus), compare_baseline=False)
        _dump(engine.save_review_baseline(report, label=args.label), output_format)
        return 0
    if args.command == "chat":
        return _chat(engine)
    if args.command == "report":
        from repobrain.ux import build_report

        report_path = build_report(engine, args.output, baseline_label=args.baseline_label)
        if args.open_report:
            webbrowser.open(report_path.resolve().as_uri())
        payload = {"report_path": str(report_path), "repo_root": str(repo_root), "opened": bool(args.open_report)}
        _dump(payload, output_format)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
