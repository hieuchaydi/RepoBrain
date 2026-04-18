from __future__ import annotations

import json
import tarfile
import tomllib
import zipfile
from pathlib import Path
from typing import Any

from repobrain import __version__


REQUIRED_FRONTEND_ASSETS = (
    "webapp/dist/index.html",
    "webapp/dist/app.js",
    "webapp/dist/app.css",
)


def inspect_release_artifacts(project_root: str | Path, require_dist: bool = False) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    checks: list[dict[str, object]] = []

    pyproject_version = _pyproject_version(root)
    webapp_version = _webapp_version(root)
    version_values = [value for value in (pyproject_version, __version__, webapp_version) if value]
    versions_match = bool(version_values) and len(set(version_values)) == 1
    _add_check(
        checks,
        name="version alignment",
        status="pass" if versions_match else "fail",
        summary="Python package and webapp versions are aligned." if versions_match else "Release versions are not aligned.",
        detail=f"pyproject={pyproject_version or 'missing'} package={__version__} webapp={webapp_version or 'missing'}",
    )

    source_missing = _missing_source_assets(root)
    _add_check(
        checks,
        name="frontend build assets",
        status="pass" if not source_missing else "fail",
        summary="Built React frontend assets are present." if not source_missing else "Built React frontend assets are missing.",
        detail=", ".join(source_missing) if source_missing else "webapp/dist contains index.html, app.js, and app.css.",
    )

    artifacts = _dist_artifacts(root)
    wheel_count = sum(1 for artifact in artifacts if artifact.suffix == ".whl")
    sdist_count = sum(1 for artifact in artifacts if artifact.name.endswith(".tar.gz"))
    dist_ready = wheel_count > 0 and sdist_count > 0
    missing_dist_status = "fail" if require_dist else "warn"
    _add_check(
        checks,
        name="dist artifacts",
        status="pass" if dist_ready else missing_dist_status,
        summary="Wheel and sdist artifacts are available." if dist_ready else "Wheel and sdist artifacts are not both available.",
        detail=f"wheels={wheel_count} sdists={sdist_count}",
    )

    package_findings = _inspect_packaged_assets(artifacts)
    if package_findings:
        missing_packages = [
            f"{finding['artifact']}: {', '.join(finding['missing'])}"
            for finding in package_findings
            if finding["missing"]
        ]
        _add_check(
            checks,
            name="packaged frontend assets",
            status="fail" if missing_packages else "pass",
            summary="Packaged artifacts include the React frontend assets."
            if not missing_packages
            else "Some release artifacts are missing React frontend assets.",
            detail="; ".join(missing_packages) if missing_packages else f"validated={len(package_findings)} artifact(s)",
        )
    else:
        _add_check(
            checks,
            name="packaged frontend assets",
            status=missing_dist_status,
            summary="No release artifacts were available for package-content inspection.",
            detail="Run `python -m build`, then rerun this check.",
        )

    status = _overall_status(checks)
    return {
        "kind": "release_check",
        "project_root": str(root),
        "status": status,
        "require_dist": require_dist,
        "versions": {
            "pyproject": pyproject_version,
            "package": __version__,
            "webapp": webapp_version,
        },
        "dist": {
            "wheel_count": wheel_count,
            "sdist_count": sdist_count,
            "artifacts": [str(artifact.relative_to(root)) for artifact in artifacts],
        },
        "checks": checks,
    }


def _add_check(checks: list[dict[str, object]], *, name: str, status: str, summary: str, detail: str = "") -> None:
    checks.append(
        {
            "name": name,
            "status": status,
            "summary": summary,
            "detail": detail,
        }
    )


def _pyproject_version(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    version = project.get("version") if isinstance(project, dict) else None
    return str(version) if version else None


def _webapp_version(root: Path) -> str | None:
    package_json = root / "webapp" / "package.json"
    if not package_json.exists():
        return None
    data = json.loads(package_json.read_text(encoding="utf-8"))
    version = data.get("version")
    return str(version) if version else None


def _missing_source_assets(root: Path) -> list[str]:
    missing: list[str] = []
    for asset in REQUIRED_FRONTEND_ASSETS:
        path = root / asset
        if not path.exists() or path.stat().st_size <= 0:
            missing.append(asset)
    return missing


def _dist_artifacts(root: Path) -> list[Path]:
    dist_dir = root / "dist"
    if not dist_dir.exists():
        return []
    artifacts = [*dist_dir.glob("*.whl"), *dist_dir.glob("*.tar.gz")]
    return sorted(artifacts, key=lambda path: path.name)


def _inspect_packaged_assets(artifacts: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for artifact in artifacts:
        names = _artifact_names(artifact)
        missing = [
            required
            for required in REQUIRED_FRONTEND_ASSETS
            if not any(name == required or name.endswith(f"/{required}") for name in names)
        ]
        findings.append({"artifact": artifact.name, "missing": missing})
    return findings


def _artifact_names(artifact: Path) -> set[str]:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            return {name.replace("\\", "/") for name in archive.namelist()}
    if artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, "r:gz") as archive:
            return {member.name.replace("\\", "/") for member in archive.getmembers()}
    return set()


def _overall_status(checks: list[dict[str, object]]) -> str:
    statuses = {str(check.get("status")) for check in checks}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"
