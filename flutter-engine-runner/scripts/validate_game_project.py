#!/usr/bin/env python3
"""Run a source-only game runtime preflight for a Flutter project.

The checker deliberately never builds or launches the target application.  It
checks the structural contract before a real iPhone run: an explicit decision
about whether a dedicated engine is needed, real runtime ownership, authored
local scene assets, a playable vertical slice, and current-device evidence.
The iPhone Simulator run remains the final acceptance authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


MANIFEST_PATH = Path(".codex-work/game-engine.json")
RUNTIME_EVIDENCE_PATH = Path(".codex-work/game-runtime.json")
TEXT_EXTENSIONS = {
    ".dart", ".yaml", ".yml", ".json", ".swift", ".m", ".mm", ".h", ".gd",
    ".tscn", ".godot", ".unity", ".cs", ".shader", ".asmdef", ".pbxproj", ".xcconfig", ".xml", ".plist", ".md",
    ".txt", ".html", ".defold", ".scene", ".world", ".js", ".ts", ".tsx",
    ".c", ".cc", ".cpp", ".cxx", ".hpp", ".rs", ".kt", ".java",
}
EXCLUDED_DIRS = {".git", ".dart_tool", "build", "Pods", ".symlinks", ".codex-work"}
SEMVER = re.compile(r"(?<!\d)(\d+\.\d+(?:\.\d+)?)(?!\d)")
VISUAL_MODES = {"2.5d", "3d"}


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_relative(root: Path, value: Any, label: str, findings: list[str], *, allow_work: bool = False) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        findings.append(f"{label}: expected a project-relative file path")
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        findings.append(f"{label}: path must stay inside project: {value}")
        return None
    resolved = (root / candidate).resolve()
    if not _is_within(resolved, root):
        findings.append(f"{label}: path must stay inside project: {value}")
        return None
    if not allow_work and (candidate.parts and candidate.parts[0] == ".codex-work"):
        findings.append(f"{label}: scene asset cannot live in .codex-work bundled evidence directory: {value}")
        return None
    # A symlink can escape after the resolve check; reject it even if it currently
    # resolves below the root so a later replacement cannot change the contract.
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            findings.append(f"{label}: symlink paths are not accepted: {value}")
            return None
    return resolved


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in parts):
            continue
        yield path


def _strip_comments(text: str) -> str:
    """Remove ordinary source comments before runtime-token checks.

    This is intentionally conservative; it is not a language parser.  It keeps
    quoted strings, which are useful for paths and method-channel names, while
    preventing a prose comment from satisfying an engine gate.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"(^|\s)//[^\n]*", r"\1", text)
    text = re.sub(r"(^|\s)#[^\n]*", r"\1", text)
    return text


def _source_text(root: Path) -> tuple[str, dict[Path, str]]:
    by_path: dict[Path, str] = {}
    for path in _iter_text_files(root):
        try:
            by_path[path] = _strip_comments(_read(path))
        except OSError:
            continue
    return "\n".join(by_path.values()), by_path


def _find_dependency(pubspec: str, package: str) -> str | None:
    # A conservative indentation-aware read is enough for pubspec dependency
    # declarations and avoids executing or importing a YAML implementation.
    in_section = False
    section_indent = 0
    for line in pubspec.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0 and stripped.rstrip(":") in {"dependencies", "dev_dependencies"}:
            in_section = True
            section_indent = indent
            continue
        if in_section and indent <= section_indent and stripped.endswith(":"):
            in_section = False
            continue
        if in_section:
            match = re.match(rf"^{re.escape(package)}\s*:\s*(.*?)\s*$", stripped)
            if match:
                return match.group(1).strip().strip('"\'')
    return None


