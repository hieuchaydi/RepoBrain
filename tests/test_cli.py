from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from repobrain.cli import main
from repobrain.config import RepoBrainConfig
from repobrain.engine.core import RepoBrainEngine
from repobrain.models import FileEvidence, QueryIntent, QueryPlan, QueryResult
from repobrain.ux import cli_wordmark, payload_to_text, quickstart_text


def test_cli_init_index_query_and_doctor(mixed_repo: Path, capsys) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    init_payload = json.loads(capsys.readouterr().out)
    assert init_payload["state_dir"].endswith(".repobrain")

    assert main(["index", "--repo", str(mixed_repo)]) == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["files"] >= 7
    assert index_payload["parsers"]

    assert main(["query", "Where is payment retry logic implemented?", "--repo", str(mixed_repo)]) == 0
    query_payload = json.loads(capsys.readouterr().out)
    assert query_payload["top_files"]
    assert query_payload["file_context"]["files"]

    assert main(["doctor", "--repo", str(mixed_repo)]) == 0
    doctor_payload = json.loads(capsys.readouterr().out)
    assert doctor_payload["indexed"] is True
    assert doctor_payload["provider_status"]["embedding"]["ready"] is True
    assert "reranker_model" in doctor_payload["providers"]
    assert "language_parsers" in doctor_payload["capabilities"]

    assert main(["provider-smoke", "--repo", str(mixed_repo)]) == 0
    smoke_payload = json.loads(capsys.readouterr().out)
    assert smoke_payload["embedding_smoke"]["status"] == "pass"
    assert smoke_payload["reranker_smoke"]["status"] == "pass"


def test_cli_remembers_active_repo_after_init(mixed_repo: Path, capsys) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force", "--format", "text"]) == 0
    init_output = capsys.readouterr().out
    assert "Active repo:" in init_output
    assert str(mixed_repo) in init_output

    assert main(["index", "--format", "text"]) == 0
    index_output = capsys.readouterr().out
    assert "RepoBrain Index Complete" in index_output

    assert main(["query", "Where is payment retry logic implemented?", "--format", "text"]) == 0
    query_output = capsys.readouterr().out
    assert "RepoBrain Result" in query_output
    assert "Top files:" in query_output
    assert "RepoBrain Auto-Attached Files" in query_output


