#!/usr/bin/env python3
"""Validate resource, dependency, accessibility, resilience, and secret-scan evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUS = {"Passed", "Failed", "Blocked", "Not verified", "Not applicable"}
IMAGE_TYPES = {"image", "photo", "illustration", "logo", "background"}
REQUIRED_RESILIENCE = {
    "offline_cold_start",
    "permission_denied",
    "foreground_background",
    "clear_data_interrupted",
}
REQUIRED_ACCESSIBILITY = {"voiceover", "dynamic_type", "reduce_motion", "contrast"}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|access[_-]?token|auth[_-]?token|password)\b"
        r"\s*[:=]\s*[\"'][^\"']{12,}[\"']"
    ),
)
SCAN_SUFFIXES = {
    ".dart",
    ".swift",
    ".m",
    ".mm",
    ".h",
    ".plist",
    ".pbxproj",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
    ".kt",
    ".java",
    ".gradle",
    ".properties",
    ".sh",
    ".command",
    ".js",
    ".ts",
    ".html",
    ".env",
}
SKIP_PARTS = {".git", ".codex-work", "build", ".dart_tool", "Pods", ".symlinks"}


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _resolve_inside(root: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _check_image_signature(path: Path) -> bool:
    try:
        header = path.read_bytes()[:16]
    except OSError:
        return False
    return (
        header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith(b"\xff\xd8\xff")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    )


def _scan_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"secret-like value in {relative.as_posix()} ({pattern.pattern})")
                break
    return findings


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    path = root / ".codex-work" / "quality-matrix.json"
    if not path.is_file():
        return {
            "status": "Not verified",
            "errors": ["missing .codex-work/quality-matrix.json"],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return {"status": "Failed", "errors": [f"invalid quality matrix JSON: {error}"]}
    if not isinstance(data, dict):
        return {"status": "Failed", "errors": ["quality matrix must be an object"]}

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not _non_empty(data.get("run_id")):
        errors.append("run_id must be a non-empty string")

    project_type = data.get("project_type")
    if project_type in {"game", "non_game", "mixed"}:
        final_visual = data.get("final_visual_product")
        if not isinstance(final_visual, dict):
            errors.append("final_visual_product quality section is required for game, non_game, and mixed projects")
        else:
            if final_visual.get("contract") != ".codex-work/final-visual-product.json":
                errors.append("final_visual_product.contract must point to .codex-work/final-visual-product.json")
            if final_visual.get("status") not in ALLOWED_STATUS:
                errors.append("final_visual_product.status is invalid or missing")
            for field in ("refinement_evidence", "current_iphone_evidence"):
                values = final_visual.get(field)
                if not isinstance(values, list) or not values:
                    errors.append(f"final_visual_product.{field} must be a non-empty list")

    resources = data.get("resources")
    if not isinstance(resources, list) or not resources:
        errors.append("resources must be a non-empty list")
        resources = []
    seen_resources: set[str] = set()
    for index, row in enumerate(resources):
        prefix = f"resources[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = (
            "path",
            "asset_type",
            "role",
            "source_kind",
            "source",
            "license",
            "consumer",
            "display_position",
            "sha256",
            "bytes",
            "max_bytes",
            "status",
        )
        for field in required:
            if field not in row:
                errors.append(f"{prefix} missing {field}")
        relative = row.get("path")
        if relative in seen_resources:
            errors.append(f"duplicate resource path: {relative}")
        seen_resources.add(relative)
        file_path = _resolve_inside(root, relative)
        if file_path is None:
            errors.append(f"{prefix}.path must stay inside project root")
        elif not file_path.is_file() or file_path.is_symlink():
            errors.append(f"{prefix}.path must point to a regular file: {relative}")
        else:
            actual_bytes = file_path.stat().st_size
            if row.get("bytes") != actual_bytes:
                errors.append(f"{prefix}.bytes does not match the file")
            expected_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if row.get("sha256", "").lower() != expected_hash:
                errors.append(f"{prefix}.sha256 does not match the file")
            if row.get("asset_type") in IMAGE_TYPES and not _check_image_signature(file_path):
                errors.append(f"{prefix} image has an unknown or invalid signature")
        if row.get("asset_type") in IMAGE_TYPES:
            max_bytes = row.get("max_bytes")
            if not isinstance(max_bytes, int) or max_bytes <= 0 or max_bytes > 262144:
                errors.append(f"{prefix}.max_bytes must be a positive image limit <= 262144")
            elif file_path and file_path.is_file() and file_path.stat().st_size > max_bytes:
                errors.append(f"{prefix} exceeds max_bytes")
        for field in ("role", "source_kind", "source", "license", "consumer", "display_position"):
            if not _non_empty(row.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        if row.get("status") not in ALLOWED_STATUS:
            errors.append(f"{prefix}.status is invalid")
        if row.get("status") == "Passed" and not isinstance(row.get("visual_review"), dict):
            errors.append(f"{prefix}.visual_review is required for Passed resources")

    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("dependencies must be a list")
        dependencies = []
    for index, row in enumerate(dependencies):
        prefix = f"dependencies[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("name", "version", "license", "source", "consumer"):
            if not _non_empty(row.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        if str(row.get("consumer", "")).strip().lower() in {
            "package",
            "pubspec",
            "dependency",
            "installed",
        }:
            errors.append(f"{prefix}.consumer must identify a real page/service consumer")

    accessibility = data.get("accessibility")
    if not isinstance(accessibility, list) or not accessibility:
        errors.append("accessibility must be a non-empty list")
        accessibility = []
    for index, row in enumerate(accessibility):
        prefix = f"accessibility[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not _non_empty(row.get("surface")):
            errors.append(f"{prefix}.surface must be non-empty")
        for field in REQUIRED_ACCESSIBILITY:
            if row.get(field) not in ALLOWED_STATUS:
                errors.append(f"{prefix}.{field} is invalid or missing")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be non-empty")

    resilience = data.get("resilience")
    if not isinstance(resilience, list):
        errors.append("resilience must be a list")
        resilience = []
    scenarios = set()
    for index, row in enumerate(resilience):
        prefix = f"resilience[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        scenario = row.get("scenario")
        if scenario in scenarios:
            errors.append(f"duplicate resilience scenario: {scenario}")
        scenarios.add(scenario)
        for field in ("scenario", "expected", "observed"):
            if not _non_empty(row.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        if row.get("status") not in ALLOWED_STATUS:
            errors.append(f"{prefix}.status is invalid")
        if not isinstance(row.get("evidence"), list) or not row.get("evidence"):
            errors.append(f"{prefix}.evidence must be non-empty")
    missing_scenarios = sorted(REQUIRED_RESILIENCE - scenarios)
    if missing_scenarios:
        errors.append("missing resilience scenarios: " + ", ".join(missing_scenarios))

    security = data.get("security")
    if not isinstance(security, dict):
        errors.append("security must be an object")
    else:
        if security.get("status") not in ALLOWED_STATUS:
            errors.append("security.status is invalid or missing")
        if not isinstance(security.get("evidence"), list) or not security.get("evidence"):
            errors.append("security.evidence must be non-empty")
    secret_findings = _scan_secrets(root)
    errors.extend(secret_findings)

    return {
        "status": "Failed" if errors else "Passed",
        "errors": errors,
        "resource_count": len(resources),
        "dependency_count": len(dependencies),
        "accessibility_surface_count": len(accessibility),
        "resilience_scenarios": sorted(scenarios),
        "secret_findings": secret_findings,
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