def _version(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = SEMVER.search(value)
    return match.group(1) if match else None


def _manifest(root: Path, findings: list[str]) -> dict[str, Any] | None:
    """Read the manifest without assuming that a game needs an engine.

    The implementation decision is validated later because native Flutter games
    deliberately have ``engine: null`` and a different runtime contract.
    """
    path = root / MANIFEST_PATH
    if not path.is_file():
        findings.append(f"missing {MANIFEST_PATH.as_posix()}")
        return None
    try:
        value = json.loads(_read(path))
    except (OSError, ValueError) as error:
        findings.append(f"invalid {MANIFEST_PATH.as_posix()}: {error}")
        return None
    if not isinstance(value, dict):
        findings.append("game-engine.json must contain an object")
        return None
    project_type = value.get("project_type")
    if project_type not in {"game", "mixed"}:
        findings.append("game-engine.json project_type must be 'game' or 'mixed'")
    visual_mode = value.get("visual_mode")
    if not isinstance(visual_mode, str) or visual_mode.strip().casefold() not in VISUAL_MODES:
        findings.append("game-engine.json visual_mode must be '2.5d' or '3d' for every game or mixed project")
    return value


def _implementation_decision(manifest: Mapping[str, Any], findings: list[str]) -> tuple[str | None, bool | None, str | None]:
    """Resolve and validate the explicit engine-necessity decision.

    ``flutter_native`` is the canonical spelling in the workflow documents;
    ``flutter-native`` and ``native_flutter`` are accepted compatibility aliases.
    A nested ``decision`` object is accepted only when it carries the same
    explicit fields and does not conflict with top-level values.
    """
    decision = manifest.get("decision")
    if decision is not None and not isinstance(decision, dict):
        findings.append("game-engine.json decision must be an object when provided")
        decision = {}
    decision = decision if isinstance(decision, dict) else {}

    def choose(field: str, *aliases: str) -> Any:
        top = manifest.get(field)
        nested = decision.get(field)
        if field == "decision_reason":
            nested = decision.get("reason", decision.get("decision_reason"))
        if top is not None and nested is not None and top != nested:
            findings.append(f"game-engine.json {field} conflicts with decision.{field}")
        if top is not None:
            return top
        if nested is not None:
            return nested
        for alias in aliases:
            if manifest.get(alias) is not None:
                return manifest.get(alias)
            if decision.get(alias) is not None:
                return decision.get(alias)
        return None

    raw_mode = choose("implementation_mode")
    if not isinstance(raw_mode, str) or not raw_mode.strip():
        findings.append("game-engine.json implementation_mode decision is required")
        mode = None
    else:
        mode_aliases = {
            "engine": "engine",
            "flutter_native": "flutter-native",
            "flutter-native": "flutter-native",
            "native_flutter": "flutter-native",
        }
        mode = mode_aliases.get(raw_mode.strip().lower())
        if mode is None:
            findings.append("game-engine.json implementation_mode must be engine or flutter_native")

    raw_required = choose("engine_required")
    if not isinstance(raw_required, bool):
        findings.append("game-engine.json engine_required must be a boolean")
        required = None
    else:
        required = raw_required

    reason = choose("decision_reason")
    if not isinstance(reason, str) or not reason.strip():
        findings.append("game-engine.json decision_reason must explain why the engine is or is not required")
        reason_value = None
    else:
        reason_value = reason

    if mode is not None and required is not None and required != (mode == "engine"):
        findings.append("game-engine.json implementation_mode and engine_required disagree")
    elif mode is None and required is not None:
        findings.append("game-engine.json engine_required cannot be interpreted without implementation_mode")
    return mode, required, reason_value


def _merged_engine_contract(manifest: Mapping[str, Any], findings: list[str]) -> dict[str, Any] | None:
    """Return the engine route contract with documented runtime aliases merged."""
    engine = manifest.get("engine")
    if not isinstance(engine, dict):
        findings.append("engine mode requires a nonempty engine object")
        return None
    merged = dict(engine)
    runtime = manifest.get("runtime")
    runtime = runtime if isinstance(runtime, dict) else {}
    for key in ("entrypoint", "scene_assets", "runtime_owner", "native_bridge"):
        if merged.get(key) in (None, "", []):
            if runtime.get(key) not in (None, "", []):
                merged[key] = runtime[key]
    for key in ("build_commands", "evidence"):
        if merged.get(key) in (None, "", []):
            if manifest.get(key) not in (None, "", []):
                merged[key] = manifest[key]
            elif runtime.get(key) not in (None, "", []):
                merged[key] = runtime[key]
    return merged


def _native_runtime_contract(manifest: Mapping[str, Any], findings: list[str]) -> dict[str, Any] | None:
    """Resolve the native Flutter runtime contract and documented aliases."""
    if manifest.get("engine") not in (None, {}):
        findings.append("flutter-native mode must leave engine absent or null")
    runtime = manifest.get("native_runtime")
    if runtime is None:
        runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        findings.append("flutter-native mode requires a native_runtime object")
        return None
    merged = dict(runtime)
    if merged.get("animation_effects") in (None, "", []):
        merged["animation_effects"] = merged.get("animation_effect_catalog")
    if merged.get("formula_record") in (None, "", []):
        merged["formula_record"] = merged.get("prompt_formula")
    if merged.get("evidence") in (None, "", []):
        merged["evidence"] = manifest.get("evidence")
    return merged


def _require_entrypoints(root: Path, values: Any, findings: list[str], label: str) -> list[Path]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list) or not values:
        findings.append(f"{label}: expected a nonempty list of project-relative entrypoints")
        return []
    paths: list[Path] = []
    for index, value in enumerate(values):
        path = _safe_relative(root, value, f"{label}[{index}]", findings)
        if path is None:
            continue
        if not path.is_file():
            findings.append(f"{label}[{index}]: missing entrypoint: {value}")
            continue
        paths.append(path)
    return paths


