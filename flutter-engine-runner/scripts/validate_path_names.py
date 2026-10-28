#!/usr/bin/env python3
"""Read-only check of actual project paths against the abbreviation glossary.

This checks spelling, known expansions and case collisions, not semantic naming
quality, reference resolution, third-party ownership or runtime asset loading.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path


GROUPS = {
    "cfg": ("configuration", "config", "configurations"),
    "ctl": ("controller", "controllers"),
    "cmp": ("component", "components"),
    "svc": ("service", "services"),
    "repo": ("repository", "repositories"),
    "dlg": ("dialog", "dialogs"),
    "thumb": ("thumbnail", "thumbnails"),
    "det": ("detail", "details"),
    "prefs": ("settings", "preferences"),
    "init": ("initialization",),
    "mdl": ("model", "models"),
    "wgt": ("widget", "widgets"),
    "rt": ("route", "routes"),
    "util": ("utility", "utilities"),
    "hlp": ("helper", "helpers"),
    "const": ("constant", "constants"),
    "mgr": ("manager", "managers"),
    "anim": ("animation", "animations"),
    "deco": ("decoration", "decorations"),
    "bg": ("background", "backgrounds"),
    "ill": ("illustration", "illustrations"),
}
DEFAULT_TERMS = {word: short for short, words in GROUPS.items() for word in words}
SHORT_NAME = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")

# These are tool/output contracts, not blanket exemptions for app-owned code.
SKIP_ROOTS = (
    ".git", ".codex-work", ".dart_tool", "build", ".idea", ".vscode",
    "aduit", "AppListing", "ios/Pods", "ios/.symlinks", "ios/Flutter",
    "ios/Runner.xcodeproj", "ios/Runner.xcworkspace",
)
FIXED_PATHS = {
    "lib/common_module", "lib/page_module", "lib/service_module",
    "lib/common_module/theme/app_theme.dart", "assets/logo.png",
    "assets/backgrounds", "assets/illustrations",
    "assets/media/resource_manifest.json", "lib/welcome.dart", "lib/main.dart",
    "pubspec.yaml", "pubspec.lock", "analysis_options.yaml", "l10n.yaml",
    "README.md", "CHANGELOG.md", "LICENSE", "LICENSE.md", "NOTICE", "AUTHORS",
    ".gitignore", ".gitattributes", ".metadata", ".flutter-plugins",
    ".flutter-plugins-dependencies", ".DS_Store",
    "ios/Runner", "ios/RunnerTests", "ios/Podfile", "ios/Podfile.lock",
    "ios/RunnerTests/RunnerTests.swift",
}
NATIVE_NAMES = {
    "AppDelegate.swift", "SceneDelegate.swift", "Runner-Bridging-Header.h",
    "GeneratedPluginRegistrant.h", "GeneratedPluginRegistrant.m", "Info.plist",
    "InfoPlist.strings", "PrivacyInfo.xcprivacy", "LaunchScreen.storyboard",
    "Main.storyboard", "Assets.xcassets", "Contents.json",
}


def beneath(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def fixed_name(path, is_dir):
    if path in FIXED_PATHS:
        return True
    name = path.rsplit("/", 1)[-1]
    if path.startswith("ios/"):
        if name in NATIVE_NAMES or (is_dir and name.endswith(".lproj")):
            return True
        if any(part in {"AppIcon.appiconset", "LaunchImage.imageset"} for part in path.split("/")):
            return True
    return False


def name_stem(path, is_dir):
    name = path.rsplit("/", 1)[-1]
    if not is_dir:
        name = Path(name).stem
        # Generated Dart suffixes are required by their generator.
        if path.endswith((".g.dart", ".freezed.dart", ".gr.dart")):
            name = name.rsplit(".", 1)[0]
    match = re.fullmatch(r"assets/backgrounds/([^/]+)/\1_background\.[^/]+", path)
    if match:
        return match.group(1)  # Only the fixed suffix is exempt; page_id is not.
    return name


def load_terms(root, errors):
    terms = dict(DEFAULT_TERMS)
    keep = {}
    glossary = root / ".codex-work/path-terms.json"
    try:
        if glossary.is_symlink():
            raise ValueError("glossary must be a regular project file")
        data = json.loads(glossary.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or "terms" not in data
                or set(data) - {"terms", "keep"} or not isinstance(data["terms"], dict)):
            raise ValueError('expected {"terms": {"full_term": "short_term"}, "keep": []}')
        for full, short in data["terms"].items():
            if not isinstance(short, str) or not SHORT_NAME.fullmatch(full) or not SHORT_NAME.fullmatch(short):
                raise ValueError("terms and abbreviations must be lower_snake_case")
            if len(short.replace("_", "")) >= len(full.replace("_", "")):
                raise ValueError(f"abbreviation must be shorter: {full} -> {short}")
            if full in terms and terms[full] != short:
                raise ValueError(f"cannot override the standard abbreviation for {full}")
            terms[full] = short
        for full, short in terms.items():
            for expanded in terms:
                if re.search(r"(?:^|_)" + re.escape(expanded) + r"(?:_|$)", short):
                    raise ValueError(f"abbreviation still contains an expanded term: {full} -> {short}")
        entries = data.get("keep", [])
        if not isinstance(entries, list):
            raise ValueError("keep must list exact paths and concrete reasons")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "reason"}:
                raise ValueError("each keep entry needs path and reason")
            path, reason = entry["path"], entry["reason"]
            if (not isinstance(path, str) or not path or path.startswith("/")
                    or any(part in ("", ".", "..") for part in path.split("/"))
                    or any(char in path for char in "*?[]\\") or path in keep):
                raise ValueError("keep paths must be unique exact project-relative paths, without globs")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"keep reason is required: {path}")
            if not (root / path).exists() or (root / path).is_symlink():
                raise ValueError(f"keep path must exist without being a symbolic link: {path}")
            keep[path] = reason.strip()
    except (OSError, ValueError) as error:
        errors.append(f".codex-work/path-terms.json: {error}")
    return terms, keep


def check(root):
    errors, checked, preserved, excluded = [], [], [], []
    if not root.is_dir() or not (root / "pubspec.yaml").is_file():
        return {"status": "Failed", "errors": ["--project-root must be the actual Flutter project root (pubspec.yaml required)"], "checked": [], "preserved": [], "excluded": []}
    terms, keep = load_terms(root, errors)
    seen = {}

    def walk_error(error):
        errors.append(f"Cannot inspect project path: {error}")

    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs.sort()
        files.sort()
        for name in dirs[:] + files:
            item = Path(parent) / name
            relative = item.relative_to(root).as_posix()
            is_dir = name in dirs
            skip = next((p for p in SKIP_ROOTS if beneath(relative, p)), None)
            if skip:
                excluded.append(relative)
                if is_dir:
                    dirs.remove(name)
                continue
            key = unicodedata.normalize("NFC", relative).casefold()
            if key in seen and seen[key] != relative:
                errors.append(f"case-insensitive path collision: {seen[key]} / {relative}")
            seen[key] = relative
            if item.is_symlink():
                errors.append(f"{relative}: uninspected symbolic link; resolve ownership and inspect its target")
                if is_dir:
                    dirs.remove(name)
                continue
            if fixed_name(relative, is_dir) or relative in keep:
                preserved.append(relative)
                continue
            checked.append(relative)
            stem = name_stem(relative, is_dir)
            if not SHORT_NAME.fullmatch(stem):
                errors.append(f"{relative}: use a short lower_snake_case name")
            for full, short in sorted(terms.items()):
                if re.search(r"(?:^|_)" + re.escape(full) + r"(?:_|$)", stem.lower()):
                    errors.append(f"{relative}: abbreviate {full} -> {short}")
    return {"status": "Failed" if errors else "Passed", "errors": errors, "checked": checked,
            "preserved": preserved, "kept_with_reasons": keep, "excluded": excluded}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="emit the complete read-only inventory as JSON")
    args = parser.parse_args()
    result = check(args.project_root.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in result["errors"]:
            print("FAIL: " + error)
        print(f'{result["status"]}: {len(result["checked"])} custom paths inspected; '
              f'{len(result["preserved"])} contract entries preserved; '
              f'{len(result["excluded"])} tool/delivery roots excluded.')
        print("Semantic naming, reference/build correctness and runtime loading require separate verification.")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
