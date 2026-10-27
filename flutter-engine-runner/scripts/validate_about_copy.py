#!/usr/bin/env python3
"""Check the four final site pages for unfinished publication copy, read-only."""

import argparse
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


PAGES = ("index.html", "PrivacyPolicy.html", "Terms&Conditions.html", "Support.html")
BLOCKS = frozenset((
    "address", "article", "aside", "blockquote", "br", "button", "div", "dl", "dt", "dd",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
    "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "td", "th", "title", "tr", "ul",
))
RULES = (
    ("draft or placeholder copy", re.compile(
        r"\b(?:drafts?|wip|tbd|todo|placeholder|unfinished|pending confirmation|work in progress)\b"
    )),
    ("development distribution notice", re.compile(
        r"\b(?:development|developer|test|preview)\s+(?:distribution|edition|build|version)\b"
        r"|\bpre[\s-]?release\b"
    )),
    ("unconfigured publication details", re.compile(
        r"\b(?:has|have) not (?:yet )?been configured\b"
        r"|\b(?:operator identity|developer identity|contact channel|contact address|public policy address)"
        r"\s+(?:(?:is|are)\s+)?(?:not (?:yet )?(?:configured|verified|provided|available)|missing|pending)\b"
        r"|\b(?:must|needs? to) be (?:completed|configured|verified) before (?:public )?release\b"
        r"|\bno contact address or public availability is implied\b"
        r"|\bnot provided[\s,;:-]+pending(?: confirmation)?\b"
    )),
    ("unfinished publication status", re.compile(
        r"草稿|开发(?:版本?|分发)|待(?:配置|补充|完善|确认)|未(?:完成|配置)"
    )),
)


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    value = "".join(c for c in value if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", " ", value).strip()


class PageCopy(HTMLParser):
    """Read copy even when CSS hides it; ignore code, comments and identifiers."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.exposed = []
        self.code_tag = None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.code_tag = tag
            return
        if self.code_tag:
            return
        if tag in BLOCKS:
            self.parts.append(" ")
        attrs = dict(attrs)
        for key in ("alt", "title", "aria-label", "aria-description", "aria-valuetext", "placeholder"):
            if attrs.get(key):
                self.exposed.append(attrs[key])
        if tag == "meta" and attrs.get("content"):
            self.exposed.append(attrs["content"])
        if tag in ("input", "button") and attrs.get("value"):
            self.exposed.append(attrs["value"])

    def handle_endtag(self, tag):
        if tag == self.code_tag:
            self.code_tag = None
        if not self.code_tag and tag in BLOCKS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.code_tag:
            self.parts.append(data)


def inspect_page(path):
    try:
        source = path.read_text(encoding="utf-8-sig")
        parser = PageCopy()
        parser.feed(source)
        parser.close()
    except (OSError, UnicodeError) as error:
        return [f"cannot read page: {error}"]
    copy = normalize("".join(parser.parts) + " " + " ".join(parser.exposed))
    if not copy:
        return ["page has no readable copy"]
    findings = []
    for label, pattern in RULES:
        match = pattern.search(copy)
        if match:
            excerpt = copy[max(0, match.start() - 35):match.end() + 85]
            findings.append(f"{label}: {excerpt}")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, type=Path)
    args = parser.parse_args()
    failed = False
    for name in PAGES:
        page = args.site_dir / name
        for finding in inspect_page(page):
            failed = True
            print(f"FAIL {page}: {finding}")
    if failed:
        return 1
    print("PASS: all four pages contain no detected draft/publication-placeholder copy.")
    print("This static check does not replace rendered-page review or factual/legal verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
