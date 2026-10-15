#!/usr/bin/env python3
"""Validate fixed AppListing directory contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = {
    "Intro.md",
    "site/index.html",
    "site/PrivacyPolicy.html",
    "site/Terms&Conditions.html",
    "site/Support.html",
    "site/img/logo.png",
}


def collect_files(app_listing_root: Path) -> set[str]:
    return {
        str(path.relative_to(app_listing_root)).replace("\\", "/")
        for path in app_listing_root.rglob("*")
        if path.is_file()
    }


def validate_listing_contract(app_listing_root: Path) -> list[str]:
    files = collect_files(app_listing_root)
    errors: list[str] = []

    for required in sorted(REQUIRED_FILES):
        if required not in files:
            errors.append(f"Missing required AppListing file: {required}.")

    extras = sorted(files - REQUIRED_FILES)
    for extra in extras:
        errors.append(f"Unexpected AppListing file outside fixed contract: {extra}.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate fixed AppListing directory contract.")
    parser.add_argument("--app-listing-dir", required=True, help="Path to AppListing directory")
    args = parser.parse_args()

    app_listing_root = Path(args.app_listing_dir)
    errors = validate_listing_contract(app_listing_root)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
