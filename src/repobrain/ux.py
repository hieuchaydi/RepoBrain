from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repobrain.engine.core import RepoBrainEngine
from repobrain.models import QueryResult, ReviewReport, ShipReport


def payload_to_json(payload: object) -> str:
    if hasattr(payload, "to_dict"):
        return json.dumps(payload.to_dict(), indent=2)
    return json.dumps(payload, indent=2)


def payload_to_text(payload: object, *, styled: bool = False) -> str:
    text = _payload_to_text_plain(payload)
    return _style_terminal_block(text) if styled else text


def _payload_to_text_plain(payload: object) -> str:
    if isinstance(payload, QueryResult):
        return query_result_to_text(payload)
    if isinstance(payload, ReviewReport):
        return review_to_text(payload)
    if isinstance(payload, ShipReport):
        return ship_to_text(payload)
    if hasattr(payload, "to_dict"):
        payload = payload.to_dict()
    if isinstance(payload, dict):
        if "embedding_smoke" in payload and "reranker_smoke" in payload:
            return provider_smoke_to_text(payload)
        if payload.get("kind") == "workspace_projects":
            return workspace_projects_to_text(payload)
        if payload.get("kind") == "workspace_summary":
            return workspace_summary_to_text(payload)
        if payload.get("kind") == "workspace_query":
            return workspace_query_to_text(payload)
        if payload.get("kind") == "demo_clean":
            return demo_clean_to_text(payload)
        if payload.get("kind") == "release_check":
            return release_check_to_text(payload)
        if "baseline_path" in payload:
            return "\n".join(
                [
                    "RepoBrain Baseline Saved",
                    f"Label: {payload.get('label')}",
                    f"Baseline: {payload.get('baseline_path')}",
                    f"History snapshot: {payload.get('history_path')}",
                ]
            )
        if "report_path" in payload:
            return "\n".join(
                [
                    "RepoBrain Report",
                    f"Written to: {payload.get('report_path')}",
                    "",
                    "Open the file in a browser to view the local dashboard.",
                ]
            )
        if "provider_status" in payload and "security" in payload:
            return doctor_to_text(payload)
        if {"repo_root", "config_path", "state_dir"}.issubset(payload):
            lines = [
                "RepoBrain Workspace Ready",
                f"Repo: {payload.get('repo_root')}",
                f"Config: {payload.get('config_path')}",
                f"State: {payload.get('state_dir')}",
            ]
            if payload.get("active_repo"):
                lines.append(f"Active repo: {payload.get('active_repo')}")
            lines.extend(["", "Next: repobrain index --format text"])
            return "\n".join(lines)
        if {"files", "chunks", "symbols", "edges"}.issubset(payload):
            return index_stats_to_text(payload)
        if {"recall_at_3", "mrr", "citation_accuracy", "edit_target_hit_rate"}.issubset(payload):
            return benchmark_to_text(payload)
    return payload_to_json(payload)


def review_to_text(report: ReviewReport) -> str:
    readiness_map = {
        "not_ready": "Not ready for production",
        "needs_hardening": "Needs hardening",
        "promising": "Promising, with a few gaps left",
    }
    stats = report.stats or {}
    language_text = ", ".join(
        f"{language}={count}"
        for language, count in sorted((stats.get("languages") or {}).items())
    ) or "unknown"
    lines = [
        "RepoBrain Review",
        f"Repo: {report.repo_root}",
        f"Focus: {report.focus.value}",
        f"Readiness: {readiness_map.get(report.readiness, report.readiness)}",
        f"Score: {report.score:.1f}/10",
        "",
        report.summary,
        "",
        f"Surface: code_files={stats.get('code_files', 0)} route_files={stats.get('route_files', 0)} test_files={stats.get('test_files', 0)}",
        f"Languages: {language_text}",
        "",
        "Top findings:",
    ]
    if report.findings:
        for index, finding in enumerate(report.findings[:5], start=1):
            lines.append(f"{index}. [{finding.severity.value}] {finding.title}")
            lines.append(f"   {finding.summary}")
            if finding.file_paths:
                lines.append(f"   files: {', '.join(finding.file_paths[:4])}")
            if finding.recommendation:
                lines.append(f"   fix next: {finding.recommendation}")
    else:
        lines.append("- No high-signal findings from the local scan.")

    if report.next_steps:
        lines.extend(["", "What to fix first:"])
        lines.extend(f"- {step}" for step in report.next_steps[:3])

    if report.delta:
        lines.extend(
            [
                "",
                f"Baseline drift: {report.delta.status} vs {report.delta.baseline_label} ({report.delta.score_delta:+.1f})",
                f"Previous readiness: {report.delta.baseline_readiness} -> now {report.delta.current_readiness}",
            ]
        )
        if report.delta.new_findings:
            lines.append(f"New findings: {', '.join(report.delta.new_findings[:3])}")
        if report.delta.resolved_findings:
            lines.append(f"Resolved findings: {', '.join(report.delta.resolved_findings[:3])}")

    lines.extend(["", "Tip: run `repobrain review --focus security --format text` for a narrower pass."])
    return "\n".join(lines)


def ship_to_text(report: ShipReport) -> str:
    status_map = {
        "blocked": "Blocked",
        "caution": "Caution",
        "ready": "Ready",
    }
    review = report.review
    benchmark = report.benchmark or {}
    history = report.history or {}
    lines = [
        "RepoBrain Ship Gate",
        f"Repo: {report.repo_root}",
        f"Status: {status_map.get(report.status, report.status)}",
        f"Score: {report.score:.1f}/10",
        "",
        report.summary,
    ]
    if review is not None:
        lines.append(f"Review: {review.readiness} ({review.score:.1f}/10)")
        if review.delta is not None:
            lines.append(
                f"Baseline: {review.delta.baseline_label} is {review.delta.status} ({review.delta.score_delta:+.1f})"
            )
    if benchmark:
        lines.append(
            "Benchmark: "
            f"recall@3={benchmark.get('recall_at_3', 0)} "
            f"mrr={benchmark.get('mrr', 0)} "
            f"edit_target_hit_rate={benchmark.get('edit_target_hit_rate', 0)}"
        )
    if history.get("saved_snapshots", 0):
        lines.append(
            "Trend: "
            f"{history.get('direction', 'flat')} over {history.get('saved_snapshots', 0)} saved snapshot(s) "
            f"({float(history.get('score_change', 0.0)):+.1f})"
        )
        recurring = history.get("recurring_findings", [])
        if recurring:
            recurring_text = ", ".join(
                f"{item.get('title')} x{item.get('count')}"
                for item in recurring[:3]
                if isinstance(item, dict)
            )
            if recurring_text:
                lines.append(f"Recurring findings: {recurring_text}")

    lines.extend(["", "Checks:"])
    for check in report.checks:
        lines.append(f"- [{check.status}] {check.name}: {check.summary}")
        if check.detail:
            lines.append(f"  {check.detail}")

    if report.blockers:
        lines.extend(["", "Blockers:"])
        lines.extend(f"- {item}" for item in report.blockers[:4])

    if report.highlights:
        lines.extend(["", "What is already solid:"])
        lines.extend(f"- {item}" for item in report.highlights[:4])

    if report.next_steps:
        lines.extend(["", "Next steps:"])
        lines.extend(f"- {item}" for item in report.next_steps[:4])

    lines.extend(["", "Tip: run `repobrain baseline` after a clean hardening pass to track drift over time."])
    return "\n".join(lines)


