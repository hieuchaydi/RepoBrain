from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class QueryIntent(StrEnum):
    LOCATE = "locate"
    EXPLAIN = "explain"
    TRACE = "trace"
    IMPACT = "impact"
    CHANGE = "change"


class ReviewSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewFocus(StrEnum):
    FULL = "full"
    SECURITY = "security"
    PRODUCTION = "production"
    QUALITY = "quality"


@dataclass(slots=True)
class ReviewDelta:
    baseline_label: str
    baseline_saved_at: str
    status: str
    baseline_score: float
    current_score: float
    score_delta: float
    baseline_readiness: str
    current_readiness: str
    new_findings: list[str] = field(default_factory=list)
    resolved_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_label": self.baseline_label,
            "baseline_saved_at": self.baseline_saved_at,
            "status": self.status,
            "baseline_score": round(self.baseline_score, 1),
            "current_score": round(self.current_score, 1),
            "score_delta": round(self.score_delta, 1),
            "baseline_readiness": self.baseline_readiness,
            "current_readiness": self.current_readiness,
            "new_findings": self.new_findings,
            "resolved_findings": self.resolved_findings,
        }


@dataclass(slots=True)
class ReadinessCheck:
    name: str
    status: str
    summary: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "detail": self.detail,
        }


@dataclass(slots=True)
class Symbol:
    name: str
    kind: str
    start_line: int
    end_line: int
    signature: str
    doc_hint: str = ""


@dataclass(slots=True)
class Chunk:
    file_path: str
    language: str
    role: str
    start_line: int
    end_line: int
    content: str
    search_text: str
    symbol_name: str | None = None
    symbol_kind: str | None = None
    neighborhood: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    chunk_id: int | None = None


@dataclass(slots=True)
class Edge:
    source_file: str
    source_symbol: str
    target: str
    edge_type: str
    target_file: str | None = None


@dataclass(slots=True)
class ParsedDocument:
    file_path: str
    language: str
    role: str
    content: str
    symbols: list[Symbol]
    imports: list[str]
    edges: list[Edge]
    chunks: list[Chunk]
    hints: list[str]
    parser_name: str = "heuristic"
    parser_detail: str = ""


@dataclass(slots=True)
class SearchHit:
    chunk_id: int
    file_path: str
    language: str
    role: str
    symbol_name: str | None
    start_line: int
    end_line: int
    content: str
    score: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FileEvidence:
    file_path: str
    language: str
    role: str
    score: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EditTarget:
    file_path: str
    score: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QueryPlan:
    intent: QueryIntent
    steps: list[str]
    rewritten_queries: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "steps": self.steps,
            "rewritten_queries": self.rewritten_queries,
        }


@dataclass(slots=True)
class QueryResult:
    query: str
    intent: QueryIntent
    top_files: list[FileEvidence]
    snippets: list[SearchHit]
    call_chain: list[str]
    dependency_edges: list[dict[str, Any]]
    edit_targets: list[EditTarget]
    confidence: float
    warnings: list[str]
    next_questions: list[str]
    plan: QueryPlan
    confidence_label: str = ""
    confidence_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent.value,
            "top_files": [item.to_dict() for item in self.top_files],
            "snippets": [item.to_dict() for item in self.snippets],
            "call_chain": self.call_chain,
            "dependency_edges": self.dependency_edges,
            "edit_targets": [item.to_dict() for item in self.edit_targets],
            "confidence": round(self.confidence, 3),
            "confidence_label": self.confidence_label,
            "confidence_summary": self.confidence_summary,
            "warnings": self.warnings,
            "next_questions": self.next_questions,
            "plan": self.plan.to_dict(),
        }


@dataclass(slots=True)
class ReviewFinding:
    severity: ReviewSeverity
    category: str
    title: str
    summary: str
    file_paths: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "file_paths": self.file_paths,
            "recommendation": self.recommendation,
        }


@dataclass(slots=True)
class ReviewReport:
    repo_root: str
    focus: ReviewFocus
    readiness: str
    score: float
    summary: str
    findings: list[ReviewFinding] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    category_counts: dict[str, int] = field(default_factory=dict)
    severity_counts: dict[str, int] = field(default_factory=dict)
    delta: ReviewDelta | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "focus": self.focus.value,
            "readiness": self.readiness,
            "score": round(self.score, 1),
            "summary": self.summary,
            "findings": [item.to_dict() for item in self.findings],
            "next_steps": self.next_steps,
            "stats": self.stats,
            "category_counts": self.category_counts,
            "severity_counts": self.severity_counts,
            "delta": self.delta.to_dict() if self.delta else None,
        }


@dataclass(slots=True)
class ShipReport:
    repo_root: str
    status: str
    score: float
    summary: str
    checks: list[ReadinessCheck] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    doctor: dict[str, Any] = field(default_factory=dict)
    review: ReviewReport | None = None
    benchmark: dict[str, Any] | None = None
    history: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "status": self.status,
            "score": round(self.score, 1),
            "summary": self.summary,
            "checks": [item.to_dict() for item in self.checks],
            "blockers": self.blockers,
            "highlights": self.highlights,
            "next_steps": self.next_steps,
            "doctor": self.doctor,
            "review": self.review.to_dict() if self.review else None,
            "benchmark": self.benchmark,
            "history": self.history,
        }