def _validate_native_runtime(root: Path, manifest: Mapping[str, Any],
                             files: Mapping[Path, str], findings: list[str]) -> None:
    runtime = _native_runtime_contract(manifest, findings)
    if runtime is None:
        return
    entry_paths = _require_entrypoints(root, runtime.get("entrypoint"), findings, "native_runtime.entrypoint")
    _require_asset_paths(root, runtime.get("scene_assets"), findings, "native_runtime.scene_assets")
    owner = runtime.get("runtime_owner")
    if not isinstance(owner, str) or len(owner.strip()) < 12:
        findings.append("native_runtime.runtime_owner must describe Flutter-owned scene, state, input, update, rules, results and restart")
    else:
        owner_text = owner.casefold()
        owner_markers = {
            "scene": r"\bscene\b|场景",
            "state": r"\bstate\b|状态",
            "input": r"\binput\b|输入",
            "update": r"\bupdate\b|更新",
            "rules": r"\brules?\b|规则",
            "result": r"\bresults?\b|结果",
            "restart": r"\brestart\b|重开|重置",
        }
        missing_owner = [name for name, pattern in owner_markers.items()
                         if not re.search(pattern, owner_text, re.I)]
        if missing_owner:
            findings.append(
                "native_runtime.runtime_owner must explicitly assign Flutter ownership for: "
                + ", ".join(missing_owner)
            )
    bridge = runtime.get("native_bridge")
    if bridge not in (None, "", "null", "not applicable"):
        findings.append("flutter-native native_runtime.native_bridge must be null or not applicable")

    effects = runtime.get("animation_effects")
    if not isinstance(effects, list) or not effects or not all(isinstance(item, str) and item.strip() for item in effects):
        findings.append("native_runtime.animation_effects must list selected animation/effect tools")
    else:
        catalog_text = " ".join(effects).casefold()
        known = ("rive", "flame", "flutter_animate", "lottie", "fragment", "shader", "confetti", "particle", "custompainter", "animationcontroller", "pathmetric", "backdropfilter", "blendmode", "ticker", "matrix4")
        if not any(token in catalog_text for token in known):
            findings.append("native_runtime.animation_effects must identify a known animation/effect tool or explicit native primitive")

    formula = runtime.get("formula_record")
    if not isinstance(formula, str) or not formula.strip():
        findings.append("native_runtime.formula_record must point to the six-part motion formula record")
    else:
        formula_path = _safe_relative(root, formula, "native_runtime.formula_record", findings, allow_work=True)
        if formula_path is not None:
            if not formula_path.is_file() or formula_path.stat().st_size == 0:
                findings.append(f"native_runtime.formula_record: missing or empty file: {formula}")
            else:
                formula_text = _read(formula_path).casefold()
                formula_markers = (
                    "主题", "主体", "前", "中", "后", "运动", "轨迹", "触发",
                    "技术", "实现", "参数", "时间", "cycle", "end", "interruption",
                    "lifecycle", "reduce motion", "负面", "negative",
                )
                numbered_parts = len(re.findall(r"(?:^|\n)\s*(?:[1-6][.)]|(?:part|section)\s*[1-6])", formula_text, re.I))
                if sum(marker in formula_text for marker in formula_markers) < 6 and numbered_parts < 6:
                    findings.append("native_runtime.formula_record must contain the six-part motion formula and lifecycle constraints")

    evidence = runtime.get("evidence")
    _require_evidence_paths(root, evidence, findings, label="native_runtime.evidence")
    runtime_text = _runtime_dart_text(root, files)
    if entry_paths and not any(path in files and files[path].strip() for path in entry_paths):
        findings.append("native_runtime.entrypoint must contain a nonempty Dart runtime implementation")
    _require_token(runtime_text, [r"\b(?:GestureDetector|Listener|InkWell|onTap|onTapUp|onTapDown|handleInput|applyMove|advanceTurn|onPan|PointerDownEvent)\b"], "input", findings)
    _require_token(runtime_text, [r"\b(?:updateRules|update_rules|applyMove|advanceTurn|nextTurn|notifyListeners|ValueNotifier|ChangeNotifier|setState\s*\()\b"], "rule/update", findings)
    _require_token(runtime_text, [r"\b(?:success|succeed|won|win|failure|fail|lost|lose|gameResult|result)\b"], "success/failure result", findings)
    _require_token(runtime_text, [r"\b(?:restart|reset|replay|playAgain|newGame)\s*\("], "restart path", findings)
    _require_token(runtime_text, [r"\b(?:HUD|Hud|feedback|showSuccess|showFailure|Score|resultPanel|Overlay|Text\s*\()\b"], "HUD/feedback", findings)
    _require_token(runtime_text, [r"\b(?:WidgetsBindingObserver|didChangeAppLifecycleState|AppLifecycleState|dispose\s*\(|TickerProviderStateMixin)\b"], "lifecycle handling", findings)
    dynamic_patterns = (r"AnimationController", r"CustomPainter", r"FragmentProgram", r"PathMetric", r"BlendMode", r"BackdropFilter", r"Ticker", r"Rive", r"Lottie", r"flutter_animate", r"Particle", r"Shader", r"Animation<")
    if not any(re.search(pattern, runtime_text, re.I) for pattern in dynamic_patterns):
        findings.append("native Flutter game needs a real animation/effect consumer; package installation alone is insufficient")


