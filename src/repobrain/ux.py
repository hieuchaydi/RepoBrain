from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repobrain.engine.core import RepoBrainEngine
from repobrain.models import QueryResult, ReviewReport, ShipReport


def payload_to_json(payload: object) -> str:
    if hasattr(payload, "to_dict"):
        return json.dumps(payload.to_dict(), indent=2)
    return json.dumps(payload, indent=2)


def payload_to_text(payload: object) -> str:
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
    lines = [
        "RepoBrain Result",
        f"Query: {result.query}",
        f"Intent: {result.intent.value} | Confidence: {result.confidence:.3f}",
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


def quickstart_text() -> str:
    return "\n".join(
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
            f"<div class=\"mini-card\">"
            f"<span>baseline drift</span>"
            f"<strong>{html.escape(review.delta.status)} vs {html.escape(review.delta.baseline_label)}</strong>"
            f"<small>{html.escape(review.delta.baseline_saved_at or 'unknown snapshot time')} | score delta {review.delta.score_delta:+.1f}</small>"
            f"<p>{html.escape(', '.join(review.delta.new_findings[:3]) or 'No new high-signal findings.')}</p>"
            f"</div>"
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
              <div class="row" style="justify-content:space-between;">
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

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RepoBrain Report</title>
  <style>
    :root {{
      --ink: #1d241f;
      --muted: #66706a;
      --paper: #f5f0e6;
      --panel: rgba(255, 252, 244, 0.86);
      --line: #d8ccb8;
      --accent: #0f766e;
      --accent-2: #c2410c;
      --shadow: 0 24px 80px rgba(40, 32, 18, 0.14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.24), transparent 34rem),
        radial-gradient(circle at bottom right, rgba(194, 65, 12, 0.18), transparent 30rem),
        linear-gradient(135deg, #f8f1e3 0%, #efe3ce 100%);
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 48px 0;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 24px;
      align-items: stretch;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2.6rem, 8vw, 6rem);
      letter-spacing: -0.08em;
      line-height: 0.9;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 1.2rem;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--accent);
    }}
    p {{ color: var(--muted); font-size: 1.04rem; line-height: 1.7; }}
    .badge {{
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      color: white;
      background: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 0.86rem;
    }}
    .badge.warn {{ background: var(--accent-2); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-top: 24px;
    }}
    .metric {{
      padding: 18px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.42);
    }}
    .metric span, .mini-card span {{
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 2rem;
      line-height: 1;
    }}
    .stack {{
      display: grid;
      gap: 14px;
      margin-top: 24px;
    }}
    .mini-card {{
      padding: 16px;
      border-radius: 18px;
      background: #fff8ec;
      border: 1px solid var(--line);
    }}
    .mini-card strong {{ display: block; margin: 6px 0; }}
    .timeline {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
    }}
    .timeline-item {{
      padding: 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.52);
    }}
    .timeline-item.current {{
      background: rgba(15, 118, 110, 0.1);
      border-color: rgba(15, 118, 110, 0.35);
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
      background: linear-gradient(90deg, var(--accent), #2563eb);
    }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    }}
    pre {{
      overflow-x: auto;
      padding: 18px;
      border-radius: 18px;
      color: #fdf6e3;
      background: #17211d;
    }}
    footer {{
      margin-top: 24px;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    @media (max-width: 820px) {{
      .hero, .grid {{ grid-template-columns: 1fr; }}
      main {{ padding: 24px 0; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="panel">
        <span class="badge {status_class}">{status_label}</span>
        <h1>RepoBrain</h1>
        <p>Local codebase memory for AI coding assistants. It indexes files, extracts evidence, traces likely flows, and warns when context is weak.</p>
        <div class="grid">
          <div class="metric"><span>files</span><strong>{stats.get('files', 0)}</strong></div>
          <div class="metric"><span>chunks</span><strong>{stats.get('chunks', 0)}</strong></div>
          <div class="metric"><span>symbols</span><strong>{stats.get('symbols', 0)}</strong></div>
          <div class="metric"><span>edges</span><strong>{stats.get('edges', 0)}</strong></div>
        </div>
      </div>
      <aside class="panel">
        <h2>System</h2>
        <p><strong>Ship gate:</strong> <span class="badge {ship_badge_class}">{html.escape(ship_status_map.get(ship.status, ship.status))}</span></p>
        <p><strong>Ship score:</strong> {ship.score:.1f}/10</p>
        <p><strong>Embedding:</strong> {html.escape(str(providers.get('embedding', 'unknown')))}</p>
        <p><strong>Embedding model:</strong> {html.escape(str(providers.get('embedding_model', 'n/a')))}</p>
        <p><strong>Reranker:</strong> {html.escape(str(providers.get('reranker', 'unknown')))}</p>
        <p><strong>Reranker model:</strong> {html.escape(str(providers.get('reranker_model', 'n/a')))}</p>
        <p><strong>Gemini fallback pool:</strong> {html.escape(reranker_models_text)}</p>
        <p><strong>Last failover event:</strong> {html.escape(last_failover_text)}</p>
        <p><strong>Local storage only:</strong> {html.escape(str(security.get('local_storage_only', True)))}</p>
        <p><strong>Review score:</strong> {review.score:.1f}/10</p>
        <p><strong>Readiness:</strong> {html.escape(readiness_map.get(review.readiness, review.readiness))}</p>
        <p><strong>Trend:</strong> <span class="badge {trend_badge_class}">{html.escape(trend_label_map.get(trend_direction, trend_direction))}</span></p>
        <p><strong>Trend summary:</strong> {html.escape(trend_summary)}</p>
        <p><strong>Generated:</strong> {generated_at}</p>
      </aside>
    </section>

    <section class="panel stack">
      <h2>Ship Gate</h2>
      <p>{html.escape(ship.summary)}</p>
      <div class="grid">{ship_checks_html}</div>
      <div class="grid">
        <article class="mini-card">
          <span>benchmark</span>
          <strong>retrieval quality</strong>
          <small>{html.escape(benchmark_html)}</small>
          <p>RepoBrain uses this as a lightweight release signal instead of relying on intuition alone.</p>
        </article>
        {delta_html or '<article class="mini-card"><span>baseline drift</span><strong>No baseline yet</strong><small>Run repobrain baseline</small><p>Save a stable snapshot after hardening so future scans can detect regressions automatically.</p></article>'}
      </div>
      <div class="mini-card">
        <span>what is already solid</span>
        <ul>{highlights_html}</ul>
      </div>
      <div class="mini-card">
        <span>ship next steps</span>
        <ul>{ship_next_steps_html}</ul>
      </div>
    </section>

    <section class="panel stack">
      <h2>Provider Posture</h2>
      <p>See which provider path is active, whether network-backed paths are ready, and which Gemini rerank models are available for failover.</p>
      <div class="grid">{provider_cards}</div>
      <div class="grid">
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

    <section class="panel stack">
      <h2>Baseline Trend</h2>
      <p>{html.escape(trend_summary)}</p>
      <div class="grid">
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

    <section class="panel stack">
      <h2>Project Review</h2>
      <p>{html.escape(review.summary)}</p>
      <div class="grid">{review_cards}</div>
      <div class="mini-card">
        <span>what to fix first</span>
        <ul>{next_steps_html}</ul>
      </div>
    </section>

    <section class="panel stack">
      <h2>Parsers</h2>
      <div class="grid">{parser_cards}</div>
    </section>

    <section class="panel stack">
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