def query_result_to_text(result: QueryResult) -> str:
    confidence_tail = f" ({result.confidence_label})" if result.confidence_label else ""
    lines = [
        "RepoBrain Result",
        f"Query: {result.query}",
        f"Intent: {result.intent.value} | Confidence: {result.confidence:.3f}{confidence_tail}",
        "",
        "Top files:",
    ]
    if result.top_files:
        for index, item in enumerate(result.top_files[:5], start=1):
            reasons = ", ".join(item.reasons[:4]) if item.reasons else "no explicit reasons"
            lines.append(f"{index}. {item.file_path} [{item.role}] score={item.score:.3f}")
            lines.append(f"   reasons: {reasons}")
    else:
        lines.append("- No files found.")

    lines.extend(["", "Snippets:"])
    if result.snippets:
        for hit in result.snippets[:3]:
            symbol = f"::{hit.symbol_name}" if hit.symbol_name else ""
            preview = " ".join(hit.content.split())
            if len(preview) > 140:
                preview = preview[:137] + "..."
            lines.append(f"- {hit.file_path}:{hit.start_line}-{hit.end_line}{symbol}")
            lines.append(f"  {preview}")
    else:
        lines.append("- No snippets found.")

    if result.call_chain:
        lines.extend(["", "Call chain hints:"])
        lines.extend(f"- {item}" for item in result.call_chain[:5])

    if result.edit_targets:
        lines.extend(["", "Edit targets:"])
        for target in result.edit_targets[:3]:
            lines.append(f"- {target.file_path} score={target.score:.3f}")
            lines.append(f"  {target.rationale}")

    if result.confidence_summary:
        lines.extend(["", "Assessment:"])
        lines.append(f"- {result.confidence_summary}")

    if result.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in result.warnings)

    if result.next_questions:
        lines.extend(["", "Next questions:"])
        lines.extend(f"- {question}" for question in result.next_questions)

    lines.extend(["", "Tip: use --format json for machine-readable output."])
    return "\n".join(lines)


def doctor_to_text(payload: dict[str, Any]) -> str:
    stats = payload.get("stats", {})
    providers = payload.get("providers", {})
    security = payload.get("security", {})
    capabilities = payload.get("capabilities", {})
    language_parsers = capabilities.get("language_parsers", {}) if isinstance(capabilities, dict) else {}

    lines = [
        "RepoBrain Doctor",
        f"Repo: {payload.get('repo_root')}",
        f"Indexed: {'yes' if payload.get('indexed') else 'no'}",
        f"Stats: files={stats.get('files', 0)} chunks={stats.get('chunks', 0)} symbols={stats.get('symbols', 0)} edges={stats.get('edges', 0)}",
        f"Providers: embedding={providers.get('embedding')} reranker={providers.get('reranker')}",
        f"Provider models: embedding={providers.get('embedding_model', 'n/a')} reranker={providers.get('reranker_model', 'n/a')}",
        f"Security: local_storage_only={security.get('local_storage_only')} remote_providers={security.get('remote_providers_enabled')}",
        "",
        "Parsers:",
    ]
    reranker_models = providers.get("reranker_models")
    if isinstance(reranker_models, list) and reranker_models:
        lines.insert(6, f"Gemini fallback pool: {', '.join(str(item) for item in reranker_models)}")
    if language_parsers:
        for language, detail in sorted(language_parsers.items()):
            selected = detail.get("selected", "unknown") if isinstance(detail, dict) else "unknown"
            fallback = detail.get("heuristic_fallback", True) if isinstance(detail, dict) else True
            lines.append(f"- {language}: {selected} fallback={fallback}")
    else:
        lines.append("- No parser capability details available.")

    lines.extend(["", "Next:", "- repobrain index", "- repobrain query \"Where is the main flow implemented?\""])
    return "\n".join(lines)


def provider_smoke_to_text(payload: dict[str, Any]) -> str:
    providers = payload.get("providers", {}) if isinstance(payload.get("providers"), dict) else {}
    embedding_smoke = payload.get("embedding_smoke", {}) if isinstance(payload.get("embedding_smoke"), dict) else {}
    reranker_smoke = payload.get("reranker_smoke", {}) if isinstance(payload.get("reranker_smoke"), dict) else {}
    pool = reranker_smoke.get("pool", [])
    pool_text = ", ".join(str(item) for item in pool) if isinstance(pool, list) and pool else "single-model mode"

    lines = [
        "RepoBrain Provider Smoke",
        f"Repo: {payload.get('repo_root')}",
        f"Embedding: {providers.get('embedding')} model={providers.get('embedding_model', 'n/a')}",
        f"Reranker: {providers.get('reranker')} model={providers.get('reranker_model', 'n/a')}",
        f"Gemini pool: {pool_text}",
        "",
        "Embedding smoke:",
        f"- status={embedding_smoke.get('status')}",
    ]
    if embedding_smoke.get("status") == "pass":
        lines.append(
            f"- vectors={embedding_smoke.get('vector_count')} dimensions={embedding_smoke.get('dimensions')}"
        )
    else:
        lines.append(f"- error={embedding_smoke.get('error')}")

    lines.extend(
        [
            "",
            "Reranker smoke:",
            f"- status={reranker_smoke.get('status')}",
            f"- active_model_before={reranker_smoke.get('active_model_before')}",
            f"- active_model_after={reranker_smoke.get('active_model_after')}",
        ]
    )
    if reranker_smoke.get("status") == "pass":
        lines.append(f"- score={reranker_smoke.get('score')}")
    else:
        lines.append(f"- error={reranker_smoke.get('error')}")
    if reranker_smoke.get("last_failover_error"):
        lines.append(f"- last_failover_error={reranker_smoke.get('last_failover_error')}")
    return "\n".join(lines)


def release_check_to_text(payload: dict[str, Any]) -> str:
    versions = payload.get("versions", {}) if isinstance(payload.get("versions"), dict) else {}
    dist = payload.get("dist", {}) if isinstance(payload.get("dist"), dict) else {}
    checks = payload.get("checks", []) if isinstance(payload.get("checks"), list) else []
    lines = [
        "RepoBrain Release Check",
        f"Project: {payload.get('project_root')}",
        f"Status: {str(payload.get('status', 'unknown')).upper()}",
        (
            "Versions: "
            f"pyproject={versions.get('pyproject') or 'missing'} "
            f"package={versions.get('package') or 'missing'} "
            f"webapp={versions.get('webapp') or 'missing'}"
        ),
        f"Dist: wheels={dist.get('wheel_count', 0)} sdists={dist.get('sdist_count', 0)}",
        "",
        "Checks:",
    ]
    if checks:
        for check in checks:
            if not isinstance(check, dict):
                continue
            lines.append(f"- [{check.get('status')}] {check.get('name')}: {check.get('summary')}")
            if check.get("detail"):
                lines.append(f"  {check.get('detail')}")
    else:
        lines.append("- No release checks were returned.")
    lines.extend(
        [
            "",
            "Tip: run `npm run build` in webapp, then `python -m build`, then rerun `repobrain release-check --require-dist --format text`.",
        ]
    )
    return "\n".join(lines)