def _require_asset_paths(root: Path, values: Any, findings: list[str], label: str, *, minimum: int = 2) -> list[Path]:
    if not isinstance(values, list):
        findings.append(f"{label}: expected a list")
        return []
    paths: list[Path] = []
    for index, value in enumerate(values):
        path = _safe_relative(root, value, f"{label}[{index}]", findings)
        if path is None:
            continue
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"{label}[{index}]: missing or empty scene asset: {value}")
            continue
        paths.append(path)
    if len(paths) < minimum:
        findings.append(f"{label}: at least {minimum} authored local scene assets are required (subject and environment)")
    return paths


def _require_evidence_paths(root: Path, values: Any, findings: list[str], *, label: str = "engine.evidence") -> None:
    if not isinstance(values, list) or not values:
        findings.append(f"{label} must list .codex-work/game-runtime.json and related evidence")
        return
    if ".codex-work/game-runtime.json" not in values:
        findings.append(f"{label} must include .codex-work/game-runtime.json")
    for index, value in enumerate(values):
        path = _safe_relative(root, value, f"{label}[{index}]", findings, allow_work=True)
        if path is None:
            continue
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"{label}[{index}]: missing or empty file: {value}")


def _runtime_evidence(root: Path, findings: list[str]) -> dict[str, Any] | None:
    path = root / RUNTIME_EVIDENCE_PATH
    if not path.is_file():
        findings.append("missing .codex-work/game-runtime.json runtime evidence")
        return None
    try:
        record = json.loads(_read(path))
    except (OSError, ValueError) as error:
        findings.append(f"invalid .codex-work/game-runtime.json: {error}")
        return None
    if not isinstance(record, dict):
        findings.append(".codex-work/game-runtime.json must contain an object")
        return None
    for field in ("build_id", "bundle_id", "device", "os"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            findings.append(f"runtime evidence needs {field}")
    if isinstance(record.get("device"), str) and not re.search(r"\biPhone\b", record["device"], re.I):
        findings.append("runtime evidence device must identify an iPhone")
    if isinstance(record.get("os"), str) and not re.match(r"iOS\s+\d", record["os"], re.I):
        findings.append("runtime evidence os must identify an iOS version")

    def evidence_file(value: Any, label: str, extensions: set[str]) -> None:
        path_value = _safe_relative(root, value, label, findings, allow_work=True)
        if path_value is None:
            return
        if path_value.suffix.lower() not in extensions:
            findings.append(f"{label}: unexpected evidence file type: {value}")
        elif not path_value.is_file() or path_value.stat().st_size == 0:
            findings.append(f"{label}: missing or empty file: {value}")

    recording = record.get("recording")
    if not isinstance(recording, str) or not recording.strip():
        findings.append("runtime evidence requires a gameplay recording path")
    else:
        evidence_file(recording, "runtime recording", {".mp4", ".mov", ".m4v"})
    screenshots = record.get("screenshots")
    if not isinstance(screenshots, list) or not screenshots:
        findings.append("runtime evidence requires at least one iPhone screenshot")
    else:
        for index, value in enumerate(screenshots):
            evidence_file(value, f"runtime screenshot[{index}]", {".png", ".jpg", ".jpeg", ".heic"})
    logs = record.get("logs")
    if not isinstance(logs, list) or not logs:
        findings.append("runtime evidence requires at least one runtime log")
    else:
        for index, value in enumerate(logs):
            evidence_file(value, f"runtime log[{index}]", {".log", ".txt", ".json"})
    return record


def _require_token(text: str, patterns: Sequence[str], label: str, findings: list[str]) -> bool:
    if not any(re.search(pattern, text, re.I | re.M | re.S) for pattern in patterns):
        findings.append(f"vertical slice missing {label} implementation")
        return False
    return True


def _runtime_dart_text(root: Path, files: Mapping[Path, str]) -> str:
    chunks: list[str] = []
    for path, source in files.items():
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] == "lib" and path.suffix.lower() == ".dart":
            chunks.append(source)
    return "\n".join(chunks)


