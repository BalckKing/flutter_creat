#!/usr/bin/env python3
"""Static validation of standalone launch-guide output, without browser tests."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from html_text import visible_text


CONTINUE_FUNCTION = """function continueToApp() {
  if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {
    window.AppBridge.postMessage('continue');
    return;
  }
  window.location.href = 'go://continue';
}"""


class OnboardingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards = 0
        self.dots = 0
        self.cta = 0
        self.template_id = ""
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attributes = dict(attrs)
        if tag == "body":
            self.template_id = str(attributes.get("data-template-id", ""))
        classes = str(attributes.get("class", "")).split()
        self.cards += int(tag == "article" and "onboarding-card" in classes)
        self.dots += int(tag == "button" and "onboarding-dot" in classes)
        self.cta += int(tag == "button" and "onboarding-action" in classes)
        for key in ("src", "srcset", "poster"):
            value = attributes.get(key)
            if value and not str(value).startswith("data:"):
                self.errors.append(f"index depends on an external resource: {tag}.{key}")
        if tag == "link" and attributes.get("href"):
            self.errors.append("index must not load linked resources")
        if tag == "a" and str(attributes.get("href", "")).lower().endswith(".html"):
            self.errors.append("index must not contain cross-page navigation")


def validate_onboarding_output(raw_html: str) -> list[str]:
    parser = OnboardingParser()
    parser.feed(raw_html)
    errors = parser.errors
    if not 3 <= parser.cards <= 5 or parser.dots != parser.cards:
        errors.append("index requires 3–5 cards and one clickable dot per card")
    if parser.cta != 1:
        errors.append("index requires exactly one Continue action")
    if parser.template_id and not parser.template_id.startswith("onboarding-"):
        errors.append("index has an invalid onboarding template marker")
    for token in ("viewport-fit=cover", "env(safe-area-inset-top", "env(safe-area-inset-bottom"):
        if token not in raw_html:
            errors.append(f"index is missing {token}")
    if re.sub(r"\s+", " ", CONTINUE_FUNCTION) not in re.sub(r"\s+", " ", raw_html):
        errors.append("index must preserve the exact Continue bridge/fallback function")
    if re.search(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", visible_text(raw_html)):
        errors.append("index visible text must be English")
    if re.search(r"@import|url\(\s*['\"]?(?!data:)[^\s)]+|\bfetch\s*\(", raw_html, re.IGNORECASE):
        errors.append("index must not request external CSS, fonts, images or runtime data")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-html", required=True)
    args = parser.parse_args()
    errors = validate_onboarding_output(Path(args.index_html).read_text(encoding="utf-8"))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
