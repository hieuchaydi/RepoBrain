from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from repobrain.config import RepoBrainConfig
from repobrain.engine.patch_review import PatchReviewer
from repobrain.engine.providers import build_provider_bundle, inspect_provider_status, tokenize
from repobrain.engine.scanner import RepositoryScanner
from repobrain.engine.store import MetadataStore
from repobrain.models import (
    EditTarget,
    FileEvidence,
    PatchReviewReport,
    QueryIntent,
    QueryPlan,
    QueryResult,
    ReadinessCheck,
    ReviewFocus,
    ReviewReport,
    SearchHit,
    ShipReport,
)
from repobrain.prompt_pack import build_prompt_pack
from repobrain.review import ProjectReviewer
from repobrain.review_store import ReviewArtifactsStore


BENCHMARK_CASES = [
    {"query": "Where is payment retry logic implemented?", "expected": ["payment_retry_job.py", "retry_handler.py", "auth_service.py"]},
    {"query": "Trace login with Google from route to service", "expected": ["auth.py", "auth_service.py", "login.ts"]},
    {"query": "What breaks if I change auth callback handling?", "expected": ["auth.py", "oauth.ts", "auth_service.py"]},
]


@dataclass(slots=True)
class BenchmarkReport:
    cases_run: int
    recall_at_3: float
    mrr: float
    citation_accuracy: float
    edit_target_hit_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "cases_run": self.cases_run,
            "recall_at_3": round(self.recall_at_3, 3),
            "mrr": round(self.mrr, 3),
            "citation_accuracy": round(self.citation_accuracy, 3),
            "edit_target_hit_rate": round(self.edit_target_hit_rate, 3),
        }


@dataclass(slots=True)
class QueryProfile:
    tokens: set[str]
    preferred_roles: set[str]
    focus_terms: list[str]
    include_tests: bool = False


