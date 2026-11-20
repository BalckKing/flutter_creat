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
from collections import Counter
import hashlib
import json
import math
import re
import struct
import sys
import zlib
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
RUNTIME_ASSET_MARKERS = (
    r"\b(?:Image\.asset|AssetImage|drawImage|drawImageRect|SpriteComponent|SpriteBatch|Texture|TextureRect|"
    r"ImageComponent|MeshInstance|TexturedModel|Material|Shader|Rive|Lottie|loadSprite|loadTexture|"
    r"Texture2D|StandardMaterial3D|Sprite2D|Sprite3D)\b",
)
FLAT_RENDER_MARKERS = (
    r"\b(?:drawRect|drawLine|drawPath|ColoredBox|Container\s*\([^\n]*\bcolor\s*:|solidColor|flatColor)\b",
)
RICH_RENDER_MARKERS = (
    r"\b(?:drawImage|drawImageRect|Image\.asset|AssetImage|Sprite|Texture|Material|Shader|Gradient|"
    r"BackdropFilter|Rive|Lottie|Particle|Mesh|PBR|shadow|occlusion|parallax)\b",
)
DEFAULT_RASTER_QUALITY = {
    "minimum_width": 32,
    "minimum_height": 32,
    "minimum_unique_colors": 16,
    "maximum_dominant_color_ratio": 0.88,
    "minimum_opaque_coverage": 0.12,
    "minimum_texture_variation": 0.02,
}


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


