#!/usr/bin/env python3
"""Validate IAP-related legal and intro coverage for AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text
from legal_facts import build_product_facts

TAG_PATTERN = re.compile(r"<[^>]+>")

TERMS_IAP_GROUPS = {
    "iap_or_apple": ["in-app purchase", "apple", "app store"],
    "virtual_goods": ["credits", "coins", "virtual", "consumable"],
    "refund_or_limits": ["refund", "final sale", "non-refundable", "restore"],
}

PRIVACY_IAP_GROUPS = {
    "payments": ["purchase", "billing", "payment", "credits", "coins"],
}

INTRO_IAP_HINTS = ["purchase", "credits", "coins", "subscription", "virtual"]


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase.lower() in text for phrase in phrases)


def validate_iap_legal(inspect_payload: dict, intro_text: str, privacy_text: str, terms_text: str) -> tuple[list[str], list[str]]:
    privacy_signals = inspect_payload.get("privacy_signals", {})
    has_iap = bool(privacy_signals.get("payments")) or bool(inspect_payload.get("iap_codes"))
    if not has_iap:
        return [], []

    errors: list[str] = []
    warnings: list[str] = []

    facts = build_product_facts(inspect_payload)["facts"]
    groups = {key: value for key, value in TERMS_IAP_GROUPS.items() if key != "virtual_goods"}
    if facts["virtual_goods"] is True:
        groups["virtual_goods"] = TERMS_IAP_GROUPS["virtual_goods"]
    for field, phrases in (("subscription", ["subscription", "renewal", "cancellation"]), ("consumable_iap", ["consumable"]), ("non_consumable_iap", ["non-consumable", "unlock"])):
        if facts[field] is True:
            groups[field] = phrases
    for group_name, phrases in groups.items():
        if not contains_any(terms_text, phrases):
            errors.append(f"Terms are missing IAP coverage for: {group_name}.")

    for group_name, phrases in PRIVACY_IAP_GROUPS.items():
        if not contains_any(privacy_text, phrases):
            errors.append(f"Privacy policy is missing IAP coverage for: {group_name}.")

    if not contains_any(intro_text.lower(), INTRO_IAP_HINTS):
        errors.append("Intro description should mention purchase or virtual goods context when IAP is detected.")

    if facts["virtual_goods"] is True and not contains_any(terms_text, ["not redeemable for cash", "not redeemable", "no cash value"]):
        warnings.append("Terms could be strengthened with non-cash-value language for virtual goods.")
    if facts["iap_type"] == "unknown":
        warnings.append("IAP product type is unknown; confirm the type instead of assuming virtual goods.")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate IAP legal coverage in AppListing outputs.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    parser.add_argument("--privacy-html", required=True, help="Path to PrivacyPolicy.html")
    parser.add_argument("--terms-html", required=True, help="Path to Terms&Conditions.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    intro_text = Path(args.intro_md).read_text(encoding="utf-8")
    privacy_text = html_to_text(Path(args.privacy_html).read_text(encoding="utf-8"))
    terms_text = html_to_text(Path(args.terms_html).read_text(encoding="utf-8"))
    errors, warnings = validate_iap_legal(inspect_payload, intro_text, privacy_text, terms_text)
    print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