def demo_clean_to_text(payload: dict[str, Any]) -> str:
    removed = payload.get("removed", []) if isinstance(payload.get("removed"), list) else []
    preserved = payload.get("preserved", []) if isinstance(payload.get("preserved"), list) else []
    errors = payload.get("errors", []) if isinstance(payload.get("errors"), list) else []
    action_label = "Would remove" if payload.get("dry_run") else "Removed"
    lines = [
        "RepoBrain Demo Clean",
        f"Project: {payload.get('project_root')}",
        f"Status: {str(payload.get('status', 'unknown')).upper()}",
        f"Mode: {'dry-run' if payload.get('dry_run') else 'apply'}",
        f"Removed: {payload.get('removed_count', 0)}",
        f"Preserved: {payload.get('preserved_count', 0)}",
        f"Errors: {payload.get('error_count', 0)}",
    ]
    if removed:
        lines.extend(["", f"{action_label}:"])
        lines.extend(f"- {item}" for item in removed[:12])
        remaining = len(removed) - 12
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")
    if preserved:
        lines.extend(["", "Preserved:"])
        for item in preserved[:6]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('path')}: {item.get('reason')}")
    if errors:
        lines.extend(["", "Errors:"])
        for item in errors[:6]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('path')}: {item.get('error')}")
    lines.extend(
        [
            "",
            "Tip: run `repobrain demo-clean --format text` before a live demo to remove local test/build clutter while keeping `webapp/dist` ready for `serve-web`.",
        ]
    )
    return "\n".join(lines)


def index_stats_to_text(payload: dict[str, Any]) -> str:
    parsers = payload.get("parsers", {})
    parser_text = ", ".join(f"{name}={count}" for name, count in sorted(parsers.items())) if isinstance(parsers, dict) else "unknown"
    return "\n".join(
        [
            "RepoBrain Index Complete",
            f"Files: {payload.get('files', 0)}",
            f"Chunks: {payload.get('chunks', 0)}",
            f"Symbols: {payload.get('symbols', 0)}",
            f"Edges: {payload.get('edges', 0)}",
            f"Parsers: {parser_text}",
            "",
            "Try next:",
            "repobrain query \"Where is the main flow implemented?\" --format text",
            "repobrain chat",
        ]
    )


def benchmark_to_text(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "RepoBrain Benchmark",
            f"Cases: {payload.get('cases_run')}",
            f"Recall@3: {payload.get('recall_at_3')}",
            f"MRR: {payload.get('mrr')}",
            f"Citation accuracy: {payload.get('citation_accuracy')}",
            f"Edit-target hit rate: {payload.get('edit_target_hit_rate')}",
        ]
    )


def workspace_projects_to_text(payload: dict[str, Any]) -> str:
    projects = payload.get("projects", []) if isinstance(payload.get("projects"), list) else []
    lines = [
        "RepoBrain Workspace",
        f"Current repo: {payload.get('current_repo') or 'none'}",
        f"Tracked repos: {payload.get('project_count', len(projects))}",
    ]
    if payload.get("message"):
        lines.extend(["", str(payload.get("message"))])
    if not projects:
        lines.extend(["", "No tracked repos yet.", "Try: repobrain workspace add /path/to/project --format text"])
        return "\n".join(lines)

    lines.append("")
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            continue
        active_suffix = " [active]" if project.get("active") else ""
        lines.append(f"{index}. {project.get('name')}{active_suffix}")
        lines.append(f"   {project.get('repo_root')}")
        summary = str(project.get("summary", "")).strip()
        if summary:
            lines.append(f"   summary: {summary}")
        recent_queries = project.get("recent_queries", [])
        if isinstance(recent_queries, list) and recent_queries:
            lines.append(f"   recent: {' | '.join(str(item) for item in recent_queries[-2:])}")
    lines.extend(["", "Tip: use `/use <repo>` in chat or `repobrain workspace use <repo>` in CLI."])
    return "\n".join(lines)


def workspace_summary_to_text(payload: dict[str, Any]) -> str:
    lines = [
        "RepoBrain Memory Summary",
        f"Repo: {payload.get('repo_root')}",
        f"Name: {payload.get('name')}",
    ]
    if payload.get("message"):
        lines.extend(["", str(payload.get("message"))])
    summary = str(payload.get("summary", "")).strip()
    lines.extend(["", f"Summary: {summary or 'No stored summary yet.'}"])

    manual_notes = payload.get("manual_notes", [])
    if isinstance(manual_notes, list) and manual_notes:
        lines.extend(["", "Manual notes:"])
        lines.extend(f"- {item}" for item in manual_notes[-4:])

    recent_queries = payload.get("recent_queries", [])
    if isinstance(recent_queries, list) and recent_queries:
        lines.extend(["", "Recent asks:"])
        lines.extend(f"- {item}" for item in recent_queries[-4:])

    top_files = payload.get("top_files", [])
    if isinstance(top_files, list) and top_files:
        lines.extend(["", "Hot files:"])
        lines.extend(f"- {item}" for item in top_files[-4:])

    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "Watch-outs:"])
        lines.extend(f"- {item}" for item in warnings[-3:])

    next_questions = payload.get("next_questions", [])
    if isinstance(next_questions, list) and next_questions:
        lines.extend(["", "Next thread:"])
        lines.extend(f"- {item}" for item in next_questions[-3:])

    lines.extend(["", "Tip: `/remember <note>` stores project-specific context for later chats."])
    return "\n".join(lines)


