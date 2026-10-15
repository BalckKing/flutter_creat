#!/usr/bin/env python3
"""Validate that generated legal pages do not claim unsupported product areas."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


from html_text import visible_text
from legal_facts import build_product_facts, legal_fact_errors


def html_to_text(raw_html: str) -> str:
    return visible_text(raw_html).lower()


def validate_dynamic_legal_output(inspect_payload: dict, privacy_text: str, terms_text: str) -> list[str]:
    matrix = build_product_facts(inspect_payload)
    facts = matrix["facts"]
    combined = f"{privacy_text} {terms_text}".lower()
    # Only contradictions and high-risk unsupported legal configurations block
    # validation. Operator, jurisdiction, audience, retention, and recipient
    # details are reported separately for final legal review.
    errors = legal_fact_errors(inspect_payload)
    rules = {
        "iap": r"\b(?:in-app purchases?|purchase records|billing|virtual goods|consumable items|subscriptions?)\b",
        "location_features": r"\b(?:nearby places|map-based tools|location sharing)\b",
        "community_ugc": r"\b(?:community content|publishing features|user-generated content)\b",
        "messaging": r"\b(?:member messaging|private chat|chat messages)\b",
        "photo_editing": r"\b(?:photo-editing|photo editing|finished edits)\b",
        "saved_notes": r"\b(?:saved notes|dictated notes)\b",
    }
    for field, pattern in rules.items():
        if facts.get(field) is not True and re.search(pattern, combined):
            errors.append(f"Legal output claims {field} without corresponding product evidence.")
    if facts["tracking"] is not True and re.search(r"\b(?:tracking starts|tracking permission|app tracking transparency)\b", combined):
        errors.append("Privacy output describes tracking without confirmed tracking behavior.")
    if not (facts["photo_capture"] or facts["photo_import"] or facts["photo_upload"] or facts["photo_editing"]) and re.search(r"\b(?:photos?|photo library|camera access|selected image)\b", combined):
        errors.append("Legal output mentions photo handling without photo-feature evidence.")
    if facts["children_targeted"] != False and "not directed to children" in combined:
        errors.append("Privacy output asserts a non-child audience without confirmed audience evidence.")
    age = re.search(r"you must be (\d+) or older", terms_text.lower())
    if age and facts["minimum_age"] != int(age.group(1)):
        errors.append("Terms age restriction does not match the confirmed minimum age.")
    if facts["consumable_iap"] is not True and re.search(r"\bconsumable (?:digital )?items\b", terms_text.lower()):
        errors.append("Terms describe consumables without product-type evidence.")
    if facts["face_data"] is not True and "face recognition" in combined:
        errors.append("Legal output inserts face-data clauses without a face-data workflow.")
    return list(dict.fromkeys(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-json", required=True)
    parser.add_argument("--privacy-html", required=True)
    parser.add_argument("--terms-html", required=True)
    args = parser.parse_args()
    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    errors = validate_dynamic_legal_output(
        inspect_payload,
        html_to_text(Path(args.privacy_html).read_text(encoding="utf-8")),
        html_to_text(Path(args.terms_html).read_text(encoding="utf-8")),
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
