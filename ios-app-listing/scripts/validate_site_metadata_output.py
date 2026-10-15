#!/usr/bin/env python3
"""Validate that site HTML does not expose internal listing metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SITE_PAGE_NAMES = ["index.html", "Support.html", "PrivacyPolicy.html", "Terms&Conditions.html"]
WHITESPACE_RE = re.compile(r"\s+")
INLINE_FIELD_PATTERN = re.compile(r"\b(?:UGC|Chat|Category|IAP\s*Codes?)\s*:\s*[^\n\r<]+", re.IGNORECASE)
SIMPLE_TAG_TEXT_PATTERN = re.compile(
    r"<(?P<tag>h1|h2|h3|p|span|li|strong|em|div)\b[^>]*>\s*(?P<text>[^<>]{1,120})\s*</(?P=tag)>",
    re.IGNORECASE,
)
FIELD_LABELS = {
    "category",
    "ugc",
    "chat",
    "iap code",
    "iap codes",
}
CATEGORY_VALUES = {
    "social networking",
    "travel",
    "photo & video",
    "finance",
    "utilities",
    "社交 (social networking)",
    "旅游 (travel)",
    "摄影与录像 (photo & video)",
    "财务 (finance)",
    "工具 (utilities)",
}
IAP_CODE_TOKEN = r"[A-Za-z][A-Za-z_]*\d+(?:0[1-9]|1[0-2])"
IAP_CODE_DISPLAY_PATTERN = re.compile(
    rf"^(?:{IAP_CODE_TOKEN}(?:\s*-\s*{IAP_CODE_TOKEN})?)(?:\s*,\s*{IAP_CODE_TOKEN}(?:\s*-\s*{IAP_CODE_TOKEN})?)*$"
)


def normalize_visible_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def collect_site_htmls(site_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in SITE_PAGE_NAMES:
        path = site_dir / name
        if path.exists():
            result[name] = path.read_text(encoding="utf-8")
    return result


def validate_site_metadata_output(site_htmls: dict[str, str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for file_name, raw_html in site_htmls.items():
        for match in INLINE_FIELD_PATTERN.finditer(raw_html):
            snippet = normalize_visible_text(match.group(0))
            error = f"{file_name} exposes internal listing metadata in visible HTML: {snippet}."
            if error not in seen:
                seen.add(error)
                errors.append(error)

        for match in SIMPLE_TAG_TEXT_PATTERN.finditer(raw_html):
            visible_text = normalize_visible_text(match.group("text"))
            if not visible_text:
                continue
            lowered = visible_text.casefold()

            if lowered in FIELD_LABELS:
                error = f"{file_name} exposes internal listing metadata label in visible HTML: {visible_text}."
            elif lowered in CATEGORY_VALUES:
                error = f"{file_name} exposes App Store category metadata in visible HTML: {visible_text}."
            elif IAP_CODE_DISPLAY_PATTERN.fullmatch(visible_text):
                error = f"{file_name} exposes IAP code inventory in visible HTML: {visible_text}."
            else:
                continue

            if error not in seen:
                seen.add(error)
                errors.append(error)

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate that site HTML does not expose internal listing metadata.")
    parser.add_argument("--site-dir", required=True, help="Path to AppListing/site")
    args = parser.parse_args()

    site_htmls = collect_site_htmls(Path(args.site_dir))
    errors = validate_site_metadata_output(site_htmls)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
