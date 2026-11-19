#!/usr/bin/env python3
"""Validate a Flutter project's declared code architecture, routing and storage.

The workflow allows one primary routing strategy (Navigator, GetX or
go_router), one primary architecture style (MVVM, MVC or VIPER), and any
combination of the approved storage backends when each backend has a declared
purpose and a real consumer.  This is a read-only static gate; runtime
evidence paths are required to make missing simulator evidence visible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MANIFEST_RELATIVE_PATH = Path(".codex-work/code-architecture.json")
ALLOWED_ARCHITECTURES = {"mvvm", "mvc", "viper"}
ALLOWED_ROUTES = {"navigator", "getx", "go_router"}
ALLOWED_STORAGE = {"sqlite", "sqflite", "drift", "shared_preferences", "flutter_secure_storage"}

TEXT_SUFFIXES = {
    ".dart", ".yaml", ".yml", ".json", ".plist", ".pbxproj", ".xcconfig",
    ".swift", ".m", ".mm", ".h", ".xml", ".html", ".md", ".txt",
}
SOURCE_SUFFIXES = {
    ".dart", ".yaml", ".yml", ".plist", ".pbxproj", ".xcconfig",
    ".swift", ".m", ".mm", ".h", ".xml",
}
EXCLUDED_DIRS = {".git", ".dart_tool", ".codex-work", "build", "Pods", ".symlinks"}

ROUTE_DEPENDENCY = {
    "navigator": "flutter",
    "getx": "get",
    "go_router": "go_router",
}
ROUTE_MARKERS = {
    "navigator": (
        re.compile(r"\b(?:Navigator|NavigatorState)\b"),
        re.compile(r"\b(?:MaterialPageRoute|CupertinoPageRoute|PageRouteBuilder|RouteSettings|Route)\b"),
        re.compile(r"\b(?:MaterialApp|CupertinoApp|WidgetsApp)\b"),
    ),
    "getx": (
        re.compile(r"package:get(?:/|\\)"),
        re.compile(r"\b(?:GetMaterialApp|GetCupertinoApp|Get\.to|Get\.off|Get\.offAll|Get\.back|GetPage)\b"),
    ),
    "go_router": (
        re.compile(r"package:go_router(?:/|\\)"),
        re.compile(r"\b(?:GoRouter|GoRoute|GoRouterState|MaterialApp\.router|RouterConfig)\b"),
    ),
}
STORAGE_MARKERS = {
    "shared_preferences": re.compile(r"\bSharedPreferences\b"),
    "flutter_secure_storage": re.compile(r"\bFlutterSecureStorage\b"),
    "sqlite": re.compile(r"\b(?:openDatabase|Database|Drift|sqlite3)\b"),
    "sqflite": re.compile(r"\b(?:openDatabase|Database)\b"),
    "drift": re.compile(r"\b(?:DriftDatabase|Table|GeneratedDatabase)\b"),
}
ARCHITECTURE_BOUNDARIES = {
    "mvvm": {
        "view": re.compile(r"(?:^|/)(?:views?|pages?|screens?)(?:/|$)", re.I),
        "view_model": re.compile(r"(?:^|/)(?:view_models?|viewmodels?)(?:/|$)|view[_-]?model", re.I),
        "repository": re.compile(r"(?:^|/)(?:repositories?|repos?)(?:/|$)|repository", re.I),
        "model": re.compile(r"(?:^|/)(?:models?|entities?)(?:/|$)|model", re.I),
    },
    "mvc": {
        "view": re.compile(r"(?:^|/)(?:views?|pages?|screens?)(?:/|$)", re.I),
        "controller": re.compile(r"(?:^|/)(?:controllers?|ctl)(?:/|$)|controller", re.I),
        "model": re.compile(r"(?:^|/)(?:models?|entities?)(?:/|$)|model", re.I),
        "repository": re.compile(r"(?:^|/)(?:repositories?|repos?)(?:/|$)|repository", re.I),
    },
    "viper": {
        "view": re.compile(r"(?:^|/)(?:views?|pages?|screens?)(?:/|$)", re.I),
        "interactor": re.compile(r"(?:^|/)(?:interactors?|use_cases?|usecases?)(?:/|$)|interactor", re.I),
        "presenter": re.compile(r"(?:^|/)(?:presenters?)(?:/|$)|presenter", re.I),
        "entity": re.compile(r"(?:^|/)(?:entities?|models?)(?:/|$)|entity", re.I),
        "router": re.compile(r"(?:^|/)(?:routers?|routes?)(?:/|$)|router", re.I),
    },
}


def iter_project_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_source_files(root: Path):
    for path in iter_project_files(root):
        if path.suffix.lower() in SOURCE_SUFFIXES:
            yield path


def _as_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty list")
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field} entries must be non-empty strings")
        else:
            result.append(item)
    return result


def _require_exact_version(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be an exact non-empty version")
        return
    version = value.strip()
    if version.lower() in {"sdk", "flutter sdk"}:
        return
    if version[0] in "^~<>=*" or any(operator in version for operator in ("||", " ")):
        errors.append(f"{field} must be an exact version, not a range: {value}")


def _evidence_paths(root: Path, values: list[str], field: str, errors: list[str]) -> None:
    for value in values:
        path = root / value
        if not path.exists():
            errors.append(f"{field} path does not exist: {value}")


def _load_manifest(root: Path, errors: list[str]) -> dict[str, Any] | None:
    manifest_path = root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        errors.append(f"{MANIFEST_RELATIVE_PATH.as_posix()} is required")
        return None
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{MANIFEST_RELATIVE_PATH.as_posix()} is invalid JSON: {error}")
        return None
    if not isinstance(value, dict):
        errors.append("code architecture manifest must be a JSON object")
        return None
    if value.get("schema_version") != 1:
        errors.append("code architecture manifest schema_version must be 1")
    return value


def _validate_architecture(root: Path, manifest: dict[str, Any], all_dart: str, errors: list[str]) -> None:
    architecture = manifest.get("architecture")
    if not isinstance(architecture, dict):
        errors.append("architecture must be an object")
        return
    style = str(architecture.get("style", "")).lower()
    if style not in ALLOWED_ARCHITECTURES:
        errors.append("architecture.style must be one of mvvm, mvc, viper")
        return
    rationale = architecture.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append("architecture.rationale must explain the project-specific choice")
    evidence = _as_list(architecture.get("evidence"), "architecture.evidence", errors)
    _evidence_paths(root, evidence, "architecture.evidence", errors)

    boundaries = ARCHITECTURE_BOUNDARIES[style]
    evidence_paths = [Path(item).as_posix() for item in evidence]
    for boundary, pattern in boundaries.items():
        if not any(pattern.search(path) and (root / path).is_file() for path in evidence_paths):
            errors.append(f"{style} architecture is missing {boundary} boundary evidence")

    source_paths = [path for path in evidence_paths if path.endswith(".dart") and (root / path).is_file()]
    source_text = "\n".join(read_text(root / path) for path in source_paths)
    if not source_text:
        errors.append(f"{style} architecture evidence must include Dart consumers")
    elif not re.search(r"\b(?:class|mixin|abstract\s+class)\s+[A-Z]\w*", source_text):
        errors.append(f"{style} architecture evidence must contain Dart types")


def _validate_routing(root: Path, manifest: dict[str, Any], all_text: str, errors: list[str]) -> None:
    routing = manifest.get("routing")
    if not isinstance(routing, dict):
        errors.append("routing must be an object")
        return
    kind = str(routing.get("kind", "")).lower()
    if kind not in ALLOWED_ROUTES:
        errors.append("routing.kind must be one of navigator, getx, go_router")
        return
    package = str(routing.get("package", "")).strip()
    expected_package = ROUTE_DEPENDENCY[kind]
    if kind != "navigator" and package != expected_package:
        errors.append(f"routing.package must be {expected_package} for {kind}")
    _require_exact_version(routing.get("version"), "routing.version", errors)
    consumer = _as_list(routing.get("actual_consumer"), "routing.actual_consumer", errors)
    evidence = _as_list(routing.get("runtime_evidence"), "routing.runtime_evidence", errors)
    _evidence_paths(root, consumer, "routing.actual_consumer", errors)
    _evidence_paths(root, evidence, "routing.runtime_evidence", errors)
    entrypoint = routing.get("entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint.strip() or not (root / entrypoint).is_file():
        errors.append("routing.entrypoint must point to an existing project file")
    return_behavior = routing.get("return_behavior")
    if not isinstance(return_behavior, str) or not return_behavior.strip():
        errors.append("routing.return_behavior must describe back/return behavior")

    markers = ROUTE_MARKERS[kind]
    for marker, label in zip(markers, ("package/API", "route API", "app shell")):
        if not marker.search(all_text):
            errors.append(f"routing {kind} {label} is missing from project sources")

    route_signals = {
        "navigator": bool(ROUTE_MARKERS["navigator"][0].search(all_text) and ROUTE_MARKERS["navigator"][1].search(all_text)),
        "getx": bool(ROUTE_MARKERS["getx"][0].search(all_text) and ROUTE_MARKERS["getx"][1].search(all_text)),
        "go_router": bool(ROUTE_MARKERS["go_router"][0].search(all_text) and ROUTE_MARKERS["go_router"][1].search(all_text)),
    }
    if sum(route_signals.values()) > 1:
        selected = ", ".join(name for name, active in route_signals.items() if active)
        errors.append(f"routing strategies are mixed: {selected}")

    pubspec = root / "pubspec.yaml"
    pubspec_text = read_text(pubspec) if pubspec.is_file() else ""
    if kind != "navigator" and not re.search(rf"(?im)^\s*{re.escape(expected_package)}\s*:", pubspec_text):
        errors.append(f"routing dependency {expected_package} is missing from pubspec.yaml")
    if kind == "navigator" and re.search(r"(?im)^\s*(?:get|go_router|auto_route|beamer|fluro|qlevar_router)\s*:", pubspec_text):
        errors.append("navigator routing cannot declare an external routing dependency")


def _storage_kind(entry: dict[str, Any]) -> str:
    return str(entry.get("kind", "")).lower().replace(" ", "_")


def _validate_storage(root: Path, manifest: dict[str, Any], all_dart: str, errors: list[str]) -> None:
    storage = manifest.get("storage")
    if not isinstance(storage, list):
        errors.append("storage must be a list (use [] when no persistence is needed)")
        return
    seen: set[str] = set()
    pubspec_text = read_text(root / "pubspec.yaml") if (root / "pubspec.yaml").is_file() else ""
    for index, raw_entry in enumerate(storage):
        prefix = f"storage[{index}]"
        if not isinstance(raw_entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = _storage_kind(raw_entry)
        if kind not in ALLOWED_STORAGE:
            errors.append(f"{prefix}.kind must be one of sqlite, shared_preferences, flutter_secure_storage")
            continue
        if kind in seen:
            errors.append(f"storage backend is declared more than once: {kind}")
        seen.add(kind)
        for required in ("purpose", "package"):
            value = raw_entry.get(required)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{required} must be a non-empty string")
        _require_exact_version(raw_entry.get("version"), f"{prefix}.version", errors)
        purpose = str(raw_entry.get("purpose", "")).lower()
        if kind == "shared_preferences" and not any(token in purpose for token in ("preference", "setting", "onboarding", "偏好", "设置", "引导")):
            errors.append("shared_preferences purpose must describe lightweight preferences or onboarding state")
        if kind == "flutter_secure_storage" and not any(token in purpose for token in ("secret", "token", "key", "credential", "敏感", "密钥", "令牌")):
            errors.append("flutter_secure_storage purpose must describe sensitive private values")
        if kind in {"sqlite", "sqflite", "drift"} and not any(token in purpose for token in ("structured", "record", "history", "query", "离线", "结构化", "记录", "历史", "查询")):
            errors.append("sqlite purpose must describe structured offline data or records")

        package = str(raw_entry.get("package", "")).strip()
        allowed_packages = {
            "sqlite": {"sqflite", "drift", "sqlite3"},
            "sqflite": {"sqflite"},
            "drift": {"drift"},
            "shared_preferences": {"shared_preferences"},
            "flutter_secure_storage": {"flutter_secure_storage"},
        }[kind]
        if package not in allowed_packages:
            errors.append(f"{prefix}.package is incompatible with {kind}")
        elif package != "sqlite3" and not re.search(rf"(?im)^\s*{re.escape(package)}\s*:", pubspec_text):
            errors.append(f"storage dependency {package} is missing from pubspec.yaml")

        consumers = _as_list(raw_entry.get("actual_consumer"), f"{prefix}.actual_consumer", errors)
        evidence = _as_list(raw_entry.get("runtime_evidence"), f"{prefix}.runtime_evidence", errors)
        _evidence_paths(root, consumers, f"{prefix}.actual_consumer", errors)
        _evidence_paths(root, evidence, f"{prefix}.runtime_evidence", errors)
        if consumers:
            consumer_text = "\n".join(read_text(root / path) for path in consumers if (root / path).is_file())
            consumer_code = re.sub(r"(?m)^\s*import\s+['\"][^'\"]+['\"]\s*;?\s*$", "", consumer_text)
            marker = STORAGE_MARKERS[kind]
            if not marker.search(consumer_code):
                errors.append(f"{prefix} {kind} has no real API/package consumer in declared files")
            all_dart_code = re.sub(r"(?m)^\s*import\s+['\"][^'\"]+['\"]\s*;?\s*$", "", all_dart)
            if not marker.search(all_dart_code):
                errors.append(f"{prefix} {kind} is not consumed by project Dart sources")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return [f"{root}: project root does not exist"]
    if not (root / "pubspec.yaml").is_file():
        errors.append(f"{root}: pubspec.yaml is required for a Flutter project")
    if not (root / "lib").is_dir():
        errors.append(f"{root}: lib/ is required for a Flutter project")
    manifest = _load_manifest(root, errors)
    if manifest is None:
        return errors

    dart_files = sorted((root / "lib").rglob("*.dart"))
    if not dart_files:
        errors.append("lib/: at least one Dart source file is required")
    all_dart = "\n".join(read_text(path) for path in dart_files)
    all_text = "\n".join(read_text(path) for path in iter_source_files(root))
    _validate_architecture(root, manifest, all_dart, errors)
    _validate_routing(root, manifest, all_text, errors)
    _validate_storage(root, manifest, all_dart, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args()
    errors = validate(args.project_root)
    report = {"status": "Passed" if not errors else "Failed", "errors": errors}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if errors:
            for error in errors:
                print(f"FAIL {error}")
        else:
            print("PASS: declared architecture, routing and storage have matching consumers and evidence.")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
