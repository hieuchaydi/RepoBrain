from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from repobrain.config import RepoBrainConfig
from repobrain.engine.scanner import FileCandidate, RepositoryScanner
from repobrain.models import ParsedDocument, ReviewFinding, ReviewFocus, ReviewReport, ReviewSeverity


ROOT_TEXT_FILES = (
    ".dockerignore",
    ".env",
    ".env.example",
    ".gitignore",
    ".pre-commit-config.yaml",
    "Dockerfile",
    "README.md",
    "docker-compose.yml",
    "compose.yml",
    "compose.yaml",
    "package.json",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements.txt",
    "setup.cfg",
    "tox.ini",
    "ruff.toml",
    ".ruff.toml",
)

DOCKER_ENV_COPY_RE = re.compile(r"(?im)^\s*(?:copy|add)\s+\.env(?:\s|$)")
DOCKER_BROAD_COPY_RE = re.compile(r"(?im)^\s*copy\s+\.\s+")
MUTATING_ROUTE_RE = re.compile(
    r"(?im)(?:@\w+\.(?:post|put|patch|delete)\s*\(|\b\w+\.(?:post|put|patch|delete)\s*\()"
)
AUTH_GUARD_RE = re.compile(
    r"(?i)(HTTPBearer|OAuth2|APIKey|get_current_user|require_auth|require_user|authMiddleware|authenticate|verifyToken|jwt|passport|Depends\([^)]*(?:auth|user|token|bearer|oauth|key))"
)
RAW_EXCEPTION_RE = re.compile(
    r"(?i)(detail\s*=\s*str\(exc\)|['\"](?:error|detail|message)['\"]\s*:\s*str\(exc\)|return\s+\{[^}]*str\(exc\))"
)
CI_SIGNAL_RE = re.compile(r"(?i)(pytest|ruff|black|mypy|npm test|pnpm test|yarn test|uv run pytest)")
PYTHON_LINT_SIGNAL_RE = re.compile(r"(?i)(\[tool\.ruff\]|\[tool\.black\]|flake8|isort|mypy)")
JS_LINT_SIGNAL_RE = re.compile(r'(?i)("eslint"|eslintConfig|"prettier"|"biome")')

SEVERITY_ORDER = {
    ReviewSeverity.CRITICAL: 0,
    ReviewSeverity.HIGH: 1,
    ReviewSeverity.MEDIUM: 2,
    ReviewSeverity.LOW: 3,
}
SEVERITY_PENALTY = {
    ReviewSeverity.CRITICAL: 2.6,
    ReviewSeverity.HIGH: 1.7,
    ReviewSeverity.MEDIUM: 0.9,
    ReviewSeverity.LOW: 0.4,
}
FOCUS_CATEGORIES = {
    ReviewFocus.FULL: {"security", "production", "quality", "testing", "tooling"},
    ReviewFocus.SECURITY: {"security"},
    ReviewFocus.PRODUCTION: {"security", "production"},
    ReviewFocus.QUALITY: {"quality", "testing", "tooling"},
}


@dataclass(slots=True)
class RepoSnapshot:
    repo_root: Path
    code_files: list[FileCandidate]
    code_text: dict[str, str]
    root_text: dict[str, str]
    workflow_text: dict[str, str]

    @property
    def route_files(self) -> list[FileCandidate]:
        return [candidate for candidate in self.code_files if candidate.role == "route"]

    @property
    def test_files(self) -> list[FileCandidate]:
        return [candidate for candidate in self.code_files if candidate.role == "test"]

    @property
    def non_test_files(self) -> list[FileCandidate]:
        return [candidate for candidate in self.code_files if candidate.role != "test"]


