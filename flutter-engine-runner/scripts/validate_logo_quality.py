#!/usr/bin/env python3
"""Validate Logo candidate review evidence and final RGB PNG identity."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STYLES = {"reality-inspired", "hand-drawn", "oil-painting", "artistic-expression"}
REQUIRED_CHECKS = {
    "proportion",
    "perspective",
    "contact_and_overlap",
    "shadow_and_light_direction",
    "texture_consistency",
    "object_boundaries",
}
PASS_VALUES = {"pass", "passed", "none", "low"}
STARGATE_PROVIDER_URL = "http://stargate.local:3100/"
SERIAL_QUEUE_POLICIES = {"serialize", "serial", "single-flight", "exclusive-lock"}


def _png_info(path: Path) -> tuple[tuple[int, int, int] | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as error:
        return None, str(error)
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None, "not a valid PNG signature"
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return (width, height, color_type), f"bit_depth={bit_depth} color_type={color_type}"


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.astimezone(timezone.utc) if result.tzinfo else None


def _inside(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = root / value
    # Check the lexical path before resolving it.  ``Path.resolve()`` removes a
    # symlink, so checking only the resolved result would allow a symlinked
    # candidate or staging directory to masquerade as an in-project file.
    cursor = candidate
    while cursor != root and cursor != cursor.parent:
        if cursor.is_symlink():
            return None
        cursor = cursor.parent
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _resolve_generation_staging(root: Path, value: Any) -> Path | None:
    """Resolve a project staging root under the managed Downloads directory.

    Older fixtures used an in-project ``staging/`` directory.  New projects use
    the required external ``/Users/admin/Downloads/<project-name>/`` directory;
    both are accepted so existing records remain readable while new records are
    checked against the single managed Downloads folder.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        return _inside(root, value)
    candidate = candidate.resolve()
    if candidate == root or candidate.is_symlink():
        return None
    if candidate.name == "Downloads" or candidate.parent.name != "Downloads":
        return None
    try:
        candidate.relative_to(candidate.parent)
    except ValueError:
        return None
    return candidate


