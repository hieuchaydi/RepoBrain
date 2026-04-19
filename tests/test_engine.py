from __future__ import annotations

import json
from pathlib import Path

from repobrain.config import RepoBrainConfig
from repobrain.engine.core import RepoBrainEngine
from repobrain.engine.providers import ProviderBundle
from repobrain.models import ReviewFocus


def _build_insecure_repo(repo_root: Path) -> Path:
    (repo_root / "app" / "routes").mkdir(parents=True)
    (repo_root / "app" / "services").mkdir(parents=True)
    (repo_root / "app" / "jobs").mkdir(parents=True)
    (repo_root / "tests").mkdir(parents=True)

    (repo_root / ".env").write_text("LINKEDIN_ACCESS_TOKEN=secret\n", encoding="utf-8")
    (repo_root / ".gitignore").write_text("__pycache__/\n.venv/\n", encoding="utf-8")
    (repo_root / "Dockerfile").write_text(
        "FROM python:3.12-slim\nCOPY requirements.txt .\nCOPY .env ./.env\nCOPY app ./app\n",
        encoding="utf-8",
    )
    (repo_root / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    (repo_root / "app" / "routes" / "posts.py").write_text(
        "from fastapi import APIRouter, HTTPException\n\n"
        "router = APIRouter()\n\n"
        "@router.post('/publish')\n"
        "def publish_post():\n"
        "    try:\n"
        "        return {'ok': True}\n"
        "    except Exception as exc:\n"
        "        raise HTTPException(status_code=500, detail=str(exc)) from exc\n",
        encoding="utf-8",
    )
    for name in ("publish.py", "queue.py", "history.py"):
        (repo_root / "app" / "services" / name).write_text(
            f"def {name.removesuffix('.py')}_service():\n    return True\n",
            encoding="utf-8",
        )
    for name in ("worker.py", "retry_job.py"):
        (repo_root / "app" / "jobs" / name).write_text(
            f"def {name.removesuffix('.py')}():\n    return True\n",
            encoding="utf-8",
        )
    (repo_root / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    return repo_root


def test_config_write_and_load(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config = RepoBrainConfig.default(repo_root)
    written = config.write_default()
    loaded = RepoBrainConfig.load(repo_root)
    assert written.exists()
    assert loaded.project.name == "RepoBrain"
    assert loaded.project.state_dir == ".repobrain"
    assert loaded.parsing.prefer_tree_sitter is True
    assert "python" in loaded.parsing.tree_sitter_languages


def test_index_and_query_find_retry_logic(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    stats = engine.index_repository()
    result = engine.query("Where is payment retry logic implemented?")

    assert stats["files"] >= 7
    assert stats["parsers"]
    assert "retry_handler.py" in result.top_files[0].file_path or "payment_retry_job.py" in result.top_files[0].file_path
    assert any("retry_handler.py" in item.file_path for item in result.top_files)
    assert any("payment_retry_job.py" in item.file_path for item in result.top_files)
    assert result.confidence > 0.45
    assert result.confidence_label in {"moderate", "strong"}
    assert result.confidence_summary


def test_trace_and_targets_return_grounded_files(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()

    trace_result = engine.trace("Trace login with Google from route to service")
    target_result = engine.targets("Which files should I edit to add GitHub login?")
    change_context = engine.build_change_context("Which files should I edit to add GitHub login?")

    assert any("auth.py" in item.file_path for item in trace_result.top_files)
    assert any("oauth.ts" in item.file_path for item in target_result.top_files)
    assert trace_result.call_chain
    assert change_context["edit_targets"]
    assert len(change_context["top_files"]) <= 4
    assert len(change_context["edit_targets"]) <= 3
    assert change_context["supporting_snippets"]
    assert change_context["confidence_label"] in {"moderate", "strong"}
    assert change_context["confidence_summary"]
    assert change_context["evidence_summary"]
    assert "supporting_reasons" in change_context["edit_targets"][0]
    assert change_context["plan_steps"]


def test_runtime_queries_penalize_test_files_unless_tests_are_requested(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src" / "routes").mkdir(parents=True)
    (repo_root / "src" / "services").mkdir(parents=True)
    (repo_root / "tests").mkdir()
    (repo_root / "src" / "routes" / "login.py").write_text(
        "from src.services.auth_service import login_with_google\n\n"
        "def login_route():\n"
        "    return login_with_google()\n",
        encoding="utf-8",
    )
    (repo_root / "src" / "services" / "auth_service.py").write_text(
        "def login_with_google():\n"
        "    return {'provider': 'google'}\n",
        encoding="utf-8",
    )
    (repo_root / "tests" / "test_login.py").write_text(
        "def test_acceptance_phrase():\n"
        "    assert 'Trace login with Google from route to service'\n",
        encoding="utf-8",
    )

    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)
    engine.index_repository()

    runtime_result = engine.trace("Trace login with Google from route to service")
    test_result = engine.query("Which test covers login with Google?")

    assert runtime_result.top_files[0].role in {"route", "service"}
    assert any("test_surface_penalty" in hit.reasons for hit in runtime_result.snippets if hit.role == "test")
    assert test_result.top_files[0].role == "test"


def test_runtime_queries_warn_when_only_test_evidence_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tests").mkdir(parents=True)
    (repo_root / "tests" / "test_login.py").write_text(
        "def test_acceptance_phrase():\n"
        "    assert 'Trace login with Google from route to service'\n",
        encoding="utf-8",
    )

    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)
    engine.index_repository()
    result = engine.trace("Trace login with Google from route to service")

    assert result.top_files[0].role == "test"
    assert any("only appears in test files" in warning for warning in result.warnings)
    assert result.confidence < 0.75


def test_doctor_includes_provider_status_and_security(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()
    doctor = engine.doctor()

    assert doctor["provider_status"]["embedding"]["ready"] is True
    assert doctor["provider_status"]["reranker"]["ready"] is True
    assert doctor["security"]["local_storage_only"] is True
    assert doctor["security"]["mcp_transport"] == "stdio-json"
    assert doctor["capabilities"]["language_parsers"]["python"]["heuristic_fallback"] is True
    assert "reranker_model" in doctor["providers"]


def test_provider_smoke_reports_embedding_and_reranker_health(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)

    class FakeEmbedder:
        name = "fake-embedder"
        model = "fake-embedding-model"

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeReranker:
        name = "fake-reranker"
        model = "fake-rerank-model"
        models = ["fake-rerank-model", "backup-rerank-model"]
        last_failover_error = None

        def score(self, query: str, candidate_text: str) -> float:
            return 0.77

    engine.providers = ProviderBundle(embedder=FakeEmbedder(), reranker=FakeReranker())
    smoke = engine.provider_smoke()

    assert smoke["embedding_smoke"]["status"] == "pass"
    assert smoke["embedding_smoke"]["dimensions"] == 3
    assert smoke["reranker_smoke"]["status"] == "pass"
    assert smoke["reranker_smoke"]["score"] == 0.77
    assert smoke["reranker_smoke"]["pool"] == ["fake-rerank-model", "backup-rerank-model"]


def test_ignore_files_from_repobrainignore(tmp_path: Path) -> None:
    repo_root = tmp_path / "ignored_repo"
    repo_root.mkdir()
    (repo_root / ".repobrainignore").write_text("ignored.py\n", encoding="utf-8")
    (repo_root / "ignored.py").write_text("def hidden():\n    return True\n", encoding="utf-8")
    (repo_root / "visible.py").write_text("def shown():\n    return True\n", encoding="utf-8")

    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)
    stats = engine.index_repository()
    result = engine.query("Where is shown implemented?")

    assert stats["files"] == 1
    assert all("ignored.py" not in item.file_path for item in result.top_files)


def test_empty_metadata_db_is_not_treated_as_indexed(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)
    engine.store.initialize(reset=True)

    assert engine.store.indexed() is False
    assert engine.doctor()["indexed"] is False


def test_benchmark_returns_metrics(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()
    report = engine.benchmark()

    payload = report.to_dict()
    assert payload["cases_run"] == 3
    assert payload["recall_at_3"] >= 0.333
    assert payload["edit_target_hit_rate"] >= 0.333


def test_low_evidence_query_returns_warning(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()
    result = engine.query("Where is kerberos saml tenant federation broker pipeline implemented?")

    assert result.warnings
    assert result.confidence < 0.7
    assert result.confidence_label in {"exploratory", "weak"}
    assert any("confidence band" in warning.lower() for warning in result.warnings)


def test_confidence_calibration_bands(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()
    grounded = engine.query("Where is payment retry logic implemented?")
    weak = engine.query("Where is kerberos saml tenant federation broker pipeline implemented?")
    rank = {"exploratory": 0, "weak": 1, "moderate": 2, "strong": 3}

    assert 0.45 <= grounded.confidence <= 0.97
    assert 0.05 <= weak.confidence <= 0.7
    assert weak.confidence < grounded.confidence
    assert rank[weak.confidence_label] < rank[grounded.confidence_label]


def test_trace_query_can_surface_contradiction_or_surface_warning(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()
    result = engine.trace("Trace login with Google from route to service")

    assert result.warnings
    assert any("surface" in warning.lower() or "exploratory" in warning.lower() or "provider" in warning.lower() for warning in result.warnings)


def test_review_surfaces_high_signal_repo_risks(tmp_path: Path) -> None:
    repo_root = _build_insecure_repo(tmp_path / "review_repo")
    engine = RepoBrainEngine(repo_root)
    engine.init_workspace(force=True)

    report = engine.review()
    security_report = engine.review(focus=ReviewFocus.SECURITY)

    assert report.readiness == "not_ready"
    assert report.score < 7.0
    titles = {finding.title for finding in report.findings}
    assert "Secrets may be baked into the Docker image" in titles
    assert "Mutating endpoints have no obvious auth guard nearby" in titles
    assert any("str(exc)" in finding.summary or "internal" in finding.summary for finding in report.findings)
    assert all(finding.category == "security" for finding in security_report.findings)


def test_review_baseline_and_ship_gate_surface_drift(mixed_repo: Path) -> None:
    engine = RepoBrainEngine(mixed_repo)
    engine.init_workspace(force=True)
    engine.index_repository()

    baseline_report = engine.review(compare_baseline=False)
    saved = engine.save_review_baseline(baseline_report)
    ship = engine.ship()

    assert saved["baseline_path"].endswith("baseline.json")
    assert ship.review is not None
    assert ship.review.delta is not None
    assert ship.review.delta.baseline_label == "baseline"
    assert ship.summary
    assert ship.checks
    assert ship.history["points"]
    assert ship.history["saved_snapshots"] >= 1
    assert any(check.name == "benchmark" for check in ship.checks)
    assert ship.status in {"blocked", "caution", "ready"}
