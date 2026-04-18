from __future__ import annotations

import io
import json
import tarfile
import zipfile
from pathlib import Path

from repobrain.release import REQUIRED_FRONTEND_ASSETS, inspect_release_artifacts


def _write_release_project(root: Path) -> None:
    (root / "src" / "repobrain").mkdir(parents=True)
    (root / "webapp" / "dist").mkdir(parents=True)
    (root / "dist").mkdir()
    (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "repobrain"',
                'version = "0.5.0"',
            ]
        ),
        encoding="utf-8",
    )
    (root / "webapp" / "package.json").write_text(json.dumps({"version": "0.5.0"}), encoding="utf-8")
    for asset in REQUIRED_FRONTEND_ASSETS:
        (root / asset).write_text(f"asset: {asset}", encoding="utf-8")


def _write_artifacts(root: Path, include_assets: bool = True) -> None:
    wheel = root / "dist" / "repobrain-0.5.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("repobrain/__init__.py", '__version__ = "0.5.0"\n')
        if include_assets:
            for asset in REQUIRED_FRONTEND_ASSETS:
                archive.writestr(asset, "asset")

    sdist = root / "dist" / "repobrain-0.5.0.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        for asset in (REQUIRED_FRONTEND_ASSETS if include_assets else ("README.md",)):
            data = b"asset"
            info = tarfile.TarInfo(f"repobrain-0.5.0/{asset}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_release_check_passes_when_dist_artifacts_include_frontend_assets(tmp_path: Path) -> None:
    _write_release_project(tmp_path)
    _write_artifacts(tmp_path)

    payload = inspect_release_artifacts(tmp_path, require_dist=True)

    assert payload["status"] == "pass"
    assert payload["dist"]["wheel_count"] == 1
    assert payload["dist"]["sdist_count"] == 1
    assert all(check["status"] == "pass" for check in payload["checks"])


def test_release_check_fails_when_packaged_frontend_assets_are_missing(tmp_path: Path) -> None:
    _write_release_project(tmp_path)
    _write_artifacts(tmp_path, include_assets=False)

    payload = inspect_release_artifacts(tmp_path, require_dist=True)

    assert payload["status"] == "fail"
    package_check = next(check for check in payload["checks"] if check["name"] == "packaged frontend assets")
    assert package_check["status"] == "fail"
    assert "webapp/dist/index.html" in package_check["detail"]


def test_release_check_warns_for_missing_dist_until_artifacts_are_required(tmp_path: Path) -> None:
    _write_release_project(tmp_path)

    local_payload = inspect_release_artifacts(tmp_path)
    required_payload = inspect_release_artifacts(tmp_path, require_dist=True)

    assert local_payload["status"] == "warn"
    assert required_payload["status"] == "fail"
