#!/usr/bin/env python3
"""Validate the universal final-visual-product contract.

The technical vertical slice and the final visual product are deliberately
separate gates.  This checker validates the source contract and its evidence
paths; it does not claim that a screenshot or recording is visually good.  A
current iPhone review is still required before a project can be marked ready.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


CONTRACT_PATH = Path(".codex-work/final-visual-product.json")
PROJECT_TYPES = {"game", "non_game", "mixed"}
FINAL_CLAIM = "final_visual_product"
VERIFIED = "Verified"
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"functional\s+prototype", re.I),
    re.compile(r"visual\s+prototype", re.I),
    re.compile(r"prototype[- ]only", re.I),
    re.compile(r"placeholder", re.I),
    re.compile(r"static\s+(?:screenshot|mock|scene)", re.I),
    re.compile(r"color(?:ed)?[- ]block", re.I),
    re.compile(r"simple\s+line(?:\s+art)?", re.I),
    re.compile(r"to\s+be\s+polished", re.I),
    re.compile(r"unfinished\s+(?:visual|art|build)", re.I),
)
FORBIDDEN_PATH_PARTS = {"placeholder", "mockup", "prototype", "draft"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_path(root: Path, value: Any, label: str, findings: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        findings.append(f"{label} must be a non-empty project-relative path")
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        findings.append(f"{label} must stay inside the project: {value}")
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        findings.append(f"{label} escapes the project: {value}")
        return None
    current = root
    for part in candidate.parts:
        current /= part
        if current.is_symlink():
            findings.append(f"{label} must not use a symlink: {value}")
            return None
    if any(part.casefold() in FORBIDDEN_PATH_PARTS for part in candidate.parts):
        findings.append(f"{label} points to prototype/draft/placeholder evidence: {value}")
    return resolved


def _paths(root: Path, values: Any, label: str, findings: list[str], *, minimum: int = 1) -> list[Path]:
    if not isinstance(values, list) or len(values) < minimum:
        findings.append(f"{label} must contain at least {minimum} path(s)")
        return []
    result: list[Path] = []
    for index, value in enumerate(values):
        path = _safe_path(root, value, f"{label}[{index}]", findings)
        if path is None:
            continue
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"{label}[{index}] must point to a non-empty regular file: {value}")
        else:
            result.append(path)
    return result


def _require_iphone_capture_marker(values: Any, label: str, findings: list[str]) -> None:
    """Require evidence names to identify both the iPhone run and its capture."""
    if not isinstance(values, list):
        return
    for index, value in enumerate(values):
        if not isinstance(value, str):
            continue
        marker = value.casefold()
        has_device = any(token in marker for token in ("iphone", "ios", "simulator"))
        has_capture = any(token in marker for token in ("recording", "screenshot", "capture", "screen", "build"))
        if not (has_device and has_capture):
            findings.append(
                f"{label}[{index}] must name a current iPhone capture (include a device marker and recording/screenshot marker): {value}"
            )


def _scan_values(value: Any, location: str = "contract") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _scan_values(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scan_values(child, f"{location}[{index}]")
    elif isinstance(value, str):
        yield location, value


def _reject_forbidden_values(contract: Mapping[str, Any], findings: list[str]) -> None:
    for location, value in _scan_values(contract):
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                findings.append(f"{location} contains forbidden prototype/low-fidelity completion language: {value}")
                break


def _require_text(mapping: Mapping[str, Any], key: str, label: str, findings: list[str]) -> None:
    if not _nonempty(mapping.get(key)):
        findings.append(f"{label}.{key} must be a non-empty description")


def _validate_common(root: Path, contract: Mapping[str, Any], findings: list[str]) -> None:
    common = contract.get("common_visual_contract")
    if not isinstance(common, Mapping):
        findings.append("common_visual_contract must be an object")
        return
    for key in (
        "no_simple_line_art",
        "no_flat_color_blocks",
        "no_solid_color_background",
        "no_placeholder_or_static_mock",
    ):
        if common.get(key) is not True:
            findings.append(f"common_visual_contract.{key} must be true")
    for key in (
        "authored_asset_review",
        "composition_review",
        "motion_review",
        "state_coverage_review",
        "accessibility_review",
    ):
        if common.get(key) != VERIFIED:
            findings.append(f"common_visual_contract.{key} must be {VERIFIED}")
    rounds = common.get("refinement_rounds")
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 3:
        findings.append("common_visual_contract.refinement_rounds must be an integer >= 3")
    current_iphone = common.get("current_iphone_evidence")
    _paths(root, current_iphone, "common_visual_contract.current_iphone_evidence", findings)
    _require_iphone_capture_marker(current_iphone, "common_visual_contract.current_iphone_evidence", findings)


def _validate_game(root: Path, contract: Mapping[str, Any], findings: list[str]) -> None:
    visual = contract.get("game_visual_contract")
    if not isinstance(visual, Mapping):
        findings.append("game_visual_contract is required for game and mixed projects")
        return
    mode = visual.get("visual_mode")
    if isinstance(mode, str):
        mode = mode.casefold()
    if mode not in {"2.5d", "3d"}:
        findings.append("game_visual_contract.visual_mode must be 2.5d or 3d")
    for key in (
        "renderer",
        "camera_model",
        "materials_lighting",
        "state_variants",
        "animation_feedback",
        "hud_hierarchy",
        "content_scope",
    ):
        _require_text(visual, key, "game_visual_contract", findings)
    layers = visual.get("depth_layers")
    if not isinstance(layers, list) or len(layers) < 3 or not all(_nonempty(item) for item in layers):
        findings.append("game_visual_contract.depth_layers must contain at least three named layers")
    _paths(root, visual.get("authored_assets"), "game_visual_contract.authored_assets", findings, minimum=4)
    _paths(root, visual.get("runtime_evidence"), "game_visual_contract.runtime_evidence", findings)


def _validate_components(components: Any, findings: list[str]) -> None:
    if not isinstance(components, list) or len(components) < 2:
        findings.append("non_game_visual_contract.ui_component_consumers must contain at least two components")
        return
    for index, component in enumerate(components):
        label = f"non_game_visual_contract.ui_component_consumers[{index}]"
        if not isinstance(component, Mapping):
            findings.append(f"{label} must be an object")
            continue
        for key in ("name", "version", "license/source", "actual_consumer"):
            if not _nonempty(component.get(key)):
                findings.append(f"{label}.{key} must be non-empty")
        consumer = str(component.get("actual_consumer", "")).strip().casefold()
        if consumer in {"package", "pubspec", "dependency", "installed"}:
            findings.append(f"{label}.actual_consumer must identify a real page/service consumer")
        evidence = component.get("runtime_evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(f"{label}.runtime_evidence must be a non-empty list")


def _validate_non_game(root: Path, contract: Mapping[str, Any], findings: list[str]) -> None:
    visual = contract.get("non_game_visual_contract")
    if not isinstance(visual, Mapping):
        findings.append("non_game_visual_contract is required for non-game and mixed projects")
        return
    domain = visual.get("primary_domain")
    if domain not in {"tool", "education", "food", "travel", "sports", "fitness_health", "photo_video"}:
        findings.append("non_game_visual_contract.primary_domain must be one of the seven registered domains")
    for key in (
        "visual_language",
        "state_coverage",
    ):
        _require_text(visual, key, "non_game_visual_contract", findings)
    result_surfaces = visual.get("result_surfaces")
    if not isinstance(result_surfaces, list) or len(result_surfaces) < 3 or not all(_nonempty(item) for item in result_surfaces):
        findings.append("non_game_visual_contract.result_surfaces must contain at least three distinct result surfaces")
    page_compositions = visual.get("page_compositions")
    if not isinstance(page_compositions, list) or len(page_compositions) < 3 or not all(_nonempty(item) for item in page_compositions):
        findings.append("non_game_visual_contract.page_compositions must contain at least three distinct compositions")
    _validate_components(visual.get("ui_component_consumers"), findings)
    _paths(root, visual.get("domain_assets"), "non_game_visual_contract.domain_assets", findings, minimum=3)
    _paths(root, visual.get("runtime_evidence"), "non_game_visual_contract.runtime_evidence", findings)


def validate_project(project_root: Path | str) -> list[str]:
    root = Path(project_root).expanduser().resolve()
    findings: list[str] = []
    path = root / CONTRACT_PATH
    if not path.is_file() or path.is_symlink():
        return [f"missing {CONTRACT_PATH.as_posix()}"]
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"invalid {CONTRACT_PATH.as_posix()}: {error}"]
    if not isinstance(contract, Mapping):
        return ["final visual product contract must be a JSON object"]

    if contract.get("schema_version") != 1:
        findings.append("schema_version must be 1")
    project_type = contract.get("project_type")
    if project_type not in PROJECT_TYPES:
        findings.append("project_type must be game, non_game, or mixed")
    if contract.get("claim") != FINAL_CLAIM:
        findings.append("claim must be final_visual_product; a prototype or vertical slice cannot claim final completion")
    if contract.get("development_stage") != FINAL_CLAIM:
        findings.append("development_stage must be final_visual_product; vertical_slice is an earlier gate")

    boundary = contract.get("prototype_boundary")
    if not isinstance(boundary, Mapping):
        findings.append("prototype_boundary must be an object")
    else:
        if boundary.get("vertical_slice_status") != "Passed":
            findings.append("prototype_boundary.vertical_slice_status must be Passed before final visual review")
        if boundary.get("cannot_substitute_for_final") is not True:
            findings.append("prototype_boundary.cannot_substitute_for_final must be true")

    evidence = contract.get("evidence")
    _paths(root, evidence, "evidence", findings)
    _validate_common(root, contract, findings)
    if project_type in {"game", "mixed"}:
        _validate_game(root, contract, findings)
    if project_type in {"non_game", "mixed"}:
        _validate_non_game(root, contract, findings)
    _reject_forbidden_values(contract, findings)
    return findings


validate = validate_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    findings = validate_project(args.project_root)
    result = {
        "scope": "final-visual-product",
        "project_root": str(args.project_root.expanduser().resolve()),
        "status": "Passed" if not findings else "Failed",
        "findings": findings,
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS: final visual product contract is structurally complete." if not findings else "FAIL: final visual product contract is incomplete.")
        for finding in findings:
            print(f"- {finding}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
