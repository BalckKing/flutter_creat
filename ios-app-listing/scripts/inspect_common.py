#!/usr/bin/env python3
"""Shared inspection helpers for iOS AppListing skills."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import tempfile
from legal_facts import inspect_legal_signals
from project_profile import build_project_profile
from pathlib import Path
from urllib.parse import urlparse


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def is_valid_image_file(path: Path) -> bool:
    """Require an image signature and a successful decode, not an extension."""
    try:
        with path.open("rb") as handle:
            header = handle.read(32)
    except (OSError, ValueError):
        return False
    if header.startswith(PNG_SIGNATURE):
        if len(header) < 24 or header[12:16] != b"IHDR":
            return False
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        if width <= 0 or height <= 0:
            return False
    elif not (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or (len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP")
    ):
        return False
    try:
        from PIL import Image
    except ImportError:
        decoder = shutil.which("sips")
        if not decoder:
            return False
        try:
            with tempfile.TemporaryDirectory(prefix="listing_image_check_") as temp_dir:
                output = Path(temp_dir) / "decoded.png"
                result = subprocess.run(
                    [decoder, "-s", "format", "png", str(path), "--out", str(output)],
                    capture_output=True, timeout=20,
                )
                return result.returncode == 0 and output.is_file() and output.stat().st_size > 32
        except (OSError, subprocess.SubprocessError):
            return False
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
        return True
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        return False


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
STRING_PATTERN = re.compile(r'(?<!\\)(["\'])(.*?)(?<!\\)\1', re.DOTALL)
URL_PATTERN = re.compile(r"https?://[^\s\"')>]+")
IAP_CODE_RE = re.compile(r"(?P<prefix>[A-Za-z][A-Za-z_]*)(?P<body>\d+)(?P<slot>0[1-9]|1[0-2])")
IAP_SIGNAL_RE = re.compile(
    r"goodsCode|storeProductIds|productIds|in_app_purchase|queryProductDetails|ProductDetails|PurchaseDetails|SKProduct|StoreKit|IAP",
    re.IGNORECASE,
)

CAPABILITY_RULES = {
    "feed": {
        "screen": [r"\bfeed\b", r"(?:feed|community)(?:view|screen|controller|page)$"],
        "route": [r"(?:^|/)(feed|community)(?:/|$)", r"(?:^|/)post(?:/|$)"],
        "entity": [r"\bpost\b", r"\bcomment\b"],
        "action": [r"(?:like|report|block|react|comment)(?:on)?(?:post|comment|user|member)"],
        "ui": [r"^(?:community|social|public) feed$", r"^(?:my|your|new|latest|public|community) posts?$", r"^(?:report|like|comment on) (?:a |this )?post$"],
        "dependency": [],
    },
    "profile": {
        "screen": [r"\bprofile\b"],
        "route": [r"(?:^|/)profile(?:/|$)", r"(?:^|/)me(?:/|$)"],
        "entity": [r"\bprofile\b"],
        "action": [r"updateprofile", r"editprofile", r"saveprofile"],
        "ui": [r"profile", r"edit profile"],
        "dependency": [],
    },
    "post_creation": {
        "screen": [r"\bcomposer\b", r"\bpublish\b", r"\bpostcreator\b", r"\bposteditor\b"],
        "route": [r"(?:^|/)compose(?:/|$)", r"(?:^|/)composer(?:/|$)", r"(?:^|/)publish(?:/|$)", r"(?:^|/)create-post(?:/|$)"],
        "entity": [r"\bpost\b", r"\bcaption\b", r"\bcomposer\b"],
        "action": [r"publish", r"createpost", r"submitpost"],
        "ui": [r"create a post", r"publish post", r"write a caption"],
        "dependency": [],
    },
    "messaging": {
        "screen": [r"\bchat\b", r"\bmessage\b", r"\binbox\b", r"\bthread\b"],
        "route": [r"/chat", r"/message", r"/inbox", r"/thread"],
        "entity": [r"\bmessage\b", r"\bconversation\b"],
        "action": [r"sendmessage", r"reply", r"openchat", r"markread"],
        "ui": [r"chat", r"inbox", r"message", r"conversation"],
        "dependency": [],
    },
    "recharge": {
        "screen": [r"\brecharge\b", r"\bwallet\b", r"\bbilling\b", r"\bpurchase\b"],
        "route": [r"/recharge", r"/wallet", r"/billing", r"/purchase"],
        "entity": [r"\bbalance\b", r"\bcredit\b", r"\btoken\b", r"\bpack\b"],
        "action": [r"purchase", r"recharge", r"restorepurchase", r"buy"],
        "ui": [r"wallet", r"credits", r"tokens", r"balance"],
        "dependency": [r"in_app_purchase", r"storekit", r"revenuecat", r"iap"],
    },
    "location": {
        "screen": [r"(?:map|location|nearby)(?:view|screen|controller|page)$", r"\bnearby\b"],
        "route": [r"/map", r"/location", r"/nearby"],
        "entity": [r"\b(?:coordinate|geolocation|gps)\b"],
        "action": [r"picklocation", r"searchlocation", r"requestlocation"],
        "ui": [r"\bmap view\b", r"\bnearby places\b", r"\bfind nearby\b", r"\bcurrent location\b", r"\buse my location\b", r"\blocation services\b", r"\broute guidance\b"],
        "dependency": [r"corelocation", r"mapkit", r"googlemaps", r"location"],
    },
    "translate_text": {
        "screen": [r"\btranslate\b", r"\btext\b"],
        "route": [r"/translate"],
        "entity": [r"\btranslation\b"],
        "action": [r"translate", r"translatetext"],
        "ui": [r"translate text", r"translation", r"source language"],
        "dependency": [],
    },
    "translate_voice": {
        "screen": [r"\bvoice\b", r"\bspeech\b", r"\btranslate\b"],
        "route": [r"/voice", r"/speech", r"/translate"],
        "entity": [r"\btranscript\b", r"\btranslation\b"],
        "action": [r"transcribe", r"recordvoice", r"translatevoice"],
        "ui": [r"voice", r"spoken language", r"record"],
        "dependency": [r"speech", r"avfoundation"],
    },
    "beauty_editing": {
        "screen": [r"\bbeauty\b", r"\bretouch\b", r"\bphotoeditor\b", r"\bimageeditor\b", r"\boverlay\b", r"\bportrait\b"],
        "route": [r"(?:^|/)beauty(?:/|$)", r"(?:^|/)retouch(?:/|$)", r"(?:^|/)photo-editor(?:/|$)", r"(?:^|/)image-editor(?:/|$)"],
        "entity": [r"\bretouch\b", r"\boverlay\b", r"\bportrait\b"],
        "action": [r"retouch", r"applyfilter", r"enhanceimage", r"cropimage", r"mirrorimage"],
        "ui": [
            r"beauty",
            r"retouch",
            r"photo editor",
            r"portrait photo editor",
            r"overlay",
            r"\bcrop\b",
            r"\bmirror\b",
        ],
        "dependency": [],
    },
    "education": {
        "screen": [r"\blesson\b", r"\bcourse\b", r"\bquiz\b", r"\blearn\b"],
        "route": [r"/lesson", r"/course", r"/quiz", r"/learn"],
        "entity": [r"\blesson\b", r"\bquiz\b"],
        "action": [r"startlesson", r"startquiz", r"completecourse"],
        "ui": [r"lesson", r"course", r"quiz"],
        "dependency": [],
    },
    "budgeting": {
        "screen": [r"\bbudget\b", r"\bexpense\b", r"\bfinance\b", r"\bwallet\b"],
        "route": [r"/budget", r"/expense", r"/finance"],
        "entity": [r"\bexpense\b", r"\bbudget\b", r"\btransaction\b"],
        "action": [r"addexpense", r"trackexpense", r"savebudget"],
        "ui": [r"budget", r"expense", r"finance"],
        "dependency": [],
    },
    "ai_chat": {
        "screen": [r"\bassistant\b", r"\bcopilot\b", r"\bchatgpt\b", r"\bllm\b"],
        "route": [r"/assistant", r"/copilot", r"/prompt", r"/ai-assistant", r"/ai/chat"],
        "entity": [r"\bcompletion\b", r"\bassistant\b"],
        "action": [r"sendprompt", r"generateanswer", r"requestcompletion", r"askassistant"],
        "ui": [r"assistant", r"ask ai", r"chat with ai", r"ai assistant"],
        "dependency": [r"openai", r"anthropic", r"gemini", r"langchain"],
    },
    "ai_image_generation": {
        "screen": [r"\bgenerator\b", r"\bavatar\b", r"characterstudio", r"characterresult", r"\btryon\b", r"\bpreview\b"],
        "route": [r"(?:^|/)generate(?:/|$)", r"(?:^|/)avatar(?:/|$)", r"(?:^|/)character_result(?:/|$)", r"(?:^|/)dream(?:/|$)", r"(?:^|/)tryon(?:/|$)", r"(?:^|/)preview(?:/|$)"],
        "entity": [r"\bgeneration\b", r"\bcharacter\b", r"\bpreview\b", r"\btryon\b"],
        "action": [r"generateimage", r"renderimage", r"createavatar", r"generateavatar", r"fetchcharacterimage", r"generatecharacter"],
        "ui": [r"generate image", r"avatar", r"image generation", r"draft character", r"character studio", r"preview could not load"],
        "dependency": [r"openai", r"replicate", r"stability", r"diffusers"],
    },
}

WEIGHTS = {
    "screen": 1.2,
    "route": 1.0,
    "entity": 0.9,
    "action": 0.8,
    "ui": 0.7,
    "dependency": 0.6,
}

EVIDENCE_SOURCE_KEYS = {
    "screen": "screens",
    "route": "routes",
    "entity": "entities",
    "action": "actions",
    "ui": "ui_strings",
}

PERMISSION_LABELS = {
    "NSCameraUsageDescription": "camera",
    "NSMicrophoneUsageDescription": "microphone",
    "NSPhotoLibraryUsageDescription": "photo_library",
    "NSPhotoLibraryAddUsageDescription": "photo_library_add",
    "NSUserTrackingUsageDescription": "tracking",
    "NSLocationWhenInUseUsageDescription": "location_when_in_use",
    "NSLocationAlwaysAndWhenInUseUsageDescription": "location_always",
    "NSContactsUsageDescription": "contacts",
    "NSSpeechRecognitionUsageDescription": "speech_recognition",
    "NSFaceIDUsageDescription": "face_id",
}

ANALYTICS_HINTS = [
    "firebase",
    "amplitude",
    "mixpanel",
    "appsflyer",
    "adjust",
    "analytics",
]

AI_PROVIDER_HINTS = {
    "Alibaba Cloud DashScope": ["dashscope.aliyuncs.com", "aliyuncs.com", "dashscope"],
    "OpenAI": ["openai", "chatgpt", "api.openai.com"],
    "Anthropic": ["anthropic", "claude", "api.anthropic.com"],
    "Google Gemini": ["gemini", "generativelanguage.googleapis.com", "vertexai"],
    "Replicate": ["replicate", "api.replicate.com"],
    "Hugging Face": ["huggingface", "hf.space"],
}

AI_TYPE_HINTS = {
    "ai_chat": ["assistant", "ask ai", "completion", "copilot", "chatgpt", "llm"],
    "third_party_inference": ["inference", "completion", "model provider", "api.openai.com", "api.anthropic.com"],
    "image_generation": ["generate image", "avatar", "diffusion", "image generator", "create avatar"],
}

AI_PREVIEW_MARKERS = [
    "ai preview",
    "preview result",
    "generated preview",
    "image preview",
    "tryon",
    "try-on",
    "try on",
    "/image-preview",
    "/tryon",
]

AI_PREVIEW_CONSENT_MARKERS = [
    "consent",
    "agree & continue",
    "agree to continue",
    "ensureconsent",
    "presentconsentdialog",
    "remember ai preview consent",
    "preview consent",
]

AI_PREVIEW_SELECTED_PHOTO_MARKERS = [
    "choose a photo",
    "choose photo",
    "choose from photo library",
    "take photo",
    "capture a new photo",
    "selected user photo",
    "user photo",
    "person image",
    "portrait",
]

AI_PREVIEW_SAVE_MARKERS = [
    "save the result",
    "save result",
    "save image",
    "save to photos",
    "saved to photos",
    "save a generated preview",
    "image_gallery_saver",
    "commitimageingallery",
]

AI_PREVIEW_GENERATED_RESULT_MARKERS = [
    "generated image",
    "generated preview",
    "preview result",
    "generated image url",
    "ai preview",
]

AI_PREVIEW_TEMP_CACHE_MARKERS = [
    "temporary preview file",
    "cached preview",
    "preview result cached",
    "deleted temporary preview file",
]

AI_PREVIEW_REFERENCE_MARKERS = [
    "reference image",
    "product image",
    "shoe image",
    "heels image",
]

AI_TRANSLATION_FACE_VISIBILITY_MARKERS = [
    "face visibility consent",
    "image translation",
    "translation providers",
    "text extraction and translation",
]

AI_ACCESS_CONTEXT_HINTS = (
    "ai",
    "assistant",
    "copilot",
    "guide",
    "tryon",
    "preview",
    "translate",
    "generator",
    "avatar",
)

AI_AUTH_CONTEXT_PATH_HINTS = (
    "main",
    "app",
    "entry",
    "launch",
    "login",
    "root",
    "shell",
    "scene",
    "delegate",
)

AI_RUNTIME_ENABLED_PATTERNS = (
    ("enabled_flag", re.compile(r"\b(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:enabled|available|active)\b\s*[:=]\s*true")),
    (
        "configured_endpoint",
        re.compile(
            r"\b(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:apikey|api_key|endpoint|baseurl|base_url|model)\b\s*[:=]\s*['\"](?!\s*['\"])"
        ),
    ),
    (
        "nonempty_guard",
        re.compile(
            r"\bhas[a-z0-9_]*(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:apikey|api_key|token|endpoint|baseurl|base_url|model)\b[^\n]{0,100}\bisnotempty\b"
        ),
    ),
)

AI_RUNTIME_DISABLED_PATTERNS = (
    ("disabled_flag", re.compile(r"\b(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:enabled|available|active)\b\s*[:=]\s*false")),
    (
        "empty_config",
        re.compile(
            r"\b(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:apikey|api_key|token|endpoint|baseurl|base_url|model)\b\s*[:=]\s*['\"]\s*['\"]"
        ),
    ),
    (
        "empty_guard",
        re.compile(
            r"\b(?:ai|assistant|copilot|guide|tryon|preview)[a-z0-9_]*(?:apikey|api_key|token|endpoint|baseurl|base_url|model)\b[^\n]{0,100}\bisempty\b"
        ),
    ),
)

AI_AUTH_GATE_PATTERNS = (
    ("login_route", re.compile(r"\bloginroute\b")),
    ("login_redirect", re.compile(r"\b(?:get\.(?:offallnamed|offnamed|tonamed)|navigator\.(?:pushnamed|of\(context\)\.pushnamed)|context\.(?:go|push))\b[^\n]{0,120}\blogin\b")),
    ("launch_auth_switch", re.compile(r"\b(?:isloggedin|hasauthtoken|authtoken|token)\b[^\n]{0,120}\blogin\b")),
    ("login_flow", re.compile(r"\bloginuntil\.login\b")),
    ("sign_in_prompt", re.compile(r"\b(?:sign in to continue|quick sign in|log in to continue)\b")),
)

ACCESS_IDENTITY_INPUT_PATTERNS = (
    ("email_field", re.compile(r"\b(?:email|e-mail|email address)\b[^\n]{0,120}\b(?:field|textfield|textformfield|textinput|controller|text field)\b")),
    ("username_field", re.compile(r"\b(?:username|user name)\b[^\n]{0,120}\b(?:field|textfield|textformfield|textinput|controller|text field)\b")),
    ("phone_field", re.compile(r"\b(?:phone|phone number)\b[^\n]{0,120}\b(?:field|textfield|textformfield|textinput|controller|text field)\b")),
)

ACCESS_PASSWORD_INPUT_PATTERNS = (
    ("password_field", re.compile(r"\bpassword\b[^\n]{0,120}\b(?:field|textfield|textformfield|textinput|controller|text field)\b")),
    ("secure_password_field", re.compile(r"\b(?:password|passcode)\b[^\n]{0,120}\b(?:securefield|obscuretext|securetextentry|issecuretextentry)\b")),
)

ACCESS_AUTH_ACTION_PATTERNS = (
    ("login_action", re.compile(r"\b(?:login|log in|signin|sign in|signup|sign up|register|authenticate)\b")),
    ("email_password_auth", re.compile(r"\b(?:signinwithemailandpassword|createuserwithemailandpassword|sign_in_with_email_and_password|create_user_with_email_and_password)\b")),
    ("credential_auth", re.compile(r"\b(?:signinwithcredential|performrequests|authorizationcontroller|authorize)\b")),
)

ACCESS_EXTERNAL_AUTH_TEXT_PATTERNS = (
    ("apple_sign_in", re.compile(r"\b(?:sign in with apple|asauthorizationappleidprovider|appleidcredential|authenticationservices)\b")),
    ("google_sign_in", re.compile(r"\b(?:sign in with google|gidsignin|google sign in)\b")),
    ("firebase_auth", re.compile(r"\b(?:firebaseauth|signinwithcredential|signinwithemailandpassword|createuserwithemailandpassword)\b")),
    ("oauth", re.compile(r"\b(?:oauth|auth0|openid|openidconnect|pkce)\b")),
)

ACCESS_AUTH_ENDPOINT_PATTERNS = (
    ("auth_route", re.compile(r"(?:^|[\"'])/(?:login|signin|signup|register|auth)(?:/|[\"'])")),
    ("auth_endpoint", re.compile(r"https?://[^\s\"']*(?:login|signin|signup|register|oauth|token|session)\b")),
)

ACCESS_LOCAL_SESSION_PATTERNS = (
    ("logout", re.compile(r"\b(?:logout|log out|signout|sign out)\b")),
    ("session_state", re.compile(r"\b(?:isloggedin|loggedin|restore session|resume session|user session|session state)\b")),
    ("quick_entry", re.compile(r"\b(?:quick sign in|continue as guest|guest mode|continue without account|skip login)\b")),
    ("session_store", re.compile(r"\b(?:sharedpreferences|userdefaults|fluttersecurestorage|keychain|save session|clear session|store session)\b")),
)

ACCESS_EXTERNAL_AUTH_DEPENDENCY_PATTERNS = [
    r"firebase_auth",
    r"google_sign_in",
    r"googleidentity",
    r"authenticationservices",
    r"appauth",
    r"auth0",
    r"oauth",
]

AI_PAYWALL_TOKENS = (
    "credit",
    "credits",
    "balance",
    "recharge",
    "top up",
    "topup",
    "wallet",
    "purchase",
    "subscription",
    "premium",
    "vip",
    "requiredcredits",
    "messagecost",
    "previewcreditcost",
    "signalopencreditswallet",
    "not enough credits",
    "free tryon",
    "free preview",
)

IGNORED_DIR_NAMES = {
    "package",
    "packages",
    "pods",
    "build",
    ".build",
    ".dart_tool",
    ".git",
    ".idea",
    ".vscode",
    ".topic-change",
    ".topic_change",
    ".reskin",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def path_has_ignored_dir(path: Path, ignored: set[str] | None = None) -> bool:
    blocked = ignored or IGNORED_DIR_NAMES
    return any(part.lower() in blocked for part in path.parts)


def iter_paths(
    root: Path,
    pattern: str,
    ignored: set[str] | None = None,
    *,
    include_files: bool = True,
    include_dirs: bool = False,
):
    blocked = {item.lower() for item in (ignored or IGNORED_DIR_NAMES)}
    if root.is_file():
        if include_files and fnmatch.fnmatch(root.name, pattern) and not path_has_ignored_dir(root, blocked):
            yield root
        return

    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if name.lower() not in blocked]
        dir_names.sort()
        file_names.sort()
        current_path = Path(current_root)
        if include_dirs:
            for name in dir_names:
                if fnmatch.fnmatch(name, pattern):
                    yield current_path / name
        if include_files:
            for name in file_names:
                if fnmatch.fnmatch(name, pattern):
                    yield current_path / name


def iter_files(root: Path, pattern: str, ignored: set[str] | None = None):
    yield from iter_paths(root, pattern, ignored, include_files=True, include_dirs=False)


def iter_dirs(root: Path, pattern: str, ignored: set[str] | None = None):
    yield from iter_paths(root, pattern, ignored, include_files=False, include_dirs=True)


def title_case_slug(value: str) -> str:
    cleaned = re.sub(r"[_\\-]+", " ", value).strip()
    return " ".join(part.capitalize() for part in cleaned.split()) or "App"


def to_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower()) or "app"


def normalize_string(value: str) -> str:
    return re.sub(r"\\s+", " ", value).strip()


def extract_ui_strings(text: str) -> list[str]:
    results: list[str] = []
    for _, value in STRING_PATTERN.findall(text):
        candidate = normalize_string(value)
        if len(candidate) < 3 or len(candidate) > 160:
            continue
        if "assets/" in candidate or "http://" in candidate or "https://" in candidate:
            continue
        if re.fullmatch(r"[A-Za-z0-9_./:-]+", candidate):
            continue
        if not re.search(r"[A-Za-z]", candidate):
            continue
        results.append(candidate)
    return results


def extract_string_literals(text: str) -> list[str]:
    literals: list[str] = []
    for _, value in STRING_PATTERN.findall(text):
        candidate = normalize_string(value)
        if candidate:
            literals.append(candidate)
    return literals


def match_patterns(values: list[str], patterns: list[str]) -> list[str]:
    hits: list[str] = []
    lower_values = [value.lower() for value in values]
    for pattern in patterns:
        regex = re.compile(pattern)
        for original, lowered in zip(values, lower_values):
            if regex.search(lowered):
                hits.append(original)
    return sorted(set(hits))


def infer_capability_candidates(evidence: dict[str, list[str]], dependencies: list[str]) -> dict[str, dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}
    dep_values = [item.lower() for item in dependencies]

    for capability, rules in CAPABILITY_RULES.items():
        score = 0.0
        hits: dict[str, list[str]] = {}
        for source in ("screen", "route", "entity", "action", "ui"):
            values = evidence.get(EVIDENCE_SOURCE_KEYS[source], [])
            matched = match_patterns(values, rules[source])
            if matched:
                hits[source] = matched[:6]
                score += WEIGHTS[source] * len(matched)
        dep_hits = match_patterns(dep_values, rules["dependency"])
        if dep_hits:
            hits["dependency"] = dep_hits[:6]
            score += WEIGHTS["dependency"] * len(dep_hits)
        if score > 0:
            candidates[capability] = {
                "score": round(score, 2),
                "confidence": "high" if score >= 3.0 else "medium" if score >= 1.5 else "low",
                "evidence": hits,
            }
    return dict(sorted(candidates.items(), key=lambda item: (-float(item[1]["score"]), item[0])))


def extract_support_email(app_root: Path) -> str | None:
    # Ignore generated listing output so old artifacts cannot become "explicit"
    # support evidence for a new inspection run.
    for rel in ["README.md", "docs", "Sources", "lib", "ios"]:
        root = app_root / rel
        if not root.exists():
            continue
        paths = [root] if root.is_file() else iter_files(root, "*")
        for path in paths:
            if not path.is_file():
                continue
            if path_has_ignored_dir(path):
                continue
            if path.suffix.lower() not in {".swift", ".dart", ".md", ".html", ".txt", ".yaml", ".yml", ".plist"}:
                continue
            match = EMAIL_PATTERN.search(read_text(path))
            if match:
                return match.group(0)
    return None


def support_email_facts(app_root: Path) -> dict[str, str | None]:
    email = extract_support_email(app_root)
    return {
        "support_email": email,
        "support_email_source": "explicit" if email else "missing",
    }


def extract_url_hosts(urls: list[str]) -> list[str]:
    hosts = []
    for url in urls:
        try:
            host = (urlparse(url).hostname or "").strip().lower()
        except ValueError:
            host = ""
        if host:
            hosts.append(host)
    return sorted(set(hosts))


def keyword_hits(values: list[str], keywords: list[str], limit: int = 6) -> list[str]:
    hits: list[str] = []
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for value in values:
        lowered_value = value.lower()
        if any(keyword in lowered_value for keyword in lowered_keywords):
            hits.append(value)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in hits:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped[:limit]


def blob_contains_hint(blob: str, hint: str) -> bool:
    lowered_hint = hint.lower()
    if " " in lowered_hint or any(token in lowered_hint for token in (":", "/", ".", "-", "_")):
        return lowered_hint in blob
    return re.search(rf"\b{re.escape(lowered_hint)}\b", blob) is not None


def _file_has_hint(relative_path: str, text: str, hints: tuple[str, ...]) -> bool:
    lowered_path = relative_path.lower()
    lowered_text = text.lower()
    return any(hint in lowered_path or hint in lowered_text for hint in hints)


def _append_unique_hit(target: list[str], value: str, *, limit: int = 6) -> bool:
    if value in target:
        return False
    target.append(value)
    return len(target) >= limit


def _collect_pattern_hits(
    file_cache: dict[str, str],
    patterns: tuple[tuple[str, re.Pattern], ...],
    *,
    include_paths: set[str] | None = None,
    path_hints: tuple[str, ...] = (),
    require_ai_context: bool = False,
    limit: int = 6,
) -> list[str]:
    hits: list[str] = []
    for relative_path in sorted(file_cache):
        lowered_path = relative_path.lower()
        if include_paths is not None and relative_path not in include_paths and not any(token in lowered_path for token in path_hints):
            continue
        text = file_cache[relative_path]
        if require_ai_context and not _file_has_hint(relative_path, text, AI_ACCESS_CONTEXT_HINTS):
            continue
        lowered_text = text.lower()
        for label, pattern in patterns:
            if not pattern.search(lowered_text):
                continue
            if _append_unique_hit(hits, f"{relative_path}: {label}", limit=limit):
                return hits
    return hits


def _collect_token_hits(
    file_cache: dict[str, str],
    tokens: tuple[str, ...],
    *,
    include_paths: set[str] | None = None,
    path_hints: tuple[str, ...] = (),
    require_ai_context: bool = False,
    limit: int = 6,
) -> list[str]:
    hits: list[str] = []
    for relative_path in sorted(file_cache):
        lowered_path = relative_path.lower()
        if include_paths is not None and relative_path not in include_paths and not any(token in lowered_path for token in path_hints):
            continue
        text = file_cache[relative_path]
        if require_ai_context and not _file_has_hint(relative_path, text, AI_ACCESS_CONTEXT_HINTS):
            continue
        lowered_text = text.lower()
        for token in tokens:
            if token not in lowered_path and token not in lowered_text:
                continue
            if _append_unique_hit(hits, f"{relative_path}: {token}", limit=limit):
                return hits
    return hits


def ai_reachability_paths(ai_reachability: dict[str, object]) -> set[str]:
    paths: set[str] = set()
    candidate_files = ai_reachability.get("candidate_files", [])
    if isinstance(candidate_files, list):
        for item in candidate_files:
            if isinstance(item, str) and item.strip():
                paths.add(item.strip())

    evidence = ai_reachability.get("evidence", {})
    if not isinstance(evidence, dict):
        return paths
    for items in evidence.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, str):
                continue
            relative_path, _, _ = item.partition(":")
            if relative_path.strip():
                paths.add(relative_path.strip())
    return paths


def analyze_ai_access_profile(
    file_cache: dict[str, str],
    ai_reachability: dict[str, object],
    *,
    code_present: bool,
) -> dict[str, object]:
    relevant_paths = ai_reachability_paths(ai_reachability)
    structural_entry = bool(
        ai_reachability.get("route_registered")
        or ai_reachability.get("navigation_invoked")
        or ai_reachability.get("entry_surface_visible")
        or ai_reachability.get("claimable")
    )

    runtime_enabled_hits = _collect_pattern_hits(
        file_cache,
        AI_RUNTIME_ENABLED_PATTERNS,
        require_ai_context=True,
    )
    runtime_disabled_hits = _collect_pattern_hits(
        file_cache,
        AI_RUNTIME_DISABLED_PATTERNS,
        require_ai_context=True,
    )
    auth_hits = (
        _collect_pattern_hits(
            file_cache,
            AI_AUTH_GATE_PATTERNS,
            include_paths=relevant_paths if relevant_paths else None,
            path_hints=AI_AUTH_CONTEXT_PATH_HINTS,
        )
        if structural_entry
        else []
    )
    paywall_hits = (
        _collect_token_hits(
            file_cache,
            AI_PAYWALL_TOKENS,
            include_paths=relevant_paths if relevant_paths else None,
            require_ai_context=bool(relevant_paths),
        )
        if structural_entry
        else []
    )

    return {
        "runtime_enabled": bool(code_present) and not runtime_disabled_hits,
        "auth_gated": bool(code_present) and structural_entry and bool(auth_hits),
        "paywall_gated": bool(code_present) and structural_entry and bool(paywall_hits),
        "residual_code": bool(code_present) and not structural_entry,
        "runtime_evidence": {
            "enabled_hits": runtime_enabled_hits,
            "disabled_hits": runtime_disabled_hits,
        },
        "gating_evidence": {
            "auth_hits": auth_hits,
            "paywall_hits": paywall_hits,
        },
    }


def finalize_ai_signals(
    ai_signals: dict[str, object],
    ai_reachability: dict[str, object],
    file_cache: dict[str, str],
) -> dict[str, object]:
    code_present = bool(ai_signals.get("active"))
    access_profile = analyze_ai_access_profile(file_cache, ai_reachability, code_present=code_present)
    runtime_enabled = bool(access_profile.get("runtime_enabled"))

    ai_signals["code_present"] = code_present
    ai_signals["route_registered"] = code_present and bool(ai_reachability.get("route_registered"))
    ai_signals["navigation_invoked"] = code_present and bool(ai_reachability.get("navigation_invoked"))
    ai_signals["entry_surface_visible"] = code_present and bool(ai_reachability.get("entry_surface_visible"))
    ai_signals["runtime_enabled"] = code_present and runtime_enabled
    ai_signals["auth_gated"] = code_present and bool(access_profile.get("auth_gated"))
    ai_signals["paywall_gated"] = code_present and bool(access_profile.get("paywall_gated"))
    ai_signals["residual_code"] = code_present and bool(access_profile.get("residual_code"))
    structural_entry = bool(
        ai_reachability.get("route_registered")
        or ai_reachability.get("navigation_invoked")
        or ai_reachability.get("entry_surface_visible")
        or ai_reachability.get("claimable")
    )
    ai_signals["user_reachable"] = code_present and runtime_enabled and bool(
        ai_reachability.get("user_reachable") or structural_entry
    )
    ai_signals["claimable"] = code_present and runtime_enabled and bool(
        ai_reachability.get("claimable") or structural_entry
    )
    ai_signals["active"] = code_present
    ai_signals["reachability"] = ai_reachability
    ai_signals["disclosure_required"] = bool(
        ai_signals["claimable"] or (code_present and runtime_enabled and structural_entry)
    )
    ai_signals["runtime_evidence"] = access_profile.get("runtime_evidence", {})
    ai_signals["gating_evidence"] = access_profile.get("gating_evidence", {})
    return ai_signals


def _parse_app_icon_scale(value: object) -> int:
    if not isinstance(value, str):
        return 1
    match = re.fullmatch(r"(\d+)x", value.strip())
    if match is None:
        return 1
    return max(1, int(match.group(1)))


def _parse_app_icon_size(value: object) -> int:
    if not isinstance(value, str):
        return 0
    match = re.fullmatch(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", value.strip())
    if match is None:
        return 0
    try:
        width = float(match.group(1))
        height = float(match.group(2))
    except ValueError:
        return 0
    return int(round(max(width, height)))


def _app_icon_candidates_from_set(iconset_root: Path, app_root: Path) -> list[tuple[tuple[int, int, int, str], str]]:
    contents_path = iconset_root / "Contents.json"
    candidates: list[tuple[tuple[int, int, int, str], str]] = []

    if contents_path.exists():
        try:
            payload = json.loads(read_text(contents_path))
        except json.JSONDecodeError:
            payload = {}
        images = payload.get("images", []) if isinstance(payload, dict) else []
        if isinstance(images, list):
            for item in images:
                if not isinstance(item, dict):
                    continue
                filename = item.get("filename")
                if not isinstance(filename, str) or not filename.strip():
                    continue
                candidate = iconset_root / filename.strip()
                if not candidate.exists() or not candidate.is_file():
                    continue
                idiom = str(item.get("idiom", "")).strip().lower()
                scale = _parse_app_icon_scale(item.get("scale"))
                base_size = _parse_app_icon_size(item.get("size"))
                rendered_size = base_size * scale
                is_marketing = 1 if idiom == "ios-marketing" else 0
                rel = str(candidate.relative_to(app_root))
                candidates.append(((is_marketing, rendered_size, scale, rel), rel))

    if candidates:
        return candidates

    # Fallback when Contents.json is missing or incomplete: still constrain to AppIcon.appiconset assets only.
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for path in iter_files(iconset_root, ext):
            rel = str(path.relative_to(app_root))
            candidates.append(((0, 0, 0, rel), rel))
    return candidates


def find_logo_candidates(app_root: Path, slug: str) -> list[str]:
    del slug
    # The workflow's verified source logo is authoritative. Keep it ahead of
    # any stale AppIcon export so About pages cannot silently revert branding.
    explicit_logo_paths = [
        app_root / "assets" / "logo.png",
        app_root / "ios" / "Runner" / "assets" / "logo.png",
    ]
    explicit_results: list[str] = []
    for path in explicit_logo_paths:
        if path.is_file() and is_valid_image_file(path):
            explicit_results.append(str(path.relative_to(app_root)))

    iconset_roots = [
        app_root / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset",
        app_root / "Assets.xcassets" / "AppIcon.appiconset",
    ]
    ranked: list[tuple[tuple[int, int, int, str], str]] = []
    for root in iconset_roots:
        if not root.exists():
            continue
        ranked.extend(_app_icon_candidates_from_set(root, app_root))

    ranked.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2], item[0][3]))
    seen: set[str] = set()
    results: list[str] = []
    for _, rel in ranked:
        if rel in seen:
            continue
        seen.add(rel)
        path = app_root / rel
        if app_root.resolve() not in path.resolve().parents or not is_valid_image_file(path):
            continue
        results.append(rel)
    return [*explicit_results, *results][:8]


def check_existing_listing(app_root: Path) -> dict[str, object]:
    site = app_root / "AppListing" / "site"
    return {
        "has_site": site.exists(),
        "has_intro": (app_root / "AppListing" / "Intro.md").exists(),
        "has_privacy": (site / "PrivacyPolicy.html").exists() if site.exists() else False,
        "has_terms": (site / "TermsConditions.html").exists() if site.exists() else False,
    }


def parse_permissions_from_info(info: dict[object, object]) -> dict[str, str]:
    permissions: dict[str, str] = {}
    for key, label in PERMISSION_LABELS.items():
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            permissions[label] = value.strip()
    return permissions


def extract_iap_codes_from_literals(values: list[str]) -> list[str]:
    codes: list[str] = []
    for value in values:
        candidate = str(value).strip()
        if not candidate:
            continue
        match = IAP_CODE_RE.fullmatch(candidate)
        if match is None:
            continue
        codes.append(match.group(0))
    return sorted(set(codes))


def extract_iap_codes_from_content(content: str) -> list[str]:
    if not IAP_SIGNAL_RE.search(content):
        return []
    return extract_iap_codes_from_literals(extract_string_literals(content))


def format_iap_shop_code_display(iap_codes: list[str]) -> str:
    normalized_codes = sorted(set(str(code).strip() for code in iap_codes if str(code).strip()))
    if not normalized_codes:
        return "None detected"

    grouped: dict[tuple[str, int], list[int]] = {}
    for code in normalized_codes:
        match = IAP_CODE_RE.fullmatch(code)
        if match is None:
            continue
        prefix = match.group("prefix")
        numeric = f"{match.group('body')}{match.group('slot')}"
        key = (prefix, len(numeric))
        grouped.setdefault(key, []).append(int(numeric))

    display_parts: list[str] = []
    for prefix, width in sorted(grouped.keys()):
        numbers = sorted(set(grouped[(prefix, width)]))
        if not numbers:
            continue
        run_start = numbers[0]
        previous = numbers[0]
        for number in numbers[1:] + [None]:
            if number is not None and number == previous + 1:
                previous = number
                continue
            start_code = f"{prefix}{run_start:0{width}d}"
            end_code = f"{prefix}{previous:0{width}d}"
            if run_start == previous:
                display_parts.append(start_code)
            else:
                display_parts.append(f"{start_code} - {end_code}")
            if number is not None:
                run_start = number
                previous = number

    return ", ".join(display_parts) if display_parts else "None detected"


def strip_dart_comments(text: str) -> str:
    cleaned: list[str] = []
    index = 0
    length = len(text)
    string_delimiter: str | None = None
    triple_quoted = False

    while index < length:
        if string_delimiter is not None:
            if triple_quoted and text.startswith(string_delimiter * 3, index):
                cleaned.append(string_delimiter * 3)
                index += 3
                string_delimiter = None
                triple_quoted = False
                continue

            char = text[index]
            cleaned.append(char)
            if not triple_quoted and char == "\\" and index + 1 < length:
                cleaned.append(text[index + 1])
                index += 2
                continue
            if not triple_quoted and char == string_delimiter:
                string_delimiter = None
            index += 1
            continue

        if text.startswith("'''", index) or text.startswith('"""', index):
            string_delimiter = text[index]
            triple_quoted = True
            cleaned.append(string_delimiter * 3)
            index += 3
            continue

        char = text[index]
        next_char = text[index + 1] if index + 1 < length else ""

        if char in {"'", '"'}:
            string_delimiter = char
            triple_quoted = False
            cleaned.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            index += 2
            while index < length and text[index] != "\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            index += 2
            depth = 1
            while index < length and depth > 0:
                if text.startswith("/*", index):
                    depth += 1
                    index += 2
                    continue
                if text.startswith("*/", index):
                    depth -= 1
                    index += 2
                    continue
                if text[index] == "\n":
                    cleaned.append("\n")
                index += 1
            continue

        cleaned.append(char)
        index += 1

    return "".join(cleaned)


