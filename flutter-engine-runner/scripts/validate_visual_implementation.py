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
    return [path for path in files if "page" in path.name.lower()
            or "page_module" in path.parts or path.name == "welcome.dart"]


def validate_welcome_source(root: Path):
    """Check the Dart/HTML boundary; runtime layout still needs verification."""
    findings = []
    welcome = root / "lib/welcome.dart"
    if not welcome.is_file() or welcome.is_symlink():
        findings.append("missing regular Welcome source lib/welcome.dart")
    else:
        source = welcome.read_text(encoding="utf-8", errors="replace")
        require(r"\bclass\s+WelcomePage\b", source,
                "lib/welcome.dart must define WelcomePage", findings)
        if re.search(r"WebView|HtmlWidget|loadHtmlString|AppBridge|go://continue", source):
            findings.append("Welcome must use Flutter Widgets and direct Dart navigation, not HTML or a web bridge")
        if re.search(r"\b(?:SingleChildScrollView|ListView|CustomScrollView|NestedScrollView)\b"
                     r"|scrollDirection\s*:\s*Axis\.vertical", source):
            findings.append("Welcome must not contain a vertical scrolling layout; use responsive non-scrolling content and horizontal cards")
    for relative in ("welcome.html", "enter.html", "aduit/enter.html"):
        path = root / relative
        if path.exists() or path.is_symlink():
            findings.append(f"obsolete Welcome HTML path: {relative}; preserve standalone HTML only at aduit/welcome.html")
    runtime_files = list((root / "lib").rglob("*.dart"))
    runtime_files += [root / "pubspec.yaml"]
    for path in runtime_files:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        # Preserve the three raw policy URLs even if their server paths contain
        # a delivery directory name. A web URL is not an asset filesystem path.
        source = re.sub(r"https?://[^\s\x22\x27<>]+", "", source)
        if re.search(r"(?:welcome|enter)\.html|aduit[/\\]", source, re.IGNORECASE):
            findings.append(f"runtime source must not reference delivery HTML or aduit paths: {path.relative_to(root)}")
    return findings


VISUAL_GATES = {
    "brand_palette", "gradients", "typography", "particles", "motion",
    "page_transitions", "background_motion",
    "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content", "layout", "controls", "states",
    "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement",
}
OPTIONAL_VISUAL_GATES = {"gradients"}
PAGE_GATES = {
    "brand_palette", "gradients", "typography", "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content",
    "layout", "controls", "states", "appearance", "accessibility",
}
FLUTTER_MOTION_GATES = {"page_transitions", "background_motion"}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".mp4", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".webp"}
LAYOUT_AXES = (
    "composition", "region_order", "media_structure", "content_structure",
    "action_structure", "navigation_structure",
)