def _runtime_code_text(root: Path, files: Mapping[Path, str]) -> str:
    """Return implementation sources while excluding prose and work ledgers."""
    code_suffixes = {
        ".dart", ".gd", ".swift", ".m", ".mm", ".h", ".cs", ".shader", ".tscn", ".unity",
        ".defold", ".scene", ".world", ".js", ".ts", ".tsx", ".c", ".cc", ".cpp", ".cxx",
        ".hpp", ".rs", ".kt", ".java",
    }
    chunks: list[str] = []
    for path, source in files.items():
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if path.suffix.lower() in code_suffixes and ".codex-work" not in relative.parts:
            chunks.append(source)
    return "\n".join(chunks)


def _visual_contract(manifest: Mapping[str, Any], root: Path, findings: list[str]) -> dict[str, Any] | None:
    """Validate the game-wide 2.5D/3D visual contract.

    This is intentionally engine-neutral.  A game can use any suitable engine
    or third-party renderer when it declares the real camera/depth/material
    path and provides source/runtime evidence for that choice.
    """
    raw_mode = manifest.get("visual_mode")
    mode = raw_mode.strip().casefold() if isinstance(raw_mode, str) else ""
    if mode not in VISUAL_MODES:
        return None
    contract = manifest.get("visual_contract")
    if not isinstance(contract, dict):
        findings.append("game-engine.json visual_contract is required for 2.5d/3d games")
        return None

    required_text = {
        "renderer": "renderer",
        "camera_model": "camera_model",
        "materials_lighting": "materials_lighting",
        "animation_feedback": "animation_feedback",
    }
    for key, label in required_text.items():
        value = contract.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(f"visual_contract.{label} must describe the real runtime implementation")

    layers = contract.get("depth_layers")
    if not isinstance(layers, list) or len(layers) < 3 or not all(isinstance(item, str) and item.strip() for item in layers):
        findings.append("visual_contract.depth_layers must list at least background, midground and foreground")

    assets = contract.get("authored_assets")
    if not isinstance(assets, list) or len(assets) < 2:
        findings.append("visual_contract.authored_assets must list at least two authored subject/environment assets")
    else:
        for index, value in enumerate(assets):
            path = _safe_relative(root, value, f"visual_contract.authored_assets[{index}]", findings)
            if path is not None and (not path.is_file() or path.stat().st_size == 0):
                findings.append(f"visual_contract.authored_assets[{index}]: missing or empty asset: {value}")

    if contract.get("no_flat_color_blocks") is not True:
        findings.append("visual_contract.no_flat_color_blocks must be true")
    return contract


