#!/usr/bin/env python3
"""Unified iOS app inspector for Flutter and native Swift roots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import inspect_flutter_app
import inspect_swift_app
from inspect_common import iter_dirs, iter_files


def detect_stack(app_root: Path) -> str:
    if (app_root / "pubspec.yaml").exists():
        return "flutter"
    if any(iter_dirs(app_root, "*.xcodeproj")):
        return "swift"
    if any(iter_files(app_root, "Info.plist")) and any(iter_files(app_root, "*.swift")):
        return "swift"
    if (app_root / "Package.swift").exists():
        return "swift"
    raise SystemExit("unable_to_detect_ios_stack")


def inspect(app_root: Path, stack: str | None = None) -> dict[str, object]:
    resolved_stack = stack or detect_stack(app_root)
    if resolved_stack == "flutter":
        return inspect_flutter_app.inspect(app_root)
    if resolved_stack == "swift":
        return inspect_swift_app.inspect(app_root)
    raise SystemExit(f"unsupported_stack:{resolved_stack}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a Flutter or native Swift iOS app for AppListing generation.")
    parser.add_argument("--target", required=True, help="Path to the app root")
    parser.add_argument("--stack", choices=("flutter", "swift"), help="Optional explicit stack override")
    args = parser.parse_args()
    root = Path(args.target).resolve()
    print(json.dumps(inspect(root, stack=args.stack), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