class RepoBrainEngine:
    def __init__(self, repo_root: str | Path) -> None:
        self.config = RepoBrainConfig.load(repo_root)
        self.providers = build_provider_bundle(self.config)
        self.scanner = RepositoryScanner(self.config)
        self.store = MetadataStore(self.config)
        self.reviewer = ProjectReviewer(self.config, self.scanner)
        self.review_artifacts = ReviewArtifactsStore(self.config)
        self.patch_reviewer = PatchReviewer(self.config, self.scanner, self.store, self.providers.embedder)

    def init_workspace(self, force: bool = False) -> dict[str, str]:
        self.config.state_path.mkdir(parents=True, exist_ok=True)
        self.config.vectors_dir.mkdir(parents=True, exist_ok=True)
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        config_path = self.config.write_default(force=force)
        return {"repo_root": str(self.config.resolved_repo_root), "config_path": str(config_path), "state_dir": str(self.config.state_path)}

    def index_repository(self, *, include_review: bool = False) -> dict[str, object]:
        candidates = self.scanner.scan()
        documents = [self.scanner.parse(candidate) for candidate in candidates]
        stats = self.store.replace_documents(documents, self.providers.embedder)
        parser_counts: dict[str, int] = defaultdict(int)
        for document in documents:
            parser_counts[document.parser_name] += 1
        stats["parsers"] = dict(sorted(parser_counts.items()))
        stats["repo_root"] = str(self.config.resolved_repo_root)
        if include_review:
            review = self.reviewer.review_from_documents(documents)
            self._attach_index_stats_to_review(review, stats)
            stats["review"] = review.to_dict()
            stats["import_assessment"] = self._import_assessment(stats, review)
        return stats

    def query(
        self,
        query: str,
        forced_intent: QueryIntent | None = None,
        limit: int = 6,
        context: str | None = None,
    ) -> QueryResult:
        if not self.store.indexed():
            raise RuntimeError("Repository has not been indexed yet. Run `repobrain index` first.")

        intent = forced_intent or self._classify_intent(query)
        profile = self._build_query_profile(query, intent, context=context)
        rewritten = self._rewrite_query(query, intent, profile, context=context)
        plan = QueryPlan(intent=intent, steps=self._plan_steps(intent), rewritten_queries=rewritten)

        fused_hits: dict[int, SearchHit] = {}
        for variant_index, variant in enumerate(rewritten):
            for rank, hit in enumerate(self.store.search_fts(variant, limit=limit * 2), start=1):
                self._merge_hit(fused_hits, hit, source="fts", rank=rank, variant_index=variant_index)
            for rank, hit in enumerate(self.store.search_vectors(variant, self.providers.embedder, limit=limit * 2), start=1):
                self._merge_hit(fused_hits, hit, source="vector", rank=rank, variant_index=variant_index)

        reranked_hits = self._rerank(query, intent, profile, list(fused_hits.values()))
        top_hits = reranked_hits[:limit]
        top_files = self._build_top_files(top_hits)
        dependency_edges = self.store.get_edges_for_files([item.file_path for item in top_files], limit=14)
        call_chain = self._build_call_chain(dependency_edges)
        edit_targets = self._build_edit_targets(intent, top_files, dependency_edges)
        query_tokens = set(tokenize(query))
        confidence = self._confidence(intent, profile, top_hits, dependency_edges)
        confidence_label = self._confidence_label(confidence)
        warnings = self._warnings(
            query,
            intent,
            confidence,
            confidence_label,
            top_hits,
            dependency_edges,
            query_tokens=query_tokens,
        )
        next_questions = self._next_questions(intent, top_hits, warnings, confidence_label)
        confidence_summary = self._confidence_summary(
            intent,
            confidence_label,
            top_hits,
            dependency_edges,
            warnings,
            query_tokens=query_tokens,
        )

        return QueryResult(
            query=query,
            intent=intent,
            top_files=top_files,
            snippets=top_hits,
            call_chain=call_chain,
            dependency_edges=dependency_edges,
            edit_targets=edit_targets,
            confidence=confidence,
            warnings=warnings,
            next_questions=next_questions,
            plan=plan,
            confidence_label=confidence_label,
            confidence_summary=confidence_summary,
        )

    def trace(self, query: str, *, context: str | None = None) -> QueryResult:
        return self.query(query, forced_intent=QueryIntent.TRACE, context=context)

    def impact(self, query: str, *, context: str | None = None) -> QueryResult:
        return self.query(query, forced_intent=QueryIntent.IMPACT, context=context)

    def targets(self, query: str, *, context: str | None = None) -> QueryResult:
        return self.query(query, forced_intent=QueryIntent.CHANGE, context=context)

    def build_change_context(self, query: str) -> dict[str, object]:
        result = self.targets(query)
        top_file_map = {item.file_path: item for item in result.top_files}
        edit_targets: list[dict[str, object]] = []
        for item in result.edit_targets[:3]:
            payload = item.to_dict()
            support = top_file_map.get(item.file_path)
            if support is not None:
                payload["role"] = support.role
                payload["evidence_score"] = round(support.score, 3)
                payload["supporting_reasons"] = support.reasons[:4]
            edit_targets.append(payload)

        return {
            "query": result.query,
            "intent": result.intent.value,
            "top_files": [item.to_dict() for item in result.top_files[:4]],
            "edit_targets": edit_targets,
            "supporting_snippets": [self._change_context_snippet(hit) for hit in result.snippets[:3]],
            "warnings": result.warnings,
            "risk_notes": result.warnings[:3],
            "confidence": result.confidence,
            "confidence_label": result.confidence_label,
            "confidence_summary": result.confidence_summary,
            "evidence_summary": self._change_context_evidence_summary(result),
            "next_questions": result.next_questions,
            "plan_steps": result.plan.steps,
        }

    def patch_review(self, base: str | None = None, files: list[str] | None = None) -> PatchReviewReport:
        return self.patch_reviewer.review(base=base, files=files)

    def prompt_pack(
        self,
        *,
        source: str = "review",
        focus: ReviewFocus = ReviewFocus.FULL,
        baseline_label: str = "baseline",
        base: str | None = None,
        files: list[str] | None = None,
        flow_query: str | None = None,
        score_threshold: float = 0.7,
        style: str = "generic",
        max_prompts: int = 6,
    ) -> dict[str, object]:
        normalized_source = source.strip().lower()
        repo_root = str(self.config.resolved_repo_root)
        if normalized_source == "review":
            payload = self.review(focus=focus).to_dict()
        elif normalized_source == "ship":
            payload = self.ship(baseline_label=baseline_label).to_dict()
        elif normalized_source == "patch-review":
            payload = self.patch_review(base=base, files=files).to_dict()
        elif normalized_source == "import":
            review = self.review(focus=focus, compare_baseline=False)
            stats = self.store.stats() if self.store.indexed() else {"files": 0, "chunks": 0, "symbols": 0, "edges": 0}
            payload = self._import_assessment(stats, review)
        elif normalized_source == "flow":
            payload = self._flow_assessment(flow_query or "login flow", score_threshold=score_threshold)
        else:
            raise ValueError("`source` must be one of: review, ship, patch-review, import, flow.")

        return build_prompt_pack(
            source=normalized_source,
            repo_root=repo_root,
            payload=payload,
            style=style,
            max_prompts=max_prompts,
        )

    def doctor(self) -> dict[str, object]:
        provider_status = inspect_provider_status(self.config)
        remote_enabled = any(not status["local_only"] for status in provider_status.values())
        providers: dict[str, object] = {
            "embedding": self.providers.embedder.name,
            "reranker": self.providers.reranker.name,
            "embedding_model": getattr(self.providers.embedder, "model", "n/a"),
            "reranker_model": getattr(self.providers.reranker, "model", "n/a"),
        }
        if hasattr(self.providers.reranker, "models"):
            providers["reranker_models"] = list(getattr(self.providers.reranker, "models"))
        if hasattr(self.providers.reranker, "last_failover_error"):
            providers["reranker_last_failover_error"] = getattr(self.providers.reranker, "last_failover_error")
        return {
            "repo_root": str(self.config.resolved_repo_root),
            "config_path": str(self.config.config_path),
            "state_dir": str(self.config.state_path),
            "indexed": self.store.indexed(),
            "stats": self.store.stats() if self.store.indexed() else {"files": 0, "chunks": 0, "symbols": 0, "edges": 0},
            "providers": providers,
            "provider_status": provider_status,
            "security": {
                "local_storage_only": True,
                "remote_providers_enabled": remote_enabled,
                "network_required": any(status["requires_network"] for status in provider_status.values() if not status["local_only"]),
                "mcp_transport": "stdio-json",
            },
            "capabilities": self.scanner.capabilities(),
        }

    def provider_smoke(self) -> dict[str, object]:
        doctor = self.doctor()
        providers = doctor.get("providers", {}) if isinstance(doctor.get("providers"), dict) else {}
        embedding_result: dict[str, object]
        reranker_result: dict[str, object]

        try:
            vectors = self.providers.embedder.embed(["RepoBrain provider smoke embedding sample"])
            first_vector = vectors[0] if vectors else []
            embedding_result = {
                "status": "pass",
                "vector_count": len(vectors),
                "dimensions": len(first_vector),
            }
        except Exception as exc:
            embedding_result = {
                "status": "error",
                "error": str(exc),
            }

        reranker_before = getattr(self.providers.reranker, "model", None)
        reranker_pool = list(getattr(self.providers.reranker, "models", [])) if hasattr(self.providers.reranker, "models") else []
        try:
            score = self.providers.reranker.score(
                "Where is the auth callback handled?",
                "The auth callback route calls the auth service to exchange the provider code.",
            )
            reranker_result = {
                "status": "pass",
                "score": round(float(score), 6),
                "active_model_before": reranker_before,
                "active_model_after": getattr(self.providers.reranker, "model", None),
                "pool": reranker_pool,
                "last_failover_error": getattr(self.providers.reranker, "last_failover_error", None),
            }
        except Exception as exc:
            reranker_result = {
                "status": "error",
                "error": str(exc),
                "active_model_before": reranker_before,
                "active_model_after": getattr(self.providers.reranker, "model", None),
                "pool": reranker_pool,
                "last_failover_error": getattr(self.providers.reranker, "last_failover_error", None),
            }

        return {
            "repo_root": str(self.config.resolved_repo_root),
            "providers": providers,
            "provider_status": doctor.get("provider_status", {}),
            "embedding_smoke": embedding_result,
            "reranker_smoke": reranker_result,
        }

    def review(
        self,
        focus: ReviewFocus = ReviewFocus.FULL,
        max_findings: int = 6,
        compare_baseline: bool = True,
        baseline_label: str = "baseline",
    ) -> ReviewReport:
        report = self.reviewer.review(focus=focus, max_findings=max_findings)
        self._attach_index_stats_to_review(report)
        if compare_baseline:
            report.delta = self.review_artifacts.compare(report, label=baseline_label)
        return report

    def _attach_index_stats_to_review(
        self,
        report: ReviewReport,
        index_stats: dict[str, object] | None = None,
    ) -> None:
        indexed = bool(index_stats) or self.store.indexed()
        report.stats["indexed"] = indexed
        if indexed:
            stats = index_stats or self.store.stats()
            report.stats["indexed_files"] = int(stats.get("files", 0) or 0)
            report.stats["indexed_chunks"] = int(stats.get("chunks", 0) or 0)

    def _import_assessment(self, stats: dict[str, object], review: ReviewReport) -> dict[str, object]:
        top_findings = [
            {
                "severity": finding.severity.value,
                "category": finding.category,
                "title": finding.title,
                "file_paths": finding.file_paths[:4],
            }
            for finding in review.findings[:3]
        ]
        return {
            "kind": "import_assessment",
            "repo_root": str(self.config.resolved_repo_root),
            "readiness": review.readiness,
            "score": round(review.score, 1),
            "summary": review.summary,
            "top_findings": top_findings,
            "next_steps": review.next_steps[:3],
            "index": {
                "files": int(stats.get("files", 0) or 0),
                "chunks": int(stats.get("chunks", 0) or 0),
                "symbols": int(stats.get("symbols", 0) or 0),
                "edges": int(stats.get("edges", 0) or 0),
            },
        }

    def _flow_assessment(self, flow_query: str, *, score_threshold: float) -> dict[str, object]:
        normalized_query = flow_query.strip() or "login flow"
        threshold = max(0.0, min(float(score_threshold), 1.0))
        trace_result = self.trace(normalized_query)
        impact_result = self.impact(f"What breaks if {normalized_query} changes?")
        targets_result = self.targets(f"Where should we patch {normalized_query}?")

        entry_files = self._unique_nonempty(
            [item.file_path for item in trace_result.top_files[:4]]
            + [item.file_path for item in impact_result.top_files[:3]],
            limit=10,
        )
        edit_targets = self._unique_nonempty([item.file_path for item in targets_result.edit_targets[:5]], limit=8)
        flow_edges = self._unique_nonempty(
            [self._format_flow_edge(edge) for edge in trace_result.dependency_edges[:10]],
            limit=10,
        )
        combined_hits = [*trace_result.snippets[:4], *impact_result.snippets[:4], *targets_result.snippets[:4]]
        input_contracts = self._flow_contract_clues(combined_hits, direction="input")
        output_contracts = self._flow_contract_clues(combined_hits, direction="output")
        type_risks = self._flow_type_risks(combined_hits)
        warnings = self._unique_nonempty(
            [*trace_result.warnings, *impact_result.warnings, *targets_result.warnings],
            limit=10,
        )
        bottlenecks = self._flow_bottlenecks(
            trace_result=trace_result,
            flow_edges=flow_edges,
            input_contracts=input_contracts,
            output_contracts=output_contracts,
            type_risks=type_risks,
            warnings=warnings,
        )
        next_steps = self._flow_next_steps(
            bottlenecks=bottlenecks,
            type_risks=type_risks,
            input_contracts=input_contracts,
            output_contracts=output_contracts,
            targets_result=targets_result,
        )
        file_scores = self._flow_file_scores(
            trace_result=trace_result,
            impact_result=impact_result,
            targets_result=targets_result,
        )
        low_score_files = [item for item in file_scores if float(item.get("score", 0.0) or 0.0) < threshold]
        summary = (
            f"Flow audit for `{normalized_query}` found {len(bottlenecks)} bottleneck(s), "
            f"{len(type_risks)} type-risk signal(s), and {len(flow_edges)} structural edge hint(s). "
            f"{len(low_score_files)} file(s) scored below {threshold:.2f} and need fix prompts."
        )
        return {
            "kind": "flow_assessment",
            "flow_query": normalized_query,
            "summary": summary,
            "score_threshold": round(threshold, 2),
            "entry_files": entry_files,
            "edit_targets": edit_targets,
            "file_scores": file_scores,
            "flow_edges": flow_edges,
            "input_contracts": input_contracts,
            "output_contracts": output_contracts,
            "type_risks": type_risks,
            "bottlenecks": bottlenecks,
            "warnings": warnings,
            "next_steps": next_steps,
            "confidence": {
                "trace": trace_result.confidence_label or f"{trace_result.confidence:.3f}",
                "impact": impact_result.confidence_label or f"{impact_result.confidence:.3f}",
                "targets": targets_result.confidence_label or f"{targets_result.confidence:.3f}",
            },
        }

    def _flow_file_scores(
        self,
        *,
        trace_result: QueryResult,
        impact_result: QueryResult,
        targets_result: QueryResult,
    ) -> list[dict[str, object]]:
        trace_norm = self._normalized_file_scores([(item.file_path, item.score) for item in trace_result.top_files[:6]])
        impact_norm = self._normalized_file_scores([(item.file_path, item.score) for item in impact_result.top_files[:6]])
        target_norm = self._normalized_file_scores([(item.file_path, item.score) for item in targets_result.edit_targets[:6]])
        role_map = {
            item.file_path: item.role
            for item in [*trace_result.top_files[:6], *impact_result.top_files[:6]]
        }
        reason_map = {
            item.file_path: item.reasons[:3]
            for item in [*trace_result.top_files[:6], *impact_result.top_files[:6]]
        }
        target_reason_map = {
            item.file_path: item.rationale
            for item in targets_result.edit_targets[:6]
        }
        trace_conf = trace_result.confidence
        impact_conf = impact_result.confidence
        target_conf = targets_result.confidence

        file_paths = set(trace_norm) | set(impact_norm) | set(target_norm)
        scored: list[dict[str, object]] = []
        for file_path in sorted(file_paths):
            source_scores: list[float] = []
            source_labels: list[str] = []
            confidence_scores: list[float] = []
            if file_path in trace_norm:
                source_scores.append(trace_norm[file_path])
                source_labels.append("trace")
                confidence_scores.append(trace_conf)
            if file_path in impact_norm:
                source_scores.append(impact_norm[file_path])
                source_labels.append("impact")
                confidence_scores.append(impact_conf)
            if file_path in target_norm:
                source_scores.append(target_norm[file_path])
                source_labels.append("targets")
                confidence_scores.append(target_conf)
            if not source_scores:
                continue
            mean_signal = sum(source_scores) / len(source_scores)
            source_coverage = len(source_scores) / 3.0
            confidence_signal = sum(confidence_scores) / len(confidence_scores)
            support_score = min(
                1.0,
                (mean_signal * 0.58) + (source_coverage * 0.24) + (confidence_signal * 0.18),
            )
            reasons = reason_map.get(file_path, [])
            target_rationale = target_reason_map.get(file_path)
            if target_rationale:
                reasons = [*reasons, target_rationale]
            scored.append(
                {
                    "file_path": file_path,
                    "score": round(support_score, 3),
                    "role": role_map.get(file_path, "module"),
                    "sources": source_labels,
                    "reasons": reasons[:4],
                }
            )
        return sorted(scored, key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)[:10]

    def _normalized_file_scores(self, values: list[tuple[str, float]]) -> dict[str, float]:
        cleaned = [(path, float(score)) for path, score in values if str(path).strip()]
        if not cleaned:
            return {}
        max_score = max(score for _, score in cleaned)
        if max_score <= 0:
            return {path: 0.0 for path, _ in cleaned}
        return {path: min(float(score) / max_score, 1.0) for path, score in cleaned}

    def _flow_contract_clues(self, hits: list[SearchHit], *, direction: str) -> list[str]:
        if direction == "input":
            terms = (
                "request",
                "req",
                "params",
                "payload",
                "body",
                "query",
                "headers",
                "token",
                "validate",
            )
        else:
            terms = (
                "return",
                "response",
                "respond",
                "json(",
                "status",
                "result",
                "error",
                "raise",
            )
        clues: list[str] = []
        for hit in hits[:10]:
            for raw_line in hit.content.splitlines():
                line = " ".join(raw_line.strip().split())
                if not line:
                    continue
                lower = line.lower()
                if not any(term in lower for term in terms):
                    continue
                clue = f"{hit.file_path}:{hit.start_line}-{hit.end_line} -> {line[:140]}"
                if clue not in clues:
                    clues.append(clue)
                break
            if len(clues) >= 8:
                break
        return clues

    def _flow_type_risks(self, hits: list[SearchHit]) -> list[str]:
        patterns: list[tuple[re.Pattern[str], str]] = [
            (re.compile(r"\bas any\b"), "Type assertion uses `any`; enforce explicit contract."),
            (re.compile(r"\bany\b"), "Dynamic `any` typing found on a flow boundary."),
            (re.compile(r"\bunknown\b"), "`unknown` value should be narrowed before use."),
            (re.compile(r"dict\s*\[\s*str\s*,\s*any\s*\]"), "Weak dict typing with `Any` detected."),
            (re.compile(r"\bjson\.loads\("), "Parsed JSON should be validated before downstream use."),
            (re.compile(r"\bparseint\("), "Numeric parsing requires explicit NaN/failure handling."),
            (re.compile(r"\.get\("), "Dictionary `.get` can hide missing required fields."),
        ]
        findings: list[str] = []
        for hit in hits[:10]:
            content = hit.content.lower()
            for pattern, message in patterns:
                if not pattern.search(content):
                    continue
                finding = f"{hit.file_path}:{hit.start_line}-{hit.end_line} -> {message}"
                if finding not in findings:
                    findings.append(finding)
                break
            if len(findings) >= 8:
                break
        return findings

    def _flow_bottlenecks(
        self,
        *,
        trace_result: QueryResult,
        flow_edges: list[str],
        input_contracts: list[str],
        output_contracts: list[str],
        type_risks: list[str],
        warnings: list[str],
    ) -> list[str]:
        bottlenecks: list[str] = []
        if trace_result.confidence_label in {"exploratory", "weak"}:
            bottlenecks.append(
                f"Trace confidence is {trace_result.confidence_label}; flow grounding is still weak."
            )
        if not flow_edges:
            bottlenecks.append("No dependency edge hints were found for this flow; manual hop tracing is required.")
        if not input_contracts:
            bottlenecks.append("Input contract clues are missing near entry boundaries.")
        if not output_contracts:
            bottlenecks.append("Output contract clues are missing near response boundaries.")
        if type_risks:
            bottlenecks.append(f"Detected {len(type_risks)} potential type-risk surface(s) in this flow.")
        for warning in warnings[:4]:
            bottlenecks.append(f"Warning: {warning}")
        return self._unique_nonempty(bottlenecks, limit=8)

    def _flow_next_steps(
        self,
        *,
        bottlenecks: list[str],
        type_risks: list[str],
        input_contracts: list[str],
        output_contracts: list[str],
        targets_result: QueryResult,
    ) -> list[str]:
        steps: list[str] = []
        if not input_contracts:
            steps.append("Define and enforce request/input schema at the first flow boundary.")
        if not output_contracts:
            steps.append("Define explicit output contract (success + error) for downstream consumers.")
        if type_risks:
            steps.append("Replace weakly-typed payload handling with explicit contract checks.")
        if bottlenecks:
            steps.append("Patch the smallest bottleneck first and re-run trace/impact to confirm flow continuity.")
        steps.extend(targets_result.next_questions[:2])
        if not steps:
            steps.append("Use top edit targets to add regression tests for happy path and failure path.")
        return self._unique_nonempty(steps, limit=6)

    def _format_flow_edge(self, edge: dict[str, str | None]) -> str:
        source_file = str(edge.get("source_file", "") or "").strip()
        source_symbol = str(edge.get("source_symbol", "") or "").strip()
        target = str(edge.get("target", "") or "").strip()
        edge_type = str(edge.get("edge_type", "") or "calls").strip() or "calls"
        target_file = str(edge.get("target_file", "") or "").strip()
        if not source_file and not target:
            return ""
        left = f"{source_file}::{source_symbol}" if source_symbol else (source_file or "unknown_source")
        right = target_file or target or "unknown_target"
        return f"{left} --{edge_type}--> {right}"

    def _unique_nonempty(self, values: list[str], *, limit: int) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            if not text or text in seen:
                continue
            deduped.append(text)
            seen.add(text)
            if len(deduped) >= limit:
                break
        return deduped

    def save_review_baseline(self, report: ReviewReport, label: str = "baseline") -> dict[str, str]:
        saved = self.review_artifacts.save_baseline(report, label=label)
        saved["repo_root"] = str(self.config.resolved_repo_root)
        return saved

    def ship(self, baseline_label: str = "baseline") -> ShipReport:
        doctor = self.doctor()
        review = self.review(compare_baseline=True, baseline_label=baseline_label)
        history = self.review_artifacts.history_summary(review, label=baseline_label)
        benchmark = self.benchmark().to_dict() if doctor["indexed"] else None
        checks = self._build_ship_checks(doctor=doctor, review=review, benchmark=benchmark)
        status = self._ship_status(checks)
        blockers = self._ship_blockers(checks, review)
        highlights = self._ship_highlights(checks, review, benchmark, history)
        next_steps = self._ship_next_steps(checks, review, baseline_label)
        score = self._ship_score(review, checks)
        summary = self._ship_summary(status=status, checks=checks, blockers=blockers, review=review)
        return ShipReport(
            repo_root=str(self.config.resolved_repo_root),
            status=status,
            score=score,
            summary=summary,
            checks=checks,
            blockers=blockers,
            highlights=highlights,
            next_steps=next_steps,
            doctor=doctor,
            review=review,
            benchmark=benchmark,
            history=history,
        )

    def benchmark(self) -> BenchmarkReport:
        if not self.store.indexed():
            raise RuntimeError("Repository has not been indexed yet. Run `repobrain index` first.")

        recall_hits = 0
        reciprocal_ranks: list[float] = []
        citation_hits = 0
        edit_target_hits = 0

        for case in BENCHMARK_CASES:
            result = self.query(case["query"])
            expected = case["expected"]
            top_file_paths = [item.file_path for item in result.top_files[:3]]
            edit_paths = [item.file_path for item in result.edit_targets[:3]]

            matched_rank = 0.0
            for index, path in enumerate(top_file_paths, start=1):
                if any(token in path for token in expected):
                    matched_rank = 1 / index
                    break
            reciprocal_ranks.append(matched_rank)
            if matched_rank:
                recall_hits += 1
                citation_hits += 1
            if any(any(token in path for token in expected) for path in edit_paths):
                edit_target_hits += 1

        total = len(BENCHMARK_CASES)
        return BenchmarkReport(
            cases_run=total,
            recall_at_3=recall_hits / total,
            mrr=sum(reciprocal_ranks) / total,
            citation_accuracy=citation_hits / total,
            edit_target_hit_rate=edit_target_hits / total,
        )

    def _build_ship_checks(
        self,
        *,
        doctor: dict[str, object],
        review: ReviewReport,
        benchmark: dict[str, object] | None,
    ) -> list[ReadinessCheck]:
        checks: list[ReadinessCheck] = []
        stats = doctor.get("stats", {}) if isinstance(doctor.get("stats", {}), dict) else {}
        indexed = bool(doctor.get("indexed"))
        if indexed:
            checks.append(
                ReadinessCheck(
                    name="index",
                    status="pass",
                    summary=f"Index is ready with {stats.get('files', 0)} files, {stats.get('chunks', 0)} chunks, and {stats.get('edges', 0)} edges.",
                )
            )
        else:
            checks.append(
                ReadinessCheck(
                    name="index",
                    status="fail",
                    summary="Repository has not been indexed yet, so retrieval and benchmark checks are incomplete.",
                    detail="Run `repobrain index` before using ship readiness as a release gate.",
                )
            )

        review_status = {
            "not_ready": "fail",
            "needs_hardening": "warn",
            "promising": "pass",
        }.get(review.readiness, "warn")
        review_detail = ""
        if review.delta is not None:
            review_detail = (
                f"Baseline {review.delta.baseline_label} from {review.delta.baseline_saved_at or 'unknown'} "
                f"is {review.delta.status} with score delta {review.delta.score_delta:+.1f}."
            )
            if review.delta.status == "regressed" and review_status != "fail":
                review_status = "fail"
        checks.append(
            ReadinessCheck(
                name="review",
                status=review_status,
                summary=f"Project review is {review.readiness} at {review.score:.1f}/10.",
                detail=review_detail,
            )
        )

        checks.append(self._provider_ship_check(doctor))
        checks.append(self._parser_ship_check(doctor))
        checks.append(self._benchmark_ship_check(benchmark))
        return checks

    def _provider_ship_check(self, doctor: dict[str, object]) -> ReadinessCheck:
        provider_status = doctor.get("provider_status", {})
        if not isinstance(provider_status, dict):
            return ReadinessCheck(name="providers", status="warn", summary="Provider status is unavailable.")

        failing: list[str] = []
        remote_enabled = False
        for kind, payload in sorted(provider_status.items()):
            if not isinstance(payload, dict):
                continue
            if not payload.get("local_only", True):
                remote_enabled = True
            if payload.get("ready", False):
                continue
            missing = ", ".join(str(item) for item in payload.get("missing", [])) or "unknown dependency"
            failing.append(f"{kind}: {missing}")

        if failing:
            return ReadinessCheck(
                name="providers",
                status="fail",
                summary="Configured providers are not fully ready for production use.",
                detail="; ".join(failing),
            )
        if remote_enabled:
            return ReadinessCheck(
                name="providers",
                status="warn",
                summary="Remote providers are enabled and healthy.",
                detail="Confirm network policy, latency expectations, and code-sharing rules before using hosted providers in production.",
            )
        return ReadinessCheck(
            name="providers",
            status="pass",
            summary="Providers are local-only, so retrieval stays on-device by default.",
        )

    def _parser_ship_check(self, doctor: dict[str, object]) -> ReadinessCheck:
        capabilities = doctor.get("capabilities", {})
        if not isinstance(capabilities, dict):
            return ReadinessCheck(name="parsers", status="warn", summary="Parser capability data is unavailable.")

        language_parsers = capabilities.get("language_parsers", {})
        if not isinstance(language_parsers, dict):
            return ReadinessCheck(name="parsers", status="warn", summary="Language parser selection data is unavailable.")

        enabled_languages = [
            language
            for language, detail in sorted(language_parsers.items())
            if isinstance(detail, dict) and detail.get("tree_sitter_enabled", False)
        ]
        optional_selected = [
            language
            for language in enabled_languages
            if isinstance(language_parsers.get(language), dict) and language_parsers[language].get("selected") != "heuristic"
        ]
        if not enabled_languages:
            return ReadinessCheck(name="parsers", status="pass", summary="Parser fallback is available for all supported languages.")
        if len(optional_selected) == len(enabled_languages):
            return ReadinessCheck(
                name="parsers",
                status="pass",
                summary=f"Preferred parser path is active for {', '.join(optional_selected)}.",
            )
        if optional_selected:
            missing = [language for language in enabled_languages if language not in optional_selected]
            return ReadinessCheck(
                name="parsers",
                status="warn",
                summary=f"Preferred parser path is only active for {', '.join(optional_selected)}.",
                detail=f"Heuristic fallback is still covering {', '.join(missing)}.",
            )
        return ReadinessCheck(
            name="parsers",
            status="warn",
            summary="Tree-sitter is preferred, but heuristic fallback is carrying all enabled languages.",
            detail="Install tree-sitter extras if you want stronger symbol ranges and parser fidelity.",
        )

    def _benchmark_ship_check(self, benchmark: dict[str, object] | None) -> ReadinessCheck:
        if benchmark is None:
            return ReadinessCheck(
                name="benchmark",
                status="warn",
                summary="Benchmark is not available yet because the repo is not indexed.",
            )

        recall = float(benchmark.get("recall_at_3", 0.0))
        edit_hit = float(benchmark.get("edit_target_hit_rate", 0.0))
        mrr = float(benchmark.get("mrr", 0.0))
        summary = f"Benchmark recall@3={recall:.3f}, mrr={mrr:.3f}, edit_target_hit_rate={edit_hit:.3f}."
        if recall >= 0.67 and edit_hit >= 0.67 and mrr >= 0.45:
            return ReadinessCheck(name="benchmark", status="pass", summary=summary)
        if recall >= 0.34 and edit_hit >= 0.34:
            return ReadinessCheck(
                name="benchmark",
                status="warn",
                summary=summary,
                detail="Retrieval is usable, but benchmark quality should improve before treating it as a strong release gate.",
            )
        return ReadinessCheck(
            name="benchmark",
            status="fail",
            summary=summary,
            detail="Benchmark signals are too weak for a confident production rollout.",
        )

    def _ship_status(self, checks: list[ReadinessCheck]) -> str:
        statuses = {check.status for check in checks}
        if "fail" in statuses:
            return "blocked"
        if "warn" in statuses:
            return "caution"
        return "ready"

    def _ship_blockers(self, checks: list[ReadinessCheck], review: ReviewReport) -> list[str]:
        blockers = [check.summary for check in checks if check.status == "fail"]
        high_signal = [finding.title for finding in review.findings if finding.severity.value in {"critical", "high"}]
        for title in high_signal:
            blocker = f"High-signal finding: {title}"
            if blocker not in blockers:
                blockers.append(blocker)
        return blockers[:5]

    def _ship_highlights(
        self,
        checks: list[ReadinessCheck],
        review: ReviewReport,
        benchmark: dict[str, object] | None,
        history: dict[str, object],
    ) -> list[str]:
        highlights = [check.summary for check in checks if check.status == "pass"]
        if benchmark is not None and not any(check.name == "benchmark" and check.status == "pass" for check in checks):
            highlights.append(
                "Benchmark is available, so retrieval quality can be tracked instead of guessed."
            )
        if review.delta is not None and review.delta.status == "improved":
            highlights.append(
                f"Review improved against baseline {review.delta.baseline_label} ({review.delta.score_delta:+.1f})."
            )
        if history.get("saved_snapshots", 0) and history.get("direction") == "improving":
            highlights.append(
                f"Baseline trend is improving over {history.get('saved_snapshots')} saved snapshot(s) ({float(history.get('score_change', 0.0)):+.1f})."
            )
        return highlights[:4]

    def _ship_next_steps(self, checks: list[ReadinessCheck], review: ReviewReport, baseline_label: str) -> list[str]:
        steps: list[str] = []
        for check in checks:
            if check.detail and check.detail not in steps and check.status != "pass":
                steps.append(check.detail)
            if len(steps) >= 2:
                break
        for step in review.next_steps:
            if step not in steps:
                steps.append(step)
            if len(steps) >= 4:
                break
        if review.delta is None:
            baseline_tip = f"Save a baseline with `repobrain baseline --label {baseline_label}` so future reviews can flag regressions."
            if baseline_tip not in steps:
                steps.append(baseline_tip)
        return steps[:4]

    def _ship_score(self, review: ReviewReport, checks: list[ReadinessCheck]) -> float:
        status_weight = {"pass": 1.0, "warn": 0.62, "fail": 0.0}
        weighted = sum(status_weight.get(check.status, 0.0) for check in checks)
        checks_score = (weighted / max(len(checks), 1)) * 10.0
        return round((review.score * 0.68) + (checks_score * 0.32), 1)

    def _ship_summary(
        self,
        *,
        status: str,
        checks: list[ReadinessCheck],
        blockers: list[str],
        review: ReviewReport,
    ) -> str:
        warn_count = sum(1 for check in checks if check.status == "warn")
        fail_count = sum(1 for check in checks if check.status == "fail")
        if status == "blocked":
            lead = blockers[0] if blockers else "High-signal release blockers remain."
            return f"Ship is blocked by {fail_count} failed gate(s) and {warn_count} warning gate(s). Start with: {lead}"
        if status == "caution":
            return (
                f"Ship can proceed with caution. RepoBrain found {warn_count} warning gate(s); "
                f"the main production posture is `{review.readiness}` at {review.score:.1f}/10."
            )
        return "Ship looks ready from the current local signals: index, review, parser posture, provider posture, and benchmark all passed."

    def _build_query_profile(self, query: str, intent: QueryIntent, *, context: str | None = None) -> QueryProfile:
        tokens = set(tokenize(query))
        tokens.update(tokenize(context or ""))
        preferred_roles = {"service"}
        if intent == QueryIntent.TRACE:
            preferred_roles.update({"route", "service"})
        elif intent == QueryIntent.IMPACT:
            preferred_roles.update({"service", "job", "config"})
        elif intent == QueryIntent.CHANGE:
            preferred_roles.update({"route", "service", "config"})

        if tokens.intersection({"route", "callback", "login", "auth", "webhook"}):
            preferred_roles.add("route")
        if tokens.intersection({"retry", "queue", "job", "worker", "cron"}):
            preferred_roles.update({"job", "service"})
        if tokens.intersection({"config", "provider", "env", "settings"}):
            preferred_roles.add("config")
        include_tests = bool(tokens.intersection({"test", "tests", "pytest", "unittest", "fixture", "fixtures", "spec", "coverage"}))
        if include_tests:
            preferred_roles.add("test")

        focus_terms = [
            token
            for token in sorted(tokens)
            if token in {"auth", "callback", "cron", "github", "google", "job", "login", "oauth", "payment", "queue", "retry", "webhook"}
        ]
        if not focus_terms:
            focus_terms = sorted(token for token in tokens if len(token) >= 5)[:5]

        return QueryProfile(tokens=tokens, preferred_roles=preferred_roles, focus_terms=focus_terms[:6], include_tests=include_tests)

    def _merge_hit(
        self,
        fused_hits: dict[int, SearchHit],
        hit: SearchHit,
        source: str,
        rank: int,
        variant_index: int,
    ) -> None:
        source_weight = 1.25 if source == "fts" else 1.0
        rrf_score = source_weight / (50 + rank)
        quality_weight = 0.45 if source == "fts" else 0.35
        variant_bonus = max(0.06 - (variant_index * 0.01), 0.0)
        delta = rrf_score + (hit.score * quality_weight) + variant_bonus

        existing = fused_hits.get(hit.chunk_id)
        if existing is None:
            reasons = sorted(set(hit.reasons))
            if variant_index > 0:
                reasons.append("multi_variant")
            fused_hits[hit.chunk_id] = SearchHit(
                chunk_id=hit.chunk_id,
                file_path=hit.file_path,
                language=hit.language,
                role=hit.role,
                symbol_name=hit.symbol_name,
                start_line=hit.start_line,
                end_line=hit.end_line,
                content=hit.content,
                score=round(delta, 6),
                reasons=reasons,
            )
            return

        existing.score = round(existing.score + delta, 6)
        existing.reasons.extend(reason for reason in hit.reasons if reason not in existing.reasons)
        if variant_index > 0 and "multi_variant" not in existing.reasons:
            existing.reasons.append("multi_variant")
        if "fts" in existing.reasons and "vector" in existing.reasons and "multi_source" not in existing.reasons:
            existing.reasons.append("multi_source")

    def _classify_intent(self, query: str) -> QueryIntent:
        tokens = set(tokenize(query))
        lowered = query.lower()
        if tokens.intersection({"trace", "flow", "route", "chain"}) or "route to" in lowered:
            return QueryIntent.TRACE
        if tokens.intersection({"impact", "affected", "breaks"}) or "what breaks" in lowered:
            return QueryIntent.IMPACT
        if tokens.intersection({"edit", "change", "add", "implement", "modify"}) or ("which" in tokens and "files" in tokens):
            return QueryIntent.CHANGE
        if tokens.intersection({"why", "how", "explain"}):
            return QueryIntent.EXPLAIN
        return QueryIntent.LOCATE

    def _rewrite_query(
        self,
        query: str,
        intent: QueryIntent,
        profile: QueryProfile,
        *,
        context: str | None = None,
    ) -> list[str]:
        variants = [query]
        tokens = sorted(profile.tokens)
        if tokens:
            variants.append(" ".join(tokens))
            symbolish = " ".join(token for token in tokens if "_" in token or token.endswith(("handler", "service", "job", "auth", "login", "callback")))
            if symbolish:
                variants.append(symbolish)
        if profile.focus_terms:
            variants.append(" ".join(profile.focus_terms))
        context_tokens = sorted(tokenize(context or ""))
        if context_tokens:
            variants.append(" ".join(context_tokens[:12]))
        if intent == QueryIntent.TRACE:
            variants.append(f"{query} call chain entrypoint callback dependency")
        if intent == QueryIntent.IMPACT:
            variants.append(f"{query} affected dependency blast radius callback config")
        if intent == QueryIntent.CHANGE:
            variants.append(f"{query} edit target patch callback provider")
        deduped: list[str] = []
        for item in variants:
            if item and item not in deduped:
                deduped.append(item)
        return deduped

    def _plan_steps(self, intent: QueryIntent) -> list[str]:
        common = ["planner", "retriever", "file_selector", "evidence_collector", "self_check"]
        if intent == QueryIntent.CHANGE:
            return ["planner", "retriever", "file_selector", "evidence_collector", "edit_target_scorer", "self_check"]
        return common

    def _rerank(self, query: str, intent: QueryIntent, profile: QueryProfile, hits: list[SearchHit]) -> list[SearchHit]:
        reranked: list[SearchHit] = []
        query_tokens = set(tokenize(query))
        for hit in hits:
            lexical = self.providers.reranker.score(query, f"{hit.file_path} {hit.symbol_name or ''} {hit.content}")
            path_tokens = set(tokenize(hit.file_path.replace("/", " ").replace(".", " ")))
            symbol_tokens = set(tokenize(hit.symbol_name or ""))
            path_bonus = (len(query_tokens & path_tokens) / max(len(query_tokens), 1)) * 0.45
            symbol_bonus = (len(query_tokens & symbol_tokens) / max(len(query_tokens), 1)) * 0.25
            role_bonus = 0.16 if hit.role in profile.preferred_roles else 0.0
            intent_bonus = 0.0
            if intent == QueryIntent.TRACE and hit.role in {"route", "service"}:
                intent_bonus = 0.08
            elif intent == QueryIntent.IMPACT and hit.role in {"service", "job", "config"}:
                intent_bonus = 0.08
            elif intent == QueryIntent.CHANGE and hit.role in {"route", "service", "config"}:
                intent_bonus = 0.1
            source_bonus = 0.12 if "multi_source" in hit.reasons else 0.0
            test_penalty = 0.0
            if hit.role == "test" and not profile.include_tests:
                test_penalty = 4.5
            hit.score = round(hit.score + lexical + path_bonus + symbol_bonus + role_bonus + intent_bonus + source_bonus - test_penalty, 6)
            if lexical and "reranked" not in hit.reasons:
                hit.reasons.append("reranked")
            if path_bonus and "path_overlap" not in hit.reasons:
                hit.reasons.append("path_overlap")
            if symbol_bonus and "symbol_overlap" not in hit.reasons:
                hit.reasons.append("symbol_overlap")
            if role_bonus and "role_match" not in hit.reasons:
                hit.reasons.append("role_match")
            if intent_bonus and "intent_match" not in hit.reasons:
                hit.reasons.append("intent_match")
            if test_penalty and "test_surface_penalty" not in hit.reasons:
                hit.reasons.append("test_surface_penalty")
            reranked.append(hit)
        return sorted(reranked, key=lambda item: item.score, reverse=True)

    def _build_top_files(self, hits: list[SearchHit]) -> list[FileEvidence]:
        records = self.store.get_file_records(sorted({hit.file_path for hit in hits}))
        record_map = {row["path"]: row for row in records}
        grouped_hits: dict[str, list[SearchHit]] = defaultdict(list)
        reasons: dict[str, set[str]] = defaultdict(set)
        for hit in hits:
            grouped_hits[hit.file_path].append(hit)
            if hit.symbol_name:
                reasons[hit.file_path].add(f"symbol:{hit.symbol_name}")
            reasons[hit.file_path].update(hit.reasons)
        files: list[FileEvidence] = []
        file_scores: list[tuple[str, float]] = []
        for file_path, file_hits in grouped_hits.items():
            sorted_scores = sorted((hit.score for hit in file_hits), reverse=True)
            score = sorted_scores[0]
            if len(sorted_scores) > 1:
                score += sum(sorted_scores[1:3]) * 0.35
            if "path_overlap" in reasons[file_path]:
                score += 0.1
            if "multi_source" in reasons[file_path]:
                score += 0.08
            if "path_overlap" not in reasons[file_path] and "symbol_overlap" not in reasons[file_path]:
                score -= 0.18
            file_scores.append((file_path, round(score, 6)))

        for file_path, score in sorted(file_scores, key=lambda item: item[1], reverse=True):
            row = record_map.get(file_path)
            language = row["language"] if row else "unknown"
            role = row["role"] if row else "module"
            files.append(
                FileEvidence(
                    file_path=file_path,
                    language=language,
                    role=role,
                    score=round(score, 6),
                    reasons=sorted(reasons[file_path]),
                )
            )
        return files[:6]

    def _build_call_chain(self, dependency_edges: list[dict[str, str | None]]) -> list[str]:
        chain: list[str] = []
        for edge in dependency_edges:
            chain.append(f"{edge['source_file']}::{edge['source_symbol']} --{edge['edge_type']}--> {edge['target']}")
        return chain[:8]

    def _build_edit_targets(
        self,
        intent: QueryIntent,
        top_files: list[FileEvidence],
        dependency_edges: list[dict[str, str | None]],
    ) -> list[EditTarget]:
        edge_counts: dict[str, int] = defaultdict(int)
        for edge in dependency_edges:
            edge_counts[str(edge["source_file"])] += 1
        results: list[EditTarget] = []
        for file in top_files:
            base = file.score
            if intent == QueryIntent.CHANGE and file.role in {"route", "service", "config"}:
                base += 0.25
            if intent == QueryIntent.IMPACT and file.role == "job":
                base += 0.15
            if "multi_source" in file.reasons:
                base += 0.1
            base += min(edge_counts.get(file.file_path, 0) * 0.04, 0.2)
            rationale = "High evidence density and dependency centrality."
            if file.role == "route":
                rationale = "Likely user-entry or callback surface for the requested flow."
            elif file.role == "service":
                rationale = "Contains business logic connected to the query."
            elif file.role == "job":
                rationale = "Participates in background or retry execution paths."
            results.append(EditTarget(file_path=file.file_path, score=round(base, 6), rationale=rationale))
        return sorted(results, key=lambda item: item.score, reverse=True)[:5]

    def _confidence(
        self,
        intent: QueryIntent,
        profile: QueryProfile,
        hits: list[SearchHit],
        dependency_edges: list[dict[str, str | None]],
    ) -> float:
        if not hits:
            return 0.05

        considered_hits = hits[:4]
        unique_files = {hit.file_path for hit in considered_hits}
        unique_roles = {hit.role for hit in considered_hits}
        multi_source_hits = sum(1 for hit in considered_hits if "multi_source" in hit.reasons)

        top_score = considered_hits[0].score
        runner_up = considered_hits[1].score if len(considered_hits) > 1 else top_score * 0.7
        gap = max(top_score - runner_up, 0.0)
        file_diversity = len(unique_files) / max(min(len(considered_hits), 4), 1)
        role_diversity = len(unique_roles) / max(min(len(considered_hits), 3), 1)
        source_diversity = multi_source_hits / max(len(considered_hits), 1)
        edge_support = min(len(dependency_edges) / 8, 1.0)
        token_overlap = self._best_evidence_overlap(profile.tokens, considered_hits)

        confidence = (
            0.16
            + min(top_score / 6.0, 0.24)
            + min(gap / 2.0, 0.16)
            + (source_diversity * 0.16)
            + (file_diversity * 0.1)
            + (edge_support * 0.12)
            + (token_overlap * 0.14)
        )
        if intent == QueryIntent.TRACE:
            confidence += role_diversity * 0.07

        if len(unique_files) == 1:
            confidence -= 0.14
        if multi_source_hits == 0:
            confidence -= 0.08
        if intent == QueryIntent.TRACE and len(unique_roles) < 2:
            confidence -= 0.08
        if top_score < 1.0:
            confidence -= 0.06
        if token_overlap < 0.12:
            confidence -= 0.12
        elif token_overlap < 0.2:
            confidence -= 0.06
        if intent == QueryIntent.CHANGE and not dependency_edges:
            confidence -= 0.05
        if not profile.include_tests and unique_roles == {"test"}:
            confidence -= 0.22

        return round(max(0.05, min(confidence, 0.97)), 3)

    def _warnings(
        self,
        query: str,
        intent: QueryIntent,
        confidence: float,
        confidence_label: str,
        hits: list[SearchHit],
        dependency_edges: list[dict[str, str | None]],
        *,
        query_tokens: set[str] | None = None,
    ) -> list[str]:
        warnings: list[str] = []
        query_tokens = set(query_tokens or tokenize(query))
        if confidence_label == "exploratory":
            warnings.append("Confidence band is exploratory. Treat the result as directional and confirm the exact source file before editing.")
        elif confidence_label == "weak":
            warnings.append("Confidence band is weak. Cross-check the lead files before planning a patch.")
        if not hits:
            warnings.append("No grounded evidence was found for this query.")
        if "github" in query.lower() and not any("github" in hit.content.lower() for hit in hits):
            warnings.append("GitHub-specific evidence is weak; inspect auth provider configuration manually.")
        if len({hit.file_path for hit in hits[:4]}) == 1:
            warnings.append("Evidence is concentrated in one file. Cross-check nearby routes, services, and config.")
        if hits and not any("multi_source" in hit.reasons for hit in hits[:4]):
            warnings.append("Evidence is dominated by one retrieval source. Cross-check lexical and semantic coverage.")
        if hits:
            best_overlap = self._best_evidence_overlap(query_tokens, hits[:4])
            if best_overlap < 0.2:
                warnings.append("Retrieved evidence has weak explicit token overlap with the query. Treat the result as exploratory.")
        if intent == QueryIntent.TRACE and len({hit.role for hit in hits[:4]}) < 2:
            warnings.append("Trace evidence lacks role diversity. Cross-check both route and service layers.")
        if hits and "test" not in query_tokens and len({hit.role for hit in hits[:4]}) == 1 and hits[0].role == "test":
            warnings.append("Evidence only appears in test files. Inspect runtime source files before editing.")
        if intent == QueryIntent.CHANGE and not dependency_edges:
            warnings.append("Edit-target suggestions have limited structural edge support. Review imports and callbacks manually.")
        warnings.extend(self._contradiction_warnings(query_tokens, hits))
        deduped: list[str] = []
        for warning in warnings:
            if warning not in deduped:
                deduped.append(warning)
        return deduped

    def _next_questions(
        self,
        intent: QueryIntent,
        hits: list[SearchHit],
        warnings: list[str],
        confidence_label: str,
    ) -> list[str]:
        if hits and not warnings and confidence_label in {"moderate", "strong"}:
            return []
        joined_warnings = " ".join(warnings).lower()
        if "test files" in joined_warnings:
            return ["Which runtime source file should RepoBrain prioritize beyond the tests?"]
        if "provider" in joined_warnings:
            return ["Which auth provider symbol or callback handler should RepoBrain narrow on next?"]
        if intent == QueryIntent.CHANGE and confidence_label in {"exploratory", "weak"}:
            return ["Which route, service, or config file is the most likely starting point for this change?"]
        prompts = {
            QueryIntent.LOCATE: "Which module or symbol name should RepoBrain prioritize next?",
            QueryIntent.EXPLAIN: "Should the answer focus on route flow, background jobs, or configuration?",
            QueryIntent.TRACE: "Which starting entrypoint should be traced first: route, job, or service?",
            QueryIntent.IMPACT: "Do you want impact on runtime flow, tests, or configuration surfaces?",
            QueryIntent.CHANGE: "Should RepoBrain rank edit targets for route, service, or config files first?",
        }
        return [prompts[intent]]

    def to_json(self, payload: object) -> str:
        if hasattr(payload, "to_dict"):
            return json.dumps(payload.to_dict(), indent=2)
        return json.dumps(payload, indent=2)

    def _confidence_label(self, confidence: float) -> str:
        if confidence < 0.28:
            return "exploratory"
        if confidence < 0.5:
            return "weak"
        if confidence < 0.72:
            return "moderate"
        return "strong"

    def _best_evidence_overlap(self, query_tokens: set[str], hits: list[SearchHit]) -> float:
        filtered_tokens = {token for token in query_tokens if len(token) >= 3}
        if not filtered_tokens or not hits:
            return 0.0

        best_overlap = 0.0
        for hit in hits[:4]:
            evidence_tokens = set(tokenize(f"{hit.file_path} {hit.symbol_name or ''} {hit.content}"))
            overlap = len(filtered_tokens & evidence_tokens) / max(len(filtered_tokens), 1)
            best_overlap = max(best_overlap, overlap)
        return round(best_overlap, 3)

    def _confidence_summary(
        self,
        intent: QueryIntent,
        confidence_label: str,
        hits: list[SearchHit],
        dependency_edges: list[dict[str, str | None]],
        warnings: list[str],
        *,
        query_tokens: set[str],
    ) -> str:
        if not hits:
            return "No grounded evidence was found for this query."

        file_count = len({hit.file_path for hit in hits[:4]})
        role_count = len({hit.role for hit in hits[:4]})
        overlap = self._best_evidence_overlap(query_tokens, hits[:4])
        multi_source = any("multi_source" in hit.reasons for hit in hits[:4])
        lead = {
            "strong": "Strong grounding",
            "moderate": "Moderate grounding",
            "weak": "Weak grounding",
            "exploratory": "Exploratory grounding",
        }[confidence_label]

        parts = [f"{lead} across {file_count} file(s)"]
        if multi_source:
            parts.append("with lexical and semantic agreement")
        else:
            parts.append("with limited retrieval-source agreement")
        if dependency_edges:
            parts.append(f"and {min(len(dependency_edges), 3)} structural edge hint(s)")
        if intent == QueryIntent.TRACE:
            parts.append(f"covering {role_count} role type(s)")
        if overlap < 0.2:
            parts.append("but weak token overlap to the query")
        if warnings and confidence_label in {"weak", "exploratory"}:
            parts.append("so inspect the lead files before planning edits")
        return " ".join(parts) + "."

    def _change_context_snippet(self, hit: SearchHit) -> dict[str, object]:
        preview = " ".join(hit.content.split())
        if len(preview) > 180:
            preview = preview[:177] + "..."
        return {
            "file_path": hit.file_path,
            "start_line": hit.start_line,
            "end_line": hit.end_line,
            "symbol_name": hit.symbol_name,
            "score": round(hit.score, 3),
            "reasons": hit.reasons[:4],
            "preview": preview,
        }

    def _change_context_evidence_summary(self, result: QueryResult) -> str:
        lead_files = [item.file_path for item in result.top_files[:3]]
        if not lead_files:
            return "No grounded edit surfaces were identified."

        lead_text = ", ".join(lead_files[:3])
        if result.confidence_label in {"exploratory", "weak"}:
            return (
                f"Lead change surfaces are {lead_text}, but the evidence is {result.confidence_label}. "
                "Verify the entrypoint and config wiring before patching."
            )
        return f"Primary change surfaces are {lead_text}. Start there before touching adjacent files."

    def _contradiction_warnings(self, query_tokens: set[str], hits: list[SearchHit]) -> list[str]:
        if not hits:
            return []

        contradiction_groups = [
            {"name": "provider", "tokens": {"github", "google", "gitlab", "microsoft", "saml", "oidc"}},
            {"name": "surface", "tokens": {"callback", "webhook", "cron", "queue", "retry", "login"}},
        ]
        evidence_texts = [f"{hit.file_path} {hit.symbol_name or ''} {hit.content}".lower() for hit in hits[:4]]
        warnings: list[str] = []

        for group in contradiction_groups:
            group_tokens = group["tokens"]
            query_focus = sorted(query_tokens & group_tokens)
            if not query_focus:
                continue

            evidence_counts = {
                token: sum(1 for text in evidence_texts if token in text)
                for token in group_tokens
            }
            focus_hits = sum(evidence_counts[token] for token in query_focus)
            conflicting = sorted(
                token
                for token, count in evidence_counts.items()
                if token not in query_focus and count >= 2
            )
            if focus_hits == 0 and conflicting:
                warnings.append(
                    f"Evidence is skewed toward {'/'.join(conflicting)} while the query asks about {'/'.join(query_focus)}. Verify the requested {group['name']} manually."
                )
            elif focus_hits > 0 and conflicting:
                warnings.append(
                    f"Evidence mixes {'/'.join(query_focus)} with {'/'.join(conflicting)}. Verify the requested {group['name']} before editing."
                )

        return warnings
