#!/usr/bin/env python3
"""Validate AppListing claims against claimable features and evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text

TAG_PATTERN = re.compile(r"<[^>]+>")


def intro_to_text(raw_markdown: str) -> str:
    lines: list[str] = []
    for raw_line in raw_markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return " ".join(lines).lower()


CLAIM_RULES = {
    "ai": {"required": {"ai_chat", "ai_image_generation", "beauty_editing"}, "phrases": ["ai", "assistant", "preview"]},
    "chat": {"required": {"messaging"}, "phrases": ["chat", "message", "inbox"]},
    "community": {"required": {"feed", "post_creation", "profile"}, "phrases": ["community", "publish", "post", "feed"]},
    "purchase": {"required": {"recharge"}, "phrases": ["purchase", "credits", "coins", "recharge"]},
}


def contains_phrase(text: str, phrase: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(phrase.lower())}\b")
    return bool(pattern.search(text))


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def validate_listing_claims(classification_payload: dict, intro_text: str, index_text: str) -> list[str]:
    claimable_features = set(classification_payload.get("claimable_features", [])) | set(classification_payload.get("capabilities", []))
    combined = f"{intro_to_text(intro_text)}\n{index_text.lower()}"
    errors: list[str] = []

    for rule_name, rule in CLAIM_RULES.items():
        if any(contains_phrase(combined, phrase) for phrase in rule["phrases"]) and not (claimable_features & rule["required"]):
            errors.append(f"Listing contains unsupported claim language for: {rule_name}.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AppListing claims against classification output.")
    parser.add_argument("--classification-json", required=True, help="Path to validated classification JSON")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    parser.add_argument("--index-html", required=True, help="Path to index.html")
    args = parser.parse_args()

    classification_payload = json.loads(Path(args.classification_json).read_text(encoding="utf-8"))
    intro_text = Path(args.intro_md).read_text(encoding="utf-8")
    index_text = html_to_text(Path(args.index_html).read_text(encoding="utf-8"))
    errors = validate_listing_claims(classification_payload, intro_text, index_text)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
