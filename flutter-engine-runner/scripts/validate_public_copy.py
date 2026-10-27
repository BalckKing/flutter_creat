#!/usr/bin/env python3
"""Scan user-visible Flutter/HTML copy for prohibited review-facing terms."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path


FORBIDDEN = (
    "H5", "SDK", "广告", "第三方框架", "技术实现", "内部模块", "lib",
    "package", "packages", "local", "device", "测试", "模板", "马甲", "过审",
    "third-party framework", "technical implementation", "internal module",
    "testing", "template", "reskin", "white-label", "review bypass", "ads",
    "advertisement", "advertising", "webview", "webkit",
)
FORBIDDEN_RE = re.compile(
    r"(?<![A-Za-z])(?:" + "|".join(
        r"[\s\-_\u200b\ufeff]*".join(map(re.escape, term)) for term in FORBIDDEN
    ) + r")(?![A-Za-z])", re.IGNORECASE,
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if self.hidden:
            return
        attrs = dict(attrs)
        for key in ("alt", "title", "aria-label", "aria-description", "placeholder", "value"):
            if attrs.get(key):
                self.parts.append(attrs[key])
        if tag == "meta" and attrs.get("content"):
            self.parts.append(attrs["content"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def scan_text(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    if CJK_RE.search(text):
        findings.append("CJK text")
    match = FORBIDDEN_RE.search(text)
    if match:
        findings.append(f"prohibited term {match.group(0)!r}")
    return findings


def validate(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"{root}: project root does not exist"]
    if not (root / "lib").is_dir():
        return [f"{root}: missing Flutter lib directory; public copy was not scanned"]
    files = list((root / "lib").rglob("*.dart")) if (root / "lib").exists() else []
    files += [root / "welcome.html"]
    site = root / "aduit" / "site"
    if site.exists():
        files += list(site.glob("*.html"))
    for path in files:
        if not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            findings.append(f"{path}: cannot read: {error}")
            continue
        visible = source
        if path.suffix.lower() == ".dart":
            # Restrict Dart checks to string literals so internal identifiers such
            # as package paths or service variable names are not public copy.
            literal_pattern = re.compile(
                r"//[^\n]*|/\*[\s\S]*?\*/|"
                r"(?s:(?:r)?'''(.*?)'''|(?:r)?\"\"\"(.*?)\"\"\")|"
                r"(?:r)?'(?:\\.|[^'\\])*'|(?:r)?\"(?:\\.|[^\"\\])*\""
            )
            flat: list[str] = []
            ui_call = re.compile(
                r"(?:Text(?:\.rich)?|SelectableText|RichText|Tooltip|Semantics|"
                r"AppBar|NavigationDestination|BottomNavigationBarItem|SnackBar|"
                r"showDialog)\s*\([^)]*$"
            )
            ui_property = re.compile(
                r"(?:label|title|subtitle|hintText|helperText|errorText|semanticLabel|"
                r"tooltip|message|placeholder|aria-label)\s*:\s*$"
            )
            for match in literal_pattern.finditer(source):
                if match.group(0).startswith(("//", "/*")):
                    continue
                context = source[max(0, match.start() - 220):match.start()]
                if not (ui_call.search(context) or ui_property.search(context)):
                    continue
                if match.group(1) is not None:
                    flat.append(match.group(1))
                elif match.group(2) is not None:
                    flat.append(match.group(2))
                else:
                    value = match.group(0)
                    flat.append(value[2:-1] if value.startswith(("r'", 'r"')) else value[1:-1])
            visible = " ".join(flat)
        elif path.suffix.lower() == ".html":
            parser = VisibleHTML()
            parser.feed(source)
            parser.close()
            visible = " ".join(parser.parts)
        for finding in scan_text(path, visible):
            findings.append(f"{path}: {finding}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    findings = validate(args.project_root)
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print("PASS: no prohibited terms found in detected UI literals and static HTML copy.")
    print("Review rendered copy, indirect strings and script-generated text separately; this scan is not runtime proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
