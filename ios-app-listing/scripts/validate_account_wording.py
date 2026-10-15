#!/usr/bin/env python3
"""Validate account/login wording against inspected access evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from html_text import visible_text

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_common import inspect_access_mode

TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

BLOCKED_PATTERNS = [
    ("user accounts", re.compile(r"\buser accounts?\b", re.IGNORECASE)),
    ("account", re.compile(r"\baccounts?\b", re.IGNORECASE)),
    ("register", re.compile(r"\bregister\b", re.IGNORECASE)),
    ("log in", re.compile(r"\blog[ -]?in\b", re.IGNORECASE)),
    ("sign in", re.compile(r"\bsign[ -]?in\b", re.IGNORECASE)),
    ("credentials", re.compile(r"\bcredentials?\b", re.IGNORECASE)),
    ("username", re.compile(r"\busername\b", re.IGNORECASE)),
    ("password", re.compile(r"\bpassword\b", re.IGNORECASE)),
]


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html)


def load_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".html":
        return html_to_text(raw)
    return raw


def collect_site_texts(site_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ["index.html", "Support.html", "PrivacyPolicy.html", "Terms&Conditions.html"]:
        path = site_dir / name
        if path.exists():
            result[name] = load_text(path)
    return result


def compact_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def extract_excerpt(text: str, start: int, end: int) -> str:
    compact = compact_text(text)
    excerpt_start = max(0, start - 40)
    excerpt_end = min(len(compact), end + 60)
    return compact[excerpt_start:excerpt_end]


def validate_account_wording(
    inspect_payload: dict,
    intro_text: str,
    site_texts: dict[str, str],
) -> list[dict[str, str]]:
    if inspect_access_mode(inspect_payload) == "credential_account":
        return []

    errors: list[dict[str, str]] = []
    for file_name, content in {"Intro.md": intro_text, **site_texts}.items():
        compact = compact_text(content)
        for phrase, pattern in BLOCKED_PATTERNS:
            for match in pattern.finditer(compact):
                errors.append(
                    {
                        "file": file_name,
                        "phrase": phrase,
                        "excerpt": extract_excerpt(compact, match.start(), match.end()),
                        "hint": "Rewrite the user-visible text to use neutral profile, community, service, or saved-state wording unless inspect evidence supports credential-based sign-in.",
                    }
                )
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in errors:
        key = (item["file"], item["phrase"], item["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate account/login wording against inspected access evidence.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect JSON")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    parser.add_argument("--site-dir", required=True, help="Path to AppListing/site")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    intro_text = load_text(Path(args.intro_md))
    site_texts = collect_site_texts(Path(args.site_dir))
    errors = validate_account_wording(inspect_payload, intro_text, site_texts)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