def extract_brand_colors_from_dart(paths: list[Path], app_root: Path) -> list[dict[str, str]]:
    seen: set[str] = set()
    colors: list[dict[str, str]] = []
    pattern = re.compile(r"([A-Za-z0-9_]+)\s*=\s*Color\(0x([A-Fa-f0-9]{8})\)")
    for path in paths:
        text = strip_dart_comments(read_text(path))
        for match in pattern.finditer(text):
            name = match.group(1)
            hex_value = f"#{match.group(2)[2:].upper()}"
            key = f"{name}:{hex_value}"
            if key in seen:
                continue
            seen.add(key)
            colors.append({"name": name, "hex": hex_value, "source": str(path.relative_to(app_root))})
    return colors[:12]


def _component_to_hex(component: str) -> str:
    value = max(0.0, min(1.0, float(component)))
    return f"{round(value * 255):02X}"


def extract_brand_colors_from_xcassets(app_root: Path) -> list[dict[str, str]]:
    colors: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in iter_files(app_root, "Contents.json"):
        if path.parent.suffix != ".colorset":
            continue
        try:
            payload = json.loads(read_text(path))
        except json.JSONDecodeError:
            continue
        for color in payload.get("colors", []):
            if not isinstance(color, dict):
                continue
            components = color.get("color", {}).get("components", {})
            if not isinstance(components, dict):
                continue
            if not {"red", "green", "blue"} <= set(components.keys()):
                continue
            try:
                hex_value = (
                    "#"
                    + _component_to_hex(str(components["red"]))
                    + _component_to_hex(str(components["green"]))
                    + _component_to_hex(str(components["blue"]))
                )
            except ValueError:
                continue
            name = path.parent.stem
            key = f"{name}:{hex_value}"
            if key in seen:
                continue
            seen.add(key)
            colors.append({"name": name, "hex": hex_value, "source": str(path.relative_to(app_root))})
    return colors[:12]