def workspace_query_to_text(payload: dict[str, Any]) -> str:
    results = payload.get("results", []) if isinstance(payload.get("results"), list) else []
    errors = payload.get("errors", []) if isinstance(payload.get("errors"), list) else []
    comparison = payload.get("comparison", {}) if isinstance(payload.get("comparison"), dict) else {}
    lines = [
        "RepoBrain Cross-Repo Query",
        f"Question: {payload.get('query')}",
        f"Current repo: {payload.get('current_repo')}",
        f"Compared repos: {payload.get('project_count', len(results))}",
        f"Context applied: {'yes' if payload.get('context_applied') else 'no'}",
    ]
    best_match = comparison.get("best_match")
    if isinstance(best_match, dict) and best_match:
        lines.extend(
            [
                "",
                "Leader:",
                (
                    f"- {best_match.get('name')} rank=#{best_match.get('global_rank')} "
                    f"citation={float(best_match.get('evidence_score', 0.0)):.3f} "
                    f"confidence={float(best_match.get('confidence', 0.0)):.3f} "
                    f"intent={best_match.get('intent')}"
                ),
            ]
        )
        if best_match.get("summary"):
            lines.append(f"  {best_match.get('summary')}")

    comparison_notes = comparison.get("notes", [])
    if isinstance(comparison_notes, list) and comparison_notes:
        lines.extend(["", "Comparison notes:"])
        lines.extend(f"- {item}" for item in comparison_notes[:4])

    shared_hotspots = comparison.get("shared_hotspots", [])
    if isinstance(shared_hotspots, list) and shared_hotspots:
        lines.extend(["", "Shared hotspots:"])
        for item in shared_hotspots[:3]:
            if not isinstance(item, dict):
                continue
            repo_names = item.get("repos", [])
            repo_label = ", ".join(str(name) for name in repo_names[:4]) if isinstance(repo_names, list) else ""
            lines.append(f"- {item.get('label')} across {int(item.get('count', 0))} repos")
            if repo_label:
                lines.append(f"  repos: {repo_label}")

    global_evidence = comparison.get("global_evidence", [])
    if isinstance(global_evidence, list) and global_evidence:
        lines.extend(["", "Global evidence leaders:"])
        for item in global_evidence[:5]:
            if not isinstance(item, dict):
                continue
            symbol = f"::{item.get('symbol_name')}" if item.get("symbol_name") else ""
            lines.append(
                f"- #{item.get('rank')} {item.get('name')} score={float(item.get('score', 0.0)):.3f} "
                f"{item.get('file_path')}:{item.get('start_line')}-{item.get('end_line')}{symbol}"
            )
            preview = str(item.get("preview", "")).strip()
            if preview:
                lines.append(f"  {preview}")

    if results:
        lines.extend(["", "Best evidence by repo:"])
        for index, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue
            active_suffix = " [active]" if item.get("active") else ""
            lines.append(
                (
                    f"{index}. {item.get('name')}{active_suffix} "
                    f"rank=#{item.get('global_rank')} "
                    f"citation={float(item.get('evidence_score', 0.0)):.3f} "
                    f"confidence={float(item.get('confidence', 0.0)):.3f}"
                )
            )
            lines.append(f"   {item.get('repo_root')}")
            top_files = item.get("top_files", [])
            if isinstance(top_files, list) and top_files:
                lines.append(f"   top files: {', '.join(str(path) for path in top_files[:3])}")
            if item.get("summary"):
                lines.append(f"   summary: {item.get('summary')}")
            if item.get("memory_summary"):
                lines.append(f"   memory: {item.get('memory_summary')}")
            citations = item.get("citations", [])
            if isinstance(citations, list) and citations:
                lines.append("   citations:")
                for citation in citations[:2]:
                    if not isinstance(citation, dict):
                        continue
                    symbol = f"::{citation.get('symbol_name')}" if citation.get("symbol_name") else ""
                    lines.append(
                        f"   - {citation.get('file_path')}:{citation.get('start_line')}-{citation.get('end_line')}{symbol}"
                    )
                    preview = str(citation.get("preview", "")).strip()
                    if preview:
                        lines.append(f"     {preview}")
            warnings = item.get("warnings", [])
            if isinstance(warnings, list) and warnings:
                lines.append(f"   warnings: {'; '.join(str(warning) for warning in warnings[:2])}")
            next_questions = item.get("next_questions", [])
            if isinstance(next_questions, list) and next_questions:
                lines.append(f"   next: {' | '.join(str(question) for question in next_questions[:2])}")
    else:
        lines.extend(["", "No successful repo results."])

    if errors:
        lines.extend(["", "Errors:"])
        for item in errors[:4]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('name')}: {item.get('error')}")

    lines.extend(["", "Tip: use `/summary` after a useful run to inspect the stored project memory."])
    return "\n".join(lines)


def cli_wordmark() -> str:
    return "\n".join(
        [
            "||\\\\  ||||| ||\\\\   /\\\\   ||\\\\  ||\\\\   /\\\\   || ||  ||",
            "|| || ||    || || /    \\\\ || || || || /    \\\\ || ||| ||",
            "||//  ||||  ||//  |||||| ||\\\\  ||//  |||||| || || |||",
            "||\\\\  ||    ||\\\\  ||  || || || ||\\\\  ||  || || ||  ||",
            "|| \\\\ ||||| || \\\\ ||  || ||//  || \\\\ ||  || || ||  ||",
            "",
            "codebase memory | flow trace | grounded answers",
        ]
    )


def _terminal_supports_color(stream: Any | None = None) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    target = stream or sys.stdout
    return bool(getattr(target, "isatty", lambda: False)())


def _ansi(text: str, *codes: str) -> str:
    if not _terminal_supports_color():
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


_KEY_VALUE_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<label>[A-Za-z][A-Za-z0-9 @._/\-+]*:)(?P<value>.*)$")
_STATUS_BULLET_PATTERN = re.compile(r"^(?P<prefix>\s*(?:- |\d+\. ))(?P<status>\[[^\]]+\])(?P<rest>.*)$")
_BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
_NUMBERED_SECTION_PATTERN = re.compile(r"^\d+\.\s.+:$")
_COMMAND_PREFIXES = (
    "repobrain ",
    "python ",
    "python -m ",
    "npm ",
    ".\\",
    "./",
)


def _status_codes(token: str) -> tuple[str, ...]:
    normalized = token.strip("[]").strip().lower().replace("_", " ")
    if normalized in {"pass", "ready", "indexed", "promising", "improving", "low"}:
        return ("1", "92")
    if normalized in {"fail", "error", "blocked", "critical", "high", "not ready", "not ready for production"}:
        return ("1", "91")
    return ("1", "93")


def _style_inline_fragments(text: str) -> str:
    def replace_code(match: re.Match[str]) -> str:
        return _ansi(match.group(0), "1", "93")

    return _BACKTICK_PATTERN.sub(replace_code, text)


def _style_terminal_line(line: str, *, is_first_non_empty: bool = False) -> str:
    if not _terminal_supports_color() or not line:
        return line

    stripped = line.strip()
    if not stripped:
        return line
    if is_first_non_empty:
        return _ansi(line, "1", "96")
    if stripped.startswith("Tip:"):
        return f"{_ansi('Tip:', '1', '95')}{_style_inline_fragments(line[len('Tip:'):])}"
    if stripped.startswith("Starter prompt:"):
        return f"{_ansi('Starter prompt:', '1', '95')}{_style_inline_fragments(line[len('Starter prompt:'):])}"
    if stripped.endswith(":") and not stripped.startswith("- ") and not _NUMBERED_SECTION_PATTERN.match(stripped):
        return _ansi(line, "1", "94")
    if _NUMBERED_SECTION_PATTERN.match(stripped):
        return _ansi(line, "1", "94")

    status_match = _STATUS_BULLET_PATTERN.match(line)
    if status_match:
        prefix = _ansi(status_match.group("prefix"), "1", "94")
        status = _ansi(status_match.group("status"), *_status_codes(status_match.group("status")))
        rest = _style_inline_fragments(status_match.group("rest"))
        return f"{prefix}{status}{rest}"

    key_value_match = _KEY_VALUE_PATTERN.match(line)
    if key_value_match:
        indent = key_value_match.group("indent")
        label = _ansi(key_value_match.group("label"), "1", "37")
        value = _style_inline_fragments(key_value_match.group("value"))
        return f"{indent}{label}{value}"

    if stripped.startswith(_COMMAND_PREFIXES):
        return _ansi(line, "1", "93")
    if stripped.startswith("- ") and stripped[2:].startswith(_COMMAND_PREFIXES):
        command_offset = line.find("- ") + 2
        return f"{line[:command_offset]}{_ansi(line[command_offset:], '1', '93')}"

    return _style_inline_fragments(line)


