#!/usr/bin/env python3
"""Prepare AI-facing classification input from extracted iOS app evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_classifier_input(evidence: dict) -> dict:
    capability_candidates = evidence.get("capability_candidates", {})
    top_capabilities = [
        {
            "name": name,
            "score": payload.get("score", 0.0),
            "confidence": payload.get("confidence", "low"),
            "evidence": payload.get("evidence", {}),
        }
        for name, payload in capability_candidates.items()
    ]
    return {
        "source_stack": evidence.get("source_stack"),
        "app_name": evidence.get("app_name"),
        "app_slug": evidence.get("app_slug"),
        "support_email": evidence.get("support_email"),
        "support_email_source": evidence.get("support_email_source"),
        "permissions": evidence.get("permissions", {}),
        "dependencies": evidence.get("dependencies", []),
        "network_destinations": evidence.get("network_destinations", []),
        "privacy_signals": evidence.get("privacy_signals", {}),
        "ai_signals": evidence.get("ai_signals", {}),
        "access_signals": evidence.get("access_signals", {}),
        "capability_candidates": top_capabilities,
        "evidence": evidence.get("evidence", {}),
        "instructions": {
            "required_outputs": [
                "category",
                "archetype",
                "theme",
                "theme_hint",
                "capabilities",
                "claimable_features",
                "confidence",
                "reasoning",
            ],
            "constraints": [
                "Do not infer category from app name or archetype.",
                "Use evidence and capability candidates only.",
                "Do not claim features that lack supporting evidence.",
                "Private notes, local profiles, catalog likes/reports, and community place names do not establish user-generated community content.",
                "System sharing and restoring hidden items do not establish data backup, export, or restore tools.",
                "Do not infer a credential-account or full login system from profile, feed, post_creation, logout, session, or community-only evidence.",
                "Do not erase AI or privacy signals from the classification reasoning when they are material.",
                "Theme must come from inspected evidence, review notes, or product copy rather than hardcoded app-name assumptions.",
                "When access_signals.mode is not credential_account, avoid account/register/log in/credentials wording in reasoning and theme_hint.",
                "theme_hint must be a concise app-writing payload with identity, experience, keywords, currency, index_title_suffix, social_noun, and post_label.",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AI-facing classification input for iOS AppListing.")
    parser.add_argument("--inspect-json", required=True, help="Path to inspect output JSON")
    args = parser.parse_args()
    evidence = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    print(json.dumps(build_classifier_input(evidence), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