def analyze_ai_preview_review_profile(
    evidence: dict[str, list[str]],
    permissions: dict[str, str],
    dependencies: list[str],
) -> dict[str, object]:
    preview_values = [
        *evidence.get("screens", []),
        *evidence.get("routes", []),
        *evidence.get("actions", []),
        *evidence.get("ui_strings", []),
        *dependencies,
    ]
    preview_hits = keyword_hits(preview_values, AI_PREVIEW_MARKERS)
    consent_hits = keyword_hits(preview_values, AI_PREVIEW_CONSENT_MARKERS)
    selected_photo_hits = keyword_hits(preview_values, AI_PREVIEW_SELECTED_PHOTO_MARKERS)
    save_hits = keyword_hits(preview_values, AI_PREVIEW_SAVE_MARKERS)
    generated_result_hits = keyword_hits(preview_values, AI_PREVIEW_GENERATED_RESULT_MARKERS)
    temp_cache_hits = keyword_hits(preview_values, AI_PREVIEW_TEMP_CACHE_MARKERS)
    reference_hits = keyword_hits(preview_values, AI_PREVIEW_REFERENCE_MARKERS)

    has_photo_permissions = any(
        key in permissions for key in ("camera", "photo_library", "photo_library_add")
    )
    preview_or_tryon = bool(preview_hits)
    selected_photo = bool(selected_photo_hits) or (preview_or_tryon and has_photo_permissions)
    consent_prompt = bool(consent_hits)
    save_to_photos = "photo_library_add" in permissions or bool(save_hits)
    generated_result = bool(generated_result_hits) or preview_or_tryon
    reference_image = bool(reference_hits)
    temporary_cache = bool(temp_cache_hits)
    face_visibility_translation_hits = keyword_hits(
        preview_values,
        AI_TRANSLATION_FACE_VISIBILITY_MARKERS,
    )
    translation_face_visibility = bool(face_visibility_translation_hits)
    workflow_kind = "preview"
    if translation_face_visibility:
        workflow_kind = "translation_face_visibility"
    face_data_likely = preview_or_tryon and selected_photo
    if translation_face_visibility and has_photo_permissions:
        face_data_likely = True
    needs_face_data_clauses = all(
        [
            preview_or_tryon or translation_face_visibility,
            selected_photo,
            consent_prompt,
            save_to_photos or translation_face_visibility,
            generated_result or translation_face_visibility,
            has_photo_permissions,
        ]
    )

    return {
        "workflow_kind": workflow_kind,
        "preview_or_tryon": preview_or_tryon,
        "translation_face_visibility": translation_face_visibility,
        "selected_photo": selected_photo,
        "consent_prompt": consent_prompt,
        "save_to_photos": save_to_photos,
        "generated_result": generated_result,
        "reference_image": reference_image,
        "temporary_cache": temporary_cache,
        "face_data_likely": face_data_likely,
        "needs_face_data_clauses": needs_face_data_clauses,
        "evidence": {
            "preview": preview_hits,
            "consent": consent_hits,
            "selected_photo": selected_photo_hits,
            "save": save_hits,
            "generated_result": generated_result_hits,
            "temporary_cache": temp_cache_hits,
            "reference_image": reference_hits,
            "translation_face_visibility": face_visibility_translation_hits,
        },
    }