def _png_samples(path: Path, *, max_side: int = 256) -> tuple[int, int, list[tuple[int, int, int, int]]] | None:
    """Decode the common 8-bit PNG forms without making Pillow mandatory.

    Generated game assets are commonly PNGs.  The fallback decoder keeps this
    source gate portable and lets it inspect pixels even when the optional
    Pillow package is unavailable.  Unsupported PNG variants are rejected by
    the caller instead of silently bypassing the visual-quality gate.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        return None
    position = len(signature)
    width = height = bit_depth = color_type = None
    palette: list[tuple[int, int, int]] = []
    transparency: list[int] = []
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
    channel_count = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    row_bytes = width * channel_count
    try:
        decoded = zlib.decompress(bytes(compressed))
    except zlib.error:
        return None
    expected = height * (row_bytes + 1)
    if len(decoded) < expected:
        return None
    rows: list[bytes] = []
    offset = 0
    previous = bytearray(row_bytes)
    for _ in range(height):
        filter_type = decoded[offset]
        raw = bytearray(decoded[offset + 1:offset + 1 + row_bytes])
        offset += row_bytes + 1
        if filter_type not in {0, 1, 2, 3, 4}:
            return None
        reconstructed = bytearray(row_bytes)
        for index, value in enumerate(raw):
            left = reconstructed[index - channel_count] if index >= channel_count else 0
            up = previous[index]
            up_left = previous[index - channel_count] if index >= channel_count else 0
            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 0xff
            elif filter_type == 2:
                result = (value + up) & 0xff
            elif filter_type == 3:
                result = (value + ((left + up) // 2)) & 0xff
            else:
                estimate = left + up - up_left
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                result = (value + predictor) & 0xff
            reconstructed[index] = result
        rows.append(bytes(reconstructed))
        previous = reconstructed

    step_x = max(1, math.ceil(width / max_side))
    step_y = max(1, math.ceil(height / max_side))
    samples: list[tuple[int, int, int, int]] = []
    for y in range(0, height, step_y):
        row = rows[y]
        for x in range(0, width, step_x):
            start = x * channel_count
            values = row[start:start + channel_count]
            if color_type == 0:
                gray = values[0]
                alpha = 0 if transparency and gray == int.from_bytes(bytes(transparency[:2]), "big") else 255
                samples.append((gray, gray, gray, alpha))
            elif color_type == 2:
                alpha = 255
                if transparency and len(transparency) >= 6:
                    alpha = 0 if tuple(values) == tuple(int.from_bytes(bytes(transparency[i:i + 2]), "big") for i in (0, 2, 4)) else 255
                samples.append((values[0], values[1], values[2], alpha))
            elif color_type == 3:
                palette_index = values[0]
                if palette_index >= len(palette):
                    return None
                red, green, blue = palette[palette_index]
                alpha = transparency[palette_index] if palette_index < len(transparency) else 255
                samples.append((red, green, blue, alpha))
            elif color_type == 4:
                samples.append((values[0], values[0], values[0], values[1]))
            else:
                samples.append((values[0], values[1], values[2], values[3]))
    return int(width), int(height), samples


def _image_samples(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]]] | None:
    """Return bounded pixel samples using Pillow when available, PNG fallback otherwise."""
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        Image = None  # type: ignore
    if Image is not None:
        try:
            with Image.open(path) as image:
                width, height = image.size
                image = image.convert("RGBA")
                image.thumbnail((256, 256))
                pixel_data = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
                return width, height, list(pixel_data)
        except Exception:
            pass
    return _png_samples(path)


def _raster_metrics(path: Path) -> dict[str, float] | None:
    decoded = _image_samples(path)
    if decoded is None:
        return None
    width, height, samples = decoded
    if not samples:
        return None
    quantized = [(red // 16, green // 16, blue // 16, alpha // 32) for red, green, blue, alpha in samples]
    counts = Counter(quantized)
    dominant_ratio = max(counts.values()) / len(samples)
    opaque = sum(1 for _, _, _, alpha in samples if alpha > 0) / len(samples)
    luminance = [0.2126 * red + 0.7152 * green + 0.0722 * blue for red, green, blue, _ in samples]
    # Samples are row-major after thumbnailing.  A one-dimensional gradient
    # proxy still catches flat blocks and simple line drawings without needing
    # to retain a second full image buffer.
    side = max(1, int(round(math.sqrt(len(samples)))))
    variation = 0.0
    comparisons = 0
    edge_count = 0
    for index in range(1, len(luminance)):
        delta = abs(luminance[index] - luminance[index - 1]) / 255.0
        variation += delta
        comparisons += 1
        if delta >= 0.16:
            edge_count += 1
    texture_variation = variation / max(1, comparisons)
    edge_density = edge_count / max(1, comparisons)
    return {
        "width": float(width),
        "height": float(height),
        "unique_colors": float(len(counts)),
        "dominant_color_ratio": dominant_ratio,
        "opaque_coverage": opaque,
        "texture_variation": texture_variation,
        "edge_density": edge_density,
        "sample_count": float(len(samples)),
        "sample_side": float(side),
    }


def _validate_raster_asset(path: Path, label: str, quality: Mapping[str, Any], findings: list[str]) -> None:
    if path.suffix.casefold() not in IMAGE_SUFFIXES:
        return
    metrics = _raster_metrics(path)
    if metrics is None:
        findings.append(f"{label}: raster quality cannot be inspected; use a decodable authored image, not a placeholder or line-art bypass")
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
            findings.append(
                f"{label}: fails raster quality ({description} {actual:.4f} {operator} {float(expected):.4f}); "
                "simple line art, solid color blocks and flat geometry are forbidden"
            )
    line_like = (
        metrics["unique_colors"] <= max(8.0, float(quality.get("minimum_unique_colors", 16)) / 2.0)
        and metrics["edge_density"] >= 0.01
        and metrics["dominant_color_ratio"] >= 0.45
    )
    if line_like:
        findings.append(f"{label}: raster appears to be simple line art rather than a textured scene asset")


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
    quality = _mapping(visual.get("raster_quality") if isinstance(visual, Mapping) else None, "visual_system.raster_quality", findings)
    if quality is not None:
        for key, minimum, maximum in (
            ("minimum_width", 32, None),
            ("minimum_height", 32, None),
            ("minimum_unique_colors", 16, None),
            ("maximum_dominant_color_ratio", None, 0.88),
            ("minimum_opaque_coverage", 0.12, 1.0),
            ("minimum_texture_variation", 0.02, None),
        ):
            _numeric(quality, key, "visual_system.raster_quality", findings, minimum=minimum, maximum=maximum)
    offline = _list(pipeline.get("offline_assets"), "asset_pipeline.offline_assets", findings, minimum=3)
    offline_paths: set[str] = set()
    for index, value in enumerate(offline):
        path = _file_path(root, value, f"asset_pipeline.offline_assets[{index}]", findings)
        if path is not None:
            offline_paths.add(path.relative_to(root).as_posix())
            if quality is not None:
                _validate_raster_asset(path, f"asset_pipeline.offline_assets[{index}]", quality, findings)
    for key in ("layers", "occlusion_order", "load_entrypoints"):
        _list(pipeline.get(key), f"asset_pipeline.{key}", findings, minimum=3 if key == "layers" else 1)
    entrypoints = pipeline.get("load_entrypoints")
    entrypoint_sources: list[str] = []
    if isinstance(entrypoints, list):
        for index, value in enumerate(entrypoints):
            entrypoint_value = value.split(":", 1)[0] if isinstance(value, str) else value
            entrypoint = _file_path(root, entrypoint_value, f"asset_pipeline.load_entrypoints[{index}]", findings)
            if entrypoint is not None:
                try:
                    entrypoint_sources.append(entrypoint.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    runtime_text = "\n".join(entrypoint_sources)
    if entrypoint_sources and not any(re.search(pattern, runtime_text, re.I | re.M) for pattern in RUNTIME_ASSET_MARKERS):
        findings.append(
            "asset_pipeline.load_entrypoints must contain a real image/material/texture consumer; "
            "a Canvas made only from lines or solid color blocks cannot satisfy the game visual contract"
        )
    if entrypoint_sources and any(re.search(pattern, runtime_text, re.I | re.M) for pattern in FLAT_RENDER_MARKERS):
        if not any(re.search(pattern, runtime_text, re.I | re.M) for pattern in RICH_RENDER_MARKERS):
            findings.append(
                "asset_pipeline.load_entrypoints contains only flat geometric rendering; "
                "add authored image/material/texture consumers and reject line/color-block-only scenes"
            )
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
            if quality is not None:
                _validate_raster_asset(path, f"asset_pipeline.assets[{index}].path", quality, findings)
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
