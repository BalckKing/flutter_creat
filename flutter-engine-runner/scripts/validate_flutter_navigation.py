#!/usr/bin/env python3
"""Validate the declared Flutter routing strategy and its real consumers.

Routing is selected per project in ``.codex-work/code-architecture.json``.
The allowed primary strategies are Flutter Navigator, GetX and go_router. The
validator rejects undeclared, missing or mixed route implementations while
leaving architecture and storage checks to validate_code_architecture.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MANIFEST = Path(".codex-work/code-architecture.json")
ALLOWED = {"navigator", "getx", "go_router"}
EXCLUDED_DIRS = {".git", ".dart_tool", ".codex-work", "build", "Pods", ".symlinks"}
TEXT_SUFFIXES = {
    ".dart", ".yaml", ".yml", ".json", ".plist", ".pbxproj", ".xcconfig",
    ".swift", ".m", ".mm", ".h", ".xml", ".html", ".md", ".txt",
}
SOURCE_SUFFIXES = {
    ".dart", ".yaml", ".yml", ".plist", ".pbxproj", ".xcconfig",
    ".swift", ".m", ".mm", ".h", ".xml",
}

ROUTE_SIGNALS = {
    "navigator": (
        re.compile(r"\b(?:Navigator|NavigatorState)\b"),
        re.compile(r"\b(?:MaterialPageRoute|CupertinoPageRoute|PageRouteBuilder|RouteSettings|Route)\b"),
        re.compile(r"\b(?:MaterialApp|CupertinoApp|WidgetsApp)\b"),
    ),
    "getx": (
        re.compile(r"package:get(?:/|\\)"),
        re.compile(r"\b(?:GetMaterialApp|GetCupertinoApp|Get\.to|Get\.off|Get\.offAll|Get\.back|GetPage|GetX|Obx)\b"),
    ),
    "go_router": (
        re.compile(r"package:go_router(?:/|\\)"),
        re.compile(r"\b(?:GoRouter|GoRoute|GoRouterState|MaterialApp\.router|RouterConfig)\b"),
    ),
}
DEPENDENCY_NAMES = {"getx": "get", "go_router": "go_router"}


def iter_project_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_source_files(root: Path):
    for path in iter_project_files(root):
        if path.suffix.lower() in SOURCE_SUFFIXES:
            yield path


def _list_field(value, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty list")
        return []
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field} entries must be non-empty strings")
        else:
            values.append(item)
    return values


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return [f"{root}: project root does not exist"]
    pubspec = root / "pubspec.yaml"
    lib = root / "lib"
    if not pubspec.is_file():
        errors.append(f"{root}: pubspec.yaml is required for a Flutter project")
    if not lib.is_dir():
        errors.append(f"{root}: lib/ is required for a Flutter project")
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        errors.append(f"{MANIFEST.as_posix()} is required")
        return errors
    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as error:
        errors.append(f"{MANIFEST.as_posix()} is invalid JSON: {error}")
        return errors
    if not isinstance(manifest, dict):
        return ["code architecture manifest must be a JSON object"]
    routing = manifest.get("routing")
    if not isinstance(routing, dict):
        errors.append("routing must be an object in code architecture manifest")
        return errors
    kind = str(routing.get("kind", "")).lower()
    if kind not in ALLOWED:
        errors.append("routing.kind must be one of navigator, getx, go_router")
        return errors
    consumer = _list_field(routing.get("actual_consumer"), "routing.actual_consumer", errors)
    evidence = _list_field(routing.get("runtime_evidence"), "routing.runtime_evidence", errors)
    for field, paths in (("routing.actual_consumer", consumer), ("routing.runtime_evidence", evidence)):
        for value in paths:
            if not (root / value).exists():
                errors.append(f"{field} path does not exist: {value}")
    entrypoint = routing.get("entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint.strip() or not (root / entrypoint).is_file():
        errors.append("routing.entrypoint must point to an existing project file")
    version = routing.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append("routing.version must be a non-empty SDK/package version")
    return_behavior = routing.get("return_behavior")
    if not isinstance(return_behavior, str) or not return_behavior.strip():
        errors.append("routing.return_behavior must describe back/return behavior")

    all_text = "\n".join(read_text(path) for path in iter_source_files(root))
    signals = {
        route: bool(all(pattern.search(all_text) for pattern in patterns))
        for route, patterns in ROUTE_SIGNALS.items()
    }
    selected_signals = [route for route, active in signals.items() if active]
    if kind not in selected_signals:
        errors.append(f"routing declaration {kind} has no matching route API consumer")
    if len(selected_signals) > 1:
        errors.append(f"routing strategies are mixed: {', '.join(selected_signals)}")

    pubspec_text = read_text(pubspec) if pubspec.is_file() else ""
    if kind == "navigator":
        if re.search(r"(?im)^\s*(?:get|go_router|auto_route|beamer|fluro|qlevar_router)\s*:", pubspec_text):
            errors.append("navigator routing cannot declare an external routing dependency")
    else:
        dependency = DEPENDENCY_NAMES[kind]
        if not re.search(rf"(?im)^\s*{re.escape(dependency)}\s*:", pubspec_text):
            errors.append(f"routing dependency {dependency} is missing from pubspec.yaml")

    consumer_text = "\n".join(read_text(root / value) for value in consumer if (root / value).is_file())
    if not consumer_text:
        errors.append("routing.actual_consumer must include readable project sources")
    elif not all(pattern.search(consumer_text) for pattern in ROUTE_SIGNALS[kind]):
        errors.append(f"routing.actual_consumer does not consume the declared {kind} route API")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.project_root)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS: declared Flutter routing strategy has matching dependency, API consumer and evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
