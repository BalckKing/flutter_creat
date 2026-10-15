#!/usr/bin/env python3
"""Validate AI-related terms coverage for AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text

TAG_PATTERN = re.compile(r"<[^>]+>")

REQUIRED_GROUPS = {
    "ai_reference": ["ai", "artificial intelligence", "model", "assistant"],
    "output_limits": ["output", "results", "may vary", "not guaranteed", "limitations"],
    "user_responsibility": ["responsible", "review", "your responsibility"],
    "processing_recipient": ["provider", "processing service", "privacy policy"],
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


def face_data_workflow_kind(inspect_payload: dict) -> str:
    profile = inspect_payload.get("ai_signals", {}).get("review_profile", {})
    if not isinstance(profile, dict):
        return "preview"
    return str(profile.get("workflow_kind", "preview")).strip() or "preview"


def validate_terms_ai(inspect_payload: dict, terms_text: str) -> list[str]:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict) or not ai_disclosure_required(inspect_payload):
        return []

    errors: list[str] = []
    for group_name, phrases in REQUIRED_GROUPS.items():
        if not contains_any(terms_text, phrases):
            errors.append(f"Terms are missing AI coverage for: {group_name}.")

    preview_profile = ai_signals.get("review_profile", {})
    if isinstance(preview_profile, dict) and preview_profile.get("needs_face_data_clauses"):
        if face_data_workflow_kind(inspect_payload) == "translation_face_visibility":
            preview_groups = {
                "translation_reference": ["ai-assisted translation", "image translation", "selected image", "selected photo"],
                "allowed_use": ["consumer translation", "informational content", "care labels", "captions"],
                "prohibited_identity_use": ["identity verification", "face recognition", "biometric"],
                "high_risk_limits": ["legal", "medical", "safety-critical", "safety critical"],
            }
        else:
            preview_groups = {
                "preview_reference": ["ai preview", "preview", "selected photo"],
                "allowed_use": ["visual styling preview", "style preview", "consumer entertainment"],
                "prohibited_identity_use": ["identity verification", "face recognition", "biometric"],
                "high_risk_limits": ["legal", "medical", "safety-critical", "safety critical"],
            }
        for group_name, phrases in preview_groups.items():
            if not contains_any(terms_text, phrases):
                errors.append(f"Terms are missing face-data AI coverage for: {group_name}.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AI terms coverage.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--terms-html", required=True, help="Path to Terms&Conditions.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    terms_text = html_to_text(Path(args.terms_html).read_text(encoding="utf-8"))
    errors = validate_terms_ai(inspect_payload, terms_text)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
