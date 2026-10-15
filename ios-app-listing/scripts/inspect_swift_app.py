#!/usr/bin/env python3
"""Extract structured native Swift iOS app evidence for AppListing generation."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_common import (
    analyze_access_signals,
    build_inspect_result,
    extract_brand_colors_from_xcassets,
    extract_iap_codes_from_content,
    finalize_ai_signals,
    iter_files,
    parse_permissions_from_info,
    read_text,
    title_case_slug,
    to_slug,
    URL_PATTERN,
    extract_ui_strings,
)


TYPE_PATTERN = re.compile(r"\b(?:class|struct|enum)\s+([A-Z][A-Za-z0-9_]*)")
SCREEN_TYPE_PATTERN = re.compile(r"\b(?:class|struct)\s+([A-Z][A-Za-z0-9_]*(?:ViewController|Controller|Coordinator|Screen|Page|View))\b")
ENTITY_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:Entity|Model|ViewModel|Plan|Record|Message|Conversation|Post|User))\b")
FUNC_PATTERN = re.compile(r"\bfunc\s+([a-z][A-Za-z0-9_]*)\s*\(")
ROUTE_PATTERN = re.compile(r'["\'](/[A-Za-z0-9_\-/]+)["\']')
STRING_ROUTE_PATTERN = re.compile(r'["\']([A-Z][A-Za-z0-9_]*(?:View|ViewController|Controller|Screen|Page)|/[A-Za-z0-9_\-/]+)["\']')
SWIFT_PACKAGE_PATTERN = re.compile(r"\.package\([^\\n]*url:\s*\"([^\"]+)\"")
POD_PATTERN = re.compile(r"pod\s+['\"]([^'\"]+)['\"]")
PRODUCT_NAME_PATTERN = re.compile(r"PRODUCT_NAME\s*=\s*([^;]+);")
AI_REACHABILITY_PATH_HINTS = (
    "assistant",
    "copilot",
    "prompt",
    "translate",
    "ai_",
    "ai/",
    "generator",
    "avatar",
    "preview",
    "tryon",
)
AI_REACHABILITY_TEXT_HINTS = (
    "ask ai",
    "ai assistant",
    "copilot",
    "prompt",
    "text translation",
    "voice translation",
    "image translation",
    "translate image",
    "translate text",
    "generate image",
    "ai preview",
    "preview result",
    "save to photos",
)
AI_VISIBLE_ENTRY_ROUTE_HINTS = (
    "/assistant",
    "/copilot",
    "/prompt",
    "/ai-assistant",
    "/ai/chat",
    "/generate",
    "/avatar",
    "/image-preview",
    "/tryon",
    "/translate",
)
ACTIVE_CAPABILITY_THRESHOLD = 1.0
SWIFT_AI_NAV_ACTION_HINTS = (
    "navigationlink",
    "pushviewcontroller",
    "present(",
    "sheet(",
    "fullscreencover",
    "navigationdestination",
    "uihostingcontroller",
)
SWIFT_AI_NAV_TRIGGER_HINTS = (
    "button(",
    "ontapgesture",
    "toolbar",
    "menu(",
    "list(",
    "tabview",
)
SWIFT_AI_TAB_CONTAINER_HINTS = (
    "tabview",
    "pageview",
)


def find_info_plist(app_root: Path) -> Path | None:
    candidates = []
    for path in iter_files(app_root, "Info.plist"):
        lowered = str(path).lower()
        if any(token in lowered for token in ("pods/", "build/", ".build/")):
            continue
        candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda path: (len(path.parts), str(path)))
    return candidates[0]


def extract_name(app_root: Path) -> tuple[str, str]:
    info_plist = find_info_plist(app_root)
    if info_plist is not None:
        with info_plist.open("rb") as handle:
            info = plistlib.load(handle)
        display = str(info.get("CFBundleDisplayName") or "").strip()
        if display:
            return display, to_slug(display)

    pbxproj_candidates = sorted(iter_files(app_root, "project.pbxproj"))
    for pbxproj in pbxproj_candidates:
        match = PRODUCT_NAME_PATTERN.search(read_text(pbxproj))
        if match:
            raw = match.group(1).strip().strip('"').replace("$(TARGET_NAME)", "").strip()
            if raw:
                return title_case_slug(raw), to_slug(raw)

    return title_case_slug(app_root.name), to_slug(app_root.name)


def extract_permissions(app_root: Path) -> dict[str, str]:
    info_plist = find_info_plist(app_root)
    if info_plist is None:
        return {}
    with info_plist.open("rb") as handle:
        info = plistlib.load(handle)
    return parse_permissions_from_info(info)


def extract_dependencies(app_root: Path) -> list[str]:
    dependencies: set[str] = set()
    package_swift = app_root / "Package.swift"
    if package_swift.exists():
        text = read_text(package_swift)
        for match in SWIFT_PACKAGE_PATTERN.findall(text):
            name = Path(match).stem
            if name:
                dependencies.add(name)
    for candidate in ("Podfile", "Podfile.lock"):
        path = app_root / candidate
        if not path.exists():
            continue
        text = read_text(path)
        for match in POD_PATTERN.findall(text):
            dependencies.add(match)
    for path in iter_files(app_root, "*.swift"):
        lowered = str(path).lower()
        if any(token in lowered for token in ("/pods/", "/build/", "/.build/")):
            continue
        text = read_text(path)
        for match in re.findall(r"(?m)^import\s+([A-Za-z0-9_]+)", text):
            if match not in {"SwiftUI", "Foundation", "UIKit", "Combine"}:
                dependencies.add(match)
    return sorted(dependencies)


def _swift_source_files(app_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in iter_files(app_root, "*.swift"):
        lowered = str(path).lower()
        if any(token in lowered for token in ("/pods/", "/build/", "/.build/")):
            continue
        files.append(path)
    return files


def _swift_module_root(path: Path, app_root: Path) -> Path:
    rel = path.relative_to(app_root)
    parts = rel.parts
    if "Features" in parts:
        index = parts.index("Features")
        if index + 1 < len(parts):
            return Path(*parts[: index + 2])
    if rel.parent != Path("."):
        return rel.parent
    return rel


def _path_is_within(rel: Path, root: Path) -> bool:
    return rel.parts[: len(root.parts)] == root.parts


def _file_matches_hints(path: Path, app_root: Path, text: str, path_hints: tuple[str, ...], text_hints: tuple[str, ...]) -> bool:
    lowered_rel = str(path.relative_to(app_root)).lower()
    lowered_text = text.lower()
    return any(token in lowered_rel for token in path_hints) or any(token in lowered_text for token in text_hints)


def _collect_entry_symbols(text: str, path: Path) -> set[str]:
    symbols = {
        class_name
        for class_name in SCREEN_TYPE_PATTERN.findall(text)
        if class_name.endswith(("View", "ViewController", "Controller", "Screen", "Page"))
    }
    if path.stem.endswith(("View", "Controller", "Screen", "Page")):
        symbols.add(path.stem)
    return symbols


def _looks_like_ui_surface(path: Path, app_root: Path, text: str) -> bool:
    lowered_rel = str(path.relative_to(app_root)).lower()
    if any(token in lowered_rel for token in ("view", "screen", "page", "home", "main", "tab", "profile", "feed", "dashboard")):
        return True
    return bool(SCREEN_TYPE_PATTERN.findall(text))


def _looks_like_navigation_shell_path(path: Path, app_root: Path) -> bool:
    lowered_rel = str(path.relative_to(app_root)).lower()
    return any(token in lowered_rel for token in ("nav", "route", "router", "routing", "registry", "shell", "coordinator"))


def _looks_like_top_level_surface(path: Path, app_root: Path) -> bool:
    lowered_rel = str(path.relative_to(app_root)).lower()
    return any(token in lowered_rel for token in ("home", "main", "root", "dashboard", "tab", "feed", "profile", "contentview"))


def _is_ai_candidate_path(path: Path, app_root: Path, text: str) -> bool:
    lowered_rel = str(path.relative_to(app_root)).lower()
    return _file_matches_hints(path, app_root, text, AI_REACHABILITY_PATH_HINTS, AI_REACHABILITY_TEXT_HINTS) and not (
        _looks_like_navigation_shell_path(path, app_root) and not any(token in lowered_rel for token in AI_REACHABILITY_PATH_HINTS)
    )


def _collect_candidate_route_hits(text: str) -> list[str]:
    lowered_text = text.lower()
    hits: list[str] = []
    for token in AI_VISIBLE_ENTRY_ROUTE_HINTS:
        if token in lowered_text and token not in hits:
            hits.append(token)
    return hits


def _collect_candidate_route_symbols(text: str) -> set[str]:
    return set(STRING_ROUTE_PATTERN.findall(text))


def _has_navigation_invocation(text: str) -> bool:
    lowered_text = text.lower()
    return any(token in lowered_text for token in SWIFT_AI_NAV_ACTION_HINTS)


def _has_user_entry_trigger(text: str) -> bool:
    lowered_text = text.lower()
    return any(token in lowered_text for token in SWIFT_AI_NAV_TRIGGER_HINTS)


def _has_tab_surface_mount(text: str) -> bool:
    lowered_text = text.lower()
    return any(token in lowered_text for token in SWIFT_AI_TAB_CONTAINER_HINTS)


def analyze_swift_ai_reachability(app_root: Path) -> dict[str, object]:
    swift_files = _swift_source_files(app_root)
    candidate_paths: list[Path] = []
    candidate_path_set: set[Path] = set()
    file_cache: dict[Path, str] = {}

    for path in swift_files:
        text = read_text(path)
        file_cache[path] = text
        if not _is_ai_candidate_path(path, app_root, text):
            continue
        candidate_paths.append(path)
        candidate_path_set.add(path)

    module_entry_symbols: dict[Path, set[str]] = {}
    module_route_symbols: dict[Path, set[str]] = {}
    candidate_roots: list[Path] = []
    candidate_files: list[str] = []
    embedded_surface_hits: list[str] = []
    route_registration_hits: list[str] = []
    navigation_invocation_hits: list[str] = []
    entry_surface_hits: list[str] = []
    seen_embedded: set[str] = set()
    seen_route_registration: set[str] = set()
    seen_navigation: set[str] = set()
    seen_entry_surface: set[str] = set()

    for path in candidate_paths:
        text = file_cache[path]
        root = _swift_module_root(path, app_root)
        if root not in candidate_roots:
            candidate_roots.append(root)
        module_entry_symbols.setdefault(root, set()).update(_collect_entry_symbols(text, path))
        module_route_symbols.setdefault(root, set()).update(_collect_candidate_route_symbols(text))
        relative_path = str(path.relative_to(app_root))
        if relative_path not in candidate_files:
            candidate_files.append(relative_path)
        if (
            _looks_like_ui_surface(path, app_root, text)
            and not _looks_like_navigation_shell_path(path, app_root)
            and _looks_like_top_level_surface(path, app_root)
        ):
            hit = f"{relative_path}: embedded_ai_surface"
            if hit not in seen_embedded:
                seen_embedded.add(hit)
                embedded_surface_hits.append(hit)

    if not candidate_roots:
        return {
            "user_reachable": False,
            "route_registered": False,
            "navigation_invoked": False,
            "entry_surface_visible": False,
            "claimable": False,
            "candidate_files": [],
            "evidence": {
                "embedded_surface_hits": [],
                "route_registration_hits": [],
                "navigation_invocation_hits": [],
                "entry_surface_hits": [],
                "ignored_navigation_shell_hits": [],
            },
        }

    ignored_navigation_shell_hits: list[str] = []
    seen_ignored: set[str] = set()

    for path, text in file_cache.items():
        if path in candidate_path_set:
            continue

        relative_path = str(path.relative_to(app_root))
        is_navigation_shell = _looks_like_navigation_shell_path(path, app_root)
        is_ui_surface = _looks_like_ui_surface(path, app_root, text)
        target_hits: list[str] = []
        for root, symbols in module_entry_symbols.items():
            if not symbols:
                continue
            for symbol in sorted(symbols):
                if not re.search(rf"\b{re.escape(symbol)}\b", text):
                    continue
                target_hits.append(symbol)
            route_symbols = module_route_symbols.get(root, set())
            for symbol in sorted(route_symbols):
                if symbol in text:
                    target_hits.append(symbol)
        route_hits = _collect_candidate_route_hits(text)
        target_hits.extend(route_hits)
        target_hits = list(dict.fromkeys(target_hits))
        if not target_hits:
            continue

        if is_navigation_shell:
            for target in target_hits:
                hit = f"{relative_path}: {target}"
                if hit not in seen_route_registration:
                    seen_route_registration.add(hit)
                    route_registration_hits.append(hit)
            if is_ui_surface and _looks_like_top_level_surface(path, app_root) and _has_user_entry_trigger(text):
                for target in target_hits:
                    hit = f"{relative_path}: {target}"
                    if hit not in seen_entry_surface:
                        seen_entry_surface.add(hit)
                        entry_surface_hits.append(hit)
            else:
                for target in target_hits:
                    hit = f"{relative_path}: {target}"
                    if hit not in seen_ignored:
                        seen_ignored.add(hit)
                        ignored_navigation_shell_hits.append(hit)
            continue

        if _has_navigation_invocation(text) or _has_tab_surface_mount(text):
            for target in target_hits:
                hit = f"{relative_path}: {target}"
                if hit not in seen_navigation:
                    seen_navigation.add(hit)
                    navigation_invocation_hits.append(hit)

        if is_ui_surface and _looks_like_top_level_surface(path, app_root):
            for target in target_hits:
                hit = f"{relative_path}: {target}"
                if hit not in seen_entry_surface:
                    seen_entry_surface.add(hit)
                    entry_surface_hits.append(hit)

    route_registered = bool(route_registration_hits or embedded_surface_hits)
    navigation_invoked = bool(navigation_invocation_hits or embedded_surface_hits)
    entry_surface_visible = bool(entry_surface_hits or embedded_surface_hits)
    claimable = bool(
        embedded_surface_hits
        or (navigation_invoked and entry_surface_visible)
        or (route_registered and entry_surface_visible)
        or (route_registered and navigation_invoked)
    )
    user_reachable = bool(claimable or route_registered or navigation_invoked or entry_surface_visible)
    return {
        "user_reachable": user_reachable,
        "route_registered": route_registered,
        "navigation_invoked": navigation_invoked,
        "entry_surface_visible": entry_surface_visible,
        "claimable": claimable,
        "candidate_files": candidate_files[:12],
        "evidence": {
            "embedded_surface_hits": embedded_surface_hits[:12],
            "route_registration_hits": route_registration_hits[:12],
            "navigation_invocation_hits": navigation_invocation_hits[:12],
            "entry_surface_hits": entry_surface_hits[:12],
            "ignored_navigation_shell_hits": ignored_navigation_shell_hits[:12],
        },
    }


def _capability_active(result: dict[str, object], capability: str) -> bool:
    capability_candidates = result.get("capability_candidates", {})
    payload = capability_candidates.get(capability, {}) if isinstance(capability_candidates, dict) else {}
    return isinstance(payload, dict) and float(payload.get("raw_score", payload.get("score", 0.0))) >= ACTIVE_CAPABILITY_THRESHOLD


def apply_capability_reachability_gates(result: dict[str, object]) -> None:
    capability_candidates = result.get("capability_candidates", {})
    if not isinstance(capability_candidates, dict):
        return

    reachability_summary: dict[str, dict[str, object]] = {}
    for capability, payload in capability_candidates.items():
        if not isinstance(payload, dict):
            continue
        raw_score = float(payload.get("raw_score", payload.get("score", 0.0)))
        payload["raw_score"] = raw_score
        user_reachable = True
        reachability: dict[str, object] | None = None
        if capability in {"ai_chat", "ai_image_generation"}:
            signals = result.get("ai_signals", {})
            if isinstance(signals, dict):
                user_reachable = bool(signals.get("user_reachable"))
                maybe_reachability = signals.get("reachability")
                if isinstance(maybe_reachability, dict):
                    reachability = maybe_reachability
        payload["user_reachable"] = user_reachable
        if isinstance(reachability, dict):
            payload["reachability"] = reachability
        if not user_reachable and raw_score >= ACTIVE_CAPABILITY_THRESHOLD:
            payload["score"] = 0.0
            payload["confidence"] = "low"
            if capability in {"ai_chat", "ai_image_generation"}:
                ai_signals = result.get("ai_signals", {})
                if isinstance(ai_signals, dict) and ai_signals.get("residual_code"):
                    payload["downrank_reason"] = "residual_code"
        reachability_summary[capability] = {
            "active_in_code": raw_score >= ACTIVE_CAPABILITY_THRESHOLD,
            "user_reachable": user_reachable,
        }
    result["capability_reachability"] = reachability_summary


def extract_swift_evidence(app_root: Path) -> tuple[dict[str, list[str]], list[str], list[str]]:
    screens: set[str] = set()
    routes: set[str] = set()
    entities: set[str] = set()
    actions: set[str] = set()
    ui_strings: set[str] = set()
    urls: set[str] = set()
    iap_codes: set[str] = set()

    for path in _swift_source_files(app_root):
        text = read_text(path)
        for match in SCREEN_TYPE_PATTERN.findall(text):
            screens.add(match)
        for match in TYPE_PATTERN.findall(text):
            if match.endswith(("View", "ViewController", "Controller", "Coordinator", "Screen", "Page")):
                screens.add(match)
        for match in ENTITY_PATTERN.findall(text):
            entities.add(match)
        for match in FUNC_PATTERN.findall(text):
            if match not in {"body", "makeUIView", "updateUIView", "viewDidLoad"}:
                actions.add(match)
        for route in ROUTE_PATTERN.findall(text):
            routes.add(route)
        for item in extract_ui_strings(text):
            ui_strings.add(item)
        for code in extract_iap_codes_from_content(text):
            iap_codes.add(code)
        for url in URL_PATTERN.findall(text):
            urls.add(url)
        lower_name = path.stem.lower()
        if any(token in lower_name for token in ("view", "controller", "screen", "page", "profile", "feed")):
            screens.add(path.stem)

    return {
        "screens": sorted(screens),
        "routes": sorted(routes),
        "entities": sorted(entities),
        "actions": sorted(actions),
        "ui_strings": sorted(ui_strings),
    }, sorted(urls), sorted(iap_codes)


def inspect(app_root: Path) -> dict[str, object]:
    app_name, app_slug = extract_name(app_root)
    evidence, urls, iap_codes = extract_swift_evidence(app_root)
    result = build_inspect_result(
        source_stack="swift",
        app_root=app_root,
        app_name=app_name,
        app_slug=app_slug,
        permissions=extract_permissions(app_root),
        dependencies=extract_dependencies(app_root),
        evidence=evidence,
        brand_colors=extract_brand_colors_from_xcassets(app_root),
        urls=urls,
        iap_codes=iap_codes,
    )
    ai_reachability = analyze_swift_ai_reachability(app_root)
    ai_signals = result.get("ai_signals", {})
    if isinstance(ai_signals, dict):
        ai_file_cache = {
            str(path.relative_to(app_root)): read_text(path)
            for path in _swift_source_files(app_root)
        }
        ai_signals = finalize_ai_signals(ai_signals, ai_reachability, ai_file_cache)
        preview_profile = ai_signals.get("review_profile")
        if isinstance(preview_profile, dict):
            preview_profile["code_present_needs_face_data_clauses"] = bool(preview_profile.get("needs_face_data_clauses"))
        result["ai_signals"] = ai_signals

    apply_capability_reachability_gates(result)

    result["access_signals"] = analyze_access_signals(
        {
            str(path.relative_to(app_root)): read_text(path)
            for path in _swift_source_files(app_root)
        },
        result.get("capability_candidates", {}),
        result.get("dependencies", []),
        urls,
    )

    privacy_signals = result.get("privacy_signals", {})
    if isinstance(privacy_signals, dict):
        privacy_signals["ai_features"] = bool(result.get("ai_signals", {}).get("disclosure_required"))
        privacy_signals["credential_auth"] = bool(result.get("access_signals", {}).get("credential_account"))
        result["privacy_signals"] = privacy_signals

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract native Swift iOS app evidence for AppListing generation.")
    parser.add_argument("--target", required=True, help="Path to the Swift app root")
    args = parser.parse_args()
    root = Path(args.target).resolve()
    print(json.dumps(inspect(root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
