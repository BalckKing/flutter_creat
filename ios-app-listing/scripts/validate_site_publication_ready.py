#!/usr/bin/env python3
"""Reject draft-state and placeholder copy in generated AppListing pages."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


REQUIRED_PAGES = (
    "index.html",
    "PrivacyPolicy.html",
    "Terms&Conditions.html",
    "Support.html",
)
STANDALONE_STATUS_LABELS = {"draft", "wip", "tbd", "todo", "placeholder", "pending confirmation", "coming soon", "under construction", "for review only"}

STATUS_PATTERNS = (
    ("draft status", re.compile(r"\b(?:working\s+draft|draft\s+(?:copy|version|policy|terms|page|status|state))\b", re.IGNORECASE)),
    ("placeholder", re.compile(r"\bplaceholder\b", re.IGNORECASE)),
    ("lorem ipsum", re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE)),
    ("TBD", re.compile(r"\btbd\b", re.IGNORECASE)),
    ("TODO", re.compile(r"\btodo\b", re.IGNORECASE)),
    ("pending confirmation", re.compile(r"\bpending\s+confirmation\b", re.IGNORECASE)),
    ("pending review", re.compile(r"\bpending\s+review\b", re.IGNORECASE)),
    ("pending details", re.compile(r"\bpending\s+(?:details|information|completion)\b", re.IGNORECASE)),
    ("under construction", re.compile(r"\bunder\s+construction\b", re.IGNORECASE)),
    ("work in progress", re.compile(r"\bwork\s+in\s+progress\b", re.IGNORECASE)),
    ("review-only status", re.compile(r"\b(?:for\s+review\s+only|under\s+review|not\s+final|preliminary\s+version)\b", re.IGNORECASE)),
    ("coming soon", re.compile(r"\bcoming\s+soon\b", re.IGNORECASE)),
    (
        "unfinished authoring instruction",
        re.compile(r"\bto\s+be\s+(?:filled|completed|confirmed|provided|determined)\b", re.IGNORECASE),
    ),
    (
        "bracketed authoring field",
        re.compile(r"\[[^\]\r\n]{1,60}\]"),
    ),
    (
        "authoring instruction",
        re.compile(r"\b(?:insert|replace|add)\s+(?:your\s+)?(?:name|email|company|jurisdiction|date|url|domain)\b", re.IGNORECASE),
    ),
)


class PageCopyParser(HTMLParser):
    """Collect rendered copy plus metadata and accessible labels users can encounter."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.suppressed_depth = 0
        self.heading_depth = 0
        self.body_parts: list[str] = []
        self.body_text_nodes: list[str] = []
        self.title_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.metadata_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        if tag == "head":
            self.in_head = True
        if tag == "title":
            self.in_title = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_depth += 1
        if tag in {"script", "style"}:
            self.suppressed_depth += 1

        for name in ("aria-label", "alt", "title", "placeholder", "value"):
            value = values.get(name, "").strip()
            if value:
                self.metadata_parts.append(value)
        if tag == "meta":
            key = (values.get("name") or values.get("property") or "").lower()
            if key in {"description", "og:title", "og:description", "twitter:title", "twitter:description"}:
                value = values.get("content", "").strip()
                if value:
                    self.metadata_parts.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.heading_depth:
            self.heading_depth -= 1
        if tag == "head":
            self.in_head = False
        if tag in {"script", "style"} and self.suppressed_depth:
            self.suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.suppressed_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self.in_title:
            self.title_parts.append(text)
        elif not self.in_head:
            self.body_parts.append(text)
            self.body_text_nodes.append(text)
        if self.heading_depth:
            self.heading_parts.append(text)

    def normalized_copy(self) -> str:
        return " ".join((*self.body_parts, *self.title_parts, *self.metadata_parts)).casefold()


def extract_page_copy(raw_html: str) -> str:
    parser = PageCopyParser()
    parser.feed(raw_html)
    return parser.normalized_copy()


def validate_page_html(page_name: str, raw_html: str) -> list[str]:
    parser = PageCopyParser()
    parser.feed(raw_html)
    text = parser.normalized_copy()
    errors: list[str] = []
    if not text.strip():
        errors.append(f"{page_name} has no readable page copy.")
        return errors
    if len(" ".join(parser.body_parts)) < 80:
        errors.append(f"{page_name} does not contain enough substantive page copy.")

    metadata_text = " ".join((*parser.title_parts, *parser.metadata_parts))
    if re.search(r"\bdraft\b", metadata_text, re.IGNORECASE):
        errors.append(f"{page_name} exposes a draft marker in its title, description, or accessible labels.")
    standalone_labels = {item.casefold() for item in parser.body_text_nodes}
    if "draft" in standalone_labels:
        errors.append(f"{page_name} exposes a standalone draft marker in the page body.")
    other_status_labels = sorted(standalone_labels & (STANDALONE_STATUS_LABELS - {"draft"}))
    if other_status_labels:
        errors.append(f"{page_name} exposes an unfinished page-state label: {', '.join(other_status_labels)}.")
    heading_text = " ".join(parser.heading_parts).strip()
    if re.match(r"draft\b", heading_text, re.IGNORECASE):
        errors.append(f"{page_name} exposes a draft marker in a page heading.")

    for label, pattern in STATUS_PATTERNS:
        if pattern.search(text):
            errors.append(f"{page_name} contains unfinished {label} content.")
    return errors


def validate_site_dir(site_dir: Path) -> list[str]:
    errors: list[str] = []
    for page_name in REQUIRED_PAGES:
        page_path = site_dir / page_name
        if not page_path.is_file():
            errors.append(f"Missing required site page: {page_name}.")
            continue
        try:
            raw_html = page_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"Cannot read {page_name}: {error}.")
            continue
        errors.extend(validate_page_html(page_name, raw_html))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate publication-ready copy in all four AppListing pages.")
    parser.add_argument("--site-dir", required=True, help="Path to AppListing/site")
    args = parser.parse_args()

    errors = validate_site_dir(Path(args.site_dir))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
