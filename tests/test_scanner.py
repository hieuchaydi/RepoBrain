from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from repobrain.config import RepoBrainConfig
from repobrain.engine.scanner import FileCandidate, ParseArtifacts, RepositoryScanner
from repobrain.models import Symbol


class StubParserAdapter:
    name = "tree_sitter_stub"

    def __init__(self, languages: set[str]) -> None:
        self.languages = languages

    def can_parse(self, language: str) -> bool:
        return language in self.languages

    def parse(self, candidate: FileCandidate, content: str, scanner: RepositoryScanner) -> ParseArtifacts | None:
        if not self.can_parse(candidate.language):
            return None
        return ParseArtifacts(
            symbols=[Symbol("from_stub", "function", 1, 1, "def from_stub():")],
            imports=["stub.import"],
            parser_name=self.name,
            parser_detail="test-stub",
        )

    def describe_language(self, language: str) -> dict[str, object]:
        ready = self.can_parse(language)
        return {"ready": ready, "source": "test-stub" if ready else "", "error": "" if ready else "disabled"}


def test_scanner_prefers_optional_parser_when_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "service.py").write_text("def real_symbol():\n    return True\n", encoding="utf-8")

    config = RepoBrainConfig.default(repo_root)
    scanner = RepositoryScanner(config, parser_adapters=[StubParserAdapter({"python"})])
    candidate = scanner.scan()[0]
    document = scanner.parse(candidate)

    assert document.parser_name == "tree_sitter_stub"
    assert document.parser_detail == "test-stub"
    assert document.symbols[0].name == "from_stub"
    assert scanner.capabilities()["language_parsers"]["python"]["selected"] == "tree_sitter_stub"


def test_scanner_falls_back_to_heuristic_when_optional_parser_disabled(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "service.py").write_text("def real_symbol():\n    return True\n", encoding="utf-8")

    config = RepoBrainConfig.default(repo_root)
    config.parsing.prefer_tree_sitter = False
    scanner = RepositoryScanner(config, parser_adapters=[StubParserAdapter({"python"})])
    candidate = scanner.scan()[0]
    document = scanner.parse(candidate)

    assert document.parser_name == "heuristic"
    assert document.symbols[0].name == "real_symbol"
    assert scanner.capabilities()["language_parsers"]["python"]["selected"] == "heuristic"


def test_python_named_imports_create_import_call_edges(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "route.py").write_text(
        "from services.auth import login_with_google as start_google\n\n"
        "def handler():\n"
        "    return start_google()\n",
        encoding="utf-8",
    )

    config = RepoBrainConfig.default(repo_root)
    config.parsing.prefer_tree_sitter = False
    scanner = RepositoryScanner(config, parser_adapters=[])
    document = scanner.parse(scanner.scan()[0])

    assert "start_google" in document.imports
    assert any(edge.edge_type == "imports_call" and edge.target == "start_google" for edge in document.edges)


def test_typescript_named_imports_create_import_call_edges(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "route.ts").write_text(
        'import { handleGitHubCallback as handleCallback } from "../services/oauth";\n\n'
        "export async function githubCallback(code: string) {\n"
        "  return handleCallback(code);\n"
        "}\n",
        encoding="utf-8",
    )

    config = RepoBrainConfig.default(repo_root)
    config.parsing.prefer_tree_sitter = False
    scanner = RepositoryScanner(config, parser_adapters=[])
    document = scanner.parse(scanner.scan()[0])

    assert "handleCallback" in document.imports
    assert any(edge.edge_type == "imports_call" and edge.target == "handleCallback" for edge in document.edges)


def test_scanner_detects_more_realistic_route_job_and_config_roles(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "app" / "api" / "auth").mkdir(parents=True)
    (repo_root / "app" / "tasks").mkdir(parents=True)
    (repo_root / "app" / "core").mkdir(parents=True)
    (repo_root / "app" / "services").mkdir(parents=True)

    (repo_root / "app" / "api" / "auth" / "route.ts").write_text(
        "export async function GET() {\n  return Response.json({ ok: true });\n}\n",
        encoding="utf-8",
    )
    (repo_root / "app" / "tasks" / "revalidate.ts").write_text(
        "export async function revalidateTask() {\n  return 'queued';\n}\n",
        encoding="utf-8",
    )
    (repo_root / "app" / "core" / "settings.py").write_text(
        "from pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    debug: bool = False\n",
        encoding="utf-8",
    )
    (repo_root / "app" / "services" / "auth_service.py").write_text(
        "def login_service():\n    return True\n",
        encoding="utf-8",
    )

    config = RepoBrainConfig.default(repo_root)
    scanner = RepositoryScanner(config, parser_adapters=[])
    roles = {candidate.rel_path: candidate.role for candidate in scanner.scan()}

    assert roles["app/api/auth/route.ts"] == "route"
    assert roles["app/tasks/revalidate.ts"] == "job"
    assert roles["app/core/settings.py"] == "config"
    assert roles["app/services/auth_service.py"] == "service"


def test_scanner_extracts_framework_style_hints(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "app" / "api").mkdir(parents=True)
    file_path = repo_root / "app" / "api" / "route.ts"
    file_path.write_text(
        "export async function POST() {\n"
        "  const token = process.env.API_TOKEN;\n"
        "  return Response.json({ queued: true });\n"
        "}\n",
        encoding="utf-8",
    )

    config = RepoBrainConfig.default(repo_root)
    config.parsing.prefer_tree_sitter = False
    scanner = RepositoryScanner(config, parser_adapters=[])
    document = scanner.parse(scanner.scan()[0])

    assert "route_flow" in document.hints
    assert "config_touchpoint" in document.hints


def test_scanner_uses_real_tree_sitter_parser_when_available(tmp_path: Path) -> None:
    required_modules = ["tree_sitter"]
    optional_sources = ["tree_sitter_language_pack", "tree_sitter_python"]
    if not all(importlib.util.find_spec(module) for module in required_modules):
        pytest.skip("tree-sitter runtime is not installed in this environment.")
    if not any(importlib.util.find_spec(module) for module in optional_sources):
        pytest.skip("No tree-sitter grammar source is installed in this environment.")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "service.py").write_text(
        "def outer():\n"
        "    value = 1\n"
        "    return value\n\n"
        "class AuthService:\n"
        "    def login(self):\n"
        "        return True\n",
        encoding="utf-8",
    )

    config = RepoBrainConfig.default(repo_root)
    scanner = RepositoryScanner(config)
    document = scanner.parse(scanner.scan()[0])

    if document.parser_name != "tree_sitter":
        pytest.skip("tree-sitter extras are installed but no ready parser was selected in this environment.")

    assert document.parser_detail
    assert any(symbol.name == "outer" and symbol.end_line >= 3 for symbol in document.symbols)
    assert any(symbol.name == "AuthService" and symbol.end_line >= 6 for symbol in document.symbols)