def _resolve_output_path(root: Path, staging_root: Path | None, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = Path(value).expanduser()
    if raw.is_absolute():
        candidate = raw.resolve()
    elif staging_root is not None and staging_root.is_absolute() and not _inside(root, value):
        candidate = (staging_root / value).resolve()
    else:
        candidate = _inside(root, value)
    if candidate is None or candidate.is_symlink():
        return None
    return candidate


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_generation(root: Path, data: dict[str, Any], errors: list[str]) -> tuple[dict[str, Any] | None, Path | None, set[str]]:
    """Validate the image-generation session and return its identity and staging root.

    A successful visual review is not enough to prove that an image belongs to this
    project.  The manifest must also show that the result came from an exclusive,
    serialized Stargate task in this project's own staging directory.
    """
    generation = data.get("generation")
    if not isinstance(generation, dict):
        errors.append("generation must be an object")
        return None, None, set()

    required = (
        "project_id",
        "provider",
        "session_id",
        "process_id",
        "exclusive",
        "queue_policy",
        "status",
        "staging_root",
        "lock_events",
        "foreign_outputs",
    )
    for field in required:
        if field not in generation:
            errors.append(f"generation.{field} is required")

    project_id = generation.get("project_id")
    provider = generation.get("provider")
    provider_url = generation.get("provider_url", provider)
    session_id = generation.get("session_id")
    process_id = generation.get("process_id")
    if not _non_empty_string(project_id) or project_id in {".", ".."} or "/" in project_id or "\\" in project_id:
        errors.append("generation.project_id must be a safe non-empty project identifier")
    if not _non_empty_string(provider):
        errors.append("generation.provider must be non-empty")
    if provider_url != STARGATE_PROVIDER_URL:
        errors.append(
            f"generation.provider_url must be {STARGATE_PROVIDER_URL}"
        )
    for field, value in (("session_id", session_id), ("process_id", process_id)):
        if not _non_empty_string(value):
            errors.append(f"generation.{field} must be non-empty")
    if generation.get("exclusive") is not True:
        errors.append("generation.exclusive must be true for an isolated image task")
    if generation.get("queue_policy") not in SERIAL_QUEUE_POLICIES:
        errors.append("generation.queue_policy must declare a serialized/exclusive policy")
    if generation.get("status") != "completed":
        errors.append("generation.status must be completed")

    staging = _resolve_generation_staging(root, generation.get("staging_root"))
    if staging is None or not staging.is_dir() or staging.is_symlink():
        errors.append("generation.staging_root must point to a regular project staging directory")
        staging = None
    elif staging.name != project_id:
        errors.append("generation.staging_root must end with the current project_id")

    lock_events = generation.get("lock_events")
    if not isinstance(lock_events, list) or not lock_events:
        errors.append("generation.lock_events must record lock acquisition and release")
    else:
        events: list[str] = []
        for index, event in enumerate(lock_events):
            if not isinstance(event, dict) or not _non_empty_string(event.get("event")):
                errors.append(f"generation.lock_events[{index}] must include an event name")
                continue
            events.append(event["event"])
            if _parse_timestamp(event.get("at")) is None:
                errors.append(f"generation.lock_events[{index}].at must be timezone-aware ISO-8601")
        if "acquired" not in events:
            errors.append("generation.lock_events must include acquired")
        if "released" not in events:
            errors.append("generation.lock_events must include released")
        if "acquired" in events and "released" in events and events.index("acquired") > events.index("released"):
            errors.append("generation.lock_events must release after acquisition")

    foreign_outputs = generation.get("foreign_outputs")
    if not isinstance(foreign_outputs, list):
        errors.append("generation.foreign_outputs must be a list")
    elif foreign_outputs:
        errors.append("generation.foreign_outputs must be empty; foreign results are blocked")

    identity = {
        "project_id": project_id,
        "provider_url": provider_url,
        "session_id": session_id,
        "process_id": process_id,
    }
    return identity, staging, set()


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / ".codex-work/logo-review.json"
    if not manifest_path.is_file():
        return {"status": "Not verified", "errors": ["missing .codex-work/logo-review.json"]}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return {"status": "Failed", "errors": [f"invalid Logo review JSON: {error}"]}
    if not isinstance(data, dict):
        return {"status": "Failed", "errors": ["Logo review must be an object"]}
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(data.get("run_id"), str) or not data["run_id"].strip():
        errors.append("run_id must be non-empty")
    generated = _parse_timestamp(data.get("generated_at"))
    if generated is None:
        errors.append("generated_at must be a timezone-aware ISO-8601 timestamp")
    elif generated > datetime.now(timezone.utc):
        errors.append("generated_at is in the future")
    generation_identity, staging_root, _ = _validate_generation(root, data, errors)
    final_path = data.get("final_asset")
    final = _inside(root, final_path)
    if final is None or not final.is_file() or final.is_symlink():
        errors.append("final_asset must point to a regular in-project file")
    else:
        info, detail = _png_info(final)
        if info is None:
            errors.append(f"final_asset: {detail}")
        else:
            width, height, color_type = info
            if (width, height) != (1024, 1024):
                errors.append(f"final_asset must be 1024x1024, got {width}x{height}")
            if color_type in {4, 6}:
                errors.append("final_asset must be RGB/RGBA-free; alpha channel is forbidden")
            elif color_type != 2:
                errors.append(f"final_asset must use RGB color type 2, got {color_type}")
        expected_hash = data.get("final_sha256")
        actual_hash = hashlib.sha256(final.read_bytes()).hexdigest()
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            errors.append("final_sha256 must be 64 hexadecimal characters")
        elif expected_hash.lower() != actual_hash:
            errors.append("final_sha256 does not match final_asset")

    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        candidates = []
    if len(candidates) != 12:
        errors.append(f"exactly 12 Logo candidates are required, found {len(candidates)}")
    counts = {style: 0 for style in STYLES}
    ids: set[str] = set()
    selected = data.get("selected_candidate")
    selected_row: dict[str, Any] | None = None
    generation_task_ids: set[str] = set()
    output_paths: set[Path] = set()
    for index, row in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip() or row_id in ids:
            errors.append(f"{prefix}.id must be unique and non-empty")
        elif row_id not in ids:
            ids.add(row_id)
        style = row.get("style")
        if style not in STYLES:
            errors.append(f"{prefix}.style is invalid")
        else:
            counts[style] += 1
        candidate_path = _inside(root, row.get("path"))
        if candidate_path is None or not candidate_path.is_file() or candidate_path.is_symlink():
            errors.append(f"{prefix}.path must point to a regular in-project file")
        else:
            actual_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
            candidate_sha256 = row.get("sha256")
            if not isinstance(candidate_sha256, str) or candidate_sha256.lower() != actual_hash:
                errors.append(f"{prefix}.sha256 does not match candidate file")
        for field in (
            "output_path",
            "generation_task_id",
            "project_id",
            "source_project_id",
            "session_id",
            "process_id",
            "generation_status",
            "result_binding",
        ):
            if field not in row:
                errors.append(f"{prefix}.{field} is required for generation provenance")
        task_id = row.get("generation_task_id")
        if not _non_empty_string(task_id):
            errors.append(f"{prefix}.generation_task_id must be non-empty")
        elif task_id in generation_task_ids:
            errors.append(f"{prefix}.generation_task_id must be unique")
        else:
            generation_task_ids.add(task_id)
        if generation_identity is not None:
            if row.get("project_id") != generation_identity["project_id"]:
                errors.append(f"{prefix}.project_id must match generation.project_id")
            if row.get("source_project_id") != generation_identity["project_id"]:
                errors.append(f"{prefix}.source_project_id must match the current project")
            if row.get("session_id") != generation_identity["session_id"]:
                errors.append(f"{prefix}.session_id must match generation.session_id")
            if row.get("process_id") != generation_identity["process_id"]:
                errors.append(f"{prefix}.process_id must match generation.process_id")
        if row.get("generation_status") != "completed":
            errors.append(f"{prefix}.generation_status must be completed")
        if row.get("result_binding") != "task_result":
            errors.append(f"{prefix}.result_binding must be task_result")
        output_path = _resolve_output_path(root, staging_root, row.get("output_path"))
        if staging_root is None or output_path is None:
            errors.append(f"{prefix}.output_path must point inside generation.staging_root")
        else:
            try:
                output_path.relative_to(staging_root)
            except ValueError:
                errors.append(f"{prefix}.output_path must be inside generation.staging_root")
            else:
                if output_path == staging_root:
                    errors.append(f"{prefix}.output_path must point to a file, not staging_root")
                elif not output_path.is_file() or output_path.is_symlink():
                    errors.append(f"{prefix}.output_path must point to a regular task-result file")
                elif output_path in output_paths:
                    errors.append(f"{prefix}.output_path must be unique")
                else:
                    output_paths.add(output_path)
        if row.get("status") != "Passed":
            errors.append(f"{prefix}.status must be Passed before selection")
        if row.get("reviewed") is not True:
            errors.append(f"{prefix}.reviewed must be true")
        if _parse_timestamp(row.get("reviewed_at")) is None:
            errors.append(f"{prefix}.reviewed_at must be timezone-aware ISO-8601")
        if row.get("ai_style_risk") not in {"low", "none"}:
            errors.append(f"{prefix}.ai_style_risk must be low or none")
        for field in ("reality_logic", "object_integrity", "material_lighting"):
            if row.get(field) not in {"pass", "passed"}:
                errors.append(f"{prefix}.{field} must be pass")
        if row.get("text_artifacts") not in {"none", "absent"}:
            errors.append(f"{prefix}.text_artifacts must report none/absent")
        checks = row.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"{prefix}.checks must be an object")
        else:
            missing = sorted(REQUIRED_CHECKS - set(checks))
            if missing:
                errors.append(f"{prefix}.checks missing: {', '.join(missing)}")
            for check in REQUIRED_CHECKS:
                if checks.get(check) not in {"pass", "passed"}:
                    errors.append(f"{prefix}.checks.{check} must be pass")
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            errors.append(f"{prefix}.notes must document the visual review")
        if not isinstance(row.get("evidence"), list) or not row["evidence"]:
            errors.append(f"{prefix}.evidence must be non-empty")
        if row_id == selected:
            selected_row = row
    for style, count in counts.items():
        if count != 3:
            errors.append(f"style {style} requires exactly 3 candidates, found {count}")
    if selected_row is None:
        errors.append("selected_candidate must identify one reviewed candidate")
    else:
        if selected_row.get("ai_style_risk") not in {"low", "none"}:
            errors.append("selected candidate has excessive AI-style risk")
        if selected_row.get("reality_logic") not in {"pass", "passed"}:
            errors.append("selected candidate failed reality-logic review")
        if selected_row.get("object_integrity") not in {"pass", "passed"}:
            errors.append("selected candidate failed object-integrity review")
    return {
        "status": "Failed" if errors else "Passed",
        "errors": errors,
        "candidate_count": len(candidates),
        "style_counts": counts,
        "selected_candidate": selected,
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
