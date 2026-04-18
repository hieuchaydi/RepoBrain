from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path

ROOT_TEMP_PATTERNS = (
    ".pytest_tmp*",
    "pytest_tmp*",
    "pytest_work*",
    "pytest-cache-files-*",
    ".tmp-build",
    ".tmp-test-runs",
    "tmp*",
    "dist",
    "htmlcov",
)
RECURSIVE_TEMP_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".pyre",
    ".hypothesis",
    ".npm-cache",
}
RECURSIVE_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
}
TEMP_FILES = {
    ".coverage",
    "coverage.xml",
}


def cleanup_demo_artifacts(
    project_root: Path,
    *,
    dry_run: bool = False,
    include_dist: bool = True,
    include_state: bool = False,
) -> dict[str, object]:
    root = project_root.expanduser().resolve()
    web_dist = root / "webapp" / "dist"
    root_state = root / ".repobrain"
    removed: list[str] = []
    preserved: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    candidates = _collect_candidates(root, include_dist=include_dist, include_state=include_state)

    if not include_state and root_state.exists():
        preserved.append({"path": str(root_state), "reason": "preserved active workspace state"})
    if web_dist.exists():
        preserved.append({"path": str(web_dist), "reason": "preserved built frontend required by serve-web"})

    for path in candidates:
        try:
            if not path.exists():
                continue
            if dry_run:
                removed.append(str(path))
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(str(path))
        except FileNotFoundError:
            continue
        except Exception as exc:  # pragma: no cover - platform-specific filesystem failures
            errors.append({"path": str(path), "error": str(exc)})

    status = "warn" if errors else "pass"
    return {
        "kind": "demo_clean",
        "project_root": str(root),
        "status": status,
        "dry_run": dry_run,
        "removed_count": len(removed),
        "preserved_count": len(preserved),
        "error_count": len(errors),
        "removed": removed,
        "preserved": preserved,
        "errors": errors,
    }


def _collect_candidates(root: Path, *, include_dist: bool, include_state: bool) -> list[Path]:
    candidates: set[Path] = set()

    for child in root.iterdir():
        if child.name == "webapp":
            continue
        if child.name == ".repobrain":
            if include_state:
                candidates.add(child.resolve())
            continue
        if child.name == "dist" and not include_dist:
            continue
        if any(fnmatch.fnmatch(child.name, pattern) for pattern in ROOT_TEMP_PATTERNS):
            candidates.add(child.resolve())

    for filename in TEMP_FILES:
        file_path = root / filename
        if file_path.exists():
            candidates.add(file_path.resolve())

    walk_errors: list[OSError] = []

    def onerror(exc: OSError) -> None:
        walk_errors.append(exc)

    for current_root, dirnames, filenames in os.walk(root, topdown=True, onerror=onerror):
        current_path = Path(current_root)
        next_dirs: list[str] = []
        for dirname in dirnames:
            path = current_path / dirname
            if path == root / "webapp" / "dist":
                continue
            if dirname in RECURSIVE_SKIP_DIRS:
                continue
            if dirname in RECURSIVE_TEMP_DIRS:
                candidates.add(path.resolve())
                continue
            if dirname == ".repobrain":
                if path == root / ".repobrain" and not include_state:
                    continue
                candidates.add(path.resolve())
                continue
            next_dirs.append(dirname)
        dirnames[:] = next_dirs

        for filename in filenames:
            if filename in TEMP_FILES:
                candidates.add((current_path / filename).resolve())

    for error in walk_errors:
        filename = getattr(error, "filename", None)
        if filename:
            candidates.add(Path(filename).resolve())

    return _prune_nested(candidates)


def _prune_nested(candidates: set[Path]) -> list[Path]:
    selected: list[Path] = []
    for path in sorted(candidates, key=lambda item: (len(item.parts), str(item))):
        if any(parent == path or parent in path.parents for parent in selected):
            continue
        selected.append(path)
    return selected
