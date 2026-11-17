#!/usr/bin/env python3
"""Validate that a Flutter project uses Flutter's native Navigator stack only.

This is a read-only static gate. It intentionally rejects GetX and other
external routing packages so the onboarding, initialization, settings and
main flows remain auditable through MaterialApp/CupertinoApp/WidgetsApp and
Navigator routes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".dart", ".yaml", ".yml", ".json", ".plist", ".pbxproj", ".xcconfig",
    ".swift", ".m", ".mm", ".h", ".xml", ".html", ".md", ".txt",
}
EXCLUDED_DIRS = {".git", ".dart_tool", "build", "Pods", ".symlinks"}

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GetX dependency", re.compile(r"(?im)^\s*get\s*:")),
    ("GetX package import", re.compile(r"package:get(?:/|\\)")),
    ("GetMaterialApp", re.compile(r"\bGetMaterialApp\b")),
    ("GetCupertinoApp", re.compile(r"\bGetCupertinoApp\b")),
    ("GetX", re.compile(r"\bGetX\b")),
    ("GetBuilder", re.compile(r"\bGetBuilder\b")),
    ("Obx", re.compile(r"\bObx\b")),
    ("GetPage", re.compile(r"\bGetPage\b")),
    ("GetController", re.compile(r"\bGetController\b")),
    ("Rx", re.compile(r"\bRx(?:<|\b)")),
    ("Get navigation/service API", re.compile(
        r"\bGet\.(?:to|off|offAll|back|dialog|bottomSheet|snackbar|put|find)\s*\(")),
    ("GetX observable", re.compile(r"\.[A-Za-z_][A-Za-z0-9_]*\.obs\b|\bobs\b")),
    ("external routing package", re.compile(r"(?im)^\s*(?:go_router|auto_route|beamer|fluro|qlevar_router)\s*:")),
    ("external routing import", re.compile(r"package:(?:go_router|auto_route|beamer|fluro|qlevar_router)(?:/|\\)")),
)

APP_TOKENS = re.compile(r"\b(?:MaterialApp|CupertinoApp|WidgetsApp)\b")
NAVIGATOR_TOKENS = re.compile(r"\b(?:Navigator|NavigatorState)\b")
ROUTE_TOKENS = re.compile(
    r"\b(?:Route|MaterialPageRoute|CupertinoPageRoute|PageRouteBuilder|RouteSettings|NavigatorObserver)\b"
)


def iter_project_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def validate(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"{root}: project root does not exist"]
    pubspec = root / "pubspec.yaml"
    lib = root / "lib"
    if not pubspec.is_file():
        findings.append(f"{root}: pubspec.yaml is required for a Flutter project")
    if not lib.is_dir():
        findings.append(f"{root}: lib/ is required for a Flutter project")
    if findings:
        return findings

    lib_files = sorted(lib.rglob("*.dart"))
    if not lib_files:
        findings.append(f"{lib}: at least one Dart source file is required")

    all_text: list[tuple[Path, str]] = []
    for path in iter_project_files(root):
        try:
            all_text.append((path, read_text(path)))
        except OSError as error:
            findings.append(f"{path}: cannot read: {error}")

    for path, text in all_text:
        for label, pattern in FORBIDDEN_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(root)}:{line}: forbidden {label}")

    dart_source = "\n".join(text for path, text in all_text if path.suffix.lower() == ".dart" and path.is_relative_to(lib))
    if not APP_TOKENS.search(dart_source):
        findings.append("lib/: native Flutter app shell required (MaterialApp, CupertinoApp, or WidgetsApp)")
    if not NAVIGATOR_TOKENS.search(dart_source):
        findings.append("lib/: native Navigator usage required (Navigator or NavigatorState)")
    if not ROUTE_TOKENS.search(dart_source):
        findings.append("lib/: native Navigator route required (Route/MaterialPageRoute/CupertinoPageRoute/PageRouteBuilder/RouteSettings)")
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
    print("PASS: Flutter project uses a native app shell and Navigator routes with no forbidden GetX or external router usage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