def test_cli_key_gemini_writes_env_and_provider_config(mixed_repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert (
        main(
            [
                "key",
                "gemini",
                "--repo",
                str(mixed_repo),
                "--api-key",
                "cli-gemini-key",
                "--model-pool",
                "gemini-2.5-flash,gemini-3-flash-preview",
                "--format",
                "text",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    config = RepoBrainConfig.load(mixed_repo)

    assert "RepoBrain Gemini Config" in output
    assert "API key: saved" in output
    assert "cli-gemini-key" not in output
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GEMINI_API_KEY=cli-gemini-key"
    assert config.providers.embedding == "gemini"
    assert config.providers.reranker == "gemini"
    assert config.providers.options["gemini_models"] == ["gemini-2.5-flash", "gemini-3-flash-preview"]


def test_cli_key_groq_writes_env_and_provider_config(mixed_repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert (
        main(
            [
                "key",
                "groq",
                "--repo",
                str(mixed_repo),
                "--api-key",
                "cli-groq-key",
                "--model-pool",
                "llama-3.3-70b-versatile,openai/gpt-oss-20b",
                "--format",
                "text",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    config = RepoBrainConfig.load(mixed_repo)

    assert "RepoBrain Groq Config" in output
    assert "API key: saved" in output
    assert "cli-groq-key" not in output
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GROQ_API_KEY=cli-groq-key"
    assert config.providers.embedding == "local"
    assert config.providers.reranker == "groq"
    assert config.providers.options["groq_models"] == ["llama-3.3-70b-versatile", "openai/gpt-oss-20b"]


def test_cli_chat_can_exit(mixed_repo: Path, capsys, monkeypatch) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    capsys.readouterr()
    assert main(["index", "--repo", str(mixed_repo)]) == 0
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _: "/exit")
    assert main(["chat", "--repo", str(mixed_repo)]) == 0
    chat_output = capsys.readouterr().out
    assert cli_wordmark() in chat_output
    assert "RepoBrain chat is local-only" in chat_output


def test_cli_chat_key_command_prompts_for_gemini_key(mixed_repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    inputs = iter(["/key gemini", "/exit"])

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("repobrain.cli.getpass.getpass", lambda _: "chat-gemini-key")

    assert main(["chat", "--repo", str(mixed_repo)]) == 0
    output = capsys.readouterr().out
    config = RepoBrainConfig.load(mixed_repo)

    assert "RepoBrain Gemini Config" in output
    assert "API key: saved" in output
    assert "chat-gemini-key" not in output
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GEMINI_API_KEY=chat-gemini-key"
    assert config.providers.embedding == "gemini"
    assert config.providers.reranker == "gemini"


def test_cli_chat_key_command_prompts_for_groq_key(mixed_repo: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    inputs = iter(["/key groq", "/exit"])

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("repobrain.cli.getpass.getpass", lambda _: "chat-groq-key")

    assert main(["chat", "--repo", str(mixed_repo)]) == 0
    output = capsys.readouterr().out
    config = RepoBrainConfig.load(mixed_repo)

    assert "RepoBrain Groq Config" in output
    assert "API key: saved" in output
    assert "chat-groq-key" not in output
    assert (mixed_repo / ".env").read_text(encoding="utf-8").splitlines()[0] == "GROQ_API_KEY=chat-groq-key"
    assert config.providers.embedding == "local"
    assert config.providers.reranker == "groq"


def test_cli_text_output_and_quickstart(mixed_repo: Path, capsys) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    capsys.readouterr()
    assert main(["doctor", "--repo", str(mixed_repo), "--format", "text"]) == 0
    doctor_output = capsys.readouterr().out
    assert "RepoBrain Doctor" in doctor_output
    assert "Provider models:" in doctor_output

    assert main(["provider-smoke", "--repo", str(mixed_repo), "--format", "text"]) == 0
    smoke_output = capsys.readouterr().out
    assert "RepoBrain Provider Smoke" in smoke_output
    assert "Embedding smoke:" in smoke_output

    assert main(["index", "--repo", str(mixed_repo), "--format", "text"]) == 0
    index_output = capsys.readouterr().out
    assert "RepoBrain Index Complete" in index_output
    assert "Parsers:" in index_output

    assert main(["query", "Where is payment retry logic implemented?", "--repo", str(mixed_repo), "--format", "text"]) == 0
    query_output = capsys.readouterr().out
    assert "RepoBrain Result" in query_output
    assert "Top files:" in query_output
    assert "Assessment:" in query_output

    assert main(["review", "--repo", str(mixed_repo), "--format", "text"]) == 0
    review_output = capsys.readouterr().out
    assert "RepoBrain Review" in review_output
    assert "Top findings:" in review_output

    assert main(["baseline", "--repo", str(mixed_repo), "--format", "text"]) == 0
    baseline_output = capsys.readouterr().out
    assert "RepoBrain Baseline Saved" in baseline_output

    assert main(["ship", "--repo", str(mixed_repo), "--format", "text"]) == 0
    ship_output = capsys.readouterr().out
    assert "RepoBrain Ship Gate" in ship_output
    assert "Checks:" in ship_output
    assert "Trend:" in ship_output

    assert main(["quickstart"]) == 0
    quickstart_output = capsys.readouterr().out
    assert quickstart_output.startswith(cli_wordmark())
    assert "RepoBrain Quickstart" in quickstart_output
    assert "repobrain review --format text" in quickstart_output
    assert "repobrain ship --format text" in quickstart_output


def test_cli_patch_review_outputs_text_and_json(patch_review_repo: Path, capsys) -> None:
    assert main(["init", "--repo", str(patch_review_repo), "--force"]) == 0
    capsys.readouterr()
    assert main(["index", "--repo", str(patch_review_repo)]) == 0
    capsys.readouterr()

    route_path = patch_review_repo / "backend" / "app" / "api" / "auth.py"
    route_path.write_text(
        route_path.read_text(encoding="utf-8") + "\n\nasync def audit_patch() -> None:\n    return None\n",
        encoding="utf-8",
    )

    assert main(["patch-review", "--repo", str(patch_review_repo), "--format", "text"]) == 0
    text_output = capsys.readouterr().out
    assert "RepoBrain Patch Review" in text_output
    assert "Changed files:" in text_output
    assert "Suggested tests:" in text_output
    assert "Config surfaces:" in text_output
    assert "RepoBrain Auto-Attached Files" in text_output

    assert main(["patch-review", "--repo", str(patch_review_repo)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "patch_review"
    assert payload["changed_files"]
    assert "risk_label" in payload
    assert payload["file_context"]["files"][0]["file_path"] == "backend/app/api/auth.py"


def test_cli_patch_review_rejects_base_and_files_together(patch_review_repo: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "patch-review",
                "--repo",
                str(patch_review_repo),
                "--base",
                "main",
                "--files",
                "backend/app/api/auth.py",
            ]
        )

    assert excinfo.value.code == 2


def test_cli_report_generates_local_html(mixed_repo: Path, tmp_path: Path, capsys) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    capsys.readouterr()
    assert main(["index", "--repo", str(mixed_repo)]) == 0
    capsys.readouterr()
    output = tmp_path / "report.html"

    assert main(["report", "--repo", str(mixed_repo), "--output", str(output), "--format", "text"]) == 0
    report_output = capsys.readouterr().out

    assert output.exists()
    assert "RepoBrain Report" in report_output
    assert "RepoBrain" in output.read_text(encoding="utf-8")
    assert "Control Room Report" in output.read_text(encoding="utf-8")
    assert "Ship Gate" in output.read_text(encoding="utf-8")
    assert "Baseline Trend" in output.read_text(encoding="utf-8")
    assert "Provider Posture" in output.read_text(encoding="utf-8")
    assert "Embedding model:" in output.read_text(encoding="utf-8")


def test_python_module_entrypoint_runs_quickstart() -> None:
    repo_root = Path(__file__).parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    completed = subprocess.run(
        [sys.executable, "-m", "repobrain.cli", "quickstart"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout.startswith(cli_wordmark())
    assert "RepoBrain Quickstart" in completed.stdout


def test_cli_release_check_outputs_text(capsys) -> None:
    repo_root = Path(__file__).parents[1]

    assert main(["release-check", "--repo", str(repo_root), "--format", "text"]) == 0
    output = capsys.readouterr().out

    assert "RepoBrain Release Check" in output
    assert "version alignment" in output
    assert "frontend build assets" in output


def test_cli_demo_clean_outputs_text(tmp_path: Path, capsys) -> None:
    repo_root = tmp_path / "demo_repo"
    (repo_root / "dist").mkdir(parents=True, exist_ok=True)
    (repo_root / "dist" / "artifact.whl").write_text("wheel", encoding="utf-8")
    (repo_root / "webapp" / "dist").mkdir(parents=True, exist_ok=True)
    (repo_root / "webapp" / "dist" / "index.html").write_text("<html></html>", encoding="utf-8")

    assert main(["demo-clean", "--repo", str(repo_root), "--format", "text", "--dry-run"]) == 0
    output = capsys.readouterr().out

    assert "RepoBrain Demo Clean" in output
    assert "Mode: dry-run" in output
    assert "Preserved:" in output
    assert str((repo_root / "webapp" / "dist").resolve()) in output


def test_cli_first_look_outputs_local_demo_summary(mixed_repo: Path, capsys) -> None:
    assert main(["first-look", "--repo", str(mixed_repo), "--format", "text"]) == 0
    output = capsys.readouterr().out

    assert "RepoBrain First Look" in output
    assert "Mode: local-only" in output
    assert "Indexed surface:" in output
    assert "Starter questions already tested:" in output
    assert "Report:" in output
    assert (mixed_repo / ".repobrain" / "report.html").exists()


def test_cli_demo_alias_can_skip_report(mixed_repo: Path, capsys) -> None:
    assert main(["demo", "--repo", str(mixed_repo), "--no-report", "--format", "text"]) == 0
    output = capsys.readouterr().out

    assert "RepoBrain First Look" in output
    assert "Report:" not in output


def test_terminal_styling_is_opt_in(monkeypatch) -> None:
    monkeypatch.setattr("repobrain.ux._terminal_supports_color", lambda stream=None: True)
    payload = {"files": 1, "chunks": 2, "symbols": 3, "edges": 4, "parsers": {"heuristic": 1}}

    plain_text = payload_to_text(payload)
    styled_text = payload_to_text(payload, styled=True)
    quickstart_styled = quickstart_text(styled=True)

    assert "\x1b[" not in plain_text
    assert "\x1b[" in styled_text
    assert "\x1b[" in quickstart_styled


def test_workspace_query_text_includes_comparison_and_citations() -> None:
    payload = {
        "kind": "workspace_query",
        "query": "auth callback",
        "current_repo": "c:/repo-a",
        "project_count": 2,
        "context_applied": True,
        "comparison": {
            "best_match": {
                "name": "repo-a",
                "repo_root": "c:/repo-a",
                "confidence": 0.88,
                "evidence_score": 0.77,
                "global_rank": 1,
                "intent": "locate",
                "summary": "locate via auth_service.py; no major warnings",
            },
            "active_rank": 1,
            "shared_hotspots": [{"label": "auth_service.py", "count": 2, "repos": ["repo-a", "repo-b"]}],
            "global_evidence": [
                {
                    "name": "repo-a",
                    "repo_root": "c:/repo-a",
                    "active": True,
                    "rank": 1,
                    "file_path": "backend/auth_service.py",
                    "language": "python",
                    "role": "service",
                    "score": 0.77,
                    "start_line": 12,
                    "end_line": 24,
                    "symbol_name": "handle_callback",
                    "reasons": ["vector", "path_overlap"],
                    "preview": "def handle_callback(...): return finalize_auth()",
                }
            ],
            "notes": ["Best evidence currently leans toward repo-a (0.880)."],
        },
        "results": [
            {
                "name": "repo-a",
                "repo_root": "c:/repo-a",
                "active": True,
                "confidence": 0.88,
                "evidence_score": 0.77,
                "global_rank": 1,
                "intent": "locate",
                "top_files": ["backend/auth_service.py"],
                "warnings": ["Cross-check route wiring."],
                "summary": "locate via auth_service.py; Cross-check route wiring.",
                "memory_summary": "Notes: auth callback is the main thread.",
                "next_questions": ["Trace callback route to service next?"],
                "citations": [
                    {
                        "file_path": "backend/auth_service.py",
                        "language": "python",
                        "role": "service",
                        "score": 0.77,
                        "start_line": 12,
                        "end_line": 24,
                        "symbol_name": "handle_callback",
                        "reasons": ["vector", "path_overlap"],
                        "preview": "def handle_callback(...): return finalize_auth()",
                    }
                ],
            }
        ],
        "errors": [],
    }

    output = payload_to_text(payload)

    assert "Comparison notes:" in output
    assert "Shared hotspots:" in output
    assert "Global evidence leaders:" in output
    assert "citations:" in output
    assert "rank=#1 citation=0.770 confidence=0.880" in output
    assert "backend/auth_service.py:12-24::handle_callback" in output


def test_chat_native_commands_apply_focus_context_and_memory(
    mixed_repo: Path,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    capsys.readouterr()

    second_repo = tmp_path / "sample_repo_two"
    shutil.copytree(mixed_repo, second_repo)

    recorded: dict[str, list[tuple[str, str, str | None]]] = {"query": [], "trace": []}

    def fake_result(repo_name: str, query: str) -> QueryResult:
        return QueryResult(
            query=query,
            intent=QueryIntent.LOCATE,
            top_files=[
                FileEvidence(
                    file_path=f"{repo_name}/backend/auth_service.py",
                    language="python",
                    role="service",
                    score=0.91,
                    reasons=["path_overlap", "role_match"],
                )
            ],
            snippets=[],
            call_chain=[],
            dependency_edges=[],
            edit_targets=[],
            confidence=0.74,
            warnings=["Evidence is concentrated in one file. Cross-check nearby routes, services, and config."],
            next_questions=["Should RepoBrain trace route flow or service flow next?"],
            plan=QueryPlan(intent=QueryIntent.LOCATE, steps=["planner"], rewritten_queries=[query]),
        )

    def fake_query(self, query: str, forced_intent=None, limit: int = 6, context: str | None = None):
        recorded["query"].append((self.config.resolved_repo_root.name, query, context))
        return fake_result(self.config.resolved_repo_root.name, query)

    def fake_trace(self, query: str, *, context: str | None = None):
        recorded["trace"].append((self.config.resolved_repo_root.name, query, context))
        return fake_result(self.config.resolved_repo_root.name, query)

    inputs = iter(
        [
            "/remember auth callback is the main thread",
            "/focus auth callback handling",
            "/focus",
            "/evidence show me the callback files",
            "/summary",
            f"/add {second_repo}",
            "/projects",
            "/use sample_repo_two",
            "/map login path",
            "/multi auth callback",
            "/remember clear",
            "/focus clear",
            "/query plain question after clear",
            "/exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(RepoBrainEngine, "query", fake_query)
    monkeypatch.setattr(RepoBrainEngine, "trace", fake_trace)

    assert main(["chat", "--repo", str(mixed_repo)]) == 0
    output = capsys.readouterr().out

    assert "Active focus: auth callback handling" in output
    assert "Focus cleared." in output
    assert "Stored repo memory note." in output
    assert "RepoBrain Cross-Repo Query" in output
    assert "sample_repo_two" in output
    assert recorded["query"][0][1] == "show me the callback files"
    assert "auth callback is the main thread" in str(recorded["query"][0][2])
    assert "Focus: auth callback handling." in str(recorded["query"][0][2])
    assert recorded["trace"][0][0] == "sample_repo_two"
    assert recorded["trace"][0][1] == "login path"
    assert "sample_repo_two/backend/auth_service.py" in output
    assert recorded["query"][-1][1] == "plain question after clear"
    assert "sample_repo/backend/auth_service.py" in output


def test_cli_workspace_commands_manage_projects_and_notes(mixed_repo: Path, capsys) -> None:
    assert main(["workspace", "add", str(mixed_repo), "--format", "text"]) == 0
    add_output = capsys.readouterr().out
    assert "Tracked repo and set active" in add_output
    assert str(mixed_repo) in add_output

    assert main(["workspace", "remember", "payment retry flow lives in backend", "--format", "text"]) == 0
    remember_output = capsys.readouterr().out
    assert "Stored repo memory note." in remember_output
    assert "payment retry flow lives in backend" in remember_output

    assert main(["workspace", "summary", "--format", "text"]) == 0
    summary_output = capsys.readouterr().out
    assert "RepoBrain Memory Summary" in summary_output
    assert "payment retry flow lives in backend" in summary_output

    assert main(["workspace", "list", "--format", "text"]) == 0
    list_output = capsys.readouterr().out
    assert "RepoBrain Workspace" in list_output
    assert "[active]" in list_output


def test_chat_launcher_prefers_project_virtualenv() -> None:
    launcher = Path(__file__).parents[1] / "chat.cmd"
    content = launcher.read_text(encoding="utf-8")

    assert "venv\\Scripts\\python.exe" in content
    assert '"%PYEXE%" -m repobrain.cli chat --repo .' in content


def test_report_launcher_prefers_project_virtualenv_and_opens_report() -> None:
    launcher = Path(__file__).parents[1] / "report.cmd"
    content = launcher.read_text(encoding="utf-8")

    assert "venv\\Scripts\\python.exe" in content
    assert '"%PYEXE%" -m repobrain.cli report --repo . --format text' in content
    assert 'start "" ".repobrain\\report.html"' in content
