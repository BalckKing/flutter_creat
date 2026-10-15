#!/usr/bin/env python3
"""Extract structured Flutter app evidence for iOS AppListing generation."""

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
    extract_brand_colors_from_dart,
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


CLASS_PATTERN = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)")
ROUTE_PATTERN = re.compile(r"['\"](/[A-Za-z0-9_\-/]+)['\"]")
ACTION_PATTERN = re.compile(r"\b([a-z][A-Za-z0-9_]{2,})\s*\(")
DEPENDENCY_PATTERN = re.compile(r"(?m)^  ([A-Za-z0-9_]+):")
ENTITY_HINT_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:Entity|Model|Plan|Record|Message|Conversation|Post|User))\b")
STRING_ROUTE_PATTERN = re.compile(r"['\"]([A-Z][A-Za-z0-9_]*(?:Page|Screen|View|Controller)|/[A-Za-z0-9_\-/]+)['\"]")
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
    "studio",
    "beauty",
    "beauty_filter",
    "virtual_makeup",
    "makeup",
    "retouch",
    "edit_desk",
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
    "ai umbrella preview",
    "umbrella preview",
    "preview consent",
    "render umbrella preview",
    "save preview to photos",
    "ai mask checks",
    "mask tone check",
    "skin finish check",
    "shade preview",
    "virtual makeup",
    "beauty filter",
    "face data consent",
    "sending your selected photo for ai processing",
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
    "/ai-beauty/",
    "/virtual-makeup",
    "/beauty-filter",
)
TRANSLATION_REACHABILITY_PATH_HINTS = (
    "translate",
    "translation",
)
TRANSLATION_REACHABILITY_TEXT_HINTS = (
    "text translation",
    "voice translation",
    "image translation",
    "translate image",
    "translate text",
    "text translator",
    "voice translator",
    "source language",
    "target language",
)
BEAUTY_REACHABILITY_PATH_HINTS = (
    "beauty",
    "retouch",
    "filter",
    "photo_editor",
    "image_editor",
    "overlay",
)
BEAUTY_REACHABILITY_TEXT_HINTS = (
    "beauty",
    "retouch",
    "filter",
    "photo editor",
    "portrait photo editor",
    "overlay",
    "crop",
    "mirror",
)
MESSAGING_FILE_HINTS = ("chat", "message", "thread", "conversation", "inbox")
MESSAGING_TEXT_HINTS = ("chat", "message", "thread", "conversation", "inbox")
MESSAGING_WORD_PATTERN = re.compile(r"\b(chat|chats|message|messages|thread|threads|conversation|conversations|inbox)\b")
SEED_MESSAGING_MARKERS = (
    "seedmessages",
    "seedconversations",
    "seedprovider",
    "meridiancachepayloadbridge",
    "sharedpreferences",
    "commitencodedlist",
    "getjsonlist",
    "collectmessagesbyconversationid",
    "collectconversations",
    "manage local data storage",
    "本地数据",
)
REMOTE_MESSAGING_IMPORT_MARKERS = (
    "package:dio/",
    "package:http/",
    "package:websocket_channel/",
    "package:socket_io_client/",
    "package:stomp_dart_client/",
    "package:mqtt_client/",
    "cloud_firestore",
    "firebase_database",
    "supabase_flutter",
    "stream_chat_flutter",
)
REMOTE_MESSAGING_TRANSPORT_PATTERNS = (
    re.compile(r"https?://[^\s\"']*(messages?|conversations?|inbox|threads?|im)\b"),
    re.compile(r"wss?://"),
    re.compile(r"collection\(['\"](messages|conversations|threads)['\"]\)"),
    re.compile(r"\b(firebasefirestore|supabase|streamchat|socketio|websocket|signalr|mqtt|stomp)\b"),
)
REMOTE_MESSAGING_SERVICE_PATTERNS = (
    re.compile(r"\b(chat|message|conversation|thread)(api|service|repository|client)\b"),
    re.compile(r"\b(send|fetch|load|get|list|stream|subscribe)[a-z0-9_]*(message|conversation|thread|inbox)\b"),
)
ACTIVE_CAPABILITY_THRESHOLD = 1.0
FLUTTER_AI_NAV_ACTION_HINTS = (
    "navigator.push",
    "navigator.of(context).push",
    "navigator.pushnamed",
    "context.push",
    "context.go",
    "get.to",
    "get.off",
    "navigationdestination",
)
FLUTTER_AI_NAV_TRIGGER_HINTS = (
    "onpressed",
    "ontap",
    "gesturedetector",
    "inkwell",
    "iconbutton",
    "elevatedbutton",
    "textbutton",
    "floatingactionbutton",
    "bottomnavigationbar",
    "tabbar",
)
FLUTTER_AI_TAB_CONTAINER_HINTS = (
    "indexedstack(",
    "pageview(",
    "tabbarview(",
    "children:",
)


