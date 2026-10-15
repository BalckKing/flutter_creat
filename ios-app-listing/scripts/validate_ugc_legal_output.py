#!/usr/bin/env python3
"""Validate UGC-related legal coverage for AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text
from legal_facts import build_product_facts

TAG_PATTERN = re.compile(r"<[^>]+>")

PRIVACY_REQUIRED_GROUPS = {
    "community_or_user_content": ["community", "user content", "content", "post", "message", "messages"],
    "collection_or_processing": ["collect", "process", "store", "display", "share", "moderate"],
}

TERMS_REQUIRED_GROUPS = {
    "community_or_user_content": ["community", "user content", "content", "post", "message", "messages"],
    "responsibility": ["responsible", "responsibility", "accountable"],
    "reporting": ["report", "reporting", "flag"],
    "blocking_or_restriction": ["block", "blocking", "block other members", "block abusive users"],
    "prohibited_conduct": ["harass", "abuse", "illegal", "harmful", "prohibited"],
    "enforcement": ["review", "moderate", "remove", "suspend", "terminate"],
    "contact": ["contact", "support@", "email"],
}

OPTIONAL_STRENGTH_GROUPS = {
    "timely_review": ["24 hour", "24-hour", "promptly", "timely"],
    "eula_or_acceptance": ["acceptance of terms", "accept these terms", "agree to these terms", "eula"],
}

DISALLOWED_BLOCKING_TERMS = ["mute", "hide"]


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def requires_ugc_legal(inspect_payload: dict) -> bool:
    privacy_signals = inspect_payload.get("privacy_signals", {})
    if isinstance(privacy_signals, dict) and isinstance(privacy_signals.get("community_ugc"), bool):
        return privacy_signals["community_ugc"]
    capability_candidates = inspect_payload.get("capability_candidates", {})
    if not isinstance(capability_candidates, dict):
        return bool(isinstance(privacy_signals, dict) and privacy_signals.get("user_content"))
    for name in ("feed", "post_creation"):
        payload = capability_candidates.get(name, {})
        if isinstance(payload, dict) and float(payload.get("score", 0.0)) >= 1.0:
            return True
    if any(name in capability_candidates for name in ("feed", "post_creation", "messaging")):
        return False
    return bool(isinstance(privacy_signals, dict) and privacy_signals.get("user_content"))


def validate_ugc_legal(inspect_payload: dict, privacy_text: str, terms_text: str) -> tuple[list[str], list[str]]:
    if not requires_ugc_legal(inspect_payload):
        return [], []

    errors: list[str] = []
    warnings: list[str] = []

    for group_name, phrases in PRIVACY_REQUIRED_GROUPS.items():
        if not contains_any(privacy_text, phrases):
            errors.append(f"Privacy policy is missing UGC coverage for: {group_name}.")

    for group_name, phrases in TERMS_REQUIRED_GROUPS.items():
        if not contains_any(terms_text, phrases):
            errors.append(f"Terms are missing UGC coverage for: {group_name}.")

    for disallowed in DISALLOWED_BLOCKING_TERMS:
        if contains_any(privacy_text, [disallowed]) or contains_any(terms_text, [disallowed]):
            errors.append(f"Use explicit block wording for abusive-user controls; do not use '{disallowed}'.")

    facts = build_product_facts(inspect_payload)["facts"]
    for group_name, phrases in OPTIONAL_STRENGTH_GROUPS.items():
        if not contains_any(terms_text, phrases):
            warnings.append(f"Terms could be strengthened with UGC language for: {group_name}.")
    age = facts["minimum_age"]
    if isinstance(age, int) and f"{age} or older" not in terms_text:
        errors.append("Terms must reflect the confirmed community age policy.")

    if not (
        contains_any(privacy_text, ["eula", "terms of use", "accept the app's eula", "accept the app's terms", "accept the terms"])
        or contains_any(terms_text, ["eula", "terms of use", "acceptance of terms", "accept these terms", "agree to these terms"])
    ):
        warnings.append("Privacy or Terms could be strengthened with UGC language for: community_terms_acceptance.")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate UGC legal coverage in Privacy and Terms outputs.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--privacy-html", required=True, help="Path to PrivacyPolicy.html")
    parser.add_argument("--terms-html", required=True, help="Path to Terms&Conditions.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    privacy_text = html_to_text(Path(args.privacy_html).read_text(encoding="utf-8"))
    terms_text = html_to_text(Path(args.terms_html).read_text(encoding="utf-8"))
    errors, warnings = validate_ugc_legal(inspect_payload, privacy_text, terms_text)
    print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
