#!/usr/bin/env python3
"""Validate that the target Flutter app contains the required visual behavior.

This is a source preflight only. It intentionally does not replace iPhone runtime
verification, but it prevents design prose or unused theme tokens from counting
as implemented particles, typography, or gradients.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
import re
import struct
import sys
import zlib
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
    for relative in ("welcome.html", "enter.html", "AppListing/enter.html"):
        path = root / relative
        if path.exists() or path.is_symlink():
            findings.append(f"obsolete Welcome HTML path: {relative}; preserve standalone HTML only at AppListing/welcome.html")
    runtime_files = list((root / "lib").rglob("*.dart"))
    runtime_files += [root / "pubspec.yaml"]
    for path in runtime_files:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        # Preserve the three raw policy URLs even if their server paths contain
        # a delivery directory name. A web URL is not an asset filesystem path.
        source = re.sub(r"https?://[^\s\x22\x27<>]+", "", source)
        if re.search(r"(?:welcome|enter)\.html|AppListing[/\\]", source, re.IGNORECASE):
            findings.append(f"runtime source must not reference delivery HTML or AppListing paths: {path.relative_to(root)}")
    return findings


VISUAL_GATES = {
    "brand_palette", "gradients", "typography", "particles", "motion",
    "page_transitions", "background_motion",
    "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content", "layout", "controls", "states",
    "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement",
}
OPTIONAL_VISUAL_GATES = set()
DESIGN_REVIEW_CATEGORIES = {
    "accessibility",
    "touch_interaction",
    "safe_area",
    "typography",
    "color_contrast",
    "responsive_layout",
    "motion",
    "navigation",
    "reduced_motion",
}
PAGE_GATES = {
    "brand_palette", "gradients", "typography", "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content",
    "layout", "controls", "states", "appearance", "accessibility",
}
FLUTTER_MOTION_GATES = {"page_transitions", "background_motion"}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".mp4", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".webp"}
MOTION_RECORDING_EXTENSIONS = {".mp4", ".mov"}
NATIVE_FLUTTER_MOTION_APIS = {
    "AnimationController", "Tween", "CurvedAnimation", "AnimatedBuilder",
    "AnimatedContainer", "AnimatedOpacity", "AnimatedSwitcher", "AnimatedPositioned",
    "CustomPainter", "CustomPaint", "BackdropFilter", "ShaderMask", "Transform",
}
FORBIDDEN_MOTION_FORMS = re.compile(
    r"(?:simple\s+(?:gradient|fade|scale|slide)|flat\s+color|color\s*block|static\s+only|"
    r"简单渐变|单纯渐变|纯色块|色块拼接|静态占位|无动效)", re.I
)
DEFAULT_RASTER_QUALITY = {
    "minimum_width": 32,
    "minimum_height": 32,
    "minimum_unique_colors": 16,
    "maximum_dominant_color_ratio": 0.88,
    "minimum_opaque_coverage": 0.12,
    "minimum_texture_variation": 0.02,
}
NON_GAME_FLAT_RENDER_MARKERS = (
    r"\b(?:drawLine|drawRect|drawPath|lineTo|moveTo|fillRect|strokeRect|stroke|solidColor|flatColor)\b",
    r"\bColoredBox\b",
    r"\bContainer\s*\([^\n]*(?:\bcolor\s*:|BoxDecoration\s*\([^\n]*\bcolor\s*:)",
    r"\b(?:canvas\.fill|canvas\.stroke|context\.fillRect|context\.strokeRect)\b",
)
NON_GAME_RICH_RENDER_MARKERS = (
    r"\b(?:Image\.asset|AssetImage|NetworkImage|DecorationImage|ImageProvider|Texture|Material|Shader|"
    r"FragmentProgram|BackdropFilter|Rive|Lottie|VideoPlayer|Sprite|Particle|MapView|GoogleMap|Mapbox|"
    r"FlutterMap|AppleMap|LineChart|BarChart|PieChart|FlChart|Chart|PBR|occlusion|parallax)\b",
    r"\b(?:CustomPainter|CustomPaint)\b.*\b(?:Image|Shader|Particle|Texture|Material)\b",
    r"(?:data:image/|<img\b|<video\b|background-image\s*:)",
    r"\.(?:png|jpe?g|webp|heic|gif|mp4|mov)\b",
)
LAYOUT_AXES = (
    "composition", "region_order", "media_structure", "content_structure",
    "action_structure", "navigation_structure",
)


def _png_samples(path: Path, *, max_side: int = 256):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    position = 8
    width = height = bit_depth = color_type = None
    palette = []
    transparency = []
    compressed = bytearray()
    while position + 8 <= len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        start = position + 8
        end = start + length
        if end + 4 > len(data):
            return None
        payload = data[start:end]
        position = end + 4
        if kind == b"IHDR" and len(payload) == 13:
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if compression != 0 or filtering != 0 or interlace != 0:
                return None
        elif kind == b"PLTE":
            palette = [tuple(payload[index:index + 3]) for index in range(0, len(payload) - 2, 3)]
        elif kind == b"tRNS":
            transparency = list(payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if not width or not height or bit_depth != 8 or color_type not in {0, 2, 3, 4, 6}:
        return None
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    row_bytes = width * channels
    try:
        decoded = zlib.decompress(bytes(compressed))
    except zlib.error:
        return None
    if len(decoded) < height * (row_bytes + 1):
        return None
    rows = []
    offset = 0
    previous = bytearray(row_bytes)
    for _ in range(height):
        filter_type = decoded[offset]
        raw = bytearray(decoded[offset + 1:offset + 1 + row_bytes])
        offset += row_bytes + 1
        if filter_type not in {0, 1, 2, 3, 4}:
            return None
        row = bytearray(row_bytes)
        for index, value in enumerate(raw):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            up_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            else:
                estimate = left + up - up_left
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
            row[index] = (value + predictor) & 0xff
        rows.append(bytes(row))
        previous = row
    step_x = max(1, math.ceil(width / max_side))
    step_y = max(1, math.ceil(height / max_side))
    samples = []
    for y in range(0, height, step_y):
        row = rows[y]
        for x in range(0, width, step_x):
            start = x * channels
            values = row[start:start + channels]
            if color_type == 0:
                gray = values[0]
                samples.append((gray, gray, gray, 255))
            elif color_type == 2:
                samples.append((values[0], values[1], values[2], 255))
            elif color_type == 3:
                index = values[0]
                if index >= len(palette):
                    return None
                red, green, blue = palette[index]
                alpha = transparency[index] if index < len(transparency) else 255
                samples.append((red, green, blue, alpha))
            elif color_type == 4:
                samples.append((values[0], values[0], values[0], values[1]))
            else:
                samples.append((values[0], values[1], values[2], values[3]))
    return int(width), int(height), samples


def _raster_metrics(path: Path):
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        Image = None  # type: ignore
    decoded = None
    if Image is not None:
        try:
            with Image.open(path) as image:
                width, height = image.size
                image = image.convert("RGBA")
                image.thumbnail((256, 256))
                pixel_data = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
                decoded = (width, height, list(pixel_data))
        except Exception:
            decoded = None
    decoded = decoded or _png_samples(path)
    if decoded is None:
        return None
    width, height, samples = decoded
    if not samples:
        return None
    quantized = [(red // 16, green // 16, blue // 16, alpha // 32) for red, green, blue, alpha in samples]
    counts = Counter(quantized)
    luminance = [0.2126 * red + 0.7152 * green + 0.0722 * blue for red, green, blue, _ in samples]
    differences = [abs(luminance[index] - luminance[index - 1]) / 255.0 for index in range(1, len(luminance))]
    return {
        "width": float(width),
        "height": float(height),
        "unique_colors": float(len(counts)),
        "dominant_color_ratio": max(counts.values()) / len(samples),
        "opaque_coverage": sum(1 for _, _, _, alpha in samples if alpha > 0) / len(samples),
        "texture_variation": sum(differences) / max(1, len(differences)),
        "edge_density": sum(1 for value in differences if value >= 0.16) / max(1, len(differences)),
    }


def validate_raster_quality(path: Path, label: str, quality: dict, findings: list[str]):
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        return
    metrics = _raster_metrics(path)
    if metrics is None:
        findings.append(f"{label}: raster quality cannot be inspected; use a decodable authored image")
        return
    checks = (
        ("minimum_width", metrics["width"], ">=", "width"),
        ("minimum_height", metrics["height"], ">=", "height"),
        ("minimum_unique_colors", metrics["unique_colors"], ">=", "unique colors/material regions"),
        ("maximum_dominant_color_ratio", metrics["dominant_color_ratio"], "<=", "dominant color ratio"),
        ("minimum_opaque_coverage", metrics["opaque_coverage"], ">=", "opaque coverage"),
        ("minimum_texture_variation", metrics["texture_variation"], ">=", "texture variation"),
    )
    for key, actual, operator, description in checks:
        expected = quality.get(key)
        if not isinstance(expected, (int, float)) or isinstance(expected, bool):
            continue
        passed = actual >= float(expected) if operator == ">=" else actual <= float(expected)
        if not passed:
            findings.append(f"{label}: raster quality fails ({description} {actual:.4f} {operator} {float(expected):.4f}); simple line art and flat color blocks are forbidden")
    if (
        metrics["unique_colors"] <= max(8.0, float(quality.get("minimum_unique_colors", 16)) / 2.0)
        and metrics["edge_density"] >= 0.01
        and metrics["dominant_color_ratio"] >= 0.45
    ):
        findings.append(f"{label}: raster appears to be simple line art rather than an authored image")


def validate_design_system_contract(root: Path, ledger: dict) -> list[str]:
    """Require the design reference and UI/UX review before visual implementation.

    The visual ledger is the hand-off between planning and implementation.  A
    package name, mockup, or screenshot cannot satisfy this gate: the selected
    reference, persisted design-system master, resolved review findings, and
    current iPhone evidence must all be present inside the project boundary.
    """
    findings: list[str] = []
    contract = ledger.get("design_system")
    if not isinstance(contract, dict):
        return [
            "design_system contract is required: select awesome-design-md or record a custom DESIGN.md, "
            "then complete ui-ux-pro-max review before component selection"
        ]

    def required_text(value, label):
        if not isinstance(value, str) or not value.strip():
            findings.append(f"design_system.{label} must be a nonempty string")

    def required_local_file(value, label):
        if not isinstance(value, str) or not value.strip():
            findings.append(f"design_system.{label} must be a project-relative file path")
            return None
        relative = Path(value)
        candidate = (root / relative).resolve()
        if relative.is_absolute() or not is_within(candidate, root):
            findings.append(f"design_system.{label} must stay inside the project: {value}")
            return None
        if not candidate.is_file() or candidate.stat().st_size == 0:
            findings.append(f"design_system.{label} is missing or empty: {value}")
            return None
        return candidate

    reference = contract.get("reference")
    if not isinstance(reference, dict):
        findings.append("design_system.reference is required")
    else:
        kind = reference.get("kind")
        if kind not in {"awesome-design-md", "custom"}:
            findings.append("design_system.reference.kind must be awesome-design-md or custom")
        required_text(reference.get("name"), "reference.name")
        required_text(reference.get("selection_reason"), "reference.selection_reason")
        source = reference.get("source")
        required_text(source, "reference.source")
        if kind == "awesome-design-md" and isinstance(source, str) and "awesome-design-md" not in source:
            findings.append("design_system.reference.source must identify the awesome-design-md catalog")
        if kind == "custom" and isinstance(source, str) and not source.strip():
            findings.append("custom design_system.reference.source must explain the custom origin")

    required_local_file(contract.get("design_doc", "DESIGN.md"), "design_doc")
    required_local_file(contract.get("master"), "master")
    required_text(contract.get("ui_ux_command"), "ui_ux_command")
    required_text(contract.get("ui_ux_query"), "ui_ux_query")
    required_text(contract.get("ui_ux_stack"), "ui_ux_stack")
    if contract.get("ui_ux_stack") != "flutter":
        findings.append("design_system.ui_ux_stack must be flutter for this workflow")
    if contract.get("status") != "Verified":
        findings.append("design_system.status must be Verified")
    if contract.get("component_selection_gate") != "design_review_verified":
        findings.append("component selection must be gated by a Verified design review")

    review = contract.get("ui_ux_review")
    if not isinstance(review, dict):
        findings.append("design_system.ui_ux_review is required")
        return findings
    review_path = required_local_file(review.get("record"), "ui_ux_review.record")
    if review.get("status") != "Verified":
        findings.append("design_system.ui_ux_review.status must be Verified")
    if not isinstance(review.get("unresolved_findings"), list):
        findings.append("design_system.ui_ux_review.unresolved_findings must be a list")
    elif review["unresolved_findings"]:
        findings.append("design_system.ui_ux_review contains unresolved findings")
    categories = review.get("categories")
    if not isinstance(categories, dict):
        findings.append("design_system.ui_ux_review.categories must be an object")
        categories = {}
    for category in sorted(DESIGN_REVIEW_CATEGORIES):
        row = categories.get(category)
        if not isinstance(row, dict):
            findings.append(f"design_system.ui_ux_review.categories.{category} is required")
            continue
        if row.get("status") != "Verified":
            findings.append(f"design_system.ui_ux_review.categories.{category}.status must be Verified")
        for key in ("finding", "resolution"):
            required_text(row.get(key), f"ui_ux_review.categories.{category}.{key}")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(f"design_system.ui_ux_review.categories.{category}.evidence is required")

    evidence = review.get("current_iphone_evidence")
    if not isinstance(evidence, list) or not evidence:
        findings.append("design_system.ui_ux_review.current_iphone_evidence is required")
    else:
        for index, value in enumerate(evidence):
            path = required_local_file(value, f"ui_ux_review.current_iphone_evidence[{index}]")
            if path is not None and path.suffix.lower() not in MEDIA_EXTENSIONS:
                findings.append(
                    f"design_system.ui_ux_review.current_iphone_evidence[{index}] must be an image or recording: {value}"
                )

    if review_path is not None:
        review_text = review_path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"awesome-design-md|custom design system", review_text, re.I):
            findings.append("ui-ux review record must state the selected catalog or custom design-system decision")
        if not re.search(r"ui-ux-pro-max", review_text, re.I):
            findings.append("ui-ux review record must identify ui-ux-pro-max")
        if re.search(r"\b(?:TBD|TODO|pending|unresolved|half[- ]finished|placeholder)\b", review_text, re.I):
            findings.append("ui-ux review record contains unresolved or placeholder language")
    return findings


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
                (row.get("kind") == "html" and row.get("source") == "AppListing/welcome.html"
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


def validate_non_game_ui_contract(root: Path, ledger: dict, surfaces, findings: list[str]) -> None:
    """Require real UI components and authored visual treatment for non-game work.

    The contract is deliberately separate from the game-engine manifest. A
    non-game app may choose any suitable Flutter SDK widget, package, renderer,
    shader or animation component, but it must identify a real consumer and
    provide visual evidence. Pure line art, flat color-block collages and a
    single solid-color background are rejected as implementation shortcuts.
    """
    root = root.resolve()
    project_type = ledger.get("project_type")
    if project_type not in {"non_game", "mixed"}:
        return

    contract = ledger.get("ui_component_contract")
    if not isinstance(contract, dict):
        findings.append("ui_component_contract is required for non-game and mixed projects")
        return

    components = contract.get("components")
    if not isinstance(components, list) or len(components) < 2:
        findings.append("ui_component_contract.components must list at least two selected UI components")
        components = []

    for index, component in enumerate(components):
        label = f"ui_component_contract.components[{index}]"
        if not isinstance(component, dict):
            findings.append(f"{label} must be an object")
            continue
        for key in ("name", "version", "license/source", "actual_consumer"):
            value = component.get(key)
            if not isinstance(value, str) or not value.strip():
                findings.append(f"{label}.{key} is required")

        consumer_value = component.get("actual_consumer")
        consumer = None
        if isinstance(consumer_value, str) and consumer_value.strip():
            consumer = (root / consumer_value).resolve()
            if Path(consumer_value).is_absolute() or not is_within(consumer, root):
                findings.append(f"{label}.actual_consumer must stay inside the project: {consumer_value}")
                consumer = None
            elif not consumer.is_file():
                findings.append(f"{label}.actual_consumer is missing: {consumer_value}")

        markers = component.get("runtime_markers")
        if not isinstance(markers, list) or not markers or any(not isinstance(marker, str) or not marker.strip() for marker in markers):
            findings.append(f"{label}.runtime_markers must list the component calls consumed at runtime")
        elif consumer is not None and consumer.is_file():
            source = consumer.read_text(encoding="utf-8", errors="replace")
            missing = [marker for marker in markers if marker not in source]
            if missing:
                findings.append(f"{label}.runtime_markers are not consumed by {consumer_value}: {', '.join(missing)}")

    constraints = contract.get("visual_constraints")
    if not isinstance(constraints, dict):
        findings.append("ui_component_contract.visual_constraints is required")
    else:
        for key, label in (
            ("no_simple_line_art", "simple line art"),
            ("no_flat_color_blocks", "flat color blocks"),
            ("no_solid_color_background", "solid color backgrounds"),
        ):
            if constraints.get(key) is not True:
                findings.append(f"ui_component_contract must reject {label}")

    runtime_evidence = contract.get("runtime_evidence")
    if not isinstance(runtime_evidence, list) or not runtime_evidence:
        findings.append("ui_component_contract.runtime_evidence must list current iPhone visual evidence")
    else:
        for index, value in enumerate(runtime_evidence):
            evidence = local_contract_file(root, value, f"ui_component_contract.runtime_evidence[{index}]", findings)
            if evidence is not None and evidence.suffix.lower() not in MEDIA_EXTENSIONS:
                findings.append(f"ui_component_contract.runtime_evidence[{index}] must be an image or recording: {value}")

    raster_quality = contract.get("raster_quality")
    if raster_quality is not None and not isinstance(raster_quality, dict):
        findings.append("ui_component_contract.raster_quality must be an object")

    forbidden = re.compile(r"(?:solid\s+colou?r|flat\s+colou?r|colour\s*block|color\s*block|simple\s+line|line\s*art|纯色|色块|简易线条|线条拼接)", re.I)
    rich_markers = re.compile(r"(?:texture|material|lighting|light|depth|layer|image|illustration|scene|gradient|translucent|photo|纹理|材质|光影|景深|层次|图片|插画|场景|渐变|半透明)", re.I)
    # Scan only files that are declared as visual/runtime consumers. Scanning
    # every Dart helper would mistake a theme token or a non-visual utility
    # for a page that is actually rendered as flat geometry.
    runtime_paths = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        source = surface.get("source")
        if isinstance(source, str) and source.strip():
            candidate = (root / source).resolve()
            if is_within(candidate, root) and candidate.is_file():
                runtime_paths.add(candidate)
        background = surface.get("background")
        if isinstance(background, dict):
            implementations = background.get("implementation", [])
            if isinstance(implementations, list):
                for value in implementations:
                    if isinstance(value, str) and value.strip():
                        candidate = (root / value).resolve()
                        if is_within(candidate, root) and candidate.is_file():
                            runtime_paths.add(candidate)
    for component in components:
        if not isinstance(component, dict):
            continue
        value = component.get("actual_consumer")
        if isinstance(value, str) and value.strip():
            candidate = (root / value).resolve()
            if is_within(candidate, root) and candidate.is_file():
                runtime_paths.add(candidate)
    if (root / "AppListing/welcome.html").is_file():
        runtime_paths.add(root / "AppListing/welcome.html")
    if (root / "AppListing/site").is_dir():
        runtime_paths.update(path for path in (root / "AppListing/site").glob("*.html") if path.is_file())

    flat_only_hits = []
    for runtime_path in sorted(runtime_paths):
        source = runtime_path.read_text(encoding="utf-8", errors="replace")
        has_flat = any(re.search(pattern, source, re.I | re.M | re.S) for pattern in NON_GAME_FLAT_RENDER_MARKERS)
        has_rich = any(re.search(pattern, source, re.I | re.M | re.S) for pattern in NON_GAME_RICH_RENDER_MARKERS)
        if has_flat and not has_rich:
            flat_only_hits.append(runtime_path)
    if flat_only_hits:
        names = ", ".join(path.relative_to(root).as_posix() for path in flat_only_hits[:4])
        findings.append(
            "non-game runtime surface contains only flat geometric drawing without an authored image/material/texture consumer: "
            f"{names}; line maps, color-block charts and hand-drawn placeholders are forbidden"
        )
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        surface_id = surface.get("id", "?")
        background = surface.get("background") if isinstance(surface.get("background"), dict) else {}
        treatment = background.get("visual_treatment")
        if not isinstance(treatment, str) or not treatment.strip():
            findings.append(f"{surface_id}: non-game background.visual_treatment must describe an authored layered treatment")
            continue
        if forbidden.search(treatment):
            findings.append(f"{surface_id}: visual treatment contains forbidden flat/simple visual language")
        if len(rich_markers.findall(treatment)) < 2:
            findings.append(f"{surface_id}: visual treatment must describe at least two rich material/image/depth qualities")


def _validate_background_provenance(background: dict, surface_id: str, findings: list[str]) -> None:
    """Require an auditable third-party-first acquisition decision for every page image."""
    provenance = background.get("asset_provenance")
    label = f"{surface_id}: background.asset_provenance"
    if not isinstance(provenance, dict):
        findings.append(f"{label} is required; record third-party search before image generation")
        return
    order = provenance.get("acquisition_order")
    if not isinstance(order, list) or not order or order[0] != "third_party_search":
        findings.append(f"{label}.acquisition_order must begin with third_party_search")
    elif "image_generation" in order and order.index("image_generation") < order.index("third_party_search"):
        findings.append(f"{label}.acquisition_order must try third-party sources before image generation")

    search = provenance.get("third_party_search")
    if not isinstance(search, dict):
        findings.append(f"{label}.third_party_search is required for every page background")
        search = {}
    if search.get("attempted") is not True:
        findings.append(f"{label}.third_party_search.attempted must be true")
    sources = search.get("sources")
    if not isinstance(sources, list) or not sources or any(
        not isinstance(value, str) or not re.match(r"https?://", value, re.I) for value in sources
    ):
        findings.append(f"{label}.third_party_search.sources must list at least one free-resource website URL")
    for key in ("query", "license_or_usage", "reason"):
        if not isinstance(search.get(key), str) or not search[key].strip():
            findings.append(f"{label}.third_party_search.{key} is required")
    if search.get("free_access") is not True:
        findings.append(f"{label}.third_party_search.free_access must be true for a freely obtainable asset")
    result = search.get("result")
    if result not in {"selected", "no_suitable", "failed"}:
        findings.append(f"{label}.third_party_search.result must be selected, no_suitable or failed")

    selected = provenance.get("selected_source")
    if selected not in {"third_party", "generated"}:
        findings.append(f"{label}.selected_source must be third_party or generated")
    generation = provenance.get("generation")
    if not isinstance(generation, dict):
        findings.append(f"{label}.generation is required")
        generation = {}
    used = generation.get("used")
    if not isinstance(used, bool):
        findings.append(f"{label}.generation.used must be boolean")
    if selected == "third_party":
        if result != "selected":
            findings.append(f"{label}: selected third-party background requires third_party_search.result=selected")
        if used is not False:
            findings.append(f"{label}: image generation must not replace a selected free third-party asset")
    if selected == "generated":
        if result not in {"no_suitable", "failed"}:
            findings.append(f"{label}: generated background requires an unsuccessful/no-suitable third-party search")
        if used is not True:
            findings.append(f"{label}.generation.used must be true when selected_source=generated")
        for key in ("provider_url", "prompt", "task_ids", "evidence"):
            value = generation.get(key)
            if key in {"task_ids", "evidence"}:
                if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                    findings.append(f"{label}.generation.{key} must be a non-empty list")
            elif not isinstance(value, str) or not value.strip():
                findings.append(f"{label}.generation.{key} is required when image generation is used")
        if isinstance(generation.get("provider_url"), str) and not re.match(r"https?://", generation["provider_url"], re.I):
            findings.append(f"{label}.generation.provider_url must be an HTTP(S) image-generation website")


def _validate_dynamic_effects(root: Path, surface: dict, findings: list[str]) -> None:
    """Validate per-page, native-first motion contracts for Flutter surfaces."""
    surface_id = surface.get("id", "?")
    effects = surface.get("dynamic_effects")
    label = f"{surface_id}: dynamic_effects"
    if not isinstance(effects, list) or len(effects) < 2:
        findings.append(f"{label} must contain at least two distinct theme-related effects")
        return
    ids = set()
    triggers = set()
    forms = set()
    for index, effect in enumerate(effects):
        item_label = f"{label}[{index}]"
        if not isinstance(effect, dict):
            findings.append(f"{item_label} must be an object")
            continue
        for key in ("id", "trigger", "implementation_mode", "curve", "visual_form", "reduce_motion", "lifecycle"):
            if not isinstance(effect.get(key), str) or not effect[key].strip():
                findings.append(f"{item_label}.{key} is required")
        effect_id = effect.get("id")
        if isinstance(effect_id, str):
            if effect_id in ids:
                findings.append(f"{label} contains duplicate effect id: {effect_id}")
            ids.add(effect_id)
        trigger = effect.get("trigger")
        if isinstance(trigger, str):
            triggers.add(trigger)
        form = effect.get("visual_form")
        if isinstance(form, str):
            forms.add(form.casefold())
            if FORBIDDEN_MOTION_FORMS.search(form):
                findings.append(f"{item_label}.visual_form cannot be a simple gradient, flat block or static placeholder")
        implementation_mode = effect.get("implementation_mode")
        if implementation_mode not in {"flutter_native", "third_party"}:
            findings.append(f"{item_label}.implementation_mode must be flutter_native or third_party")
        implementation = effect.get("implementation")
        implementation_paths = []
        if not isinstance(implementation, list) or not implementation:
            findings.append(f"{item_label}.implementation must list executable project files")
        else:
            for value in implementation:
                path = local_contract_file(root, value, f"{item_label}.implementation", findings)
                if path is not None:
                    implementation_paths.append(path)
        markers = effect.get("runtime_markers")
        if not isinstance(markers, list) or not markers or any(not isinstance(marker, str) or not marker.strip() for marker in markers):
            findings.append(f"{item_label}.runtime_markers must list actual runtime calls")
        elif implementation_paths:
            source = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in implementation_paths)
            missing = [marker for marker in markers if marker not in source]
            if missing:
                findings.append(f"{item_label}.runtime_markers are not consumed by implementation: {', '.join(missing)}")
        native_apis = effect.get("native_apis")
        if implementation_mode == "flutter_native":
            if not isinstance(native_apis, list) or not native_apis:
                findings.append(f"{item_label}.native_apis must list Flutter SDK animation/drawing APIs")
            elif not any(api in NATIVE_FLUTTER_MOTION_APIS for api in native_apis if isinstance(api, str)):
                findings.append(f"{item_label}.native_apis must include a Flutter-native animation/drawing API")
        else:
            for key in ("third_party_name", "third_party_version", "third_party_license/source", "third_party_reason"):
                if not isinstance(effect.get(key), str) or not effect[key].strip():
                    findings.append(f"{item_label}.{key} is required only when native Flutter cannot provide the effect")
        duration = effect.get("duration_ms")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            findings.append(f"{item_label}.duration_ms must be a positive number")
        parameters = effect.get("parameters")
        if not isinstance(parameters, dict) or not parameters:
            findings.append(f"{item_label}.parameters must contain numeric effect parameters")
        elif not any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in parameters.values()):
            findings.append(f"{item_label}.parameters must include at least one numeric parameter")
        evidence = effect.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(f"{item_label}.evidence must list current iPhone before/active/result recording evidence")
        else:
            paths = [local_contract_file(root, value, f"{item_label}.evidence", findings) for value in evidence]
            if not any(path is not None and path.suffix.lower() in MOTION_RECORDING_EXTENSIONS for path in paths):
                findings.append(f"{item_label}.evidence must include an iPhone .mp4 or .mov recording")
    if len(triggers) < 2 and len(forms) < 2:
        findings.append(f"{label} must contain two semantically different triggers or visual forms")
    if not any(re.search(r"(?:tap|press|click|gesture|drag|swipe|select)", trigger, re.I) for trigger in triggers):
        findings.append(f"{label} must include at least one real tap/press/gesture interaction trigger")


def local_contract_file(root: Path, value, label: str, findings: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        findings.append(f"{label}: expected a project-relative file path")
        return None
    relative = Path(value)
    candidate = (root / relative).resolve()
    if relative.is_absolute() or not is_within(candidate, root):
        findings.append(f"{label}: path must stay inside project: {value}")
        return None
    if not candidate.is_file() or candidate.stat().st_size == 0:
        findings.append(f"{label}: missing or empty file: {value}")
        return None
    return candidate


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
    project_type = ledger.get("project_type")
    if project_type not in {"non_game", "mixed", "game"}:
        findings.append("project_type is required and must be non_game, mixed, or game")
    # The design-system gate is unconditional for every real visual ledger.
    # Requiring an explicit type prevents an incomplete or malformed ledger
    # from bypassing the hard UI quality chain by omitting project_type.
    findings.extend(validate_design_system_contract(root, ledger))
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
    validate_non_game_ui_contract(root, ledger, surfaces, findings)
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
    raster_quality_missing_reported = False
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
        standalone_welcome = bool(path and path == root / "AppListing/welcome.html"
                                  and surface.get("kind") == "html")

        background = surface.get("background")
        if not isinstance(background, dict):
            findings.append(f"{surface_id}: missing background record")
            continue
        if surface.get("kind") in {"flutter", "html"}:
            _validate_background_provenance(background, surface_id, findings)
            if surface.get("kind") == "flutter":
                _validate_dynamic_effects(root, surface, findings)
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
            if project_type in {"non_game", "mixed"}:
                component_contract = ledger.get("ui_component_contract")
                component_quality = component_contract.get("raster_quality") if isinstance(component_contract, dict) else None
                surface_quality = background.get("raster_quality")
                quality = component_quality if isinstance(component_quality, dict) else surface_quality
                if not isinstance(quality, dict):
                    if not raster_quality_missing_reported:
                        findings.append(
                            "ui_component_contract.raster_quality is required for non-game and mixed image assets"
                        )
                        raster_quality_missing_reported = True
                else:
                    for key, minimum, maximum in (
                        ("minimum_width", 32, None),
                        ("minimum_height", 32, None),
                        ("minimum_unique_colors", 16, None),
                        ("maximum_dominant_color_ratio", None, 0.88),
                        ("minimum_opaque_coverage", 0.12, 1.0),
                        ("minimum_texture_variation", 0.02, None),
                    ):
                        value = quality.get(key)
                        if isinstance(value, bool) or not isinstance(value, (int, float)):
                            findings.append(f"ui_component_contract.raster_quality.{key} must be numeric")
                        elif minimum is not None and value < minimum:
                            findings.append(f"ui_component_contract.raster_quality.{key} must be >= {minimum:g}")
                        elif maximum is not None and value > maximum:
                            findings.append(f"ui_component_contract.raster_quality.{key} must be <= {maximum:g}")
                    validate_raster_quality(background_path, f"surface {surface_id} background", quality, findings)
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
                    if resource and (is_within(resource, root / ".codex-work") or is_within(resource, root / "AppListing")):
                        findings.append(f"{surface_id}: background resources must be bundled project assets: {value}")
            if surface.get("kind") == "flutter":
                recording = local_file(background.get("recording"), f"surface {surface_id} background motion recording")
                if recording and recording.suffix.lower() not in {".mp4", ".mov"}:
                    findings.append(f"{surface_id}: background needs an iPhone motion recording file")
        # Bright gradient treatment is a hard visual requirement. Every
        # inventoried surface must expose at least one named gradient token;
        # the runtime gate below still requires the actual implementation and
        # current-iPhone evidence, so metadata alone cannot certify the result.
        gradient_tokens = background.get("gradient_tokens")
        if not isinstance(gradient_tokens, list) or not gradient_tokens or any(
            not isinstance(value, str) or not value.strip() for value in gradient_tokens
        ):
            findings.append(f"{surface_id}: gradient_tokens must list at least one nonempty gradient token")
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
    expected_sources += [root / "AppListing/welcome.html"] if (root / "AppListing/welcome.html").is_file() else []
    expected_sources += list((root / "AppListing/site").glob("*.html"))
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
        if gate == "gradients" and exclusions:
            findings.append("gradients: hard requirement cannot be excluded for any surface")
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

    # Typography and gradient tokens must be declared and consumed.
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