def extract_name(app_root: Path) -> tuple[str, str]:
    info_plist = app_root / "ios" / "Runner" / "Info.plist"
    if info_plist.exists():
        with info_plist.open("rb") as handle:
            info = plistlib.load(handle)
        display = str(info.get("CFBundleDisplayName") or "").strip()
        if display:
            return display, to_slug(display)

    pubspec = app_root / "pubspec.yaml"
    if pubspec.exists():
        match = re.search(r"(?m)^name:\s*['\"]?([^'\"]+?)['\"]?\s*$", read_text(pubspec))
        if match:
            value = match.group(1).strip()
            return title_case_slug(value), to_slug(value)

    return title_case_slug(app_root.name), to_slug(app_root.name)


def extract_permissions(app_root: Path) -> dict[str, str]:
    info_plist = app_root / "ios" / "Runner" / "Info.plist"
    if not info_plist.exists():
        return {}
    with info_plist.open("rb") as handle:
        info = plistlib.load(handle)
    return parse_permissions_from_info(info)


def extract_dependencies(app_root: Path) -> list[str]:
    pubspec = app_root / "pubspec.yaml"
    if not pubspec.exists():
        return []
    dependencies: list[str] = []
    in_dependencies = False
    for raw_line in read_text(pubspec).splitlines():
        line = raw_line.rstrip()
        if line.startswith("dependencies:"):
            in_dependencies = True
            continue
        if in_dependencies and re.match(r"^[A-Za-z_]", line):
            break
        if not in_dependencies:
            continue
        match = DEPENDENCY_PATTERN.match(line)
        if match:
            dependencies.append(match.group(1))
    return sorted(set(dependencies))


def extract_dart_evidence(app_root: Path) -> tuple[dict[str, list[str]], list[Path], list[str]]:
    lib_root = app_root / "lib"
    screens: set[str] = set()
    routes: set[str] = set()
    entities: set[str] = set()
    actions: set[str] = set()
    ui_strings: set[str] = set()
    dart_files: list[Path] = []
    urls: set[str] = set()

    if not lib_root.exists():
        return {"screens": [], "routes": [], "entities": [], "actions": [], "ui_strings": []}, [], []

    for path in iter_files(lib_root, "*.dart"):
        dart_files.append(path)
        text = read_text(path)
        lower_rel = str(path.relative_to(lib_root)).lower()

        for class_name in CLASS_PATTERN.findall(text):
            screens.add(class_name)
            if class_name.endswith(("Entity", "Model", "Plan", "Record", "Message", "Conversation", "Post", "User")):
                entities.add(class_name)
        for route in ROUTE_PATTERN.findall(text):
            routes.add(route)
        for entity in ENTITY_HINT_PATTERN.findall(text):
            entities.add(entity)
        for action in ACTION_PATTERN.findall(text):
            if action in {"if", "for", "while", "switch", "return", "print", "setState", "build", "createState"}:
                continue
            actions.add(action)
        for item in extract_ui_strings(text):
            ui_strings.add(item)
        for match in URL_PATTERN.findall(text):
            urls.add(match)

        if any(token in lower_rel for token in ("screen", "page", "view", "detail", "feed", "profile")):
            screens.add(path.stem)

    return {
        "screens": sorted(screens),
        "routes": sorted(routes),
        "entities": sorted(entities),
        "actions": sorted(actions),
        "ui_strings": sorted(ui_strings),
    }, dart_files, sorted(urls)


