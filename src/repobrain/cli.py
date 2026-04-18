from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from repobrain.active_repo import read_active_repo, resolve_repo_root, write_active_repo
from repobrain.cleanup import cleanup_demo_artifacts
from repobrain.engine.core import RepoBrainEngine
from repobrain.mcp_server import serve_mcp
from repobrain.models import ReviewFocus
from repobrain.release import inspect_release_artifacts
from repobrain.web import serve_web
from repobrain.ux import build_report, payload_to_json, payload_to_text, quickstart_text


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

    for command, help_text in (
        ("query", "Run a grounded retrieval query."),
        ("trace", "Trace a likely flow through routes, services, or jobs."),
        ("impact", "Estimate impacted files and dependency edges."),
        ("targets", "Rank suggested edit targets."),
    ):
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument("query")
        command_parser.add_argument("--repo", default=None)
        _add_format_argument(command_parser)

    review_parser = subparsers.add_parser("review", help="Scan the repo and summarize the biggest security, production, and code-quality gaps.")
    review_parser.add_argument("--repo", default=None)
    review_parser.add_argument("--focus", choices=tuple(item.value for item in ReviewFocus), default=ReviewFocus.FULL.value)
    _add_format_argument(review_parser)

    baseline_parser = subparsers.add_parser("baseline", help="Save the current project review as a named baseline snapshot.")
    baseline_parser.add_argument("--repo", default=None)
    baseline_parser.add_argument("--label", default="baseline")
    baseline_parser.add_argument("--focus", choices=tuple(item.value for item in ReviewFocus), default=ReviewFocus.FULL.value)
    _add_format_argument(baseline_parser)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the built-in benchmark cases against the current index.")
    benchmark_parser.add_argument("--repo", default=None)
    _add_format_argument(benchmark_parser)

    ship_parser = subparsers.add_parser("ship", help="Run the production-readiness gate across index health, review findings, providers, parsers, and benchmark.")
    ship_parser.add_argument("--repo", default=None)
    ship_parser.add_argument("--baseline-label", default="baseline")
    _add_format_argument(ship_parser)

    doctor_parser = subparsers.add_parser("doctor", help="Inspect local RepoBrain configuration and index health.")
    doctor_parser.add_argument("--repo", default=None)
    _add_format_argument(doctor_parser)

    smoke_parser = subparsers.add_parser("provider-smoke", help="Run a live smoke check through the configured embedding and reranker providers.")
    smoke_parser.add_argument("--repo", default=None)
    _add_format_argument(smoke_parser)

    chat_parser = subparsers.add_parser("chat", help="Start an interactive local RepoBrain question loop.")
    chat_parser.add_argument("--repo", default=None)

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

    subparsers.add_parser("quickstart", help="Print the shortest path from install to first query.")

    mcp_parser = subparsers.add_parser("serve-mcp", help="Serve RepoBrain tools over a stdio JSON transport.")
    mcp_parser.add_argument("--repo", default=None)

    web_parser = subparsers.add_parser("serve-web", help="Serve a local browser UI for import, index, and query flows.")
    web_parser.add_argument("--repo", default=None)
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8765)
    web_parser.add_argument("--open", action="store_true", dest="open_browser", help="Open the browser UI after the server starts.")
    return parser


def _add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format. Defaults to json.")


def _dump(payload: object, output_format: str = "json") -> None:
    if output_format == "text":
        print(payload_to_text(payload))
        return
    print(payload_to_json(payload))


def _chat(engine: RepoBrainEngine) -> int:
    output_format = "text"
    print("RepoBrain chat is local-only. Type /help for commands, /json for raw payloads, or /exit to quit.")
    while True:
        try:
            raw_query = input("repobrain> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw_query:
            continue
        lowered = raw_query.lower()
        if lowered in {"/exit", "exit", "quit", ":q"}:
            return 0
        if lowered == "/help":
            print("Commands: /trace <q>, /impact <q>, /targets <q>, /doctor, /provider-smoke, /index, /review, /baseline, /ship, /report, /json, /text, /exit")
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
                _dump(engine.doctor(), output_format)
            elif lowered == "/provider-smoke":
                _dump(engine.provider_smoke(), output_format)
            elif lowered == "/index":
                _dump(engine.index_repository(), output_format)
            elif lowered == "/review":
                _dump(engine.review(), output_format)
            elif lowered == "/baseline":
                report = engine.review(compare_baseline=False)
                _dump(engine.save_review_baseline(report), output_format)
            elif lowered == "/ship":
                _dump(engine.ship(), output_format)
            elif lowered == "/report":
                report_path = build_report(engine)
                print(f"RepoBrain report written to: {report_path}")
            elif raw_query.startswith("/trace "):
                _dump(engine.trace(raw_query.removeprefix("/trace ").strip()), output_format)
            elif raw_query.startswith("/impact "):
                _dump(engine.impact(raw_query.removeprefix("/impact ").strip()), output_format)
            elif raw_query.startswith("/targets "):
                _dump(engine.targets(raw_query.removeprefix("/targets ").strip()), output_format)
            else:
                _dump(engine.query(raw_query), output_format)
        except Exception as exc:
            _dump({"error": str(exc), "hint": "Run /index if the repository has not been indexed yet."}, output_format)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command == "quickstart":
        print(quickstart_text())
        return 0

    if args.command == "release-check":
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

    if args.command == "serve-mcp":
        return serve_mcp(str(repo_root))
    if args.command == "serve-web":
        explicit_repo = getattr(args, "repo", None)
        initial_repo = ""
        if explicit_repo:
            initial_repo = str(Path(explicit_repo).expanduser().resolve())
        else:
            active_repo = read_active_repo()
            if active_repo is not None:
                initial_repo = str(active_repo)
        return serve_web(repo_root=initial_repo, host=args.host, port=args.port, open_browser=args.open_browser)

    engine = RepoBrainEngine(repo_root)
    output_format = getattr(args, "format", "json")

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
        _dump(engine.query(args.query), output_format)
        return 0
    if args.command == "trace":
        _dump(engine.trace(args.query), output_format)
        return 0
    if args.command == "impact":
        _dump(engine.impact(args.query), output_format)
        return 0
    if args.command == "targets":
        _dump(engine.targets(args.query), output_format)
        return 0
    if args.command == "benchmark":
        _dump(engine.benchmark(), output_format)
        return 0
    if args.command == "ship":
        _dump(engine.ship(baseline_label=args.baseline_label), output_format)
        return 0
    if args.command == "doctor":
        _dump(engine.doctor(), output_format)
        return 0
    if args.command == "provider-smoke":
        _dump(engine.provider_smoke(), output_format)
        return 0
    if args.command == "review":
        _dump(engine.review(focus=ReviewFocus(args.focus)), output_format)
        return 0
    if args.command == "baseline":
        report = engine.review(focus=ReviewFocus(args.focus), compare_baseline=False)
        _dump(engine.save_review_baseline(report, label=args.label), output_format)
        return 0
    if args.command == "chat":
        return _chat(engine)
    if args.command == "report":
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
