#!/usr/bin/env python3
"""Validate Intro.md structure and content rules for AppListing."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXPECTED_TITLE_TEMPLATE = "# {app_name} — App Store Description"
EXPECTED_SECTION_HEADINGS = [
    "## App Name",
    "## Sub Title",
    "## Category",
    "## Description",
    "## Keywords",
    "## Support URL",
    "## Terms of Service URL",
    "## All URL",
    "## UGC",
    "## Chat",
    "## Copyright",
]

ALLOWED_CATEGORIES = {
    "图书 (Books)",
    "商务 (Business)",
    "开发者工具 (Developer Tools)",
    "教育 (Education)",
    "娱乐 (Entertainment)",
    "财务 (Finance)",
    "美食佳饮 (Food & Drink)",
    "游戏 (Games)",
    "图形和设计 (Graphics & Design)",
    "健康健美 (Health & Fitness)",
    "生活 (Lifestyle)",
    "儿童 (Kids)",
    "报刊杂志 (Magazines & Newspapers)",
    "医疗 (Medical)",
    "音乐 (Music)",
    "导航 (Navigation)",
    "新闻 (News)",
    "摄影与录像 (Photo & Video)",
    "效率 (Productivity)",
    "参考 (Reference)",
    "社交 (Social Networking)",
    "体育 (Sports)",
    "旅游 (Travel)",
    "工具 (Utilities)",
    "天气 (Weather)",
}

DISALLOWED_SUBTITLE_WORDS = {
    "chat",
    "call",
    "ai",
    "bag",
    "preview",
    "notes",
}

DESCRIPTION_STYLES = {
    "concise",
    "feature_3",
    "feature_4",
    "feature_5",
    "benefit_3",
    "benefit_4",
    "longform",
    "summary_plus_feature_3",
    "summary_plus_benefit_3",
    "community_then_purchase",
    "feature_then_value",
    "you_can_3",
    "you_can_4",
    "why_choose_3",
    "homebase_4",
    "all_in_one",
    "members_first",
    "everyday_use",
}

LOW_LEVEL_PHRASES = [
    "video chat",
    "1v1 call",
    "preview flow",
    "try-on pipeline",
]
UGC_DESCRIPTION_PHRASES = [
    "community",
    "share",
    "sharing",
    "profile",
    "post",
    "publish",
    "updates",
]
CHAT_DESCRIPTION_PHRASES = [
    "chat",
    "message",
    "messages",
    "conversation",
    "conversations",
    "inbox",
    "thread",
    "threads",
]
GENERIC_DESCRIPTION_FIRST_SENTENCE_PHRASES = [
    "community-driven lifestyle app",
    "community lifestyle app",
    "community app",
]


SECTION_HEADING_RE = re.compile(r"^(#|##) ")
SUBTITLE_PATTERN = re.compile(r"^[A-Z][a-zA-Z]+ & [A-Z][a-zA-Z]+$")
URL_PATTERN = re.compile(r"^https://[^\s]+$")
COPYRIGHT_PATTERN = re.compile(r"^©\s+\d{4}\s+.+")
BULLET_RE = re.compile(r"^[-*]\s+")
WITH_YOU_CAN_RE = re.compile(r"^With .+, you can:$")
ALL_URL_BORDER = "=================================================="


def parse_sections(markdown: str) -> tuple[list[str], dict[str, str]]:
    lines = markdown.splitlines()
    headings: list[str] = []
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None

    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("# ") and not headings:
            headings.append(stripped)
            current_heading = None
            continue
        if stripped.startswith("## "):
            headings.append(stripped)
            current_heading = stripped
            sections.setdefault(current_heading, [])
            continue
        if current_heading is not None:
            sections[current_heading].append(line)

    return headings, {key: "\n".join(value).strip() for key, value in sections.items()}


def count_bullets(text: str) -> int:
    return sum(1 for line in text.splitlines() if BULLET_RE.match(line.strip()))


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


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


def translation_disclosure_required(inspect_payload: dict) -> bool:
    translation_signals = inspect_payload.get("translation_signals", {})
    if isinstance(translation_signals, dict) and translation_signals:
        if not translation_signals.get("active"):
            return False
        return bool(translation_signals.get("disclosure_required", translation_signals.get("user_reachable", True)))
    return bool({"translate_text", "translate_voice"} & active_capabilities(inspect_payload))


def face_data_review_profile(inspect_payload: dict) -> dict:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return {}
    profile = ai_signals.get("review_profile", {})
    if not isinstance(profile, dict) or not profile.get("needs_face_data_clauses"):
        return {}
    if not (ai_disclosure_required(inspect_payload) or translation_disclosure_required(inspect_payload)):
        return {}
    return profile


def first_sentence(text: str) -> str:
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line:
            continue
        match = re.match(r"^(.+?[.!?])(?:\s|$)", line)
        return match.group(1).strip() if match else line
    return ""


def active_capabilities(inspect_payload: dict) -> set[str]:
    active: set[str] = set()
    for name, payload in inspect_payload.get("capability_candidates", {}).items():
        if float(payload.get("score", 0.0)) >= 1.0:
            active.add(name)
    return active


def face_data_workflow_kind(inspect_payload: dict) -> str:
    profile = face_data_review_profile(inspect_payload)
    if not isinstance(profile, dict):
        return "preview"
    return str(profile.get("workflow_kind", "preview")).strip() or "preview"


def has_chat_capability(inspect_payload: dict, active: set[str] | None = None) -> bool:
    messaging_signals = inspect_payload.get("messaging_signals", {})
    if isinstance(messaging_signals, dict) and "real_user_chat" in messaging_signals:
        return bool(messaging_signals.get("real_user_chat"))
    return "messaging" in (active or active_capabilities(inspect_payload))


def expected_ugc_chat_values(inspect_payload: dict) -> tuple[str, str]:
    active = active_capabilities(inspect_payload)
    privacy_signals = inspect_payload.get("privacy_signals", {})
    ugc_enabled = bool({"feed", "post_creation"} & active)
    if not ugc_enabled and bool(privacy_signals.get("user_content")):
        ugc_enabled = True
    chat_enabled = has_chat_capability(inspect_payload, active)
    return ("Yes" if ugc_enabled else "No", "Yes" if chat_enabled else "No")


def validate_intro(inspect_payload: dict, intro_markdown: str) -> list[str]:
    headings, sections = parse_sections(intro_markdown)
    errors: list[str] = []

    expected_title = EXPECTED_TITLE_TEMPLATE.format(app_name=inspect_payload.get("app_name", "App Name"))
    expected_headings = [expected_title, *EXPECTED_SECTION_HEADINGS]

    if headings != expected_headings:
        errors.append("Intro headings must exactly match the fixed template order and names.")
        return errors

    app_name = sections["## App Name"]
    subtitle = sections["## Sub Title"]
    category = sections["## Category"]
    description = sections["## Description"]
    keywords = sections["## Keywords"]
    support_url = sections["## Support URL"]
    terms_url = sections["## Terms of Service URL"]
    all_url = sections["## All URL"]
    ugc_value = sections["## UGC"]
    chat_value = sections["## Chat"]
    copyright_text = sections["## Copyright"]

    if not app_name:
        errors.append("App Name section must not be empty.")

    if not subtitle or len(subtitle) > 30:
        errors.append("Sub Title must be present and at most 30 characters.")
    elif not SUBTITLE_PATTERN.fullmatch(subtitle):
        errors.append("Sub Title must be exactly two Title Case words joined by ' & '.")
    else:
        left, right = [part.strip().lower() for part in subtitle.split("&")]
        if left in DISALLOWED_SUBTITLE_WORDS or right in DISALLOWED_SUBTITLE_WORDS:
            errors.append("Sub Title uses a disallowed literal feature word.")
        if "video" in {left, right}:
            capability_candidates = inspect_payload.get("capability_candidates", {})
            has_video_evidence = any(
                float(payload.get("score", 0.0)) >= 1.0
                for payload in capability_candidates.values()
                if isinstance(payload, dict)
            )
            if not has_video_evidence:
                errors.append("Sub Title may only use 'Video' when inspected evidence supports a video-centered identity.")

    if not category:
        errors.append("Category section must not be empty.")
    elif category not in ALLOWED_CATEGORIES:
        errors.append("Category must be one concise allowed App Store category label.")

    if not description:
        errors.append("Description section must not be empty.")
    else:
        if len(description) > 4000:
            errors.append("Description must be at most 4000 characters.")
        if "<" in description or ">" in description:
            errors.append("Description must be plain text only, with no HTML.")
        first_255 = description[:255].strip()
        if len(first_255) < 40:
            errors.append("Description should explain the app clearly within the first 255 characters.")
        opening = first_sentence(description).lower()
        if any(phrase in opening for phrase in GENERIC_DESCRIPTION_FIRST_SENTENCE_PHRASES):
            errors.append("Description first sentence is too generic and should state the app's concrete theme.")
        preview_profile = face_data_review_profile(inspect_payload)
        if preview_profile:
            if face_data_workflow_kind(inspect_payload) == "translation_face_visibility":
                required_groups = {
                    "image_translation": ["image translation", "translated result", "translation result", "ai-assisted translation"],
                    "photo_selection": ["choose a photo", "selected image", "selected photo", "upload a photo", "pick a photo"],
                    "consent_step": ["consent prompt", "reviewing the consent", "review the consent", "review consent"],
                    "result_review": ["review the translated result", "review the translation", "translated result in the app", "receive translated"],
                }
            else:
                required_groups = {
                    "ai_preview": ["ai preview", "preview result", "generated preview"],
                    "photo_selection": ["choose a photo", "selected photo", "upload a photo", "pick a photo"],
                    "review_step": ["review it", "review the result", "review the generated result", "review the preview"],
                    "optional_save": ["save it to photos", "save the finished image to photos", "optionally save", "save the result to photos"],
                }
            for group_name, phrases in required_groups.items():
                if not contains_any(first_255, phrases):
                    errors.append(
                        f"Description must explain the face-data workflow within the first 255 characters when face-data review signals are active: {group_name}."
                    )
        style = detect_description_style(description)
        if style is None:
            errors.append("Description does not match any allowed description style.")
        elif style == "feature_3" and count_bullets(description) != 3:
            errors.append("feature_3 description must contain exactly 3 bullets.")
        elif style == "summary_plus_feature_3" and count_bullets(description) != 3:
            errors.append("summary_plus_feature_3 description must contain exactly 3 bullets.")
        elif style == "feature_4" and count_bullets(description) != 4:
            errors.append("feature_4 description must contain exactly 4 bullets.")
        elif style == "feature_then_value" and count_bullets(description) != 4:
            errors.append("feature_then_value description must contain exactly 4 bullets.")
        elif style == "feature_5":
            if count_bullets(description) != 5:
                errors.append("feature_5 description must contain exactly 5 bullets.")
            if not any(WITH_YOU_CAN_RE.fullmatch(line.strip()) for line in description.splitlines()):
                errors.append("feature_5 description must include a 'With {AppName}, you can:' line.")
        elif style == "benefit_3" and count_bullets(description) != 3:
            errors.append("benefit_3 description must contain exactly 3 bullets.")
        elif style == "summary_plus_benefit_3" and count_bullets(description) != 3:
            errors.append("summary_plus_benefit_3 description must contain exactly 3 bullets.")
        elif style == "benefit_4" and count_bullets(description) != 4:
            errors.append("benefit_4 description must contain exactly 4 bullets.")
        elif style == "community_then_purchase" and count_bullets(description) != 3:
            errors.append("community_then_purchase description must contain exactly 3 bullets.")
        elif style not in {"feature_3", "feature_4", "feature_5"}:
            lowered = description.lower()
            for phrase in LOW_LEVEL_PHRASES:
                if phrase in lowered:
                    errors.append(f"Non-feature-list description must avoid low-level phrase: {phrase}.")

    if not keywords:
        errors.append("Keywords section must not be empty.")
    else:
        if len(keywords) > 100:
            errors.append("Keywords must be at most 100 characters total.")
        parts = [part.strip() for part in keywords.split(",") if part.strip()]
        if len(parts) < 2:
            errors.append("Keywords must contain comma-separated terms.")

    if not URL_PATTERN.fullmatch(support_url):
        errors.append("Support URL must be a full https URL.")
    if not URL_PATTERN.fullmatch(terms_url):
        errors.append("Terms of Service URL must be a full https URL.")
    all_url_errors = validate_all_url_block(all_url, support_url, terms_url)
    errors.extend(all_url_errors)

    expected_ugc, expected_chat = expected_ugc_chat_values(inspect_payload)
    if ugc_value not in {"Yes", "No"}:
        errors.append("UGC section must be exactly 'Yes' or 'No'.")
    elif ugc_value != expected_ugc:
        errors.append(f"UGC section must be '{expected_ugc}' based on inspected evidence.")
    if chat_value not in {"Yes", "No"}:
        errors.append("Chat section must be exactly 'Yes' or 'No'.")
    elif chat_value != expected_chat:
        errors.append(f"Chat section must be '{expected_chat}' based on inspected evidence.")

    if ugc_value == "Yes" and not contains_any(description, UGC_DESCRIPTION_PHRASES):
        errors.append("Description should naturally mention community, profile, sharing, or post behavior when UGC is Yes.")
    if chat_value == "Yes" and not contains_any(description, CHAT_DESCRIPTION_PHRASES):
        errors.append("Description should naturally mention messaging, chat, or conversations when Chat is Yes.")
    if chat_value == "No" and contains_any(description, CHAT_DESCRIPTION_PHRASES):
        errors.append("Description must not imply in-app messaging or chat when Chat is No.")

    if not COPYRIGHT_PATTERN.fullmatch(copyright_text):
        errors.append("Copyright must start with a real © YYYY rights line.")

    if inspect_payload.get("iap_shop_code_display") not in (None, "", "None detected"):
        lowered = description.lower()
        if not any(token in lowered for token in ("purchase", "credits", "coins", "subscription", "virtual")):
            errors.append("Description should naturally mention purchase or virtual goods context when IAP is detected.")
        preview_profile = face_data_review_profile(inspect_payload)
        if preview_profile:
            if not contains_any(description[:255], ["credits", "purchase", "virtual goods"]):
                errors.append("Description must mention credits or purchase context within the first 255 characters for face-data AI flows with IAP.")

    return errors


def validate_all_url_block(all_url: str, support_url: str, terms_url: str) -> list[str]:
    errors: list[str] = []
    if not all_url:
        return ["All URL section must not be empty."]

    lines = [line.strip() for line in all_url.splitlines() if line.strip()]
    if len(lines) != 6:
        return ["All URL section must contain exactly 6 non-empty lines."]

    if lines[0] != ALL_URL_BORDER or lines[-1] != ALL_URL_BORDER:
        errors.append("All URL section must start and end with the fixed border line.")

    expected_labels = ["首页: ", "隐私政策: ", "用户协议: ", "Support: "]
    for index, label in enumerate(expected_labels, start=1):
        if not lines[index].startswith(label):
            errors.append(f"All URL line {index + 1} must start with '{label}'.")

    extracted_urls: list[str] = []
    for line in lines[1:5]:
        if ": " not in line:
            extracted_urls.append("")
            continue
        extracted_urls.append(line.split(": ", 1)[1].strip())

    for url in extracted_urls:
        if not URL_PATTERN.fullmatch(url):
            errors.append("All URL section contains a non-https URL.")
            break

    if len(extracted_urls) == 4:
        if extracted_urls[2] != terms_url:
            errors.append("All URL 用户协议 must exactly match Terms of Service URL.")
        if extracted_urls[3] != support_url:
            errors.append("All URL Support must exactly match Support URL.")

    return errors


def detect_description_style(description: str) -> str | None:
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    bullet_count = count_bullets(description)
    sentence_count = len([part for part in re.split(r"[.!?]+", description) if part.strip()])
    lowered = description.lower()
    has_with_you_can = any(WITH_YOU_CAN_RE.fullmatch(line) for line in lines)
    has_highlights = "Highlights:" in lines
    has_why_people_return = "Why People Return:" in lines
    has_why_it_feels_easy = "Why It Feels Easy:" in lines
    has_inside_app = any(re.fullmatch(r"Inside .+:", line) for line in lines)
    benefit_words = ("benefit", "enjoy", "feel", "discover", "confidence", "ease")
    why_choose_words = ("why choose", "clear reasons", "keep coming back", "reasons people keep")
    homebase_words = ("one clear home", "one place", "stay connected", "steady flow")

    if bullet_count == 5 and has_with_you_can:
        return "feature_5"
    if bullet_count == 4:
        if has_with_you_can and has_why_it_feels_easy:
            return "feature_then_value"
        if has_with_you_can:
            return "you_can_4"
        if any(word in lowered for word in benefit_words):
            return "benefit_4"
        if any(word in lowered for word in homebase_words):
            return "homebase_4"
        return "feature_4"
    if bullet_count == 5:
        return "feature_5"
    if bullet_count == 3:
        if has_highlights:
            return "summary_plus_feature_3"
        if has_why_people_return:
            return "summary_plus_benefit_3"
        if has_inside_app:
            return "community_then_purchase"
        if has_with_you_can:
            return "you_can_3"
        if any(word in lowered for word in why_choose_words):
            return "why_choose_3"
        if any(word in lowered for word in benefit_words):
            return "benefit_3"
        return "feature_3"
    if 4 <= sentence_count <= 5:
        return "longform"
    if any(word in lowered for word in ("members", "member-led", "member flow", "community space")):
        return "members_first"
    if any(
        phrase in lowered
        for phrase in (
            "everyday repeat visits",
            "reopen the app",
            "repeat-use rhythm",
            "pick up across everyday",
        )
    ):
        return "everyday_use"
    if any(phrase in lowered for phrase in ("all-in-one", "one place", "keeps together", "readable place")):
        return "all_in_one"
    if len(lines) == 1 and sentence_count <= 2 and any(
        phrase in lowered
        for phrase in ("welcome to", "built for", "designed around", "brings together", "for sharing", "for ")
    ):
        return "concise"
    if len(lines) == 1 and sentence_count <= 3:
        return "concise"
    if sentence_count >= 2:
        return "longform"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Intro.md coverage and structure.")
    parser.add_argument("--inspect-json", required=True, help="Path to the inspect JSON")
    parser.add_argument("--intro-md", required=True, help="Path to Intro.md")
    args = parser.parse_args()

    inspect_payload = json.loads(Path(args.inspect_json).read_text(encoding="utf-8"))
    intro_markdown = Path(args.intro_md).read_text(encoding="utf-8")
    errors = validate_intro(inspect_payload, intro_markdown)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