def _validate_game_lobby(root: Path, manifest: Mapping[str, Any], files: Mapping[Path, str], findings: list[str]) -> None:
    """Validate the game-only immersive lobby and its reachable flows."""
    if manifest.get("project_type") not in {"game", "mixed"}:
        return
    lobby = manifest.get("game_lobby")
    if not isinstance(lobby, dict):
        findings.append("game_lobby is required for game and mixed projects")
        return

    if lobby.get("role") != "immersive_game_lobby":
        findings.append("game_lobby.role must be immersive_game_lobby")
    if lobby.get("mode") != "immersive_portrait" or lobby.get("orientation") != "portrait":
        findings.append("game_lobby must use an immersive portrait mode and portrait orientation")
    if lobby.get("entrypoint") != "lib/welcome.dart":
        findings.append("game_lobby.entrypoint must be lib/welcome.dart; retain the file as the immersive game lobby")

    primary = lobby.get("primary_actions")
    if primary != ["Play", "Load", "Operation"]:
        findings.append("game_lobby.primary_actions must be exactly Play, Load and Operation")
    top = lobby.get("top_actions")
    if top != ["Exit", "Settings"]:
        findings.append("game_lobby.top_actions must be exactly Exit and Settings")

    expected_flows = {
        "play_flow": ["Play", "Loading", "Game"],
        "load_flow": ["Load", "Save Slot", "Game"],
    }
    for key, expected in expected_flows.items():
        if lobby.get(key) != expected:
            findings.append(f"game_lobby.{key} must be {' -> '.join(expected)}")
    controls = lobby.get("operation_controls")
    if not isinstance(controls, list) or not {"Volume", "Graphics Quality"}.issubset(controls):
        findings.append("game_lobby.operation_controls must include Volume and Graphics Quality")
    adaptation = lobby.get("performance_adaptation")
    if not isinstance(adaptation, str) or not adaptation.strip():
        findings.append("game_lobby.performance_adaptation must describe iPhone performance-tier adaptation")

    evidence = lobby.get("evidence")
    if not isinstance(evidence, list) or ".codex-work/game-lobby.json" not in evidence:
        findings.append("game_lobby.evidence must include .codex-work/game-lobby.json")
    else:
        for index, value in enumerate(evidence):
            path = _safe_relative(root, value, f"game_lobby.evidence[{index}]", findings, allow_work=True)
            if path is not None and (not path.is_file() or path.stat().st_size == 0):
                findings.append(f"game_lobby.evidence[{index}]: missing or empty file: {value}")

    entry = _safe_relative(root, lobby.get("entrypoint"), "game_lobby.entrypoint", findings)
    if entry is None or not entry.is_file():
        findings.append("game_lobby.entrypoint must point to an existing lib/welcome.dart")
    runtime_text = _runtime_dart_text(root, files)
    for label, patterns in (
        ("Play", [r"\bPlay\b", r"\bplay\s*\(", r"initializeGame"]),
        ("Loading", [r"\bLoading\b", r"showLoading", r"loading"]),
        ("Load", [r"\bLoad\b", r"\bload\s*\(", r"loadSave"]),
        ("Operation", [r"\bOperation\b", r"\boperation\s*\("] ),
        ("Exit", [r"\bExit\b", r"\bexit\s*\("] ),
        ("Settings", [r"\bSettings\b", r"\bsettings\s*\("] ),
        ("Volume", [r"volume", r"setVolume"]),
        ("Graphics Quality", [r"graphics", r"setGraphicsQuality"]),
        ("performance adaptation", [r"performance", r"adaptPerformance"]),
    ):
        _require_token(runtime_text, patterns, f"game lobby {label} action", findings)


def _validate_generic_engine(root: Path, engine: Mapping[str, Any], manifest: Mapping[str, Any],
                             files: Mapping[Path, str], findings: list[str]) -> None:
    """Validate any declared engine through an explicit adapter contract."""
    name = engine.get("name")
    if not isinstance(name, str) or not name.strip():
        findings.append("engine.name must identify the selected game engine")
    version = engine.get("version")
    if not isinstance(version, str) or not _version(version):
        findings.append("engine.version must be an exact numeric engine version")
    for key in ("role", "integration", "runtime_owner", "build_commands"):
        value = engine.get(key)
        if (key == "build_commands" and (not isinstance(value, list) or not value)) or (key != "build_commands" and (not isinstance(value, str) or not value.strip())):
            findings.append(f"engine.{key} is required for a generic engine adapter")
    bridge = engine.get("native_bridge")
    if not isinstance(bridge, str) or not bridge.strip():
        findings.append("engine.native_bridge must identify the real iOS/Flutter adapter for a non-built-in engine")
    entry = _safe_relative(root, engine.get("entrypoint"), "engine.entrypoint", findings)
    if entry is None or not entry.is_file():
        findings.append("engine.entrypoint must point to an existing generic engine runtime entrypoint")

    runtime_markers = engine.get("runtime_markers")
    if not isinstance(runtime_markers, list) or len(runtime_markers) < 3 or not all(isinstance(item, str) and item.strip() for item in runtime_markers):
        findings.append("engine.runtime_markers must list at least three real renderer/camera/scene runtime markers")
    else:
        runtime_text = _runtime_code_text(root, files)
        missing = [marker for marker in runtime_markers if not re.search(re.escape(marker), runtime_text, re.I)]
        if missing:
            findings.append("engine.runtime_markers missing from runtime source: " + ", ".join(missing))

    runtime_text = _runtime_code_text(root, files)
    _require_token(runtime_text, [r"input|touch|tap|pointer|gesture|on_input|handleInput"], "input", findings)
    _require_token(runtime_text, [r"update|tick|process|physics|step|delta"], "update loop", findings)
    _require_token(runtime_text, [r"success|failure|win|lose|result"], "success/failure result", findings)
    _require_token(runtime_text, [r"restart|reset|replay|newGame|reload"], "restart path", findings)
    _require_token(runtime_text, [r"pause|resume|lifecycle|dispose|destroy|shutdown"], "lifecycle handling", findings)