class ProjectReviewer:
    def __init__(self, config: RepoBrainConfig, scanner: RepositoryScanner | None = None) -> None:
        self.config = config
        self.scanner = scanner or RepositoryScanner(config)

    def review(self, focus: ReviewFocus = ReviewFocus.FULL, max_findings: int = 6) -> ReviewReport:
        return self._review_snapshot(self._snapshot(), focus=focus, max_findings=max_findings)

    def review_from_documents(
        self,
        documents: list[ParsedDocument],
        focus: ReviewFocus = ReviewFocus.FULL,
        max_findings: int = 6,
    ) -> ReviewReport:
        return self._review_snapshot(self._snapshot_from_documents(documents), focus=focus, max_findings=max_findings)

    def _review_snapshot(self, snapshot: RepoSnapshot, *, focus: ReviewFocus, max_findings: int) -> ReviewReport:
        findings = self._collect_findings(snapshot)
        allowed_categories = FOCUS_CATEGORIES[focus]
        filtered = [finding for finding in findings if finding.category in allowed_categories]
        filtered.sort(key=self._sort_key)
        selected = filtered[:max_findings]
        score = self._score(selected)
        readiness = self._readiness(selected, score)
        summary = self._summary(selected, readiness)
        next_steps = self._next_steps(selected)
        category_counts = self._category_counts(selected)
        severity_counts = self._severity_counts(selected)
        return ReviewReport(
            repo_root=str(snapshot.repo_root),
            focus=focus,
            readiness=readiness,
            score=score,
            summary=summary,
            findings=selected,
            next_steps=next_steps,
            stats=self._stats(snapshot),
            category_counts=category_counts,
            severity_counts=severity_counts,
        )

    def _snapshot(self) -> RepoSnapshot:
        code_files = self.scanner.scan()
        code_text = {
            candidate.rel_path: candidate.path.read_text(encoding="utf-8", errors="ignore")
            for candidate in code_files
        }
        return RepoSnapshot(
            repo_root=self.config.resolved_repo_root,
            code_files=code_files,
            code_text=code_text,
            root_text=self._root_text_snapshot(),
            workflow_text=self._workflow_text_snapshot(),
        )

    def _snapshot_from_documents(self, documents: list[ParsedDocument]) -> RepoSnapshot:
        code_files = [
            FileCandidate(
                path=self.config.resolved_repo_root / document.file_path,
                rel_path=document.file_path,
                language=document.language,
                role=document.role,
            )
            for document in documents
        ]
        return RepoSnapshot(
            repo_root=self.config.resolved_repo_root,
            code_files=code_files,
            code_text={document.file_path: document.content for document in documents},
            root_text=self._root_text_snapshot(),
            workflow_text=self._workflow_text_snapshot(),
        )

    def _root_text_snapshot(self) -> dict[str, str]:
        root_text: dict[str, str] = {}
        for name in ROOT_TEXT_FILES:
            path = self.config.resolved_repo_root / name
            if path.exists() and path.is_file():
                root_text[name] = path.read_text(encoding="utf-8", errors="ignore")
        return root_text

    def _workflow_text_snapshot(self) -> dict[str, str]:
        workflow_text: dict[str, str] = {}
        workflow_dir = self.config.resolved_repo_root / ".github" / "workflows"
        if workflow_dir.exists():
            for path in sorted(workflow_dir.glob("*.y*ml")):
                workflow_text[path.relative_to(self.config.resolved_repo_root).as_posix()] = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
        return workflow_text

    def _collect_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        findings.extend(self._docker_secret_findings(snapshot))
        findings.extend(self._env_hygiene_findings(snapshot))
        findings.extend(self._mutating_route_findings(snapshot))
        findings.extend(self._raw_exception_findings(snapshot))
        findings.extend(self._tooling_findings(snapshot))
        findings.extend(self._test_coverage_findings(snapshot))
        findings.extend(self._ci_findings(snapshot))
        return findings

    def _docker_secret_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        dockerfile = snapshot.root_text.get("Dockerfile", "")
        if not dockerfile:
            return findings

        if DOCKER_ENV_COPY_RE.search(dockerfile):
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.CRITICAL,
                    category="security",
                    title="Secrets may be baked into the Docker image",
                    summary="The Dockerfile copies `.env` directly into the image, so secrets can leak through built artifacts, image layers, or registry pushes.",
                    file_paths=["Dockerfile", ".env"],
                    recommendation="Remove `.env` from the image build, pass secrets at runtime, and keep `.env` local-only.",
                )
            )
            return findings

        dockerignore = snapshot.root_text.get(".dockerignore", "")
        if ".env" in snapshot.root_text and DOCKER_BROAD_COPY_RE.search(dockerfile) and not self._ignores_env(dockerignore):
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.HIGH,
                    category="security",
                    title="Broad Docker copy can pull `.env` into build context",
                    summary="The Dockerfile copies the repository broadly, but `.dockerignore` does not clearly exclude `.env`, which makes accidental secret inclusion likely.",
                    file_paths=["Dockerfile", ".dockerignore", ".env"],
                    recommendation="Exclude `.env` from `.dockerignore` and keep runtime secrets outside the build context.",
                )
            )
        return findings

    def _env_hygiene_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        if ".env" not in snapshot.root_text:
            return findings
        gitignore = snapshot.root_text.get(".gitignore", "")
        if not self._ignores_env(gitignore):
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.HIGH,
                    category="security",
                    title="`.env` is present without a matching `.gitignore` rule",
                    summary="RepoBrain found a real `.env` file in the project root, but `.gitignore` does not clearly exclude it. That raises the chance of leaking tokens or database credentials into source control.",
                    file_paths=[".env", ".gitignore"],
                    recommendation="Add `.env` to `.gitignore`, rotate any secrets that may already have been shared, and keep `.env.example` as the committed template.",
                )
            )
        return findings

    def _mutating_route_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        unguarded_routes: list[str] = []
        for candidate in snapshot.route_files:
            content = snapshot.code_text.get(candidate.rel_path, "")
            if not MUTATING_ROUTE_RE.search(content):
                continue
            if AUTH_GUARD_RE.search(content):
                continue
            unguarded_routes.append(candidate.rel_path)

        if not unguarded_routes:
            return []

        sample_paths = sorted(unguarded_routes)[:4]
        return [
            ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category="security",
                title="Mutating endpoints have no obvious auth guard nearby",
                summary="RepoBrain found POST/PUT/PATCH/DELETE handlers without visible authentication or authorization markers in the same route module. That is risky for internet-facing services and admin workflows.",
                file_paths=sample_paths,
                recommendation="Protect write endpoints with explicit auth middleware/dependencies and add tests that prove unauthorized requests are blocked.",
            )
        ]

    def _raw_exception_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        leaking_files = [
            path
            for path, content in snapshot.code_text.items()
            if RAW_EXCEPTION_RE.search(content)
        ]
        if not leaking_files:
            return []
        return [
            ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="production",
                title="Raw exception text may leak internals to clients",
                summary="Some code paths appear to send `str(exc)` back to callers. That can expose vendor responses, stack-context clues, or internal configuration details in production.",
                file_paths=sorted(leaking_files)[:4],
                recommendation="Map internal exceptions to stable user-facing messages, log the full exception server-side, and keep API error payloads intentionally minimal.",
            )
        ]

    def _tooling_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        python_present = any(candidate.language == "python" for candidate in snapshot.non_test_files)
        javascript_present = any(candidate.language in {"javascript", "typescript"} for candidate in snapshot.non_test_files)

        config_blobs = list(snapshot.root_text.items()) + list(snapshot.workflow_text.items())
        has_python_lint = any(PYTHON_LINT_SIGNAL_RE.search(content) for _, content in config_blobs)
        has_js_lint = any(JS_LINT_SIGNAL_RE.search(content) for _, content in config_blobs)
        has_pre_commit = ".pre-commit-config.yaml" in snapshot.root_text

        missing_python = python_present and not has_python_lint
        missing_js = javascript_present and not has_js_lint
        if not missing_python and not missing_js and has_pre_commit:
            return []

        focus_files = [name for name in ("pyproject.toml", "package.json", ".pre-commit-config.yaml", "setup.cfg") if name in snapshot.root_text]
        if not focus_files:
            focus_files = ["repo root"]
        return [
            ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="tooling",
                title="Formatting and lint guardrails are missing or incomplete",
                summary="The repo does not show a clear formatter/linter setup such as Ruff, Black, ESLint, Prettier, or pre-commit hooks. That makes consistency drift more likely as the project grows.",
                file_paths=focus_files,
                recommendation="Add a shared formatter/linter config plus a pre-commit hook so teams and agents apply the same standards before code lands.",
            )
        ]

    def _test_coverage_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        code_count = len(snapshot.non_test_files)
        test_count = len(snapshot.test_files)
        if code_count <= 5 or test_count >= 2:
            return []
        return [
            ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="testing",
                title="Test surface looks thin compared with the code footprint",
                summary=f"RepoBrain found {code_count} non-test source files but only {test_count} test file(s). That usually leaves production behavior, regressions, and edge cases under-protected.",
                file_paths=sorted(candidate.rel_path for candidate in snapshot.test_files)[:3] or ["tests/"],
                recommendation="Add focused tests for write endpoints, risky services, and the main happy-path plus failure-path flows before calling the repo production-ready.",
            )
        ]

    def _ci_findings(self, snapshot: RepoSnapshot) -> list[ReviewFinding]:
        if snapshot.workflow_text:
            has_quality_ci = any(CI_SIGNAL_RE.search(content) for content in snapshot.workflow_text.values())
            if has_quality_ci:
                return []
        return [
            ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="production",
                title="No obvious CI guardrail was found",
                summary="RepoBrain did not find a workflow that clearly runs tests or code-quality checks. That weakens production confidence because breakages can slip in without an automated gate.",
                file_paths=sorted(snapshot.workflow_text)[:2] or [".github/workflows/"],
                recommendation="Add a lightweight CI workflow that runs lint, tests, and at least one install/build check on pull requests.",
            )
        ]

    def _stats(self, snapshot: RepoSnapshot) -> dict[str, object]:
        languages = Counter(candidate.language for candidate in snapshot.non_test_files)
        return {
            "code_files": len(snapshot.non_test_files),
            "route_files": len(snapshot.route_files),
            "test_files": len(snapshot.test_files),
            "languages": dict(sorted(languages.items())),
        }

    def _score(self, findings: list[ReviewFinding]) -> float:
        penalty = sum(SEVERITY_PENALTY[finding.severity] for finding in findings[:6])
        return round(max(2.0, 10.0 - penalty), 1)

    def _readiness(self, findings: list[ReviewFinding], score: float) -> str:
        severities = {finding.severity for finding in findings}
        if ReviewSeverity.CRITICAL in severities or score < 6.0:
            return "not_ready"
        if ReviewSeverity.HIGH in severities or score < 7.5:
            return "needs_hardening"
        return "promising"

    def _summary(self, findings: list[ReviewFinding], readiness: str) -> str:
        if not findings:
            return "RepoBrain did not find any high-signal issues from the local scan. Manual review is still recommended for domain-specific logic and access control."

        categories = Counter(finding.category for finding in findings)
        dominant = ", ".join(category for category, _ in categories.most_common(2))
        top = findings[0]
        if readiness == "not_ready":
            return f"Highest-risk gaps are in {dominant}. Start with '{top.title.lower()}' before treating this repo as production-ready."
        if readiness == "needs_hardening":
            return f"The repo has a workable base, but {dominant} still need tightening. The most urgent fix is '{top.title.lower()}'."
        return f"The repo looks directionally healthy, but {dominant} still need cleanup before a confident production rollout."

    def _next_steps(self, findings: list[ReviewFinding]) -> list[str]:
        steps: list[str] = []
        for finding in findings:
            action = finding.recommendation.strip()
            if action and action not in steps:
                steps.append(action)
            if len(steps) >= 3:
                break
        return steps

    def _sort_key(self, finding: ReviewFinding) -> tuple[int, str, str]:
        return (SEVERITY_ORDER[finding.severity], finding.category, finding.title)

    def _category_counts(self, findings: list[ReviewFinding]) -> dict[str, int]:
        counts = Counter(finding.category for finding in findings)
        return dict(sorted(counts.items()))

    def _severity_counts(self, findings: list[ReviewFinding]) -> dict[str, int]:
        counts = Counter(finding.severity.value for finding in findings)
        ordered = sorted(counts.items(), key=lambda item: SEVERITY_ORDER[ReviewSeverity(item[0])])
        return dict(ordered)

    def _ignores_env(self, gitignore_text: str) -> bool:
        for raw_line in gitignore_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line in {".env", "*.env", ".env.*", "**/.env"}:
                return True
        return False
