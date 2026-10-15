"""Build a small, evidence-backed product profile for user-facing copy."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


FEATURE_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "journal_or_notes",
        "title": "Create and revisit entries",
        "body": "Write, organize, and return to the entries you choose to keep.",
        "purpose": "creating and revisiting entries",
        "surface": (r"journal", r"note", r"diary", r"entry", r"memory", r"record"),
        "route": (r"/journal", r"/note", r"/diary", r"/entry", r"/memory", r"/record"),
        "ui": (r"write your first", r"new entry", r"save note", r"journal", r"diary", r"memory"),
        "priority": 100,
    },
    {
        "id": "photo_media",
        "title": "Bring in your photos",
        "body": "Choose photos from your device or use the camera when the feature is available.",
        "purpose": "bringing in photos",
        "surface": (r"photo", r"album", r"gallery", r"media"),
        "route": (r"/photo", r"/album", r"/gallery", r"/media"),
        "ui": (r"choose photos", r"take a photo", r"photo library", r"add photos", r"camera"),
        "priority": 90,
    },
    {
        "id": "collections",
        "title": "Organize collections",
        "body": "Group related items so they are easier to return to and review.",
        "purpose": "organizing collections",
        "surface": (r"album", r"collection", r"folder", r"trip", r"playlist"),
        "route": (r"/album", r"/collection", r"/folder", r"/trip", r"/playlist"),
        "ui": (r"create .*trip", r"saved collection", r"add to album", r"organize"),
        "priority": 80,
    },
    {
        "id": "timeline_history",
        "title": "Review your history",
        "body": "Move through dated items, highlights, or saved history at your own pace.",
        "purpose": "reviewing history",
        "surface": (r"timeline", r"calendar", r"history", r"onthisday", r"highlights"),
        "route": (r"/timeline", r"/calendar", r"/history", r"/on-this-day"),
        "ui": (r"timeline", r"calendar", r"on this day", r"annual review", r"highlights"),
        "priority": 75,
    },
    {
        "id": "search_and_filters",
        "title": "Find what matters",
        "body": "Use search or filters to return to the items you want.",
        "purpose": "finding what matters",
        "surface": (r"search", r"filter"),
        "route": (r"/search", r"/filter", r"/results"),
        "ui": (r"search", r"filter", r"saved filter", r"matching"),
        "priority": 65,
    },
    {
        "id": "backup_and_export",
        "title": "Keep a copy",
        "body": "Use the available data export or backup tools to keep a copy of saved content.",
        "purpose": "keeping copies of saved content",
        "surface": (r"(?:backup|export|restorebackup)(?:view|screen|controller|page|service)$", r"(?:^|[_/])(?:backup|export)(?:[_/]|$)"),
        "route": (r"/(?:backup|export|restore-backup)(?:/|$)",),
        "ui": (r"\b(?:export|restore|import)\s+(?:a\s+|your\s+|all\s+)?(?:backup|saved (?:data|content)|app data|data archive)\b", r"\b(?:create|save)\s+(?:a\s+|your\s+)?backup\b", r"^backup(?: and restore)?$", r"^pinfi backup$"),
        "priority": 60,
    },
    {
        "id": "profile_and_preferences",
        "title": "Shape your profile",
        "body": "Update the personal details and preferences available in the app.",
        "purpose": "maintaining personal details",
        "surface": (r"profile", r"settings", r"preferences"),
        "route": (r"/profile", r"/settings", r"/preferences", r"/me"),
        "ui": (r"edit profile", r"profile", r"settings", r"preferences"),
        "priority": 45,
    },
    {
        "id": "sharing",
        "title": "Share when you choose",
        "body": "Use the available share flow to choose where to send selected content.",
        "purpose": "sharing selected content",
        "surface": (r"share", r"sharing"),
        "route": (r"/share",),
        "ui": (r"share", r"send a copy"),
        "priority": 40,
    },
)

DOC_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json"}
IGNORED_DIRS = {".git", ".dart_tool", "build", "packages", "package", "applisting", "node_modules"}


def _read_project_docs(app_root: Path) -> str:
    parts: list[str] = []
    candidates = [app_root / "README.md", app_root / "docs"]
    for root in candidates:
        paths = [root] if root.is_file() else root.rglob("*") if root.is_dir() else []
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in DOC_SUFFIXES:
                continue
            if any(part.lower() in IGNORED_DIRS for part in path.relative_to(app_root).parts):
                continue
            try:
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return "\n".join(parts)


def _match(values: list[str], patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for value in values:
        lowered = str(value).lower()
        if any(re.search(pattern, lowered) for pattern in patterns):
            hits.append(str(value))
    return sorted(set(hits))


def _feature_from_rule(rule: dict[str, Any], evidence: dict[str, list[str]], docs: str, permissions: dict[str, str]) -> dict[str, Any] | None:
    surface_hits = _match(evidence.get("screens", []), rule["surface"])
    route_hits = _match(evidence.get("routes", []), rule["route"])
    ui_hits = _match(evidence.get("ui_strings", []), rule["ui"])
    doc_hits = []
    for pattern in (*rule["surface"], *rule["ui"]):
        if re.search(pattern, docs, re.IGNORECASE):
            doc_hits.append(pattern)
    score = len(surface_hits) * 3 + len(route_hits) * 4 + len(ui_hits) * 2 + len(doc_hits)
    if score < 4:
        return None
    return {
        "id": rule["id"],
        "title": rule["title"],
        "body": rule["body"],
        "purpose": rule["purpose"],
        "status": "confirmed" if surface_hits or route_hits or len(ui_hits) >= 2 else "candidate",
        "priority": rule["priority"],
        "evidence": {
            "screens": surface_hits[:6],
            "routes": route_hits[:6],
            "ui_strings": ui_hits[:6],
            "project_docs": doc_hits[:6],
        },
    }


def build_project_profile(
    app_root: Path,
    evidence: dict[str, list[str]],
    permissions: dict[str, str],
    network_destinations: list[str] | None = None,
) -> dict[str, Any]:
    docs = _read_project_docs(app_root)
    features = [
        feature
        for rule in FEATURE_RULES
        if (feature := _feature_from_rule(rule, evidence, docs, permissions)) is not None
    ]
    features.sort(key=lambda item: (-int(item["priority"]), str(item["id"])))
    confirmed = [item for item in features if item["status"] == "confirmed"]
    labels = [str(item["purpose"]) for item in confirmed[:3]]
    if labels:
        purpose = "A focused app for " + (", ".join(labels[:-1]) + f", and {labels[-1]}" if len(labels) > 1 else labels[0]) + "."
    else:
        purpose = "An app built around the functions available in the project."
    return {
        "purpose": {"value": purpose, "status": "confirmed" if confirmed else "unknown", "evidence": ["project evidence"] if confirmed else []},
        "features": features,
        "network_destinations": sorted(set(network_destinations or [])),
        "unknowns": [] if confirmed else ["product.purpose", "product.features"],
        "conflicts": [],
    }
