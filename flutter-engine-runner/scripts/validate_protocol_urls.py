#!/usr/bin/env python3
"""Validate concrete protocol URLs and bundled, in-app protocol pages.

The public Intro material keeps the concrete HTTP URLs for later replacement,
but the running Flutter app must load the three generated HTML pages from its
own asset bundle.  This check therefore rejects network WebView loads and
requires a local ``assets/legal`` copy for every policy page.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

PAGES = ("PrivacyPolicy.html", "Terms&Conditions.html", "Support.html")
PLACEHOLDER = "【项目名称】"
WEBVIEW_MARKERS = ("WebView", "webview_flutter", "flutter_inappwebview", "InAppWebView")
# A WebView import alone is not enough: each policy button must pass its
# concrete URL directly into the in-app loading call.  Keep these markers
# intentionally small so equivalent Flutter WebView implementations remain
# valid while a URL registry with no load call is rejected.
LOCAL_LOAD_PATTERNS = (
    re.compile(r"loadFlutterAsset\s*\("),
    re.compile(r"loadFile\s*\("),
    re.compile(r"loadHtmlString\s*\("),
    re.compile(r"openProtocolAsset\s*\("),
)
NETWORK_LOAD_PATTERNS = (
    re.compile(r"loadRequest\s*\("),
    re.compile(r"loadUrl\s*\("),
)
# These names describe an intermediate protocol chooser/index.  A single
# reusable WebView page is allowed; an explicit picker/list route is not.
INTERMEDIATE_PROTOCOL_MARKERS = (
    "protocol_index",
    "protocol_list",
    "document_selector",
    "showProtocolPicker",
    "policyChooser",
    "protocolIndex",
    "protocolList",
    "documentSelector",
)


def validate(root: Path, project_name: str) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"{root}: project root does not exist"]
    if not project_name or project_name == PLACEHOLDER:
        findings.append("project name must be the user-provided concrete name, not a placeholder")
        return findings
    pubspec = root / "pubspec.yaml"
    lib = root / "lib"
    if not pubspec.is_file():
        findings.append("pubspec.yaml is required")
    if not lib.is_dir():
        findings.append("lib/ is required")
    site = root / "AppListing/site"
    for page in PAGES:
        if not (site / page).is_file():
            findings.append(f"missing protocol page: {page}")
    legal_assets = root / "assets/legal"
    for page in PAGES:
        asset = legal_assets / page
        if not asset.is_file() or asset.is_symlink():
            findings.append(f"missing bundled local HTML asset: assets/legal/{page}")
    pubspec_text = pubspec.read_text(encoding="utf-8", errors="replace") if pubspec.is_file() else ""
    if "assets/legal/" not in pubspec_text:
        findings.append("pubspec.yaml must register the bundled assets/legal/ directory")
    text_files = []
    for path in [pubspec, *lib.rglob("*.dart"), *lib.rglob("*.yaml"), *lib.rglob("*.yml")]:
        if path.is_file():
            try:
                text_files.append((path, path.read_text(encoding="utf-8", errors="replace")))
            except OSError as error:
                findings.append(f"{path}: cannot read: {error}")
    combined = "\n".join(text for _, text in text_files)
    intro_candidates = [
        root / "AppListing/Intro.md",
        root / "AppListing/intro.md",
    ]
    intro = next((path for path in intro_candidates if path.is_file()), None)
    intro_text = intro.read_text(encoding="utf-8", errors="replace") if intro else ""
    if intro is None:
        findings.append("AppListing/Intro.md (or intro.md) is required for the searchable concrete URL record")
    if PLACEHOLDER in intro_text:
        findings.append("placeholder protocol URL remains; replace 【项目名称】 with the concrete project name")
    expected = [f"http://{project_name}/{page}" for page in PAGES]
    for url in expected:
        if url not in intro_text:
            findings.append(f"missing concrete protocol URL in AppListing Intro: {url}")
    # Settings must expose exactly the three policy destinations. A source
    # registry may use a single list/map, but no extra policy URL is allowed.
    settings_files = [path for path, _ in text_files if path.name.lower() in {"settings.dart", "settings_page.dart", "settings_view.dart"}]
    settings_text = "\n".join(text for path, text in text_files if path in settings_files)
    if settings_files:
        if not all(f"assets/legal/{page}" in settings_text for page in PAGES):
            findings.append("Settings must expose exactly the three bundled local policy assets")
    runtime_policy_refs = []
    for path, text in text_files:
        if "PrivacyPolicy.html" in text or "Terms&Conditions.html" in text or "Support.html" in text:
            runtime_policy_refs.append(path)
    if any(
        path.suffix == ".html"
        and path.parent != site
        and not (root / "assets/legal").resolve() in path.resolve().parents
        for path in runtime_policy_refs
    ):
        findings.append("policy HTML must be bundled only under assets/legal or AppListing/site")
    wrong_hosts = []
    for token in ("http://", "https://"):
        for fragment in intro_text.split(token)[1:]:
            host = fragment.split("/", 1)[0]
            if any(fragment.startswith(page) for page in PAGES):
                continue
            if any(page in fragment[:160] for page in PAGES) and host != project_name:
                wrong_hosts.append(host)
    if wrong_hosts:
        findings.append(f"protocol URL uses a different project name/host: {sorted(set(wrong_hosts))}")
    if not any(marker in combined for marker in WEBVIEW_MARKERS):
        findings.append("in-app WebView integration is required even when the URL may be unreachable")
    if any(pattern.search(combined) for pattern in NETWORK_LOAD_PATTERNS):
        findings.append("protocol pages must not use a network WebView load; load the bundled local HTML assets")
    if not any(pattern.search(combined) for pattern in LOCAL_LOAD_PATTERNS):
        findings.append(
            "protocol buttons must directly load a local HTML asset in the in-app WebView "
            "(for example loadFlutterAsset('assets/legal/PrivacyPolicy.html')); "
            "a URL registry/import alone is insufficient"
        )
    intermediate = [marker for marker in INTERMEDIATE_PROTOCOL_MARKERS if marker in combined]
    if intermediate:
        findings.append(
            "protocol links must not pass through an intermediate protocol "
            f"index/list/selector: {', '.join(intermediate)}"
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--project-name", required=True)
    args = parser.parse_args()
    findings = validate(args.project_root.resolve(), args.project_name)
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print(f"PASS: concrete protocol URLs for {args.project_name!r} are registered and routed through an in-app WebView.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
