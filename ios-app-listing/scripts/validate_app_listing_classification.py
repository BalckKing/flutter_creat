#!/usr/bin/env python3
"""Validate app-listing classification against extracted app evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ACTIVE_THRESHOLD = 1.0
EVIDENCE_SOURCE_KEYS = ("screens", "routes", "entities", "actions", "ui_strings")
CATEGORY_EVIDENCE_MARKERS = {
    "Business": ("invoice", "client", "crm", "sales", "merchant", "inventory", "operations", "lead"),
    "Education": ("lesson", "course", "quiz", "flashcard", "practice test", "classroom", "teacher"),
    "Entertainment": ("streaming", "watch now", "episode", "movie", "tv show", "series", "fan club"),
    "Food & Drink": ("restaurant", "menu", "recipe", "reservation", "delivery", "dining", "cafe", "ingredients"),
    "Graphics & Design": ("graphic design", "template editor", "poster maker", "flyer maker", "logo maker", "vector", "canvas"),
    "Health & Fitness": ("workout", "fitness", "meditation", "sleep tracker", "calorie", "step counter", "wellness", "yoga"),
    "Lifestyle": ("habit tracker", "daily routine", "journal", "self care", "home decor", "wardrobe", "pet care"),
    "Music": ("playlist", "album", "karaoke", "podcast", "beat maker", "metronome", "music player"),
    "Navigation": ("directions", "turn-by-turn", "turn by turn", "destination", "eta", "traffic", "route planner", "navigation"),
    "News": ("breaking news", "latest news", "headlines", "newsroom", "top stories", "world news", "local news", "publisher"),
    "Productivity": ("to-do", "todo", "task list", "calendar", "planner", "checklist", "reminder", "project board", "focus timer"),
    "Reference": ("dictionary", "encyclopedia", "glossary", "reference", "definitions", "lookup", "manual", "knowledge base"),
    "Sports": ("scoreboard", "match center", "standings", "fixtures", "team roster", "league table", "athlete stats", "live score"),
    "Weather": ("forecast", "hourly weather", "weather radar", "storm alert", "precipitation", "air quality", "uv index", "temperature"),
}

ACCOUNT_WORDING_PATTERNS = (
    re.compile(r"\buser accounts?\b"),
    re.compile(r"\baccounts?\b"),
    re.compile(r"\bregister\b"),
    re.compile(r"\blog[ -]?in\b"),
    re.compile(r"\bsign[ -]?in\b"),
    re.compile(r"\bcredentials?\b"),
    re.compile(r"\busername\b"),
    re.compile(r"\bpassword\b"),
)


def capability_payloads(evidence: dict) -> dict[str, dict]:
    raw = evidence.get("capability_candidates", {})
    if isinstance(raw, dict):
        return {
            str(name): payload
            for name, payload in raw.items()
            if isinstance(payload, dict)
        }
    if isinstance(raw, list):
        normalized: dict[str, dict] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            normalized[name] = item
        return normalized
    return {}


def active_capabilities(evidence: dict) -> set[str]:
    capability_candidates = capability_payloads(evidence)
    active = {
        name
        for name, payload in capability_candidates.items()
        if float(payload.get("score", 0.0)) >= ACTIVE_THRESHOLD
    }
    translation_signals = evidence.get("translation_signals", {})
    if isinstance(translation_signals, dict) and not translation_signals.get(
        "disclosure_required",
        translation_signals.get("user_reachable", True),
    ):
        active.discard("translate_text")
        active.discard("translate_voice")
    ai_signals = evidence.get("ai_signals", {})
    if isinstance(ai_signals, dict) and not ai_signals.get(
        "disclosure_required",
        ai_signals.get("claimable", ai_signals.get("user_reachable", True)),
    ):
        active.discard("ai_chat")
        active.discard("ai_image_generation")
    messaging_signals = evidence.get("messaging_signals", {})
    if isinstance(messaging_signals, dict) and not messaging_signals.get(
        "real_user_chat",
        messaging_signals.get("user_reachable", True),
    ):
        active.discard("messaging")
    beauty_editing_signals = evidence.get("beauty_editing_signals", {})
    if isinstance(beauty_editing_signals, dict) and not beauty_editing_signals.get(
        "disclosure_required",
        beauty_editing_signals.get("user_reachable", True),
    ):
        active.discard("beauty_editing")
    if isinstance(ai_signals, dict) and ai_signals.get(
        "disclosure_required",
        ai_signals.get("claimable", ai_signals.get("user_reachable", False)),
    ):
        if "beauty_editing" in active:
            active.add("ai_image_generation")
    return active


def evidence_blob(evidence: dict) -> str:
    values: list[str] = []
    raw_evidence = evidence.get("evidence", {})
    if isinstance(raw_evidence, dict):
        for key in EVIDENCE_SOURCE_KEYS:
            items = raw_evidence.get(key, [])
            if not isinstance(items, list):
                continue
            values.extend(str(item).strip().lower() for item in items if str(item).strip())
    values.extend(str(item).strip().lower() for item in evidence.get("dependencies", []) if str(item).strip())
    return "\n".join(values)


def has_category_evidence(blob: str, category: str) -> bool:
    return any(marker in blob for marker in CATEGORY_EVIDENCE_MARKERS.get(category, ()))


def access_mode(evidence: dict) -> str:
    access_signals = evidence.get("access_signals", {})
    if not isinstance(access_signals, dict):
        return "neutral"
    mode = str(access_signals.get("mode", "")).strip().lower()
    if mode in {"credential_account", "local_session", "community_only", "neutral"}:
        return mode
    if access_signals.get("credential_account"):
        return "credential_account"
    if access_signals.get("local_session"):
        return "local_session"
    if access_signals.get("community_features"):
        return "community_only"
    return "neutral"


def validate_classification(evidence: dict, classification: dict) -> list[str]:
    errors: list[str] = []
    active = active_capabilities(evidence)
    category = classification.get("category", "")
    blob = evidence_blob(evidence)
    current_access_mode = access_mode(evidence)

    if category == "Travel" and not ({"translate_voice", "translate_text"} & active and "location" in active):
        errors.append("Travel requires translation and location evidence, which are not present.")
    if category == "Utilities" and "location" in active and {"translate_voice", "translate_text"} & active:
        errors.append("Utilities is inconsistent when translation and location evidence imply Travel.")
    if category == "Social Networking" and not ("feed" in active and ("profile" in active or "post_creation" in active)):
        errors.append("Social Networking requires feed evidence plus profile or post_creation evidence.")
    if category == "Finance" and "budgeting" not in active and "recharge" not in active:
        errors.append("Finance requires budgeting or payment-management evidence.")
    if category == "Education" and "education" not in active and not has_category_evidence(blob, category):
        errors.append("Education requires lesson, course, or quiz evidence.")
    if category == "Photo & Video" and not ({"beauty_editing", "ai_tryon", "ai_image_generation"} & active):
        errors.append("Photo & Video requires editing, try-on, or image-generation evidence.")
    if category in {"Business", "Entertainment", "Graphics & Design", "Health & Fitness", "Lifestyle", "Music", "Productivity"} and not has_category_evidence(blob, category):
        errors.append(f"{category} requires supporting evidence in inspected screens, routes, actions, UI strings, or dependencies.")
    if category == "Navigation":
        if "location" not in active:
            errors.append("Navigation requires location evidence.")
        if not has_category_evidence(blob, category):
            errors.append("Navigation requires route, destination, traffic, or turn-by-turn evidence.")
    if category == "Weather" and not has_category_evidence(blob, category):
        errors.append("Weather requires forecast, radar, alert, or local weather evidence.")
    if category in {"Reference", "Food & Drink", "Sports", "News"} and not has_category_evidence(blob, category):
        errors.append(f"{category} requires supporting evidence in inspected screens, routes, actions, UI strings, or dependencies.")

    claimed_capabilities = classification.get("capabilities", [])
    if isinstance(claimed_capabilities, list):
        for capability in claimed_capabilities:
            if capability not in active:
                errors.append(f"Capability '{capability}' is not supported by active evidence.")

    if current_access_mode != "credential_account":
        classification_blob = "\n".join(
            [
                str(classification.get("reasoning", "")),
                str(classification.get("theme", "")),
                json.dumps(classification.get("theme_hint", {}), ensure_ascii=False),
            ]
        ).lower()
        for pattern in ACCOUNT_WORDING_PATTERNS:
            if pattern.search(classification_blob):
                errors.append(
                    "Classification must not use strong account/login wording unless inspect evidence supports credential_account access."
                )
                break

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate app-listing classification JSON.")
    parser.add_argument("--evidence-json", required=True, help="Path to inspect output JSON")
    parser.add_argument("--classification-json", required=True, help="Path to AI classification JSON")
    args = parser.parse_args()

    evidence = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    classification = json.loads(Path(args.classification_json).read_text(encoding="utf-8"))
    errors = validate_classification(evidence, classification)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
