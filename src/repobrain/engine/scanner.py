from __future__ import annotations

import fnmatch
import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from repobrain.config import RepoBrainConfig
from repobrain.models import Chunk, Edge, ParsedDocument, Symbol

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}
SUPPORTED_LANGUAGES = sorted(set(LANGUAGE_BY_SUFFIX.values()))

PYTHON_SYMBOL_RE = re.compile(r"^(?P<indent>\s*)(?P<kind>async\s+def|def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
PYTHON_FROM_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+(.+)")
PYTHON_IMPORT_RE = re.compile(r"^\s*import\s+(.+)")
TS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:(?P<kind>async\s+function|function|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)|"
    r"(?:(?:const|let|var)\s+(?P<var_name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*=>))"
)
TS_IMPORT_RE = re.compile(r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]")
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
ROUTE_HINT_RE = re.compile(
    r"(router\.(get|post|put|delete|patch)|app\.(get|post|put|delete|patch)|@router\.|@app\.route|APIRouter|Blueprint|"
    r"export\s+async\s+function\s+(GET|POST|PUT|DELETE|PATCH)|NextRequest|NextResponse|Response\.json\()",
    re.IGNORECASE,
)
JOB_HINT_RE = re.compile(r"(cron|schedule|retry|job|worker|queue|shared_task|celery|bullmq|enqueue|background)", re.IGNORECASE)
CONFIG_HINT_RE = re.compile(r"(os\.getenv|os\.environ|process\.env|import\.meta\.env|settings\.|config\.|BaseSettings|load_dotenv|dotenv)", re.IGNORECASE)
ROUTE_PATH_PARTS = {"api", "apis", "routes", "route", "controllers", "controller", "handlers", "handler", "endpoints", "endpoint"}
JOB_PATH_PARTS = {"jobs", "job", "workers", "worker", "tasks", "task", "queues", "queue", "background", "cron"}
CONFIG_PATH_PARTS = {"config", "configs", "settings", "setting"}
SERVICE_PATH_PARTS = {"services", "service", "usecases", "usecase"}
ROUTE_FILE_STEMS = {"route", "handler", "callback", "webhook"}
JOB_FILE_STEMS = {"job", "worker", "task", "queue", "scheduler", "revalidate"}
CONFIG_FILE_STEMS = {"config", "settings", "configuration", "env"}

TREE_SITTER_LANGUAGE_ALIASES = {
    "python": ("python",),
    "javascript": ("javascript", "js"),
    "typescript": ("typescript", "ts", "tsx"),
}
TREE_SITTER_LANGUAGE_MODULES = {
    "python": ("tree_sitter_python", ("language",)),
    "javascript": ("tree_sitter_javascript", ("language",)),
    "typescript": ("tree_sitter_typescript", ("language_typescript", "language_tsx", "language")),
}


@dataclass(slots=True)
class FileCandidate:
    path: Path
    rel_path: str
    language: str
    role: str


@dataclass(slots=True)
class ParseArtifacts:
    symbols: list[Symbol]
    imports: list[str]
    parser_name: str
    parser_detail: str = ""


class ParserAdapter(Protocol):
    name: str

    def can_parse(self, language: str) -> bool:
        ...

    def parse(self, candidate: FileCandidate, content: str, scanner: RepositoryScanner) -> ParseArtifacts | None:
        ...

    def describe_language(self, language: str) -> dict[str, object]:
        ...


class HeuristicParserAdapter:
    name = "heuristic"

    def can_parse(self, language: str) -> bool:
        return language in SUPPORTED_LANGUAGES

    def parse(self, candidate: FileCandidate, content: str, scanner: RepositoryScanner) -> ParseArtifacts:
        if candidate.language == "python":
            symbols, imports = scanner._parse_python_heuristic(content)
        else:
            symbols, imports = scanner._parse_typescript_like_heuristic(content)
        return ParseArtifacts(symbols=symbols, imports=imports, parser_name=self.name, parser_detail="regex")

    def describe_language(self, language: str) -> dict[str, object]:
        return {
            "ready": self.can_parse(language),
            "source": "built-in-regex",
            "error": "" if self.can_parse(language) else "unsupported language",
        }


