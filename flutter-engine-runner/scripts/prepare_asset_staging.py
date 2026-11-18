#!/usr/bin/env python3
"""Create the one project-scoped image/download staging directory.

All generated, downloaded, browser-exported and transcoded image bytes must
land below this directory before they are copied into the Flutter project.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SUBDIRECTORIES = {
    "logo_candidates": "logo-candidates",
    "backgrounds": "backgrounds",
    "content": "content",
    "exports": "exports",
}


def sanitize_project_name(project_name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", project_name.strip())
    value = re.sub(r"_+", "_", value).strip("._-")
    return value or "project-assets"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(project_root: Path, project_name: str, downloads_root: Path | None = None) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    downloads_root = (downloads_root or Path.home() / "Downloads").expanduser().resolve()
    if not project_name.strip():
        raise ValueError("project_name must be non-empty")
    if project_root == downloads_root or project_root in downloads_root.parents:
        raise ValueError("project root cannot be the public Downloads root or one of its children")
    downloads_root.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_project_name(project_name)
    staging_root = downloads_root / sanitized
    staging_root.mkdir(exist_ok=True)
    if staging_root.is_symlink():
        raise ValueError("project staging root cannot be a symlink")
    for name in SUBDIRECTORIES.values():
        (staging_root / name).mkdir(exist_ok=True)
    record = {
        "schema_version": 1,
        "project_name": project_name,
        "sanitized_project_name": sanitized,
        "project_root": str(project_root),
        "downloads_root": str(downloads_root),
        "staging_root": str(staging_root),
        "managed_subdirectories": SUBDIRECTORIES,
        "status": "active",
    }
    _write_json(project_root / ".codex-work/asset-staging.json", record)
    return {**record, "status": "Prepared", "manifest_status": record["status"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--downloads-root", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    try:
        report = prepare(args.project_root, args.project_name, args.downloads_root)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "Failed", "errors": [str(error)]}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
