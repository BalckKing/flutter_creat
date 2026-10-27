#!/usr/bin/env python3
"""Validate the final, public App Store Review Remarks contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


HEADINGS = (
    "## 1. Actual Device",
    "## 2. Test Devices and Operating Systems",
    "## 3. App Purpose, Intended Audience, and Problem Solved",
    "## 4. Setup Steps",
    "## 5. External Services",
    "## 6. Regional Differences",
    "## 7. Unique Value",
)
BASIC_LABELS = (
    "App name:",
    "Purpose:",
    "Category:",
)
PENDING_RE = re.compile(
    r"\b(?:not\s+provided|pending(?:\s+confirmation)?|to\s+be\s+confirmed|"
    r"awaiting\s+confirmation|unconfirmed|unknown)\b",
    re.IGNORECASE,
)
EMBEDDED_BROWSER_RE = re.compile(
    r"web\s*view|wkwebview|webkit|embedded\s+(?:web|browser)|browser\s+container|"
    r"网页容器|嵌入式网页|网页视图",
    re.IGNORECASE,
)
NON_IPHONE_RE = re.compile(
    r"\b(?:ipad|ipados|android|mac(?:os)?|apple\s+watch|watchos|"
    r"apple\s+tv|tvos|vision\s+pro|visionos|windows)\b",
    re.IGNORECASE,
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _section_ranges(text: str):
    matches = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    return [(m.group(0), m.start(), matches[i + 1].start() if i + 1 < len(matches) else len(text))
            for i, m in enumerate(matches)]


def validate(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        return [f"cannot read remarks: {error}"]

    if len(text) > 4000:
        findings.append(f"remarks exceed 4,000 characters: {len(text)}")
    if "**" in text:
        findings.append("bold markers are not allowed")
    if CJK_RE.search(text):
        findings.append("remarks must be English-only: CJK text found")
    for label, pattern in (
        ("unconfirmed or missing information", PENDING_RE),
        ("embedded browser implementation term", EMBEDDED_BROWSER_RE),
        ("non-iPhone device", NON_IPHONE_RE),
    ):
        match = pattern.search(text)
        if match:
            findings.append(f"{label}: {match.group(0)}")
    if re.search(r"^Category:\s*(?:Education|Educational)\s*$", text, re.IGNORECASE | re.MULTILINE):
        findings.append("Category must use Popular Science instead of Education")
    if not re.search(r"^# App Review Remarks\s*$", text, re.MULTILINE):
        findings.append("missing exact '# App Review Remarks' title")
    for label in BASIC_LABELS:
        if not re.search(r"^" + re.escape(label) + r"\s*\S", text, re.MULTILINE):
            findings.append(f"missing basic information label: {label}")

    sections = _section_ranges(text)
    actual = [title for title, _, _ in sections]
    if actual != list(HEADINGS):
        findings.append(f"section headings/order must be exactly: {', '.join(HEADINGS)}")
        return findings

    first_body = text[sections[0][1]:sections[0][2]].split('\n', 1)[1].strip()
    if first_body != "- iPhone 17 Pro Max, iOS 26.5":
        findings.append("Actual Device must be exactly '- iPhone 17 Pro Max, iOS 26.5'")
    regional_body = text[sections[5][1]:sections[5][2]].split('\n', 1)[1].strip()
    if regional_body != "- All regions are the same.":
        findings.append("Regional Differences must be exactly '- All regions are the same.'")

    for index, (_, start, end) in enumerate(sections, start=1):
        body = text[start:end]
        if index == 2 and not body.split('\n', 1)[1].strip():
            # Unknown device records are omitted from the public artifact.
            continue
        if index == 4:
            if not re.search(r"^\s*\d+\.\s+\S", body, re.MULTILINE):
                findings.append("Setup Steps must use an ordered list")
        elif not re.search(r"^\s*-\s+\S", body, re.MULTILINE):
            findings.append(f"section {index} must contain bullet points")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remarks-file", required=True, type=Path)
    args = parser.parse_args()
    findings = validate(args.remarks_file)
    if findings:
        for finding in findings:
            print(f"FAIL {args.remarks_file}: {finding}")
        return 1
    print("PASS: Review Remarks meet the checked structure, iPhone-only and fixed-text contract.")
    print("Verify factual claims and current-app test evidence separately; static checks do not prove testing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
