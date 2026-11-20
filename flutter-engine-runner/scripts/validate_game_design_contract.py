#!/usr/bin/env python3
"""Validate the project-level game design contract.

The contract is the single source of truth for game visual design, mode/domain
coverage, scene assets, page routes, runtime evidence, and release state.  This
checker is intentionally source-only: it never launches Flutter or claims that
an iPhone run succeeded.  ``validate_project`` returns an actionable list of
blocking findings; an empty list means the static contract passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CONTRACT_PATH = Path(".codex-work/game-design-contract.json")
PROJECT_TYPES = {"game", "mixed"}
REQUIRED_DOMAIN_FIELDS = (
    "environment",
    "road_space",
    "vehicle_or_character",
    "entities",
    "rules",
    "results",
)
REQUIRED_STATUS_FIELDS = (
    "plan_status",
    "implementation_status",
    "verification_status",
    "release_status",
)
FORBIDDEN_WORDS = (
    "placeholder",
    "solid_color_block",
    "flat_rectangle",
    "static_screenshot",
    "flat color",
    "simple line",
    "color block",
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".heic"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".avi"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping(value: Any, label: str, findings: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        findings.append(f"{label} must be an object")
        return None
    return value


def _list(value: Any, label: str, findings: list[str], *, minimum: int = 1) -> list[Any]:
    if not isinstance(value, list):
        findings.append(f"{label} must be a list")
        return []
    if len(value) < minimum:
        findings.append(f"{label} must contain at least {minimum} item(s)")
    return value


def _safe_path(root: Path, value: Any, label: str, findings: list[str], *, allow_work: bool = False) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        findings.append(f"{label} must be a non-empty project-relative path")
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        findings.append(f"{label} must be project-relative: {value}")
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        findings.append(f"{label} escapes the project: {value}")
        return None
    if candidate.parts and candidate.parts[0] == ".codex-work" and not allow_work:
        findings.append(f"{label} must reference a shipped project asset, not .codex-work: {value}")
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            findings.append(f"{label} must not use a symlink: {value}")
            return None
    return resolved


def _file_path(root: Path, value: Any, label: str, findings: list[str], *, allow_work: bool = False) -> Path | None:
    path = _safe_path(root, value, label, findings, allow_work=allow_work)
    if path is None:
        return None
    if not path.is_file() or path.stat().st_size == 0:
        findings.append(f"{label} must point to a non-empty regular file: {value}")
        return None
    return path


def _require_text(obj: Mapping[str, Any], key: str, label: str, findings: list[str]) -> str | None:
    value = obj.get(key)
    if not _nonempty(value):
        findings.append(f"{label}.{key} must be a non-empty string")
        return None
    return value.strip()


def _numeric(obj: Mapping[str, Any], key: str, label: str, findings: list[str], *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        findings.append(f"{label}.{key} must be numeric")
        return None
    number = float(value)
    if minimum is not None and number < minimum:
        findings.append(f"{label}.{key} must be >= {minimum:g}")
    if maximum is not None and number > maximum:
        findings.append(f"{label}.{key} must be <= {maximum:g}")
    return number


def _normalise_visual_mode(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.casefold().replace("-", "").replace(" ", "")
    if "25d" in text or "2.5d" in text:
        return "2.5d"
    if "3d" in text:
        return "3d"
    return None


def _read_json(path: Path, label: str, findings: list[str]) -> Mapping[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        findings.append(f"invalid {label}: {error}")
        return None
    if not isinstance(value, Mapping):
        findings.append(f"{label} must contain a JSON object")
        return None
    return value


def _source_conflicts(root: Path, contract: Mapping[str, Any], source: Mapping[str, Any], visual: Mapping[str, Any], findings: list[str]) -> None:
    source_id = source.get("id")
    if source_id not in {CONTRACT_PATH.as_posix(), str(CONTRACT_PATH), "game-design-contract.json"}:
        findings.append("source_of_truth.id must identify .codex-work/game-design-contract.json")
    priority = source.get("priority")
    if not isinstance(priority, list) or not priority:
        findings.append("source_of_truth.priority must be a non-empty ordered list")
    elif not any(isinstance(item, str) and (item == "game-design-contract.json" or item.endswith("/game-design-contract.json")) for item in priority):
        findings.append("source_of_truth.priority must include game-design-contract.json")
    if source.get("conflict_policy") != "fail_on_conflict":
        findings.append("source_of_truth.conflict_policy must be fail_on_conflict")
    non_authoritative = source.get("non_authoritative_sources", [])
    if not isinstance(non_authoritative, list):
        findings.append("source_of_truth.non_authoritative_sources must be a list")
        non_authoritative = []

    expected_mode = _normalise_visual_mode(visual.get("projection"))
    # Explicitly inspect listed JSON design sources.  A legacy game-engine.json
    # is allowed only when it agrees with the new design contract.
    paths: list[Path] = []
    for index, value in enumerate(non_authoritative):
        path = _file_path(root, value, f"source_of_truth.non_authoritative_sources[{index}]", findings, allow_work=True)
        if path is not None:
            paths.append(path)
    legacy = root / ".codex-work" / "game-engine.json"
    if legacy.is_file() and legacy not in paths:
        paths.append(legacy)
    for path in paths:
        data = _read_json(path, path.relative_to(root).as_posix(), findings) if path.suffix.lower() == ".json" else None
        if data is None:
            continue
        mode = _normalise_visual_mode(data.get("visual_mode"))
        if mode and expected_mode and mode != expected_mode:
            findings.append(
                f"source-of-truth conflict: {path.relative_to(root).as_posix()} declares visual_mode {mode}, contract declares {expected_mode}"
            )
        # A second contract with a different projection is also a conflict.
        other = data.get("visual_system")
        if isinstance(other, Mapping):
            other_mode = _normalise_visual_mode(other.get("projection"))
            if other_mode and expected_mode and other_mode != expected_mode:
                findings.append(f"source-of-truth conflict: {path.relative_to(root).as_posix()} has a different visual projection")


def _validate_source_and_visual(root: Path, contract: Mapping[str, Any], findings: list[str]) -> Mapping[str, Any] | None:
    source = _mapping(contract.get("source_of_truth"), "source_of_truth", findings)
    visual = _mapping(contract.get("visual_system"), "visual_system", findings)
    if source is None or visual is None:
        return visual
    _require_text(visual, "renderer", "visual_system", findings)
    projection = _require_text(visual, "projection", "visual_system", findings)
    _require_text(visual, "coordinate_system", "visual_system", findings)
    camera = _mapping(visual.get("camera"), "visual_system.camera", findings)
    if camera is not None:
        _require_text(camera, "model", "visual_system.camera", findings)
        _numeric(camera, "near_clip", "visual_system.camera", findings, minimum=0)
        _numeric(camera, "far_clip", "visual_system.camera", findings, minimum=0)
        if isinstance(camera.get("near_clip"), (int, float)) and isinstance(camera.get("far_clip"), (int, float)) and camera["far_clip"] <= camera["near_clip"]:
            findings.append("visual_system.camera.far_clip must be greater than near_clip")
    tokens = _mapping(visual.get("design_tokens"), "visual_system.design_tokens", findings)
    if tokens is not None:
        for key in ("depth_unit_px", "shadow_blur_px", "motion_duration_ms"):
            _numeric(tokens, key, "visual_system.design_tokens", findings, minimum=0)
    layers = _list(visual.get("layers"), "visual_system.layers", findings, minimum=3)
    layer_ids: set[str] = set()
    for index, item in enumerate(layers):
        mapping = _mapping(item, f"visual_system.layers[{index}]", findings)
        if mapping is None:
            continue
        layer_id = _require_text(mapping, "id", f"visual_system.layers[{index}]", findings)
        if layer_id:
            if layer_id in layer_ids:
                findings.append(f"visual_system.layers contains duplicate id: {layer_id}")
            layer_ids.add(layer_id)
        _numeric(mapping, "z", f"visual_system.layers[{index}]", findings)
        _require_text(mapping, "role", f"visual_system.layers[{index}]", findings)
    lighting = _mapping(visual.get("materials_lighting"), "visual_system.materials_lighting", findings)
    if lighting is not None:
        materials = _list(lighting.get("materials"), "visual_system.materials_lighting.materials", findings, minimum=2)
        if any(not _nonempty(item) for item in materials):
            findings.append("visual_system.materials_lighting.materials must contain non-empty material descriptions")
        for key in ("lighting", "shadows"):
            _require_text(lighting, key, "visual_system.materials_lighting", findings)
    thresholds = _mapping(visual.get("measurable_thresholds"), "visual_system.measurable_thresholds", findings)
    if thresholds is not None:
        _numeric(thresholds, "minimum_depth_layers", "visual_system.measurable_thresholds", findings, minimum=3)
        _numeric(thresholds, "minimum_unique_mode_assets", "visual_system.measurable_thresholds", findings, minimum=3)
        _numeric(thresholds, "minimum_motion_duration_ms", "visual_system.measurable_thresholds", findings, minimum=180)
        _numeric(thresholds, "maximum_flat_geometry_ratio", "visual_system.measurable_thresholds", findings, minimum=0, maximum=0)
        _numeric(thresholds, "minimum_occlusion_layers", "visual_system.measurable_thresholds", findings, minimum=2)
    rejection = _list(visual.get("rejection_thresholds"), "visual_system.rejection_thresholds", findings, minimum=1)
    if any(not _nonempty(item) for item in rejection):
        findings.append("visual_system.rejection_thresholds must contain descriptions")
    if projection:
        mode = _normalise_visual_mode(projection)
        if mode is None:
            findings.append("visual_system.projection must explicitly describe a 2.5D or 3D projection")
    _source_conflicts(root, contract, source, visual, findings)
    return visual


def _validate_assets(root: Path, contract: Mapping[str, Any], visual: Mapping[str, Any] | None, findings: list[str]) -> tuple[set[str], set[str]]:
    pipeline = _mapping(contract.get("asset_pipeline"), "asset_pipeline", findings)
    if pipeline is None:
        return set(), set()
    offline = _list(pipeline.get("offline_assets"), "asset_pipeline.offline_assets", findings, minimum=3)
    offline_paths: set[str] = set()
    for index, value in enumerate(offline):
        path = _file_path(root, value, f"asset_pipeline.offline_assets[{index}]", findings)
        if path is not None:
            offline_paths.add(path.relative_to(root).as_posix())
    for key in ("layers", "occlusion_order", "load_entrypoints"):
        _list(pipeline.get(key), f"asset_pipeline.{key}", findings, minimum=3 if key == "layers" else 1)
    _require_text(pipeline, "transparency", "asset_pipeline", findings)
    _require_text(pipeline, "coordinate_system", "asset_pipeline", findings)
    metadata = _list(pipeline.get("assets"), "asset_pipeline.assets", findings, minimum=3)
    metadata_paths: set[str] = set()
    for index, item in enumerate(metadata):
        entry = _mapping(item, f"asset_pipeline.assets[{index}]", findings)
        if entry is None:
            continue
        value = entry.get("path")
        path = _file_path(root, value, f"asset_pipeline.assets[{index}].path", findings)
        if path is not None:
            relative = path.relative_to(root).as_posix()
            metadata_paths.add(relative)
            if relative not in offline_paths:
                findings.append(f"asset_pipeline.assets[{index}].path is missing from offline_assets: {relative}")
        for key in ("role", "geometry", "material", "render_layer"):
            _require_text(entry, key, f"asset_pipeline.assets[{index}]", findings)
        placeholder = entry.get("placeholder")
        if placeholder is not False:
            findings.append(f"asset_pipeline.assets[{index}].placeholder must be false")
        text = " ".join(str(entry.get(key, "")) for key in ("path", "role", "geometry", "material")) .casefold()
        if any(word in text for word in FORBIDDEN_WORDS):
            findings.append(f"asset_pipeline.assets[{index}] uses forbidden placeholder/flat geometry wording")
    forbidden = _list(pipeline.get("forbidden"), "asset_pipeline.forbidden", findings, minimum=1)
    forbidden_text = {str(item).casefold() for item in forbidden if isinstance(item, str)}
    for required in ("placeholder", "flat_rectangle", "static_screenshot"):
        if required not in forbidden_text:
            findings.append(f"asset_pipeline.forbidden must include {required}")
    return offline_paths, metadata_paths


def _source_contains(root: Path, reference: str) -> bool:
    if ":" not in reference:
        path = root / reference
        return path.is_file()
    file_value, symbol = reference.split(":", 1)
    path = root / file_value
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    # A consumer may be written as Class.method or as a method invocation.
    return symbol in text or symbol.split(".")[-1] in text


def _validate_modes(root: Path, contract: Mapping[str, Any], thresholds: Mapping[str, Any] | None, findings: list[str]) -> tuple[set[str], set[str]]:
    modes = _list(contract.get("modes"), "modes", findings, minimum=2)
    mode_ids: set[str] = set()
    mode_asset_sets: set[tuple[str, ...]] = set()
    mode_signatures: set[tuple[str, ...]] = set()
    min_assets = int(thresholds.get("minimum_unique_mode_assets", 3)) if thresholds and isinstance(thresholds.get("minimum_unique_mode_assets"), (int, float)) else 3
    for index, item in enumerate(modes):
        mode = _mapping(item, f"modes[{index}]", findings)
        if mode is None:
            continue
        mode_id = _require_text(mode, "mode_id", f"modes[{index}]", findings)
        _require_text(mode, "name", f"modes[{index}]", findings)
        if mode_id:
            if mode_id in mode_ids:
                findings.append(f"modes contains duplicate mode_id: {mode_id}")
            mode_ids.add(mode_id)
        values: list[str] = []
        for key in REQUIRED_DOMAIN_FIELDS:
            field = _mapping(mode.get(key), f"modes[{index}].{key}", findings)
            if field is None:
                continue
            value = _require_text(field, "value", f"modes[{index}].{key}", findings)
            if value:
                values.append(value.casefold())
            consumers = _list(field.get("render_consumers"), f"modes[{index}].{key}.render_consumers", findings, minimum=1)
            for consumer_index, consumer in enumerate(consumers):
                if not _nonempty(consumer):
                    findings.append(f"modes[{index}].{key}.render_consumers[{consumer_index}] must be non-empty")
                elif not _source_contains(root, consumer):
                    findings.append(f"modes[{index}].{key}.render_consumers[{consumer_index}] has no source consumer: {consumer}")
        assets = _list(mode.get("assets"), f"modes[{index}].assets", findings, minimum=min_assets)
        asset_values: list[str] = []
        for asset_index, value in enumerate(assets):
            path = _file_path(root, value, f"modes[{index}].assets[{asset_index}]", findings)
            if path is not None:
                asset_values.append(path.relative_to(root).as_posix())
        if len(set(asset_values)) < min_assets:
            findings.append(f"modes[{index}].assets must contain at least {min_assets} unique existing assets")
        mode_asset_sets.add(tuple(sorted(set(asset_values))))
        mode_signatures.add(tuple(values))
    if len(mode_asset_sets) < 2 and len(modes) >= 2:
        findings.append("modes must have independent scene asset sets; modes cannot share one generic scene")
    if len(mode_signatures) < 2 and len(modes) >= 2:
        findings.append("modes must have independent domain values; mode changes only copy, color, or count are rejected")
    return mode_ids, {asset for values in mode_asset_sets for asset in values}


def _validate_pages(root: Path, contract: Mapping[str, Any], findings: list[str]) -> dict[str, set[str]]:
    pages = _list(contract.get("pages"), "pages", findings, minimum=1)
    page_ids: set[str] = set()
    routes: set[str] = set()
    layouts: set[str] = set()
    page_evidence: dict[str, set[str]] = {}
    for index, item in enumerate(pages):
        page = _mapping(item, f"pages[{index}]", findings)
        if page is None:
            continue
        page_id = _require_text(page, "page_id", f"pages[{index}]", findings)
        route = _require_text(page, "route", f"pages[{index}]", findings)
        route_source = _require_text(page, "route_source", f"pages[{index}]", findings)
        layout = _require_text(page, "layout_signature", f"pages[{index}]", findings)
        _require_text(page, "composition", f"pages[{index}]", findings)
        _require_text(page, "error_recovery", f"pages[{index}]", findings)
        if page_id:
            if page_id in page_ids:
                findings.append(f"pages contains duplicate page_id: {page_id}")
            page_ids.add(page_id)
        if route:
            if route in routes:
                findings.append(f"pages contains duplicate route: {route}")
            routes.add(route)
        if layout:
            if layout in layouts:
                findings.append(f"pages must have independent layout signatures; duplicate: {layout}")
            layouts.add(layout)
        if route_source:
            source_path = _file_path(root, route_source, f"pages[{index}].route_source", findings)
            if source_path is not None and route and route not in source_path.read_text(encoding="utf-8", errors="replace"):
                findings.append(f"pages[{index}].route is not implemented by route_source: {route}")
        assets = _list(page.get("assets"), f"pages[{index}].assets", findings, minimum=1)
        for asset_index, value in enumerate(assets):
            _file_path(root, value, f"pages[{index}].assets[{asset_index}]", findings)
        for key in ("states", "interactions"):
            values = _list(page.get(key), f"pages[{index}].{key}", findings, minimum=2)
            if any(not _nonempty(value) for value in values):
                findings.append(f"pages[{index}].{key} must contain non-empty states/interactions")
        evidence = _list(page.get("evidence"), f"pages[{index}].evidence", findings, minimum=1)
        page_evidence[page_id or f"page_{index}"] = {str(value).removeprefix("evidence.") for value in evidence if _nonempty(value)}
    return page_evidence


def _validate_evidence(root: Path, contract: Mapping[str, Any], page_evidence: Mapping[str, set[str]], findings: list[str]) -> set[str]:
    identity = _mapping(contract.get("project_identity"), "project_identity", findings)
    if identity is None:
        identity = {}
    version = _require_text(identity, "version", "project_identity", findings)
    bundle = _require_text(identity, "bundle_id", "project_identity", findings)
    device = _require_text(identity, "device", "project_identity", findings)
    udid = _require_text(identity, "udid", "project_identity", findings)
    if device and "iphone" not in device.casefold():
        findings.append("project_identity.device must identify an iPhone")
    evidence = _list(contract.get("evidence"), "evidence", findings, minimum=1)
    ids: set[str] = set()
    paths: set[str] = set()
    evidence_by_id: set[str] = set()
    verified_count = 0
    for index, item in enumerate(evidence):
        entry = _mapping(item, f"evidence[{index}]", findings)
        if entry is None:
            continue
        evidence_id = _require_text(entry, "evidence_id", f"evidence[{index}]", findings)
        if evidence_id:
            if evidence_id in ids:
                findings.append(f"duplicate evidence id: {evidence_id}")
            ids.add(evidence_id)
            evidence_by_id.add(evidence_id)
        path = _file_path(root, entry.get("path"), f"evidence[{index}].path", findings, allow_work=True)
        relative = path.relative_to(root).as_posix() if path is not None else None
        if relative:
            if relative in paths:
                findings.append(f"duplicate evidence path: {relative}")
            paths.add(relative)
        entry_type = _require_text(entry, "type", f"evidence[{index}]", findings)
        if entry_type:
            normalized_type = entry_type.casefold()
            if normalized_type in {"recording", "video", "screen_recording"} and path is not None and path.suffix.casefold() in IMAGE_SUFFIXES:
                findings.append(f"evidence[{index}] motion evidence cannot be a static image: {relative}")
            if normalized_type in {"screenshot", "image", "still"} and _nonempty(entry.get("acceptance_item")) and any(token in entry["acceptance_item"].casefold() for token in ("motion", "animation", "runtime")):
                findings.append(f"evidence[{index}] static screenshot cannot prove runtime motion")
        for key, expected in (("project_version", version), ("bundle_id", bundle), ("device", device), ("udid", udid)):
            actual = entry.get(key)
            if not _nonempty(actual):
                findings.append(f"evidence[{index}].{key} must match project_identity")
            elif expected is not None and actual != expected:
                findings.append(f"stale evidence[{index}] {key} {actual!r} does not match current {expected!r}")
        status = entry.get("status")
        if status != "Verified":
            findings.append(f"evidence[{index}].status must be Verified")
        else:
            verified_count += 1
        digest = entry.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            findings.append(f"evidence[{index}].sha256 must be a 64-character SHA-256 digest")
        elif path is not None:
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest.casefold() != actual_digest:
                findings.append(f"evidence[{index}].sha256 does not match file contents: {relative}")
        linked = entry.get("page_id") or entry.get("mode_id")
        if linked and not _nonempty(linked):
            findings.append(f"evidence[{index}] page_id/mode_id must be non-empty when provided")
    for page_id, refs in page_evidence.items():
        for ref in refs:
            if ref not in evidence_by_id:
                findings.append(f"pages.{page_id} references missing evidence: {ref}")
    if evidence and verified_count != len(evidence):
        findings.append("every evidence item must be Verified before release")
    return ids


def _validate_status(contract: Mapping[str, Any], findings: list[str]) -> None:
    status = _mapping(contract.get("status"), "status", findings)
    if status is None:
        return
    for key in REQUIRED_STATUS_FIELDS:
        _require_text(status, key, "status", findings)
    values = {key: status.get(key, "").casefold() if isinstance(status.get(key), str) else "" for key in REQUIRED_STATUS_FIELDS}
    # These are intentionally small, explicit vocabularies so a prose claim
    # cannot accidentally be interpreted as a completed gate.
    allowed = {
        "plan_status": {"draft", "pending", "approved", "ready", "implemented", "complete", "completed"},
        "implementation_status": {"pending", "in_progress", "implemented", "complete", "completed", "blocked"},
        "verification_status": {"pending", "in_progress", "verified", "passed", "blocked", "failed"},
        "release_status": {"pending", "blocked", "ready", "released", "failed"},
    }
    for key, value in values.items():
        if value and value not in allowed[key]:
            findings.append(f"status.{key} has unsupported value: {status.get(key)}")
    if values.get("release_status") in {"ready", "released"}:
        if values.get("verification_status") not in {"verified", "passed"}:
            findings.append("status contradiction: release_status is Ready but verification_status is not Verified")
        if values.get("implementation_status") not in {"implemented", "complete", "completed"}:
            findings.append("status contradiction: release_status is Ready but implementation_status is not Implemented")
        if values.get("plan_status") not in {"approved", "ready", "implemented", "complete", "completed"}:
            findings.append("status contradiction: release_status is Ready but plan_status is not Approved")
    if values.get("verification_status") in {"blocked", "failed"} and values.get("release_status") in {"ready", "released"}:
        findings.append("status contradiction: blocked/failed verification cannot have a Ready release")


def _validate_rejection_rules(contract: Mapping[str, Any], findings: list[str]) -> None:
    rules = _list(contract.get("rejection_rules"), "rejection_rules", findings, minimum=5)
    text = " ".join(str(rule).casefold() for rule in rules)
    required_topics = (
        ("independent", "independent mode/scene rejection rule"),
        ("render consumer", "domain render consumer rejection rule"),
        ("placeholder", "placeholder asset rejection rule"),
        ("flat", "flat geometry rejection rule"),
        ("duplicate evidence", "duplicate evidence rejection rule"),
        ("static", "static evidence rejection rule"),
        ("route", "unimplemented route rejection rule"),
        ("stale", "stale device/build evidence rejection rule"),
    )
    for marker, label in required_topics:
        if marker not in text:
            findings.append(f"rejection_rules missing {label}")


def validate_project(project_root: Path | str) -> list[str]:
    """Return blocking findings for the game design contract."""
    root = Path(project_root).expanduser().resolve()
    findings: list[str] = []
    path = root / CONTRACT_PATH
    if not path.is_file():
        return [f"missing {CONTRACT_PATH.as_posix()}"]
    contract = _read_json(path, CONTRACT_PATH.as_posix(), findings)
    if contract is None:
        return findings
    if contract.get("schema_version") != 1:
        findings.append("schema_version must be 1")
    if contract.get("project_type") not in PROJECT_TYPES:
        findings.append("project_type must be 'game' or 'mixed'")
    visual = _validate_source_and_visual(root, contract, findings)
    thresholds = visual.get("measurable_thresholds") if isinstance(visual, Mapping) and isinstance(visual.get("measurable_thresholds"), Mapping) else None
    _validate_assets(root, contract, visual, findings)
    _validate_modes(root, contract, thresholds, findings)
    page_evidence = _validate_pages(root, contract, findings)
    _validate_evidence(root, contract, page_evidence, findings)
    _validate_status(contract, findings)
    _validate_rejection_rules(contract, findings)
    # Stable output is useful in CI and makes the first actionable finding easy
    # to scan while retaining all diagnostics.
    return list(dict.fromkeys(findings))


validate = validate_project


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    root = args.project_root.expanduser().resolve()
    findings = validate_project(root)
    result = {
        "status": "PASS" if not findings else "FAIL",
        "valid": not findings,
        "findings": findings,
        "errors": findings,
        "warnings": [],
        "contract_path": str(root / CONTRACT_PATH),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif findings:
        for finding in findings:
            print(f"FAIL {finding}")
    else:
        print("PASS: game design contract is structurally satisfied; run iPhone visual/runtime verification next.")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
