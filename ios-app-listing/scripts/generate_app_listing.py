#!/usr/bin/env python3
"""Generate evidence-based AppListing outputs for Flutter or Swift iOS apps."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import random
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_common import (
    inspect_access_mode,
    inspect_has_credential_account,
    inspect_has_local_session,
    is_valid_image_file,
)
from legal_facts import build_product_facts as normalize_product_facts, legal_fact_errors, legal_fact_review_items
from legal_copy import build_privacy as build_evidenced_privacy, build_terms as build_evidenced_terms
from legal_copy import feature_labels
from legal_copy import build_faq as build_evidenced_faq


ONBOARDING_TEMPLATE_IDS = (
    "onboarding-cards",
    "onboarding-spotlight",
    "onboarding-compact",
    "onboarding-minimal",
    "onboarding-feature-list",
)


def choose_onboarding_template_id() -> str:
    return random.choice(ONBOARDING_TEMPLATE_IDS)


ROOT = SCRIPT_DIR.parents[0]
TODAY = date.today().strftime("%B %d, %Y")
DESCRIPTION_STYLES = [
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
]
SUBTITLE_PATTERN = re.compile(r"^[A-Z][a-zA-Z]+ & [A-Z][a-zA-Z]+$")
SUBTITLE_POOL = [
    "Style & Vibes",
    "Glow & Mood",
    "Charm & Joy",
    "Scene & Spark",
    "Calm & Color",
    "Drift & Wonder",
    "Grace & Motion",
    "Dream & Delight",
    "Bloom & Breeze",
    "Rhythm & Radiance",
    "Velvet & Verse",
    "Luster & Light",
    "Poise & Ease",
    "Aura & Echo",
    "Bliss & Bloom",
    "Shine & Spirit",
    "Muse & Melody",
    "Harmony & Hue",
    "Flair & Flow",
    "Pulse & Poetry",
    "Whisper & Warmth",
    "Leisure & Light",
    "Mellow & Motion",
    "Tender & Tone",
    "Petal & Peace",
    "Dazzle & Daydream",
    "Breezy & Bliss",
    "Wonder & Whimsy",
    "Satin & Stillness",
    "Sway & Sunlight",
    "Radiant & Reverie",
    "Gentle & Gleam",
    "Serene & Sparkle",
    "Color & Cadence",
    "Lively & Luster",
    "Daydream & Drift",
    "Softness & Shine",
    "Gleam & Grace",
    "Warmth & Wonder",
    "Melody & Mist",
    "Petals & Poetry",
    "Breeze & Balance",
    "Satin & Sparkle",
    "Ember & Ease",
    "Delight & Drift",
    "Lilt & Light",
    "Whimsy & Warmth",
    "Hush & Harmony",
    "Lucent & Leisure",
    "Poise & Petals",
]
CATEGORY_LABELS = {
    "Books": "图书 (Books)",
    "Business": "商务 (Business)",
    "Developer Tools": "开发者工具 (Developer Tools)",
    "Education": "教育 (Education)",
    "Entertainment": "娱乐 (Entertainment)",
    "Social Networking": "社交 (Social Networking)",
    "Food & Drink": "美食佳饮 (Food & Drink)",
    "Games": "游戏 (Games)",
    "Graphics & Design": "图形和设计 (Graphics & Design)",
    "Health & Fitness": "健康健美 (Health & Fitness)",
    "Lifestyle": "生活 (Lifestyle)",
    "Kids": "儿童 (Kids)",
    "Magazines & Newspapers": "报刊杂志 (Magazines & Newspapers)",
    "Medical": "医疗 (Medical)",
    "Music": "音乐 (Music)",
    "Navigation": "导航 (Navigation)",
    "News": "新闻 (News)",
    "Travel": "旅游 (Travel)",
    "Photo & Video": "摄影与录像 (Photo & Video)",
    "Finance": "财务 (Finance)",
    "Productivity": "效率 (Productivity)",
    "Reference": "参考 (Reference)",
    "Sports": "体育 (Sports)",
    "Utilities": "工具 (Utilities)",
    "Weather": "天气 (Weather)",
}
LISTING_URL_RE = re.compile(
    r"https://[^\s'\"<>()]+/(?:index\.html|PrivacyPolicy\.html|Terms&Conditions\.html|Support\.html)"
)
GENERIC_URL_RE = re.compile(r"https://[^\s'\"<>()]+")
TEXT_FILE_SUFFIXES = {".md", ".txt", ".html", ".dart", ".swift", ".yaml", ".yml"}
PROJECT_URL_SYNC_SUFFIXES = {".dart", ".swift", ".plist", ".xcconfig"}
SKIP_DIRS = {
    "pods",
    "package",
    "packages",
    ".dart_tool",
    "build",
    ".git",
    ".idea",
    ".vscode",
    ".topic-change",
    ".topic_change",
    ".reskin",
}
LISTING_PAGE_URL_KEYS = {
    "index.html": "index",
    "PrivacyPolicy.html": "privacy",
    "Terms&Conditions.html": "terms",
    "Support.html": "support",
}
LISTING_PAGE_NAMES_TO_SYNC = frozenset(LISTING_PAGE_URL_KEYS)
LEGAL_CONFIG_PATH_HINTS = (
    "privacy",
    "policy",
    "terms",
    "support",
    "legal",
    "agreement",
    "config",
    "const",
    "setting",
)
LEGAL_CONFIG_TEXT_HINTS = (
    "privacypolicy.html",
    "terms&conditions.html",
    "support.html",
    "terms of service",
    "privacy policy",
    "terms_url",
    "privacy_url",
    "support_url",
    "termsofservice",
    "privacyurl",
    "supporturl",
    "legalurl",
    "legalhost",
    "aboutdomain",
    "listingurl",
    "privacypath",
    "termspath",
    "supportpath",
)
LEGAL_HOST_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:listing|legal|privacy|terms|support|about)?(?:host|domain|baseurl|base_url|siteurl|site_url)\w*\b"
    r"\s*[:=]\s*['\"]([A-Za-z0-9.-]+\.[A-Za-z]{2,})['\"]"
)
QUOTED_HOST_LITERAL_RE = re.compile(r"['\"]([A-Za-z0-9.-]+\.[A-Za-z]{2,})['\"]")
SITE_HOST_HINT_KEYWORDS = {
    "/privacy": 18,
    "/terms": 18,
    "/support": 16,
    "/help": 14,
    "/contact": 12,
    "/about": 8,
    "/legal": 8,
}
SITE_HOST_NAME_BONUS = {
    ".app": 6,
    ".com": 3,
}
SITE_HOST_PENALTY_TOKENS = (
    "api.",
    "cdn.",
    "static.",
    "images.",
    "img.",
    "media.",
    "dashscope",
    "aliyuncs",
    "pexels",
    "unsplash",
)
DEFAULT_LISTING_HOST = "xxx.xxx.xxx"
SUBDOMAIN_QUERY_URL = "http://47.107.166.178:5030/api/sub-domain/query"
SUBDOMAIN_QUERY_KEY = "tyngab-5xyvVi-kogtes"
ABOUT_DEPLOYMENTS_URL = "http://192.168.20.188:4174/api/v1/about-deployments"
REQUIRED_LISTING_PAGE_NAMES = {
    "index.html",
    "PrivacyPolicy.html",
    "Terms&Conditions.html",
    "Support.html",
}
HOSTNAME_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
PLACEHOLDER_DOMAIN_LABELS = {
    "xxx",
    "example",
    "placeholder",
    "sample",
    "your-domain",
    "yourdomain",
    "changeme",
    "todo",
    "tbd",
}
NON_DEPLOYABLE_HOSTS = {
    DEFAULT_LISTING_HOST,
    "example.com",
    "example.org",
    "example.net",
    "localhost",
}
CURL_HTTP_STATUS_MARKER = "__CODEX_HTTP_STATUS__:"
AUTHORING_SITE_OVERVIEW_KEYS = (
    "brand_overview",
    "index_subtitle",
    "purpose",
    "members_intro",
)
AUTHORING_OPTIONAL_KEYS = {
    "description",
    "description_style_label",
    "subtitle",
    "keywords",
    "site_overview",
    "legal",
    "onboarding",
    *AUTHORING_SITE_OVERVIEW_KEYS,
}
NON_AI_COPY_PATTERNS = (
    ("AI Preview", re.compile(r"\bai preview\b", re.IGNORECASE)),
    ("AI-assisted", re.compile(r"\bai-assisted\b", re.IGNORECASE)),
    ("artificial intelligence", re.compile(r"\bartificial intelligence\b", re.IGNORECASE)),
    ("AI", re.compile(r"\bai\b", re.IGNORECASE)),
    ("assistant", re.compile(r"\bassistant\b", re.IGNORECASE)),
    ("inference", re.compile(r"\binference\b", re.IGNORECASE)),
)
STYLE_ROTATION_STATE_PATH = ROOT / ".description_style_rotation.json"
UMBRELLA_THEME_MARKERS = (
    "umbrella",
    "canopy",
    "rainy-day",
    "rainy day",
    "rain drop",
    "drizzle",
    "parasol",
)
WOMEN_COMMUNITY_MARKERS = (
    "women-led",
    "women led",
    "women's",
    "women",
    "womenscircle",
)
BUSINESS_EVIDENCE_MARKERS = (
    "invoice",
    "client",
    "crm",
    "sales",
    "merchant",
    "inventory",
    "staff",
    "operations",
    "lead",
    "order management",
)
EDUCATION_EVIDENCE_MARKERS = (
    "lesson",
    "course",
    "quiz",
    "flashcard",
    "practice test",
    "classroom",
    "teacher",
    "homework",
    "study plan",
    "learning path",
)
ENTERTAINMENT_EVIDENCE_MARKERS = (
    "streaming",
    "watch now",
    "episode",
    "movie",
    "tv show",
    "series",
    "trailer",
    "fan club",
    "live show",
    "entertainment",
)
GRAPHICS_DESIGN_EVIDENCE_MARKERS = (
    "graphic design",
    "template editor",
    "poster maker",
    "flyer maker",
    "logo maker",
    "vector",
    "typography",
    "layout",
    "palette",
    "mockup",
    "canvas",
)
HEALTH_FITNESS_EVIDENCE_MARKERS = (
    "workout",
    "fitness",
    "meditation",
    "sleep tracker",
    "calorie",
    "step counter",
    "wellness",
    "yoga",
    "hydration",
    "mindfulness",
)
LIFESTYLE_EVIDENCE_MARKERS = (
    "habit tracker",
    "daily routine",
    "journal",
    "self care",
    "home decor",
    "wardrobe",
    "outfit planner",
    "pet care",
    "wedding planner",
    "lifestyle",
)
MUSIC_EVIDENCE_MARKERS = (
    "playlist",
    "album",
    "karaoke",
    "podcast",
    "beat maker",
    "metronome",
    "piano",
    "guitar",
    "music player",
    "record audio",
)
PRODUCTIVITY_EVIDENCE_MARKERS = (
    "to-do",
    "todo",
    "task list",
    "calendar",
    "planner",
    "checklist",
    "reminder",
    "project board",
    "focus timer",
    "note taking",
    "workspace",
)
FOOD_DRINK_EVIDENCE_MARKERS = (
    "restaurant",
    "menu",
    "recipe",
    "reservation",
    "delivery",
    "dining",
    "cafe",
    "ingredients",
    "cookbook",
    "food order",
)
NAVIGATION_EVIDENCE_MARKERS = (
    "directions",
    "turn-by-turn",
    "turn by turn",
    "destination",
    "eta",
    "traffic",
    "route planner",
    "navigation",
    "start route",
    "arrive by",
)
NEWS_EVIDENCE_MARKERS = (
    "breaking news",
    "latest news",
    "headlines",
    "newsroom",
    "top stories",
    "world news",
    "local news",
    "publisher",
    "news alert",
    "article feed",
)
REFERENCE_EVIDENCE_MARKERS = (
    "dictionary",
    "encyclopedia",
    "glossary",
    "reference",
    "definitions",
    "lookup",
    "manual",
    "knowledge base",
    "reference guide",
    "term lookup",
)
SPORTS_EVIDENCE_MARKERS = (
    "scoreboard",
    "match center",
    "standings",
    "fixtures",
    "team roster",
    "league table",
    "athlete stats",
    "sports news",
    "live score",
    "match schedule",
)
WEATHER_EVIDENCE_MARKERS = (
    "forecast",
    "hourly weather",
    "weather radar",
    "storm alert",
    "precipitation",
    "air quality",
    "uv index",
    "temperature",
    "humidity",
    "severe weather",
)
EVIDENCE_ARCHETYPE_MARKERS = {
    "business_tools": BUSINESS_EVIDENCE_MARKERS,
    "education_learning": EDUCATION_EVIDENCE_MARKERS,
    "entertainment_media": ENTERTAINMENT_EVIDENCE_MARKERS,
    "food_drink": FOOD_DRINK_EVIDENCE_MARKERS,
    "graphics_design": GRAPHICS_DESIGN_EVIDENCE_MARKERS,
    "health_wellness": HEALTH_FITNESS_EVIDENCE_MARKERS,
    "lifestyle_service": LIFESTYLE_EVIDENCE_MARKERS,
    "music_audio": MUSIC_EVIDENCE_MARKERS,
    "navigation_guidance": NAVIGATION_EVIDENCE_MARKERS,
    "news_reader": NEWS_EVIDENCE_MARKERS,
    "productivity_workflow": PRODUCTIVITY_EVIDENCE_MARKERS,
    "reference_lookup": REFERENCE_EVIDENCE_MARKERS,
    "sports_activity": SPORTS_EVIDENCE_MARKERS,
    "weather_forecast": WEATHER_EVIDENCE_MARKERS,
}
EVIDENCE_ARCHETYPE_WEIGHTS = {
    "business_tools": 1.2,
    "education_learning": 1.35,
    "entertainment_media": 1.1,
    "food_drink": 1.15,
    "graphics_design": 1.15,
    "health_wellness": 1.15,
    "lifestyle_service": 1.0,
    "music_audio": 1.2,
    "navigation_guidance": 1.25,
    "news_reader": 1.1,
    "productivity_workflow": 1.15,
    "reference_lookup": 1.15,
    "sports_activity": 1.15,
    "weather_forecast": 1.2,
}
GENERIC_DESCRIPTION_OPENINGS = (
    "community-driven lifestyle app",
    "community lifestyle app",
    "community app",
)
THEME_ANCHOR_STOPWORDS = {
    "access",
    "account",
    "accounts",
    "activity",
    "activities",
    "app",
    "around",
    "built",
    "clear",
    "coins",
    "community",
    "credits",
    "designed",
    "discover",
    "discovery",
    "everyday",
    "experience",
    "gems",
    "goods",
    "lifestyle",
    "member",
    "members",
    "mobile",
    "optional",
    "people",
    "personal",
    "place",
    "places",
    "post",
    "posts",
    "profile",
    "profiles",
    "publish",
    "publishing",
    "purchase",
    "purchases",
    "return",
    "revisit",
    "share",
    "shared",
    "sharing",
    "social",
    "support",
    "updates",
    "virtual",
}


@dataclass(frozen=True)
class AppHint:
    identity: str
    experience: str
    keywords: list[str]
    currency: str | None
    index_title_suffix: str
    social_noun: str
    post_label: str


@dataclass(frozen=True)
class DescriptionBlock:
    kind: str
    role: str | None = None
    count: int = 0


@dataclass(frozen=True)
class DescriptionPlan:
    style: str
    blocks: tuple[DescriptionBlock, ...]


@dataclass(frozen=True)
class DescriptionContext:
    app_name: str
    category: str
    hint: AppHint
    active: set[str]
    has_iap: bool
    inspect_payload: dict[str, Any]
    has_ugc: bool
    has_chat: bool
    has_translation: bool
    ugc_chat_sentence: str
    theme_fragment: str
    theme_pair: str
    post_label_plural: str
    purchase_sentence: str
    style_specific_tail: str


@dataclass(frozen=True)
class AboutDeploymentOptions:
    enabled: bool = False
    sync_project_listing_urls: bool = True
    max_attempts: int = 1
    poll_interval_seconds: float = 2.0
    poll_timeout_seconds: float = 900.0
    http_timeout_seconds: float = 30.0
    publish_ready_delay_seconds: float = 0.0
    publish_probe_interval_seconds: float = 2.0
    publish_probe_timeout_seconds: float = 30.0


@dataclass(frozen=True)
class JSONHTTPResponse:
    status: int
    payload: dict[str, Any]


class DeploymentError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool, reason: str = "deployment_error") -> None:
        super().__init__(message)
        self.retryable = retryable
        self.reason = reason


STYLE_DESCRIPTION_PLANS = {
    "concise": DescriptionPlan(
        style="concise",
        blocks=(
            DescriptionBlock("sentence", "intro_concise"),
            DescriptionBlock("sentence", "return_flow_direct"),
            DescriptionBlock("sentence", "purchase_inline"),
        ),
    ),
    "feature_3": DescriptionPlan(
        style="feature_3",
        blocks=(
            DescriptionBlock("sentence", "intro_feature_scan"),
            DescriptionBlock("bullets", "feature", 3),
        ),
    ),
    "feature_4": DescriptionPlan(
        style="feature_4",
        blocks=(
            DescriptionBlock("sentence", "intro_feature_detail"),
            DescriptionBlock("bullets", "feature", 4),
        ),
    ),
    "feature_5": DescriptionPlan(
        style="feature_5",
        blocks=(
            DescriptionBlock("sentence", "intro_feature_expanded"),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "bridge_feature_expanded"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "with_you_can"),
            DescriptionBlock("bullets", "feature", 5),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_feature_expanded"),
        ),
    ),
    "benefit_3": DescriptionPlan(
        style="benefit_3",
        blocks=(
            DescriptionBlock("sentence", "intro_benefit"),
            DescriptionBlock("bullets", "benefit", 3),
        ),
    ),
    "benefit_4": DescriptionPlan(
        style="benefit_4",
        blocks=(
            DescriptionBlock("sentence", "intro_benefit_expanded"),
            DescriptionBlock("bullets", "benefit", 4),
        ),
    ),
    "summary_plus_feature_3": DescriptionPlan(
        style="summary_plus_feature_3",
        blocks=(
            DescriptionBlock("sentence", "intro_feature_detail"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "highlights"),
            DescriptionBlock("bullets", "feature", 3),
        ),
    ),
    "summary_plus_benefit_3": DescriptionPlan(
        style="summary_plus_benefit_3",
        blocks=(
            DescriptionBlock("sentence", "intro_benefit_expanded"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "why_people_return"),
            DescriptionBlock("bullets", "benefit", 3),
        ),
    ),
    "community_then_purchase": DescriptionPlan(
        style="community_then_purchase",
        blocks=(
            DescriptionBlock("sentence", "intro_members_first"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "inside_app"),
            DescriptionBlock("bullets", "community_purchase", 3),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_community_then_purchase"),
        ),
    ),
    "feature_then_value": DescriptionPlan(
        style="feature_then_value",
        blocks=(
            DescriptionBlock("sentence", "intro_you_can"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "with_you_can"),
            DescriptionBlock("bullets", "feature_then_value_feature", 2),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "why_it_feels_easy"),
            DescriptionBlock("bullets", "feature_then_value_benefit", 2),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_feature_then_value"),
        ),
    ),
    "you_can_3": DescriptionPlan(
        style="you_can_3",
        blocks=(
            DescriptionBlock("sentence", "intro_you_can"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "with_you_can"),
            DescriptionBlock("bullets", "feature", 3),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_you_can"),
        ),
    ),
    "you_can_4": DescriptionPlan(
        style="you_can_4",
        blocks=(
            DescriptionBlock("sentence", "intro_you_can"),
            DescriptionBlock("blank"),
            DescriptionBlock("heading", "with_you_can"),
            DescriptionBlock("bullets", "feature", 4),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_you_can"),
        ),
    ),
    "why_choose_3": DescriptionPlan(
        style="why_choose_3",
        blocks=(
            DescriptionBlock("sentence", "intro_why_choose"),
            DescriptionBlock("bullets", "benefit", 3),
        ),
    ),
    "homebase_4": DescriptionPlan(
        style="homebase_4",
        blocks=(
            DescriptionBlock("sentence", "intro_homebase"),
            DescriptionBlock("bullets", "feature", 4),
        ),
    ),
    "all_in_one": DescriptionPlan(
        style="all_in_one",
        blocks=(
            DescriptionBlock("sentence", "intro_all_in_one"),
            DescriptionBlock("sentence", "bridge_all_in_one"),
            DescriptionBlock("sentence", "closing_all_in_one"),
        ),
    ),
    "members_first": DescriptionPlan(
        style="members_first",
        blocks=(
            DescriptionBlock("sentence", "intro_members_first"),
            DescriptionBlock("sentence", "bridge_members_first"),
            DescriptionBlock("sentence", "closing_members_first"),
        ),
    ),
    "everyday_use": DescriptionPlan(
        style="everyday_use",
        blocks=(
            DescriptionBlock("sentence", "intro_everyday_use"),
            DescriptionBlock("sentence", "bridge_everyday_use"),
            DescriptionBlock("sentence", "closing_everyday_use"),
        ),
    ),
    "longform": DescriptionPlan(
        style="longform",
        blocks=(
            DescriptionBlock("sentence", "intro_longform"),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "bridge_longform"),
            DescriptionBlock("sentence", "tail_longform"),
            DescriptionBlock("blank"),
            DescriptionBlock("sentence", "closing_longform"),
        ),
    ),
}


APP_HINTS: dict[str, AppHint] = {
    "breezi": AppHint(
        identity="a hair care community",
        experience="conditioner routines, ingredient reading, translation tools, and everyday care inspiration",
        keywords=["hair care", "conditioner routines", "ingredient labels", "care notes", "routine cards", "credits"],
        currency="credits",
        index_title_suffix="Hair Care Community",
        social_noun="wash-day routines, product discoveries, and hair care notes",
        post_label="hair care post",
    ),
    "rivano": AppHint(
        identity="a style-sharing community",
        experience="style sharing, AI look previews, and personal style updates",
        keywords=["style feed", "ai preview", "lookbook", "profiles", "credits"],
        currency="credits",
        index_title_suffix="Style Community",
        social_noun="style looks",
        post_label="style post",
    ),
    "daxori": AppHint(
        identity="an eyewear style community",
        experience="frame inspiration, glasses styling, and visual self-expression",
        keywords=["eyewear", "glasses", "frame style", "style feed", "lookbook", "profile"],
        currency="credits",
        index_title_suffix="Style Community",
        social_noun="frame looks",
        post_label="look post",
    ),
    "glavor": AppHint(
        identity="a curated headwear community",
        experience="hat inspiration, editorial sharing, and personal style notes",
        keywords=["headwear", "hat style", "beret", "look notes", "credits"],
        currency="credits",
        index_title_suffix="Headwear Community",
        social_noun="hat looks",
        post_label="look note",
    ),
    "pavric": AppHint(
        identity="a jewelry and styling community",
        experience="daily accessories, polished details, and personal style sharing",
        keywords=["jewelry", "ring style", "style feed", "look diary", "profile", "coins"],
        currency="coins",
        index_title_suffix="Jewelry Community",
        social_noun="jewelry looks",
        post_label="style post",
    ),
    "peldor": AppHint(
        identity="a mirror beauty journal with travel-ready translation tools",
        experience="beauty routines, translated notes, and place-aware sharing",
        keywords=["beauty journal", "mirror notes", "translation", "voice translate", "travel", "gems"],
        currency="gems",
        index_title_suffix="Beauty Travel Journal",
        social_noun="mirror notes",
        post_label="mirror note",
    ),
    "wexen": AppHint(
        identity="a women's necklace community",
        experience="necklace styling, gallery posts, short clips, profile sharing, and translation support",
        keywords=["necklace style", "jewelry posts", "styling clips", "profiles", "translation", "gems"],
        currency="gems",
        index_title_suffix="Necklace Community",
        social_noun="necklace looks, styling clips, and jewelry posts",
        post_label="necklace post",
    ),
    "quorix": AppHint(
        identity="a travel-aware beauty and style companion",
        experience="location-tagged look cards, translated notes, and polished community sharing",
        keywords=["travel style", "look cards", "translation", "beauty spots", "community", "voice tools"],
        currency=None,
        index_title_suffix="Travel Companion",
        social_noun="look cards",
        post_label="look card",
    ),
}

ARCHETYPE_LABELS = {
    "books_reader": "Books Reader",
    "business_tools": "Business Tools",
    "community_social": "Community Social Network",
    "developer_tools": "Developer Tools",
    "education_learning": "Education Learning",
    "entertainment_media": "Entertainment Media",
    "travel_companion": "Travel Companion",
    "food_drink": "Food & Drink",
    "games_play": "Games Experience",
    "graphics_design": "Graphics & Design",
    "health_wellness": "Health & Wellness",
    "kids_family": "Kids Experience",
    "lifestyle_service": "Lifestyle Service",
    "magazines_newsstand": "Magazines & Newspapers",
    "medical_reference": "Medical Reference",
    "music_audio": "Music & Audio",
    "navigation_guidance": "Navigation Guidance",
    "news_reader": "News Reader",
    "photo_media": "Photo-Led Experience",
    "finance_utility": "Finance Utility",
    "productivity_workflow": "Productivity Workflow",
    "reference_lookup": "Reference Lookup",
    "sports_activity": "Sports Activity",
    "weather_forecast": "Weather Forecast",
    "general_utility": "General Utility",
}
ARCHETYPE_CATEGORY_MAP = {
    "books_reader": "Books",
    "business_tools": "Business",
    "community_social": "Social Networking",
    "developer_tools": "Developer Tools",
    "education_learning": "Education",
    "entertainment_media": "Entertainment",
    "travel_companion": "Travel",
    "food_drink": "Food & Drink",
    "games_play": "Games",
    "graphics_design": "Graphics & Design",
    "health_wellness": "Health & Fitness",
    "kids_family": "Kids",
    "lifestyle_service": "Lifestyle",
    "magazines_newsstand": "Magazines & Newspapers",
    "medical_reference": "Medical",
    "music_audio": "Music",
    "navigation_guidance": "Navigation",
    "news_reader": "News",
    "photo_media": "Photo & Video",
    "finance_utility": "Finance",
    "productivity_workflow": "Productivity",
    "reference_lookup": "Reference",
    "sports_activity": "Sports",
    "weather_forecast": "Weather",
    "general_utility": "Utilities",
}
ARCHETYPE_PRIORITY = [
    "community_social",
    "travel_companion",
    "photo_media",
    "music_audio",
    "graphics_design",
    "education_learning",
    "health_wellness",
    "business_tools",
    "productivity_workflow",
    "entertainment_media",
    "lifestyle_service",
    "finance_utility",
    "books_reader",
    "developer_tools",
    "food_drink",
    "games_play",
    "kids_family",
    "magazines_newsstand",
    "medical_reference",
    "navigation_guidance",
    "news_reader",
    "reference_lookup",
    "sports_activity",
    "weather_forecast",
    "general_utility",
]
CATEGORY_ARCHETYPE_MAP = {
    "Books": "books_reader",
    "Business": "business_tools",
    "Developer Tools": "developer_tools",
    "Education": "education_learning",
    "Entertainment": "entertainment_media",
    "Food & Drink": "food_drink",
    "Games": "games_play",
    "Graphics & Design": "graphics_design",
    "Health & Fitness": "health_wellness",
    "Kids": "kids_family",
    "Lifestyle": "lifestyle_service",
    "Magazines & Newspapers": "magazines_newsstand",
    "Medical": "medical_reference",
    "Music": "music_audio",
    "Navigation": "navigation_guidance",
    "News": "news_reader",
    "Productivity": "productivity_workflow",
    "Reference": "reference_lookup",
    "Social Networking": "community_social",
    "Sports": "sports_activity",
    "Travel": "travel_companion",
    "Photo & Video": "photo_media",
    "Finance": "finance_utility",
    "Utilities": "general_utility",
    "Weather": "weather_forecast",
}
ARCHETYPE_CAPABILITY_WEIGHTS = {
    "books_reader": {},
    "business_tools": {
        "budgeting": 0.45,
        "messaging": 0.15,
        "profile": 0.15,
    },
    "community_social": {
        "feed": 1.35,
        "profile": 1.1,
        "post_creation": 1.1,
        "messaging": 0.95,
        "recharge": 0.2,
    },
    "developer_tools": {},
    "education_learning": {
        "education": 1.35,
    },
    "entertainment_media": {},
    "travel_companion": {
        "translate_text": 1.15,
        "translate_voice": 1.0,
        "location": 1.0,
        "feed": 0.15,
        "profile": 0.1,
        "post_creation": 0.1,
    },
    "food_drink": {},
    "games_play": {},
    "graphics_design": {
        "beauty_editing": 0.55,
        "ai_image_generation": 0.45,
    },
    "health_wellness": {},
    "kids_family": {},
    "lifestyle_service": {
        "feed": 0.1,
        "profile": 0.1,
    },
    "magazines_newsstand": {},
    "medical_reference": {},
    "music_audio": {},
    "navigation_guidance": {
        "location": 0.8,
    },
    "news_reader": {},
    "photo_media": {
        "beauty_editing": 1.2,
        "ai_image_generation": 1.2,
        "post_creation": 0.35,
        "feed": 0.1,
    },
    "finance_utility": {
        "budgeting": 1.2,
        "recharge": 1.0,
    },
    "productivity_workflow": {
        "messaging": 0.1,
        "profile": 0.15,
    },
    "reference_lookup": {},
    "sports_activity": {},
    "weather_forecast": {
        "location": 0.35,
    },
    "general_utility": {},
}


def run_json_script(script_name: str, *args: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name), *args],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def run_script(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name), *args],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )


def parse_validator_warnings(result: subprocess.CompletedProcess[str]) -> list[str]:
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []
    warnings = payload.get("warnings", [])
    if not isinstance(warnings, list):
        return []
    return [str(item).strip() for item in warnings if str(item).strip()]


def active_capabilities(inspect_payload: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for name, payload in inspect_payload.get("capability_candidates", {}).items():
        if float(payload.get("score", 0.0)) >= 1.0:
            result.add(name)
    translation_signals = inspect_payload.get("translation_signals", {})
    if isinstance(translation_signals, dict) and not translation_signals.get(
        "disclosure_required",
        translation_signals.get("user_reachable", True),
    ):
        result.discard("translate_text")
        result.discard("translate_voice")
    ai_signals = inspect_payload.get("ai_signals", {})
    if isinstance(ai_signals, dict) and not ai_signals.get(
        "disclosure_required",
        ai_signals.get("user_reachable", True),
    ):
        result.discard("ai_chat")
        result.discard("ai_image_generation")
    messaging_signals = inspect_payload.get("messaging_signals", {})
    if isinstance(messaging_signals, dict) and not messaging_signals.get(
        "real_user_chat",
        messaging_signals.get("user_reachable", True),
    ):
        result.discard("messaging")
    beauty_editing_signals = inspect_payload.get("beauty_editing_signals", {})
    if isinstance(beauty_editing_signals, dict) and not beauty_editing_signals.get(
        "disclosure_required",
        beauty_editing_signals.get("user_reachable", True),
    ):
        result.discard("beauty_editing")
    ai_signals = inspect_payload.get("ai_signals", {})
    if isinstance(ai_signals, dict) and ai_signals.get(
        "disclosure_required",
        ai_signals.get("user_reachable", False),
    ):
        if "beauty_editing" in result:
            result.add("ai_image_generation")
    return result


def has_ugc_capability(active: set[str]) -> bool:
    return bool({"feed", "post_creation"} & active)


def has_ugc_capability_for_payload(active: set[str], inspect_payload: dict[str, Any]) -> bool:
    """Use explicit community evidence without treating private profiles as UGC."""
    if has_ugc_capability(active):
        return True
    privacy = inspect_payload.get("privacy_signals", {})
    if isinstance(privacy, dict) and isinstance(privacy.get("community_ugc"), bool):
        return privacy["community_ugc"]
    if isinstance(privacy, dict) and privacy.get("user_content") is True:
        candidates = inspect_payload.get("capability_candidates", {})
        if isinstance(candidates, dict) and any(name in candidates for name in ("feed", "post_creation", "messaging")):
            return False
        return True
    return False


def has_chat_capability(active: set[str], inspect_payload: dict[str, Any] | None = None) -> bool:
    messaging_signals = (inspect_payload or {}).get("messaging_signals", {})
    if isinstance(messaging_signals, dict) and "real_user_chat" in messaging_signals:
        return bool(messaging_signals.get("real_user_chat"))
    return "messaging" in active


def has_community_ugc_surface(active: set[str], inspect_payload: dict[str, Any] | None = None) -> bool:
    privacy = (inspect_payload or {}).get("privacy_signals", {})
    if isinstance(privacy, dict) and isinstance(privacy.get("community_ugc"), bool):
        return privacy["community_ugc"]
    if isinstance(privacy, dict) and privacy.get("user_content") and not ("messaging" in active and not ({"feed", "post_creation"} & active)):
        return True
    return bool({"feed", "post_creation"} & active)


def has_profile_capability(active: set[str]) -> bool:
    return "profile" in active


def has_publish_capability(active: set[str]) -> bool:
    return "post_creation" in active


def has_credential_account_access(inspect_payload: dict[str, Any] | None = None) -> bool:
    return inspect_has_credential_account((inspect_payload or {}))


def access_mode(inspect_payload: dict[str, Any] | None = None) -> str:
    return inspect_access_mode((inspect_payload or {}))


def has_local_session_access(inspect_payload: dict[str, Any] | None = None) -> bool:
    return inspect_has_local_session((inspect_payload or {}))


def build_product_facts(inspect_payload: dict[str, Any], active: set[str]) -> dict[str, Any]:
    return normalize_product_facts(inspect_payload, active)


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def build_keywords(
    hint: AppHint,
    active: set[str],
    inspect_payload: dict[str, Any] | None = None,
) -> list[str]:
    has_chat = has_chat_capability(active, inspect_payload)
    filtered: list[str] = []
    for keyword in hint.keywords:
        lowered = keyword.lower()
        if any(token in lowered for token in ("chat", "message", "inbox", "conversation")) and not has_chat:
            continue
        filtered.append(keyword)
    if has_chat and not any(
        any(token in keyword.lower() for token in ("chat", "message", "inbox", "conversation"))
        for keyword in filtered
    ):
        filtered.append("direct messages")
    limited: list[str] = []
    total_length = 0
    for keyword in filtered:
        projected = total_length + len(keyword) + (1 if limited else 0)
        if projected > 100:
            continue
        limited.append(keyword)
        total_length = projected
    return limited or filtered[:1]


def capability_score_map(inspect_payload: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for name, payload in inspect_payload.get("capability_candidates", {}).items():
        if not isinstance(payload, dict):
            continue
        scores[name] = float(payload.get("score", 0.0))
    return scores


def evidence_archetype_scores(inspect_payload: dict[str, Any], active: set[str]) -> dict[str, float]:
    blob = inspect_evidence_blob(inspect_payload)
    scores: dict[str, float] = {}
    for archetype, markers in EVIDENCE_ARCHETYPE_MARKERS.items():
        weight = EVIDENCE_ARCHETYPE_WEIGHTS.get(archetype, 1.0)
        scores[archetype] = keyword_blob_score(blob, markers) * weight

    if "education" in active:
        scores["education_learning"] = scores.get("education_learning", 0.0) + 3.0
    if "budgeting" in active:
        scores["business_tools"] = scores.get("business_tools", 0.0) + 0.75
    if {"beauty_editing", "ai_image_generation"} & active:
        scores["graphics_design"] = scores.get("graphics_design", 0.0) + 0.6
    if "location" in active and scores.get("weather_forecast", 0.0) > 0:
        scores["weather_forecast"] = scores.get("weather_forecast", 0.0) + 0.75
    if "location" in active and scores.get("navigation_guidance", 0.0) > 0:
        scores["navigation_guidance"] = scores.get("navigation_guidance", 0.0) + 0.9
    if scores.get("sports_activity", 0.0) > 0 and "fitness" in blob:
        scores["sports_activity"] = scores.get("sports_activity", 0.0) + 0.35
    if scores.get("news_reader", 0.0) > 0 and "article" in blob:
        scores["news_reader"] = scores.get("news_reader", 0.0) + 0.3
    return scores


def score_archetypes(inspect_payload: dict[str, Any], active: set[str]) -> dict[str, float]:
    capability_scores = capability_score_map(inspect_payload)
    scores: dict[str, float] = {}
    for archetype, weights in ARCHETYPE_CAPABILITY_WEIGHTS.items():
        total = 0.0
        for capability, weight in weights.items():
            total += capability_scores.get(capability, 0.0) * weight
        if archetype == "community_social" and has_ugc_capability(active):
            total += 3.0
        if archetype == "travel_companion" and "location" in active and ({"translate_text", "translate_voice"} & active):
            total += 1.0
        if archetype == "photo_media" and {"beauty_editing", "ai_image_generation"} & active:
            total += 1.0
        if archetype == "finance_utility" and "recharge" in active:
            total += 0.5
        scores[archetype] = total

    for archetype, boost in evidence_archetype_scores(inspect_payload, active).items():
        scores[archetype] = scores.get(archetype, 0.0) + boost

    for archetype in list(scores.keys()):
        scores[archetype] = round(scores[archetype], 2)
    if not any(score > 0 for score in scores.values()):
        scores["general_utility"] = 0.1
    return scores


def pick_primary_archetype(archetype_scores: dict[str, float]) -> str:
    ranked = sorted(
        ARCHETYPE_PRIORITY,
        key=lambda name: (-archetype_scores.get(name, 0.0), ARCHETYPE_PRIORITY.index(name)),
    )
    return ranked[0]


def pick_category(archetype: str) -> str:
    return ARCHETYPE_CATEGORY_MAP.get(archetype, "Utilities")


def preferred_capabilities(active: set[str], category: str) -> list[str]:
    if category == "Travel":
        ordered = [
            "feed",
            "profile",
            "post_creation",
            "translate_text",
            "translate_voice",
            "location",
            "recharge",
            "beauty_editing",
            "messaging",
            "ai_chat",
            "ai_image_generation",
        ]
    elif category == "Education":
        ordered = [
            "education",
            "profile",
            "messaging",
            "recharge",
            "translate_text",
            "translate_voice",
            "location",
            "beauty_editing",
            "ai_chat",
            "ai_image_generation",
            "feed",
            "post_creation",
        ]
    elif category in {"Business", "Productivity"}:
        ordered = [
            "budgeting",
            "recharge",
            "profile",
            "messaging",
            "feed",
            "post_creation",
            "translate_text",
            "translate_voice",
            "location",
            "beauty_editing",
            "ai_chat",
            "ai_image_generation",
            "education",
        ]
    elif category in {"Navigation", "Weather"}:
        ordered = [
            "location",
            "translate_text",
            "translate_voice",
            "profile",
            "feed",
            "post_creation",
            "messaging",
            "recharge",
            "beauty_editing",
            "ai_chat",
            "ai_image_generation",
            "education",
            "budgeting",
        ]
    elif category in {"Reference", "Food & Drink", "Sports", "News"}:
        ordered = [
            "feed",
            "profile",
            "location",
            "post_creation",
            "messaging",
            "recharge",
            "translate_text",
            "translate_voice",
            "beauty_editing",
            "ai_chat",
            "ai_image_generation",
            "education",
            "budgeting",
        ]
    else:
        ordered = [
            "feed",
            "profile",
            "post_creation",
            "messaging",
            "recharge",
            "translate_text",
            "translate_voice",
            "location",
            "beauty_editing",
            "ai_chat",
            "ai_image_generation",
            "education",
            "budgeting",
        ]
    return [name for name in ordered if name in active]


def choose_subtitle(state_path: Path | None = None) -> str:
    state = load_style_rotation_state(state_path)
    subtitle_state = state.setdefault("subtitle", {})
    cursor_value = subtitle_state.get("cursor", 0)
    cursor = int(cursor_value) if isinstance(cursor_value, int) else 0
    subtitle = SUBTITLE_POOL[cursor % len(SUBTITLE_POOL)]
    subtitle_state["cursor"] = cursor + 1
    save_style_rotation_state(state, state_path)
    return subtitle


def choose_style(slug: str, override: str | None) -> str:
    del slug
    if override:
        if override not in DESCRIPTION_STYLES:
            raise ValueError(f"unsupported_description_style:{override}")
        return override
    rng = random.SystemRandom()
    return rng.choice(DESCRIPTION_STYLES)


def empty_style_rotation_state() -> dict[str, Any]:
    return {"pools": {}, "apps": {}, "subtitle": {"cursor": 0}}


def load_style_rotation_state(state_path: Path | None = None) -> dict[str, Any]:
    path = state_path or STYLE_ROTATION_STATE_PATH
    if not path.exists():
        return empty_style_rotation_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_style_rotation_state()
    if not isinstance(payload, dict):
        return empty_style_rotation_state()
    pools = payload.get("pools")
    apps = payload.get("apps")
    subtitle = payload.get("subtitle")
    return {
        "pools": dict(pools) if isinstance(pools, dict) else {},
        "apps": dict(apps) if isinstance(apps, dict) else {},
        "subtitle": dict(subtitle) if isinstance(subtitle, dict) else {"cursor": 0},
    }


def save_style_rotation_state(state: dict[str, Any], state_path: Path | None = None) -> None:
    path = state_path or STYLE_ROTATION_STATE_PATH
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_style_pool(styles: list[str]) -> list[str]:
    normalized: list[str] = []
    for style in styles:
        if style not in DESCRIPTION_STYLES:
            continue
        if style in normalized:
            continue
        normalized.append(style)
    if not normalized:
        return ["all_in_one"]
    return normalized


def description_style_pool(
    category: str,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any],
) -> tuple[str, list[str]]:
    has_ugc = has_ugc_capability(active)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    preview_profile = ai_preview_profile(inspect_payload)
    capability_count = len(active)

    if preview_profile.get("needs_face_data_clauses"):
        return ("ai_preview_high_risk", ["feature_4", "feature_5"])
    if category == "Travel" or has_translation:
        return ("travel_translation", ["benefit_3", "benefit_4", "you_can_3"])
    if category == "Finance":
        return ("finance_consumer", ["concise", "summary_plus_benefit_3", "benefit_3", "feature_3"])
    if category == "Education":
        return ("education_learning", ["summary_plus_feature_3", "you_can_3", "benefit_3", "feature_3"])
    if category == "Productivity":
        return ("productivity_workflow", ["concise", "summary_plus_feature_3", "you_can_3", "feature_3"])
    if category == "Business":
        return ("business_tools", ["feature_3", "summary_plus_benefit_3", "benefit_3", "concise"])
    if category == "Graphics & Design":
        return ("graphics_design", ["feature_4", "feature_then_value", "all_in_one", "benefit_3"])
    if category == "Health & Fitness":
        return ("health_wellness", ["benefit_3", "summary_plus_benefit_3", "everyday_use", "you_can_3"])
    if category == "Lifestyle":
        return ("lifestyle_service", ["all_in_one", "summary_plus_benefit_3", "everyday_use", "benefit_3"])
    if category == "Music":
        return ("music_audio", ["all_in_one", "summary_plus_benefit_3", "benefit_3", "feature_3"])
    if category == "Entertainment":
        return ("entertainment_media", ["all_in_one", "longform", "feature_then_value", "everyday_use"])
    if category == "Food & Drink":
        return ("food_drink", ["summary_plus_benefit_3", "benefit_3", "you_can_3", "everyday_use"])
    if category == "Navigation":
        return ("navigation_guidance", ["concise", "summary_plus_feature_3", "you_can_3", "benefit_3"])
    if category == "News":
        return ("news_reader", ["concise", "longform", "summary_plus_benefit_3", "benefit_3"])
    if category == "Reference":
        return ("reference_lookup", ["concise", "summary_plus_feature_3", "you_can_3", "feature_3"])
    if category == "Sports":
        return ("sports_activity", ["feature_3", "summary_plus_benefit_3", "benefit_3", "everyday_use"])
    if category == "Weather":
        return ("weather_forecast", ["concise", "everyday_use", "benefit_3"])
    if has_ugc and has_chat and has_iap:
        return ("community_chat_iap", ["feature_4", "community_then_purchase", "feature_then_value", "longform"])
    if has_ugc and has_chat:
        return ("community_chat", ["members_first", "summary_plus_feature_3", "feature_then_value", "longform"])
    if has_ugc and has_iap:
        return ("community_iap", ["members_first", "summary_plus_feature_3", "feature_4", "community_then_purchase", "longform"])
    if has_ugc:
        return ("community", ["members_first", "summary_plus_feature_3", "feature_4", "everyday_use"])
    if category == "Photo & Video" and has_iap:
        return ("photo_video_iap", ["feature_4", "feature_then_value", "feature_5", "all_in_one"])
    if category == "Photo & Video":
        return ("photo_video", ["feature_4", "feature_then_value", "all_in_one", "longform"])
    if category == "Utilities" and capability_count <= 2 and not has_iap:
        return ("utilities_light", ["concise", "everyday_use", "benefit_3"])
    if category == "Utilities":
        return ("utilities_feature", ["feature_3", "summary_plus_feature_3", "concise", "you_can_3"])
    if has_iap and capability_count >= 4:
        return ("feature_rich_iap", ["feature_4", "feature_then_value", "feature_5", "benefit_4"])
    if capability_count <= 2 and not has_iap and not has_chat:
        return ("lightweight_general", ["concise", "everyday_use", "benefit_3"])
    if capability_count >= 4:
        return ("feature_rich_general", ["feature_4", "feature_then_value", "you_can_4", "all_in_one"])
    return ("general_consumer", ["all_in_one", "summary_plus_benefit_3", "everyday_use", "benefit_3"])


def assign_description_style(
    target: Path,
    *,
    category: str,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any],
    override: str | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    pool_id, pool_styles = description_style_pool(category, active, has_iap, inspect_payload)
    normalized_pool = normalize_style_pool(pool_styles)

    if override:
        return {
            "style": choose_style(target.name, override),
            "pool_id": pool_id,
            "style_pool": normalized_pool,
            "assignment_source": "override",
            "reused_assignment": False,
        }

    state = load_style_rotation_state(state_path)
    pools = state.setdefault("pools", {})
    state.setdefault("apps", {})

    pool_state = pools.get(pool_id)
    if not isinstance(pool_state, dict):
        pool_state = {}
        pools[pool_id] = pool_state
    cursor_value = pool_state.get("cursor", 0)
    cursor = int(cursor_value) if isinstance(cursor_value, int) else 0
    style = normalized_pool[cursor % len(normalized_pool)]
    pool_state["cursor"] = cursor + 1
    save_style_rotation_state(state, state_path)

    return {
        "style": style,
        "pool_id": pool_id,
        "style_pool": normalized_pool,
        "assignment_source": "pool_rotation",
        "reused_assignment": False,
    }


def collect_inspect_evidence_values(inspect_payload: dict[str, Any]) -> list[str]:
    evidence = inspect_payload.get("evidence", {})
    values: list[str] = []
    if isinstance(evidence, dict):
        for key in ("screens", "routes", "actions", "ui_strings"):
            raw = evidence.get(key, [])
            if not isinstance(raw, list):
                continue
            values.extend(str(item).strip() for item in raw if str(item).strip())
    values.extend(str(item).strip() for item in inspect_payload.get("dependencies", []) if str(item).strip())
    return values


def inspect_evidence_blob(inspect_payload: dict[str, Any]) -> str:
    return "\n".join(value.lower() for value in collect_inspect_evidence_values(inspect_payload))


def keyword_blob_score(blob: str, keywords: tuple[str, ...]) -> int:
    return sum(blob.count(keyword) for keyword in keywords)


def infer_currency_label(inspect_payload: dict[str, Any], fallback: str | None) -> str | None:
    if not inspect_payload.get("privacy_signals", {}).get("payments"):
        return None

    blob = inspect_evidence_blob(inspect_payload)
    if "drop wallet" in blob or " drops" in blob or "drop pack" in blob:
        return "drops"
    if " gems" in blob or "gem pack" in blob:
        return "gems"
    if " coins" in blob or "coin pack" in blob:
        return "coins"
    return fallback or "credits"


def infer_domain_hint_from_inspect(archetype: str, inspect_payload: dict[str, Any]) -> AppHint | None:
    blob = inspect_evidence_blob(inspect_payload)
    umbrella_score = keyword_blob_score(blob, UMBRELLA_THEME_MARKERS)
    women_score = keyword_blob_score(blob, WOMEN_COMMUNITY_MARKERS)
    ai_preview_active = bool(
        inspect_payload.get("ai_signals", {}).get(
            "disclosure_required",
            inspect_payload.get("ai_signals", {}).get(
                "user_reachable",
                inspect_payload.get("ai_signals", {}).get("active"),
            ),
        )
    )

    if archetype in {"community_social", "photo_media"} and umbrella_score >= 5:
        keywords = [
            "umbrella style",
            "rainy-day posts",
            "umbrella community",
            "profile sharing",
        ]
        if women_score:
            keywords.insert(2, "women umbrella community")
        if ai_preview_active:
            keywords.insert(3, "umbrella preview")
        return AppHint(
            identity="a women-led umbrella community" if women_score else "an umbrella community",
            experience=(
                "umbrella looks, rainy-day posts, personal profiles, and AI umbrella previews"
                if ai_preview_active
                else "umbrella looks, rainy-day posts, and personal profiles"
            ),
            keywords=unique_preserve_order(keywords),
            currency=infer_currency_label(inspect_payload, "credits"),
            index_title_suffix="Umbrella Community",
            social_noun="umbrella looks and rainy-day posts",
            post_label="umbrella post",
        )
    return None


def theme_first_product_phrase(hint: AppHint) -> str | None:
    identity_blob = " ".join([hint.identity, hint.experience, hint.social_noun, hint.post_label]).lower()
    if "umbrella" not in identity_blob:
        return None
    if not any(token in identity_blob for token in ("rainy-day", "rainy day", "rain", "drizzle", "canopy")):
        return None
    if any(token in identity_blob for token in WOMEN_COMMUNITY_MARKERS):
        return "a social platform for women's umbrella styling and rainy-day looks"
    return "a social platform for umbrella styling and rainy-day looks"


def overview_identity_phrase(hint: AppHint) -> str:
    return theme_first_product_phrase(hint) or hint.identity


def extract_first_sentence(text: str) -> str:
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line:
            continue
        match = re.match(r"^(.+?[.!?])(?:\s|$)", line)
        return match.group(1).strip() if match else line
    return ""


def theme_anchor_words_from_hint(hint: AppHint) -> list[str]:
    raw = " ".join(
        [
            hint.identity,
            hint.experience,
            hint.social_noun,
            hint.post_label,
            *hint.keywords,
        ]
    ).lower()
    anchors: list[str] = []
    for word in re.findall(r"[a-z]{4,}", raw):
        if word in THEME_ANCHOR_STOPWORDS:
            continue
        if word in anchors:
            continue
        anchors.append(word)
    return anchors


def validate_description_theme_opening(description: str, hint: AppHint) -> list[str]:
    first_sentence = extract_first_sentence(description)
    if not first_sentence:
        return ["Description first sentence must not be empty."]

    lowered = first_sentence.lower()
    errors: list[str] = []
    if any(phrase in lowered for phrase in GENERIC_DESCRIPTION_OPENINGS):
        errors.append("Description first sentence is too generic and should state the app's concrete theme.")

    anchors = theme_anchor_words_from_hint(hint)
    if anchors and not any(re.search(rf"\b{re.escape(anchor)}\b", lowered) for anchor in anchors[:10]):
        errors.append("Description first sentence should include a concrete theme term supported by the app evidence.")
    return errors


def fallback_hint_for_archetype(archetype: str, inspect_payload: dict[str, Any]) -> AppHint:
    inferred = infer_domain_hint_from_inspect(archetype, inspect_payload)
    if inferred is not None:
        return inferred

    has_payments = bool(inspect_payload.get("privacy_signals", {}).get("payments"))
    currency = infer_currency_label(inspect_payload, "credits") if has_payments else None
    if archetype == "books_reader":
        return AppHint(
            identity="a book-focused reading experience",
            experience="title browsing, saved reading moments, and clear library access",
            keywords=["books", "reading", "library", "saved titles", "support", "discover"],
            currency=currency,
            index_title_suffix="Books Experience",
            social_noun="reading updates",
            post_label="reading update",
        )
    if archetype == "business_tools":
        return AppHint(
            identity="a business workflow tool",
            experience="client-facing tasks, operations support, and organized work access",
            keywords=["business", "workflow", "clients", "operations", "support", "dashboard"],
            currency=currency,
            index_title_suffix="Business Tools",
            social_noun="work updates",
            post_label="work update",
        )
    if archetype == "developer_tools":
        return AppHint(
            identity="a developer workflow utility",
            experience="project access, build-facing tasks, and release support",
            keywords=["developer", "projects", "builds", "workflow", "support", "access"],
            currency=currency,
            index_title_suffix="Developer Tools",
            social_noun="project updates",
            post_label="project update",
        )
    if archetype == "education_learning":
        return AppHint(
            identity="an interactive learning experience",
            experience="lessons, guided practice, and structured progress",
            keywords=["learning", "lessons", "practice", "study", "support", "progress"],
            currency=currency,
            index_title_suffix="Learning Experience",
            social_noun="learning updates",
            post_label="lesson update",
        )
    if archetype == "entertainment_media":
        return AppHint(
            identity="an entertainment-focused media experience",
            experience="episodes, media browsing, and easy return visits",
            keywords=["entertainment", "media", "episodes", "watchlist", "support", "discover"],
            currency=currency,
            index_title_suffix="Entertainment Hub",
            social_noun="media updates",
            post_label="media update",
        )
    if archetype == "travel_companion":
        return AppHint(
            identity="a place-aware travel companion",
            experience="translated notes, nearby context, and everyday sharing",
            keywords=["travel", "translation", "nearby", "sharing", "support", "discover"],
            currency=currency,
            index_title_suffix="Travel Companion",
            social_noun="travel updates",
            post_label="travel post",
        )
    if archetype == "food_drink":
        return AppHint(
            identity="a food and drink discovery experience",
            experience="menus, recommendations, and easy place browsing",
            keywords=["food", "drink", "menus", "recommendations", "support", "discover"],
            currency=currency,
            index_title_suffix="Food & Drink Guide",
            social_noun="menu updates",
            post_label="menu update",
        )
    if archetype == "games_play":
        return AppHint(
            identity="a game-focused entertainment experience",
            experience="sessions, progression, and player-facing updates",
            keywords=["games", "play", "sessions", "progress", "support", "discover"],
            currency=currency,
            index_title_suffix="Games Experience",
            social_noun="player updates",
            post_label="player update",
        )
    if archetype == "graphics_design":
        return AppHint(
            identity="a graphics and design creation experience",
            experience="templates, visual editing, and polished creative output",
            keywords=["design", "graphics", "templates", "visual editing", "support", "create"],
            currency=currency,
            index_title_suffix="Design Studio",
            social_noun="design updates",
            post_label="design update",
        )
    if archetype == "health_wellness":
        return AppHint(
            identity="a health and wellness companion",
            experience="routines, tracking, and everyday wellbeing support",
            keywords=["health", "wellness", "routines", "tracking", "support", "progress"],
            currency=currency,
            index_title_suffix="Wellness Companion",
            social_noun="wellness updates",
            post_label="wellness update",
        )
    if archetype == "kids_family":
        return AppHint(
            identity="a kids-focused interactive experience",
            experience="age-appropriate activities, guided learning, and family-friendly access",
            keywords=["kids", "family", "activities", "learning", "support", "play"],
            currency=currency,
            index_title_suffix="Kids Experience",
            social_noun="family updates",
            post_label="activity update",
        )
    if archetype == "lifestyle_service":
        return AppHint(
            identity="a lifestyle-focused daily experience",
            experience="routines, inspiration, and easy everyday return visits",
            keywords=["lifestyle", "routines", "inspiration", "daily use", "support", "discover"],
            currency=currency,
            index_title_suffix="Lifestyle Guide",
            social_noun="lifestyle updates",
            post_label="lifestyle update",
        )
    if archetype == "magazines_newsstand":
        return AppHint(
            identity="a magazine and publication reading experience",
            experience="issues, saved reading, and organized publication access",
            keywords=["magazines", "issues", "reading", "publications", "support", "browse"],
            currency=currency,
            index_title_suffix="Publication Reader",
            social_noun="publication updates",
            post_label="issue update",
        )
    if archetype == "medical_reference":
        return AppHint(
            identity="a medical information reference",
            experience="structured guidance, organized lookup, and professional support access",
            keywords=["medical", "reference", "guidance", "lookup", "support", "information"],
            currency=currency,
            index_title_suffix="Medical Reference",
            social_noun="reference updates",
            post_label="reference update",
        )
    if archetype == "music_audio":
        return AppHint(
            identity="a music and audio experience",
            experience="playlists, listening, and organized audio access",
            keywords=["music", "audio", "playlists", "listening", "support", "discover"],
            currency=currency,
            index_title_suffix="Music Experience",
            social_noun="audio updates",
            post_label="audio update",
        )
    if archetype == "navigation_guidance":
        return AppHint(
            identity="a navigation-focused travel utility",
            experience="routes, place guidance, and clear destination support",
            keywords=["navigation", "routes", "maps", "guidance", "support", "travel"],
            currency=currency,
            index_title_suffix="Navigation Guide",
            social_noun="route updates",
            post_label="route update",
        )
    if archetype == "news_reader":
        return AppHint(
            identity="a news and updates reading experience",
            experience="headlines, saved stories, and organized reading access",
            keywords=["news", "headlines", "stories", "reading", "support", "discover"],
            currency=currency,
            index_title_suffix="News Reader",
            social_noun="news updates",
            post_label="story update",
        )
    if archetype == "photo_media":
        return AppHint(
            identity="a photo-led lifestyle experience",
            experience="visual editing, publishing, and polished personal updates",
            keywords=["photo", "visuals", "editing", "sharing", "profiles", "support"],
            currency=currency,
            index_title_suffix="Photo Experience",
            social_noun="visual updates",
            post_label="photo post",
        )
    if archetype == "finance_utility":
        return AppHint(
            identity="a purchase-enabled utility app",
            experience="balance tools, repeat-use details, and optional purchases",
            keywords=["utility", "balance", "purchases", "support", "access", "saved details"],
            currency=currency,
            index_title_suffix="Utility Overview",
            social_noun="balance updates",
            post_label="balance update",
        )
    if archetype == "productivity_workflow":
        return AppHint(
            identity="a productivity-focused workflow tool",
            experience="tasks, planning, and organized progress across repeat visits",
            keywords=["productivity", "tasks", "planning", "workflow", "support", "organize"],
            currency=currency,
            index_title_suffix="Productivity Workflow",
            social_noun="workflow updates",
            post_label="task update",
        )
    if archetype == "reference_lookup":
        return AppHint(
            identity="a reference and lookup experience",
            experience="structured answers, saved information, and clear browsing access",
            keywords=["reference", "lookup", "information", "saved items", "support", "browse"],
            currency=currency,
            index_title_suffix="Reference Guide",
            social_noun="reference updates",
            post_label="reference update",
        )
    if archetype == "sports_activity":
        return AppHint(
            identity="a sports-focused activity experience",
            experience="teams, scores, and organized sports updates",
            keywords=["sports", "scores", "teams", "activity", "support", "updates"],
            currency=currency,
            index_title_suffix="Sports Activity",
            social_noun="sports updates",
            post_label="sports update",
        )
    if archetype == "weather_forecast":
        return AppHint(
            identity="a weather information utility",
            experience="forecasts, local conditions, and timely weather access",
            keywords=["weather", "forecasts", "conditions", "alerts", "support", "local"],
            currency=currency,
            index_title_suffix="Weather Forecast",
            social_noun="weather updates",
            post_label="forecast update",
        )
    if archetype == "general_utility":
        return AppHint(
            identity="a practical utility app",
            experience="everyday tools, repeat-use details, and product support",
            keywords=["utility", "tools", "support", "access", "saved details", "help"],
            currency=currency,
            index_title_suffix="Utility Overview",
            social_noun="product updates",
            post_label="update",
        )
    return AppHint(
        identity="a community-driven lifestyle app",
        experience="discovery, publishing, and everyday sharing",
        keywords=["community", "lifestyle", "profile", "sharing", "support", "discover"],
        currency=currency,
        index_title_suffix="Overview",
        social_noun="community updates",
        post_label="post",
    )


def normalize_archetype(value: str | None, category: str | None = None) -> str:
    raw = (value or "").strip()
    if raw in ARCHETYPE_LABELS:
        return raw
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    for key, label in ARCHETYPE_LABELS.items():
        if normalized == key or normalized == label.lower().replace(" ", "_"):
            return key
    if category:
        return CATEGORY_ARCHETYPE_MAP.get(category, "general_utility")
    return "general_utility"


def hint_from_classification(
    classification: dict[str, Any],
    inspect_payload: dict[str, Any],
    fallback: AppHint,
) -> AppHint:
    raw_hint = classification.get("theme_hint")
    if not isinstance(raw_hint, dict):
        return fallback

    identity = str(raw_hint.get("identity", "")).strip()
    experience = str(raw_hint.get("experience", "")).strip()
    keywords_raw = raw_hint.get("keywords", [])
    keywords = [str(item).strip() for item in keywords_raw if str(item).strip()] if isinstance(keywords_raw, list) else []
    currency_explicitly_set = "currency" in raw_hint
    currency_value = raw_hint.get("currency")
    currency = str(currency_value).strip() if isinstance(currency_value, str) and str(currency_value).strip() else None
    index_title_suffix = str(raw_hint.get("index_title_suffix", "")).strip()
    social_noun = str(raw_hint.get("social_noun", "")).strip()
    post_label = str(raw_hint.get("post_label", "")).strip()

    if not all([identity, experience, keywords, index_title_suffix, social_noun, post_label]):
        return fallback

    if currency is None and not currency_explicitly_set and inspect_payload.get("privacy_signals", {}).get("payments"):
        currency = fallback.currency

    return AppHint(
        identity=identity,
        experience=experience,
        keywords=keywords,
        currency=currency,
        index_title_suffix=index_title_suffix,
        social_noun=social_noun,
        post_label=post_label,
    )


def renumber_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    renumbered: list[dict[str, Any]] = []
    for index, section in enumerate(sections, start=1):
        title = str(section["title"])
        label = title.split(". ", 1)[1] if ". " in title else title
        updated = dict(section)
        updated["title"] = f"{index}. {label}"
        renumbered.append(updated)
    return renumbered


def unique_preserve_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def pluralize_phrase(phrase: str) -> str:
    words = phrase.split()
    if not words:
        return phrase

    last = words[-1]
    lower = last.lower()
    irregular = {
        "community": "communities",
        "diary": "diaries",
        "story": "stories",
    }
    if lower in irregular:
        plural = irregular[lower]
    elif lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        plural = lower[:-1] + "ies"
    elif lower.endswith(("s", "x", "z", "ch", "sh")):
        plural = lower + "es"
    else:
        plural = lower + "s"

    if last.isupper():
        plural = plural.upper()
    elif last.istitle():
        plural = plural.capitalize()

    words[-1] = plural
    return " ".join(words)


def collect_theme_fragments(hint: AppHint) -> list[str]:
    fragments: list[str] = []
    skip_markers = ("credit", "coin", "purchase", "subscription", "virtual", "support", "access", "help")
    for source in [*hint.keywords, hint.social_noun, hint.experience]:
        for part in re.split(r",| and ", source):
            cleaned = re.sub(r"\s+", " ", part).strip(" .")
            if len(cleaned) < 4:
                continue
            lowered = cleaned.lower()
            if any(marker in lowered for marker in skip_markers):
                continue
            fragments.append(cleaned)
    return unique_preserve_order(fragments) or unique_preserve_order([hint.social_noun, hint.experience])


def pick_theme_fragment(hint: AppHint, rng: random.Random) -> str:
    fragments = collect_theme_fragments(hint)
    return rng.choice(fragments) if fragments else hint.social_noun


def pick_theme_pair(hint: AppHint, rng: random.Random) -> str:
    fragments = collect_theme_fragments(hint)
    if not fragments:
        return hint.experience
    if len(fragments) == 1:
        return fragments[0]
    selected = rng.sample(fragments, k=2)
    return f"{selected[0]} and {selected[1]}"


def purchase_goods_phrase(hint: AppHint) -> str:
    if hint.currency:
        return f"in-app purchases and virtual goods such as {hint.currency}"
    return "in-app purchases and virtual goods"


def build_purchase_sentence(hint: AppHint, rng: random.Random) -> str:
    if hint.currency:
        return rng.choice(
            [
                f"Optional in-app purchases, including {hint.currency}, are available when you want more access.",
                f"You can use optional in-app purchases, including {hint.currency}, if you want added access.",
                f"Optional in-app purchases can add access when you choose to buy {hint.currency}.",
            ]
        )
    return rng.choice(
        [
            "Optional purchases are available when you want to unlock more access.",
            "You can use optional in-app purchases if you want additional access.",
            "Optional in-app purchases are available for people who want added access.",
        ]
    )


def build_purchase_bullet(hint: AppHint, rng: random.Random) -> str:
    if hint.currency:
        return rng.choice(
            [
                f"Use optional in-app purchases, including {hint.currency}, for added access when you choose to continue.",
                f"Choose optional in-app purchases, including {hint.currency}, when you want added access at your own pace.",
                f"Keep optional in-app purchases available for the moments when buying {hint.currency} makes sense.",
            ]
        )
    return rng.choice(
        [
            "Use optional in-app purchases for added access when you choose to continue.",
            "Choose optional in-app purchases when you want added access at your own pace.",
            "Keep optional in-app purchases available for the moments when added access makes sense.",
        ]
    )


def description_mentions_iap(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("purchase", "purchases", "credits", "coins", "subscription", "virtual"))


def ensure_iap_description_context(text: str, hint: AppHint, has_iap: bool, rng: random.Random) -> str:
    normalized = text.strip()
    if not has_iap or description_mentions_iap(normalized):
        return normalized
    separator = "\n" if "\n- " in normalized else " "
    return f"{normalized}{separator}{build_purchase_sentence(hint, rng)}".strip()


def sanitize_non_chat_description(text: str) -> str:
    normalized = text.strip()
    replacements = (
        ("without losing the thread", "without losing your place"),
        ("important threads", "important updates"),
        ("save the thread of the experience", "save the shape of the experience"),
        ("in-app messages", "community activity"),
        ("direct messages", "direct updates"),
        ("conversations", "activity"),
        ("conversation", "activity"),
        ("messages", "updates"),
        ("message", "update"),
        ("threads", "updates"),
        ("thread", "place"),
        ("inbox", "activity"),
        ("chat", "community"),
    )
    for old, new in replacements:
        normalized = re.sub(rf"\b{re.escape(old)}\b", new, normalized, flags=re.IGNORECASE)
    return re.sub(r" {2,}", " ", normalized).strip()


def sanitize_non_chat_site_overview_copy(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    for key in ("brand_overview", "index_subtitle", "purpose", "members_intro"):
        sanitized[key] = sanitize_non_chat_description(str(payload.get(key, "")))
    return sanitized


def build_feature_bullets(
    category: str,
    hint: AppHint,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    count: int = 3,
) -> list[str]:
    rng = rng or random.SystemRandom()
    has_ugc = has_ugc_capability(active)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload or {})
    post_label_plural = pluralize_phrase(hint.post_label)
    theme_pair = pick_theme_pair(hint, rng)
    bullets = [
        rng.choice(
            [
                f"Browse {hint.social_noun} and keep {theme_pair} in one easy flow.",
                f"Move through {hint.social_noun} while keeping {theme_pair} close at hand.",
                f"Keep up with {hint.social_noun} in a stream that stays clear and easy to revisit.",
            ]
        ),
        rng.choice(
            [
                f"Publish {post_label_plural}, keep a personal profile, and return to the updates you want to revisit."
                if has_ugc
                else "Keep your personal profile, saved moments, and everyday preferences close to the experience you build over time.",
                f"Share new {post_label_plural}, shape your profile, and keep your own activity easy to follow."
                if has_ugc
                else "Keep profile details and saved moments close without turning the experience into a heavy workflow.",
                f"Keep profile activity and fresh {post_label_plural} close together when you want to add something of your own."
                if has_ugc
                else "Keep your saved activity and repeat-use details close whenever you come back."
            ]
        ),
    ]
    if category == "Travel":
        bullets.append(
            rng.choice(
                [
                    "Translate text or voice when you need quick help while moving between places and plans.",
                    "Use text or voice translation when you need practical help across places and plans.",
                    "Keep translation tools ready when language support matters during a trip.",
                ]
            )
            if has_translation
            else rng.choice(
                [
                    "Keep nearby context and location-aware details close when you want more context while moving between places and plans.",
                    "Bring nearby details into the same flow when location helps explain what you are seeing.",
                    "Keep place context close when it adds useful detail to the experience.",
                ]
            )
        )
    elif has_chat:
        bullets.append(
            rng.choice(
                [
                    "Stay close to the people and conversations that keep the experience personal through in-app messaging.",
                    "Keep conversations moving with messaging tools that stay connected to the rest of the experience.",
                    "Move from browsing into direct messages when you want a more personal exchange.",
                ]
            )
        )
    elif has_iap:
        bullets.append(build_purchase_bullet(hint, rng))
    else:
        bullets.append(
            rng.choice(
                [
                    "Report or block problematic members or profiles so your community space stays easier to manage.",
                    "Use reporting and blocking tools when you need more control over unwanted behavior.",
                    "Keep moderation controls close when you want a cleaner community experience.",
                ]
            )
        )

    extras: list[str] = []
    if has_ugc:
        extras.extend(
            [
                f"Keep profiles and new {post_label_plural} close together when you want the app to feel active and easy to revisit.",
                f"Move between {hint.social_noun} and your own {post_label_plural} without losing your place.",
            ]
        )
    elif "profile" in active:
        extras.extend(
            [
                "Keep profile activity and saved moments easy to revisit whenever you come back.",
                    "Return to your saved details and recent activity without a heavy workflow.",
            ]
        )

    if category == "Travel":
        extras.extend(
            [
                "Bring location-aware context into the same flow when place details add useful meaning.",
                "Keep place context available when it helps explain the moment more clearly.",
            ]
        )
    elif has_chat:
        extras.extend(
            [
                "Keep conversations connected to the rest of the experience when a direct exchange matters.",
                "Move from browsing into replies and messages without losing the thread.",
            ]
        )
    elif has_iap:
        extras.extend(
            [
                "Keep optional purchases in the background until added access genuinely makes sense.",
                "Use virtual goods only when you want the extra access they unlock.",
            ]
        )
    else:
        extras.extend(
            [
                "Use reporting and blocking tools when you want more control over what you see.",
                "Keep moderation controls close when a cleaner community experience matters.",
            ]
        )

    for candidate in unique_preserve_order(extras):
        if len(bullets) >= count:
            break
        if candidate.casefold() in {item.casefold() for item in bullets}:
            continue
        bullets.append(candidate)

    if len(bullets) < count:
        fillers = [
            f"Keep {theme_pair} easy to revisit whenever you want to return to the app.",
            f"Stay close to {hint.social_noun} without turning the experience into a technical workflow.",
            "Keep the app easy to understand from the first screen to the moments you revisit later.",
        ]
        for candidate in fillers:
            if len(bullets) >= count:
                break
            if candidate.casefold() in {item.casefold() for item in bullets}:
                continue
            bullets.append(candidate)

    return bullets[:count]


def build_benefit_bullets(
    category: str,
    hint: AppHint,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any] | None = None,
    rng: random.Random | None = None,
    count: int = 3,
) -> list[str]:
    rng = rng or random.SystemRandom()
    has_ugc = has_ugc_capability(active)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload or {})
    theme_fragment = pick_theme_fragment(hint, rng)
    theme_pair = pick_theme_pair(hint, rng)
    post_label_plural = pluralize_phrase(hint.post_label)

    bullets = [
        rng.choice(
            [
                f"Discover a steadier way to keep {theme_pair} and personal updates in one place.",
                f"Discover a simpler rhythm for keeping {hint.social_noun} and personal activity close together.",
                f"Discover a clearer home for {theme_fragment} and the updates you want to revisit later.",
            ]
        ),
        rng.choice(
            [
                f"Enjoy a more polished routine when {hint.social_noun}, {post_label_plural}, and profile activity stay close together."
                if has_ugc
                else f"Enjoy a more polished routine when profile activity and {theme_fragment} stay close together.",
                "Enjoy a cleaner flow when the app keeps your profile, saved activity, and everyday context easy to reach.",
                f"Enjoy a calmer experience when {theme_pair} can stay connected to the rest of the app.",
            ]
        ),
        rng.choice(
            [
                f"Feel comfortable continuing with optional {purchase_goods_phrase(hint)} when added access makes sense for you."
                if has_iap and hint.currency
                else (
                    "Feel comfortable continuing with optional in-app purchases and virtual goods when added access makes sense for you."
                    if has_iap
                    else "Feel comfortable returning for new ideas without losing the details that mattered earlier."
                ),
                f"Feel confident revisiting {hint.social_noun} without losing the profile or activity details you cared about."
                if not has_iap
                else (
                    f"Feel confident using optional {purchase_goods_phrase(hint)} only when they fit the way you want to continue."
                    if hint.currency
                    else "Feel confident using optional in-app purchases and virtual goods only when they fit the way you want to continue."
                ),
                f"Feel a little more control over the pace of the experience, whether that means revisiting {theme_fragment} or adding optional purchases and virtual goods later."
                if has_iap
                else f"Feel a little more control over the pace of the experience as {theme_fragment} and profile activity keep their place.",
            ]
        ),
    ]

    extras: list[str] = []
    if category == "Travel":
        extras.append(
            "Keep travel context closer to the moment, whether that means nearby details or quick translation support."
            if has_translation
            else "Keep place-aware details closer to the moment when location adds useful context."
        )
    elif has_chat:
        extras.append("Keep conversations closer to the rest of the experience when a direct exchange matters.")
    elif has_ugc:
        extras.append("Keep community activity feeling lighter when profiles, posts, and safety tools stay within easy reach.")
    else:
        extras.append("Keep the experience approachable when saved details and personal preferences stay easy to revisit.")

    extras.extend(
        [
            f"Keep {theme_pair} easier to revisit without losing the shape of the experience.",
            "Enjoy a clearer sense of flow from the first visit to the moments you come back later.",
        ]
    )

    for candidate in unique_preserve_order(extras):
        if len(bullets) >= count:
            break
        if candidate.casefold() in {item.casefold() for item in bullets}:
            continue
        bullets.append(candidate)

    return bullets[:count]


def build_community_purchase_bullets(
    context: DescriptionContext,
    rng: random.Random,
    count: int,
) -> list[str]:
    bullets = [
        rng.choice(
            [
                f"Browse {context.hint.social_noun} in a feed that keeps new inspiration and personal taste close together.",
                f"Move through {context.hint.social_noun} in a community flow that stays easy to revisit.",
                f"Keep up with {context.hint.social_noun} in a polished space that still feels personal.",
            ]
        ),
        rng.choice(
            [
                f"Publish {context.post_label_plural}, keep a profile, and return to your own activity without losing your place."
                if context.has_ugc
                else "Keep your profile, saved activity, and return visits connected in one clear flow.",
                f"Share fresh {context.post_label_plural}, shape your profile, and keep the app feeling active without turning it noisy."
                if context.has_ugc
                else "Keep profile details and saved activity close whenever you come back.",
                f"Keep profiles and fresh {context.post_label_plural} close together when you want the app to feel active and readable."
                if context.has_ugc
                else "Keep repeat-use details and saved context close without making the app feel heavy.",
            ]
        ),
    ]

    if context.has_iap:
        bullets.append(build_purchase_bullet(context.hint, rng))
    else:
        bullets.append(
            rng.choice(
                [
                    "Keep reporting and blocking tools nearby when you want a cleaner community space.",
                    "Use moderation controls when you need more control over what appears in the app.",
                    "Keep safety controls close when you want the experience to stay comfortable and easy to manage.",
                ]
            )
        )
    return bullets[:count]


def build_description_bullets(
    role: str,
    context: DescriptionContext,
    rng: random.Random,
    count: int,
) -> list[str]:
    if role == "feature":
        bullets = build_feature_bullets(
            context.category,
            context.hint,
            context.active,
            context.has_iap,
            context.inspect_payload,
            rng,
            count,
        )
        if context.has_iap and count == 5 and not any(
            "purchase" in bullet.lower() or "virtual good" in bullet.lower() for bullet in bullets
        ):
            bullets[-1] = build_purchase_bullet(context.hint, rng)
        return bullets
    if role == "benefit":
        return build_benefit_bullets(
            context.category,
            context.hint,
            context.active,
            context.has_iap,
            context.inspect_payload,
            rng,
            count,
        )
    if role == "community_purchase":
        return build_community_purchase_bullets(context, rng, count)
    if role == "feature_then_value_feature":
        return build_feature_bullets(
            context.category,
            context.hint,
            context.active,
            context.has_iap,
            context.inspect_payload,
            rng,
            count,
        )
    if role == "feature_then_value_benefit":
        return build_benefit_bullets(
            context.category,
            context.hint,
            context.active,
            context.has_iap,
            context.inspect_payload,
            rng,
            count,
        )
    return []


def build_ugc_chat_sentence(
    hint: AppHint,
    active: set[str],
    inspect_payload: dict[str, Any] | None = None,
    rng: random.Random | None = None,
) -> str:
    rng = rng or random.SystemRandom()
    has_ugc = has_ugc_capability(active)
    has_chat = has_chat_capability(active, inspect_payload)
    post_label_plural = pluralize_phrase(hint.post_label)

    if has_ugc and has_chat:
        return rng.choice(
            [
                f"People can browse {hint.social_noun}, publish {post_label_plural}, keep a profile, and continue conversations inside the app.",
                f"It keeps {hint.social_noun}, personal profiles, fresh {post_label_plural}, and ongoing conversations in one place.",
                f"People can move between {hint.social_noun}, their own {post_label_plural}, profile activity, and private conversations without losing the thread.",
            ]
        )
    if has_ugc:
        return rng.choice(
            [
                f"People can browse {hint.social_noun}, publish {post_label_plural}, and keep a profile that reflects what they want to share.",
                f"It keeps {hint.social_noun}, fresh {post_label_plural}, and personal profile activity close to the same everyday flow.",
                f"People can return to {hint.social_noun}, share new {post_label_plural}, and shape a profile that stays personal over time.",
            ]
        )
    if has_chat:
        return rng.choice(
            [
                "People can keep conversations moving with in-app messages and return to important threads when they want to pick things up again.",
                "It keeps messaging and conversations easy to revisit when people want to pick things up again.",
                "People can move from discovery into messages and keep conversations close to the rest of the app.",
            ]
        )
    if "profile" in active:
        return rng.choice(
            [
                "The experience keeps profiles, saved moments, and personal preferences easy to revisit.",
                "It keeps profile activity and personal preferences close whenever people come back.",
                "Profiles and saved moments stay easy to revisit as the experience builds over time.",
            ]
        )
    return ""


def build_description_context(
    app_name: str,
    category: str,
    hint: AppHint,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any] | None = None,
    rng: random.Random | None = None,
) -> DescriptionContext:
    rng = rng or random.SystemRandom()
    inspect_payload = inspect_payload or {}
    has_ugc = has_ugc_capability(active)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    ugc_chat_sentence = build_ugc_chat_sentence(hint, active, inspect_payload, rng)
    theme_fragment = pick_theme_fragment(hint, rng)
    theme_pair = pick_theme_pair(hint, rng)
    post_label_plural = pluralize_phrase(hint.post_label)
    purchase_sentence = build_purchase_sentence(hint, rng) if has_iap else ""

    if category == "Travel":
        style_specific_tail = (
            rng.choice(
                [
                    "Translation tools and nearby context stay close when language or place matters to the moment.",
                    "It keeps place context and translation support close when moving between plans and locations.",
                    "Language support and place-aware context stay nearby when travel details need to stay practical.",
                ]
            )
            if has_translation
            else rng.choice(
                [
                    "Place-aware details stay close when location adds useful context to what people are seeing.",
                    "Nearby context stays connected to the experience when location helps explain the moment.",
                    "It keeps place context nearby when that extra detail matters.",
                ]
            )
        )
    elif has_chat:
        style_specific_tail = rng.choice(
            [
                "Conversations stay close to the rest of the experience when people want a more direct exchange.",
                "Messaging keeps the experience personal without breaking the flow back to the main app.",
                "Private conversations can continue alongside the rest of the app when people want a closer exchange.",
            ]
        )
    elif has_iap:
        style_specific_tail = purchase_sentence
    elif has_ugc:
        style_specific_tail = rng.choice(
            [
                "Profiles, posts, and reporting tools stay close together when people want more control over the space.",
                "Community tools stay close at hand when people want to post, revisit, or manage what they see.",
                "The app keeps publishing, profiles, and moderation controls close to the same rhythm.",
            ]
        )
    else:
        style_specific_tail = rng.choice(
            [
                "Personal preferences and saved moments stay easy to revisit over time.",
                "The experience keeps essential actions close without turning into a heavy workflow.",
                "It stays clear enough to revisit whenever people want to pick things up again.",
            ]
        )

    return DescriptionContext(
        app_name=app_name,
        category=category,
        hint=hint,
        active=active,
        has_iap=has_iap,
        inspect_payload=inspect_payload,
        has_ugc=has_ugc,
        has_chat=has_chat,
        has_translation=has_translation,
        ugc_chat_sentence=ugc_chat_sentence,
        theme_fragment=theme_fragment,
        theme_pair=theme_pair,
        post_label_plural=post_label_plural,
        purchase_sentence=purchase_sentence,
        style_specific_tail=style_specific_tail,
    )


def build_description_plan(style: str) -> DescriptionPlan:
    return STYLE_DESCRIPTION_PLANS.get(style, STYLE_DESCRIPTION_PLANS["all_in_one"])


def theme_first_intro_sentence(role: str, app_name: str, hint: AppHint) -> str | None:
    identity_phrase = theme_first_product_phrase(hint)
    if not identity_phrase:
        return None

    if role == "intro_concise":
        return f"{app_name} is {identity_phrase} built for {hint.experience}."
    if role == "intro_feature_scan":
        return f"{app_name} is {identity_phrase} built around {hint.experience}, so the theme reads clearly from the first screen."
    if role == "intro_feature_detail":
        return f"{app_name} is {identity_phrase} built around {hint.experience}, with a structure that keeps the core theme easy to scan."
    if role == "intro_feature_expanded":
        return f"{app_name} is {identity_phrase} built for {hint.experience}."
    if role == "intro_benefit":
        return f"{app_name} is {identity_phrase} designed for {hint.experience}, so the experience feels clear from the first visit."
    if role == "intro_benefit_expanded":
        return f"{app_name} is {identity_phrase} designed for {hint.experience}, with a flow that stays easy to return to."
    if role == "intro_you_can":
        return f"{app_name} is {identity_phrase} built for {hint.experience}, with the main actions staying clear from the start."
    if role == "intro_why_choose":
        return f"{app_name} is {identity_phrase} built around {hint.experience}, with clear reasons people keep coming back."
    if role == "intro_homebase":
        return f"{app_name} gives {hint.experience} one clear home inside {identity_phrase}."
    if role == "intro_all_in_one":
        return f"{app_name} is {identity_phrase} that keeps {hint.experience} in one clear mobile experience."
    if role == "intro_members_first":
        return f"{app_name} is {identity_phrase} built around members, profiles, and the kinds of posts that keep {hint.experience} active."
    if role == "intro_everyday_use":
        return f"{app_name} is {identity_phrase} built so {hint.experience} stay easy to pick up across repeat visits."
    if role == "intro_longform":
        return f"{app_name} is {identity_phrase} built for {hint.experience}."
    return None


def description_role_text(role: str, context: DescriptionContext, rng: random.Random) -> str:
    app_name = context.app_name
    hint = context.hint
    has_iap = context.has_iap
    has_ugc = context.has_ugc
    theme_fragment = context.theme_fragment
    theme_pair = context.theme_pair
    post_label_plural = context.post_label_plural
    themed_intro = theme_first_intro_sentence(role, app_name, hint)

    if role == "purchase_inline":
        return context.purchase_sentence
    if role == "tail_context":
        return context.style_specific_tail
    if themed_intro is not None:
        return themed_intro

    if role == "intro_concise":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} for {hint.experience}.",
                f"{app_name} brings {hint.experience} into {hint.identity}.",
                f"{app_name} keeps {hint.experience} in a direct, easy-to-read mobile experience.",
            ]
        )
    if role == "return_flow_direct":
        return context.ugc_chat_sentence or rng.choice(
            [
                f"It keeps {theme_pair} and personal activity close without making the app feel heavy.",
                f"It keeps {hint.social_noun} and profile activity easy to revisit.",
                f"It gives {theme_fragment} a clearer place to return to on mobile.",
            ]
        )
    if role == "intro_feature_scan":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} shaped around {hint.experience}, making the product easy to understand from the first screen.",
                f"{app_name} is {hint.identity} built around {hint.experience}, with a structure that stays clear from the start.",
                f"{app_name} is {hint.identity} designed for {hint.experience}, so the app reads quickly from the moment you enter.",
            ]
        )
    if role == "intro_feature_detail":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} built around {hint.experience}, with a little more detail on how the product fits together.",
                f"{app_name} is {hint.identity} shaped for {hint.experience}, so the main pieces of the app stay clear from the start.",
                f"{app_name} is {hint.identity} designed for {hint.experience}, with a structure that makes the core experience easy to scan quickly.",
            ]
        )
    if role == "intro_feature_expanded":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} for {hint.experience}.",
                f"{app_name} brings together {hint.experience} in {hint.identity}.",
                f"{app_name} is a polished space for {hint.experience}.",
            ]
        )
    if role == "bridge_feature_expanded":
        return rng.choice(
            [
                f"Discover {hint.social_noun}, share your own updates, and keep up with what you want to revisit later."
                if has_ugc
                else f"Discover {hint.social_noun} and keep the parts of the experience you want to revisit later close at hand.",
                f"Keep {theme_pair} close, return to profiles and activity, and move through the app without losing the thread.",
                context.ugc_chat_sentence or f"Keep {theme_fragment} and personal activity in one place when you want an easier way to come back later.",
            ]
        )
    if role == "closing_feature_expanded":
        return rng.choice(
            [
                f"{app_name} is built for people who want {hint.experience} to feel personal, expressive, and easy to revisit over time.",
                f"{app_name} is built for people who like lightweight discovery, a personal profile, and an experience that keeps its shape over time.",
                f"{app_name} is made for people who want {theme_fragment} to stay clear, personal, and easy to return to.",
            ]
        )
    if role == "intro_benefit":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} designed for {hint.experience}, so the experience can feel clear, friendly, and consumer-facing right away.",
                f"{app_name} is {hint.identity} built around {hint.experience}, with a flow that can feel approachable from the first visit.",
                f"{app_name} is {hint.identity} shaped for {hint.experience}, helping the experience feel direct and easy to settle into.",
            ]
        )
    if role == "intro_benefit_expanded":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} designed for {hint.experience}, with a few more reasons the experience can feel easy to return to.",
                f"{app_name} is {hint.identity} built around {hint.experience}, creating a clearer sense of flow from the first visit onward.",
                f"{app_name} is {hint.identity} shaped for {hint.experience}, helping the app feel approachable while still giving people room to do more.",
            ]
        )
    if role == "intro_you_can":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} built for {hint.experience}, with a structure that stays clear from the start.",
                f"{app_name} gives {hint.experience} a more readable mobile home, so the main actions stay easy to scan quickly.",
                f"{app_name} brings together {hint.experience} in a product that feels direct, consumer-facing, and easy to understand.",
            ]
        )
    if role == "closing_you_can":
        return rng.choice(
            [
                f"{app_name} keeps the experience broad, readable, and easy to return to whenever {theme_fragment} matter again.",
                f"{app_name} is made for people who want {hint.experience} to stay personal, clear, and easy to revisit.",
                f"The result is a mobile experience that keeps {theme_pair} and personal activity close without feeling crowded.",
            ]
        )
    if role == "intro_why_choose":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} built around {hint.experience}, with a few clear reasons people keep coming back.",
                f"{app_name} gives {hint.experience} a clearer place on mobile, with benefits that stay easy to understand from the first visit.",
                f"{app_name} is designed for {hint.experience}, so the value of the experience reads quickly for new and returning users.",
            ]
        )
    if role == "intro_homebase":
        return rng.choice(
            [
                f"{app_name} gives {hint.experience} one clear home on mobile, so the main parts of the experience stay connected.",
                f"{app_name} brings {hint.social_noun}, profile activity, and the next step together in one place people can understand quickly.",
                f"{app_name} is {hint.identity} built to keep {theme_pair} in one steady flow instead of scattering them across the app.",
            ]
        )
    if role == "intro_all_in_one":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} that keeps {hint.experience} in one clear, all-in-one mobile experience.",
                f"{app_name} brings together {hint.experience} in one place, so discovery, profile activity, and the next action stay close.",
                f"{app_name} gives people one readable place for {hint.experience} instead of splitting the experience into disconnected steps.",
            ]
        )
    if role == "bridge_all_in_one":
        return rng.choice(
            [
                context.ugc_chat_sentence or f"It keeps {theme_pair} close, makes profile activity easier to revisit, and leaves room for the next thing people want to do.",
                f"People can move through {hint.social_noun}, revisit {theme_fragment}, and keep track of what still matters later."
                if has_ugc
                else f"It keeps {theme_pair} and personal activity close enough that returning later still feels straightforward.",
                f"The app stays broad and consumer-facing, so {theme_fragment} feel connected to the rest of the product instead of isolated.",
            ]
        )
    if role == "closing_all_in_one":
        return rng.choice(
            [
                context.style_specific_tail,
                "Optional purchases stay in the background until added access genuinely makes sense."
                if has_iap
                else f"It stays easy to revisit whenever {theme_fragment} matter again.",
                f"It is designed for people who want {hint.experience} to feel clear, personal, and easy to pick back up.",
            ]
        )
    if role == "intro_members_first":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} where members browse {hint.social_noun}, keep a profile, and return to fresh updates in one grounded social flow.",
                f"{app_name} is {hint.identity} built around profiles, fresh {post_label_plural}, and the kinds of updates that keep the community feeling active on mobile.",
                f"{app_name} is {hint.identity} that keeps {hint.social_noun}, profiles, and member participation close together in a more grounded way.",
            ]
        )
    if role == "bridge_members_first":
        return rng.choice(
            [
                context.ugc_chat_sentence or f"Members can move through {theme_pair} while keeping their profile activity close by.",
                f"People can browse {hint.social_noun}, shape a profile, and return to the updates they care about without losing the thread.",
                f"It gives members a clearer place to revisit {theme_fragment} while keeping the surrounding community context readable.",
            ]
        )
    if role == "closing_members_first":
        return rng.choice(
            [
                "Safety, reporting, and everyday control stay close when members want a cleaner community space."
                if not has_iap
                else "Optional purchases sit beside that member flow only when people want added access.",
                context.style_specific_tail,
                "The product stays social without turning into a noisy wall of disconnected activity.",
            ]
        )
    if role == "intro_everyday_use":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} built so {hint.experience} stay easy to pick up across everyday repeat visits.",
                f"{app_name} gives {hint.experience} a steady shape on mobile, so people can reopen the app and find their place quickly.",
                f"{app_name} turns {hint.experience} into a product people can return to often without relearning how everything fits together.",
            ]
        )
    if role == "bridge_everyday_use":
        return rng.choice(
            [
                f"From checking {hint.social_noun} to updating a profile or sharing fresh {post_label_plural}, the flow stays easy to follow."
                if has_ugc
                else f"From reopening the app to revisiting {theme_pair}, the experience stays steady and easy to understand.",
                f"It keeps {theme_fragment}, profile activity, and the next action close enough that another visit still feels natural.",
                context.ugc_chat_sentence or f"It keeps {theme_pair} close enough that using the app again later still feels straightforward.",
            ]
        )
    if role == "closing_everyday_use":
        return rng.choice(
            [
                "That repeat-use rhythm leaves room for optional purchases only when added access makes sense."
                if has_iap
                else "That repeat-use rhythm leaves room for discovery without making the app feel heavy.",
                context.style_specific_tail,
                f"It is built for people who want {theme_fragment} to stay easy to revisit and easy to continue.",
            ]
        )
    if role == "intro_longform":
        return rng.choice(
            [
                f"{app_name} is {hint.identity} built for {hint.experience}.",
                f"{app_name} is {hint.identity} that gives {hint.experience} one clear home on mobile.",
                f"{app_name} is {hint.identity} shaped around {hint.experience}, with a theme that reads clearly from the first visit.",
            ]
        )
    if role == "bridge_longform":
        return rng.choice(
            [
                context.ugc_chat_sentence or f"It keeps {theme_pair} and personal activity close enough that the app stays easy to understand.",
                f"People can move through {hint.social_noun}, revisit {theme_fragment}, and keep track of what still matters later."
                if has_ugc
                else f"People can revisit {theme_pair} and keep personal activity close without making the experience feel crowded.",
                f"It leaves room for {theme_fragment}, profile activity, and the next action people want to take.",
            ]
        )
    if role == "tail_longform":
        return rng.choice(
            [
                context.style_specific_tail,
                "That makes the app easier to return to when people want fresh inspiration, a clearer profile view, or a calmer routine.",
                "The structure stays broad and consumer-facing, so the overall experience reads more like a product than a technical flow.",
            ]
        )
    if role == "closing_longform":
        return rng.choice(
            [
                "Optional purchases remain available in the background when people want more access."
                if has_iap
                else "It stays approachable enough that people can come back without re-learning how everything fits together.",
                f"In practice, it gives {theme_fragment} a more stable place to build over time.",
                f"It is designed for people who want {hint.experience} to stay clear, steady, and easy to revisit.",
            ]
        )
    if role == "closing_community_then_purchase":
        return rng.choice(
            [
                "The result is a member-led product that keeps community activity readable while leaving optional purchases in the background until they make sense."
                if has_iap
                else "The result is a member-led product that keeps community activity readable without turning into a crowded feed.",
                context.style_specific_tail,
                f"It keeps {theme_fragment} feeling social, polished, and easy to return to over time.",
            ]
        )
    if role == "closing_feature_then_value":
        return rng.choice(
            [
                "That mix of core actions and everyday value keeps the app broad, consumer-facing, and easy to revisit.",
                context.style_specific_tail,
                f"It is designed for people who want {hint.experience} to stay useful without feeling overbuilt.",
            ]
        )
    return ""


def render_description_plan(plan: DescriptionPlan, context: DescriptionContext, rng: random.Random) -> str:
    line_mode = any(block.kind != "sentence" for block in plan.blocks)
    if not line_mode:
        return " ".join(
            part
            for part in (description_role_text(block.role or "", context, rng) for block in plan.blocks)
            if part
        ).strip()

    lines: list[str] = []
    for block in plan.blocks:
        if block.kind == "blank":
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if block.kind == "heading":
            if block.role == "with_you_can":
                lines.append(f"With {context.app_name}, you can:")
            elif block.role == "highlights":
                lines.append("Highlights:")
            elif block.role == "why_people_return":
                lines.append("Why People Return:")
            elif block.role == "inside_app":
                lines.append(f"Inside {context.app_name}:")
            elif block.role == "why_it_feels_easy":
                lines.append("Why It Feels Easy:")
            continue
        if block.kind == "bullets":
            bullets = build_description_bullets(block.role or "", context, rng, block.count)
            lines.extend(f"- {bullet}" for bullet in bullets)
            continue
        sentence = description_role_text(block.role or "", context, rng)
        if sentence:
            lines.append(sentence)

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()


def build_description(
    app_name: str,
    category: str,
    hint: AppHint,
    active: set[str],
    style: str,
    has_iap: bool,
    inspect_payload: dict[str, Any] | None = None,
    rng: random.Random | None = None,
) -> str:
    rng = rng or random.SystemRandom()
    inspect_payload = inspect_payload or {}
    has_chat = has_chat_capability(active, inspect_payload)

    def finalize(text: str) -> str:
        normalized = ensure_iap_description_context(text, hint, has_iap, rng)
        if not has_chat:
            normalized = sanitize_non_chat_description(normalized)
        return normalized

    context = build_description_context(app_name, category, hint, active, has_iap, inspect_payload, rng)
    preview_profile = ai_preview_profile(inspect_payload)
    if preview_profile.get("needs_face_data_clauses"):
        workflow_kind = face_data_workflow_kind(inspect_payload)
        identity_phrase = overview_identity_phrase(hint)
        purchase_phrase = ""
        if has_iap and hint.currency:
            purchase_phrase = f", and purchase {hint.currency} when more preview access is needed"
        elif has_iap:
            purchase_phrase = ", and use optional purchases when more preview access is needed"

        if workflow_kind == "translation_face_visibility":
            return finalize(
                f"{app_name} is {identity_phrase} where people choose a photo with readable text, review the consent prompt, send it for image translation, review the translated result in the app, and optionally save or continue from there{purchase_phrase}. "
                f"{context.ugc_chat_sentence or 'The app keeps discovery, profiles, and user-initiated translation tools in one clear mobile flow.'} "
                "The app combines community discovery with user-initiated translation tools in a way that stays clear on mobile."
            )

        if theme_first_product_phrase(hint):
            preview_sentence = (
                f"{app_name} is {identity_phrase} where people share posts, choose a photo for AI Preview, "
                f"generate and review the preview, and save it to Photos if they want{purchase_phrase}."
            )
        else:
            preview_sentence = (
                f"{app_name} is {identity_phrase} where people share {hint.social_noun}, choose a photo for AI Preview, "
                f"generate a preview, review the result in the app, and save it to Photos if they want{purchase_phrase}."
            )
        if style == "feature_4":
            return finalize(
                "\n".join(
                    [
                        preview_sentence,
                        f"- Browse {hint.social_noun} across the community.",
                        f"- Keep a profile and publish {context.post_label_plural} in the same flow.",
                        "- Choose a photo, review consent, and generate an AI Preview based on the reference umbrella image from the feed.",
                        (
                            f"- Purchase {hint.currency} only when you want more AI Preview access."
                            if has_iap and hint.currency
                            else "- Keep optional purchases in the background until you want more AI Preview access."
                        ),
                    ]
                )
            )
        if style == "feature_5":
            return finalize(
                "\n".join(
                    [
                        preview_sentence,
                        "",
                        f"With {app_name}, you can:",
                        f"- Browse {hint.social_noun} across the community.",
                        f"- Keep a profile and publish {context.post_label_plural} in the same flow.",
                        "- Choose a photo, review consent, and generate an AI Preview based on the reference umbrella image from the feed.",
                        "- Review the generated result in the app before you decide whether to save it to Photos.",
                        (
                            f"- Purchase {hint.currency} only when you want more AI Preview access."
                            if has_iap and hint.currency
                            else "- Keep optional purchases available only when you want more AI Preview access."
                        ),
                        "",
                        f"{app_name} keeps community sharing and AI Preview tools easy to revisit.",
                    ]
                )
            )
        return finalize(
            f"{preview_sentence} "
            f"People can keep a profile, publish {context.post_label_plural}, and return without losing what they saved."
        )

    plan = build_description_plan(style)
    return finalize(render_description_plan(plan, context, rng))


def collect_candidate_files(app_root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ["lib", "docs", "README.md", "ANALYSIS.md", "analysis.md", "AGENTS.md"]:
        path = app_root / rel
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.suffix.lower() not in TEXT_FILE_SUFFIXES:
                continue
            if any(part.lower() in SKIP_DIRS for part in child.parts):
                continue
            files.append(child)
    return files


def collect_project_url_sync_files(app_root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ["lib", "ios"]:
        path = app_root / rel
        if not path.exists():
            continue
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.suffix.lower() not in PROJECT_URL_SYNC_SUFFIXES:
                continue
            if any(part.lower() in SKIP_DIRS for part in child.parts):
                continue
            files.append(child)
    return files


def listing_url_score(path: Path) -> int:
    lowered = str(path).lower()
    score = 0
    if "/lib/" in lowered:
        score += 5
    if "intro" in lowered or "info" in lowered:
        score += 4
    if "analysis" in lowered or "agents" in lowered:
        score += 1
    return score


def extract_listing_urls(app_root: Path) -> dict[str, dict[str, Any]]:
    host_map: dict[str, dict[str, Any]] = {}
    for file_path in collect_candidate_files(app_root):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        matches = LISTING_URL_RE.findall(text)
        if not matches:
            continue
        score = listing_url_score(file_path)
        for url in LISTING_URL_RE.findall(text):
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if not host or any(token in host for token in ("$", "{", "}")):
                continue
            info = host_map.setdefault(host, {"pages": set(), "score": 0})
            info["pages"].add(Path(parsed.path).name)
            info["score"] += score + 1
    return host_map


def candidate_site_host_score(host: str, path: str) -> int:
    score = 1
    lowered_host = host.lower()
    lowered_path = path.lower()
    for suffix, bonus in SITE_HOST_NAME_BONUS.items():
        if lowered_host.endswith(suffix):
            score += bonus
    for keyword, bonus in SITE_HOST_HINT_KEYWORDS.items():
        if keyword in lowered_path:
            score += bonus
    if lowered_path in {"", "/"}:
        score += 4
    if lowered_path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        score -= 10
    if any(token in lowered_host for token in SITE_HOST_PENALTY_TOKENS):
        score -= 12
    return score


def extract_site_host_hints(app_root: Path) -> dict[str, dict[str, Any]]:
    host_map: dict[str, dict[str, Any]] = {}
    for file_path in collect_candidate_files(app_root):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for url in GENERIC_URL_RE.findall(text):
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if not host or any(token in host for token in ("$", "{", "}")):
                continue
            path = parsed.path or "/"
            score = candidate_site_host_score(host, path)
            info = host_map.setdefault(host, {"paths": set(), "score": 0})
            info["paths"].add(path)
            info["score"] += score
    return host_map


def listing_urls_for_host(host: str) -> dict[str, str]:
    return {
        "index": f"https://{host}/index.html",
        "privacy": f"https://{host}/PrivacyPolicy.html",
        "terms": f"https://{host}/Terms&Conditions.html",
        "support": f"https://{host}/Support.html",
    }


def resolve_listing_urls(app_root: Path, inspect_payload: dict[str, Any]) -> dict[str, str]:
    del app_root, inspect_payload
    # Listing URLs are always emitted as placeholders so downstream setup can
    # replace them explicitly instead of inheriting any repo-local host hints.
    return listing_urls_for_host(DEFAULT_LISTING_HOST)


def listing_page_key_for_url(url: str) -> str | None:
    page_name = Path(urlparse(url).path).name
    return LISTING_PAGE_URL_KEYS.get(page_name)


def extract_project_listing_url_matches(text: str) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for url in LISTING_URL_RE.findall(text):
        page_key = listing_page_key_for_url(url)
        if page_key is None:
            continue
        parsed = urlparse(url)
        host = normalize_site_domain(parsed.netloc or parsed.hostname or "")
        if not host or any(token in host for token in ("$", "{", "}")):
            continue
        page_name = Path(parsed.path).name
        matches.append(
            {
                "url": url,
                "host": host,
                "page_key": page_key,
                "page_name": page_name,
            }
        )
    return matches


def file_has_legal_url_config_hints(path: Path, text: str) -> bool:
    lowered_path = str(path).lower()
    if any(token in lowered_path for token in LEGAL_CONFIG_PATH_HINTS):
        return True
    lowered_text = text.lower()
    return any(token in lowered_text for token in LEGAL_CONFIG_TEXT_HINTS)


def extract_legal_host_literals(text: str) -> set[str]:
    hosts: set[str] = set()
    for match in LEGAL_HOST_ASSIGNMENT_RE.finditer(text):
        host = normalize_site_domain(match.group(1))
        if host and not any(token in host for token in ("$", "{", "}")):
            hosts.add(host)
    for match in QUOTED_HOST_LITERAL_RE.finditer(text):
        host = normalize_site_domain(match.group(1))
        if host and not any(token in host for token in ("$", "{", "}")):
            hosts.add(host)
    return hosts


def default_project_url_sync_summary(enabled: bool, reason: str) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "status": "skipped",
        "reason": reason,
        "new_host": "",
        "old_hosts": [],
        "changed_files": [],
        "replaced": {
            "index": 0,
            "privacy": 0,
            "terms": 0,
            "support": 0,
            "host_fallback": 0,
        },
    }


def sync_project_listing_urls(app_root: Path, resolved_urls: dict[str, str]) -> dict[str, Any]:
    new_host = normalize_site_domain(resolved_urls.get("index", ""))
    summary = default_project_url_sync_summary(True, "no_matches")
    summary["new_host"] = new_host
    if not new_host:
        summary["reason"] = "invalid_resolved_urls"
        return summary

    file_entries: list[dict[str, Any]] = []
    listing_hosts: set[str] = set()
    generic_hosts: set[str] = set()
    qualifying_files = 0

    for file_path in collect_project_url_sync_files(app_root):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        listing_matches = extract_project_listing_url_matches(text)
        page_keys = {item["page_key"] for item in listing_matches}
        has_legal_tokens = file_has_legal_url_config_hints(file_path, text)
        has_legal_pages = bool({"privacy", "terms", "support"} & page_keys)
        listing_config = has_legal_pages or len(page_keys) >= 2 or has_legal_tokens
        if listing_config:
            qualifying_files += 1

        for item in listing_matches:
            if item["host"] != new_host:
                listing_hosts.add(item["host"])

        generic_file_hosts: set[str] = set()
        if listing_config:
            for url in GENERIC_URL_RE.findall(text):
                parsed = urlparse(url)
                host = normalize_site_domain(parsed.netloc or parsed.hostname or "")
                if not host or host == new_host or any(token in host for token in ("$", "{", "}")):
                    continue
                generic_file_hosts.add(host)
            generic_file_hosts.update(extract_legal_host_literals(text))
            generic_file_hosts.discard(new_host)
            generic_hosts.update(generic_file_hosts)

        file_entries.append(
            {
                "path": file_path,
                "text": text,
                "listing_matches": listing_matches,
                "page_keys": page_keys,
                "listing_config": listing_config,
                "has_legal_tokens": has_legal_tokens,
            }
        )

    if qualifying_files == 0:
        summary["reason"] = "no_candidate_files"
        return summary

    old_hosts = listing_hosts if listing_hosts else generic_hosts
    summary["old_hosts"] = sorted(old_hosts)
    fallback_old_host = ""
    if len(old_hosts) == 1:
        fallback_old_host = next(iter(old_hosts))
    elif len(old_hosts) > 1:
        summary["reason"] = "ambiguous_old_hosts"

    changed_files: list[str] = []
    original_texts: dict[Path, str] = {}
    host_pattern = (
        re.compile(rf"(?<![@A-Za-z0-9.-]){re.escape(fallback_old_host)}(?![A-Za-z0-9.-])")
        if fallback_old_host
        else None
    )

    try:
        for entry in file_entries:
            file_path = entry["path"]
            text = entry["text"]
            updated = text
            listing_matches = entry["listing_matches"]
            page_keys = entry["page_keys"]
            listing_config = bool(entry["listing_config"])
            has_legal_tokens = bool(entry["has_legal_tokens"])
            allow_index_sync = listing_config and (
                bool({"privacy", "terms", "support"} & page_keys) or len(page_keys) >= 2 or has_legal_tokens
            )

            seen_urls: set[tuple[str, str]] = set()
            for item in listing_matches:
                dedupe_key = (item["url"], item["page_key"])
                if dedupe_key in seen_urls:
                    continue
                seen_urls.add(dedupe_key)
                page_key = item["page_key"]
                if page_key == "index" and not allow_index_sync:
                    continue
                replacement = resolved_urls.get(page_key)
                if not replacement or item["url"] == replacement:
                    continue
                occurrences = updated.count(item["url"])
                if occurrences:
                    updated = updated.replace(item["url"], replacement)
                    summary["replaced"][page_key] += occurrences

            if host_pattern is not None and listing_config:
                host_occurrences = len(host_pattern.findall(updated))
                if host_occurrences:
                    updated = host_pattern.sub(new_host, updated)
                    summary["replaced"]["host_fallback"] += host_occurrences

            if updated == text:
                continue

            original_texts[file_path] = text
            file_path.write_text(updated, encoding="utf-8")
            changed_files.append(str(file_path.relative_to(app_root)))
    except Exception as exc:
        for file_path, original_text in original_texts.items():
            file_path.write_text(original_text, encoding="utf-8")
        summary["status"] = "failed"
        summary["reason"] = "write_failed"
        summary["detail"] = str(exc)
        summary["changed_files"] = []
        summary["replaced"] = {
            "index": 0,
            "privacy": 0,
            "terms": 0,
            "support": 0,
            "host_fallback": 0,
        }
        return summary

    summary["changed_files"] = changed_files
    if changed_files:
        summary["status"] = "updated"
        if fallback_old_host:
            summary["reason"] = "updated"
            summary["old_host"] = fallback_old_host
        elif len(old_hosts) > 1:
            summary["reason"] = "updated_with_ambiguous_old_hosts"
        else:
            summary["reason"] = "updated"
        return summary

    if len(old_hosts) > 1:
        summary["status"] = "ambiguous"
        summary["reason"] = "ambiguous_old_hosts"
        return summary

    summary["status"] = "no_matches"
    summary["reason"] = "no_matches"
    if fallback_old_host:
        summary["old_host"] = fallback_old_host
    return summary


def normalize_site_domain(value: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        return ""
    if "://" in cleaned:
        parsed = urlparse(cleaned)
        cleaned = parsed.netloc or parsed.path
    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0]
    return cleaned.strip().strip("/").lower()


def validate_live_site_domain(domain: str, app_name: str) -> str:
    cleaned = normalize_site_domain(domain)
    if not cleaned:
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned an empty live domain value.",
            retryable=False,
            reason="site_domain_unavailable",
        )

    host = cleaned.strip("[]")
    if host in NON_DEPLOYABLE_HOSTS:
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned placeholder host '{cleaned}', so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        )

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned IP address '{cleaned}' instead of a real domain, so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        )

    labels = [item for item in host.split(".") if item]
    if len(labels) < 2:
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned invalid host '{cleaned}' without a real domain suffix.",
            retryable=False,
            reason="invalid_site_domain",
        )
    if any(label in PLACEHOLDER_DOMAIN_LABELS for label in labels):
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned placeholder host '{cleaned}', so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        )
    if any(not HOSTNAME_LABEL_RE.fullmatch(label) for label in labels):
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned malformed host '{cleaned}', so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        )
    if labels[-1].isdigit():
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned malformed host '{cleaned}', so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        )

    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        reason = str(exc).strip() or "DNS resolution failed"
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned unusable host '{cleaned}' because it could not be resolved ({reason}), so About deployment was not started.",
            retryable=False,
            reason="invalid_site_domain",
        ) from exc

    return cleaned


def deployment_summary_for_error(exc: DeploymentError) -> dict[str, Any]:
    status = "failed"
    if exc.reason in {"site_domain_lookup_failed", "site_domain_unavailable", "invalid_site_domain"}:
        status = "skipped"
    return {
        "enabled": True,
        "status": status,
        "reason": exc.reason,
        "detail": str(exc),
    }


def extract_error_message(payload: Any) -> str | None:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


def parse_json_body_lenient(raw_body: bytes) -> Any | None:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def parse_json_http_response_body(raw_body: bytes, *, request_label: str, retryable: bool) -> dict[str, Any]:
    if not raw_body:
        return {}

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeploymentError(
            f"{request_label} returned a non-JSON response body.",
            retryable=retryable,
        ) from exc

    if not isinstance(payload, dict):
        raise DeploymentError(
            f"{request_label} returned an unexpected JSON structure.",
            retryable=retryable,
        )
    return payload


def is_ssl_cert_verification_failure(exc: URLError) -> bool:
    reason = getattr(exc, "reason", None)
    if isinstance(reason, ssl.SSLCertVerificationError):
        return True
    message = str(reason or exc)
    return "CERTIFICATE_VERIFY_FAILED" in message.upper()


def is_cloudflare_browser_signature_banned(status: int, payload: Any) -> bool:
    if status != 403 or not isinstance(payload, dict):
        return False

    error_name = str(payload.get("error_name", "")).strip().lower()
    if error_name == "browser_signature_banned":
        return True

    error_code = str(payload.get("error_code", "")).strip()
    error_type = str(payload.get("type", "")).strip().lower()
    detail = str(payload.get("detail", "")).strip().lower()
    return (
        error_code == "1010"
        and bool(payload.get("cloudflare_error"))
        and ("cloudflare" in error_type or ("browser" in detail and "signature" in detail))
    )


def request_json_via_curl(
    method: str,
    url: str,
    *,
    request_label: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 30.0,
    network_error_retryable: bool,
    non_retryable_statuses: set[int] | None = None,
    default_http_retryable: bool = True,
) -> JSONHTTPResponse:
    if shutil.which("curl") is None:
        raise DeploymentError(
            f"{request_label} failed: curl is not available for HTTPS fallback.",
            retryable=network_error_retryable,
        )

    with tempfile.TemporaryDirectory(prefix="request_json_curl_") as temp_dir:
        temp_root = Path(temp_dir)
        response_path = temp_root / "response.bin"
        body_path = temp_root / "request.bin"

        curl_cmd = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--request",
            method.upper(),
            "--max-time",
            str(max(1.0, float(timeout_seconds))),
            "--output",
            str(response_path),
            "--write-out",
            f"{CURL_HTTP_STATUS_MARKER}%{{http_code}}",
        ]

        header_items = list((headers or {}).items())
        if not any(key.lower() == "accept" for key, _ in header_items):
            header_items.append(("Accept", "application/json"))
        for key, value in header_items:
            curl_cmd.extend(["--header", f"{key}: {value}"])

        if body is not None:
            body_path.write_bytes(body)
            curl_cmd.extend(["--data-binary", f"@{body_path}"])

        curl_cmd.append(url)

        try:
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise DeploymentError(
                f"{request_label} failed: unable to execute curl fallback ({exc}).",
                retryable=network_error_retryable,
            ) from exc

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "curl transport error"
            raise DeploymentError(
                f"{request_label} failed: {message}",
                retryable=network_error_retryable,
            )

        marker_index = result.stdout.rfind(CURL_HTTP_STATUS_MARKER)
        if marker_index == -1:
            raise DeploymentError(
                f"{request_label} failed: curl fallback did not report an HTTP status.",
                retryable=network_error_retryable,
            )

        status_text = result.stdout[marker_index + len(CURL_HTTP_STATUS_MARKER) :].strip()
        try:
            status = int(status_text)
        except ValueError as exc:
            raise DeploymentError(
                f"{request_label} failed: curl fallback returned an invalid HTTP status '{status_text}'.",
                retryable=network_error_retryable,
            ) from exc

        raw_body = response_path.read_bytes() if response_path.exists() else b""
        if status >= 400:
            payload = parse_json_body_lenient(raw_body)
            message = extract_error_message(payload) or "unexpected HTTP error"
            retryable = default_http_retryable and status not in (non_retryable_statuses or set())
            raise DeploymentError(
                f"{request_label} failed with HTTP {status}: {message}",
                retryable=retryable,
            )

        payload = parse_json_http_response_body(
            raw_body,
            request_label=request_label,
            retryable=network_error_retryable,
        )
        return JSONHTTPResponse(status=status, payload=payload)


def upload_multipart_via_curl(
    url: str,
    *,
    request_label: str,
    file_field: str,
    file_path: Path,
    form_fields: dict[str, str],
    headers: dict[str, str] | None = None,
    timeout_seconds: float,
    network_error_retryable: bool,
    non_retryable_statuses: set[int] | None = None,
    default_http_retryable: bool = True,
) -> JSONHTTPResponse:
    if shutil.which("curl") is None:
        raise DeploymentError(
            f"{request_label} failed: curl is not available for multipart upload fallback.",
            retryable=network_error_retryable,
        )

    with tempfile.TemporaryDirectory(prefix="multipart_curl_") as temp_dir:
        response_path = Path(temp_dir) / "response.bin"
        curl_cmd = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--request",
            "POST",
            "--max-time",
            str(max(1.0, float(timeout_seconds))),
            "--header",
            "Accept: application/json",
            "--output",
            str(response_path),
            "--write-out",
            f"{CURL_HTTP_STATUS_MARKER}%{{http_code}}",
        ]

        for key, value in (headers or {}).items():
            curl_cmd.extend(["--header", f"{key}: {value}"])

        for name, value in form_fields.items():
            curl_cmd.extend(["--form", f"{name}={value}"])
        curl_cmd.extend(["--form", f"{file_field}=@{file_path};type=application/zip"])
        curl_cmd.append(url)

        try:
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise DeploymentError(
                f"{request_label} failed: unable to execute curl multipart upload ({exc}).",
                retryable=network_error_retryable,
            ) from exc

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "curl multipart transport error"
            raise DeploymentError(
                f"{request_label} failed: {message}",
                retryable=network_error_retryable,
            )

        marker_index = result.stdout.rfind(CURL_HTTP_STATUS_MARKER)
        if marker_index == -1:
            raise DeploymentError(
                f"{request_label} failed: curl multipart upload did not report an HTTP status.",
                retryable=network_error_retryable,
            )

        status_text = result.stdout[marker_index + len(CURL_HTTP_STATUS_MARKER) :].strip()
        try:
            status = int(status_text)
        except ValueError as exc:
            raise DeploymentError(
                f"{request_label} failed: curl multipart upload returned an invalid HTTP status '{status_text}'.",
                retryable=network_error_retryable,
            ) from exc

        raw_body = response_path.read_bytes() if response_path.exists() else b""
        if status >= 400:
            payload = parse_json_body_lenient(raw_body)
            message = extract_error_message(payload) or "unexpected HTTP error"
            retryable = default_http_retryable and status not in (non_retryable_statuses or set())
            raise DeploymentError(
                f"{request_label} failed with HTTP {status}: {message}",
                retryable=retryable,
            )

        payload = parse_json_http_response_body(
            raw_body,
            request_label=request_label,
            retryable=network_error_retryable,
        )
        return JSONHTTPResponse(status=status, payload=payload)


def request_json(
    method: str,
    url: str,
    *,
    request_label: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 30.0,
    network_error_retryable: bool,
    non_retryable_statuses: set[int] | None = None,
    default_http_retryable: bool = True,
) -> JSONHTTPResponse:
    request = Request(url, data=body, method=method.upper())
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    if "Accept" not in {key.title(): value for key, value in (headers or {}).items()}:
        request.add_header("Accept", "application/json")

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status = response.getcode()
            raw_body = response.read()
    except HTTPError as exc:
        raw_body = exc.read()
        payload = parse_json_body_lenient(raw_body)
        if is_cloudflare_browser_signature_banned(exc.code, payload):
            return request_json_via_curl(
                method,
                url,
                request_label=request_label,
                body=body,
                headers=headers,
                timeout_seconds=timeout_seconds,
                network_error_retryable=network_error_retryable,
                non_retryable_statuses=non_retryable_statuses,
                default_http_retryable=default_http_retryable,
            )
        message = extract_error_message(payload) or exc.reason or "unexpected HTTP error"
        retryable = default_http_retryable and exc.code not in (non_retryable_statuses or set())
        raise DeploymentError(
            f"{request_label} failed with HTTP {exc.code}: {message}",
            retryable=retryable,
        ) from exc
    except URLError as exc:
        if is_ssl_cert_verification_failure(exc):
            return request_json_via_curl(
                method,
                url,
                request_label=request_label,
                body=body,
                headers=headers,
                timeout_seconds=timeout_seconds,
                network_error_retryable=network_error_retryable,
                non_retryable_statuses=non_retryable_statuses,
                default_http_retryable=default_http_retryable,
            )
        reason = exc.reason if getattr(exc, "reason", None) else str(exc)
        raise DeploymentError(
            f"{request_label} failed: {reason}",
            retryable=network_error_retryable,
        ) from exc

    payload = parse_json_http_response_body(
        raw_body,
        request_label=request_label,
        retryable=network_error_retryable,
    )
    return JSONHTTPResponse(status=status, payload=payload)


def extract_live_h5_domain(payload: dict[str, Any], app_name: str) -> str:
    if not payload.get("success"):
        message = extract_error_message(payload) or f"Sub-domain lookup for {app_name} did not succeed."
        raise DeploymentError(message, retryable=False, reason="site_domain_lookup_failed")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned no data payload.",
            retryable=False,
            reason="site_domain_unavailable",
        )

    live_domains = data.get("live_domains")
    if not isinstance(live_domains, dict):
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned no live_domains payload.",
            retryable=False,
            reason="site_domain_unavailable",
        )

    h5_domain = normalize_site_domain(str(live_domains.get("h5", "")).strip())
    if not h5_domain:
        raise DeploymentError(
            f"Sub-domain lookup for {app_name} returned an empty live_domains.h5 value.",
            retryable=False,
            reason="site_domain_unavailable",
        )
    return h5_domain


def fetch_live_h5_domain(
    app_name: str,
    options: AboutDeploymentOptions,
) -> str:
    lookup_name = app_name.strip()
    if not lookup_name:
        raise DeploymentError(
            "Sub-domain lookup app_name is empty.",
            retryable=False,
            reason="site_domain_lookup_failed",
        )
    query = urlencode({"app_name": lookup_name, "key": SUBDOMAIN_QUERY_KEY})
    response = request_json(
        "GET",
        f"{SUBDOMAIN_QUERY_URL}?{query}",
        request_label=f"Sub-domain lookup for {lookup_name}",
        timeout_seconds=options.http_timeout_seconds,
        network_error_retryable=False,
        non_retryable_statuses=set(),
        default_http_retryable=False,
    )
    return validate_live_site_domain(extract_live_h5_domain(response.payload, lookup_name), lookup_name)


def build_site_bundle(site_dir: Path, destination: Path) -> Path:
    missing = sorted(name for name in REQUIRED_LISTING_PAGE_NAMES if not (site_dir / name).is_file())
    if missing:
        raise DeploymentError(
            f"Cannot build About deployment bundle because AppListing/site is missing: {', '.join(missing)}",
            retryable=False,
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(site_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(site_dir).as_posix())
    return destination


def build_multipart_form_data(
    fields: dict[str, str],
    *,
    file_field: str,
    file_path: Path,
) -> tuple[bytes, str]:
    boundary = f"codex-{uuid.uuid4().hex}"
    parts: list[bytes] = []

    for name, value in fields.items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode(
                    "utf-8"
                )
            ),
            b"Content-Type: application/zip\r\n\r\n",
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def create_about_deployment_task(
    site_domain: str,
    bundle_path: Path,
    options: AboutDeploymentOptions,
) -> dict[str, Any]:
    body, content_type = build_multipart_form_data(
        {"siteDomain": site_domain},
        file_field="bundle",
        file_path=bundle_path,
    )
    request_label = f"About deployment creation for {site_domain}"
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Content-Type": content_type,
        "Idempotency-Key": idempotency_key,
    }
    try:
        response = request_json(
            "POST",
            ABOUT_DEPLOYMENTS_URL,
            request_label=request_label,
            body=body,
            headers=headers,
            timeout_seconds=options.http_timeout_seconds,
            network_error_retryable=True,
            non_retryable_statuses={400, 413},
        )
    except DeploymentError:
        response = upload_multipart_via_curl(
            ABOUT_DEPLOYMENTS_URL,
            request_label=request_label,
            file_field="bundle",
            file_path=bundle_path,
            form_fields={"siteDomain": site_domain},
            headers={"Idempotency-Key": idempotency_key},
            timeout_seconds=options.http_timeout_seconds,
            network_error_retryable=True,
            non_retryable_statuses={400, 413},
        )

    task = response.payload.get("task")
    if not isinstance(task, dict) or not str(task.get("taskId", "")).strip():
        raise DeploymentError(
            f"About deployment creation for {site_domain} returned no taskId.",
            retryable=True,
        )
    return response.payload


def fetch_about_deployment_detail(task_id: str, options: AboutDeploymentOptions) -> dict[str, Any]:
    response = request_json(
        "GET",
        f"{ABOUT_DEPLOYMENTS_URL}/{task_id}",
        request_label=f"About deployment status lookup for task {task_id}",
        timeout_seconds=options.http_timeout_seconds,
        network_error_retryable=True,
        non_retryable_statuses={404},
    )
    return response.payload


def fetch_about_deployment_logs(task_id: str, options: AboutDeploymentOptions) -> list[dict[str, Any]]:
    response = request_json(
        "GET",
        f"{ABOUT_DEPLOYMENTS_URL}/{task_id}/logs",
        request_label=f"About deployment logs lookup for task {task_id}",
        timeout_seconds=options.http_timeout_seconds,
        network_error_retryable=True,
        non_retryable_statuses={404},
    )
    logs = response.payload.get("logs")
    if not isinstance(logs, list):
        return []
    return [item for item in logs if isinstance(item, dict)]


def summarize_deployment_logs(logs: list[dict[str, Any]], limit: int = 6) -> str:
    tail = logs[-limit:]
    formatted: list[str] = []
    for item in tail:
        stage = str(item.get("stage", "unknown")).strip() or "unknown"
        stream = str(item.get("stream", "system")).strip() or "system"
        message = str(item.get("message", "")).strip()
        if not message:
            continue
        formatted.append(f"[{stage}/{stream}] {message}")
    return " | ".join(formatted)


def wait_for_about_deployment(task_id: str, options: AboutDeploymentOptions) -> dict[str, Any]:
    deadline = time.monotonic() + options.poll_timeout_seconds

    while True:
        detail = fetch_about_deployment_detail(task_id, options)
        task = detail.get("task")
        if not isinstance(task, dict):
            raise DeploymentError(f"About deployment task {task_id} returned no task payload.", retryable=True)

        status = str(task.get("status", "")).strip()
        if status == "succeeded":
            return detail
        if status == "failed":
            error = task.get("error")
            error_message = extract_error_message({"error": error}) or "unknown deployment error"
            current_stage = str(task.get("currentStage", "")).strip() or "unknown"
            log_summary = ""
            try:
                logs = fetch_about_deployment_logs(task_id, options)
            except DeploymentError:
                logs = []
            else:
                detail["logs"] = logs
                log_summary = summarize_deployment_logs(logs)
            message = f"About deployment task {task_id} failed at stage {current_stage}: {error_message}"
            if log_summary:
                message = f"{message}. Recent logs: {log_summary}"
            raise DeploymentError(message, retryable=True)

        if time.monotonic() >= deadline:
            current_stage = str(task.get("currentStage", "")).strip() or "unknown"
            raise DeploymentError(
                f"About deployment task {task_id} did not finish before timeout while in stage {current_stage}.",
                retryable=True,
            )
        time.sleep(options.poll_interval_seconds)


def resolve_deployed_listing_urls(site_domain: str, result_payload: dict[str, Any] | None) -> dict[str, str]:
    urls = listing_urls_for_host(site_domain)
    if not isinstance(result_payload, dict):
        return urls

    page_urls = result_payload.get("pageUrls")
    if not isinstance(page_urls, dict):
        return urls

    for raw_key, raw_url in page_urls.items():
        candidate = str(raw_url).strip()
        if not candidate.startswith("http"):
            continue
        key = str(raw_key).strip().lower()
        path = urlparse(candidate).path.lower()
        if key in {"index", "index.html"} or path.endswith("/index.html"):
            urls["index"] = candidate
        elif key in {"privacy", "privacy.html", "privacypolicy", "privacypolicy.html"} or path.endswith(
            "/privacypolicy.html"
        ):
            urls["privacy"] = candidate
        elif key in {"terms", "terms&conditions", "terms&conditions.html", "termsconditions", "termsconditions.html"} or path.endswith(
            "/terms&conditions.html"
        ):
            urls["terms"] = candidate
        elif key in {"support", "support.html"} or path.endswith("/support.html"):
            urls["support"] = candidate
    return urls


def deploy_about_site(
    app_name: str,
    site_dir: Path,
    options: AboutDeploymentOptions,
) -> dict[str, Any]:
    # Deployment must query the sub-domain service with the inspected app_name only.
    # If lookup fails, generation keeps placeholder URLs and skips deployment.
    site_domain = fetch_live_h5_domain(app_name, options)

    with tempfile.TemporaryDirectory(prefix="about_deploy_") as temp_dir:
        bundle_path = build_site_bundle(site_dir, Path(temp_dir) / "site_bundle.zip")
        last_error: DeploymentError | None = None

        for attempt in range(1, options.max_attempts + 1):
            try:
                created = create_about_deployment_task(site_domain, bundle_path, options)
                task = created.get("task")
                if not isinstance(task, dict):
                    raise DeploymentError("About deployment creation returned no task payload.", retryable=True)
                task_id = str(task.get("taskId", "")).strip()
                if not task_id:
                    raise DeploymentError("About deployment creation returned an empty taskId.", retryable=True)

                detail = wait_for_about_deployment(task_id, options)
                result_payload = detail.get("result") if isinstance(detail.get("result"), dict) else None
                urls = resolve_deployed_listing_urls(site_domain, result_payload)
                task_payload = detail.get("task") if isinstance(detail.get("task"), dict) else {}
                return {
                    "attempts": attempt,
                    "site_domain": site_domain,
                    "task_id": task_id,
                    "status": str(task_payload.get("status", "succeeded")).strip() or "succeeded",
                    "current_stage": str(task_payload.get("currentStage", "finalizing")).strip() or "finalizing",
                    "published_base_url": (
                        str(result_payload.get("publishedBaseUrl", "")).strip() if isinstance(result_payload, dict) else ""
                    ),
                    "commit_sha": str(result_payload.get("commitSha", "")).strip() if isinstance(result_payload, dict) else "",
                    "pushed": bool(result_payload.get("pushed")) if isinstance(result_payload, dict) else False,
                    "deploy_folder": (
                        str(result_payload.get("deployFolder", "")).strip()
                        if isinstance(result_payload, dict)
                        else str(task_payload.get("deployFolder", "")).strip()
                    ),
                    "urls": urls,
                    "published_url_verification": {
                        "status": "skipped",
                        "reason": "deployment_task_succeeded",
                    },
                }
            except DeploymentError as exc:
                last_error = exc
                if not exc.retryable or attempt >= options.max_attempts:
                    if attempt >= options.max_attempts and exc.retryable:
                        raise DeploymentError(
                            f"About deployment failed after {attempt} attempts: {exc}",
                            retryable=False,
                            reason=exc.reason,
                        ) from exc
                    raise
                time.sleep(min(options.poll_interval_seconds * attempt, 5.0))

    if last_error is not None:
        raise last_error
    raise DeploymentError("About deployment did not run.", retryable=False)


def pick_logo_source(app_root: Path, inspect_payload: dict[str, Any]) -> Path | None:
    root = app_root.resolve()
    candidates: list[Path] = [
        app_root / "assets" / "logo.png",
        app_root / "ios" / "Runner" / "assets" / "logo.png",
    ]
    candidates.extend(app_root / str(rel) for rel in inspect_payload.get("logo_candidates", []))
    candidates.append(app_root / ".codex-work" / "development-brand.png")
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or root not in resolved.parents:
            continue
        seen.add(resolved)
        if resolved.is_file() and is_valid_image_file(resolved):
            return resolved
    return None


def copy_logo(source: Path, destination: Path) -> None:
    if not is_valid_image_file(source):
        raise RuntimeError(f"invalid_logo_source:{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as handle:
        is_png = handle.read(8) == b"\x89PNG\r\n\x1a\n"
    if is_png:
        shutil.copyfile(source, destination)
    else:
        subprocess.run(
            ["sips", "-s", "format", "png", str(source), "--out", str(destination)],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    if not is_valid_image_file(destination):
        raise RuntimeError(f"invalid_logo_output:{destination}")


def format_elapsed_duration(seconds: float) -> str:
    safe_seconds = max(0.0, float(seconds))
    if safe_seconds < 60:
        return f"{safe_seconds:.1f}s"

    minutes, remaining_seconds = divmod(safe_seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {remaining_seconds:.1f}s"

    hours, remaining_minutes = divmod(int(minutes), 60)
    return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"


def format_elapsed_duration_zh(seconds: float) -> str:
    safe_seconds = max(0.0, float(seconds))
    if safe_seconds < 60:
        return f"{safe_seconds:.1f} 秒"

    minutes, remaining_seconds = divmod(safe_seconds, 60)
    if minutes < 60:
        return f"{int(minutes)} 分 {remaining_seconds:.1f} 秒"

    hours, remaining_minutes = divmod(int(minutes), 60)
    return f"{hours} 小时 {remaining_minutes} 分 {remaining_seconds:.1f} 秒"


def deployment_completion_phrase(summary: dict[str, Any], *, language: str) -> str:
    deployment = summary.get("deployment")
    if not isinstance(deployment, dict):
        return "About deployment was not enabled." if language == "en" else "About 部署未启用。"

    status = str(deployment.get("status", "")).strip()
    if status == "succeeded":
        published_url = str(deployment.get("published_base_url", "")).strip()
        if not published_url:
            urls = deployment.get("urls", {})
            if isinstance(urls, dict):
                published_url = str(urls.get("index", "")).strip()
        if language == "en":
            return f"About deployment succeeded: {published_url}" if published_url else "About deployment succeeded."
        return f"About 部署成功：{published_url}" if published_url else "About 部署成功。"

    reason = str(deployment.get("reason", "")).strip() or status or "unknown"
    if language == "en":
        return f"About deployment did not complete: {reason}."
    return f"About 部署未完成：{reason}。"


def build_completion_summary(summary: dict[str, Any], total_timing: dict[str, Any], *, mode: str) -> dict[str, str]:
    app_name = str(summary.get("app_name", "App")).strip() or "App"
    category = str(summary.get("category_label") or summary.get("category") or "").strip()
    output_path = "AppListing/"
    failures = summary.get("failures", [])
    failure_count = len(failures) if isinstance(failures, list) else 0
    human = str(total_timing.get("human", ""))
    human_zh = str(total_timing.get("human_zh", ""))

    if mode == "style_selection":
        status_zh = f"已完成 {app_name} AppListing 描述风格选择。"
        status_en = f"Completed AppListing description-style selection for {app_name}."
    else:
        deployed = isinstance(summary.get("deployment"), dict) and summary["deployment"].get("status") == "succeeded"
        action_zh = "AppListing 生成并部署 About 页" if deployed else "AppListing 生成"
        action_en = "AppListing generation and About deployment" if deployed else "AppListing generation"
        if failure_count:
            status_zh = f"已完成 {app_name} {action_zh}，但存在 {failure_count} 个问题。"
            status_en = f"Completed {action_en} for {app_name} with {failure_count} issue(s)."
        else:
            status_zh = f"已完成 {app_name} {action_zh}。"
            status_en = f"Completed {action_en} for {app_name}."

    category_zh = f"分类：{category}；" if category else ""
    category_en = f"Category: {category}; " if category else ""
    deployment_zh = deployment_completion_phrase(summary, language="zh") if mode != "style_selection" else ""
    deployment_en = deployment_completion_phrase(summary, language="en") if mode != "style_selection" else ""

    return {
        "zh": f"{status_zh}总耗时 {human_zh}。{category_zh}输出：{output_path}；{deployment_zh}".rstrip("；"),
        "en": f"{status_en} Total time: {human}. {category_en}Output: {output_path}; {deployment_en}".rstrip("; "),
    }


def attach_total_timing_and_completion_summaries(
    summaries: list[dict[str, Any]],
    total_elapsed_seconds: float,
    *,
    mode: str,
) -> None:
    success_count = sum(1 for item in summaries if not item.get("failures"))
    total_timing = {
        "elapsed_seconds": round(max(0.0, float(total_elapsed_seconds)), 1),
        "human": format_elapsed_duration(total_elapsed_seconds),
        "human_zh": format_elapsed_duration_zh(total_elapsed_seconds),
        "target_count": len(summaries),
        "success_count": success_count,
        "failure_count": len(summaries) - success_count,
    }
    for summary in summaries:
        summary["total_timing"] = dict(total_timing)
        summary["completion_summary"] = build_completion_summary(summary, total_timing, mode=mode)


def write_runner_result(*, mode: str, exit_code: int, summaries: list[dict[str, Any]]) -> None:
    """Write the Runner-only machine result without changing normal CLI stdout."""
    raw_path = os.environ.get("IOS_APP_LISTING_RESULT_PATH", "").strip()
    if not raw_path:
        return
    target = Path(raw_path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    payload = {
        "protocolVersion": 1,
        "mode": mode,
        "exitCode": int(exit_code),
        "summaries": summaries,
    }
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)


def default_theme_label_from_hint(hint: AppHint) -> str:
    suffix = hint.index_title_suffix.strip()
    if suffix and suffix != "Overview":
        return suffix

    identity_blob = f"{hint.identity} {hint.experience} {hint.social_noun}".lower()
    if "umbrella" in identity_blob:
        return "Umbrella Community"
    if "travel" in identity_blob:
        return "Travel Companion"
    if "photo" in identity_blob or "visual" in identity_blob:
        return "Photo Experience"
    if "community" in identity_blob:
        return "Community Lifestyle"
    if "utility" in identity_blob:
        return "Utility Overview"
    return "Product Experience"


def theme_hint_payload(hint: AppHint) -> dict[str, Any]:
    return {
        "identity": hint.identity,
        "experience": hint.experience,
        "keywords": list(hint.keywords),
        "currency": hint.currency,
        "index_title_suffix": hint.index_title_suffix,
        "social_noun": hint.social_noun,
        "post_label": hint.post_label,
    }


def build_classification(
    inspect_payload: dict[str, Any],
    hint: AppHint,
    category: str,
    archetype: str,
    capabilities: list[str],
    theme_label: str | None = None,
) -> dict[str, Any]:
    privacy = inspect_payload.get("privacy_signals", {})
    capability_scores = capability_score_map(inspect_payload)
    active_summary = ", ".join(
        f"{name}={capability_scores.get(name, 0.0):.1f}" for name in capabilities
    )
    reasoning_parts = [
        f"Primary category is {category} because the highest-scoring archetype is {ARCHETYPE_LABELS.get(archetype, archetype)}.",
        f"Active capability evidence: {active_summary}.",
        f"The app evidence supports {hint.experience}.",
    ]
    if theme_label:
        reasoning_parts.append(f"Theme focus is {theme_label}.")
    if privacy.get("ai_features"):
        reasoning_parts.append("AI-related privacy signals are present and must be reflected in legal pages.")
    resolved_theme = theme_label or default_theme_label_from_hint(hint)
    return {
        "category": category,
        "archetype": archetype,
        "theme": resolved_theme,
        "theme_hint": theme_hint_payload(hint),
        "capabilities": capabilities,
        "claimable_features": capabilities,
        "confidence": "high" if len(capabilities) >= 3 else "medium",
        "reasoning": " ".join(reasoning_parts),
    }


def build_intro(
    app_name: str,
    subtitle: str,
    category_label: str,
    description: str,
    keywords: list[str],
    urls: dict[str, str],
    has_ugc: bool,
    has_chat: bool,
) -> str:
    return "\n".join(
        [
            f"# {app_name} — App Store Description",
            "",
            "## App Name",
            app_name,
            "",
            "## Sub Title",
            subtitle,
            "",
            "## Category",
            category_label,
            "",
            "## Description",
            description,
            "",
            "## Keywords",
            ",".join(keywords),
            "",
            "## Support URL",
            urls["support"],
            "",
            "## Terms of Service URL",
            urls["terms"],
            "",
            "## All URL",
            "==================================================",
            f"首页: {urls['index']}",
            f"隐私政策: {urls['privacy']}",
            f"用户协议: {urls['terms']}",
            f"Support: {urls['support']}",
            "==================================================",
            "",
            "## UGC",
            yes_no(has_ugc),
            "",
            "## Chat",
            yes_no(has_chat),
            "",
            "## Copyright",
            f"© {date.today().year} {app_name}. All rights reserved.",
            "",
        ]
    )


def summarize_hosts(hosts: list[str], listing_host: str) -> str:
    filtered = [
        host
        for host in hosts
        if host
        and host != listing_host
        and "$" not in host
        and "{" not in host
        and "}" not in host
        and not host.endswith(".png")
        and "tile.openstreetmap.org" not in host
    ]
    if not filtered:
        return "third-party AI service providers or external model providers we use for the feature"
    return ", ".join(sorted(set(filtered)))


def ai_disclosure_required(inspect_payload: dict[str, Any]) -> bool:
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


def translation_disclosure_required(inspect_payload: dict[str, Any]) -> bool:
    translation_signals = inspect_payload.get("translation_signals", {})
    if isinstance(translation_signals, dict) and translation_signals:
        if not translation_signals.get("active"):
            return False
        return bool(translation_signals.get("disclosure_required", translation_signals.get("user_reachable", True)))
    return bool({"translate_text", "translate_voice"} & active_capabilities(inspect_payload))


def face_data_review_disclosure_required(inspect_payload: dict[str, Any]) -> bool:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return False
    profile = ai_signals.get("review_profile", {})
    if not isinstance(profile, dict) or not profile.get("needs_face_data_clauses"):
        return False
    return ai_disclosure_required(inspect_payload) or translation_disclosure_required(inspect_payload)


def ai_preview_profile(inspect_payload: dict[str, Any]) -> dict[str, Any]:
    ai_signals = inspect_payload.get("ai_signals", {})
    if not isinstance(ai_signals, dict):
        return {}
    profile = ai_signals.get("review_profile", {})
    if not isinstance(profile, dict):
        return {}
    if profile.get("needs_face_data_clauses"):
        return profile if face_data_review_disclosure_required(inspect_payload) else {}
    if not ai_disclosure_required(inspect_payload):
        return {}
    return profile


def face_data_workflow_kind(inspect_payload: dict[str, Any] | None = None) -> str:
    profile = ai_preview_profile(inspect_payload or {})
    if not isinstance(profile, dict):
        return "preview"
    return str(profile.get("workflow_kind", "preview")).strip() or "preview"


def summarize_ai_recipients(ai_signals: dict[str, Any], listing_host: str) -> str:
    providers = [str(item).strip() for item in ai_signals.get("providers", []) if str(item).strip()]
    host_candidates = [
        host
        for host in ai_signals.get("network_hosts", [])
        if host
        and host != listing_host
        and "$" not in host
        and "{" not in host
        and "}" not in host
    ]
    ai_host_markers = ("openai", "anthropic", "gemini", "replicate", "huggingface", "dashscope", "aliyuncs")
    ai_hosts = [host for host in host_candidates if any(marker in host for marker in ai_host_markers)]
    host_text = ", ".join(sorted(set(ai_hosts or host_candidates)))
    if providers and host_text:
        return f"{providers[0]} ({host_text})"
    if providers:
        return providers[0]
    if host_text:
        return host_text
    return "third-party AI service providers or external model providers we use for the feature"


def preview_input_phrase(preview_profile: dict[str, Any]) -> str:
    if preview_profile.get("reference_image"):
        return "the selected user photo and the selected reference style image"
    return "the selected user photo"


def build_privacy_sections(
    app_name: str,
    hint: AppHint,
    inspect_payload: dict[str, Any],
    active: set[str],
    urls: dict[str, str],
) -> list[dict[str, Any]]:
    return renumber_sections(build_evidenced_privacy(app_name, inspect_payload, active))


def build_terms_sections(
    app_name: str,
    hint: AppHint,
    inspect_payload: dict[str, Any],
    active: set[str],
) -> list[dict[str, Any]]:
    return renumber_sections(build_evidenced_terms(app_name, inspect_payload, active))


def build_feature_cards(
    hint: AppHint,
    category: str,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any],
) -> list[dict[str, str]]:
    preview_profile = ai_preview_profile(inspect_payload)
    has_ai_preview_review_profile = bool(preview_profile.get("needs_face_data_clauses"))
    face_data_workflow = face_data_workflow_kind(inspect_payload)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    has_user_content = bool(inspect_payload.get("privacy_signals", {}).get("user_content"))
    if not has_user_content:
        if category == "Photo & Video":
            cards = [
                {
                    "title": "Overlay Editing",
                    "body": "Import or capture a photo, choose from the available overlay styles, and adjust color, fade, and thickness for the result you want.",
                },
                {
                    "title": "Saved Edits and Notes",
                    "body": "Keep edited photos in your saved gallery and attach typed or dictated notes when you want to revisit details later.",
                },
            ]
            if has_iap and hint.currency:
                cards.append(
                    {
                        "title": "Optional Purchases",
                        "body": f"Choose optional {hint.currency} purchases when you want more export access after the included free saves are used.",
                    }
                )
            else:
                cards.append(
                    {
                        "title": "Export to Photos",
                        "body": "Save finished edits back to Photos when you are ready to keep the result outside the app.",
                    }
                )
            return cards
        if category == "Travel":
            return [
                {
                    "title": "Places and Context",
                    "body": "Keep nearby places, saved stops, and location-aware details close when you want more context around where something happened.",
                },
                {
                    "title": "Translation Tools" if has_translation else "Saved Trip Details",
                    "body": (
                        "Use text or voice translation when you need extra help across languages while moving between locations."
                        if has_translation
                        else "Revisit saved travel details and stay organized across repeat visits without a heavy planning flow."
                    ),
                },
                {
                    "title": "Support and Access",
                    "body": "Keep permissions, support links, and service details easy to review whenever you return to the app.",
                },
            ]
        if category in {"Business", "Productivity"}:
            return [
                {
                    "title": "Organized Workflows",
                    "body": "Keep tasks, work access, and repeat actions organized so the core workflow stays easy to revisit.",
                },
                {
                    "title": "Saved Progress",
                    "body": "Return to saved progress, saved context, and the work that still needs your attention.",
                },
                {
                    "title": "Optional Purchases" if has_iap and hint.currency else "Support and Access",
                    "body": (
                        f"Use optional {hint.currency} purchases when you want more access at your own pace."
                        if has_iap and hint.currency
                        else "Keep support links, service details, and service terms close when you need them."
                    ),
                },
            ]
        if category == "Education":
            return [
                {
                    "title": "Guided Learning",
                    "body": "Move through lessons, guided practice, and structured learning steps without losing your place.",
                },
                {
                    "title": "Saved Progress",
                    "body": "Return to saved progress, course context, and the parts of the learning path you want to finish next.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep support details, service rules, and repeat-use guidance easy to review across repeat visits.",
                },
            ]
        if category == "Graphics & Design":
            return [
                {
                    "title": "Creative Tools",
                    "body": "Use design-focused tools to shape visual work, templates, and polished creative output inside one clear flow.",
                },
                {
                    "title": "Saved Projects",
                    "body": "Keep project progress, visual drafts, and reusable design context close when you come back later.",
                },
                {
                    "title": "Optional Purchases" if has_iap and hint.currency else "Support and Access",
                    "body": (
                        f"Choose optional {hint.currency} purchases when you want more creation or export access."
                        if has_iap and hint.currency
                        else "Keep support routes, service details, and service terms available when you need them."
                    ),
                },
            ]
        if category == "Health & Fitness":
            return [
                {
                    "title": "Routine Tracking",
                    "body": "Keep routines, repeat sessions, and personal progress close so the experience stays easy to reuse over time.",
                },
                {
                    "title": "Saved Progress",
                    "body": "Return to the habits, wellbeing details, and progress markers you want to keep moving forward.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep permissions, service details, and support details available when you need to review them.",
                },
            ]
        if category == "Lifestyle":
            return [
                {
                    "title": "Daily Routines",
                    "body": "Keep routines, inspiration, and personal preferences in one place for quick everyday return visits.",
                },
                {
                    "title": "Saved Preferences",
                    "body": "Return to the details, picks, and saved context that help the experience feel more personal over time.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep permissions, support details, and repeat-use details close when you need them.",
                },
            ]
        if category in {"Music", "Entertainment"}:
            return [
                {
                    "title": "Browse and Return",
                    "body": "Move through media, saved picks, and repeat visits with a structure that stays easy to scan.",
                },
                {
                    "title": "Saved Favorites",
                    "body": "Keep playlists, episodes, or other saved picks close when you want to come back later.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep service details, saved picks, and support links available when you need them.",
                },
            ]
        if category == "Food & Drink":
            return [
                {
                    "title": "Menus and Recipes",
                    "body": "Browse food and drink ideas, menu details, or recipe context without losing the thread of what you want to revisit.",
                },
                {
                    "title": "Saved Picks",
                    "body": "Return to saved places, ingredients, or dining ideas when you want to make a quicker decision later.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep service details, support routes, and saved picks close when you need them.",
                },
            ]
        if category == "Navigation":
            return [
                {
                    "title": "Routes and Guidance",
                    "body": "Keep directions, destination context, and route-aware tools close while you move between places.",
                },
                {
                    "title": "Saved Destinations",
                    "body": "Return to saved places and repeat routes when you want a faster start next time.",
                },
                {
                    "title": "Location and Support",
                    "body": "Keep location permissions, support details, and service rules easy to review when you need them.",
                },
            ]
        if category == "Weather":
            return [
                {
                    "title": "Forecasts and Alerts",
                    "body": "Review local conditions, forecast changes, and weather alerts in a flow that stays easy to check quickly.",
                },
                {
                    "title": "Saved Locations",
                    "body": "Keep saved locations close so it is easy to return to the weather details that matter most to you.",
                },
                {
                    "title": "Permissions and Support",
                    "body": "Keep location permissions, support links, and service details available whenever you need them.",
                },
            ]
        if category == "Reference":
            return [
                {
                    "title": "Structured Lookup",
                    "body": "Search for definitions, explanations, or reference details in a flow that stays clear and easy to revisit.",
                },
                {
                    "title": "Saved Context",
                    "body": "Return to saved terms, lookup history, or organized reference context when you need it again.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep support details, saved context, and service rules close when you need them.",
                },
            ]
        if category == "Sports":
            return [
                {
                    "title": "Scores and Standings",
                    "body": "Keep scores, team context, and sports details easy to scan when you want a quick update.",
                },
                {
                    "title": "Saved Teams",
                    "body": "Return to the teams, leagues, or sports details you want to keep following over time.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep support routes, saved team details, and service details available when you need them.",
                },
            ]
        if category == "News":
            return [
                {
                    "title": "Headlines and Stories",
                    "body": "Browse headlines, story context, and timely updates without turning the experience into a technical walkthrough.",
                },
                {
                    "title": "Saved Reading",
                    "body": "Return to saved stories, followed topics, and the updates you want to keep close.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep service details, support links, and saved reading details close when you need them.",
                },
            ]
        if category == "Finance":
            return [
                {
                    "title": "Balance and Access",
                    "body": "Keep balance-related tools, saved payment details, and repeat finance actions organized in one clear flow.",
                },
                {
                    "title": "Saved Records",
                    "body": "Return to the payment, balance, or saved details you want to keep close over time.",
                },
                {
                    "title": "Optional Purchases" if has_iap and hint.currency else "Support and Access",
                    "body": (
                        f"Use optional {hint.currency} purchases when you choose to unlock more access."
                        if has_iap and hint.currency
                        else "Keep support routes, service details, and saved payment details easy to review."
                    ),
                },
            ]
        if category == "Utilities":
            return [
                {
                    "title": "Everyday Tools",
                    "body": "Use practical tools that stay easy to reopen whenever you need a quick result.",
                },
                {
                    "title": "Saved Preferences",
                    "body": "Keep saved settings, repeat-use context, and the details you return to most often close across visits.",
                },
                {
                    "title": "Support and Access",
                    "body": "Keep support links, service details, and repeat-use guidance close when you need them.",
                },
            ]
        cards = [
            {
                "title": "Core Access",
                "body": f"Stay close to {hint.experience} in a flow that remains easy to revisit across return visits.",
            },
            {
                "title": "Saved Context",
                "body": "Keep progress, saved context, and the details that matter most close across return visits.",
            },
        ]
        cards.append(
            {
                "title": "Optional Purchases" if has_iap and hint.currency else "Support and Access",
                "body": (
                    f"Use optional {hint.currency} purchases when you choose to unlock more access."
                    if has_iap and hint.currency
                    else "Keep support routes, permissions, and service details available when you need them."
                ),
            }
        )
        return cards
    cards = [
        {
            "title": "Community Feed",
            "body": f"Browse {hint.social_noun} in a polished stream that keeps new inspiration easy to revisit.",
        },
        {
            "title": "Profiles and Publishing",
            "body": f"Keep your own profile, publish a fresh {hint.post_label}, and return to the updates that matter most to you.",
        },
    ]
    if has_ai_preview_review_profile and face_data_workflow == "translation_face_visibility":
        cards.append(
            {
                "title": "Image Translation",
                "body": "Choose a photo with readable text, review the consent prompt, and get translated results for labels, signs, or captions inside the app.",
            }
        )
    elif has_ai_preview_review_profile:
        cards.append(
            {
                "title": "AI Preview",
                "body": "Choose a photo, review the consent prompt, generate a preview result, and decide whether to save the finished image to Photos.",
            }
        )
    if category == "Travel":
        cards.append(
            {
                "title": "Translation and Places" if has_translation else "Places and Discovery",
                "body": (
                    "Use text or voice translation and add place context when you want to keep ideas moving across languages and locations."
                    if has_translation
                    else "Add place context and keep nearby discoveries close when you want more context around where something happened."
                ),
            }
        )
    elif has_chat:
        cards.append(
            {
                "title": "Private Conversations",
                "body": "Stay in touch with selected members when you want a more direct conversation around shared interests.",
            }
        )
    elif has_iap and hint.currency:
        cards.append(
            {
                "title": "Optional Purchases",
                "body": f"Choose optional {hint.currency} purchases if you want to continue with additional access at your own pace.",
            }
        )
    else:
        cards.append(
            {
                "title": "Safety Controls",
                "body": "Use reporting and blocking tools when you need a cleaner, more comfortable experience.",
            }
        )
    return cards


def build_members_can_do(
    hint: AppHint,
    category: str,
    active: set[str],
    has_iap: bool,
    inspect_payload: dict[str, Any],
) -> list[str]:
    preview_profile = ai_preview_profile(inspect_payload)
    has_ai_preview_review_profile = bool(preview_profile.get("needs_face_data_clauses"))
    face_data_workflow = face_data_workflow_kind(inspect_payload)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    has_user_content = bool(inspect_payload.get("privacy_signals", {}).get("user_content"))
    if not has_user_content:
        if category == "Photo & Video":
            items = [
                "Import a photo from Photos or capture a new one to start an edit.",
                "Apply overlay styles and adjust color, fade, and line thickness to shape the final look.",
            ]
            if has_iap and hint.currency:
                items.append(
                    f"Save edits, add typed or dictated notes, export to Photos, and use optional {hint.currency} purchases when you want more photo exports."
                )
            else:
                items.append("Save edits, add typed or dictated notes, and export to Photos when you are ready.")
            return items
        if category == "Travel":
            return [
                "Keep nearby places, travel context, and saved details close when location adds useful context to what you are doing.",
                (
                    "Use text or voice translation when you need practical help across languages while moving between places."
                    if has_translation
                    else "Return to saved travel details and keep the core experience easy to revisit over time."
                ),
                "Review permissions, support details, and service rules whenever you need them.",
            ]
        if category in {"Business", "Productivity"}:
            return [
                "Keep tasks, work access, and repeat actions organized in one place.",
                "Return to saved progress, saved context, and the workflow details you still need to review.",
                (
                    f"Use optional {hint.currency} purchases when you choose to unlock more access."
                    if has_iap and hint.currency
                    else "Keep support details, service rules, and repeat-use guidance easy to review."
                ),
            ]
        if category == "Education":
            return [
                "Move through lessons, guided practice, and structured learning steps without losing your place.",
                "Return to saved progress, course context, and the next part of the learning path you want to finish.",
                "Keep support details, repeat-use guidance, and service rules easy to review across repeat visits.",
            ]
        if category == "Graphics & Design":
            return [
                "Use visual creation tools, templates, and editing controls inside one clear design flow.",
                "Return to saved projects, reusable drafts, and the design context you want to keep close.",
                (
                    f"Choose optional {hint.currency} purchases when you want more creation or export access."
                    if has_iap and hint.currency
                    else "Keep support details, service rules, and repeat-use guidance available when you need them."
                ),
            ]
        if category == "Health & Fitness":
            return [
                "Keep routines, repeat sessions, and progress markers easy to revisit over time.",
                "Return to the habits, wellbeing details, and saved context you want to keep moving forward.",
                "Review permissions, support details, and service rules whenever you need them.",
            ]
        if category == "Lifestyle":
            return [
                "Keep daily routines, inspiration, and personal preferences in one place for quick return visits.",
                "Return to saved details and the personal context that helps the experience feel more tailored over time.",
                "Keep support details, permissions, and repeat-use guidance easy to review whenever you need them.",
            ]
        if category in {"Music", "Entertainment"}:
            return [
                "Browse media, saved picks, and repeat visits in a structure that stays easy to scan.",
                "Return to playlists, episodes, or other saved favorites when you want to continue later.",
                "Keep service details, support links, and saved picks available when you need them.",
            ]
        if category == "Food & Drink":
            return [
                "Browse menus, recipes, or dining ideas without losing the thread of what you want to revisit.",
                "Return to saved places, ingredients, or food picks when you want a quicker decision later.",
                "Keep support details, service rules, and saved picks close when you need them.",
            ]
        if category == "Navigation":
            return [
                "Review routes, destination context, and location-aware guidance when you need help moving between places.",
                "Return to saved destinations and repeat routes when you want a faster start next time.",
                "Keep location permissions, support details, and service rules easy to review.",
            ]
        if category == "Weather":
            return [
                "Check local conditions, forecasts, and alerts in a flow that stays easy to review quickly.",
                "Return to saved locations when you want weather details for the places you check most often.",
                "Keep location permissions, support links, and service details close when you need them.",
            ]
        if category == "Reference":
            return [
                "Look up definitions, explanations, or other reference details without losing your place.",
                "Return to saved terms, lookup history, and the reference context you want to revisit.",
                "Keep support details, service rules, and saved context close when you need them.",
            ]
        if category == "Sports":
            return [
                "Check scores, standings, and sports details in a flow that stays easy to scan.",
                "Return to saved teams, leagues, or sports context you want to follow over time.",
                "Keep support details, saved team details, and service rules easy to review when needed.",
            ]
        if category == "News":
            return [
                "Browse headlines, story context, and timely updates without a cluttered reading flow.",
                "Return to saved stories, followed topics, and the updates you want to keep close.",
                "Keep service details, support links, and saved reading details available when you need them.",
            ]
        if category == "Finance":
            return [
                "Keep balance-related tools, saved payment details, and repeat finance actions organized in one place.",
                "Return to the payment, balance, or saved details you want to keep close over time.",
                (
                    f"Use optional {hint.currency} purchases when you choose to unlock more access."
                    if has_iap and hint.currency
                    else "Keep support details, service rules, and payment details easy to review."
                ),
            ]
        if category == "Utilities":
            return [
                "Use practical tools that stay easy to reopen whenever you need a quick result.",
                "Return to saved preferences, repeat-use context, and the details that matter most.",
                "Keep support links, service details, and repeat-use guidance close when you need them.",
            ]
        items = [
            f"Stay close to {hint.experience} in a flow that remains easy to revisit.",
            "Return to saved progress, saved context, and the details you want to keep close over time.",
        ]
        items.append(
            f"Use optional {hint.currency} purchases when you choose to unlock more access."
            if has_iap and hint.currency
            else "Keep support details, service rules, and repeat-use guidance easy to review."
        )
        return items
    items = [
        f"Browse {hint.social_noun} and keep track of the ideas you want to revisit.",
        f"Maintain a personal profile and publish a new {hint.post_label} when you want to share something of your own.",
    ]
    if has_ai_preview_review_profile and face_data_workflow == "translation_face_visibility":
        items.append("Choose a photo with readable text, review the consent prompt, and receive translated label or caption results inside the app.")
    elif has_ai_preview_review_profile:
        items.append("Choose a photo, request AI Preview, review the generated result, and optionally save the finished image to Photos.")
    elif category == "Travel":
        items.append(
            "Translate text or voice and attach place context when you need practical help while moving between locations."
            if has_translation
            else "Attach place context and keep nearby details available when location adds useful context to what you share."
        )
    elif has_chat:
        items.append("Move from discovery into direct conversation with people you want to hear from again.")
    elif has_iap and hint.currency:
        items.append(f"Use optional {hint.currency} purchases when you choose to unlock more access.")
    else:
        items.append("Use built-in reporting and blocking tools to manage unwanted behavior.")
    return items


def build_faq_items(
    app_name: str,
    hint: AppHint,
    active: set[str],
    has_iap: bool,
    has_user_content: bool,
    inspect_payload: dict[str, Any],
) -> list[dict[str, str]]:
    support_email = str(inspect_payload.get("support_email") or "").strip() if inspect_payload.get("support_email_source") == "explicit" else ""
    preview_profile = ai_preview_profile(inspect_payload)
    has_ai_preview_review_profile = bool(preview_profile.get("needs_face_data_clauses"))
    face_data_workflow = face_data_workflow_kind(inspect_payload)
    has_chat = has_chat_capability(active, inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    if not has_user_content:
        items = [
            {
                "title": f"How do I start a new edit in {app_name}?",
                "body": "Open the editor, choose a photo from Photos or capture a new one with the camera, and then select the overlay style you want to use.",
            },
            {
                "title": "How do I save notes or export a finished photo?",
                "body": "Save the edit to your in-app gallery when you want to keep working on it later, add a typed or dictated note from the saved-details view, and use Export to Photos when you are ready to place the image in your photo library.",
            },
            {
                "title": "Why does the app request camera, photo-library, microphone, or photo-saving access?",
                "body": "Those permissions are requested only for user-initiated actions such as capturing a new photo, importing an image, dictating an edit note, or saving an exported photo back to Photos.",
            },
        ]
        if has_iap:
            items.append(
                {
                    "title": (
                        f"What if my {hint.currency} purchase does not appear?"
                        if hint.currency
                        else "What if my purchase does not appear?"
                    ),
                    "body": "Give the app a moment to refresh and review the purchase details shown in the app." if not support_email else "Give the app a moment to refresh, try the restore flow if it is available, and contact support if the balance still does not update.",
                }
            )
        if has_translation:
            items.append(
                {
                    "title": "How do translation tools work?",
                    "body": "Start the text or voice translation feature, provide the content you want translated, and wait for the processed result to appear before using it further.",
                }
            )
        return items
    items: list[dict[str, str]] = []
    if has_profile_capability(active):
        items.append(
            {
                "title": f"How do I update my profile in {app_name}?",
                "body": "Open your profile area, edit the details you want to change, and save the update once everything looks right.",
            }
        )
    if has_publish_capability(active):
        items.append(
            {
                "title": f"How can I publish a new {hint.post_label}?",
                "body": f"Use the publishing flow inside the app, select the media or text you want to share, review the result, and submit the {hint.post_label} when you are ready.",
            }
        )
    elif "feed" in active:
        items.append(
            {
                "title": f"How do I find or revisit {hint.social_noun}?",
                "body": "Browse the community feed, open the items you want to revisit, and use the in-app navigation to move back to the content that matters most to you.",
            }
        )
    if has_chat:
        items.append(
            {
                "title": "How do I start or manage a direct conversation?",
                "body": "Open the relevant profile or content flow, choose the direct-conversation option if it is available, and use the inbox area to revisit that conversation later.",
            }
        )
    items.append(
        {
            "title": "What if I need to report or block another member?",
            "body": "Use the report or block options available on the relevant profile or content item so the safety flow can review the issue, usually within 24 hours for objectionable-content or harassment reports, and help manage unwanted behavior.",
        }
    )
    if has_translation:
        items.append(
            {
                "title": "How do translation tools work?",
                "body": "Start the text or voice translation feature, provide the content you want translated, and wait for the processed result to appear before sharing it further.",
            }
        )
    if has_iap:
        items.append(
            {
                "title": (
                    f"What if my {hint.currency} purchase does not appear?"
                    if hint.currency
                    else "What if my purchase does not appear?"
                ),
                "body": "Give the app a moment to refresh and review the purchase details shown in the app." if not support_email else "Give the app a moment to refresh, try the restore flow if it is available, and contact support if the balance still does not update.",
            }
        )
    if has_ai_preview_review_profile and face_data_workflow == "translation_face_visibility":
        items.append(
            {
                "title": "How does AI-assisted image translation work?",
                "body": "Choose a photo with readable text, review the consent prompt, send the image for text extraction and translation, and review the translated result in the app.",
            }
        )
        items.append(
            {
                "title": "Why does the app request camera, photo-library, microphone, or speech-recognition access?",
                "body": "Those permissions are requested only for user-initiated actions such as capturing a label or styling photo, importing an image for translation or posting, or recording spoken notes for translation.",
            }
        )
    elif has_ai_preview_review_profile:
        items.append(
            {
                "title": "How does AI Preview work?",
                "body": "Choose a photo, review the consent prompt, generate the requested preview result, and decide whether to save the finished image to Photos after you review it.",
            }
        )
        items.append(
            {
                "title": "Why does the app request camera, photo-library, or add-to-library access?",
                "body": "Those permissions are requested only for user-initiated actions such as capturing a new photo, importing an image for AI Preview or posting, and saving a generated preview result back to Photos.",
            }
        )
    return items


def non_ugc_index_subtitle(app_name: str, category: str, has_translation: bool) -> str:
    if category == "Photo & Video":
        return f"A broad, evidence-based overview of how {app_name} handles saved edits, permissions, purchases, and support."
    if category == "Travel":
        return (
            f"A broad, evidence-based overview of how {app_name} handles location context, translation tools, permissions, and support."
            if has_translation
            else f"A broad, evidence-based overview of how {app_name} handles place-aware tools, permissions, and support."
        )
    if category in {"Business", "Productivity"}:
        return f"A broad, evidence-based overview of how {app_name} handles workflow access, saved progress, permissions, and support."
    if category == "Education":
        return f"A broad, evidence-based overview of how {app_name} handles lessons, saved progress, permissions, and support."
    if category == "Graphics & Design":
        return f"A broad, evidence-based overview of how {app_name} handles design projects, saved work, permissions, and support."
    if category == "Health & Fitness":
        return f"A broad, evidence-based overview of how {app_name} handles routines, progress context, permissions, and support."
    if category == "Lifestyle":
        return f"A broad, evidence-based overview of how {app_name} handles daily routines, saved preferences, permissions, and support."
    if category in {"Music", "Entertainment"}:
        return f"A broad, evidence-based overview of how {app_name} handles saved picks, permissions, and support."
    if category == "Food & Drink":
        return f"A broad, evidence-based overview of how {app_name} handles saved food picks, permissions, and support."
    if category == "Navigation":
        return f"A broad, evidence-based overview of how {app_name} handles location use, saved destinations, permissions, and support."
    if category == "Weather":
        return f"A broad, evidence-based overview of how {app_name} handles saved locations, permissions, forecast access, and support."
    if category == "Reference":
        return f"A broad, evidence-based overview of how {app_name} handles lookup access, saved context, permissions, and support."
    if category == "Sports":
        return f"A broad, evidence-based overview of how {app_name} handles scores, saved teams, and support."
    if category == "News":
        return f"A broad, evidence-based overview of how {app_name} handles reading access, saved stories, permissions, and support."
    if category == "Finance":
        return f"A broad, evidence-based overview of how {app_name} handles payment context, saved records, permissions, and support."
    if category == "Utilities":
        return f"A broad, evidence-based overview of how {app_name} handles everyday tools, saved preferences, permissions, and support."
    return f"A broad, evidence-based overview of how {app_name} handles saved context, permissions, support, and service rules."


def non_ugc_purpose(app_name: str, category: str, brand_identity_phrase: str, hint: AppHint, has_translation: bool) -> str:
    category_tail = {
        "Business": "a business workflow built for organized access, saved progress, and repeat work.",
        "Education": "a learning experience built for guided lessons, saved progress, and return visits.",
        "Entertainment": "a media experience built for browsing, saved picks, and easy return visits.",
        "Finance": "a finance utility built for saved payment context, balance details, and repeat visits.",
        "Food & Drink": "a food and drink experience built for browsing, saved picks, and light planning.",
        "Graphics & Design": "a design experience built for visual projects, saved work, and polished output.",
        "Health & Fitness": "a wellness experience built for routines, progress tracking, and steady repeat use.",
        "Lifestyle": "a lifestyle experience built for daily routines, saved preferences, and easy return visits.",
        "Music": "an audio experience built for listening, saved picks, and organized access.",
        "Navigation": "a route-focused utility built for destination guidance, saved places, and location-aware support.",
        "News": "a reading experience built for headlines, saved stories, and quick return visits.",
        "Photo & Video": "a photo editor built for quick adjustments, saved notes, and export-ready results.",
        "Productivity": "a workflow tool built for planning, saved progress, and repeat task management.",
        "Reference": "a lookup experience built for structured answers, saved context, and quick return visits.",
        "Sports": "a sports experience built for scores, team tracking, and quick return visits.",
        "Utilities": "a utility experience built for everyday tasks, saved preferences, and support.",
        "Weather": "a forecast-focused utility built for local conditions, saved locations, and timely updates.",
    }
    if category == "Travel":
        tail = (
            "a travel experience built for place-aware access, translated context, and repeat visits."
            if has_translation
            else "a travel experience built for place-aware access, saved details, and repeat visits."
        )
    else:
        tail = category_tail.get(category, "a focused product experience built for clear access, saved progress, and repeat use.")
    return f"{app_name} is {brand_identity_phrase} that brings together {hint.experience} in {tail}"


def non_ugc_members_intro(app_name: str, category: str, hint: AppHint, has_translation: bool, has_iap: bool) -> str:
    if category == "Travel":
        return (
            f"People can use {app_name} to revisit travel context, saved places, and optional translation tools when they need help across languages and locations."
            if has_translation
            else f"People can use {app_name} to revisit saved places, travel context, and repeat-use details without a heavy workflow."
        )
    if category in {"Business", "Productivity"}:
        return f"People can use {app_name} to keep work context, saved progress, and repeat actions organized across return visits."
    if category == "Education":
        return f"People can use {app_name} to move through lessons, return to saved progress, and keep the learning flow easy to revisit."
    if category == "Graphics & Design":
        return f"People can use {app_name} to revisit design work, saved project context, and polished creation tools without a cluttered workflow."
    if category == "Health & Fitness":
        return f"People can use {app_name} to keep routines, progress context, and repeat wellness actions close over time."
    if category == "Lifestyle":
        return f"People can use {app_name} to keep routines, inspiration, and saved preferences close across everyday return visits."
    if category in {"Music", "Entertainment"}:
        return f"People can use {app_name} to keep saved picks and repeat listening or viewing context close over time."
    if category == "Food & Drink":
        return f"People can use {app_name} to keep saved food picks, dining ideas, and repeat-use details close when they return."
    if category == "Navigation":
        return f"People can use {app_name} to keep route context, saved destinations, and location-aware guidance close when they need it."
    if category == "Weather":
        return f"People can use {app_name} to keep forecasts, saved locations, and quick weather checks close across repeat visits."
    if category == "Reference":
        return f"People can use {app_name} to keep structured answers, saved lookup context, and repeat-use details easy to revisit."
    if category == "Sports":
        return f"People can use {app_name} to keep scores, saved teams, and sports context close when they want a quick update."
    if category == "News":
        return f"People can use {app_name} to keep saved stories, followed topics, and timely reading context close over time."
    if category == "Finance":
        return (
            f"People can use {app_name} to keep saved payment context and optional purchase actions easy to revisit."
            if has_iap
            else f"People can use {app_name} to keep saved payment context and repeat finance actions easy to revisit."
        )
    if category == "Utilities":
        return f"People can use {app_name} to keep saved preferences and everyday tools easy to reopen."
    if category == "Photo & Video":
        return f"People can use {app_name} to edit portraits, revisit saved work, and manage optional export credits without a heavy workflow."
    return f"People can use {app_name} to stay close to {hint.experience}, revisit saved context, and keep repeat-use details easy to review."


def build_onboarding(
    app_name: str,
    hint: AppHint,
    inspect_payload: dict[str, Any],
    active: set[str],
    template_id: str | None = None,
) -> dict[str, Any]:
    profile = inspect_payload.get("project_profile", {})
    profile_features = profile.get("features", []) if isinstance(profile, dict) else []
    cards = [{"title": "Welcome", "body": f"{app_name} is ready for the functions you choose to use."}]
    for feature in profile_features:
        if not isinstance(feature, dict) or feature.get("status") != "confirmed":
            continue
        cards.append({
            "title": str(feature.get("title", "")),
            "body": str(feature.get("body", "")),
            "fact_id": str(feature.get("id", "")),
        })
        if len(cards) >= 4:
            break
    if len(cards) == 1:
        cards.append({"title": "Explore at Your Pace", "body": "Open the app to use the functions available for your needs."})
    cards.append({"title": "Ready to Begin", "body": "Select Continue to enter the app and get started."})
    cards = cards[:5]
    return {
        "template_id": template_id or "onboarding-cards",
        "layout": "carousel",
        "tagline": f"Welcome to {app_name}.",
        "cta_label": "Continue",
        "autoplay_interval_ms": 5000,
        "cards": cards,
    }


def build_payload(
    app_name: str,
    hint: AppHint,
    inspect_payload: dict[str, Any],
    active: set[str],
    category: str,
    urls: dict[str, str],
    onboarding_template_id: str | None = None,
) -> dict[str, Any]:
    support_email = str(inspect_payload.get("support_email") or "").strip() if inspect_payload.get("support_email_source") == "explicit" else ""
    has_iap = bool(inspect_payload.get("iap_codes")) or bool(inspect_payload.get("privacy_signals", {}).get("payments"))
    has_user_content = bool(inspect_payload.get("privacy_signals", {}).get("user_content"))
    preview_profile = ai_preview_profile(inspect_payload)
    has_ai_preview_review_profile = bool(preview_profile.get("needs_face_data_clauses"))
    face_data_workflow = face_data_workflow_kind(inspect_payload)
    has_translation = translation_disclosure_required(inspect_payload)
    has_credential_access = has_credential_account_access(inspect_payload)
    brand_identity_phrase = overview_identity_phrase(hint)
    if theme_first_product_phrase(hint):
        brand_overview = f"{brand_identity_phrase.capitalize()} with {hint.experience}."
    else:
        brand_overview = f"{brand_identity_phrase.capitalize()} for {hint.experience}."
    if has_ai_preview_review_profile:
        lowered_overview = brand_overview.lower()
        if face_data_workflow == "translation_face_visibility":
            if "translation" not in lowered_overview:
                brand_overview = brand_overview[:-1] + ", including AI-assisted image translation."
        elif "preview" not in lowered_overview and "try-on" not in lowered_overview and "try on" not in lowered_overview:
            brand_overview = brand_overview[:-1] + ", including AI Preview."
    payload = {
        "app_name": app_name,
        "support_email": support_email,
        "brand_colors": inspect_payload.get("brand_colors", []),
        "brand_overview": brand_overview,
        "index_title_suffix": hint.index_title_suffix,
        "index_subtitle": (
            (
                f"An evidence-based overview of how {app_name} handles community sharing, translation consent, permissions, and service rules."
                if face_data_workflow == "translation_face_visibility"
                else f"An evidence-based overview of how {app_name} handles community sharing, AI Preview, permissions, and service rules."
            )
            if has_ai_preview_review_profile
            else (
                non_ugc_index_subtitle(app_name, category, has_translation)
                if not has_user_content
                else f"A broad, evidence-based overview of how {app_name} handles discovery, sharing, support, and service rules."
            )
        ),
        "purpose": (
            (
                f"{app_name} is {brand_identity_phrase} that brings together {hint.experience}, including a user-initiated AI-assisted image translation flow where members can choose a photo with readable text, review consent, and receive translated results inside the app."
                if face_data_workflow == "translation_face_visibility"
                else f"{app_name} is {brand_identity_phrase} that brings together {hint.experience}, including a user-initiated AI Preview flow where members can choose a photo, review consent, generate a preview result, and decide whether to save it to Photos."
            )
            if has_ai_preview_review_profile
            else (
                non_ugc_purpose(app_name, category, brand_identity_phrase, hint, has_translation)
                if not has_user_content
                else f"{app_name} is {brand_identity_phrase} that brings together {hint.experience}, giving people a clearer place to browse, return, and publish without turning the experience into a technical walkthrough."
            )
        ),
        "members_intro": (
            (
                f"Members can use {app_name} to browse {hint.social_noun}, manage profile details, and run optional translation actions on labels, signs, or captions when they need more product context."
                if face_data_workflow == "translation_face_visibility"
                else f"Members can use {app_name} to browse {hint.social_noun}, manage profile details, and run optional AI Preview actions before they save or share a look."
            )
            if has_ai_preview_review_profile
            else (
                non_ugc_members_intro(app_name, category, hint, has_translation, has_iap)
                if not has_user_content
                else f"Members can use {app_name} to stay close to {hint.social_noun}, profile details, and everyday community actions."
            )
        ),
        "members_can_do": build_members_can_do(hint, category, active, has_iap, inspect_payload),
        "feature_cards": build_feature_cards(hint, category, active, has_iap, inspect_payload),
        "community_safety": (
            (
                "The app includes report, block, moderation, and contact pathways so unsafe or unwanted behavior can be reviewed and handled. "
                "Members can use those controls to report or limit unwanted interactions and content."
            )
            if has_user_content
            else "Saved edits, permission use, purchases, and support requests stay easier to review as you move through the app."
        ),
        "policy_note": (
            (
                f"Use the linked pages to review translation-consent handling, visible-face disclosures, support routes, and permission details for {app_name}."
                if face_data_workflow == "translation_face_visibility"
                else f"Use the linked pages to review AI Preview handling, support routes, and permission details for {app_name}."
            )
            if has_ai_preview_review_profile
            else f"Use the linked pages to review support details, privacy information, and service terms for {app_name}."
        ),
        "privacy_brand_line": (
            (
                f"How {app_name} collects, uses, shares, and protects selected images, translated results, and service information."
                if face_data_workflow == "translation_face_visibility"
                else f"How {app_name} collects, uses, shares, and protects selected photos, preview results, and service information."
            )
            if has_ai_preview_review_profile
            else f"How {app_name} collects, uses, shares, and protects service information."
        ),
        "privacy_intro": (
            (
                (
                    f"This Privacy Policy explains how {app_name} handles sign-in details, translation inputs, visible-face disclosures, community activity, permissions, and service operations."
                    if has_user_content and has_credential_access and face_data_workflow == "translation_face_visibility"
                    else f"This Privacy Policy explains how {app_name} handles profile details, translation inputs, visible-face disclosures, community activity, permissions, and service operations."
                    if has_user_content and face_data_workflow == "translation_face_visibility"
                    else f"This Privacy Policy explains how {app_name} handles selected images, translation inputs, visible-face disclosures, permissions, and service operations."
                    if face_data_workflow == "translation_face_visibility"
                    else f"This Privacy Policy explains how {app_name} handles sign-in details, AI Preview inputs, community activity, permissions, and service operations."
                    if has_user_content and has_credential_access
                    else f"This Privacy Policy explains how {app_name} handles profile details, AI Preview inputs, community activity, permissions, and service operations."
                    if has_user_content
                    else f"This Privacy Policy explains how {app_name} handles selected photos, AI Preview inputs, permissions, and service operations."
                )
            )
            if has_ai_preview_review_profile
            else (
                f"This Privacy Policy explains how {app_name} handles photos, notes, permissions, purchases, and support requests."
                if not has_user_content
                else (
                    f"This Privacy Policy explains how {app_name} handles sign-in details, community activity, permissions, and service operations."
                    if has_credential_access
                    else f"This Privacy Policy explains how {app_name} handles profile details, community activity, permissions, and service operations."
                )
            )
        ),
        "privacy_sections": build_privacy_sections(app_name, hint, inspect_payload, active, urls),
        "terms_brand_line": (
            (
                f"Rules for community use, AI-assisted translation, support, purchases, and assisted features in {app_name}."
                if face_data_workflow == "translation_face_visibility"
                else f"Rules for community use, AI Preview, support, purchases, and assisted features in {app_name}."
            )
            if has_ai_preview_review_profile
            else (
                (
                    f"Rules for editing tools, translation tools, support, purchases, and service operations in {app_name}."
                    if has_translation
                    else f"Rules for editing tools, saved content, support, purchases, and service operations in {app_name}."
                )
                if not has_user_content
                else (
                    f"Rules for community use, translation tools, support, purchases, and service operations in {app_name}."
                    if has_translation
                    else f"Rules for community use, support, purchases, and service operations in {app_name}."
                )
            )
        ),
        "terms_intro": f"These Terms & Conditions apply whenever you use {app_name}, its related site pages, and any optional service features.",
        "terms_sections": build_terms_sections(app_name, hint, inspect_payload, active),
        "support_brand_line": (
            (
                (
                    f"Help for translation consent, permissions, profiles, publishing, safety, purchases, and policy questions in {app_name}."
                    if has_user_content and face_data_workflow == "translation_face_visibility"
                    else f"Help for AI Preview, permissions, profiles, publishing, safety, purchases, and policy questions in {app_name}."
                    if has_user_content
                    else f"Help for translation consent, permissions, selected images, saved results, purchases, and policy questions in {app_name}."
                    if face_data_workflow == "translation_face_visibility"
                    else f"Help for AI Preview, permissions, selected photos, saved results, purchases, and policy questions in {app_name}."
                )
            )
            if has_ai_preview_review_profile
            else (
                f"Help for editing flows, permissions, saved notes, exports, purchases, and policy questions in {app_name}."
                if not has_user_content
                else f"Help for profiles, publishing, safety, purchases, and policy questions in {app_name}."
            )
        ),
        "support_subtitle": (
            (
                f"Answers for translation consent, permissions, profile, publishing, safety, and support issues in {app_name}."
                if face_data_workflow == "translation_face_visibility"
                else f"Answers for AI Preview, permissions, profile, publishing, safety, and support issues in {app_name}."
            )
            if has_ai_preview_review_profile and has_user_content
            else (
                f"Answers for translation consent, permissions, saved results, exports, purchases, and support issues in {app_name}."
                if face_data_workflow == "translation_face_visibility"
                else f"Answers for AI Preview, permissions, saved results, exports, purchases, and support issues in {app_name}."
            )
            if has_ai_preview_review_profile
            else f"Answers for profile, publishing, safety, and support issues in {app_name}."
            if has_user_content
            else f"Answers for editing, permissions, saved notes, exports, purchases, and support issues in {app_name}."
        ),
        "faq_items": build_faq_items(app_name, hint, active, has_iap, has_user_content, inspect_payload),
        "support_outro": (
            (
                f"If you still need help with {app_name}, email support and include the details that will help us review your request quickly. "
                "If your request involves translation permissions, image-translation privacy, or translation-history handling, include the relevant details so we can review the privacy context more efficiently. "
                "If your request involves objectionable content, harassment, or another safety concern, include the relevant profile, member, or content details so the report can usually be reviewed within 24 hours."
                if face_data_workflow == "translation_face_visibility"
                else f"If you still need help with {app_name}, email support and include the details that will help us review your request quickly. "
                "If your request involves AI Preview permissions, deletion, or preview-result handling, include the relevant details so we can review the privacy context more efficiently. "
                "If your request involves objectionable content, harassment, or another safety concern, include the relevant profile, member, or content details so the report can usually be reviewed within 24 hours."
            )
            if has_ai_preview_review_profile and has_user_content
            else f"If you still need help with {app_name}, email support and include the details that will help us review your request quickly. "
            "If your request involves objectionable content, harassment, or another safety concern, include the relevant profile, member, or content details so the report can usually be reviewed within 24 hours."
            if has_user_content
            else f"If you still need help with {app_name}, email support and include the details that will help us review your request quickly."
        ),
        "last_updated": TODAY,
        "index_meta_description": f"{app_name} overview, support links, privacy access, and terms information.",
        "privacy_meta_description": f"{app_name} privacy policy and data handling information.",
        "terms_meta_description": (
            f"{app_name} terms, editing rules, purchase rules, and service conditions."
            if not has_user_content
            else f"{app_name} terms, community rules, and service conditions."
        ),
        "support_meta_description": f"{app_name} support answers, contact details, and help resources.",
    }

    project_profile = inspect_payload.get("project_profile", {})
    profile_purpose = project_profile.get("purpose", {}) if isinstance(project_profile, dict) else {}
    if isinstance(profile_purpose, dict) and profile_purpose.get("status") == "confirmed":
        purpose_value = str(profile_purpose.get("value", "")).strip()
        if purpose_value:
            purpose_fragment = purpose_value.removeprefix("A focused app for ").rstrip(".")
            payload["brand_overview"] = purpose_value
            payload["purpose"] = f"{app_name} is a focused app for {purpose_fragment}."
            payload["index_subtitle"] = purpose_value
            payload["members_intro"] = f"Use {app_name} for {purpose_fragment}."

    matrix = build_product_facts(inspect_payload, active)
    labels = feature_labels(matrix)
    payload.update({
        "product_facts": matrix,
        "onboarding": build_onboarding(app_name, hint, inspect_payload, active, onboarding_template_id),
        "privacy_brand_line": f"Privacy and data handling in {app_name}.",
        "privacy_intro": f"This policy describes information processing in {app_name}'s available functions.",
        "terms_brand_line": f"Terms for {', '.join(labels) if labels else 'the available functions'} in {app_name}.",
        "terms_intro": f"These Terms & Conditions apply to your use of {app_name}.",
        "terms_meta_description": f"{app_name} terms and service conditions.",
        "support_meta_description": f"{app_name} support answers and help resources." if not support_email else f"{app_name} support answers, contact details, and help resources.",
        "policy_note": "",
        "index_meta_description": f"Welcome to {app_name}.",
        "support_brand_line": f"Help and contact information for {app_name}." if support_email else f"Help and feature information for {app_name}.",
        "support_subtitle": f"Answers about the available features in {app_name}.",
        "support_outro": f"Find guidance about the available features in {app_name} in the answers below.",
        "privacy_badges": ["Privacy", "Contact"] if support_email else ["Privacy", "Choices"],
        "terms_badges": ["Use limits", "Service rules"],
        "support_badges": ["FAQ", "Contact"] if support_email else ["FAQ"],
        "faq_items": build_evidenced_faq(inspect_payload, active),
        "privacy_sections": build_privacy_sections(app_name, hint, inspect_payload, active, urls),
        "terms_sections": build_terms_sections(app_name, hint, inspect_payload, active),
    })
    for page_kind in ("privacy", "terms", "support"):
        payload[f"{page_kind}_cards"] = [{"title": "Contact", "body": support_email}] if support_email else []
        payload[f"{page_kind}_highlights"] = []
    payload["index_layout"] = payload["onboarding"]["template_id"]
    return payload


def validate_outputs(
    app_root: Path,
    inspect_json_path: Path,
    classification_json_path: Path,
) -> list[str]:
    app_listing_dir = app_root / "AppListing"
    site_dir = app_listing_dir / "site"

    commands = [
        ("validate_app_listing_classification.py", "--evidence-json", str(inspect_json_path), "--classification-json", str(classification_json_path)),
        ("validate_intro_output.py", "--inspect-json", str(inspect_json_path), "--intro-md", str(app_listing_dir / "Intro.md")),
        ("validate_privacy_output.py", "--inspect-json", str(inspect_json_path), "--privacy-html", str(site_dir / "PrivacyPolicy.html")),
        ("validate_review_wording.py", "--intro-md", str(app_listing_dir / "Intro.md"), "--site-dir", str(site_dir)),
        ("validate_account_wording.py", "--inspect-json", str(inspect_json_path), "--intro-md", str(app_listing_dir / "Intro.md"), "--site-dir", str(site_dir)),
        ("validate_non_ai_output.py", "--inspect-json", str(inspect_json_path), "--intro-md", str(app_listing_dir / "Intro.md"), "--site-dir", str(site_dir)),
        ("validate_site_metadata_output.py", "--site-dir", str(site_dir)),
        ("validate_site_publication_ready.py", "--site-dir", str(site_dir)),
        ("validate_terms_ai_output.py", "--inspect-json", str(inspect_json_path), "--terms-html", str(site_dir / "Terms&Conditions.html")),
        ("validate_iap_legal_output.py", "--inspect-json", str(inspect_json_path), "--intro-md", str(app_listing_dir / "Intro.md"), "--privacy-html", str(site_dir / "PrivacyPolicy.html"), "--terms-html", str(site_dir / "Terms&Conditions.html")),
        ("validate_permission_privacy.py", "--inspect-json", str(inspect_json_path), "--privacy-html", str(site_dir / "PrivacyPolicy.html")),
        ("validate_dynamic_legal_output.py", "--inspect-json", str(inspect_json_path), "--privacy-html", str(site_dir / "PrivacyPolicy.html"), "--terms-html", str(site_dir / "Terms&Conditions.html")),
        ("validate_onboarding_output.py", "--index-html", str(site_dir / "index.html")),
        ("validate_support_output.py", "--inspect-json", str(inspect_json_path), "--support-html", str(site_dir / "Support.html")),
        ("validate_listing_claims.py", "--classification-json", str(classification_json_path), "--intro-md", str(app_listing_dir / "Intro.md"), "--index-html", str(site_dir / "index.html")),
        ("validate_listing_contract.py", "--app-listing-dir", str(app_listing_dir)),
    ]

    if inspect_payload := json.loads(inspect_json_path.read_text(encoding="utf-8")):
        privacy_signals = inspect_payload.get("privacy_signals", {})
        capability_candidates = inspect_payload.get("capability_candidates", {})
        requires_ugc = (
            isinstance(privacy_signals, dict)
            and privacy_signals.get("community_ugc") is True
        ) or (
            isinstance(capability_candidates, dict)
            and any(
                isinstance(capability_candidates.get(name), dict)
                and float(capability_candidates[name].get("score", 0.0)) >= 1.0
                for name in ("feed", "post_creation")
            )
        )
        if requires_ugc:
            commands.append(
                (
                    "validate_ugc_legal_output.py",
                    "--inspect-json",
                    str(inspect_json_path),
                    "--privacy-html",
                    str(site_dir / "PrivacyPolicy.html"),
                    "--terms-html",
                    str(site_dir / "Terms&Conditions.html"),
                )
            )

    failures: list[str] = []
    for script_name, *args in commands:
        try:
            run_script(script_name, *args)
        except subprocess.CalledProcessError as exc:
            failures.append(f"{script_name}: {exc.stdout.strip() or exc.stderr.strip()}")
    return failures


def render_site(payload: dict[str, Any], output_dir: Path, seed: str | None = None) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        payload_path = Path(handle.name)
    try:
        args = ["--payload-json", str(payload_path), "--output-dir", str(output_dir)]
        if seed:
            args.extend(["--seed", seed])
        run_script("render_app_listing.py", *args)
    finally:
        payload_path.unlink(missing_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_listing_validators(
    target: Path,
    slug: str,
    inspect_payload: dict[str, Any],
    classification: dict[str, Any],
) -> list[str]:
    with tempfile.TemporaryDirectory(prefix=f"{slug}_listing_") as temp_dir:
        temp_root = Path(temp_dir)
        inspect_json_path = temp_root / "inspect.json"
        classification_json_path = temp_root / "classification.json"
        write_json(inspect_json_path, inspect_payload)
        write_json(classification_json_path, classification)
        return validate_outputs(target, inspect_json_path, classification_json_path)


def load_classification_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("classification_json_must_be_object")
    return payload


def load_authoring_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("authoring_json_must_be_object")
    unknown = sorted(set(payload.keys()) - AUTHORING_OPTIONAL_KEYS)
    if unknown:
        raise ValueError(f"unsupported_authoring_keys:{','.join(unknown)}")
    site_overview = payload.get("site_overview")
    if site_overview is not None and not isinstance(site_overview, dict):
        raise ValueError("authoring_site_overview_must_be_object")
    for key in ("legal", "onboarding"):
        if key in payload and not isinstance(payload[key], dict):
            raise ValueError(f"authoring_{key}_must_be_object")
    return payload


def authoring_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None and isinstance(payload.get("site_overview"), dict):
        value = payload["site_overview"].get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"authoring_{key}_must_be_string")
    text = value.strip()
    if not text:
        raise ValueError(f"authoring_{key}_must_not_be_empty")
    return text


def authoring_keywords(payload: dict[str, Any]) -> list[str] | None:
    raw = payload.get("keywords")
    if raw is None:
        return None
    if isinstance(raw, str):
        items = [part.strip() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, list):
        items = [str(part).strip() for part in raw if str(part).strip()]
    else:
        raise ValueError("authoring_keywords_must_be_string_or_array")
    if not items:
        raise ValueError("authoring_keywords_must_not_be_empty")
    return items


def is_valid_subtitle_candidate(subtitle: str) -> bool:
    value = subtitle.strip()
    return bool(value) and len(value) <= 30 and bool(SUBTITLE_PATTERN.fullmatch(value))


def resolve_intro_subtitle(authoring_override: dict[str, Any], state_path: Path | None = None) -> str:
    authored_subtitle = authoring_string(authoring_override, "subtitle")
    if authored_subtitle and is_valid_subtitle_candidate(authored_subtitle):
        return authored_subtitle.strip()
    return choose_subtitle(state_path)


def validate_intro_markdown(inspect_payload: dict[str, Any], intro_markdown: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="intro_validate_") as temp_dir:
        temp_root = Path(temp_dir)
        inspect_json_path = temp_root / "inspect.json"
        intro_path = temp_root / "Intro.md"
        write_json(inspect_json_path, inspect_payload)
        intro_path.write_text(intro_markdown, encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "validate_intro_output.py"),
                "--inspect-json",
                str(inspect_json_path),
                "--intro-md",
                str(intro_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            if result.returncode == 0:
                return []
            stderr = result.stderr.strip() or result.stdout.strip() or "validate_intro_output_failed"
            return [stderr]
        errors = payload.get("errors", [])
        return [str(item) for item in errors] if isinstance(errors, list) else ["invalid_intro_validation_response"]


def validate_site_overview_copy(
    inspect_payload: dict[str, Any],
    *,
    brand_overview: str,
    index_subtitle: str,
    purpose: str,
    members_intro: str,
) -> list[str]:
    errors: list[str] = []
    text_pairs = {
        "brand_overview": brand_overview.strip(),
        "index_subtitle": index_subtitle.strip(),
        "purpose": purpose.strip(),
        "members_intro": members_intro.strip(),
    }

    for key, value in text_pairs.items():
        if not value:
            errors.append(f"{key}_empty")

    if not purpose.strip():
        return errors

    first_sentence = purpose.strip().split(". ", 1)[0].strip()
    if not first_sentence.endswith(".") and "." in purpose.strip():
        first_sentence = first_sentence + "."
    lower_first = first_sentence.lower()
    blocked_generic = (
        "community lifestyle app",
        "lifestyle app",
        "community app",
    )
    if any(token in lower_first for token in blocked_generic):
        errors.append("purpose_first_sentence_too_generic")

    if not has_chat_capability(active_capabilities(inspect_payload), inspect_payload):
        blocked_chat_tokens = ("chat", "message", "messages", "conversation", "conversations", "inbox", "thread", "threads", "dm", "dms")
        joined = " ".join(text_pairs.values()).lower()
        if any(token in joined for token in blocked_chat_tokens):
            errors.append("site_overview_implies_chat_when_chat_is_no")

    return errors


def dedupe_errors(errors: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for item in errors:
        if item in seen:
            continue
        unique.append(item)
        seen.add(item)
    return unique


def remove_app_name_mentions(text: str, app_name: str) -> str:
    if not app_name:
        return text
    return re.sub(re.escape(app_name), " ", text, flags=re.IGNORECASE)


def validate_non_ai_text_blobs(
    inspect_payload: dict[str, Any],
    text_blobs: dict[str, str],
    *,
    app_name: str,
) -> list[str]:
    if ai_disclosure_required(inspect_payload):
        return []

    errors: list[str] = []
    for label, raw_text in text_blobs.items():
        cleaned = remove_app_name_mentions(raw_text or "", app_name)
        for marker, pattern in NON_AI_COPY_PATTERNS:
            if pattern.search(cleaned):
                errors.append(
                    f"{label} contains AI-related wording when ai_signals.disclosure_required is false: {marker}."
                )
                break
    return errors


def filter_local_generation_intro_errors(errors: list[str]) -> list[str]:
    blocked_prefixes = (
        "Description first sentence is too generic",
        "Description first sentence should include a concrete theme term",
    )
    return [item for item in errors if not any(item.startswith(prefix) for prefix in blocked_prefixes)]


def filter_local_generation_site_overview_errors(errors: list[str]) -> list[str]:
    return [item for item in errors if item != "purpose_first_sentence_too_generic"]


def prepare_generation_context(
    target: Path,
    classification_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inspect_payload = run_json_script("inspect_app.py", "--target", str(target))
    app_name = str(inspect_payload["app_name"])
    slug = str(inspect_payload["app_slug"])
    active = active_capabilities(inspect_payload)
    archetype_scores = score_archetypes(inspect_payload, active)
    default_archetype = pick_primary_archetype(archetype_scores)
    default_category = pick_category(default_archetype)
    archetype = normalize_archetype(
        str(classification_override.get("archetype", "")).strip() if classification_override else None,
        str(classification_override.get("category", "")).strip() if classification_override else default_category,
    )
    category = (
        str(classification_override.get("category", "")).strip()
        if classification_override and str(classification_override.get("category", "")).strip()
        else pick_category(archetype)
    )
    fallback_hint = APP_HINTS.get(slug, fallback_hint_for_archetype(archetype, inspect_payload))
    hint = hint_from_classification(classification_override or {}, inspect_payload, fallback_hint)
    capabilities = preferred_capabilities(active, category)
    if classification_override and isinstance(classification_override.get("capabilities"), list):
        requested = [str(item).strip() for item in classification_override["capabilities"] if str(item).strip()]
        if requested:
            capabilities = requested
    theme_label = (
        str(classification_override.get("theme", "")).strip()
        if classification_override and str(classification_override.get("theme", "")).strip()
        else default_theme_label_from_hint(hint)
    )
    classification = (
        dict(classification_override)
        if classification_override
        else build_classification(inspect_payload, hint, category, archetype, capabilities, theme_label)
    )
    if "category" not in classification:
        classification["category"] = category
    if "archetype" not in classification:
        classification["archetype"] = archetype
    if "theme" not in classification:
        classification["theme"] = theme_label
    if "capabilities" not in classification:
        classification["capabilities"] = capabilities
    if "claimable_features" not in classification:
        classification["claimable_features"] = capabilities
    if "confidence" not in classification:
        classification["confidence"] = "high" if len(capabilities) >= 3 else "medium"
    if "reasoning" not in classification:
        classification["reasoning"] = build_classification(
            inspect_payload,
            hint,
            category,
            archetype,
            capabilities,
            theme_label,
        )["reasoning"]
    if category not in CATEGORY_LABELS:
        raise ValueError(f"unsupported_category:{category}")
    category_label = CATEGORY_LABELS[category]
    has_iap = bool(inspect_payload.get("iap_codes")) or bool(inspect_payload.get("privacy_signals", {}).get("payments"))
    return {
        "inspect_payload": inspect_payload,
        "app_name": app_name,
        "slug": slug,
        "active": active,
        "archetype_scores": archetype_scores,
        "archetype": archetype,
        "category": category,
        "category_label": category_label,
        "hint": hint,
        "capabilities": capabilities,
        "classification": classification,
        "has_iap": has_iap,
        "theme_label": theme_label,
    }


def generate_for_target(
    target: Path,
    style_override: str | None,
    classification_override: dict[str, Any] | None = None,
    authoring_override: dict[str, Any] | None = None,
    deployment_options: AboutDeploymentOptions | None = None,
    style_state_path: Path | None = None,
    onboarding_template_id: str | None = None,
) -> dict[str, Any]:
    app_listing = target / "AppListing"
    backup_handle: tempfile.TemporaryDirectory[str] | None = None
    backup_listing: Path | None = None
    deployment_options = deployment_options or AboutDeploymentOptions()
    restore_backup_on_exception = True

    if app_listing.exists():
        backup_handle = tempfile.TemporaryDirectory(prefix=f"{target.name}_applisting_backup_")
        backup_listing = Path(backup_handle.name) / "AppListing"
        shutil.move(str(app_listing), str(backup_listing))

    try:
        context = prepare_generation_context(target, classification_override)
        inspect_payload = context["inspect_payload"]
        app_name = str(context["app_name"])
        slug = str(context["slug"])
        active = set(context["active"])
        archetype_scores = dict(context["archetype_scores"])
        archetype = str(context["archetype"])
        category = str(context["category"])
        category_label = str(context["category_label"])
        hint = context["hint"]
        selected_onboarding_template_id = onboarding_template_id or choose_onboarding_template_id()
        capabilities = list(context["capabilities"])
        classification = dict(context["classification"])
        has_iap = bool(context["has_iap"])
        urls = resolve_listing_urls(target, inspect_payload)
        authoring_override = authoring_override or {}
        if "legal" in authoring_override:
            if not isinstance(authoring_override["legal"], dict):
                raise ValueError("authoring.legal must be a confirmed legal configuration object")
            inspect_payload["legal"] = authoring_override["legal"]
        requested_style_label = authoring_string(authoring_override, "description_style_label")
        style_assignment = assign_description_style(
            target,
            category=category,
            active=active,
            has_iap=has_iap,
            inspect_payload=inspect_payload,
            override=requested_style_label or style_override,
            state_path=style_state_path,
        )
        fallback_style = str(style_assignment["style"])
        authored_description = authoring_string(authoring_override, "description")
        description_source = "agent_authored" if authored_description else "local_generated"
        style_label = requested_style_label or "agent_authored"
        style = style_label if description_source == "agent_authored" else fallback_style
        subtitle = resolve_intro_subtitle(authoring_override, style_state_path)
        keywords = authoring_keywords(authoring_override) or build_keywords(hint, active, inspect_payload)
        logo_source = pick_logo_source(target, inspect_payload)
        media_review_errors = []
        if logo_source is None:
            media_review_errors.append("required_logo_missing")
        elif logo_source not in (
            (target / "assets/logo.png").resolve(),
            (target / "ios/Runner/assets/logo.png").resolve(),
        ):
            media_review_errors.append("official_logo_unverified: using existing or development brand source")
        site_dir = app_listing / "site"
        style_candidates = [style] if description_source == "agent_authored" else [
            fallback_style,
            *[candidate for candidate in style_assignment["style_pool"] if candidate != fallback_style],
        ]
        generation_attempt_count = 0
        generation_attempt_styles: list[str] = []
        description = authored_description or ""
        intro = ""
        payload: dict[str, Any] = {}
        failures: list[str] = []
        site_overview_source = "local_generated"
        for candidate_style in style_candidates:
            generation_attempt_count += 1
            generation_attempt_styles.append(candidate_style)
            current_style = style_label if description_source == "agent_authored" else candidate_style
            description = (
                authored_description
                if authored_description is not None
                else build_description(
                    app_name=app_name,
                    category=category,
                    hint=hint,
                    active=active,
                    style=candidate_style,
                    has_iap=has_iap,
                    inspect_payload=inspect_payload,
                )
            )
            intro = build_intro(
                app_name=app_name,
                subtitle=subtitle,
                category_label=category_label,
                description=description,
                keywords=keywords,
                urls=urls,
                has_ugc=has_ugc_capability_for_payload(active, inspect_payload),
                has_chat=has_chat_capability(active, inspect_payload),
            )
            intro_validation_errors = validate_intro_markdown(inspect_payload, intro)
            if description_source == "agent_authored":
                intro_validation_errors.extend(validate_description_theme_opening(description, hint))
            else:
                intro_validation_errors = filter_local_generation_intro_errors(intro_validation_errors)

            payload = build_payload(
                app_name,
                hint,
                inspect_payload,
                active,
                category,
                urls,
                onboarding_template_id=selected_onboarding_template_id,
            )
            if "onboarding" in authoring_override:
                if not isinstance(authoring_override["onboarding"], dict):
                    raise ValueError("authoring.onboarding must be an object")
                payload["onboarding"].update(authoring_override["onboarding"])
            if onboarding_template_id:
                payload["onboarding"]["template_id"] = onboarding_template_id
            payload["index_layout"] = payload["onboarding"]["template_id"]
            site_overview_source = "local_generated"
            for key in AUTHORING_SITE_OVERVIEW_KEYS:
                override_value = authoring_string(authoring_override, key)
                if override_value is not None:
                    payload[key] = override_value
                    site_overview_source = "agent_authored"
            if not has_chat_capability(active, inspect_payload):
                payload = sanitize_non_chat_site_overview_copy(payload)
            site_overview_validation_errors = validate_site_overview_copy(
                inspect_payload,
                brand_overview=str(payload["brand_overview"]),
                index_subtitle=str(payload["index_subtitle"]),
                purpose=str(payload["purpose"]),
                members_intro=str(payload["members_intro"]),
            )
            if site_overview_source != "agent_authored":
                site_overview_validation_errors = filter_local_generation_site_overview_errors(site_overview_validation_errors)

            content_gate_errors = validate_non_ai_text_blobs(
                inspect_payload,
                {
                    "Intro.md": intro,
                    "site_payload": json.dumps(
                        {key: value for key, value in payload.items() if key != "product_facts"},
                        ensure_ascii=False,
                    ),
                },
                app_name=app_name,
            )
            pre_generation_failures = dedupe_errors(
                intro_validation_errors + site_overview_validation_errors + content_gate_errors
            )

            style = current_style
            if app_listing.exists():
                shutil.rmtree(app_listing)
            (site_dir / "img").mkdir(parents=True, exist_ok=True)
            (app_listing / "Intro.md").write_text(intro, encoding="utf-8")
            render_site(payload, site_dir)
            if logo_source is not None:
                copy_logo(logo_source, site_dir / "img" / "logo.png")

            failures = dedupe_errors(pre_generation_failures + run_listing_validators(target, slug, inspect_payload, classification))
            if not failures or description_source == "agent_authored":
                break

        deployment_summary: dict[str, Any] | None = None
        legal_review_errors = legal_fact_review_items(inspect_payload)
        if inspect_payload.get("support_email_source") != "explicit":
            legal_review_errors.append("support_contact: no confirmed support email is available; add a verified contact channel before public legal publication")
        legal_blocking_errors = legal_fact_errors(inspect_payload)
        resolved_urls = urls
        project_url_sync = default_project_url_sync_summary(
            bool(deployment_options.sync_project_listing_urls),
            "disabled" if not deployment_options.sync_project_listing_urls else "deployment_not_run",
        )
        restore_backup_on_exception = False

        if deployment_options.enabled:
            if failures or media_review_errors:
                deployment_summary = {
                    "enabled": True,
                    "status": "skipped",
                    "reason": "validation_failed" if failures else "media_review_required",
                    "legal_review_errors": legal_review_errors,
                }
                project_url_sync = default_project_url_sync_summary(
                    bool(deployment_options.sync_project_listing_urls),
                    "deployment_failed" if deployment_options.sync_project_listing_urls else "disabled",
                )
            else:
                try:
                    deployment_summary = deploy_about_site(
                        app_name,
                        site_dir,
                        deployment_options,
                    )
                    resolved_urls = dict(deployment_summary["urls"])
                    updated_intro = build_intro(
                        app_name=app_name,
                        subtitle=subtitle,
                        category_label=category_label,
                        description=description,
                        keywords=keywords,
                        urls=resolved_urls,
                        has_ugc=has_ugc_capability_for_payload(active, inspect_payload),
                        has_chat=has_chat_capability(active, inspect_payload),
                    )
                    (app_listing / "Intro.md").write_text(updated_intro, encoding="utf-8")
                    failures = run_listing_validators(target, slug, inspect_payload, classification)
                    if failures:
                        raise DeploymentError(
                            "Post-deployment AppListing validation failed after Intro URL rewrite: "
                            + " | ".join(failures),
                            retryable=False,
                            reason="post_deploy_validation_failed",
                        )
                    if deployment_options.sync_project_listing_urls:
                        project_url_sync = sync_project_listing_urls(target, resolved_urls)
                    else:
                        project_url_sync = default_project_url_sync_summary(False, "disabled")
                except DeploymentError as exc:
                    (app_listing / "Intro.md").write_text(intro, encoding="utf-8")
                    resolved_urls = urls
                    failures = run_listing_validators(target, slug, inspect_payload, classification)
                    deployment_summary = deployment_summary_for_error(exc)
                    project_url_sync = default_project_url_sync_summary(
                        bool(deployment_options.sync_project_listing_urls),
                        "deployment_failed",
                    )
        else:
            project_url_sync = default_project_url_sync_summary(
                bool(deployment_options.sync_project_listing_urls),
                "deployment_disabled",
            )

        return {
            "app_name": app_name,
            "slug": slug,
            "stack": inspect_payload.get("source_stack"),
            "category": category,
            "category_label": category_label,
            "archetype": ARCHETYPE_LABELS.get(archetype, archetype),
            "archetype_scores": archetype_scores,
            "theme": classification.get("theme", "Generic"),
            "theme_confidence": classification.get("confidence", "medium"),
            "capabilities": capabilities,
            "ai_privacy": ai_disclosure_required(inspect_payload),
            "description_style": style,
            "description_style_pool_id": style_assignment["pool_id"],
            "description_style_pool": list(style_assignment["style_pool"]),
            "description_style_assignment": style_assignment["assignment_source"],
            "generation_attempts": generation_attempt_count,
            "generation_attempt_styles": generation_attempt_styles,
            "description_source": description_source,
            "site_overview_source": site_overview_source,
            "onboarding_template_id": payload["onboarding"]["template_id"],
            "legal_unknowns": payload["product_facts"]["unknowns"],
            "legal_conflicts": payload["product_facts"]["conflicts"],
            "legal_review_errors": legal_review_errors,
            "legal_blocking_errors": legal_blocking_errors,
            "legal_review_required": bool(legal_review_errors),
            "local_generation_complete": True,
            "media_review_errors": media_review_errors,
            "deployment_ready": not failures and not media_review_errors,
            "publication_ready": not failures and not legal_review_errors and not media_review_errors,
            "support_email_source": inspect_payload.get("support_email_source"),
            "support_contact_confirmed": inspect_payload.get("support_email_source") == "explicit",
            "logo_source": str(logo_source.relative_to(target.resolve())) if logo_source is not None else None,
            "urls": resolved_urls,
            "deployment": deployment_summary,
            "project_url_sync": project_url_sync,
            "failures": failures,
        }
    except Exception:
        if restore_backup_on_exception and backup_listing is not None and backup_listing.exists():
            if app_listing.exists():
                shutil.rmtree(app_listing)
            shutil.move(str(backup_listing), str(app_listing))
        raise
    finally:
        if backup_handle is not None:
            backup_handle.cleanup()


def select_description_style_for_target(
    target: Path,
    style_override: str | None,
    classification_override: dict[str, Any] | None = None,
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    context = prepare_generation_context(target, classification_override)
    assignment = assign_description_style(
        target,
        category=str(context["category"]),
        active=set(context["active"]),
        has_iap=bool(context["has_iap"]),
        inspect_payload=context["inspect_payload"],
        override=style_override,
        state_path=state_path,
    )
    return {
        "app_name": str(context["app_name"]),
        "slug": str(context["slug"]),
        "stack": context["inspect_payload"].get("source_stack"),
        "category": str(context["category"]),
        "description_style": assignment["style"],
        "description_style_pool_id": assignment["pool_id"],
        "description_style_pool": list(assignment["style_pool"]),
        "description_style_assignment": assignment["assignment_source"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AppListing outputs for one or more iOS app roots.")
    parser.add_argument("--target", action="append", required=True, help="Absolute or relative app root path. Repeat for multiple apps.")
    parser.add_argument(
        "--classification-json",
        help="Optional path to an AI-authored classification JSON containing category/archetype/theme and an optional theme_hint object.",
    )
    parser.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        help="Optional fixed Intro description style. Defaults to a random allowed style per app.",
    )
    parser.add_argument(
        "--authoring-json",
        help="Optional JSON file containing current-agent authored description and site overview copy.",
    )
    parser.add_argument("--onboarding-template-id", choices=list(ONBOARDING_TEMPLATE_IDS), help="Override the independent index launch-guide template.")
    parser.add_argument(
        "--select-description-style",
        action="store_true",
        help="Resolve and persist the routed Intro description style without generating AppListing output files.",
    )
    parser.add_argument(
        "--style-state-path",
        help="Optional path to the persistent description-style and subtitle rotation state JSON.",
    )
    deploy_group = parser.add_mutually_exclusive_group()
    deploy_group.add_argument(
        "--deploy-about",
        dest="deploy_about",
        action="store_true",
        help="Enable the default About deployment flow after validators pass.",
    )
    deploy_group.add_argument(
        "--no-deploy-about",
        dest="deploy_about",
        action="store_false",
        help="Skip the default About deployment flow and keep placeholder Intro URLs.",
    )
    parser.set_defaults(deploy_about=True)
    sync_group = parser.add_mutually_exclusive_group()
    sync_group.add_argument(
        "--sync-project-listing-urls",
        dest="sync_project_listing_urls",
        action="store_true",
        help="After a successful About deployment, sync project source listing/legal URLs to the published host.",
    )
    sync_group.add_argument(
        "--no-sync-project-listing-urls",
        dest="sync_project_listing_urls",
        action="store_false",
        help="Do not rewrite project source listing/legal URLs after a successful About deployment.",
    )
    parser.set_defaults(sync_project_listing_urls=True)
    parser.add_argument(
        "--deploy-max-attempts",
        type=int,
        default=1,
        help="Maximum About deployment task creation attempts. Defaults to one attempt to avoid duplicate deployments.",
    )
    parser.add_argument(
        "--deploy-poll-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds while waiting for the About deployment task to finish.",
    )
    parser.add_argument(
        "--deploy-poll-timeout",
        type=float,
        default=900.0,
        help="Maximum seconds to wait for one About deployment task before treating it as failed.",
    )
    parser.add_argument(
        "--deploy-publish-ready-delay",
        type=float,
        default=0.0,
        help="Deprecated compatibility option. Published listing URL probing is skipped after the deployment task succeeds.",
    )
    args = parser.parse_args()
    if args.authoring_json and len(args.target) != 1:
        parser.error("--authoring-json currently supports exactly one --target")
    return args


def main() -> None:
    run_started_at = time.monotonic()
    args = parse_args()
    summaries: list[dict[str, Any]] = []
    exit_code = 0
    classification_override = load_classification_json(Path(args.classification_json)) if args.classification_json else None
    authoring_override = load_authoring_json(Path(args.authoring_json)) if args.authoring_json else None
    style_state_path = Path(args.style_state_path).expanduser().resolve() if args.style_state_path else None
    deployment_options = AboutDeploymentOptions(
        enabled=bool(args.deploy_about),
        sync_project_listing_urls=bool(args.sync_project_listing_urls),
        max_attempts=max(1, int(args.deploy_max_attempts)),
        poll_interval_seconds=max(0.1, float(args.deploy_poll_interval)),
        poll_timeout_seconds=max(1.0, float(args.deploy_poll_timeout)),
        publish_ready_delay_seconds=max(0.0, float(args.deploy_publish_ready_delay)),
    )

    if args.select_description_style:
        for raw_target in args.target:
            target = Path(raw_target).expanduser().resolve()
            target_started_at = time.monotonic()
            summary = select_description_style_for_target(
                target,
                args.description_style,
                classification_override,
                state_path=style_state_path,
            )
            summary["timing"] = {
                "elapsed_seconds": round(max(0.0, time.monotonic() - target_started_at), 1),
            }
            summaries.append(summary)
        attach_total_timing_and_completion_summaries(
            summaries,
            time.monotonic() - run_started_at,
            mode="style_selection",
        )
        write_runner_result(mode="style_selection", exit_code=0, summaries=summaries)
        print(json.dumps(summaries, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    for raw_target in args.target:
        target = Path(raw_target).expanduser().resolve()
        target_started_at = time.monotonic()
        summary = generate_for_target(
            target,
            args.description_style,
            classification_override,
            authoring_override,
            deployment_options,
            style_state_path=style_state_path,
            onboarding_template_id=getattr(args, "onboarding_template_id", None),
        )
        summary["timing"] = {
            "elapsed_seconds": round(max(0.0, time.monotonic() - target_started_at), 1),
        }
        summaries.append(summary)
        if summary["failures"]:
            exit_code = 1

    attach_total_timing_and_completion_summaries(
        summaries,
        time.monotonic() - run_started_at,
        mode="generation",
    )
    write_runner_result(mode="generation", exit_code=exit_code, summaries=summaries)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