def _style_terminal_block(text: str) -> str:
    if not _terminal_supports_color():
        return text

    styled_lines: list[str] = []
    seen_first_non_empty = False
    for line in text.splitlines():
        styled_lines.append(_style_terminal_line(line, is_first_non_empty=not seen_first_non_empty and bool(line.strip())))
        if line.strip() and not seen_first_non_empty:
            seen_first_non_empty = True
    return "\n".join(styled_lines)


def render_cli_wordmark() -> str:
    lines = cli_wordmark().splitlines()
    if not _terminal_supports_color():
        return "\n".join(lines)
    return "\n".join(
        _ansi(line, "1", "96") if index < 5 else _ansi(line, "1", "94")
        for index, line in enumerate(lines)
    )


def chat_intro(repo_root: str | Path, *, styled: bool = False) -> str:
    root = Path(repo_root).expanduser().resolve()
    repo_name = root.name or str(root)
    text = "\n".join(
        [
            "RepoBrain chat is local-only. Type /help for commands, /json for raw payloads, or /exit to quit.",
            f"Attached repo: {repo_name}",
            f"Workspace: {root}",
            "Lanes: ask directly, /evidence, /map, /focus, /summary, /remember, /projects, /add, /use, /multi",
            'Starter prompt: "Where is auth callback handled?"',
        ]
    )
    return _style_terminal_block(text) if styled else text


def chat_help_text(*, styled: bool = False) -> str:
    text = "\n".join(
        [
            "RepoBrain chat commands",
            "Ask directly: <question>",
            "Grounded retrieval: /query <q>, /evidence <q>, /trace <q>, /impact <q>, /targets <q>, /map <q>",
            "Chat focus: /focus <topic>, /focus, /focus clear",
            "Workspace memory: /summary, /remember <note>, /remember clear",
            "Workspace routing: /projects, /add <path>, /use <repo>, /multi <q>",
            "Workspace checks: /index, /review, /baseline, /doctor, /provider-smoke, /ship, /report",
            "Output and exit: /json, /text, /exit",
        ]
    )
    return _style_terminal_block(text) if styled else text


def chat_prompt(repo_root: str | Path) -> str:
    repo_name = Path(repo_root).expanduser().resolve().name or "repo"
    safe_name = "".join(character if character.isalnum() or character in "-._" else "_" for character in repo_name)
    if not _terminal_supports_color():
        return f"repobrain[{safe_name}]> "
    return f"{_ansi('repobrain', '1', '96')}[{_ansi(safe_name, '1', '94')}]{_ansi('>', '1', '93')} "


def quickstart_text(*, styled: bool = False) -> str:
    body = "\n".join(
        [
            "RepoBrain Quickstart",
            "",
            "1. Install:",
            '   python -m pip install -e ".[dev,tree-sitter,mcp]"',
            "",
            "2. Prepare local state:",
            "   repobrain init --repo /path/to/your-project",
            "   repobrain provider-smoke --format text",
            "   repobrain review --format text",
            "   repobrain index --format text",
            "",
            "3. Ask questions:",
            '   repobrain query "Where is payment retry logic implemented?" --format text',
            '   repobrain trace "Trace login with Google from route to service" --format text',
            '   repobrain targets "Which files should I edit to add GitHub login?" --format text',
            "   repobrain ship --format text",
            "",
            "4. Friendlier modes:",
            "   repobrain chat",
            "   repobrain baseline",
            "   repobrain report --format text",
            "   repobrain report --open",
        ]
    )
    wordmark = render_cli_wordmark() if styled else cli_wordmark()
    formatted_body = _style_terminal_block(body) if styled else body
    return f"{wordmark}\n\n{formatted_body}"


def build_report(engine: RepoBrainEngine, output: str | Path | None = None, baseline_label: str = "baseline") -> Path:
    ship = engine.ship(baseline_label=baseline_label)
    doctor = ship.doctor
    review = ship.review
    if review is None:
        raise RuntimeError("Ship report did not include a review payload.")
    output_path = Path(output) if output else engine.config.state_path / "report.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_html = _report_html(doctor, review, ship)
    output_path.write_text(report_html, encoding="utf-8")
    return output_path


