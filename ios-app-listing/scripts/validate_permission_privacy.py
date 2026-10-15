#!/usr/bin/env python3
"""Validate permission-driven privacy disclosures for AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text
from legal_facts import build_product_facts

TAG_PATTERN = re.compile(r"<[^>]+>")

RULES = {
    "camera": ["camera", "photo", "capture", "image"],
    "photo_library": ["photo", "library", "images", "upload"],
    "microphone": ["microphone", "audio", "voice", "record"],
    "tracking": ["tracking", "analytics", "advertising", "advertisers"],
    "location": ["location", "nearby", "places", "map"],
}


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase.lower() in text for phrase in phrases)


def ai_disclosure_required(inspect_payload: dict) -> bool:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return False
    if "disclosure_required" in ai_signals:
        return bool(ai_signals.get("disclosure_required"))
    if "claimable" in ai_signals:
        return bool(ai_signals.get("claimable"))
    if not ai_signals.get("active"):
        return False
    return bool(ai_signals.get("user_reachable", True))


def translation_disclosure_required(inspect_payload: dict) -> bool:
    translation_signals = inspect_payload.get("translation_signals", {})
    if not isinstance(translation_signals, dict) or not translation_signals:
        return False
    if not translation_signals.get("active"):
        return False
    return bool(translation_signals.get("disclosure_required", translation_signals.get("user_reachable", True)))


def face_data_review_profile(inspect_payload: dict) -> dict:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return {}
    profile = ai_signals.get("review_profile", {})
    if not isinstance(profile, dict) or not profile.get("needs_face_data_clauses"):
        return {}
    if not (ai_disclosure_required(inspect_payload) or translation_disclosure_required(inspect_payload)):
        return {}
    return profile


def face_data_workflow_kind(inspect_payload: dict) -> str:
    profile = face_data_review_profile(inspect_payload)
    if not isinstance(profile, dict):
        return "preview"
    return str(profile.get("workflow_kind", "preview")).strip() or "preview"


def validate_permission_privacy(inspect_payload: dict, privacy_text: str) -> list[str]:
    privacy_signals = inspect_payload.get("privacy_signals", {})
    if not isinstance(privacy_signals, dict):
        return []

    errors: list[str] = []
    facts = build_product_facts(inspect_payload)["facts"]
    for signal_name, phrases in RULES.items():
        if signal_name == "tracking":
            if facts["tracking"] == "unknown":
                errors.append("tracking behavior is unknown; verify ATT use rather than accepting analytics keywords.")
            elif facts["tracking"] is True and not contains_any(privacy_text, ["app tracking transparency", "tracking permission"]):
                errors.append("Privacy policy is missing ATT authorization disclosure for actual tracking.")
            continue
        if privacy_signals.get(signal_name) and not contains_any(privacy_text, phrases):
            errors.append(f"Privacy policy is missing disclosure for permission signal: {signal_name}.")

    preview_profile = face_data_review_profile(inspect_payload)
    if preview_profile:
        legal = inspect_payload.get("legal", {})
        ai_legal = legal.get("ai", {}) if isinstance(legal, dict) and legal.get("confirmed") is True else {}
        if not ai_legal.get("send_condition"):
            errors.append("AI image workflow send condition must be confirmed before publication.")
        workflow_kind = face_data_workflow_kind(inspect_payload)
        if workflow_kind == "translation_face_visibility":
            if not contains_any(privacy_text, ["image translation", "selected image", "selected photo", "user photo"]):
                errors.append("Privacy policy must tie camera or photo access to the image-translation selected-image flow.")
            if ai_legal.get("send_condition") and not contains_any(privacy_text, ["consent prompt", "after you choose", "before", "only when you choose", "only when you request"]):
                errors.append("Privacy policy must match the confirmed image-translation send condition.")
        else:
            if not contains_any(privacy_text, ["ai preview", "selected photo", "user photo"]):
                errors.append("Privacy policy must tie camera or photo access to the AI Preview selected-photo flow.")
            if ai_legal.get("send_condition") and not contains_any(privacy_text, ["consent prompt", "after you choose", "before", "only when you choose", "only when you request"]):
                errors.append("Privacy policy must match the confirmed AI Preview send condition.")
        if facts["photo_export"] is True and not contains_any(
            privacy_text,
            ["save the result to photos", "save a copy to photos", "add-to-library", "save a generated preview"],
        ):
            errors.append("Privacy policy must explain why add-to-library access is requested for AI Preview output saving.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate permission-driven privacy disclosures.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--privacy-html", required=True, help="Path to PrivacyPolicy.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    privacy_text = html_to_text(Path(args.privacy_html).read_text(encoding="utf-8"))
    errors = validate_permission_privacy(inspect_payload, privacy_text)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