def analyze_ai_signals(
    evidence: dict[str, list[str]],
    dependencies: list[str],
    urls: list[str],
    permissions: dict[str, str],
) -> dict[str, object]:
    dep_blob = " ".join(item.lower() for item in dependencies)
    ui_blob = " ".join(item.lower() for item in evidence.get("ui_strings", []))
    screen_blob = " ".join(item.lower() for item in evidence.get("screens", []))
    route_blob = " ".join(item.lower() for item in evidence.get("routes", []))
    action_blob = " ".join(item.lower() for item in evidence.get("actions", []))
    url_blob = " ".join(item.lower() for item in urls)

    providers: list[str] = []
    provider_hits: list[str] = []
    for provider, hints in AI_PROVIDER_HINTS.items():
        if any(hint in dep_blob or hint in url_blob for hint in hints):
            providers.append(provider)
            provider_hits.extend(hints)

    active_types: list[str] = []
    for ai_type, hints in AI_TYPE_HINTS.items():
        if any(
            blob_contains_hint(ui_blob, hint)
            or blob_contains_hint(screen_blob, hint)
            or blob_contains_hint(route_blob, hint)
            or blob_contains_hint(action_blob, hint)
            or blob_contains_hint(dep_blob, hint)
            or blob_contains_hint(url_blob, hint)
            for hint in hints
        ):
            active_types.append(ai_type)

    active = bool(providers or active_types)
    review_profile = analyze_ai_preview_review_profile(evidence, permissions, dependencies)
    data_categories = {
        category
        for category, triggered in (
            ("text_prompts", "ai_chat" in active_types or "third_party_inference" in active_types),
            ("messages", "ai_chat" in active_types),
            ("images", "image_generation" in active_types),
            ("face_data", review_profile.get("face_data_likely")),
        )
        if triggered
    }
    return {
        "active": active,
        "user_reachable": active,
        "disclosure_required": active,
        "types": sorted(set(active_types)),
        "providers": sorted(set(providers)),
        "network_hosts": extract_url_hosts(urls),
        "data_categories": sorted(data_categories),
        "review_profile": review_profile,
        "evidence": {
            "dependency_hits": sorted(set(provider_hits)),
            "screens": [item for item in evidence.get("screens", []) if "ai" in item.lower() or "assistant" in item.lower() or "chat" in item.lower()][:6],
            "actions": [item for item in evidence.get("actions", []) if any(token in item.lower() for token in ("prompt", "assistant", "generate", "chat", "completion"))][:6],
            "ui_strings": [item for item in evidence.get("ui_strings", []) if any(token in item.lower() for token in ("ai", "assistant", "chat", "prompt", "generate image"))][:6],
            "urls": urls[:6],
        },
    }


