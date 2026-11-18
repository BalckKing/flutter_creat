#!/usr/bin/env python3
"""Validate the machine-readable `.codex-work` record and evidence contract."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any

STATUSES = {"Planned", "In progress", "Passed", "Failed", "Blocked", "Not verified"}
REQUIRED = {"schema_version", "run_id", "project_root", "bundle_id", "build_id", "device", "udid", "recorded_at", "status", "evidence", "next_action"}
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")

def parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} is not valid ISO-8601: {value!r}") from error
    if result.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return result.astimezone(timezone.utc)

def validate(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    root = root.resolve()
    record_dir = root / ".codex-work" / "records"
    if not record_dir.is_dir():
        return {"status": "Not verified", "errors": ["missing .codex-work/records directory; runtime evidence is not available"], "records": []}
    if record_dir.is_symlink():
        return {"status": "Failed", "errors": [".codex-work/records must not be a symbolic link"], "records": []}
    files = sorted(record_dir.glob("*.json"))
    if not files:
        return {"status": "Not verified", "errors": [".codex-work/records contains no JSON records"], "records": []}
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    errors: list[str] = []
    reports: list[dict[str, Any]] = []
    for path in files:
        label = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"{label}: invalid JSON: {error}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{label}: record must be an object")
            continue
        missing = sorted(REQUIRED - set(data))
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
        if data.get("schema_version") != 1:
            errors.append(f"{label}: schema_version must be 1")
        for field in ("run_id", "project_root", "bundle_id", "build_id", "device", "udid", "next_action"):
            if field in data and (not isinstance(data[field], str) or not data[field].strip()):
                errors.append(f"{label}: {field} must be a non-empty string")
        status = data.get("status")
        if status not in STATUSES:
            errors.append(f"{label}: status must be one of {sorted(STATUSES)}")
        try:
            recorded = parse_time(data.get("recorded_at"), f"{label}.recorded_at")
            if recorded > now + timedelta(minutes=5):
                errors.append(f"{label}: recorded_at is in the future")
        except ValueError as error:
            errors.append(str(error)); recorded = None
        window = data.get("freshness_window_hours", 24)
        if not isinstance(window, (int, float)) or window <= 0:
            errors.append(f"{label}: freshness_window_hours must be positive"); window = 24
        evidence = data.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{label}: evidence must be a list"); evidence = []
        device = data.get("device") if isinstance(data.get("device"), str) else ""
        udid = data.get("udid") if isinstance(data.get("udid"), str) else ""
        build_id = data.get("build_id") if isinstance(data.get("build_id"), str) else ""
        evidence_reports = []
        for index, item in enumerate(evidence):
            prefix = f"{label}.evidence[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix}: evidence item must be an object"); continue
            for field in ("path", "sha256", "captured_at", "source", "kind"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"{prefix}: missing non-empty {field}")
            rel = item.get("path")
            evidence_path = None
            if isinstance(rel, str) and rel:
                evidence_path = (root / rel).resolve()
                try: evidence_path.relative_to(root)
                except ValueError:
                    errors.append(f"{prefix}: evidence path escapes project root"); evidence_path = None
                if evidence_path and not evidence_path.is_file():
                    errors.append(f"{prefix}: evidence file does not exist: {rel}")
            if not isinstance(item.get("sha256"), str) or not SHA256.fullmatch(item.get("sha256", "")):
                errors.append(f"{prefix}: sha256 must be 64 hexadecimal characters")
            elif evidence_path and evidence_path.is_file():
                digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                if digest.lower() != item["sha256"].lower(): errors.append(f"{prefix}: sha256 does not match {rel}")
            try:
                captured = parse_time(item.get("captured_at"), f"{prefix}.captured_at")
                if captured > now + timedelta(minutes=5): errors.append(f"{prefix}: captured_at is in the future")
                if recorded and captured > recorded + timedelta(minutes=5): errors.append(f"{prefix}: captured_at is after recorded_at")
                if now - captured > timedelta(hours=float(window)): errors.append(f"{prefix}: evidence is older than freshness_window_hours")
            except ValueError as error: errors.append(str(error))
            if item.get("kind") in {"screenshot", "recording", "log", "artifact"}:
                if item.get("build_id") != build_id: errors.append(f"{prefix}: runtime evidence build_id must match record build_id")
                if item.get("device") != device or item.get("udid") != udid: errors.append(f"{prefix}: runtime evidence device and udid must match the record")
            evidence_reports.append({"path": rel, "kind": item.get("kind"), "source": item.get("source")})
        if status == "Passed" and not evidence: errors.append(f"{label}: Passed records require at least one evidence item")
        reports.append({"path": label, "run_id": data.get("run_id"), "status": status, "evidence": evidence_reports})
    return {"status": "Failed" if errors else "Passed", "errors": errors, "records": reports}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.project_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"Passed": 0, "Failed": 1, "Not verified": 2}.get(report["status"], 1)

if __name__ == "__main__": sys.exit(main())