def _append_hits(target: list[str], values: list[str], *, limit: int = 6) -> None:
    for value in values:
        if value in target:
            continue
        target.append(value)
        if len(target) >= limit:
            break


def _has_messaging_surface(text: str) -> bool:
    return bool(MESSAGING_WORD_PATTERN.search(text.lower()))


def _has_messaging_path_hint(path: Path, lib_root: Path) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    return any(token in lowered_rel for token in MESSAGING_FILE_HINTS)


def _is_messaging_candidate(path: Path, lib_root: Path, text: str) -> bool:
    return _has_messaging_path_hint(path, lib_root) or _has_messaging_surface(text)


def _looks_like_non_user_messaging_module(path: Path, lib_root: Path, text: str) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    lowered_text = text.lower()
    if any(token in lowered_rel for token in (*AI_REACHABILITY_PATH_HINTS, *TRANSLATION_REACHABILITY_PATH_HINTS)):
        return True
    if any(token in lowered_text for token in (*AI_REACHABILITY_TEXT_HINTS, *TRANSLATION_REACHABILITY_TEXT_HINTS)):
        return True
    return any(
        token in lowered_text
        for token in (
            "chat/completions",
            "style assist",
            "ai guide",
            "translation provider",
            "dashscope",
        )
    )


def analyze_flutter_messaging_signals(dart_files: list[Path], app_root: Path) -> dict[str, object]:
    lib_root = app_root / "lib"
    candidate_files: list[str] = []
    seed_hits: list[str] = []
    remote_import_hits: list[str] = []
    remote_transport_hits: list[str] = []
    remote_service_hits: list[str] = []
    surface_backed = False

    for path in dart_files:
        text = read_text(path)
        if not _is_messaging_candidate(path, lib_root, text):
            continue
        if not _has_messaging_path_hint(path, lib_root) and _looks_like_non_user_messaging_module(path, lib_root, text):
            continue

        lowered_text = text.lower()
        relative_path = str(path.relative_to(app_root))
        _append_hits(candidate_files, [relative_path])
        surface_backed = surface_backed or _has_messaging_path_hint(path, lib_root) or _has_messaging_surface(text)

        seed_markers = [marker for marker in SEED_MESSAGING_MARKERS if marker in lowered_text]
        _append_hits(seed_hits, [f"{relative_path}: {marker}" for marker in seed_markers])

        import_markers = [marker for marker in REMOTE_MESSAGING_IMPORT_MARKERS if marker in lowered_text]
        _append_hits(remote_import_hits, [f"{relative_path}: {marker}" for marker in import_markers])

        transport_hits = [
            match.group(0)
            for pattern in REMOTE_MESSAGING_TRANSPORT_PATTERNS
            for match in pattern.finditer(lowered_text)
        ]
        _append_hits(remote_transport_hits, [f"{relative_path}: {item}" for item in transport_hits])

        service_hits = [match.group(0) for pattern in REMOTE_MESSAGING_SERVICE_PATTERNS for match in pattern.finditer(lowered_text)]
        _append_hits(remote_service_hits, [f"{relative_path}: {item}" for item in service_hits])

    remote_backend = bool(remote_transport_hits) or bool(remote_import_hits and remote_service_hits)
    seed_backed = bool(seed_hits)
    real_user_chat = remote_backend and surface_backed

    return {
        "candidate_files": candidate_files,
        "seed_backed": seed_backed,
        "remote_messaging_backend": remote_backend,
        "real_user_chat": real_user_chat,
        "evidence": {
            "seed_markers": seed_hits,
            "remote_import_markers": remote_import_hits,
            "remote_transport_markers": remote_transport_hits,
            "remote_service_markers": remote_service_hits,
        },
    }


