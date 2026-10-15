#!/usr/bin/env python3
"""Validate AI privacy output requirements for AppListing legal pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from html_text import visible_text
from legal_facts import build_product_facts


TAG_PATTERN = re.compile(r"<[^>]+>")
HEADING_PATTERN = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase.lower() in text for phrase in phrases)


def ai_disclosure_required(inspect_payload: dict) -> bool:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return False
    if "disclosure_required" in ai_signals:
        return bool(ai_signals.get("disclosure_required"))
    if "claimable" in ai_signals:
        return bool(ai_signals.get("claimable"))
    if not ai_signals.get("active"):
        return False
    return bool(ai_signals.get("user_reachable", True))


def face_data_workflow_kind(inspect_payload: dict) -> str:
    profile = inspect_payload.get("ai_signals", {}).get("review_profile", {})
    if not isinstance(profile, dict):
        return "preview"
    return str(profile.get("workflow_kind", "preview")).strip() or "preview"


def validate_privacy_text(inspect_payload: dict, privacy_text: str) -> list[str]:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict) or not ai_disclosure_required(inspect_payload):
        return []

    legal = inspect_payload.get("legal", {})
    ai_legal = legal.get("ai", {}) if legal.get("confirmed") is True else {}
    providers = [str(item).lower() for item in ai_legal.get("providers", [])]
    providers += [str(item).lower() for item in ai_signals.get("providers", [])]
    hosts = [str(item).lower() for item in ai_signals.get("network_hosts", [])]
    hosts += [str(item.get("host", "")).lower() for item in legal.get("network_services", []) if isinstance(item, dict)]

    errors: list[str] = []

    if not contains_any(privacy_text, ["ai", "artificial intelligence", "model provider", "inference", "assistant"]):
        errors.append("AI privacy section is missing.")

    if not contains_any(privacy_text, ["prompt", "message", "image", "audio", "text", "input", "uploaded content"]):
        errors.append("Privacy policy does not disclose what AI-related data may be sent.")

    recipient_phrases = providers + hosts + ["third-party ai service provider", "external model provider", "inference provider"]
    if not contains_any(privacy_text, recipient_phrases):
        errors.append("Privacy policy does not specify who AI-related data is sent to.")

    if not contains_any(privacy_text, ["with your permission", "after you choose", "before sending", "only when you submit", "only after you request"]):
        errors.append("Privacy policy does not explain user permission or user action before sending AI-related data.")

    if not contains_any(privacy_text, ["collect", "how we collect", "we use", "used to", "purpose", "why we use"]):
        errors.append("Privacy policy does not explain collection method and usage of AI-related data.")

    if ai_legal.get("send_condition") and not contains_any(privacy_text, ["with your permission", "after you choose", "before sending", "only when you submit", "only after you request", "only when you request"]):
        errors.append("Privacy policy does not reflect the confirmed user action before AI processing.")
    if ai_legal.get("equivalent_protection_confirmed") is True and not contains_any(privacy_text, ["equivalent protection", "same level of protection", "same or equal protection", "contractually require"]):
        errors.append("Privacy policy omits the confirmed third-party protection statement.")

    return errors


def extract_headings(raw_html: str) -> list[str]:
    headings: list[str] = []
    for match in HEADING_PATTERN.findall(raw_html):
        title = TAG_PATTERN.sub(" ", match)
        normalized = re.sub(r"\s+", " ", title).strip().lower()
        if normalized:
            headings.append(normalized)
    return headings


def validate_ai_preview_privacy(inspect_payload: dict, privacy_html: str, privacy_text: str) -> list[str]:
    ai_signals = inspect_payload.get("ai_signals", {})
    preview_profile = ai_signals.get("review_profile", {}) if isinstance(ai_signals, dict) else {}
    if not ai_disclosure_required(inspect_payload) or not isinstance(preview_profile, dict) or not preview_profile.get("needs_face_data_clauses"):
        return []

    headings = extract_headings(privacy_html)
    heading_blob = " | ".join(headings)
    errors: list[str] = []
    workflow_kind = face_data_workflow_kind(inspect_payload)

    if workflow_kind == "translation_face_visibility":
        heading_groups = {
            "translation_section": ["ai translation", "selected images", "selected image", "face visibility"],
            "processing_storage_section": ["third-party ai", "processing and storage", "processing", "storage"],
            "retention_deletion_section": ["retention", "deletion", "delete", "translation retention"],
        }
    else:
        heading_groups = {
            "ai_preview_section": ["ai preview", "selected photos", "selected photo", "face data"],
            "processing_storage_section": ["third-party ai", "processing and storage", "processing", "storage"],
            "retention_deletion_section": ["retention", "deletion", "delete", "preview retention"],
        }
    for group_name, phrases in heading_groups.items():
        if not contains_any(heading_blob, phrases):
            errors.append(f"Privacy policy is missing a quoteable face-data section heading for: {group_name}.")

    if not contains_any(privacy_text, ["selected photo", "selected image", "user photo", "source photo"]):
        errors.append("Privacy policy must identify the selected user image used for the face-data workflow.")

    if not contains_any(privacy_text, ["facial features", "face data", "visual characteristics"]):
        errors.append("Privacy policy must describe facial features or equivalent visual characteristics present in face-data inputs.")

    if workflow_kind == "translation_face_visibility":
        if not contains_any(privacy_text, ["translated result", "translation result", "translated text"]):
            errors.append("Privacy policy must describe the translated result returned for the image-translation workflow.")
        if not contains_any(privacy_text, ["extract readable text", "generate the requested translation", "present the result", "show the result"]):
            errors.append("Privacy policy must explain that the selected image is used to extract text and present the requested translation.")
    else:
        if not contains_any(privacy_text, ["generated preview", "preview result", "generated result"]):
            errors.append("Privacy policy must describe the generated preview result.")
        if not contains_any(privacy_text, ["generate the requested preview", "generate the preview", "present the result", "show the result"]):
            errors.append("Privacy policy must explain that the selected photo is used to generate and present the requested preview.")
        if build_product_facts(inspect_payload)["facts"]["photo_export"] is True and not contains_any(privacy_text, ["save the result to photos", "save the result", "save a copy to photos", "save it to photos"]):
            errors.append("Privacy policy must explain the optional save-to-Photos behavior for AI Preview.")

    legal = inspect_payload.get("legal", {})
    ai_legal = legal.get("ai", {}) if legal.get("confirmed") is True else {}
    providers = [str(item).lower() for item in ai_legal.get("providers", [])]
    providers += [str(item).lower() for item in ai_signals.get("providers", [])]
    hosts = [str(item).lower() for item in ai_signals.get("network_hosts", [])]
    hosts += [str(item.get("host", "")).lower() for item in legal.get("network_services", []) if isinstance(item, dict)]
    if not contains_any(privacy_text, providers + hosts):
        errors.append("Privacy policy must name the concrete third-party AI provider or host for face-data processing.")

    processing = str(ai_legal.get("processing", "")).strip().lower()
    retention = str(ai_legal.get("retention", "")).strip().lower()
    deletion = str(ai_legal.get("deletion", "")).strip().lower()
    if processing and processing not in privacy_text:
        errors.append("Privacy policy does not match the confirmed AI processing and storage details.")
    if retention and retention not in privacy_text:
        errors.append("Privacy policy does not match the confirmed AI retention details.")
    if deletion and deletion not in privacy_text:
        errors.append("Privacy policy does not match the confirmed AI deletion details.")
    if ai_legal.get("identity_processing") is False and not contains_any(privacy_text, ["identity verification", "biometric", "face recognition"]):
        errors.append("Privacy policy omits the confirmed restriction on identity or biometric processing.")

    return errors


def validate_privacy_output(inspect_payload: dict, privacy_html: str) -> list[str]:
    privacy_text = html_to_text(privacy_html)
    return validate_privacy_text(inspect_payload, privacy_text) + validate_ai_preview_privacy(
        inspect_payload,
        privacy_html,
        privacy_text,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AI privacy coverage in PrivacyPolicy.html.")
    parser.add_argument("--inspect-json", required=True, help="Path to the inspect JSON")
    parser.add_argument("--privacy-html", required=True, help="Path to PrivacyPolicy.html")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    privacy_html = Path(args.privacy_html).read_text(encoding="utf-8")
    errors = validate_privacy_output(inspect_payload, privacy_html)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
