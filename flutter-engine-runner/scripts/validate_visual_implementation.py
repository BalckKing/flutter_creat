#!/usr/bin/env python3
"""Validate that the target Flutter app contains the required visual behavior.

This is a source preflight only. It intentionally does not replace iPhone runtime
verification, but it prevents design prose or unused theme tokens from counting
as implemented particles, typography, or gradients.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def read_dart_files(root: Path):
    lib = root / "lib"
    if not lib.is_dir():
        return [], "missing lib/"
    files = sorted(path for path in lib.rglob("*.dart") if path.is_file())
    if not files:
        return [], "no Dart files under lib/"
    return files, None


def joined(files):
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in files)


def require(pattern, text, label, findings):
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        findings.append(label)


def page_files(files):
    return [path for path in files if "page" in path.name.lower() or "page_module" in path.parts]


VISUAL_GATES = {
    "brand_palette", "gradients", "typography", "particles", "motion",
    "backgrounds", "decoration", "media", "content", "layout", "controls", "states",
    "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement",
}
PAGE_GATES = {
    "brand_palette", "gradients", "typography", "backgrounds", "decoration", "media", "content",
    "layout", "controls", "states", "appearance", "accessibility",
}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".mp4", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".webp"}


def is_within(path: Path, root: Path) -> bool:
    """Keep path checks compatible with Python versions before 3.9."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_visual_ledger(root: Path):
    """Check recorded coverage and local artifacts, never certify visual quality."""
    root = root.resolve()
    ledger_path = root / ".codex-work/ui-visual-gates.json"
    if not ledger_path.is_file():
        return ["missing .codex-work/ui-visual-gates.json (full visual acceptance ledger)"]
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as error:
        return [f"invalid ui-visual-gates.json: {error}"]
    if not isinstance(ledger, dict):
        return ["ui-visual-gates.json must be an object"]
    findings = []
    build = ledger.get("build")
    if not isinstance(build, dict) or any(
        not isinstance(build.get(key), str) or not build[key].strip() for key in ("id", "device", "os")
    ):
        findings.append("visual ledger needs build id, device and os")
    elif not re.search(r"\biPhone\b", build["device"]) or not re.match(r"iOS\s+\d", build["os"]):
        findings.append("visual ledger build must identify an iPhone and iOS version")

    def local_file(value, label):
        if not isinstance(value, str) or not value.strip():
            findings.append(f"{label}: expected a project-relative file path")
            return None
        path = (root / value).resolve()
        if Path(value).is_absolute() or not is_within(path, root):
            findings.append(f"{label}: path must stay inside project: {value}")
            return None
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"{label}: missing or empty file: {value}")
            return None
        return path

    surfaces = ledger.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        findings.append("visual ledger needs a nonempty surfaces list")
        surfaces = []
    surface_ids = set()
    recorded_sources = set()
    background_assets = set()
    background_hashes = {}
    background_signatures = set()
    page_ids = set()
    for surface in surfaces:
        if not isinstance(surface, dict) or not isinstance(surface.get("id"), str) or not surface["id"].strip():
            findings.append("each visual surface needs a nonempty id")
            continue
        surface_id = surface["id"]
        if surface_id in surface_ids:
            findings.append(f"duplicate visual surface: {surface_id}")
        surface_ids.add(surface_id)
        if surface.get("kind") not in {"flutter", "html", "native"}:
            findings.append(f"{surface_id}: kind must be flutter, html or native")
        if surface.get("kind") in {"flutter", "html"}:
            page_ids.add(surface_id)
        path = local_file(surface.get("source"), f"surface {surface_id}")
        if path:
            recorded_sources.add(path)

        background = surface.get("background")
        if not isinstance(background, dict):
            findings.append(f"{surface_id}: missing background record")
            continue
        background_asset = background.get("asset")
        background_path = local_file(background_asset, f"surface {surface_id} background")
        if background_path:
            if background_path.suffix.lower() not in IMAGE_EXTENSIONS:
                findings.append(f"{surface_id}: background asset is not an image: {background_asset}")
            if background_path in background_assets:
                findings.append(f"{surface_id}: background asset is reused by another surface: {background_asset}")
            background_assets.add(background_path)
            digest = hashlib.sha256(background_path.read_bytes()).hexdigest()
            previous_surface = background_hashes.get(digest)
            if previous_surface:
                findings.append(
                    f"{surface_id}: background bytes duplicate surface {previous_surface}; "
                    "each surface needs its own decoration"
                )
            else:
                background_hashes[digest] = surface_id
            if surface.get("kind") in {"flutter", "html"}:
                expected_prefix = f"assets/backgrounds/{surface_id}/{surface_id}_background"
                if not str(background_asset).replace("\\", "/").startswith(expected_prefix):
                    findings.append(
                        f"{surface_id}: background asset must be page-specific under "
                        f"assets/backgrounds/{surface_id}/: {background_asset}"
                    )
        gradient_tokens = background.get("gradient_tokens")
        if not isinstance(gradient_tokens, list) or len(set(gradient_tokens)) < 2:
            findings.append(f"{surface_id}: background needs at least two distinct gradient tokens")
        palette_hex = background.get("palette_hex")
        valid_hex = (
            isinstance(palette_hex, list)
            and len(set(palette_hex)) >= 3
            and all(isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6,8}", value) for value in palette_hex)
        )
        if not valid_hex:
            findings.append(f"{surface_id}: background needs at least three valid Logo-derived HEX colors")
        if isinstance(gradient_tokens, list) and isinstance(palette_hex, list):
            background_signatures.add((tuple(sorted(set(gradient_tokens))), tuple(sorted(set(palette_hex)))))
        if path and background_asset:
            source = path.read_text(encoding="utf-8", errors="replace")
            background_name = Path(str(background_asset)).name
            source_has_reference = (
                str(background_asset).replace("\\", "/") in source
                or background_name in source
                or (surface.get("kind") == "html" and re.search(r"data:image/", source, re.IGNORECASE))
            )
            if not source_has_reference:
                findings.append(f"{surface_id}: source does not reference its background asset")

    if len(page_ids) > 1 and len(background_signatures) == 1:
        findings.append("all visual surfaces use one identical background palette/gradient signature")

    dart_files, _ = read_dart_files(root)
    # Widget components need not be independent surfaces, so use declarations
    # rather than treating every helper under page_module as a separate page.
    expected_sources = [path for path in page_files(dart_files) if re.search(
        r"\bclass\s+\w*(?:Page|Screen)\b", path.read_text(encoding="utf-8", errors="replace")
    )]
    expected_sources += [root / "welcome.html"] if (root / "welcome.html").is_file() else []
    expected_sources += list((root / "aduit/site").glob("*.html"))
    expected_sources += list((root / "ios").glob("**/LaunchScreen.storyboard"))
    for path in expected_sources:
        if path.resolve() not in recorded_sources:
            findings.append(f"visual surface is not inventoried: {path.relative_to(root)}")

    checks = ledger.get("checks")
    if not isinstance(checks, list):
        findings.append("visual ledger checks must be a list")
        checks = []
    seen = set()
    for row in checks:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            findings.append("each visual check needs an id")
            continue
        gate = row["id"]
        if gate not in VISUAL_GATES or gate in seen:
            findings.append(f"unknown or duplicate visual gate: {gate}")
        seen.add(gate)
        if row.get("status") != "Verified":
            findings.append(f"{gate}: status is not Verified")
        if not isinstance(row.get("result"), str) or not row["result"].strip():
            findings.append(f"{gate}: missing observed result")
        targets = row.get("targets")
        if not isinstance(targets, list) or any(not isinstance(item, str) for item in targets):
            findings.append(f"{gate}: targets must be a list of surface ids")
            targets = []
        for target in targets:
            if target not in surface_ids:
                findings.append(f"{gate}: unknown target: {target}")
        exclusions = row.get("exclusions", {})
        if not isinstance(exclusions, dict):
            findings.append(f"{gate}: exclusions must map surface ids to factual reasons")
            exclusions = {}
        for target, reason in exclusions.items():
            if target not in surface_ids or not isinstance(reason, str) or not reason.strip():
                findings.append(f"{gate}: invalid applicability exclusion: {target}")
            if target in targets:
                findings.append(f"{gate}: target cannot also be excluded: {target}")
        if not targets:
            findings.append(f"{gate}: no verified target surfaces")
        if gate in PAGE_GATES:
            for missing in sorted(page_ids - set(targets) - set(exclusions)):
                findings.append(f"{gate}: surface has no acceptance result: {missing}")
        for field in ("implementation", "evidence"):
            values = row.get(field)
            if not isinstance(values, list) or not values:
                findings.append(f"{gate}: missing {field} file references")
                continue
            paths = [local_file(value, f"{gate} {field}") for value in values]
            if field == "evidence" and not any(path and path.suffix.lower() in MEDIA_EXTENSIONS for path in paths):
                findings.append(f"{gate}: needs a screenshot or recording file")
            if field == "implementation" and not any(path and not is_within(path, root / ".codex-work") for path in paths):
                findings.append(f"{gate}: evidence prose cannot replace an implementation file")
    for missing in sorted(VISUAL_GATES - seen):
        findings.append(f"missing visual gate: {missing}")
    return findings