def _report_html(doctor: dict[str, Any], review: ReviewReport, ship: ShipReport) -> str:
    stats = doctor.get("stats", {})
    providers = doctor.get("providers", {})
    provider_status = doctor.get("provider_status", {}) if isinstance(doctor.get("provider_status"), dict) else {}
    security = doctor.get("security", {})
    capabilities = doctor.get("capabilities", {})
    language_parsers = capabilities.get("language_parsers", {}) if isinstance(capabilities, dict) else {}
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    readiness_map = {
        "not_ready": "Not Ready",
        "needs_hardening": "Needs Hardening",
        "promising": "Promising",
    }

    parser_cards = "\n".join(
        f"""
        <article class="mini-card">
          <span>{html.escape(str(language))}</span>
          <strong>{html.escape(str(detail.get('selected', 'unknown') if isinstance(detail, dict) else 'unknown'))}</strong>
          <small>fallback: {html.escape(str(detail.get('heuristic_fallback', True) if isinstance(detail, dict) else True))}</small>
        </article>
        """
        for language, detail in sorted(language_parsers.items())
    )
    if not parser_cards:
        parser_cards = '<article class="mini-card"><span>parsers</span><strong>unknown</strong><small>Run repobrain doctor</small></article>'

    indexed = bool(doctor.get("indexed"))
    status_label = "Indexed" if indexed else "Not indexed"
    status_class = "good" if indexed else "warn"
    ship_status_map = {
        "blocked": "Blocked",
        "caution": "Caution",
        "ready": "Ready",
    }
    ship_badge_class = "warn" if ship.status in {"blocked", "caution"} else "good"
    review_cards = "\n".join(
        f"""
        <article class="mini-card">
          <span>{html.escape(finding.severity.value)}</span>
          <strong>{html.escape(finding.title)}</strong>
          <small>{html.escape(', '.join(finding.file_paths[:3]) if finding.file_paths else 'repo-wide')}</small>
          <p>{html.escape(finding.summary)}</p>
        </article>
        """
        for finding in review.findings[:5]
    )
    if not review_cards:
        review_cards = '<article class="mini-card"><span>review</span><strong>No high-signal findings</strong><small>Keep manually checking auth and domain logic.</small></article>'
    next_steps_html = "".join(f"<li>{html.escape(step)}</li>" for step in review.next_steps[:3]) or "<li>Run a narrower `repobrain review --focus security` pass.</li>"
    ship_checks_html = "\n".join(
        f"""
        <article class="mini-card">
          <span>{html.escape(check.status)}</span>
          <strong>{html.escape(check.name)}</strong>
          <small>{html.escape(check.summary)}</small>
          <p>{html.escape(check.detail or 'No extra detail.')}</p>
        </article>
        """
        for check in ship.checks
    )
    delta_html = ""
    if review.delta is not None:
        delta_html = (
            f"<article class=\"mini-card\">"
            f"<span>baseline drift</span>"
            f"<strong>{html.escape(review.delta.status)} vs {html.escape(review.delta.baseline_label)}</strong>"
            f"<small>{html.escape(review.delta.baseline_saved_at or 'unknown snapshot time')} | score delta {review.delta.score_delta:+.1f}</small>"
            f"<p>{html.escape(', '.join(review.delta.new_findings[:3]) or 'No new high-signal findings.')}</p>"
            f"</article>"
        )
    benchmark = ship.benchmark or {}
    benchmark_html = (
        f"recall@3={benchmark.get('recall_at_3', 'n/a')} | "
        f"mrr={benchmark.get('mrr', 'n/a')} | "
        f"edit_target_hit_rate={benchmark.get('edit_target_hit_rate', 'n/a')}"
        if benchmark
        else "Benchmark unavailable until the repo is indexed."
    )
    highlights_html = "".join(f"<li>{html.escape(item)}</li>" for item in ship.highlights[:4]) or "<li>Harden the repo, then rerun `repobrain ship`.</li>"
    ship_next_steps_html = "".join(f"<li>{html.escape(item)}</li>" for item in ship.next_steps[:4]) or "<li>Run `repobrain review --format text` for detailed findings.</li>"
    history = ship.history or {}
    history_points = history.get("points", []) if isinstance(history.get("points"), list) else []
    trend_direction = str(history.get("direction", "new"))
    trend_label_map = {
        "new": "New",
        "flat": "Flat",
        "improving": "Improving",
        "regressing": "Regressing",
    }
    trend_badge_class = "good" if trend_direction in {"improving", "flat"} else "warn"
    trend_summary = "Save a baseline to start tracking review drift over time."
    if history.get("saved_snapshots", 0):
        trend_summary = (
            f"{trend_label_map.get(trend_direction, trend_direction)} over "
            f"{history.get('saved_snapshots', 0)} saved snapshot(s), "
            f"with a window delta of {float(history.get('score_change', 0.0)):+.1f}."
        )
    trend_points_html_parts: list[str] = []
    for point in history_points:
        point_score = round(float(point.get("score", 0.0)), 1)
        point_name = "Current" if point.get("current") else str(point.get("saved_at", "") or point.get("name", "Snapshot"))
        point_label = point_name if point_name == "Current" else point_name.replace("T", " ")[:16]
        point_readiness = readiness_map.get(str(point.get("readiness", "unknown")), str(point.get("readiness", "unknown")))
        bar_width = max(12, min(100, int(point_score * 10)))
        item_class = " current" if point.get("current") else ""
        trend_points_html_parts.append(
            f"""
            <article class="timeline-item{item_class}">
              <div class="row between">
                <strong>{html.escape(point_label)}</strong>
                <span>{point_score:.1f}/10</span>
              </div>
              <div class="timeline-bar"><span style="width:{bar_width}%"></span></div>
              <small>{html.escape(point_readiness)} | findings {int(point.get('finding_count', 0))}</small>
            </article>
            """
        )
    trend_points_html = "\n".join(trend_points_html_parts) or (
        '<article class="timeline-item current"><strong>Current</strong>'
        '<div class="timeline-bar"><span style="width:50%"></span></div>'
        '<small>Run `repobrain baseline` after hardening to begin history tracking.</small></article>'
    )
    recurring = history.get("recurring_findings", []) if isinstance(history.get("recurring_findings"), list) else []
    recurring_html = "".join(
        f"<li>{html.escape(str(item.get('title', 'Untitled finding')))} x{int(item.get('count', 0))}</li>"
        for item in recurring[:3]
        if isinstance(item, dict)
    ) or "<li>No recurring high-signal findings across the visible trend window.</li>"
    reranker_models = providers.get("reranker_models", [])
    reranker_models_text = (
        ", ".join(str(item) for item in reranker_models)
        if isinstance(reranker_models, list) and reranker_models
        else "Single-model mode"
    )
    last_failover_error = providers.get("reranker_last_failover_error")
    last_failover_text = str(last_failover_error) if last_failover_error else "No failover recorded in this process."
    provider_cards = "\n".join(
        f"""
        <article class="mini-card">
          <span>{html.escape(str(kind))}</span>
          <strong>{html.escape(str(detail.get('active', 'unknown')))}</strong>
          <small>ready={html.escape(str(detail.get('ready', False)))} | network={html.escape(str(detail.get('requires_network', False)))}</small>
          <p>{html.escape('; '.join(str(item) for item in detail.get('warnings', [])) or 'No provider warnings.')}</p>
        </article>
        """
        for kind, detail in sorted(provider_status.items())
        if isinstance(detail, dict)
    )
    if not provider_cards:
        provider_cards = (
            '<article class="mini-card"><span>providers</span><strong>unknown</strong>'
            '<small>Run repobrain doctor</small><p>No provider posture details available.</p></article>'
        )

    brand_mark_svg = """
    <svg class="brand-mark" viewBox="0 0 192 192" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="reportShieldGradient" x1="22" y1="28" x2="170" y2="170" gradientUnits="userSpaceOnUse">
          <stop stop-color="#1A2540"/>
          <stop offset="0.5" stop-color="#243D76"/>
          <stop offset="1" stop-color="#162543"/>
        </linearGradient>
        <linearGradient id="reportNetworkGradient" x1="64" y1="42" x2="140" y2="146" gradientUnits="userSpaceOnUse">
          <stop stop-color="#85F9F4"/>
          <stop offset="0.55" stop-color="#42C9D9"/>
          <stop offset="1" stop-color="#1C86D1"/>
        </linearGradient>
      </defs>
      <path d="M31 54.5L52.4 33H101.8L156 87.2V122.2L129.8 148.5H78.5L31 101V54.5Z" fill="url(#reportShieldGradient)" />
      <path d="M31 54.5L52.4 33H101.8L156 87.2V122.2L129.8 148.5H78.5L31 101V54.5Z" stroke="#334A79" stroke-width="4" stroke-linejoin="round" />
      <path d="M75.2 58.3L90.4 46.6L116.3 48.8L133.7 67.3L133 93.8L117.6 110.9L90 115.8L67.8 103.5L57.5 80.7L62.8 60.1L75.2 58.3Z" stroke="url(#reportNetworkGradient)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity="0.96" />
      <path d="M58 81L88 78L109 81L90 116" stroke="url(#reportNetworkGradient)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="75" cy="58" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="90" cy="47" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="116" cy="49" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="134" cy="67" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="133" cy="94" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="118" cy="111" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="90" cy="116" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="68" cy="104" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="58" cy="81" r="6.5" fill="#0E1830" stroke="#86FBF6" stroke-width="4" />
      <circle cx="88" cy="78" r="8" fill="#E6FFFD" />
      <circle cx="109" cy="81" r="7.5" fill="#D7FFF8" />
    </svg>
    """.strip()

    system_facts_html = "\n".join(
        [
            f"<li><span>Repo:</span><strong>{html.escape(str(review.repo_root))}</strong></li>",
            f"<li><span>Embedding:</span><strong>{html.escape(str(providers.get('embedding', 'unknown')))}</strong></li>",
            f"<li><span>Embedding model:</span><strong>{html.escape(str(providers.get('embedding_model', 'n/a')))}</strong></li>",
            f"<li><span>Reranker:</span><strong>{html.escape(str(providers.get('reranker', 'unknown')))}</strong></li>",
            f"<li><span>Reranker model:</span><strong>{html.escape(str(providers.get('reranker_model', 'n/a')))}</strong></li>",
            f"<li><span>Gemini fallback pool:</span><strong>{html.escape(reranker_models_text)}</strong></li>",
            f"<li><span>Last failover event:</span><strong>{html.escape(last_failover_text)}</strong></li>",
            f"<li><span>Local storage only:</span><strong>{html.escape(str(security.get('local_storage_only', True)))}</strong></li>",
            f"<li><span>Remote providers:</span><strong>{html.escape(str(security.get('remote_providers_enabled', False)))}</strong></li>",
            f"<li><span>Network required:</span><strong>{html.escape(str(security.get('network_required', False)))}</strong></li>",
            f"<li><span>Review score:</span><strong>{review.score:.1f}/10</strong></li>",
            f"<li><span>Readiness:</span><strong>{html.escape(readiness_map.get(review.readiness, review.readiness))}</strong></li>",
            f"<li><span>Generated:</span><strong>{generated_at}</strong></li>",
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RepoBrain Control Room Report</title>
  <style>
    :root {{
      --bg: #efe1cc;
      --bg-soft: #f8f0e2;
      --ink: #17211d;
      --ink-soft: #55645b;
      --line: rgba(25, 31, 27, 0.12);
      --line-strong: rgba(25, 31, 27, 0.18);
      --panel: rgba(255, 250, 242, 0.88);
      --panel-strong: rgba(255, 252, 246, 0.96);
      --panel-muted: rgba(255, 255, 255, 0.46);
      --accent: #0f766e;
      --accent-strong: #0f5b58;
      --secondary: #1d4ed8;
      --warning: #c2410c;
      --good-bg: rgba(15, 118, 110, 0.1);
      --warn-bg: rgba(194, 65, 12, 0.12);
      --code-bg: #17211d;
      --code-ink: #eef2ee;
      --shadow: 0 24px 72px rgba(63, 41, 15, 0.14);
      --radius-xl: 32px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --font-sans: Aptos, "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", sans-serif;
      --font-mono: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: var(--font-sans);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.24), transparent 32rem),
        radial-gradient(circle at bottom right, rgba(194, 65, 12, 0.18), transparent 28rem),
        linear-gradient(135deg, var(--bg-soft) 0%, var(--bg) 100%);
    }}
    main {{
      width: min(1220px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 52px;
    }}
    .hero-grid,
    .card-grid,
    .double-grid,
    .metric-grid,
    .timeline,
    .info-strip {{
      display: grid;
      gap: 18px;
    }}
    .hero-grid {{
      grid-template-columns: 1.15fr 0.85fr;
    }}
    .card-grid {{
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .double-grid {{
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .metric-grid {{
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-top: 18px;
    }}
    .timeline {{
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }}
    .hero-card,
    .panel-card,
    .mini-card {{
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }}
    .hero-card,
    .panel-card {{
      padding: 26px;
      background: var(--panel);
    }}
    .mini-card {{
      padding: 16px;
      background: var(--panel-strong);
      border-radius: var(--radius-lg);
      box-shadow: none;
    }}
    .brand-card {{
      position: relative;
      overflow: hidden;
    }}
    .brand-card::after {{
      content: "";
      position: absolute;
      inset: auto -8% -12% auto;
      width: 240px;
      height: 240px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(29, 78, 216, 0.18), transparent 70%);
      pointer-events: none;
    }}
    .hero-topline,
    .section-heading,
    .row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .row.between {{
      justify-content: space-between;
    }}
    .brand-lockup {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 18px;
      margin-top: 18px;
    }}
    .brand-mark {{
      width: clamp(82px, 12vw, 132px);
      aspect-ratio: 1;
      display: block;
      filter: drop-shadow(0 18px 30px rgba(13, 30, 52, 0.22));
    }}
    .brand-copy {{
      min-width: 0;
    }}
    .brand-kicker {{
      display: inline-flex;
      align-items: center;
      padding: 7px 12px;
      border-radius: 999px;
      border: 1px solid rgba(29, 78, 216, 0.18);
      background: rgba(29, 78, 216, 0.08);
      color: var(--secondary);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    .brand-wordmark {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.14em;
      margin: 12px 0 10px;
      font-size: clamp(2.8rem, 8vw, 5.6rem);
      line-height: 0.9;
      letter-spacing: -0.07em;
    }}
    .brand-word-brain {{
      color: var(--accent-strong);
    }}
    .lead,
    .section-copy,
    .mini-card p,
    footer {{
      margin: 0;
      color: var(--ink-soft);
      line-height: 1.7;
    }}
    .brand-rail {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 22px 0 18px;
    }}
    .rail-pill,
    .status-pill,
    .mini-pill {{
      display: inline-flex;
      align-items: center;
      padding: 9px 14px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.88rem;
    }}
    .rail-pill {{
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.44);
      color: var(--ink);
    }}
    .status-pill,
    .mini-pill.good {{
      background: var(--good-bg);
      color: var(--accent-strong);
    }}
    .status-pill.warn,
    .mini-pill.warn {{
      background: var(--warn-bg);
      color: var(--warning);
    }}
    .info-strip {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin: 0 0 18px;
    }}
    .info-strip div,
    .metric,
    .timeline-item {{
      border-radius: var(--radius-lg);
      border: 1px solid var(--line);
      background: var(--panel-muted);
    }}
    .info-strip div,
    .metric,
    .timeline-item {{
      padding: 16px;
    }}
    .eyebrow,
    .metric span,
    .mini-card span,
    .fact-list span {{
      display: block;
      color: var(--ink-soft);
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    .info-strip strong,
    .metric strong,
    .mini-card strong,
    .timeline-item strong,
    .fact-list strong {{
      display: block;
      margin-top: 8px;
      line-height: 1.4;
      word-break: break-word;
    }}
    .metric strong {{
      font-size: 1.6rem;
      line-height: 1.1;
    }}
    h2 {{
      margin: 0;
      font-size: 1rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    h3 {{
      margin: 0;
      font-size: 1rem;
    }}
    .stack {{
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }}
    .fact-list,
    .mini-card ul {{
      margin: 0;
      padding-left: 18px;
    }}
    .fact-list {{
      list-style: none;
      padding: 0;
      display: grid;
      gap: 10px;
      margin-top: 18px;
    }}
    .fact-list li {{
      padding: 14px 16px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--line);
      background: var(--panel-muted);
    }}
    .fact-list strong {{
      margin-top: 6px;
    }}
    .timeline-item.current {{
      background: var(--good-bg);
      border-color: rgba(15, 118, 110, 0.35);
    }}
    .timeline-item span {{
      color: var(--ink-soft);
      font-size: 0.84rem;
    }}
    .timeline-bar {{
      width: 100%;
      height: 10px;
      margin: 10px 0 8px;
      border-radius: 999px;
      background: rgba(20, 33, 28, 0.08);
      overflow: hidden;
    }}
    .timeline-bar span {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--secondary));
    }}
    code,
    pre {{
      font-family: var(--font-mono);
    }}
    pre {{
      overflow-x: auto;
      margin: 0;
      padding: 18px;
      border-radius: var(--radius-lg);
      color: var(--code-ink);
      background: var(--code-bg);
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    footer {{
      margin-top: 18px;
      font-size: 0.92rem;
    }}
    @media (max-width: 920px) {{
      main {{
        width: min(100vw - 18px, 1220px);
        padding: 16px 0 36px;
      }}
      .hero-grid,
      .metric-grid,
      .double-grid,
      .info-strip {{
        grid-template-columns: 1fr;
      }}
      .brand-lockup,
      .hero-topline,
      .section-heading,
      .row {{
        grid-template-columns: 1fr;
        flex-direction: column;
        align-items: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero-grid">
      <article class="hero-card brand-card">
        <div class="hero-topline">
          <span class="status-pill">Local report</span>
          <span class="mini-pill {status_class}">{status_label}</span>
        </div>
        <div class="brand-lockup">
          {brand_mark_svg}
          <div class="brand-copy">
            <span class="brand-kicker">grounded codebase memory</span>
            <h1 class="brand-wordmark" aria-label="RepoBrain">
              <span class="brand-word brand-word-repo">Repo</span>
              <span class="brand-word brand-word-brain">Brain</span>
            </h1>
            <p class="lead">Local-first codebase memory for indexing one project, tracing real flows, and ranking safer edit targets with evidence.</p>
          </div>
        </div>
        <div class="brand-rail" aria-label="RepoBrain capabilities">
          <span class="rail-pill">Query</span>
          <span class="rail-pill">Trace</span>
          <span class="rail-pill">Targets</span>
          <span class="rail-pill">Review</span>
          <span class="rail-pill">Ship</span>
        </div>
        <div class="info-strip">
          <div>
            <span class="eyebrow">Report surface</span>
            <strong>Control Room snapshot</strong>
          </div>
          <div>
            <span class="eyebrow">Readiness</span>
            <strong>{html.escape(readiness_map.get(review.readiness, review.readiness))}</strong>
          </div>
          <div>
            <span class="eyebrow">Attached repo</span>
            <strong>{html.escape(str(review.repo_root))}</strong>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>files</span><strong>{stats.get('files', 0)}</strong></div>
          <div class="metric"><span>chunks</span><strong>{stats.get('chunks', 0)}</strong></div>
          <div class="metric"><span>symbols</span><strong>{stats.get('symbols', 0)}</strong></div>
          <div class="metric"><span>edges</span><strong>{stats.get('edges', 0)}</strong></div>
        </div>
      </article>

      <aside class="hero-card">
        <div class="section-heading">
          <div>
            <h2>System</h2>
            <p class="section-copy">Operational posture for this local RepoBrain run, including active providers, fallback state, and review readiness.</p>
          </div>
          <span class="mini-pill {ship_badge_class}">{html.escape(ship_status_map.get(ship.status, ship.status))}</span>
        </div>
        <ul class="fact-list">{system_facts_html}</ul>
      </aside>
    </section>

    <section class="panel-card stack">
      <div class="section-heading">
        <div>
          <h2>Ship Gate</h2>
          <p class="section-copy">{html.escape(ship.summary)}</p>
        </div>
        <span class="mini-pill {ship_badge_class}">Ship score {ship.score:.1f}/10</span>
      </div>
      <div class="card-grid">{ship_checks_html}</div>
      <div class="double-grid">
        <article class="mini-card">
          <span>benchmark</span>
          <strong>retrieval quality</strong>
          <small>{html.escape(benchmark_html)}</small>
          <p>RepoBrain uses this as a lightweight release signal instead of relying on intuition alone.</p>
        </article>
        {delta_html or '<article class="mini-card"><span>baseline drift</span><strong>No baseline yet</strong><small>Run repobrain baseline</small><p>Save a stable snapshot after hardening so future scans can detect regressions automatically.</p></article>'}
      </div>
      <div class="double-grid">
        <article class="mini-card">
          <span>what is already solid</span>
          <ul>{highlights_html}</ul>
        </article>
        <article class="mini-card">
          <span>ship next steps</span>
          <ul>{ship_next_steps_html}</ul>
        </article>
      </div>
    </section>

    <section class="panel-card stack">
      <div class="section-heading">
        <div>
          <h2>Provider Posture</h2>
          <p class="section-copy">See which provider path is active, whether network-backed paths are ready, and which Gemini rerank models are available for failover.</p>
        </div>
      </div>
      <div class="card-grid">{provider_cards}</div>
      <div class="double-grid">
        <article class="mini-card">
          <span>gemini pool</span>
          <strong>{html.escape(str(providers.get('reranker_model', 'n/a')))}</strong>
          <small>active reranker model</small>
          <p>{html.escape(reranker_models_text)}</p>
        </article>
        <article class="mini-card">
          <span>last failover</span>
          <strong>{html.escape('recorded' if last_failover_error else 'none')}</strong>
          <small>process-local failover memory</small>
          <p>{html.escape(last_failover_text)}</p>
        </article>
      </div>
    </section>

    <section class="panel-card stack">
      <div class="section-heading">
        <div>
          <h2>Baseline Trend</h2>
          <p class="section-copy">{html.escape(trend_summary)}</p>
        </div>
        <span class="mini-pill {trend_badge_class}">{html.escape(trend_label_map.get(trend_direction, trend_direction))}</span>
      </div>
      <div class="double-grid">
        <article class="mini-card">
          <span>window</span>
          <strong>{html.escape(trend_label_map.get(trend_direction, trend_direction))}</strong>
          <small>{int(history.get('saved_snapshots', 0))} saved snapshot(s)</small>
          <p>Best {float(history.get('best_score', review.score)):.1f}/10 | Worst {float(history.get('worst_score', review.score)):.1f}/10</p>
        </article>
        <article class="mini-card">
          <span>recurring findings</span>
          <strong>Persistent risk themes</strong>
          <small>Repeated high-signal findings across the visible history window.</small>
          <ul>{recurring_html}</ul>
        </article>
      </div>
      <div class="timeline">{trend_points_html}</div>
    </section>

    <section class="panel-card stack">
      <div class="section-heading">
        <div>
          <h2>Project Review</h2>
          <p class="section-copy">{html.escape(review.summary)}</p>
        </div>
      </div>
      <div class="card-grid">{review_cards}</div>
      <article class="mini-card">
        <span>what to fix first</span>
        <ul>{next_steps_html}</ul>
      </article>
    </section>

    <section class="panel-card stack">
      <h2>Parsers</h2>
      <div class="card-grid">{parser_cards}</div>
    </section>

    <section class="panel-card stack">
      <h2>Try Next</h2>
      <pre>repobrain index
repobrain query "Where is the main flow implemented?" --format text
repobrain trace "Trace login with Google from route to service" --format text
repobrain chat</pre>
    </section>

    <footer>Generated locally by <code>repobrain report</code>. No source code was sent to a hosted service.</footer>
  </main>
</body>
</html>
"""