def _ai_module_root(path: Path, lib_root: Path) -> Path:
    rel = path.relative_to(lib_root)
    parts = rel.parts
    if "features" in parts:
        index = parts.index("features")
        if index + 1 < len(parts):
            return Path(*parts[: index + 2])
    if rel.parent != Path("."):
        return rel.parent
    return rel


def _path_is_within(rel: Path, root: Path) -> bool:
    return rel.parts[: len(root.parts)] == root.parts


def _file_matches_hints(path: Path, lib_root: Path, text: str, path_hints: tuple[str, ...], text_hints: tuple[str, ...]) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    lowered_text = text.lower()
    return any(token in lowered_rel for token in path_hints) or any(token in lowered_text for token in text_hints)


def _collect_ai_symbols(text: str, path: Path) -> set[str]:
    symbols = {
        class_name
        for class_name in CLASS_PATTERN.findall(text)
        if class_name.endswith(("Page", "Screen", "View", "Controller", "Binding", "Coordinator"))
    }
    if path.stem.endswith(("page", "screen", "view", "controller", "binding", "coordinator")):
        stem = "".join(part.capitalize() for part in path.stem.split("_"))
        if stem:
            symbols.add(stem)
    return symbols


def _collect_entry_symbols(text: str, path: Path) -> set[str]:
    symbols = {
        class_name
        for class_name in CLASS_PATTERN.findall(text)
        if class_name.endswith(("Page", "Screen", "View"))
    }
    if path.stem.endswith(("page", "screen", "view")):
        stem = "".join(part.capitalize() for part in path.stem.split("_"))
        if stem:
            symbols.add(stem)
    return symbols


def _looks_like_ui_surface(path: Path, lib_root: Path, text: str) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    if any(token in lowered_rel for token in ("page", "screen", "view", "home", "main", "nav", "route", "tab")):
        return True
    return any(class_name.endswith(("Page", "Screen", "View")) for class_name in CLASS_PATTERN.findall(text))


def _looks_like_navigation_shell_path(path: Path, lib_root: Path) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    return any(token in lowered_rel for token in ("nav", "route", "router", "routing", "registry", "shell"))


def _looks_like_top_level_surface(path: Path, lib_root: Path) -> bool:
    lowered_rel = str(path.relative_to(lib_root)).lower()
    return any(token in lowered_rel for token in ("home", "main", "root", "dashboard", "tab", "feed", "profile"))


def _analyze_reachability_for_candidate_paths(
    candidate_paths: list[Path],
    dart_files: list[Path],
    app_root: Path,
    *,
    text_hints: tuple[str, ...],
) -> dict[str, object]:
    lib_root = app_root / "lib"
    module_entry_symbols: dict[Path, set[str]] = {}
    candidate_roots: list[Path] = []
    candidate_files: list[str] = []
    candidate_path_set = set(candidate_paths)

    file_cache: dict[Path, str] = {}
    for path in dart_files:
        text = read_text(path)
        file_cache[path] = text
        if path not in candidate_path_set:
            continue
        root = _ai_module_root(path, lib_root)
        if root not in candidate_roots:
            candidate_roots.append(root)
        module_entry_symbols.setdefault(root, set()).update(_collect_entry_symbols(text, path))
        relative_path = str(path.relative_to(app_root))
        if relative_path not in candidate_files:
            candidate_files.append(relative_path)

    if not candidate_roots:
        return {
            "user_reachable": False,
            "candidate_files": [],
            "evidence": {
                "external_references": [],
                "surface_hits": [],
            },
        }

    external_reference_hits: list[str] = []
    surface_hits: list[str] = []
    seen_external: set[str] = set()
    seen_surface: set[str] = set()

    for path, text in file_cache.items():
        rel = path.relative_to(lib_root)
        if any(_path_is_within(rel, root) for root in candidate_roots):
            continue

        lowered_text = text.lower()
        relative_path = str(path.relative_to(app_root))

        if _looks_like_ui_surface(path, lib_root, text):
            for token in text_hints:
                if token not in lowered_text:
                    continue
                hit = f"{relative_path}: {token}"
                if hit not in seen_surface:
                    seen_surface.add(hit)
                    surface_hits.append(hit)
                break

        for root, symbols in module_entry_symbols.items():
            if not symbols:
                continue
            for symbol in sorted(symbols):
                if not re.search(rf"\b{re.escape(symbol)}\b", text):
                    continue
                hit = f"{relative_path}: {symbol}"
                if hit in seen_external:
                    continue
                seen_external.add(hit)
                external_reference_hits.append(hit)

    user_reachable = bool(external_reference_hits or surface_hits)
    return {
        "user_reachable": user_reachable,
        "candidate_files": candidate_files[:12],
        "evidence": {
            "external_references": external_reference_hits[:12],
            "surface_hits": surface_hits[:12],
        },
    }


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
    return any(token in lowered_text for token in FLUTTER_AI_NAV_ACTION_HINTS)


