#!/usr/bin/env python3
"""Reject image/download files outside the project's single Downloads folder."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".heic", ".heif", ".bmp", ".tif", ".tiff"}
SUBDIRECTORIES = {"logo-candidates", "backgrounds", "content", "exports"}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_symlink_on_path(path: Path, stop: Path) -> bool:
    cursor = path
    while cursor != stop and cursor != cursor.parent:
        if cursor.is_symlink():
            return True
        cursor = cursor.parent
    return False


def validate(project_root: Path) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    manifest_path = project_root / ".codex-work/asset-staging.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {"status": "Not verified", "errors": ["missing .codex-work/asset-staging.json"]}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return {"status": "Failed", "errors": [f"invalid asset staging JSON: {error}"]}
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"status": "Failed", "errors": ["asset staging manifest must be an object"]}
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    project_path = Path(data.get("project_root", "")).expanduser().resolve() if isinstance(data.get("project_root"), str) else None
    downloads_root = Path(data.get("downloads_root", "")).expanduser().resolve() if isinstance(data.get("downloads_root"), str) else None
    staging_root = Path(data.get("staging_root", "")).expanduser().resolve() if isinstance(data.get("staging_root"), str) else None
    if project_path != project_root:
        errors.append("manifest project_root does not match the checked project")
    if downloads_root is None or downloads_root.name != "Downloads":
        errors.append("downloads_root must be /Users/admin/Downloads or the user's Downloads directory")
    if staging_root is None:
        errors.append("staging_root must be inside downloads_root")
    elif downloads_root is None or not _inside(staging_root, downloads_root):
        errors.append("staging_root must be inside downloads_root")
    if staging_root and _inside(staging_root, project_root):
        errors.append("staging_root cannot be inside the project")
    if staging_root and _is_symlink_on_path(staging_root, downloads_root or staging_root.parent):
        errors.append("staging_root cannot use a symlink path")
    if staging_root is None or not staging_root.is_dir() or staging_root.is_symlink():
        errors.append("staging_root must be an existing regular directory")
    managed = data.get("managed_subdirectories")
    if not isinstance(managed, dict) or set(managed.values()) != SUBDIRECTORIES:
        errors.append("managed_subdirectories must contain logo-candidates, backgrounds, content and exports")
    else:
        for name in SUBDIRECTORIES:
            child = staging_root / name if staging_root else None
            if child is None or not child.is_dir() or child.is_symlink():
                errors.append(f"managed staging directory missing or invalid: {name}")

    image_files: list[str] = []
    if downloads_root and downloads_root.is_dir():
        for path in downloads_root.rglob("*"):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            relative = path.relative_to(downloads_root)
            image_files.append(relative.as_posix())
            if staging_root is None or not _inside(path.resolve(), staging_root):
                if len(relative.parts) == 1:
                    errors.append(f"public Downloads root contains image: {relative.as_posix()}")
                else:
                    errors.append(f"image is outside this project's staging root: {relative.as_posix()}")
            elif relative.parts[1] not in SUBDIRECTORIES:
                errors.append(f"image is in an unmanaged staging directory: {relative.as_posix()}")
            if _is_symlink_on_path(path, downloads_root):
                errors.append(f"image path uses a symlink: {relative.as_posix()}")
    return {
        "status": "Failed" if errors else "Passed",
        "errors": errors,
        "staging_root": str(staging_root) if staging_root else None,
        "image_file_count": len(image_files),
        "image_files": image_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.project_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"Passed": 0, "Failed": 1, "Not verified": 2}.get(report["status"], 1)


if __name__ == "__main__":
    sys.exit(main())