def active_capability_names(capability_candidates: dict[str, dict[str, object]]) -> set[str]:
    return {
        name
        for name, payload in capability_candidates.items()
        if float(payload.get("score", 0.0)) >= 1.0
    }


def analyze_access_signals(
    file_cache: dict[str, str],
    capability_candidates: dict[str, dict[str, object]],
    dependencies: list[str],
    urls: list[str],
) -> dict[str, object]:
    identity_hits = _collect_pattern_hits(file_cache, ACCESS_IDENTITY_INPUT_PATTERNS)
    password_hits = _collect_pattern_hits(file_cache, ACCESS_PASSWORD_INPUT_PATTERNS)
    auth_action_hits = _collect_pattern_hits(file_cache, ACCESS_AUTH_ACTION_PATTERNS)
    external_auth_hits = _collect_pattern_hits(file_cache, ACCESS_EXTERNAL_AUTH_TEXT_PATTERNS)
    auth_endpoint_hits = _collect_pattern_hits(file_cache, ACCESS_AUTH_ENDPOINT_PATTERNS)
    local_session_hits = _collect_pattern_hits(file_cache, ACCESS_LOCAL_SESSION_PATTERNS)

    dep_values = [item.lower() for item in dependencies]
    dependency_auth_hits = match_patterns(dep_values, ACCESS_EXTERNAL_AUTH_DEPENDENCY_PATTERNS)
    if dependency_auth_hits:
        external_auth_hits = list(dict.fromkeys(external_auth_hits + [f"dependency: {item}" for item in dependency_auth_hits]))

    url_auth_hits = [
        url
        for url in urls
        if any(pattern.search(url.lower()) for _, pattern in ACCESS_AUTH_ENDPOINT_PATTERNS)
    ][:6]
    if url_auth_hits:
        auth_endpoint_hits = list(dict.fromkeys(auth_endpoint_hits + [f"url: {item}" for item in url_auth_hits]))

    has_identity_input = bool(identity_hits)
    has_password_input = bool(password_hits)
    has_auth_action = bool(auth_action_hits)
    has_external_auth = bool(external_auth_hits)
    has_auth_endpoint = bool(auth_endpoint_hits)
    has_credential_inputs = has_password_input and has_identity_input

    credential_account = bool(
        has_external_auth
        or (has_credential_inputs and (has_auth_action or has_auth_endpoint))
    )

    active_capabilities = active_capability_names(capability_candidates)
    community_features = bool(active_capabilities & {"feed", "post_creation", "messaging"})
    local_session = not credential_account and bool(local_session_hits)

    if credential_account:
        mode = "credential_account"
    elif local_session:
        mode = "local_session"
    elif community_features:
        mode = "community_only"
    else:
        mode = "neutral"

    return {
        "mode": mode,
        "credential_account": credential_account,
        "local_session": local_session,
        "community_features": community_features,
        "external_auth": has_external_auth,
        "credential_inputs": has_credential_inputs,
        "evidence": {
            "identity_inputs": identity_hits,
            "password_inputs": password_hits,
            "auth_actions": auth_action_hits,
            "external_auth": external_auth_hits,
            "auth_endpoints": auth_endpoint_hits,
            "local_session_markers": local_session_hits,
        },
    }