def _has_user_entry_trigger(text: str) -> bool:
    lowered_text = text.lower()
    return any(token in lowered_text for token in FLUTTER_AI_NAV_TRIGGER_HINTS)


def _has_tab_surface_mount(text: str) -> bool:
    lowered_text = text.lower()
    return any(token in lowered_text for token in FLUTTER_AI_TAB_CONTAINER_HINTS)


def analyze_flutter_module_reachability(
    dart_files: list[Path],
    app_root: Path,
    *,
    path_hints: tuple[str, ...],
    text_hints: tuple[str, ...],
) -> dict[str, object]:
    lib_root = app_root / "lib"
    candidate_paths: list[Path] = []
    for path in dart_files:
        text = read_text(path)
        lowered_rel = str(path.relative_to(lib_root)).lower()
        if not _file_matches_hints(path, lib_root, text, path_hints, text_hints):
            continue
        if _looks_like_navigation_shell_path(path, lib_root) and not any(token in lowered_rel for token in path_hints):
            continue
        candidate_paths.append(path)
    return _analyze_reachability_for_candidate_paths(
        candidate_paths,
        dart_files,
        app_root,
        text_hints=text_hints,
    )


def analyze_flutter_ai_reachability(dart_files: list[Path], app_root: Path) -> dict[str, object]:
    lib_root = app_root / "lib"
    candidate_paths: list[Path] = []
    candidate_path_set: set[Path] = set()
    file_cache: dict[Path, str] = {}

    for path in dart_files:
        text = read_text(path)
        file_cache[path] = text
        lowered_rel = str(path.relative_to(lib_root)).lower()
        if not _file_matches_hints(path, lib_root, text, AI_REACHABILITY_PATH_HINTS, AI_REACHABILITY_TEXT_HINTS):
            continue
        if _looks_like_navigation_shell_path(path, lib_root) and not any(token in lowered_rel for token in AI_REACHABILITY_PATH_HINTS):
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
        root = _ai_module_root(path, lib_root)
        if root not in candidate_roots:
            candidate_roots.append(root)
        module_entry_symbols.setdefault(root, set()).update(_collect_entry_symbols(text, path))
        module_route_symbols.setdefault(root, set()).update(_collect_candidate_route_symbols(text))
        relative_path = str(path.relative_to(app_root))
        if relative_path not in candidate_files:
            candidate_files.append(relative_path)
        if (
            _looks_like_ui_surface(path, lib_root, text)
            and not _looks_like_navigation_shell_path(path, lib_root)
            and _looks_like_top_level_surface(path, lib_root)
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
        is_navigation_shell = _looks_like_navigation_shell_path(path, lib_root)
        is_ui_surface = _looks_like_ui_surface(path, lib_root, text)
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
            shell_mounts_ai_surface = (
                is_ui_surface
                and _looks_like_top_level_surface(path, lib_root)
                and (_has_user_entry_trigger(text) or _has_tab_surface_mount(text))
            )
            for target in target_hits:
                hit = f"{relative_path}: {target}"
                if hit not in seen_route_registration:
                    seen_route_registration.add(hit)
                    route_registration_hits.append(hit)
            if shell_mounts_ai_surface:
                for target in target_hits:
                    hit = f"{relative_path}: {target}"
                    if hit not in seen_entry_surface:
                        seen_entry_surface.add(hit)
                        entry_surface_hits.append(hit)
                    if hit not in seen_navigation:
                        seen_navigation.add(hit)
                        navigation_invocation_hits.append(hit)
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

        if is_ui_surface and _looks_like_top_level_surface(path, lib_root):
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


def analyze_flutter_translation_reachability(dart_files: list[Path], app_root: Path) -> dict[str, object]:
    return analyze_flutter_module_reachability(
        dart_files,
        app_root,
        path_hints=TRANSLATION_REACHABILITY_PATH_HINTS,
        text_hints=TRANSLATION_REACHABILITY_TEXT_HINTS,
    )


def analyze_flutter_messaging_reachability(dart_files: list[Path], app_root: Path) -> dict[str, object]:
    lib_root = app_root / "lib"
    candidate_paths: list[Path] = []
    for path in dart_files:
        text = read_text(path)
        if not _is_messaging_candidate(path, lib_root, text):
            continue
        if not _has_messaging_path_hint(path, lib_root) and _looks_like_navigation_shell_path(path, lib_root):
            continue
        if not _has_messaging_path_hint(path, lib_root) and _looks_like_non_user_messaging_module(path, lib_root, text):
            continue
        candidate_paths.append(path)
    return _analyze_reachability_for_candidate_paths(
        candidate_paths,
        dart_files,
        app_root,
        text_hints=MESSAGING_TEXT_HINTS,
    )


def analyze_flutter_beauty_editing_reachability(dart_files: list[Path], app_root: Path) -> dict[str, object]:
    return analyze_flutter_module_reachability(
        dart_files,
        app_root,
        path_hints=BEAUTY_REACHABILITY_PATH_HINTS,
        text_hints=BEAUTY_REACHABILITY_TEXT_HINTS,
    )


def _capability_active(result: dict[str, object], capability: str) -> bool:
    capability_candidates = result.get("capability_candidates", {})
    payload = capability_candidates.get(capability, {}) if isinstance(capability_candidates, dict) else {}
    return isinstance(payload, dict) and float(payload.get("raw_score", payload.get("score", 0.0))) >= ACTIVE_CAPABILITY_THRESHOLD


def _gated_capability_reachability(result: dict[str, object], capability: str) -> tuple[bool, dict[str, object] | None]:
    if capability in {"translate_text", "translate_voice"}:
        signals = result.get("translation_signals", {})
        if isinstance(signals, dict):
            return bool(signals.get("user_reachable")), signals.get("reachability")
    if capability in {"ai_chat", "ai_image_generation"}:
        signals = result.get("ai_signals", {})
        if isinstance(signals, dict):
            return bool(signals.get("user_reachable")), signals.get("reachability")
    if capability == "messaging":
        signals = result.get("messaging_signals", {})
        if isinstance(signals, dict):
            return bool(signals.get("real_user_chat", signals.get("user_reachable"))), signals.get("reachability")
    if capability == "beauty_editing":
        signals = result.get("beauty_editing_signals", {})
        if isinstance(signals, dict):
            return bool(signals.get("user_reachable")), signals.get("reachability")
    return True, None


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
        user_reachable, reachability = _gated_capability_reachability(result, capability)
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


def inspect(app_root: Path) -> dict[str, object]:
    app_name, app_slug = extract_name(app_root)
    evidence, dart_files, urls = extract_dart_evidence(app_root)
    iap_codes: list[str] = []
    for path in dart_files:
        iap_codes.extend(extract_iap_codes_from_content(read_text(path)))
    result = build_inspect_result(
        source_stack="flutter",
        app_root=app_root,
        app_name=app_name,
        app_slug=app_slug,
        permissions=extract_permissions(app_root),
        dependencies=extract_dependencies(app_root),
        evidence=evidence,
        brand_colors=extract_brand_colors_from_dart(dart_files, app_root),
        urls=urls,
        iap_codes=iap_codes,
    )
    messaging_signals = analyze_flutter_messaging_signals(dart_files, app_root)
    messaging_reachability = analyze_flutter_messaging_reachability(dart_files, app_root)
    messaging_signals["user_reachable"] = bool(messaging_signals.get("candidate_files")) and bool(
        messaging_reachability.get("user_reachable")
    )
    messaging_signals["reachability"] = messaging_reachability
    messaging_signals["real_user_chat"] = bool(messaging_signals.get("remote_messaging_backend")) and bool(
        messaging_signals.get("user_reachable")
    )
    messaging_signals["disclosure_required"] = bool(messaging_signals.get("real_user_chat"))
    result["messaging_signals"] = messaging_signals

    beauty_editing_reachability = analyze_flutter_beauty_editing_reachability(dart_files, app_root)
    result["beauty_editing_signals"] = {
        "active": _capability_active(result, "beauty_editing"),
        "user_reachable": _capability_active(result, "beauty_editing")
        and bool(beauty_editing_reachability.get("user_reachable")),
        "reachability": beauty_editing_reachability,
        "disclosure_required": _capability_active(result, "beauty_editing")
        and bool(beauty_editing_reachability.get("user_reachable")),
    }

    ai_reachability = analyze_flutter_ai_reachability(dart_files, app_root)
    ai_signals = result.get("ai_signals", {})
    if isinstance(ai_signals, dict):
        ai_file_cache = {
            str(path.relative_to(app_root)): read_text(path)
            for path in dart_files
        }
        ai_signals = finalize_ai_signals(ai_signals, ai_reachability, ai_file_cache)
        preview_profile = ai_signals.get("review_profile")
        if isinstance(preview_profile, dict):
            preview_profile["code_present_needs_face_data_clauses"] = bool(preview_profile.get("needs_face_data_clauses"))
        result["ai_signals"] = ai_signals
    translation_reachability = analyze_flutter_translation_reachability(dart_files, app_root)
    translation_signals = result.get("translation_signals", {})
    if isinstance(translation_signals, dict):
        translation_signals["user_reachable"] = bool(translation_signals.get("active")) and bool(
            translation_reachability.get("user_reachable")
        )
        translation_signals["reachability"] = translation_reachability
        translation_signals["disclosure_required"] = bool(translation_signals.get("active")) and bool(
            translation_signals.get("user_reachable")
        )
        result["translation_signals"] = translation_signals

    apply_capability_reachability_gates(result)

    result["access_signals"] = analyze_access_signals(
        {
            str(path.relative_to(app_root)): read_text(path)
            for path in dart_files
        },
        result.get("capability_candidates", {}),
        result.get("dependencies", []),
        urls,
    )

    privacy_signals = result.get("privacy_signals", {})
    if isinstance(privacy_signals, dict):
        active_capabilities = {
            name
            for name, payload in result.get("capability_candidates", {}).items()
            if isinstance(payload, dict) and float(payload.get("score", 0.0)) >= ACTIVE_CAPABILITY_THRESHOLD
        }
        privacy_signals["payments"] = "recharge" in active_capabilities
        privacy_signals["user_content"] = bool({"feed", "post_creation", "messaging"} & active_capabilities)
        privacy_signals["community_ugc"] = bool({"feed", "post_creation"} & active_capabilities)
        privacy_signals["ai_features"] = bool(result.get("ai_signals", {}).get("disclosure_required"))
        privacy_signals["credential_auth"] = bool(result.get("access_signals", {}).get("credential_account"))
        result["privacy_signals"] = privacy_signals

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Flutter iOS app evidence for AppListing generation.")
    parser.add_argument("--target", required=True, help="Path to the Flutter app root")
    args = parser.parse_args()
    root = Path(args.target).resolve()
    print(json.dumps(inspect(root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
