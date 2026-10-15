#!/usr/bin/env python3
"""Validate review-harmful wording in AppListing user-visible content."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text

TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

BANNED_RULES = [
    {"id": "mock_data", "phrase": "mock data", "mode": "phrase"},
    {"id": "local_data", "phrase": "local data", "mode": "phrase"},
    {"id": "local_storage", "phrase": "local storage", "mode": "phrase"},
    {"id": "device_storage", "phrase": "device storage", "mode": "phrase"},
    {"id": "offline_only", "phrase": "offline only", "mode": "phrase"},
    {"id": "mock", "phrase": "mock", "mode": "word"},
    {"id": "offline", "phrase": "offline", "mode": "word"},
    {"id": "local_impl", "phrase": "local", "mode": "contextual"},
]

EXCEPTION_PHRASES = {
    "local laws",
    "local regulations",
    "local community",
    "locale",
}

LOCAL_CONTEXT_HINTS = {
    "data",
    "storage",
    "stored",
    "device",
    "devices",
    "database",
    "cache",
    "cached",
    "sync",
    "synchronization",
    "filesystem",
    "file system",
}


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html)


def normalize_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip().lower()


def load_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".html":
        return html_to_text(raw)
    return raw


def has_exception(normalized_text: str, start: int, end: int) -> bool:
    window_start = max(0, start - 20)
    window_end = min(len(normalized_text), end + 30)
    window = normalized_text[window_start:window_end]
    return any(phrase in window for phrase in EXCEPTION_PHRASES)


def contextual_local_match(normalized_text: str, match: re.Match[str]) -> bool:
    if has_exception(normalized_text, match.start(), match.end()):
        return False
    window_start = max(0, match.start() - 40)
    window_end = min(len(normalized_text), match.end() + 40)
    window = normalized_text[window_start:window_end]
    return any(hint in window for hint in LOCAL_CONTEXT_HINTS)


def find_banned_matches(text: str) -> list[dict[str, str]]:
    normalized_text = normalize_text(text)
    errors: list[dict[str, str]] = []

    for rule in BANNED_RULES:
        phrase = rule["phrase"]
        if rule["mode"] == "phrase":
            for match in re.finditer(re.escape(phrase), normalized_text):
                if has_exception(normalized_text, match.start(), match.end()):
                    continue
                errors.append({"phrase": phrase, "excerpt": extract_excerpt(text, match.start(), match.end())})
        elif rule["mode"] == "word":
            pattern = re.compile(rf"\b{re.escape(phrase)}\b")
            for match in pattern.finditer(normalized_text):
                if has_exception(normalized_text, match.start(), match.end()):
                    continue
                errors.append({"phrase": phrase, "excerpt": extract_excerpt(text, match.start(), match.end())})
        else:
            pattern = re.compile(r"\blocal\b")
            for match in pattern.finditer(normalized_text):
                if not contextual_local_match(normalized_text, match):
                    continue
                errors.append({"phrase": phrase, "excerpt": extract_excerpt(text, match.start(), match.end())})

    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in errors:
        key = (item["phrase"], item["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def extract_excerpt(original_text: str, start: int, end: int) -> str:
    compact = WHITESPACE_RE.sub(" ", original_text).strip()
    excerpt_start = max(0, start - 30)
    excerpt_end = min(len(compact), end + 50)
    return compact[excerpt_start:excerpt_end]


def validate_review_wording(intro_text: str, site_texts: dict[str, str]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for file_name, content in {"Intro.md": intro_text, **site_texts}.items():
        for match in find_banned_matches(content):
            errors.append(
                {
                    "file": file_name,
                    "phrase": match["phrase"],
                    "excerpt": match["excerpt"],
                    "hint": "Rewrite the user-visible text to avoid exposing mock, offline, or local-implementation details.",
                }
            )
    return errors


def collect_site_texts(site_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ["index.html", "Support.html", "PrivacyPolicy.html", "Terms&Conditions.html"]:
        path = site_dir / name
        if path.exists():
            result[name] = load_text(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate review-harmful wording in AppListing output.")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    parser.add_argument("--site-dir", required=True, help="Path to AppListing/site")
    args = parser.parse_args()

    intro_text = load_text(Path(args.intro_md))
    site_texts = collect_site_texts(Path(args.site_dir))
    errors = validate_review_wording(intro_text, site_texts)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