class TreeSitterParserAdapter:
    name = "tree_sitter"

    def __init__(self, enabled_languages: list[str]) -> None:
        self.enabled_languages = set(enabled_languages)
        self.runtime_available = False
        self._factories: dict[str, Any] = {}
        self._sources: dict[str, str] = {}
        self._errors: dict[str, str] = {}
        self._discover()

    def can_parse(self, language: str) -> bool:
        return language in self.enabled_languages and language in self._factories

    def available_languages(self) -> list[str]:
        return sorted(self._factories)

    def parse(self, candidate: FileCandidate, content: str, scanner: RepositoryScanner) -> ParseArtifacts | None:
        if not self.can_parse(candidate.language):
            return None

        source_bytes = content.encode("utf-8")
        try:
            parser = self._factories[candidate.language]()
            tree = parser.parse(source_bytes)
            root_node = getattr(tree, "root_node", None)
            if root_node is None:
                return None
            symbols = scanner._extract_tree_sitter_symbols(candidate.language, root_node, content, source_bytes)
            imports = scanner._extract_imports(candidate.language, content)
            return ParseArtifacts(
                symbols=symbols,
                imports=imports,
                parser_name=self.name,
                parser_detail=self._sources.get(candidate.language, "unknown"),
            )
        except Exception as exc:  # pragma: no cover - depends on optional native parser packages
            self._errors[candidate.language] = str(exc)
            return None

    def describe_language(self, language: str) -> dict[str, object]:
        ready = self.can_parse(language)
        return {
            "ready": ready,
            "source": self._sources.get(language, ""),
            "error": "" if ready else self._errors.get(language, "tree-sitter grammar is not installed"),
        }

    def _discover(self) -> None:
        self._discover_language_pack("tree_sitter_language_pack")
        self._discover_language_pack("tree_sitter_languages")
        self._discover_language_modules()
        if not self.runtime_available:
            try:
                importlib.import_module("tree_sitter")
                self.runtime_available = True
            except ImportError:
                pass

    def _discover_language_pack(self, module_name: str) -> None:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return

        self.runtime_available = True
        get_parser = getattr(module, "get_parser", None)
        if not callable(get_parser):
            return

        for language in self.enabled_languages:
            if language in self._factories:
                continue
            last_error = ""
            for alias in TREE_SITTER_LANGUAGE_ALIASES.get(language, (language,)):
                try:
                    parser = get_parser(alias)
                    parser.parse(b"")
                except Exception as exc:  # pragma: no cover - depends on optional native parser packages
                    last_error = str(exc)
                    continue
                self._factories[language] = lambda alias=alias, get_parser=get_parser: get_parser(alias)
                self._sources[language] = f"{module_name}:{alias}"
                last_error = ""
                break
            if last_error:
                self._errors[language] = last_error

    def _discover_language_modules(self) -> None:
        try:
            runtime = importlib.import_module("tree_sitter")
        except ImportError:
            return

        self.runtime_available = True
        parser_cls = getattr(runtime, "Parser", None)
        if parser_cls is None:
            return

        for language, (module_name, function_names) in TREE_SITTER_LANGUAGE_MODULES.items():
            if language not in self.enabled_languages or language in self._factories:
                continue
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue

            for function_name in function_names:
                language_factory = getattr(module, function_name, None)
                if not callable(language_factory):
                    continue
                factory = self._make_parser_factory(runtime, parser_cls, language_factory)
                try:
                    parser = factory()
                    parser.parse(b"")
                except Exception as exc:  # pragma: no cover - depends on optional native parser packages
                    self._errors[language] = str(exc)
                    continue
                self._factories[language] = factory
                self._sources[language] = f"{module_name}:{function_name}"
                break

    def _make_parser_factory(self, runtime: object, parser_cls: object, language_factory: object) -> object:
        def factory() -> object:
            parser = parser_cls()
            language = language_factory()
            self._set_parser_language(runtime, parser, language)
            return parser

        return factory

    def _set_parser_language(self, runtime: object, parser: object, language: object) -> None:
        try:
            if hasattr(parser, "set_language"):
                parser.set_language(language)
            else:
                parser.language = language
            return
        except Exception as direct_error:
            language_cls = getattr(runtime, "Language", None)
            if language_cls is None:
                raise direct_error
            try:
                wrapped_language = language_cls(language)
                if hasattr(parser, "set_language"):
                    parser.set_language(wrapped_language)
                else:
                    parser.language = wrapped_language
                return
            except Exception:
                raise direct_error