def access_signals_mode(access_signals: dict[str, object] | None) -> str:
    if not isinstance(access_signals, dict):
        return "neutral"
    mode = str(access_signals.get("mode", "")).strip().lower()
    if mode in {"credential_account", "local_session", "community_only", "neutral"}:
        return mode
    if access_signals.get("credential_account"):
        return "credential_account"
    if access_signals.get("local_session"):
        return "local_session"
    if access_signals.get("community_features"):
        return "community_only"
    return "neutral"


def inspect_access_mode(inspect_payload: dict[str, object]) -> str:
    return access_signals_mode(inspect_payload.get("access_signals"))


def inspect_has_credential_account(inspect_payload: dict[str, object]) -> bool:
    return inspect_access_mode(inspect_payload) == "credential_account"


def inspect_has_local_session(inspect_payload: dict[str, object]) -> bool:
    return inspect_access_mode(inspect_payload) == "local_session"


def analyze_translation_signals(
    capability_candidates: dict[str, dict[str, object]],
    urls: list[str],
) -> dict[str, object]:
    active_capabilities = active_capability_names(capability_candidates)
    translation_types: list[str] = []
    if "translate_text" in active_capabilities:
        translation_types.append("text")
    if "translate_voice" in active_capabilities:
        translation_types.append("voice")
    active = bool(translation_types)

    evidence: dict[str, object] = {}
    if "translate_text" in capability_candidates:
        evidence["translate_text"] = capability_candidates["translate_text"].get("evidence", {})
    if "translate_voice" in capability_candidates:
        evidence["translate_voice"] = capability_candidates["translate_voice"].get("evidence", {})

    return {
        "active": active,
        "user_reachable": active,
        "disclosure_required": active,
        "types": translation_types,
        "network_hosts": extract_url_hosts(urls),
        "evidence": evidence,
    }


