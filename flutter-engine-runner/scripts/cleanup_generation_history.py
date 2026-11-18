#!/usr/bin/env python3
"""Validate the post-download deletion record for the image-generation site.

This script deliberately does not guess a Stargate API or delete arbitrary
history.  The exact task IDs must first be deleted through the provider's own
UI or a documented provider action, then the observed result is recorded here.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROVIDER_URL = "http://stargate.local:3100/"


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc)


def _strings(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        return None
    return value


def validate(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    manifest_path = root / ".codex-work/generation-cleanup.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {"status": "Not verified", "errors": ["missing .codex-work/generation-cleanup.json"]}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return {"status": "Failed", "errors": [f"invalid generation cleanup JSON: {error}"]}
    if not isinstance(data, dict):
        return {"status": "Failed", "errors": ["generation cleanup manifest must be an object"]}
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("provider_url") != PROVIDER_URL:
        errors.append(f"provider_url must be {PROVIDER_URL}")
    if data.get("cleanup_required") is not True:
        errors.append("cleanup_required must be true")
    if data.get("trigger") != "after_download":
        errors.append("trigger must be after_download")
    if data.get("download_status") != "completed":
        errors.append("download_status must be completed before history deletion")
    task_ids = _strings(data.get("task_ids"))
    if task_ids is None or len(set(task_ids)) != len(task_ids):
        errors.append("task_ids must be a non-empty list of unique task IDs")
        task_ids = []
    downloaded = _strings(data.get("downloaded_asset_paths"))
    if downloaded is None:
        errors.append("downloaded_asset_paths must list downloaded files")
        downloaded = []
    if data.get("status") != "completed":
        errors.append("status must be completed only after exact history deletion is observed")
    deleted = _strings(data.get("deleted_task_ids"))
    if deleted is None or set(deleted) != set(task_ids):
        errors.append("deleted_task_ids must exactly match task_ids")
        deleted = []
    if not _timestamp(data.get("deleted_at")):
        errors.append("deleted_at must be a timezone-aware timestamp in the past")
    evidence = _strings(data.get("evidence"))
    if evidence is None:
        errors.append("evidence must contain the provider history deletion result")
        evidence = []
    if data.get("executor") not in {"provider-ui", "documented-provider-action"}:
        errors.append("executor must identify the provider UI or a documented provider action")
    return {
        "status": "Failed" if errors else "Passed",
        "errors": errors,
        "provider_url": data.get("provider_url"),
        "task_count": len(task_ids),
        "downloaded_asset_count": len(downloaded),
        "deleted_task_count": len(deleted),
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