def _validate_flame(root: Path, engine: Mapping[str, Any], pubspec: str, text: str,
                    files: Mapping[Path, str], findings: list[str]) -> None:
    runtime_text = _runtime_dart_text(root, files)
    dependency = _find_dependency(pubspec, "flame")
    if not dependency or not _version(dependency):
        findings.append("Flame dependency must be declared with a numeric version")
    if not re.search(r"package:flame(?:/|\\)", runtime_text, re.I):
        findings.append("Flame dependency alone is insufficient: runtime must import package:flame")
    if not re.search(r"\b(?:FlameGame|GameWidget|Game)\b", runtime_text):
        findings.append("Flame runtime must instantiate Game/FlameGame and GameWidget")
    if not re.search(r"\b(?:Component|SpriteComponent|PositionComponent|World|ParticleSystemComponent)\b", runtime_text):
        findings.append("Flame runtime must own scene entities/components")
    entry = _safe_relative(root, engine.get("entrypoint"), "engine.entrypoint", findings)
    if entry is None or not entry.is_file():
        findings.append("Flame engine.entrypoint must point to an existing Dart scene entrypoint")
    _require_token(runtime_text, [r"\b(?:onTap|onTapDown|onTapUp|TapDetector|PanDetector|DragDetector|Keyboard|PointerMoveEvent|PointerDownEvent|handleInput)\b"], "input", findings)
    _require_token(runtime_text, [r"\b(?:void|Future<[^>]+>|double|num)\s+update\s*\(", r"@override\s+void\s+update\s*\("], "update loop", findings)
    _require_token(runtime_text, [r"\b(?:success|succeed|won|win|failure|fail|lost|lose|gameResult|result)\b"], "success/failure result", findings)
    _require_token(runtime_text, [r"\b(?:restart|reset|replay|playAgain|reloadCurrentScene|newGame)\s*\("], "restart path", findings)
    _require_token(runtime_text, [r"\b(?:overlayBuilderMap|HUD|Hud|TextComponent|Score|feedback|showSuccess|showFailure|ParticleSystemComponent|add\s*\()"], "HUD/feedback", findings)
    _require_token(runtime_text, [r"\b(?:WidgetsBindingObserver|didChangeAppLifecycleState|pauseEngine|resumeEngine|onDetach|onMount|dispose\s*\()"], "lifecycle handling", findings)
    if re.search(r"Container\s*\([^\n]*\bcolor\s*:\s*Colors\.|ColoredBox\s*\(", runtime_text) and not re.search(r"\b(?:FlameGame|GameWidget)\b", runtime_text):
        findings.append("colored-block mock is not a game engine vertical slice")


def _validate_godot(root: Path, engine: Mapping[str, Any], text: str,
                     files: Mapping[Path, str], findings: list[str]) -> None:
    runtime_text = _runtime_code_text(root, files)
    project = root / "game/project.godot"
    if not project.is_file():
        findings.append("Godot project.godot is required")
    entry = _safe_relative(root, engine.get("entrypoint"), "engine.entrypoint", findings)
    if entry is None or not entry.is_file() or entry.suffix.lower() != ".tscn":
        findings.append("Godot engine.entrypoint must point to an existing .tscn scene")
    if not re.search(r"\b(?:SwiftGodot|SwiftGodotKit|GodotHost|Godot\s*engine)\b", runtime_text, re.I):
        findings.append("Godot runtime needs SwiftGodot/SwiftGodotKit host bridge evidence")
    if not re.search(r"\b(?:FlutterMethodChannel|MethodChannel|UiKitView|FlutterPlatformView|platform\s*view|binaryMessenger)\b", runtime_text, re.I):
        findings.append("Godot runtime needs a Flutter channel or platform-view bridge")
    if not re.search(r"(?:loadScene|project\.godot|res://|\.tscn|engine\.)", runtime_text, re.I):
        findings.append("Godot bridge must call an engine-owned scene")
    _require_token(runtime_text, [r"\b(?:_input|InputEvent|onTap|touch|screenTouch|apply_move|handleInput)\b"], "input", findings)
    _require_token(runtime_text, [r"\b(?:_process|_physics_process|update_rules|physics|delta)\b"], "update loop", findings)
    _require_token(runtime_text, [r"\b(?:success|succeed|won|win|failure|fail|lost|lose|gameResult|result)\b"], "success/failure result", findings)
    _require_token(runtime_text, [r"\b(?:restart|reset|reload_current_scene|reloadCurrentScene|newGame)\s*\("], "restart path", findings)
    _require_token(runtime_text, [r"\b(?:HUD|show_success|show_failure|feedback|Score|CanvasLayer|Control)\b"], "HUD/feedback", findings)
    _require_token(runtime_text, [r"(?:pause[_A-Za-z]*|resume[_A-Za-z]*|dispose\s*\(|lifecycle|_notification|tree_exiting)"], "lifecycle handling", findings)


