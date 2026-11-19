#!/usr/bin/env python3
"""Static Welcome/Initialization flow contract check."""
from __future__ import annotations
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


ROUTING_SCRIPT = Path(__file__).with_name("validate_flutter_navigation.py")
ROUTING_SPEC = importlib.util.spec_from_file_location("validate_flutter_navigation", ROUTING_SCRIPT)
ROUTING_MODULE = importlib.util.module_from_spec(ROUTING_SPEC)
assert ROUTING_SPEC and ROUTING_SPEC.loader
ROUTING_SPEC.loader.exec_module(ROUTING_MODULE)


def _load_route_kind(root: Path, errors: list[str]) -> str | None:
    manifest = root / ".codex-work/code-architecture.json"
    if not manifest.is_file():
        errors.append("Welcome flow requires .codex-work/code-architecture.json")
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"code architecture manifest is invalid JSON: {error}")
        return None
    route = data.get("routing") if isinstance(data, dict) else None
    kind = route.get("kind") if isinstance(route, dict) else None
    if kind not in {"navigator", "getx", "go_router"}:
        errors.append("Welcome flow routing.kind must be navigator, getx, or go_router")
        return None
    return kind


def validate(root: Path):
    errors = []
    welcome = root / "lib/welcome.dart"
    if not welcome.is_file():
        return {"status": "Not verified", "errors": ["lib/welcome.dart is missing"]}
    source = welcome.read_text(encoding="utf-8", errors="replace")
    lib = root / "lib"
    all_dart = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in lib.rglob("*.dart"))
    route_kind = _load_route_kind(root, errors)
    if not re.search(r"class\s+WelcomePage\b", source):
        errors.append("WelcomePage must be defined in lib/welcome.dart")
    if not re.search(r"\bContinue\b", source):
        errors.append("Welcome must expose Continue")
    if re.search(r"\b(?:pause|paused|resume)\b|Pause|暂停", source, re.I):
        errors.append("Welcome pause controls or paused state must be removed")
    if re.search(r"(?:welcome|enter)\.html|aduit[/\\]", all_dart, re.I):
        errors.append("runtime Dart must not load delivery HTML or aduit paths")
    if route_kind is not None:
        route_errors = ROUTING_MODULE.validate(root)
        errors.extend(f"routing: {error}" for error in route_errors)
    has_clear = bool(re.search(r"Clear\s*Data|clearData|clear_data", all_dart, re.I))
    has_entry = bool(re.search(r"/entry|Initialization|initialization", all_dart, re.I))
    if has_clear and has_entry and not re.search(
        r"(?:clearData|clear_data|Clear\s*Data)[\s\S]{0,700}(?:entry|Initialization|/entry)",
        all_dart,
        re.I,
    ):
        errors.append("Initialization must follow successful Clear Data")
    if has_entry and not re.search(r"\bEnter\b", all_dart):
        errors.append("Initialization action must be labelled Enter")
    for obsolete in (root / "welcome.html", root / "enter.html", root / "aduit/enter.html"):
        if obsolete.exists():
            errors.append(f"obsolete Welcome HTML path exists: {obsolete.relative_to(root)}")
    if not (root / "aduit/welcome.html").is_file():
        errors.append("standalone delivery aduit/welcome.html is missing")
    return {"status": "Failed" if errors else "Passed", "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.project_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "Passed" else 1


if __name__ == "__main__":
    sys.exit(main())
