#!/usr/bin/env python3
"""Validate Support.html completeness for AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text

TAG_PATTERN = re.compile(r"<[^>]+>")
PLACEHOLDER_PATTERNS = ["draft", "lorem", "placeholder", "tbd", "todo", "pending confirmation", "coming soon"]


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


def validate_support_output(inspect_payload: dict, support_text: str) -> list[str]:
    errors: list[str] = []
    support_email = str(inspect_payload.get("support_email") or "").strip().lower()
    if support_email and inspect_payload.get("support_email_source") == "explicit" and support_email not in support_text:
        errors.append("Support page is missing the inspected support email.")

    faq_markers = ["faq", "question", "help", "support"]
    if not any(marker in support_text for marker in faq_markers):
        errors.append("Support page should include FAQ or help-oriented content.")

    if sum(support_text.count(token) for token in ["?", "how ", "can i", "what if"]) < 2:
        errors.append("Support page should include at least a few concrete FAQ-style entries.")

    preview_profile = face_data_review_profile(inspect_payload)
    if preview_profile:
        if face_data_workflow_kind(inspect_payload) == "translation_face_visibility":
            if not contains_any(support_text, ["image translation", "translated result", "translation work"]):
                errors.append("Support page must include an AI-assisted image translation FAQ entry when face-data translation signals are active.")
            if not contains_any(
                support_text,
                [
                    "camera, photo-library, microphone, or speech-recognition",
                    "camera, photo-library, or microphone",
                    "recording spoken notes",
                    "importing an image for translation",
                ],
            ):
                errors.append("Support page must explain why media or speech permissions are requested for AI-assisted translation.")
        else:
            if "ai preview" not in support_text:
                errors.append("Support page must include an AI Preview FAQ entry when face-data preview signals are active.")
            if not contains_any(
                support_text,
                [
                    "camera, photo-library, or add-to-library",
                    "camera or photo-library",
                    "save a generated preview",
                    "save the finished image to photos",
                ],
            ):
                errors.append("Support page must explain why media permissions are requested for AI Preview.")

    for placeholder in PLACEHOLDER_PATTERNS:
        if placeholder in support_text:
            errors.append(f"Support page contains placeholder text: {placeholder}.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Support.html completeness.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--support-html", required=True, help="Path to Support.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    support_text = html_to_text(Path(args.support_html).read_text(encoding="utf-8"))
    errors = validate_support_output(inspect_payload, support_text)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