def analyze_privacy_signals(
    permissions: dict[str, str],
    dependencies: list[str],
    capability_candidates: dict[str, dict[str, object]],
    ai_signals: dict[str, object],
    urls: list[str],
) -> dict[str, object]:
    dep_blob = " ".join(item.lower() for item in dependencies)
    active_capabilities = active_capability_names(capability_candidates)
    return {
        "camera": "camera" in permissions,
        "microphone": "microphone" in permissions or "speech_recognition" in permissions,
        "photo_library": "photo_library" in permissions or "photo_library_add" in permissions,
        "photo_library_add": "photo_library_add" in permissions,
        "tracking": "tracking" in permissions,
        "location": "location_when_in_use" in permissions or "location_always" in permissions,
        "analytics": any(hint in dep_blob for hint in ANALYTICS_HINTS),
        "payments": "recharge" in active_capabilities,
        # Settings/profile shells do not imply public posting or moderation obligations.
        "user_content": bool({"feed", "post_creation", "messaging"} & active_capabilities),
        "community_ugc": bool({"feed", "post_creation"} & active_capabilities),
        "network_hosts": extract_url_hosts(urls),
        "ai_features": bool(ai_signals.get("disclosure_required", ai_signals.get("active"))),
    }


def build_inspect_result(
    *,
    source_stack: str,
    app_root: Path,
    app_name: str,
    app_slug: str,
    permissions: dict[str, str],
    dependencies: list[str],
    evidence: dict[str, list[str]],
    brand_colors: list[dict[str, str]],
    urls: list[str],
    iap_codes: list[str],
) -> dict[str, object]:
    support_contact = support_email_facts(app_root)
    capability_candidates = infer_capability_candidates(evidence, dependencies)
    ai_signals = analyze_ai_signals(evidence, dependencies, urls, permissions)
    translation_signals = analyze_translation_signals(capability_candidates, urls)
    privacy_signals = analyze_privacy_signals(permissions, dependencies, capability_candidates, ai_signals, urls)
    return {
        "source_stack": source_stack,
        "app_name": app_name,
        "app_slug": app_slug,
        **support_contact,
        "permissions": permissions,
        "dependencies": sorted(set(dependencies)),
        "network_destinations": extract_url_hosts(urls),
        "iap_codes": sorted(set(iap_codes)),
        "iap_shop_code_display": format_iap_shop_code_display(iap_codes),
        "evidence": {
            "screens": sorted(set(evidence.get("screens", []))),
            "routes": sorted(set(evidence.get("routes", []))),
            "entities": sorted(set(evidence.get("entities", []))),
            "actions": sorted(set(evidence.get("actions", []))),
            "ui_strings": sorted(set(evidence.get("ui_strings", []))),
        },
        "capability_candidates": capability_candidates,
        "privacy_signals": privacy_signals,
        "legal_signals": inspect_legal_signals(app_root, IGNORED_DIR_NAMES | {"applisting", "tests", "test", "node_modules"}),
        "ai_signals": ai_signals,
        "translation_signals": translation_signals,
        "brand_colors": brand_colors,
        "logo_candidates": find_logo_candidates(app_root, app_slug),
        "existing_app_listing": check_existing_listing(app_root),
        "project_profile": build_project_profile(
            app_root,
            evidence,
            permissions,
            extract_url_hosts(urls),
        ),
    }