class RepositoryScanner:
    def __init__(self, config: RepoBrainConfig, parser_adapters: list[ParserAdapter] | None = None) -> None:
        self.config = config
        self.root = config.resolved_repo_root
        self.ignore_patterns = self._load_ignore_patterns()
        self.heuristic_parser = HeuristicParserAdapter()
        self.optional_parsers = (
            parser_adapters if parser_adapters is not None else [TreeSitterParserAdapter(config.parsing.tree_sitter_languages)]
        )

    def scan(self) -> list[FileCandidate]:
        candidates: list[FileCandidate] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel_path = path.relative_to(self.root).as_posix()
            language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
            if language is None:
                continue
            if self._should_ignore(path, rel_path):
                continue
            if path.stat().st_size > self.config.indexing.max_file_size_bytes:
                continue
            candidates.append(FileCandidate(path=path, rel_path=rel_path, language=language, role=self._detect_role(rel_path)))
        return sorted(candidates, key=lambda item: item.rel_path)

    def parse(self, candidate: FileCandidate) -> ParsedDocument:
        content = candidate.path.read_text(encoding="utf-8", errors="ignore")
        artifacts = self._parse_with_best_adapter(candidate, content)
        hints = self._extract_hints(candidate.rel_path, content)
        edges = self._extract_edges(candidate.rel_path, content, artifacts.symbols, artifacts.imports)
        chunks = self._build_chunks(candidate.rel_path, candidate.language, candidate.role, content, artifacts.symbols, hints)
        return ParsedDocument(
            file_path=candidate.rel_path,
            language=candidate.language,
            role=candidate.role,
            content=content,
            symbols=artifacts.symbols,
            imports=artifacts.imports,
            edges=edges,
            chunks=chunks,
            hints=hints,
            parser_name=artifacts.parser_name,
            parser_detail=artifacts.parser_detail,
        )

    def capabilities(self) -> dict[str, object]:
        enabled_languages = set(self.config.parsing.tree_sitter_languages)
        language_parsers: dict[str, dict[str, object]] = {}
        ready_optional_languages: set[str] = set()

        for language in SUPPORTED_LANGUAGES:
            selected = self.heuristic_parser.name
            optional_details = []
            for adapter in self.optional_parsers:
                detail = adapter.describe_language(language)
                optional_details.append({"name": adapter.name, **detail})
                if adapter.can_parse(language):
                    ready_optional_languages.add(language)
                if (
                    selected == self.heuristic_parser.name
                    and self.config.parsing.prefer_tree_sitter
                    and language in enabled_languages
                    and adapter.can_parse(language)
                ):
                    selected = adapter.name

            language_parsers[language] = {
                "selected": selected,
                "tree_sitter_enabled": language in enabled_languages,
                "heuristic_fallback": True,
                "optional_adapters": optional_details,
            }

        return {
            "tree_sitter_available": any(
                bool(getattr(adapter, "runtime_available", False)) for adapter in self.optional_parsers if "tree_sitter" in adapter.name
            ),
            "tree_sitter_ready": bool(ready_optional_languages),
            "parser_preference": "tree_sitter" if self.config.parsing.prefer_tree_sitter else "heuristic",
            "heuristic_fallback": True,
            "language_parsers": language_parsers,
        }

    def _parse_with_best_adapter(self, candidate: FileCandidate, content: str) -> ParseArtifacts:
        if self.config.parsing.prefer_tree_sitter and candidate.language in set(self.config.parsing.tree_sitter_languages):
            for adapter in self.optional_parsers:
                if not adapter.can_parse(candidate.language):
                    continue
                artifacts = adapter.parse(candidate, content, self)
                if artifacts is not None:
                    return artifacts
        return self.heuristic_parser.parse(candidate, content, self)

    def _load_ignore_patterns(self) -> list[str]:
        patterns = list(self.config.indexing.exclude)
        for ignore_name in (".gitignore", ".repobrainignore"):
            ignore_path = self.root / ignore_name
            if not ignore_path.exists():
                continue
            for line in ignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    patterns.append(stripped.lstrip("./"))
        return patterns

    def _should_ignore(self, path: Path, rel_path: str) -> bool:
        for pattern in self.ignore_patterns:
            normalized = pattern.rstrip("/")
            if fnmatch.fnmatch(rel_path, normalized) or fnmatch.fnmatch(path.name, normalized):
                return True
            if normalized and any(part == normalized for part in rel_path.split("/")):
                return True
            if normalized and rel_path.startswith(normalized + "/"):
                return True
        includes = self.config.indexing.include
        if includes and not any(fnmatch.fnmatch(rel_path, item) for item in includes):
            return True
        return False

    def _detect_role(self, rel_path: str) -> str:
        lowered = rel_path.lower()
        parts = [part for part in lowered.split("/") if part]
        stem = Path(lowered).stem
        if (
            "/tests/" in lowered
            or lowered.startswith("tests/")
            or lowered.endswith("_test.py")
            or lowered.endswith("_spec.py")
            or ".test." in lowered
            or ".spec." in lowered
        ):
            return "test"
        if lowered.startswith("app/api/") or "pages/api/" in lowered:
            return "route"
        if any(part in ROUTE_PATH_PARTS for part in parts) or stem in ROUTE_FILE_STEMS:
            return "route"
        if any(part in JOB_PATH_PARTS for part in parts) or stem in JOB_FILE_STEMS:
            return "job"
        if lowered.endswith(".env") or any(part in CONFIG_PATH_PARTS for part in parts) or stem in CONFIG_FILE_STEMS:
            return "config"
        if any(part in SERVICE_PATH_PARTS for part in parts) or stem.endswith("_service"):
            return "service"
        return "module"

    def _parse_python_heuristic(self, content: str) -> tuple[list[Symbol], list[str]]:
        symbols: list[Symbol] = []
        imports: list[str] = []
        lines = content.splitlines()
        for index, line in enumerate(lines, start=1):
            if match := PYTHON_SYMBOL_RE.match(line):
                kind = match.group("kind").replace("async ", "")
                name = match.group("name")
                signature = line.strip()
                doc_hint = self._doc_hint(lines, index)
                symbols.append(Symbol(name=name, kind=kind, start_line=index, end_line=index, signature=signature, doc_hint=doc_hint))
            imports.extend(self._python_imports_from_line(line))
        self._fill_symbol_ranges(symbols, len(lines))
        return symbols, self._dedupe_imports(imports)

    def _parse_typescript_like_heuristic(self, content: str) -> tuple[list[Symbol], list[str]]:
        symbols: list[Symbol] = []
        imports: list[str] = []
        lines = content.splitlines()
        for index, line in enumerate(lines, start=1):
            if match := TS_SYMBOL_RE.match(line):
                kind = match.group("kind") or "function"
                name = match.group("name") or match.group("var_name")
                if name:
                    doc_hint = self._doc_hint(lines, index)
                    symbols.append(Symbol(name=name, kind=kind.replace("async ", ""), start_line=index, end_line=index, signature=line.strip(), doc_hint=doc_hint))
            imports.extend(self._typescript_imports_from_line(line))
        self._fill_symbol_ranges(symbols, len(lines))
        return symbols, self._dedupe_imports(imports)

    def _extract_imports(self, language: str, content: str) -> list[str]:
        if language == "python":
            _, imports = self._parse_python_heuristic(content)
            return imports
        _, imports = self._parse_typescript_like_heuristic(content)
        return imports

    def _python_imports_from_line(self, line: str) -> list[str]:
        if match := PYTHON_FROM_IMPORT_RE.match(line):
            module = match.group(1)
            imported = self._split_import_bindings(match.group(2))
            return [module, *imported]
        if match := PYTHON_IMPORT_RE.match(line):
            return self._split_import_bindings(match.group(1), keep_module_alias=True)
        return []

    def _typescript_imports_from_line(self, line: str) -> list[str]:
        match = TS_IMPORT_RE.match(line)
        if match is None:
            return []
        bindings = match.group(1).strip()
        module = match.group(2)
        imported = [module]

        if named_match := re.search(r"\{(?P<named>[^}]+)\}", bindings):
            imported.extend(self._split_import_bindings(named_match.group("named")))

        before_named = re.sub(r"\{[^}]+\}", "", bindings).strip().strip(",")
        if before_named.startswith("* as "):
            imported.append(before_named.removeprefix("* as ").strip())
        elif before_named and not before_named.startswith("{"):
            imported.extend(self._split_import_bindings(before_named))

        return self._dedupe_imports(imported)

    def _split_import_bindings(self, raw_imports: str, keep_module_alias: bool = False) -> list[str]:
        imports: list[str] = []
        for raw_item in raw_imports.split(","):
            item = raw_item.strip()
            if not item or item.startswith("(") or item.startswith("*"):
                continue
            item = item.split("#", 1)[0].strip()
            item = item.strip("()")
            if not item:
                continue
            if " as " in item:
                original, alias = [part.strip() for part in item.split(" as ", 1)]
                imports.append(alias)
                if keep_module_alias:
                    imports.append(original)
            elif ":" in item:
                original, alias = [part.strip() for part in item.split(":", 1)]
                imports.append(alias)
                imports.append(original)
            else:
                imports.append(item.split(".")[-1] if keep_module_alias else item)
        return self._dedupe_imports(imports)

    def _dedupe_imports(self, imports: list[str]) -> list[str]:
        deduped: list[str] = []
        for item in imports:
            cleaned = item.strip()
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped

    def _extract_tree_sitter_symbols(
        self,
        language: str,
        root_node: object,
        content: str,
        source_bytes: bytes,
    ) -> list[Symbol]:
        lines = content.splitlines()
        if language == "python":
            symbols = self._tree_sitter_python_symbols(root_node, lines, source_bytes)
        else:
            symbols = self._tree_sitter_typescript_like_symbols(root_node, lines, source_bytes)
        return self._dedupe_symbols(symbols)

    def _tree_sitter_python_symbols(self, root_node: object, lines: list[str], source_bytes: bytes) -> list[Symbol]:
        symbols: list[Symbol] = []
        for node in self._walk_tree(root_node):
            node_type = getattr(node, "type", "")
            if node_type not in {"function_definition", "class_definition"}:
                continue
            name_node = self._field_node(node, "name")
            if name_node is None:
                continue
            start_line = self._node_start_line(node)
            end_line = self._node_end_line(node, len(lines))
            name = self._node_text(name_node, source_bytes).strip()
            kind = "class" if node_type == "class_definition" else "def"
            symbols.append(self._symbol_from_node(name, kind, start_line, end_line, lines))
        return symbols

    def _tree_sitter_typescript_like_symbols(self, root_node: object, lines: list[str], source_bytes: bytes) -> list[Symbol]:
        symbols: list[Symbol] = []
        for node in self._walk_tree(root_node):
            node_type = getattr(node, "type", "")
            if node_type in {"function_declaration", "class_declaration", "method_definition"}:
                name_node = self._field_node(node, "name")
                if name_node is None:
                    continue
                kind = "class" if node_type == "class_declaration" else "function"
                symbols.append(
                    self._symbol_from_node(
                        self._node_text(name_node, source_bytes).strip(),
                        kind,
                        self._node_start_line(node),
                        self._node_end_line(node, len(lines)),
                        lines,
                    )
                )
            elif node_type == "variable_declarator":
                value_node = self._field_node(node, "value")
                if value_node is None or getattr(value_node, "type", "") not in {"arrow_function", "function_expression"}:
                    continue
                name_node = self._field_node(node, "name")
                if name_node is None:
                    continue
                symbols.append(
                    self._symbol_from_node(
                        self._node_text(name_node, source_bytes).strip(),
                        "function",
                        self._node_start_line(node),
                        self._node_end_line(node, len(lines)),
                        lines,
                    )
                )
        return symbols

    def _symbol_from_node(self, name: str, kind: str, start_line: int, end_line: int, lines: list[str]) -> Symbol:
        safe_start = max(start_line, 1)
        safe_end = max(end_line, safe_start)
        signature = lines[safe_start - 1].strip() if safe_start <= len(lines) else name
        return Symbol(
            name=name,
            kind=kind,
            start_line=safe_start,
            end_line=safe_end,
            signature=signature,
            doc_hint=self._doc_hint(lines, safe_start),
        )

    def _walk_tree(self, node: object) -> list[object]:
        nodes = [node]
        for child in getattr(node, "children", []):
            nodes.extend(self._walk_tree(child))
        return nodes

    def _field_node(self, node: object, field_name: str) -> object | None:
        child_by_field_name = getattr(node, "child_by_field_name", None)
        if not callable(child_by_field_name):
            return None
        return child_by_field_name(field_name)

    def _node_text(self, node: object, source_bytes: bytes) -> str:
        return source_bytes[getattr(node, "start_byte") : getattr(node, "end_byte")].decode("utf-8", errors="ignore")

    def _node_start_line(self, node: object) -> int:
        return int(getattr(node, "start_point")[0]) + 1

    def _node_end_line(self, node: object, total_lines: int) -> int:
        row = int(getattr(node, "end_point")[0]) + 1
        return min(max(row, 1), max(total_lines, 1))

    def _dedupe_symbols(self, symbols: list[Symbol]) -> list[Symbol]:
        unique: list[Symbol] = []
        seen: set[tuple[str, str, int, int]] = set()
        for symbol in sorted(symbols, key=lambda item: (item.start_line, item.end_line, item.name)):
            key = (symbol.name, symbol.kind, symbol.start_line, symbol.end_line)
            if key in seen:
                continue
            seen.add(key)
            unique.append(symbol)
        return unique

    def _fill_symbol_ranges(self, symbols: list[Symbol], total_lines: int) -> None:
        for current, nxt in zip(symbols, symbols[1:]):
            current.end_line = max(current.start_line, nxt.start_line - 1)
        if symbols:
            symbols[-1].end_line = total_lines

    def _doc_hint(self, lines: list[str], line_number: int) -> str:
        for pointer in range(line_number - 2, max(line_number - 5, -1), -1):
            if pointer < 0:
                continue
            candidate = lines[pointer].strip()
            if candidate.startswith(('"""', "'''", "#", "//", "/**", "*")):
                return candidate.strip("#/ *'")
            if candidate:
                break
        return ""

    def _extract_hints(self, rel_path: str, content: str) -> list[str]:
        hints: list[str] = []
        lowered_path = rel_path.lower()
        if ROUTE_HINT_RE.search(content) or lowered_path.startswith("app/api/") or "pages/api/" in lowered_path or "/api/" in lowered_path or "/routes/" in lowered_path:
            hints.append("route_flow")
        if JOB_HINT_RE.search(content) or any(token in lowered_path for token in ("/jobs/", "/workers/", "/tasks/", "/queue/", "/background/")):
            hints.append("job_or_retry")
        if CONFIG_HINT_RE.search(content) or any(token in lowered_path for token in ("/config/", "/configs/", "/settings/")):
            hints.append("config_touchpoint")
        if "oauth" in content.lower() or "github" in content.lower() or "google" in content.lower():
            hints.append("oauth_or_social_login")
        return hints

    def _extract_edges(self, rel_path: str, content: str, symbols: list[Symbol], imports: list[str]) -> list[Edge]:
        lines = content.splitlines()
        symbol_names = {symbol.name for symbol in symbols}
        imported_names = {item.split(".")[-1] for item in imports}
        edges: list[Edge] = []
        for symbol in symbols:
            body = "\n".join(lines[symbol.start_line - 1 : symbol.end_line])
            for match in CALL_RE.finditer(body):
                target = match.group(1)
                if target == symbol.name:
                    continue
                if target in symbol_names:
                    edges.append(Edge(rel_path, symbol.name, target, "calls", rel_path))
                elif target in imported_names:
                    edges.append(Edge(rel_path, symbol.name, target, "imports_call", None))
        for imported in imports:
            edges.append(Edge(rel_path, "__module__", imported, "imports", None))
        return edges

    def _build_chunks(
        self,
        rel_path: str,
        language: str,
        role: str,
        content: str,
        symbols: list[Symbol],
        hints: list[str],
    ) -> list[Chunk]:
        lines = content.splitlines()
        max_lines = self.config.indexing.chunk_max_lines
        overlap = self.config.indexing.chunk_overlap_lines
        chunks: list[Chunk] = []
        if symbols:
            for index, symbol in enumerate(symbols):
                start = symbol.start_line
                end = min(symbol.end_line, len(lines))
                neighborhood = []
                if index > 0:
                    neighborhood.append(symbols[index - 1].name)
                if index + 1 < len(symbols):
                    neighborhood.append(symbols[index + 1].name)
                body_lines = lines[start - 1 : end]
                if len(body_lines) <= max_lines:
                    chunks.append(
                        self._make_chunk(rel_path, language, role, start, end, body_lines, symbol, neighborhood, hints)
                    )
                    continue
                window_start = start
                while window_start <= end:
                    window_end = min(window_start + max_lines - 1, end)
                    chunk_lines = lines[window_start - 1 : window_end]
                    chunks.append(
                        self._make_chunk(rel_path, language, role, window_start, window_end, chunk_lines, symbol, neighborhood, hints)
                    )
                    if window_end >= end:
                        break
                    window_start = max(window_start + max_lines - overlap, window_start + 1)
        else:
            start = 1
            while start <= len(lines):
                end = min(start + max_lines - 1, len(lines))
                body_lines = lines[start - 1 : end]
                chunks.append(self._make_chunk(rel_path, language, role, start, end, body_lines, None, [], hints))
                if end >= len(lines):
                    break
                start = max(start + max_lines - overlap, start + 1)
        return chunks

    def _make_chunk(
        self,
        rel_path: str,
        language: str,
        role: str,
        start: int,
        end: int,
        body_lines: list[str],
        symbol: Symbol | None,
        neighborhood: list[str],
        hints: list[str],
    ) -> Chunk:
        content = "\n".join(body_lines).strip()
        search_parts = [rel_path, language, role, content]
        if symbol is not None:
            search_parts.extend([symbol.name, symbol.kind, symbol.signature, symbol.doc_hint])
        search_parts.extend(neighborhood)
        search_parts.extend(hints)
        return Chunk(
            file_path=rel_path,
            language=language,
            role=role,
            start_line=start,
            end_line=end,
            content=content,
            search_text=" ".join(part for part in search_parts if part),
            symbol_name=symbol.name if symbol else None,
            symbol_kind=symbol.kind if symbol else None,
            neighborhood=neighborhood,
            hints=hints,
        )
