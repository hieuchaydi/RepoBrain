from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from repobrain.cli import main


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


def test_cli_chat_can_exit(mixed_repo: Path, capsys, monkeypatch) -> None:
    assert main(["init", "--repo", str(mixed_repo), "--force"]) == 0
    capsys.readouterr()
    assert main(["index", "--repo", str(mixed_repo)]) == 0
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _: "/exit")
    assert main(["chat", "--repo", str(mixed_repo)]) == 0
    chat_output = capsys.readouterr().out
    assert "RepoBrain chat is local-only" in chat_output


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
    assert "RepoBrain Quickstart" in quickstart_output
    assert "repobrain review --format text" in quickstart_output
    assert "repobrain ship --format text" in quickstart_output


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
    assert "RepoBrain Quickstart" in completed.stdout


def test_cli_release_check_outputs_text(capsys) -> None:
    repo_root = Path(__file__).parents[1]

    assert main(["release-check", "--repo", str(repo_root), "--format", "text"]) == 0
    output = capsys.readouterr().out

    assert "RepoBrain Release Check" in output
    assert "version alignment" in output
    assert "frontend build assets" in output


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
