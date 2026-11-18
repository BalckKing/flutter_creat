#!/usr/bin/env python3
"""Validate a layered, theme-rich native iOS Launch Screen contract.

This is a source/evidence preflight. It does not replace a current iPhone
cold-launch inspection, but rejects the common white-background/small-centered-
image splash that provides no usable visual composition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_ROLES = {"background_gradient", "theme_image", "brand", "copy", "decoration"}
NEAR_WHITE = {"#FFFFFF", "#FEFEFE", "#FAFAFA", "#FAF9F2", "#F9F8F2", "#F7F6F0"}


def _regular_file(root: Path, relative: str) -> bool:
    path = root / relative
    return path.is_file() and not path.is_symlink()


def _load_ledger(root: Path, findings: list[str]):
    path = root / ".codex-work/launch-screen-visual.json"
    if not path.is_file() or path.is_symlink():
        findings.append("missing .codex-work/launch-screen-visual.json launch composition ledger")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        findings.append(f"invalid launch composition ledger: {error}")
        return None
    if not isinstance(data, dict):
        findings.append("launch composition ledger must be a JSON object")
        return None
    return data


def validate(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"{root}: project root does not exist"]

    storyboard_candidates = (
        "ios/Runner/Base.lproj/LaunchScreen.storyboard",
        "ios/Runner/LaunchScreen.storyboard",
    )
    storyboard = next((path for path in storyboard_candidates if _regular_file(root, path)), None)
    if storyboard is None:
        findings.append("Launch Screen storyboard is required at ios/Runner/Base.lproj/LaunchScreen.storyboard or ios/Runner/LaunchScreen.storyboard")

    ledger = _load_ledger(root, findings)
    if ledger is None:
        return findings

    source = ledger.get("source")
    if not isinstance(source, str) or not source.strip():
        findings.append("launch ledger must identify the native Launch Screen storyboard")
    elif storyboard is not None and source != storyboard:
        findings.append(f"launch ledger source does not match the native Launch Screen storyboard: {source}")

    composition = ledger.get("composition")
    if not isinstance(composition, str) or not composition.strip():
        findings.append("launch ledger must name a layered visual composition")
    elif composition == "single_centered_image":
        findings.append("single centered image launch screen is forbidden")

    background = ledger.get("background")
    if not isinstance(background, dict):
        findings.append("launch ledger must describe a full-bleed background layer")
    else:
        mode = background.get("mode")
        coverage = background.get("coverage")
        tokens = background.get("tokens")
        if mode not in {"gradient", "image_gradient", "hybrid"}:
            findings.append("launch screen must use a gradient or hybrid background, not a plain solid fill")
        if coverage != "full_bleed":
            findings.append("launch screen background must be full-bleed")
        if not isinstance(tokens, list) or len([item for item in tokens if isinstance(item, str) and item.strip()]) < 2:
            findings.append("launch screen needs at least two named gradient/light background tokens")
        colors = background.get("colors", [])
        if isinstance(colors, list) and colors and all(
            isinstance(color, str) and color.upper() in NEAR_WHITE for color in colors
        ):
            findings.append("near-white-only launch background is forbidden")

    layers = ledger.get("layers")
    if not isinstance(layers, list):
        findings.append("launch ledger must list background, theme image, brand, copy, and decoration layers")
        layers = []
    roles = {row.get("role") for row in layers if isinstance(row, dict)}
    missing_roles = sorted(REQUIRED_ROLES - roles)
    if missing_roles:
        findings.append(f"launch screen is missing required visual layers: {', '.join(missing_roles)}")

    theme_layers = [row for row in layers if isinstance(row, dict) and row.get("role") == "theme_image"]
    if theme_layers:
        translucent = False
        for row in theme_layers:
            opacity = row.get("opacity")
            asset = row.get("asset")
            placement = row.get("placement")
            if isinstance(opacity, (int, float)) and not isinstance(opacity, bool) and 0 < opacity < 1:
                translucent = True
            if not isinstance(asset, str) or not asset.strip() or not _regular_file(root, asset):
                findings.append("launch theme image layer must reference an existing regular asset")
            if not isinstance(placement, str) or not placement.strip() or placement == "center_small":
                findings.append("launch theme image must use a composed or full-bleed placement, not a small centered tile")
        if not translucent:
            findings.append("launch screen needs a translucent theme-image layer")

    copy_layers = [row for row in layers if isinstance(row, dict) and row.get("role") == "copy"]
    copy_text = copy_layers[0].get("text") if copy_layers else None
    if not isinstance(copy_text, list) or len([item for item in copy_text if isinstance(item, str) and item.strip()]) < 2:
        findings.append("launch screen copy must include the project name and a positioning line")

    layout = ledger.get("layout")
    if not isinstance(layout, dict):
        findings.append("launch ledger must describe layered layout geometry")
    else:
        if layout.get("single_centered_image") is True or layout.get("type") == "single_centered_image":
            findings.append("single centered image launch layout is forbidden")
        empty_ratio = layout.get("empty_area_ratio")
        if not isinstance(empty_ratio, (int, float)) or isinstance(empty_ratio, bool):
            findings.append("launch layout must record empty_area_ratio")
        elif empty_ratio > 0.60:
            findings.append("launch screen has excessive empty area; build a richer composition")

    evidence = ledger.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        findings.append("launch ledger must include current-build evidence")
    else:
        for item in evidence:
            if not isinstance(item, str) or not _regular_file(root, item):
                findings.append(f"missing current-build Launch Screen evidence: {item}")

    if storyboard is not None:
        try:
            storyboard_text = (root / storyboard).read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            findings.append(f"cannot read Launch Screen storyboard: {error}")
        else:
            if "LaunchScreen" not in storyboard_text:
                findings.append("native Launch Screen storyboard must contain a LaunchScreen scene")
            if any(token in storyboard_text.lower() for token in ("progressbar", "progress", "activityindicator", "animation")):
                findings.append("native Launch Screen must remain static without progress or animation controls")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    findings = validate(args.project_root.resolve())
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print("PASS: native Launch Screen uses a layered bright composition with full-bleed background, translucent theme imagery, brand copy, decoration, and current-build evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