def validate_layout_diversity(surfaces, history=()):
    """Reject missing/near-identical structural records; screenshots need review."""
    findings = []

    def signature(row, label):
        layout = row.get("layout")
        if not isinstance(layout, dict):
            findings.append(f"{label}: missing layout record")
            return None
        values = []
        for axis in LAYOUT_AXES:
            value = layout.get(axis)
            parts = value if axis == "region_order" else [value]
            if not isinstance(parts, list) or not parts or any(
                not isinstance(part, str) or not part.strip() for part in parts
            ):
                findings.append(f"{label}: invalid layout axis {axis}")
                return None
            normalized = tuple(re.sub(r"[\W_]+", "_", part.casefold()).strip("_") for part in parts)
            if not all(normalized):
                findings.append(f"{label}: empty layout axis {axis}")
                return None
            values.append(normalized)
        return tuple(values)

    valid_rows = [row for row in surfaces if isinstance(row, dict)
                  and isinstance(row.get("id"), str) and row["id"].strip()]
    by_id = {row["id"]: row for row in valid_rows}
    current = []
    for row in valid_rows:
        label = str(row["id"])
        value = signature(row, label)
        alias = row.get("same_layout_as")
        if alias is not None:
            target = by_id.get(alias) if isinstance(alias, str) else None
            allowed = bool(target and (
                (row.get("kind") == "html" and row.get("source") == "aduit/welcome.html"
                 and target.get("kind") == "flutter" and target.get("source") == "lib/welcome.dart")
                or (row.get("kind") == target.get("kind") == "native"
                    and row.get("role") == "native_cover" and target.get("role") == "native_launch")
            ))
            if not allowed or target.get("same_layout_as") is not None:
                findings.append(f"{label}: invalid same_layout_as representation")
            elif value != signature(target, str(alias)):
                findings.append(f"{label}: representation layout differs from {alias}")
            continue
        if value:
            current.append((label, value))

    previous = []
    for row in history:
        if not isinstance(row, dict) or not isinstance(row.get("project"), str) or not row["project"].strip():
            findings.append("invalid layout history project record")
            continue
        label = f"history {row['project']}/{row.get('id', '?')}"
        value = signature(row, label)
        if value:
            previous.append((label, value))

    for index, (label, value) in enumerate(current):
        for other_label, other_value in current[:index] + previous:
            difference = sum(left != right for left, right in zip(value, other_value))
            if difference < 3:
                findings.append(f"{label}: insufficient structural difference from {other_label} ({difference}/6 axes; need 3)")
    return findings


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
    history = ledger.get("layout_history")
    records = []
    if (not isinstance(history, dict) or not isinstance(history.get("scope"), str)
            or history["scope"] not in {"available_records", "first_record", "unavailable"}):
        findings.append("missing layout_history scope and records")
    elif not isinstance(history.get("records"), list):
        findings.append("layout_history records must be a list")
    else:
        records = history["records"]
        if history["scope"] == "unavailable":
            findings.append("cross-project layout comparison is not verified")
        if history["scope"] == "available_records" and not records:
            findings.append("available layout history must contain records")
        if history["scope"] == "first_record" and records:
            findings.append("first_record layout history cannot contain prior records")
    findings.extend(validate_layout_diversity(surfaces, records))
    surface_ids = set()
    recorded_sources = set()
    background_assets = set()
    background_hashes = {}
    background_scenes = set()
    page_ids = set()
    flutter_ids = set()
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
        if surface.get("kind") == "flutter":
            flutter_ids.add(surface_id)
        path = local_file(surface.get("source"), f"surface {surface_id}")
        if path:
            recorded_sources.add(path)
        standalone_welcome = bool(path and path == root / "aduit/welcome.html"
                                  and surface.get("kind") == "html")

        background = surface.get("background")
        if not isinstance(background, dict):
            findings.append(f"{surface_id}: missing background record")
            continue
        # The image accent is required in addition to any procedural/animated
        # scene. Metadata cannot establish real visibility; inspect the build.
        background_asset = background.get("asset")
        if not isinstance(background_asset, str) or not background_asset.strip():
            findings.append(f"{surface_id}: missing required translucent background image asset")
        opacity = background.get("opacity")
        if isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not 0 < opacity < 1:
            findings.append(f"{surface_id}: background opacity must be numeric and strictly between 0 and 1")
        placement = background.get("placement")
        if not isinstance(placement, str) or not placement.strip():
            findings.append(f"{surface_id}: background placement must describe the visible image region")
        background_mode = background.get("mode", "image")
        if not isinstance(background_mode, str) or background_mode not in {"image", "procedural", "animation", "hybrid"}:
            findings.append(f"{surface_id}: unknown background mode: {background_mode}")
            continue
        uses_scene = background_mode in {"procedural", "animation", "hybrid"}
        background_path = local_file(background_asset, f"surface {surface_id} background")
        if background_path:
            if background_path.suffix.lower() not in IMAGE_EXTENSIONS:
                findings.append(f"{surface_id}: background asset is not an image: {background_asset}")
            if background_path in background_assets and not standalone_welcome:
                findings.append(f"{surface_id}: background asset is reused by another surface: {background_asset}")
            if not standalone_welcome:
                background_assets.add(background_path)
            digest = hashlib.sha256(background_path.read_bytes()).hexdigest()
            previous_surface = background_hashes.get(digest)
            if previous_surface and not standalone_welcome:
                findings.append(
                    f"{surface_id}: background bytes duplicate surface {previous_surface}; "
                    "each surface needs its own decoration"
                )
            elif not standalone_welcome:
                background_hashes[digest] = surface_id
            if surface.get("kind") in {"flutter", "html"}:
                background_id = "welcome" if standalone_welcome else surface_id
                expected_prefix = f"assets/backgrounds/{background_id}/{background_id}_background"
                if not str(background_asset).replace("\\", "/").startswith(expected_prefix):
                    findings.append(
                        f"{surface_id}: background asset must be page-specific under "
                        f"assets/backgrounds/{surface_id}/: {background_asset}"
                    )
        if uses_scene:
            if surface.get("kind") == "native":
                findings.append(f"{surface_id}: native Launch Screen must stay static; export a still and use image mode")
            scene_id = background.get("scene_id")
            if not isinstance(scene_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", scene_id):
                findings.append(f"{surface_id}: background needs a stable scene_id")
            elif scene_id in background_scenes and not standalone_welcome:
                findings.append(f"{surface_id}: background scene_id is reused by another surface: {scene_id}")
            elif not standalone_welcome:
                background_scenes.add(scene_id)
            implementation = background.get("implementation")
            scene_code = []
            if not isinstance(implementation, list) or not implementation:
                findings.append(f"{surface_id}: missing executable background implementation file references")
            else:
                for value in implementation:
                    scene_path = local_file(value, f"surface {surface_id} background implementation")
                    if not scene_path:
                        continue
                    allowed_extensions = {".dart", ".frag", ".glsl"} if surface.get("kind") == "flutter" else {".html", ".css", ".js"}
                    if (is_within(scene_path, root / ".codex-work")
                            or scene_path.suffix.lower() not in allowed_extensions):
                        findings.append(f"{surface_id}: expected executable background implementation: {value}")
                    else:
                        scene_code.append(scene_path.read_text(encoding="utf-8", errors="replace"))
            entrypoint = background.get("entrypoint")
            if not isinstance(entrypoint, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", entrypoint):
                findings.append(f"{surface_id}: background needs a callable entrypoint identifier")
            else:
                entry_pattern = rf"\b{re.escape(entrypoint)}\b"
                source = path.read_text(encoding="utf-8", errors="replace") if path else ""
                if not re.search(entry_pattern, source) or not any(re.search(entry_pattern, code) for code in scene_code):
                    findings.append(f"{surface_id}: source and implementation must reference the background entrypoint")
            resources = background.get("resources", [])
            if not isinstance(resources, list):
                findings.append(f"{surface_id}: background resources must be a list of bundled file paths")
            else:
                for value in resources:
                    resource = local_file(value, f"surface {surface_id} background resource")
                    if resource and (is_within(resource, root / ".codex-work") or is_within(resource, root / "aduit")):
                        findings.append(f"{surface_id}: background resources must be bundled project assets: {value}")
            if surface.get("kind") == "flutter":
                recording = local_file(background.get("recording"), f"surface {surface_id} background motion recording")
                if recording and recording.suffix.lower() not in {".mp4", ".mov"}:
                    findings.append(f"{surface_id}: background needs an iPhone motion recording file")
        # Color metadata is optional. Validate its shape when supplied, without
        # imposing palette sizes, hue choices or gradient usage on the design.
        if "gradient_tokens" in background:
            gradient_tokens = background["gradient_tokens"]
            if not isinstance(gradient_tokens, list) or any(
                not isinstance(value, str) or not value.strip() for value in gradient_tokens
            ):
                findings.append(f"{surface_id}: gradient_tokens must be a list of nonempty token names")
        if "palette_hex" in background:
            palette_hex = background["palette_hex"]
            if not isinstance(palette_hex, list) or any(
                not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?", value)
                for value in palette_hex
            ):
                findings.append(f"{surface_id}: palette_hex must be a list of valid HEX colors")
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

    dart_files, _ = read_dart_files(root)
    # Widget components need not be independent surfaces, so use declarations
    # rather than treating every helper under page_module as a separate page.
    expected_sources = [path for path in page_files(dart_files) if re.search(
        r"\bclass\s+\w*(?:Page|Screen)\b", path.read_text(encoding="utf-8", errors="replace")
    )]
    expected_sources += [root / "aduit/welcome.html"] if (root / "aduit/welcome.html").is_file() else []
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
        if gate in FLUTTER_MOTION_GATES:
            for missing in sorted(flutter_ids - set(targets)):
                findings.append(f"{gate}: Flutter surface has no motion acceptance result: {missing}")
        for field in ("implementation", "evidence"):
            values = row.get(field)
            if not isinstance(values, list) or not values:
                findings.append(f"{gate}: missing {field} file references")
                continue
            paths = [local_file(value, f"{gate} {field}") for value in values]
            if field == "evidence" and not any(path and path.suffix.lower() in MEDIA_EXTENSIONS for path in paths):
                findings.append(f"{gate}: needs a screenshot or recording file")
            if (field == "evidence" and gate in FLUTTER_MOTION_GATES
                    and not any(path and path.suffix.lower() in {".mp4", ".mov"} for path in paths)):
                findings.append(f"{gate}: needs an iPhone motion recording file")
            if field == "implementation" and not any(path and not is_within(path, root / ".codex-work") for path in paths):
                findings.append(f"{gate}: evidence prose cannot replace an implementation file")
    for missing in sorted(VISUAL_GATES - OPTIONAL_VISUAL_GATES - seen):
        findings.append(f"missing visual gate: {missing}")
    return findings


def validate(root: Path):
    files, error = read_dart_files(root)
    if error:
        return [error]

    all_dart = joined(files)
    findings = validate_welcome_source(root)

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

    # Typography must be declared and consumed; gradients are a design choice.
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
    require(r"Text\.rich|RichText|InlineSpan", all_dart, "missing semantic emphasized text", findings)

    pages = page_files(files)
    visual_page_count = 0
    for path in pages:
        source = path.read_text(encoding="utf-8", errors="replace")
        has_typography = re.search(
            r"Theme\.of\(|textTheme|AppTheme|TextStyle|Text\.rich|RichText",
            source,
        )
        if has_typography:
            visual_page_count += 1
    if visual_page_count < 3:
        findings.append(
            f"typography implementation is consumed by only "
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