def validate(root: Path):
    files, error = read_dart_files(root)
    if error:
        return [error]

    all_dart = joined(files)
    findings = []

    # Particle implementation must be real code, not a mention in a plan.
    require(r"\bAnimationController\b", all_dart, "missing AnimationController", findings)
    require(r"\bCustomPainter\b", all_dart, "missing CustomPainter", findings)
    require(r"\bonTapUp\b", all_dart, "missing onTapUp particle trigger", findings)
    for token in ("position", "velocity", "gravity", "color", "trail"):
        require(rf"(?:\b|_){token}s?\b", all_dart, f"particle code does not expose {token}", findings)
    require(
        r"disableAnimations|accessibleNavigation|MediaQuery\.of\([^)]*\)\.disableAnimations",
        all_dart,
        "missing Reduce Motion handling",
        findings,
    )

    # Typography and gradients must be declared and consumed by page code.
    brand_entry = root / "lib/common_module/theme/app_theme.dart"
    theme_files = [path for path in files if brand_entry.parent in path.parents]
    if not brand_entry.is_file() or brand_entry.is_symlink():
        findings.append("missing required brand entry lib/common_module/theme/app_theme.dart")
    else:
        theme = joined(theme_files)
        for role in ("display", "heading", "body", "metadata", "action"):
            require(rf"\b{role}\b", theme, f"missing typography role: {role}", findings)
        require(r"fontStyle\s*:\s*FontStyle\.italic", theme, "missing italic title treatment", findings)
        require(r"fontWeight\s*:\s*FontWeight\.", theme, "missing font-weight treatment", findings)
        require(r"LinearGradient|RadialGradient", theme, "missing shared gradient token", findings)

    require(r"ShaderMask|\.shader\b|foreground\s*:\s*Paint", all_dart, "missing gradient text implementation", findings)
    require(r"Text\.rich|RichText|InlineSpan", all_dart, "missing semantic emphasized text", findings)

    pages = page_files(files)
    visual_page_count = 0
    for path in pages:
        source = path.read_text(encoding="utf-8", errors="replace")
        has_gradient = re.search(
            r"LinearGradient|RadialGradient|ShaderMask|brandGradient|sunsetGradient|accentBorder",
            source,
        )
        has_typography = re.search(
            r"Theme\.of\(|textTheme|AppTheme|TextStyle|Text\.rich|RichText",
            source,
        )
        if has_gradient and has_typography:
            visual_page_count += 1
    if visual_page_count < 3:
        findings.append(
            f"gradient and typography implementation is consumed together by only "
            f"{visual_page_count} page files; need at least 3"
        )

    refinement = root / ".codex-work" / "ui-refinement.md"
    if not refinement.is_file():
        findings.append("missing .codex-work/ui-refinement.md")
    else:
        evidence = refinement.read_text(encoding="utf-8", errors="replace")
        for round_name in ("Round 1", "Round 2", "Round 3"):
            if round_name not in evidence:
                findings.append(f"missing {round_name} UI refinement record")
        if not re.search(r"iPhone|iphone", evidence):
            findings.append("UI refinement record has no iPhone evidence")
        if not re.search(r"\.(?:png|jpg|jpeg|heic|mp4|mov)\b", evidence, re.IGNORECASE):
            findings.append("UI refinement record has no screenshot or recording path")

    interaction = root / ".codex-work" / "particle-evidence.md"
    if not interaction.is_file():
        findings.append("missing .codex-work/particle-evidence.md")
    else:
        evidence = interaction.read_text(encoding="utf-8", errors="replace")
        for label in ("before", "active", "result"):
            if not re.search(rf"\b{label}\b", evidence, re.IGNORECASE):
                findings.append(f"particle evidence missing {label} state")
        action_lines = re.findall(r"(?im)^\s*(?:action|target)\b", evidence)
        if len(action_lines) < 2:
            findings.append("particle evidence does not identify two action targets")

    findings.extend(validate_visual_ledger(root))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    findings = validate(args.project_root.resolve())
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        print("UI visual contract is not verified; do not report visual completion.")
        return 1
    print("PASS: source preflight and full visual acceptance ledger are present.")
    print("Runtime iPhone verification is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