def _validate_unity(root: Path, engine: Mapping[str, Any], text: str, files: Mapping[Path, str], findings: list[str]) -> None:
    runtime_text = _runtime_code_text(root, files)
    bridge = str(engine.get("native_bridge", ""))
    if not bridge.strip() or bridge.strip().lower() in {"none", "not applicable"}:
        findings.append("Unity projects require explicit native_bridge adapter evidence")
    if not re.search(r"\b(?:UnityFramework|FlutterUnity|Unity\s*view|UnityEngine)\b", runtime_text, re.I):
        findings.append("Unity runtime requires UnityFramework/FlutterUnity adapter source")
    entry = _safe_relative(root, engine.get("entrypoint"), "engine.entrypoint", findings)
    if entry is None or not entry.is_file():
        findings.append("Unity engine.entrypoint must point to an existing scene/adapter file")
    for label, patterns in (
        ("input", [r"Input\.Get", r"touch", r"onTap"]),
        ("update loop", [r"\bUpdate\s*\(", r"FixedUpdate"]),
        ("success/failure result", [r"success|failure|win|lose|result"]),
        ("restart path", [r"restart|reload|Reset"]),
        ("HUD/feedback", [r"HUD|Canvas|feedback|score"]),
        ("lifecycle handling", [r"OnApplicationPause|OnDestroy|dispose|lifecycle"]),
    ):
        _require_token(runtime_text, patterns, label, findings)


def validate_project(project_root: Path | str) -> list[str]:
    """Return actionable findings; an empty list means the source gate passes."""
    root = Path(project_root).expanduser().resolve()
    findings: list[str] = []
    if not root.is_dir():
        return [
            f"project root does not exist: {root}",
            "pubspec.yaml: required Flutter project path is missing",
            "lib/: required Flutter project path is missing",
            "ios/: required Flutter project path is missing",
        ]
    for required in ("pubspec.yaml", "lib", "ios"):
        path = root / required
        exists = path.is_file() if required == "pubspec.yaml" else path.is_dir()
        if not exists:
            findings.append(f"{required + ('/' if required != 'pubspec.yaml' else '')}: required Flutter project path is missing")
    if findings:
        return findings

    manifest = _manifest(root, findings)
    if manifest is None:
        return findings
    _visual_contract(manifest, root, findings)
    _lobby_text, lobby_files = _source_text(root)
    _validate_game_lobby(root, manifest, lobby_files, findings)
    mode, _required, _reason = _implementation_decision(manifest, findings)
    if mode == "flutter-native":
        _runtime_evidence(root, findings)
        try:
            pubspec = _read(root / "pubspec.yaml")
        except OSError as error:
            findings.append(f"cannot read pubspec.yaml: {error}")
            pubspec = ""
        _text, files = _source_text(root)
        _validate_native_runtime(root, manifest, files, findings)
        return findings

    engine = _merged_engine_contract(manifest, findings)
    if not isinstance(engine, dict):
        return findings
    _require_asset_paths(root, engine.get("scene_assets"), findings, "engine.scene_assets")
    _require_evidence_paths(root, engine.get("evidence"), findings)
    _runtime_evidence(root, findings)

    try:
        pubspec = _read(root / "pubspec.yaml")
    except OSError as error:
        findings.append(f"cannot read pubspec.yaml: {error}")
        pubspec = ""
    text, files = _source_text(root)
    name = engine.get("name")
    if name == "Flame":
        _validate_flame(root, engine, pubspec, text, files, findings)
    elif name == "Godot":
        _validate_godot(root, engine, text, files, findings)
    elif name == "Unity":
        _validate_unity(root, engine, text, files, findings)
    else:
        _validate_generic_engine(root, engine, manifest, files, findings)

    return findings


# Keep the public helper name consistent with the other workflow validators.
validate = validate_project


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    root = args.project_root.expanduser().resolve()
    findings = validate_project(root)
    result = {
        "scope": "game-engine-preflight",
        "project_root": str(root),
        "valid": not findings,
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "runtime_authority": "iPhone Simulator interaction and logs remain required",
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif findings:
        for finding in findings:
            print(f"FAIL {finding}")
    else:
        print("PASS: game engine source contract is structurally satisfied; run the iPhone runtime gate next.")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
