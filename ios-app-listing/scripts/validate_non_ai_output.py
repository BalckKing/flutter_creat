#!/usr/bin/env python3
"""Reject AI-related wording for non-AI AppListing outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text

TAG_PATTERN = re.compile(r"<[^>]+>")
NON_AI_COPY_PATTERNS = (
    ("AI Preview", re.compile(r"\bai preview\b", re.IGNORECASE)),
    ("AI-assisted", re.compile(r"\bai-assisted\b", re.IGNORECASE)),
    ("artificial intelligence", re.compile(r"\bartificial intelligence\b", re.IGNORECASE)),
    ("AI", re.compile(r"\bai\b", re.IGNORECASE)),
    ("assistant", re.compile(r"\bassistant\b", re.IGNORECASE)),
    ("inference", re.compile(r"\binference\b", re.IGNORECASE)),
)
SITE_FILES = (
    "index.html",
    "PrivacyPolicy.html",
    "Terms&Conditions.html",
    "Support.html",
)


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html)


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


def remove_app_name_mentions(text: str, app_name: str) -> str:
    if not app_name:
        return text
    return re.sub(re.escape(app_name), " ", text, flags=re.IGNORECASE)


def validate_non_ai_output(
    inspect_payload: dict,
    intro_markdown: str,
    site_pages: dict[str, str],
) -> list[str]:
    if ai_disclosure_required(inspect_payload):
        return []

    app_name = str(inspect_payload.get("app_name", "")).strip()
    text_blobs = {"Intro.md": intro_markdown, **site_pages}
    errors: list[str] = []
    for label, raw_text in text_blobs.items():
        cleaned = remove_app_name_mentions(raw_text or "", app_name)
        for marker, pattern in NON_AI_COPY_PATTERNS:
            if pattern.search(cleaned):
                errors.append(
                    f"{label} contains AI-related wording when ai_signals.disclosure_required is false: {marker}."
                )
                break
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate that non-AI apps do not emit AI wording.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    parser.add_argument("--site-dir", required=True, help="Path to AppListing/site")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    intro_markdown = Path(args.intro_md).read_text(encoding="utf-8")
    site_dir = Path(args.site_dir)
    site_pages = {
        name: html_to_text((site_dir / name).read_text(encoding="utf-8"))
        for name in SITE_FILES
        if (site_dir / name).exists()
    }
    errors = validate_non_ai_output(inspect_payload, intro_markdown, site_pages)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
