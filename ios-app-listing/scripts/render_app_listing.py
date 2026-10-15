#!/usr/bin/env python3
"""Render AppListing site pages with layout variants and brand-derived themes."""

from __future__ import annotations

import argparse
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "site-render"
MANIFEST_PATH = ASSET_ROOT / "templates-manifest.json"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def choose_template_id(manifest: dict, seed: str | None) -> str:
    templates = manifest["templates"]
    rng = random.Random(seed) if seed is not None else random.Random()
    weighted_ids: list[str] = []
    for item in templates:
        weighted_ids.extend([item["template_id"]] * int(item.get("weight", 1)))
    return rng.choice(weighted_ids)


def template_spec(manifest: dict, template_id: str) -> dict:
    for item in manifest["templates"]:
        if item["template_id"] == template_id:
            return item
    available = ", ".join(sorted(item["template_id"] for item in manifest.get("templates", [])))
    raise KeyError(f"Unknown template_id '{template_id}'. Available: {available}")


def normalize_hex(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.startswith("#"):
        hex_value = raw[1:]
    else:
        hex_value = raw
    if len(hex_value) == 3 and all(ch in "0123456789abcdefABCDEF" for ch in hex_value):
        return "#" + "".join(ch * 2 for ch in hex_value).upper()
    if len(hex_value) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in hex_value):
        return "#" + hex_value.upper()
    return None


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    normalized = normalize_hex(value)
    if normalized is None:
        raise ValueError(f"Invalid hex color: {value}")
    return tuple(int(normalized[index : index + 2], 16) for index in (1, 3, 5))


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02X}{green:02X}{blue:02X}"


def clamp_channel(value: float) -> int:
    return max(0, min(255, round(value)))


def mix(color_a: str, color_b: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    red_a, green_a, blue_a = hex_to_rgb(color_a)
    red_b, green_b, blue_b = hex_to_rgb(color_b)
    return rgb_to_hex(
        clamp_channel(red_a + (red_b - red_a) * ratio),
        clamp_channel(green_a + (green_b - green_a) * ratio),
        clamp_channel(blue_a + (blue_b - blue_a) * ratio),
    )


def lighten(color: str, ratio: float) -> str:
    return mix(color, "#FFFFFF", ratio)


def darken(color: str, ratio: float) -> str:
    return mix(color, "#000000", ratio)


def rgba(color: str, alpha: float) -> str:
    red, green, blue = hex_to_rgb(color)
    return f"rgba({red}, {green}, {blue}, {max(0.0, min(1.0, alpha)):.3f})"


def luminance(color: str) -> float:
    def channel(value: int) -> float:
        normalized = value / 255.0
        if normalized <= 0.03928:
            return normalized / 12.92
        return ((normalized + 0.055) / 1.055) ** 2.4

    red, green, blue = hex_to_rgb(color)
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast_ratio(color_a: str, color_b: str) -> float:
    luminance_a = luminance(color_a)
    luminance_b = luminance(color_b)
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_text(color: str) -> str:
    return "#150D20" if luminance(color) > 0.48 else "#FBF7FF"


def ensure_contrast(color: str, background: str, minimum_ratio: float) -> str:
    if contrast_ratio(color, background) >= minimum_ratio:
        return color

    target = contrast_text(background)
    best = target
    for step in range(1, 13):
        candidate = mix(color, target, step / 12.0)
        if contrast_ratio(candidate, background) >= minimum_ratio:
            return candidate
        best = candidate
    return best


def brand_color_map(payload: dict) -> dict[str, str]:
    colors: dict[str, str] = {}
    for item in payload.get("brand_colors", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip().lower()
        hex_value = normalize_hex(str(item.get("hex", "")).strip())
        if not name or hex_value is None:
            continue
        colors.setdefault(name, hex_value)
    return colors


def pick_brand_color(
    colors: dict[str, str],
    exact_names: tuple[str, ...],
    partial_names: tuple[str, ...],
    fallback: str,
) -> str:
    for name in exact_names:
        if name in colors:
            return colors[name]
    for key, value in colors.items():
        if any(token in key for token in partial_names):
            return value
    return fallback


def brand_color_priority(name: str, value: str) -> float:
    lowered = name.lower()
    red, green, blue = hex_to_rgb(value)
    spread = max(red, green, blue) - min(red, green, blue)
    score = float(spread)
    if any(token in lowered for token in ("primary", "accent", "brand", "highlight")):
        score += 180.0
    if any(token in lowered for token in ("secondary", "border", "divider", "stroke")):
        score += 120.0
    if any(token in lowered for token in ("text", "label", "font")):
        score -= 240.0
    if any(token in lowered for token in ("background", "surface", "card")):
        score -= 180.0
    if any(token in lowered for token in ("grey", "gray", "neutral")):
        score -= 110.0
    tone = luminance(value)
    if tone > 0.90:
        score -= 120.0
    elif tone < 0.08:
        score -= 80.0
    else:
        score += 18.0
    return score


def pick_brand_fallback_color(
    colors: dict[str, str],
    *,
    exclude_values: set[str] | None = None,
    fallback: str,
) -> str:
    exclude_values = exclude_values or set()
    ranked = sorted(
        (
            (brand_color_priority(name, value), name, value)
            for name, value in colors.items()
            if value not in exclude_values
        ),
        reverse=True,
    )
    for _, _, value in ranked:
        return value
    return fallback


def build_page_background(shell: str, base: str, primary: str, secondary: str, accent: str) -> str:
    if shell == "split":
        return (
            f"radial-gradient(circle at 12% 12%, {rgba(primary, 0.30)}, transparent 28%), "
            f"radial-gradient(circle at 84% 18%, {rgba(accent, 0.22)}, transparent 24%), "
            f"linear-gradient(155deg, {darken(base, 0.24)} 0%, {base} 48%, {mix(base, secondary, 0.46)} 100%)"
        )
    if shell == "sidebar":
        return (
            f"radial-gradient(circle at 88% 12%, {rgba(accent, 0.18)}, transparent 23%), "
            f"linear-gradient(130deg, {darken(base, 0.28)} 0%, {mix(base, primary, 0.18)} 34%, {mix(base, secondary, 0.42)} 100%)"
        )
    if shell == "billboard":
        return (
            f"radial-gradient(circle at 16% 12%, {rgba(primary, 0.26)}, transparent 24%), "
            f"radial-gradient(circle at 82% 22%, {rgba(secondary, 0.24)}, transparent 25%), "
            f"linear-gradient(160deg, {darken(base, 0.20)} 0%, {mix(base, accent, 0.18)} 48%, {mix(base, secondary, 0.48)} 100%)"
        )
    if shell == "editorial":
        return (
            f"radial-gradient(circle at 18% 14%, {rgba(accent, 0.18)}, transparent 22%), "
            f"radial-gradient(circle at 82% 12%, {rgba(primary, 0.22)}, transparent 24%), "
            f"linear-gradient(180deg, {darken(base, 0.30)} 0%, {base} 38%, {mix(base, secondary, 0.40)} 100%)"
        )
    return (
        f"radial-gradient(circle at 14% 14%, {rgba(primary, 0.28)}, transparent 27%), "
        f"radial-gradient(circle at 84% 12%, {rgba(accent, 0.24)}, transparent 25%), "
        f"linear-gradient(150deg, {darken(base, 0.24)} 0%, {base} 46%, {mix(base, secondary, 0.44)} 100%)"
    )


DEFAULT_VISUAL_STYLE = "vibrant-canvas"
PLAIN_VISUAL_STYLES = {
    "document-plain",
    "halo-outline",
    "editorial-paper",
    "product-sheet",
    "ledger-minimal",
}
VISUAL_STYLE_FONTS = {
    DEFAULT_VISUAL_STYLE: {
        "font-body": '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif',
        "font-heading": '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif',
        "font-ui": '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif',
    },
    "document-plain": {
        "font-body": '"Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif',
        "font-heading": '"Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif',
        "font-ui": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
    },
    "halo-outline": {
        "font-body": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
        "font-heading": '"Avenir Next Condensed", "Franklin Gothic Medium", "Arial Narrow", sans-serif',
        "font-ui": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
    },
    "editorial-paper": {
        "font-body": '"Charter", "Iowan Old Style", Georgia, serif',
        "font-heading": '"Charter", "Iowan Old Style", Georgia, serif',
        "font-ui": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
    },
    "product-sheet": {
        "font-body": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
        "font-heading": '"SF Pro Display", "Avenir Next", "Helvetica Neue", Arial, sans-serif',
        "font-ui": '"SF Pro Text", "Avenir Next", "Helvetica Neue", Arial, sans-serif',
    },
    "ledger-minimal": {
        "font-body": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
        "font-heading": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
        "font-ui": 'ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace',
    },
}


def visual_style(spec: dict) -> str:
    return str(spec.get("visual_style", DEFAULT_VISUAL_STYLE)).strip().lower() or DEFAULT_VISUAL_STYLE


def derive_theme_tokens(payload: dict, spec: dict) -> dict[str, str]:
    colors = brand_color_map(payload)
    primary = pick_brand_color(colors, ("primary",), ("primary",), "")
    if not primary:
        primary = pick_brand_fallback_color(colors, fallback="#6E4BFF")
    secondary = pick_brand_color(colors, ("secondary",), ("secondary", "primarydark"), "")
    if not secondary:
        secondary = pick_brand_fallback_color(colors, exclude_values={primary}, fallback=darken(primary, 0.18))
    accent = pick_brand_color(colors, ("accent",), ("accent", "primarylight", "secondarylight"), "")
    if not accent:
        accent = pick_brand_fallback_color(colors, exclude_values={primary, secondary}, fallback=lighten(secondary, 0.18))
    background_seed = pick_brand_color(
        colors,
        ("background",),
        ("background", "backgrounddark", "surface", "cardbackground"),
        darken(primary, 0.42),
    )
    surface_seed = pick_brand_color(
        colors,
        ("cardbackground", "surface", "backgroundlight"),
        ("cardbackground", "surface", "backgroundlight", "surfacelight"),
        lighten(primary, 0.92),
    )
    text_seed = pick_brand_color(
        colors,
        ("textprimary", "textblack"),
        ("textprimary", "textblack", "textsecondary"),
        "#1E1630",
    )

    background_anchor = background_seed if luminance(background_seed) < 0.40 else darken(background_seed, 0.44)
    surface = surface_seed if luminance(surface_seed) > 0.80 else lighten(surface_seed, 0.78)
    surface_alt = lighten(mix(surface, accent, 0.04), 0.03)
    panel = lighten(mix(surface, accent, 0.03), 0.01)
    text_main = text_seed if luminance(text_seed) < 0.45 else "#1E1630"
    text_soft = mix(text_main, surface, 0.46)
    heading = darken(text_main, 0.08)
    style = visual_style(spec)
    fonts = VISUAL_STYLE_FONTS.get(style, VISUAL_STYLE_FONTS[DEFAULT_VISUAL_STYLE])

    if style in PLAIN_VISUAL_STYLES:
        card_shadow = rgba(darken(text_main, 0.54), 0.06)
        nav_idle_bg = "#FFFFFF"
        nav_idle_text = ensure_contrast(darken(primary, 0.16), "#FFFFFF", 5.0)
        page_bg = "#FFFFFF"
        hero_surface = "#FFFFFF"
        hero_overlay = "none"
        highlight = lighten(primary, 0.92)
        active_bg = lighten(primary, 0.92)
        canvas_panel_bg = "#FFFFFF"
        canvas_line = rgba(text_main, 0.12)
        canvas_shadow = rgba(darken(text_main, 0.56), 0.04)
        canvas_text_soft = ensure_contrast(mix(text_main, "#FFFFFF", 0.42), "#FFFFFF", 4.5)
        canvas_heading = ensure_contrast(heading, "#FFFFFF", 7.0)
        canvas_blur = "0px"
        line = rgba(text_main, 0.10)
        line_strong = rgba(text_main, 0.18)
        shell_stroke = rgba(text_main, 0.12)
        shell_glow = rgba(primary, 0.08)
        wash = rgba(primary, 0.06)
        nav_active_text = ensure_contrast(primary, "#FFFFFF", 4.5)
    else:
        card_shadow = rgba(darken(primary, 0.36), 0.18)
        nav_idle_bg = rgba(lighten(surface, 0.01), 0.92)
        nav_idle_text = darken(primary, 0.16)
        page_bg = build_page_background(str(spec["shell"]), background_anchor, primary, secondary, accent)
        hero_surface = f"linear-gradient(155deg, {rgba(surface, 0.97)} 0%, {rgba(panel, 0.99)} 100%)"
        hero_overlay = f"linear-gradient(135deg, {rgba(primary, 0.16)}, {rgba(accent, 0.18)})"
        highlight = f"linear-gradient(135deg, {mix(primary, surface, 0.24)}, {mix(accent, surface, 0.14)})"
        active_bg = f"linear-gradient(135deg, {primary}, {accent})"
        canvas_panel_bg = f"linear-gradient(160deg, {rgba(surface, 0.96)} 0%, {rgba(surface_alt, 0.93)} 100%)"
        canvas_line = rgba(surface, 0.68)
        canvas_shadow = rgba(darken(primary, 0.48), 0.22)
        canvas_text_soft = ensure_contrast(mix(text_main, surface, 0.32), surface, 4.5)
        canvas_heading = ensure_contrast(heading, surface, 7.0)
        canvas_blur = "14px"
        if str(spec["shell"]) == "billboard":
            canvas_blur = "6px"
        line = rgba(primary, 0.14)
        line_strong = rgba(primary, 0.26)
        shell_stroke = rgba(surface, 0.18)
        shell_glow = rgba(accent, 0.22)
        wash = rgba(primary, 0.08)
        nav_active_text = contrast_text(primary)

    tokens = {
        "theme_color": primary,
        "page-bg": page_bg,
        "surface": surface,
        "surface-alt": surface_alt,
        "panel": panel,
        "text-main": text_main,
        "text-soft": text_soft,
        "heading": heading,
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "line": line,
        "line-strong": line_strong,
        "shadow": card_shadow,
        "hero-surface": hero_surface,
        "hero-overlay": hero_overlay,
        "highlight": highlight,
        "nav-idle-bg": nav_idle_bg,
        "nav-idle-text": nav_idle_text,
        "nav-active-bg": active_bg,
        "nav-active-text": nav_active_text,
        "shell-stroke": shell_stroke,
        "shell-glow": shell_glow,
        "wash": wash,
        "canvas-panel-bg": canvas_panel_bg,
        "canvas-line": canvas_line,
        "canvas-shadow": canvas_shadow,
        "canvas-text-soft": canvas_text_soft,
        "canvas-heading": canvas_heading,
        "canvas-blur": canvas_blur,
    }
    tokens.update(fonts)
    return tokens


def css_variables(theme: dict[str, str]) -> str:
    lines = [f"  --{key}: {value};" for key, value in theme.items() if key != "theme_color"]
    return ":root {\n" + "\n".join(lines) + "\n}"


COMMON_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html {
  scroll-behavior: smooth;
}
body {
  position: relative;
  font-family: var(--font-body);
  line-height: 1.68;
  color: var(--text-main);
  background: var(--page-bg);
  padding: calc(16px + env(safe-area-inset-top, 0px)) calc(16px + env(safe-area-inset-right, 0px)) calc(16px + env(safe-area-inset-bottom, 0px)) calc(16px + env(safe-area-inset-left, 0px));
}
a { color: inherit; }
.skip-link {
  position: absolute;
  left: 12px;
  top: -48px;
  z-index: 20;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--nav-active-bg);
  color: var(--nav-active-text);
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 800;
  text-decoration: none;
  box-shadow: 0 10px 22px var(--shadow);
  transition: top 140ms ease;
}
.skip-link:focus {
  top: 12px;
}
.app-shell {
  max-width: 960px;
  margin: 0 auto;
  color: var(--text-main);
}
.page-root {
  display: block;
}
.surface-block {
  padding: 0;
}
.page-main {
  display: grid;
  gap: 18px;
}
.page-head {
  display: grid;
  gap: 14px;
}
.page-grid {
  display: grid;
  gap: 18px;
  align-items: start;
}
.main-column,
.page-side,
.section-stack,
.policy-sections,
.faq-stack {
  display: grid;
  gap: 16px;
}
.page-intro {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid var(--canvas-line);
  background: var(--canvas-panel-bg);
  box-shadow: 0 10px 24px var(--canvas-shadow);
  backdrop-filter: blur(var(--canvas-blur));
  -webkit-backdrop-filter: blur(var(--canvas-blur));
}
.page-topbar,
.topbar-nav-group,
.topbar-meta,
.brand-copy {
  display: grid;
  gap: 10px;
}
.page-topbar {
  padding: 14px 16px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: linear-gradient(180deg, var(--surface-alt) 0%, var(--surface) 100%);
  box-shadow: 0 12px 26px var(--shadow);
}
.page-topbar--brand-split,
.page-topbar--compact-row {
  grid-template-columns: minmax(0, 1fr) minmax(300px, 1.1fr);
  align-items: start;
}
.page-topbar--nav-band,
.page-topbar--editorial-bar,
.page-topbar--stacked-frame,
.page-topbar--policy-hero,
.page-topbar--document-ribbon,
.page-topbar--store-strip,
.page-topbar--quiet-legal {
  gap: 12px;
}
.page-topbar--nav-band {
  background: linear-gradient(145deg, var(--surface) 0%, var(--surface-alt) 100%);
}
.page-topbar--nav-band .page-nav {
  order: -1;
}
.page-topbar--compact-row {
  background: linear-gradient(135deg, var(--surface-alt) 0%, var(--panel) 100%);
}
.page-topbar--compact-row .topbar-meta {
  grid-column: 1 / -1;
}
.page-topbar--editorial-bar {
  border-left: 3px solid var(--primary);
}
.page-topbar--stacked-frame .page-nav {
  padding: 8px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.18);
}
.page-topbar--policy-hero {
  padding: 18px;
  border: 1px solid var(--line-strong);
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.22), transparent 32%),
    linear-gradient(150deg, var(--surface-alt) 0%, var(--surface) 54%, var(--panel) 100%);
}
.page-topbar--policy-hero .topbar-nav-group {
  gap: 12px;
}
.page-topbar--document-ribbon {
  border-top: 4px solid var(--primary);
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
}
.page-topbar--document-ribbon .topbar-meta {
  grid-template-columns: auto 1fr;
  align-items: center;
}
.page-topbar--store-strip {
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.95fr);
  align-items: start;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.26), transparent 30%),
    linear-gradient(145deg, var(--surface-alt) 0%, var(--panel) 55%, var(--surface) 100%);
}
.page-topbar--store-strip .topbar-nav-group {
  gap: 12px;
}
.page-topbar--quiet-legal {
  gap: 14px;
  border-color: var(--canvas-line);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, var(--surface) 100%);
  box-shadow: 0 8px 20px var(--shadow);
}
.page-topbar--quiet-legal .page-nav {
  border-top: 1px solid var(--line);
  padding-top: 10px;
}
.brand-lockup {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.brand-copy strong {
  color: var(--heading);
  font-family: var(--font-heading);
  font-size: 0.98rem;
  letter-spacing: -0.03em;
}
.brand-copy span,
.topbar-note {
  font-family: var(--font-body);
  color: var(--text-soft);
  font-size: 13px;
  line-height: 1.58;
}
.topbar-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--wash);
  border: 1px solid var(--line);
  color: var(--primary);
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.page-label {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--wash);
  color: var(--primary);
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.page-title {
  color: var(--canvas-heading);
  font-family: var(--font-heading);
  font-size: clamp(1.72rem, 4vw, 2.5rem);
  line-height: 1.12;
  letter-spacing: -0.04em;
}
.page-subtitle,
.page-last-updated {
  color: var(--canvas-text-soft);
  font-size: 0.96rem;
  line-height: 1.58;
  max-width: 60ch;
}
.content-section p,
.policy-section p,
.faq-item p,
.context-card p,
.policy-note p,
.contact-panel p,
.feature-card p,
.footer-note {
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.72;
}
.page-nav {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  font-family: var(--font-ui);
}
.page-link {
  text-decoration: none;
  text-align: center;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease, color 160ms ease;
}
.page-link:hover {
  transform: translateY(-1px);
}
.page-link.is-active {
  pointer-events: none;
}
.page-nav--pill .page-link,
.page-nav--tabs .page-link,
.page-nav--ghost .page-link,
.page-nav--rail .page-link,
.page-nav--marker .page-link {
  padding: 11px 12px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--nav-idle-bg);
  color: var(--nav-idle-text);
  font-size: 13px;
  font-weight: 700;
}
.page-nav--pill .page-link.is-active,
.page-nav--tabs .page-link.is-active,
.page-nav--ghost .page-link.is-active,
.page-nav--rail .page-link.is-active,
.page-nav--marker .page-link.is-active {
  background: var(--nav-active-bg);
  border-color: transparent;
  color: var(--nav-active-text);
}
.page-nav--minimal {
  grid-template-columns: repeat(4, minmax(0, max-content));
  justify-content: start;
  gap: 8px 16px;
}
.page-nav--minimal .page-link {
  padding: 8px 0;
  border: none;
  border-bottom: 1px solid transparent;
  border-radius: 0;
  background: transparent;
  color: var(--text-soft);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.page-nav--minimal .page-link.is-active {
  color: var(--heading);
  border-color: var(--primary);
}
.page-nav--underline {
  gap: 10px;
}
.page-nav--underline .page-link {
  padding: 10px 0;
  border: none;
  border-bottom: 2px solid var(--line);
  border-radius: 0;
  background: transparent;
  color: var(--text-soft);
  font-size: 13px;
  font-weight: 700;
}
.page-nav--underline .page-link.is-active {
  background: transparent;
  color: var(--heading);
  border-color: var(--primary);
}
.page-footer .page-nav--underline .page-link {
  color: var(--canvas-text-soft);
  border-color: var(--canvas-line);
}
.page-footer .page-nav--underline .page-link.is-active {
  color: var(--canvas-heading);
  border-color: var(--primary);
}
.page-nav--tabs .page-link {
  border-radius: 14px;
}
.page-nav--ghost .page-link {
  background: transparent;
}
.page-nav--rail {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.page-nav--rail .page-link {
  border-radius: 16px;
}
.page-nav--marker {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.page-nav--marker .page-link {
  position: relative;
  padding-left: 18px;
  text-align: left;
}
.page-nav--marker .page-link::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 10px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.42;
  transform: translateY(-50%);
}
.page-nav--marker .page-link.is-active::before {
  opacity: 1;
}
.content-section,
.policy-section,
.faq-item,
.feature-card,
.context-card,
.contact-panel,
.policy-note {
  position: relative;
  border-radius: 22px;
}
.content-section h2,
.policy-section h2,
.page-main h2,
.page-side h2 {
  color: var(--heading);
  font-family: var(--font-heading);
  font-size: clamp(1.2rem, 2.4vw, 1.7rem);
  line-height: 1.2;
  margin-bottom: 12px;
}
.content-section h3,
.policy-section h3,
.faq-item h3,
.feature-card h3,
.context-card h3,
.contact-panel h3 {
  color: var(--heading);
  font-family: var(--font-heading);
  font-size: 1rem;
  line-height: 1.35;
  margin-bottom: 8px;
}
.content-section p,
.policy-section p,
.faq-item p,
.feature-card p,
.context-card p,
.contact-panel p,
.policy-note p {
  margin: 0;
}
.content-section ul,
.policy-section ul,
.page-main ul {
  margin-left: 20px;
  display: grid;
  gap: 10px;
}
.content-section li,
.policy-section li,
.page-main li {
  font-size: 14px;
  line-height: 1.68;
}
.feature-collection {
  display: grid;
  gap: 14px;
}
.feature-card,
.faq-item,
.contact-panel,
.context-card,
.policy-note {
  background: var(--surface-alt);
  border: 1px solid var(--line);
  padding: 16px;
}
.context-card--outline {
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
}
.context-card--accent {
  background: linear-gradient(145deg, var(--surface-alt) 0%, var(--panel) 100%);
}
.outline-list {
  display: grid;
  gap: 8px;
}
.outline-link {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.52);
  color: var(--text-main);
  text-decoration: none;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.outline-link:hover {
  transform: translateY(-1px);
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.7);
}
.outline-link span {
  color: var(--primary);
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.outline-link strong {
  color: var(--heading);
  font-family: var(--font-heading);
  font-size: 13px;
  line-height: 1.45;
}
.badge-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.badge-list span {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--wash);
  color: var(--nav-idle-text);
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 700;
}
.feature-style--grid .feature-collection {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--split .feature-collection {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--split .feature-card:first-child {
  grid-column: 1 / -1;
  background: var(--highlight);
}
.feature-style--list .feature-collection {
  grid-template-columns: 1fr;
}
.feature-style--spotlight .feature-collection {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--spotlight .feature-card:first-child {
  background: var(--highlight);
  min-height: 220px;
}
.feature-style--mosaic .feature-collection {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--mosaic .feature-card:nth-child(1),
.feature-style--mosaic .feature-card:nth-child(4) {
  grid-column: span 2;
}
.feature-style--steps .feature-collection {
  counter-reset: feature-steps;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--steps .feature-card {
  counter-increment: feature-steps;
  padding-top: 48px;
}
.feature-style--steps .feature-card::before {
  content: counter(feature-steps, decimal-leading-zero);
  position: absolute;
  top: 14px;
  left: 16px;
  color: var(--primary);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.14em;
}
.feature-style--showcase .feature-collection {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.feature-style--showcase .feature-card:first-child {
  grid-column: 1 / -1;
  padding: 22px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.22), transparent 32%),
    linear-gradient(140deg, var(--highlight) 0%, var(--surface-alt) 100%);
  border-color: var(--line-strong);
  box-shadow: 0 14px 30px var(--shadow);
}
.section-style--cards .content-section,
.section-style--cards .policy-section,
.section-style--cards .faq-item {
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--line);
  box-shadow: 0 10px 22px var(--shadow);
  padding: 20px;
}
.section-style--bands .content-section,
.section-style--bands .policy-section,
.section-style--bands .faq-item {
  padding: 20px 22px;
  background: linear-gradient(145deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--line);
}
.section-style--bands .content-section:nth-child(even),
.section-style--bands .policy-section:nth-child(even),
.section-style--bands .faq-item:nth-child(even) {
  background: linear-gradient(145deg, var(--surface-alt) 0%, var(--surface) 100%);
}
.section-style--outline .content-section,
.section-style--outline .policy-section,
.section-style--outline .faq-item {
  padding: 18px 18px 18px 22px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 3px solid var(--primary);
}
.section-style--outline .content-section::before,
.section-style--outline .policy-section::before,
.section-style--outline .faq-item::before {
  content: "";
  position: absolute;
  top: 18px;
  left: -9px;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: var(--nav-active-bg);
  box-shadow: 0 0 0 6px var(--wash);
}
.section-style--columns .section-stack,
.section-style--columns .policy-sections,
.section-style--columns .faq-stack {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
.section-style--columns .content-section,
.section-style--columns .policy-section,
.section-style--columns .faq-item {
  background: var(--surface);
  border: 1px solid var(--line);
  padding: 20px;
  min-height: 100%;
}
.section-style--columns .content-section--wide,
.section-style--columns .policy-section--wide,
.section-style--columns .faq-item--wide {
  grid-column: 1 / -1;
}
.section-style--soft-panels .content-section,
.section-style--soft-panels .policy-section,
.section-style--soft-panels .faq-item {
  padding: 20px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.24), transparent 32%),
    linear-gradient(150deg, rgba(255, 255, 255, 0.92) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--line);
  box-shadow: 0 12px 24px var(--shadow);
}
.section-style--soft-panels .content-section::after,
.section-style--soft-panels .policy-section::after,
.section-style--soft-panels .faq-item::after {
  content: "";
  position: absolute;
  inset: 0;
  border-top: 3px solid var(--primary);
  border-radius: 22px;
  opacity: 0.28;
  pointer-events: none;
}
.section-style--paper .content-section,
.section-style--paper .policy-section,
.section-style--paper .faq-item {
  padding: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(255, 255, 255, 0.92) 100%),
    repeating-linear-gradient(180deg, rgba(0, 0, 0, 0.03) 0, rgba(0, 0, 0, 0.03) 1px, transparent 1px, transparent 28px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 10px 22px rgba(20, 13, 32, 0.10);
}
.section-style--paper .content-section h2,
.section-style--paper .policy-section h2,
.section-style--paper .faq-item h3 {
  letter-spacing: -0.02em;
}
.section-style--legal-grid .section-stack,
.section-style--legal-grid .policy-sections,
.section-style--legal-grid .faq-stack {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}
.section-style--legal-grid .content-section,
.section-style--legal-grid .policy-section,
.section-style--legal-grid .faq-item {
  padding: 18px 20px 18px 22px;
  background: linear-gradient(180deg, var(--surface) 0%, var(--surface-alt) 100%);
  border: 1px solid var(--line);
  border-top: 4px solid var(--primary);
  min-height: 100%;
}
.section-style--legal-grid .content-section--wide,
.section-style--legal-grid .policy-section--wide,
.section-style--legal-grid .faq-item--wide {
  grid-column: 1 / -1;
}
.contact-panel {
  display: grid;
  gap: 12px;
}
.contact-panel .email {
  color: var(--primary);
  font-family: var(--font-ui);
  font-weight: 800;
  text-decoration: none;
}
.contact-panel .email:hover {
  text-decoration: underline;
}
.page-footer {
  display: grid;
  gap: 12px;
  margin-top: 4px;
  padding: 16px 18px;
  border-radius: 22px;
  border: 1px solid var(--canvas-line);
  background: var(--canvas-panel-bg);
  box-shadow: 0 10px 24px var(--canvas-shadow);
  backdrop-filter: blur(var(--canvas-blur));
  -webkit-backdrop-filter: blur(var(--canvas-blur));
}
.page-footer--note-only {
  gap: 0;
}
.footer-note {
  color: var(--canvas-text-soft);
  font-size: 13px;
  line-height: 1.6;
}
.support-footer {
  display: grid;
  gap: 18px;
}
.layout-shell--stacked .surface-block {
  max-width: 820px;
  margin: 0 auto;
}
.layout-shell--split .page-grid {
  grid-template-columns: minmax(0, 1.55fr) minmax(220px, 0.8fr);
}
.layout-shell--sidebar .page-grid {
  grid-template-columns: minmax(240px, 280px) minmax(0, 1fr);
}
.layout-shell--sidebar .page-side {
  order: -1;
}
.layout-shell--billboard .page-intro {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}
.layout-shell--billboard .page-side {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.layout-shell--editorial .page-grid {
  grid-template-columns: minmax(0, 1.62fr) minmax(220px, 0.82fr);
}
.layout-shell--editorial .context-card--accent {
  border-left: 3px solid var(--primary);
}
@media (max-width: 980px) {
  body { padding: 12px; }
  .layout-shell--split .page-grid,
  .layout-shell--sidebar .page-grid,
  .layout-shell--editorial .page-grid {
    grid-template-columns: 1fr;
  }
  .page-topbar--brand-split,
  .page-topbar--compact-row,
  .page-topbar--store-strip {
    grid-template-columns: 1fr;
  }
  .layout-shell--sidebar .page-side {
    order: 0;
  }
  .page-side {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}
@media (max-width: 720px) {
  body { padding: 10px; }
  .surface-block {
    padding: 18px 14px 16px;
    border-radius: 18px;
  }
  .page-topbar {
    padding: 12px;
    border-radius: 18px;
  }
  .page-intro,
  .page-footer {
    padding: 14px;
    border-radius: 18px;
  }
  .page-title {
    font-size: clamp(1.45rem, 8vw, 1.98rem);
    line-height: 1.16;
  }
  .page-subtitle,
  .page-last-updated {
    font-size: 0.9rem;
  }
  .brand-copy strong {
    font-size: 0.94rem;
  }
  .page-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .page-nav--minimal {
    grid-template-columns: repeat(2, minmax(0, max-content));
  }
  .page-nav--rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .page-link {
    white-space: normal;
  }
  .page-nav--pill .page-link,
  .page-nav--tabs .page-link,
  .page-nav--ghost .page-link,
  .page-nav--rail .page-link,
  .page-nav--underline .page-link {
    padding: 10px 8px;
    font-size: 12px;
  }
  .content-section,
  .policy-section,
  .faq-item,
  .feature-card,
  .context-card,
  .contact-panel,
  .policy-note {
    border-radius: 18px;
  }
  .content-section p,
  .policy-section p,
  .faq-item p,
  .feature-card p,
  .context-card p,
  .contact-panel p,
  .policy-note p,
  .footer-note,
  .content-section li,
  .policy-section li,
  .page-main li {
    font-size: 13px;
    line-height: 1.62;
  }
  .feature-style--mosaic .feature-card:nth-child(1),
  .feature-style--mosaic .feature-card:nth-child(4) {
    grid-column: auto;
  }
  .section-style--outline .content-section,
  .section-style--outline .policy-section,
  .section-style--outline .faq-item {
    padding-left: 18px;
  }
}
"""


VISUAL_STYLE_CSS = {
    DEFAULT_VISUAL_STYLE: "",
    "document-plain": """
body {
  background: #FFFFFF;
  padding: 28px 20px 36px;
}
.app-shell {
  max-width: 860px;
}
.page-main,
.page-head {
  gap: 22px;
}
.page-topbar,
.page-intro,
.page-footer {
  padding: 0 0 14px;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.page-topbar {
  gap: 16px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.14);
}
.page-intro {
  gap: 10px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.10);
}
.page-footer {
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(17, 24, 39, 0.14);
}
.page-title {
  color: var(--heading);
  font-size: clamp(2.2rem, 4vw, 3.15rem);
  line-height: 1.02;
}
.page-subtitle,
.page-last-updated,
.topbar-note,
.footer-note {
  max-width: 72ch;
  color: var(--text-soft);
}
.page-label,
.topbar-kicker,
.badge-list span {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--primary);
}
.page-nav {
  gap: 10px 18px;
}
.page-nav--minimal {
  grid-template-columns: repeat(4, minmax(0, max-content));
  gap: 8px 18px;
}
.page-nav--minimal .page-link {
  padding: 3px 0;
  font-size: 11px;
  letter-spacing: 0.18em;
}
.content-section,
.policy-section,
.faq-item,
.feature-card,
.context-card,
.contact-panel,
.policy-note {
  padding: 18px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
.section-style--paper .content-section,
.section-style--paper .policy-section,
.section-style--paper .faq-item,
.section-style--paper .content-section--wide,
.section-style--paper .policy-section--wide,
.section-style--paper .faq-item--wide {
  padding: 18px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.12);
  background: transparent;
  box-shadow: none;
}
.content-section--wide:first-child,
.policy-sections .policy-section:first-child,
.faq-stack .faq-item:first-child,
.feature-collection .feature-card:first-child {
  border-top-width: 2px;
}
.outline-link {
  padding: 10px 0;
  border: none;
  border-bottom: 1px solid rgba(17, 24, 39, 0.10);
  border-radius: 0;
  background: transparent;
}
.outline-link:hover {
  background: transparent;
}
.context-card--outline,
.context-card--accent {
  background: transparent;
}
.feature-style--steps .feature-card {
  padding-top: 42px;
}
.feature-style--steps .feature-card::before {
  left: 0;
  top: 0;
}
@media (max-width: 720px) {
  body {
    padding: 20px 16px 28px;
  }
  .page-topbar,
  .page-intro,
  .page-footer,
  .content-section,
  .policy-section,
  .faq-item,
  .feature-card,
  .context-card,
  .contact-panel,
  .policy-note {
    border-radius: 0;
  }
}
""",
    "halo-outline": """
body {
  background: #FFFFFF;
  padding: 22px 18px 30px;
}
.app-shell {
  max-width: 1080px;
}
.page-main {
  gap: 20px;
}
.page-topbar,
.page-intro,
.page-footer {
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.page-topbar {
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: 28px;
}
.page-topbar::after {
  content: "";
  position: absolute;
  inset: 10px;
  border: 1px solid var(--line-strong);
  border-radius: 20px;
  pointer-events: none;
}
.page-topbar--policy-hero {
  background: transparent;
}
.page-intro {
  padding: 22px 24px;
  border: 1px solid var(--line);
  border-radius: 28px;
}
.page-title {
  font-size: clamp(2.4rem, 4.8vw, 3.45rem);
  line-height: 0.98;
}
.page-label,
.topbar-kicker {
  background: transparent;
}
.page-nav--marker .page-link {
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px 10px 20px;
}
.page-nav--marker .page-link.is-active {
  background: transparent;
  border-color: var(--primary);
  color: var(--primary);
}
.page-nav--marker .page-link::before {
  left: 12px;
  background: var(--primary);
}
.content-section,
.policy-section,
.faq-item,
.feature-card,
.context-card,
.contact-panel,
.policy-note {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: 26px;
  box-shadow: none;
}
.section-style--soft-panels .content-section,
.section-style--soft-panels .policy-section,
.section-style--soft-panels .faq-item {
  background: #FFFFFF;
  box-shadow: none;
}
.section-style--soft-panels .content-section::after,
.section-style--soft-panels .policy-section::after,
.section-style--soft-panels .faq-item::after {
  inset: 10px;
  border-top: 1px solid var(--line-strong);
  opacity: 1;
  border-radius: 16px;
}
.feature-style--showcase .feature-card:first-child {
  background: transparent;
  border: 1px solid var(--line-strong);
  box-shadow: none;
  min-height: 0;
}
.page-side {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
.page-footer {
  margin-top: 4px;
  padding: 14px 0 0;
  border: none;
}
@media (max-width: 720px) {
  .page-topbar,
  .page-intro,
  .content-section,
  .policy-section,
  .faq-item,
  .feature-card,
  .context-card,
  .contact-panel,
  .policy-note {
    border-radius: 20px;
  }
}
""",
    "editorial-paper": """
body {
  background: #FFFFFF;
  padding: 24px 20px 34px;
}
.app-shell {
  max-width: 1180px;
}
.page-main {
  gap: 18px;
}
.page-topbar,
.page-intro,
.page-footer {
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.page-topbar {
  padding: 0 0 14px;
  border: none;
  border-top: 3px double rgba(17, 24, 39, 0.42);
  border-bottom: 1px solid rgba(17, 24, 39, 0.16);
}
.page-topbar--document-ribbon {
  background: transparent;
}
.page-intro {
  padding: 12px 0 0 18px;
  border: none;
  border-left: 3px solid var(--primary);
}
.page-footer {
  padding: 18px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.16);
}
.page-title {
  font-size: clamp(2.25rem, 4.3vw, 3.25rem);
  max-width: 12ch;
}
.page-label,
.topbar-kicker,
.badge-list span {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--primary);
}
.page-nav--underline .page-link {
  padding: 8px 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-bottom-color: rgba(17, 24, 39, 0.16);
}
.content-section,
.policy-section,
.faq-item,
.feature-card {
  padding: 16px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.14);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
.section-style--legal-grid .content-section,
.section-style--legal-grid .policy-section,
.section-style--legal-grid .faq-item {
  min-height: 0;
  padding: 16px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.14);
  background: transparent;
}
.context-card,
.contact-panel,
.policy-note {
  background: transparent;
  border: 1px solid rgba(17, 24, 39, 0.14);
  border-radius: 0;
  box-shadow: none;
}
.context-card--accent {
  border-left: 3px solid var(--primary);
}
.outline-link {
  padding: 10px 0;
  border: none;
  border-bottom: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 0;
  background: transparent;
}
.outline-link:hover {
  background: transparent;
}
.feature-style--steps .feature-card {
  padding: 44px 0 0;
}
.feature-style--steps .feature-card::before {
  left: 0;
}
""",
    "product-sheet": """
body {
  background: #FFFFFF;
  padding: 20px 18px 30px;
}
.app-shell {
  max-width: 1080px;
}
.page-main {
  gap: 18px;
}
.page-topbar {
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: #FFFFFF;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}
.page-topbar--store-strip {
  background: #FFFFFF;
}
.page-intro {
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: #FFFFFF;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.05);
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.page-footer {
  padding: 12px 0 0;
  border: none;
  background: transparent;
  box-shadow: none;
}
.page-title {
  font-size: clamp(2.15rem, 4.1vw, 3.05rem);
}
.page-label,
.topbar-kicker {
  background: transparent;
}
.page-nav--tabs .page-link {
  background: transparent;
  border-color: rgba(15, 23, 42, 0.12);
  border-radius: 999px;
  font-weight: 800;
}
.page-nav--tabs .page-link.is-active {
  background: transparent;
  border-color: var(--primary);
  color: var(--primary);
}
.content-section,
.policy-section,
.faq-item,
.feature-card,
.context-card,
.contact-panel,
.policy-note {
  background: #FFFFFF;
  border: 1px solid rgba(15, 23, 42, 0.10);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}
.section-style--soft-panels .content-section,
.section-style--soft-panels .policy-section,
.section-style--soft-panels .faq-item {
  background: #FFFFFF;
  border-top: 3px solid var(--primary);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}
.section-style--soft-panels .content-section::after,
.section-style--soft-panels .policy-section::after,
.section-style--soft-panels .faq-item::after {
  content: none;
}
.feature-style--showcase .feature-card:first-child {
  background: #FFFFFF;
  border-top: 3px solid var(--primary);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.07);
  min-height: 0;
}
.outline-link {
  background: #FFFFFF;
  border-color: rgba(15, 23, 42, 0.10);
}
""",
    "ledger-minimal": """
body {
  background: #FFFFFF;
  padding: 22px 18px 30px;
}
.app-shell {
  max-width: 1100px;
}
.page-main {
  gap: 16px;
}
.page-topbar,
.page-intro {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
.page-topbar {
  border-radius: 14px;
}
.page-topbar--quiet-legal {
  background: transparent;
}
.page-intro {
  border-radius: 14px;
}
.page-footer {
  padding: 14px 0 0;
  border: none;
  border-top: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
.page-label,
.topbar-kicker,
.badge-list span {
  font-family: var(--font-ui);
  letter-spacing: 0.16em;
}
.page-nav--marker .page-link {
  padding: 10px 0 10px 18px;
  border: none;
  border-bottom: 1px solid var(--line);
  border-radius: 0;
  background: transparent;
}
.page-nav--marker .page-link.is-active {
  background: transparent;
  color: var(--heading);
  border-color: var(--primary);
}
.content-section,
.policy-section,
.faq-item,
.feature-card,
.context-card,
.contact-panel,
.policy-note {
  background: transparent;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 14px;
  box-shadow: none;
}
.section-style--paper .content-section,
.section-style--paper .policy-section,
.section-style--paper .faq-item {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: transparent;
  box-shadow: none;
}
.layout-shell--sidebar .page-grid {
  grid-template-columns: minmax(240px, 260px) minmax(0, 1fr);
}
.page-side {
  gap: 12px;
}
@media (max-width: 980px) {
  .layout-shell--sidebar .page-grid {
    grid-template-columns: 1fr;
  }
}
""",
}


def build_style(theme: dict[str, str], spec: dict) -> str:
    return css_variables(theme) + "\n" + COMMON_CSS + "\n" + VISUAL_STYLE_CSS.get(visual_style(spec), "")


def header_style(spec: dict) -> str:
    return str(spec.get("header_style", "brand-split")).strip().lower()


def shell_class_names(spec: dict, shell: str) -> str:
    return " ".join(
        [
            "app-shell",
            "layout-shell",
            f"layout-shell--{esc(shell)}",
            f"visual-style--{esc(visual_style(spec))}",
            "nav-style--none",
            f"section-style--{esc(spec['section_style'])}",
            f"feature-style--{esc(spec['feature_style'])}",
        ]
    )


HIDDEN_METADATA_PREFIXES = ("ugc:", "chat:", "category:", "iap code:", "iap codes:")
BLOCKED_VISIBLE_TITLES = {
    "what the site covers",
    "what the app supports",
    "category",
    "iap code",
    "iap codes",
}
HIDDEN_STANDALONE_VALUES = {
    "category",
    "social networking",
    "travel",
    "photo & video",
    "finance",
    "utilities",
    "社交 (social networking)",
    "旅游 (travel)",
    "摄影与录像 (photo & video)",
    "财务 (finance)",
    "工具 (utilities)",
    "iap code",
    "iap codes",
}
INLINE_METADATA_PATTERN = re.compile(r"\b(?:UGC|Chat|Category|IAP\s*Codes?)\s*:\s*[^\n\r]+", re.IGNORECASE)
IAP_CODE_TOKEN = r"[A-Za-z][A-Za-z_]*\d+(?:0[1-9]|1[0-2])"
IAP_CODE_DISPLAY_PATTERN = re.compile(
    rf"^(?:{IAP_CODE_TOKEN}(?:\s*-\s*{IAP_CODE_TOKEN})?)(?:\s*,\s*{IAP_CODE_TOKEN}(?:\s*-\s*{IAP_CODE_TOKEN})?)*$"
)


def is_hidden_visible_text(cleaned: str) -> bool:
    lowered = cleaned.casefold()
    if any(lowered.startswith(prefix) for prefix in HIDDEN_METADATA_PREFIXES):
        return True
    if lowered in HIDDEN_STANDALONE_VALUES:
        return True
    if IAP_CODE_DISPLAY_PATTERN.fullmatch(cleaned):
        return True
    return False


def sanitize_visible_text(text: object) -> str:
    lines = []
    for raw_line in str(text).splitlines():
        without_inline_metadata = INLINE_METADATA_PATTERN.sub("", raw_line)
        cleaned = " ".join(without_inline_metadata.split()).strip()
        if not cleaned:
            continue
        if is_hidden_visible_text(cleaned):
            continue
        lines.append(cleaned)
    if not lines:
        cleaned = " ".join(INLINE_METADATA_PATTERN.sub("", str(text)).split()).strip()
        if cleaned and not is_hidden_visible_text(cleaned):
            lines.append(cleaned)
    return " ".join(lines).strip()


def sanitize_visible_items(items: list[object]) -> list[str]:
    sanitized: list[str] = []
    for item in items:
        cleaned = sanitize_visible_text(item)
        if cleaned:
            sanitized.append(cleaned)
    return sanitized


def sanitize_visible_cards(cards: list[dict[str, object]]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    for card in cards:
        title = sanitize_visible_text(card.get("title", ""))
        body = sanitize_visible_text(card.get("body", ""))
        if not title or title.casefold() in BLOCKED_VISIBLE_TITLES or not body:
            continue
        sanitized.append({"title": title, "body": body})
    return sanitized


def render_brand_lockup(app_name: str, descriptor: str) -> str:
    return (
        '<div class="brand-lockup">'
        '<div class="brand-copy">'
        f"<strong>{esc(app_name)}</strong>"
        f"<span>{esc(descriptor)}</span>"
        "</div></div>"
    )


def render_context_cards(cards: list[dict[str, str]], *, extra_class: str = "") -> str:
    classes = "context-card"
    if extra_class:
        classes += f" {extra_class}"
    visible_cards = sanitize_visible_cards(cards)
    return "".join(
        f'<article class="{classes}"><h3>{esc(card["title"])}</h3><p>{esc(card["body"])}</p></article>'
        for card in visible_cards
    )


def render_highlight_cards(cards: list[dict[str, str]]) -> str:
    visible_cards = sanitize_visible_cards(cards)
    return "".join(
        f'<div class="hero-highlight"><h3>{esc(card["title"])}</h3><p>{esc(card["body"])}</p></div>'
        for card in visible_cards
    )


def render_feature_collection(items: list[dict[str, str]]) -> str:
    visible_items = sanitize_visible_cards(items)
    return '<div class="feature-collection">' + "".join(
        f'<article class="feature-card"><h3>{esc(item["title"])}</h3><p>{esc(item["body"])}</p></article>'
        for item in visible_items
    ) + "</div>"


def render_list(items: list[str]) -> str:
    visible_items = sanitize_visible_items(items)
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in visible_items) + "</ul>"


def render_faq_items(items: list[dict[str, str]]) -> str:
    visible_items = sanitize_visible_cards(items)
    return '<div class="faq-stack">' + "".join(
        f'<article class="faq-item"><h3>{esc(item["title"])}</h3><p>{esc(item["body"])}</p></article>'
        for item in visible_items
    ) + "</div>"


def render_badge_list(items: list[str]) -> str:
    visible_items = sanitize_visible_items(items)
    return '<div class="badge-list">' + "".join(f"<span>{esc(item)}</span>" for item in visible_items) + "</div>"


HEADING_NUMBER_PREFIX = re.compile(r"^\s*\d+[\.\)\-:\s]+")
SLUG_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")


def policy_anchor_id(page_kind: str, title: str, index: int) -> str:
    cleaned = HEADING_NUMBER_PREFIX.sub("", sanitize_visible_text(title)).strip().lower()
    slug = SLUG_TOKEN_PATTERN.sub("-", cleaned).strip("-")
    if not slug:
        slug = f"section-{index + 1}"
    return f"{page_kind}-{slug}"


def policy_outline_items(sections: list[dict[str, object]], page_kind: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index, section in enumerate(sections):
        title = sanitize_visible_text(section.get("title", ""))
        body = sanitize_visible_text(section.get("body", ""))
        if not title or title.casefold() in BLOCKED_VISIBLE_TITLES or not body:
            continue
        items.append(
            {
                "id": policy_anchor_id(page_kind, title, index),
                "title": HEADING_NUMBER_PREFIX.sub("", title).strip(),
                "label": f"Section {len(items) + 1}",
            }
        )
    return items


def render_policy_outline(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    return (
        '<section class="context-card context-card--outline"><h3>On This Page</h3><div class="outline-list">'
        + "".join(
            f'<a class="outline-link" href="#{esc(item["id"])}"><span>{esc(item["label"])}</span><strong>{esc(item["title"])}</strong></a>'
            for item in items
        )
        + "</div></section>"
    )


def render_policy_sections(
    sections: list[dict[str, object]],
    *,
    wide_first: bool = False,
    page_kind: str = "policy",
) -> str:
    rendered: list[str] = []
    for index, section in enumerate(sections):
        title = sanitize_visible_text(section["title"])
        body = sanitize_visible_text(section["body"])
        if not title or title.casefold() in BLOCKED_VISIBLE_TITLES or not body:
            continue
        classes = ["policy-section"]
        if wide_first and index == 0:
            classes.append("policy-section--wide")
        anchor_id = policy_anchor_id(page_kind, title, index)
        bullets = sanitize_visible_items(list(section.get("bullets", [])))
        block = [
            f'<article id="{esc(anchor_id)}" class="{" ".join(classes)}">',
            f'<h2><a href="#{esc(anchor_id)}">{esc(title)}</a></h2>',
            f"<p>{esc(body)}</p>",
        ]
        if bullets:
            block.append(render_list(bullets))
        block.append("</article>")
        rendered.append("".join(block))
    return '<div class="policy-sections">' + "".join(rendered) + "</div>"


def render_overview_sections(payload: dict, spec: dict) -> str:
    sections = [
        (
            "Our Purpose",
            f"<p>{esc(sanitize_visible_text(payload['purpose']))}</p>",
            "content-section content-section--wide",
        ),
        (
            sanitize_visible_text(payload.get("features_section_title", "Core Features")) or "Core Features",
            render_feature_collection(payload["feature_cards"]),
            "content-section content-section--wide",
        ),
        (
            sanitize_visible_text(payload.get("service_section_title", "Service Notes")) or "Service Notes",
            f"<p>{esc(sanitize_visible_text(payload['community_safety']))}</p>",
            "content-section",
        ),
    ]
    sections = [section for section in sections if section[0].casefold() not in BLOCKED_VISIBLE_TITLES]
    if spec["shell"] in {"billboard", "editorial"} and len(sections) > 2:
        sections[2] = (sections[2][0], sections[2][1], "content-section content-section--wide")
    blocks = [
        f'<section class="{classes}"><h2>{esc(title)}</h2>{body}</section>'
        for title, body, classes in sections
    ]
    return '<div class="section-stack">' + "".join(blocks) + "</div>"


def render_privacy_sections(payload: dict) -> str:
    content = [
        f'<section class="content-section content-section--wide"><h2>Privacy Policy</h2><p>{esc(payload["privacy_intro"])}</p></section>',
        render_policy_sections(payload["privacy_sections"], wide_first=True, page_kind="privacy"),
    ]
    if payload.get("support_email"):
        content.append(
            '<section class="content-section content-section--wide">'
            '<div class="contact-panel">'
            "<h3>Contact</h3>"
            "<p>For questions about this Privacy Policy or privacy requests, contact us.</p>"
            f'<p><strong>Email:</strong> <a href="mailto:{esc(payload["support_email"])}" class="email">{esc(payload["support_email"])}</a></p>'
            "</div></section>"
        )
    return '<div class="section-stack">' + "".join(content) + "</div>"


def render_terms_sections(payload: dict) -> str:
    content = [
        f'<section class="content-section content-section--wide"><h2>Terms &amp; Conditions</h2><p>{esc(payload["terms_intro"])}</p></section>',
        render_policy_sections(payload["terms_sections"], wide_first=False, page_kind="terms"),
    ]
    if payload.get("support_email"):
        content.append(
            '<section class="content-section">'
            '<div class="contact-panel">'
            "<h3>Need Help?</h3>"
            "<p>If you have questions about these Terms, contact us.</p>"
            f'<p><strong>Email:</strong> <a href="mailto:{esc(payload["support_email"])}" class="email">{esc(payload["support_email"])}</a></p>'
            "</div></section>"
        )
    return '<div class="section-stack">' + "".join(content) + "</div>"


def render_support_sections(payload: dict) -> str:
    content = [
        f'<section class="content-section content-section--wide"><h2>Frequently Asked Questions</h2>{render_faq_items(payload["faq_items"])}</section>',
    ]
    if payload.get("support_email"):
        content.append(
            '<section class="content-section content-section--wide support-footer">'
            "<h2>Still Need Help?</h2>"
            f"<p>{esc(payload['support_outro'])}</p>"
            '<div class="contact-panel">'
            f'<p><strong>Email:</strong> <a href="mailto:{esc(payload["support_email"])}" class="email">{esc(payload["support_email"])}</a></p>'
            "</div></section>"
        )
    return '<div class="section-stack">' + "".join(content) + "</div>"


def page_context(payload: dict, page_kind: str) -> dict[str, object]:
    app_name = str(payload["app_name"])
    support_email = str(payload.get("support_email") or "").strip()
    contact_card = [{"title": "Support contact", "body": support_email}] if support_email else []
    contexts = {
        "index": {
            "descriptor": payload["brand_overview"],
            "eyebrow": "Overview",
            "title": f"About {app_name}",
            "subtitle": payload["index_subtitle"],
            "lead": payload["purpose"],
            "meta_badges": payload.get("index_badges", ["Product overview", "Evidence-based output", "Shared legal set"]),
            "cards": payload.get(
                "index_cards",
                contact_card,
            ),
            "highlights": payload.get(
                "index_highlights",
                [
                    {"title": "Theme", "body": payload["brand_overview"]},
                    *([{"title": "Support", "body": support_email}] if support_email else []),
                ],
            ),
        },
        "privacy": {
            "descriptor": payload["privacy_brand_line"],
            "eyebrow": "Privacy",
            "title": "Privacy Policy",
            "subtitle": f"Last Updated: {payload['last_updated']}",
            "lead": payload["privacy_intro"],
            "outline_items": policy_outline_items(list(payload.get("privacy_sections", [])), "privacy"),
            "meta_badges": payload.get("privacy_badges", ["Collection", "Use", "Rights"]),
            "cards": payload.get(
                "privacy_cards",
                [
                    {"title": "Policy scope", "body": payload["privacy_brand_line"]},
                    *([{"title": "Contact", "body": support_email}] if support_email else []),
                ],
            ),
            "highlights": payload.get(
                "privacy_highlights",
                [
                    *([{"title": "Rights requests", "body": support_email}] if support_email else []),
                    {"title": "Coverage", "body": "Permissions, sharing, retention, and deletion notes."},
                ],
            ),
        },
        "terms": {
            "descriptor": payload["terms_brand_line"],
            "eyebrow": "Terms",
            "title": "Terms & Conditions",
            "subtitle": f"Last Updated: {payload['last_updated']}",
            "lead": payload["terms_intro"],
            "outline_items": policy_outline_items(list(payload.get("terms_sections", [])), "terms"),
            "meta_badges": payload.get("terms_badges", ["Use limits", "Service rules", "Paid access"]),
            "cards": payload.get(
                "terms_cards",
                [
                    {"title": "Service scope", "body": payload["terms_brand_line"]},
                    *([{"title": "Questions", "body": support_email}] if support_email else []),
                ],
            ),
            "highlights": payload.get(
                "terms_highlights",
                [
                    {"title": "Applies to", "body": "Service use, optional purchases, and support pathways."},
                    *([{"title": "Contact", "body": support_email}] if support_email else []),
                ],
            ),
        },
        "support": {
            "descriptor": payload["support_brand_line"],
            "eyebrow": "Support",
            "title": "Support",
            "subtitle": payload["support_subtitle"],
            "lead": payload["support_outro"],
            "meta_badges": payload.get("support_badges", ["FAQ", "Permissions", "Purchases"]),
            "cards": payload.get(
                "support_cards",
                [
                    *([{"title": "Fastest route", "body": support_email}] if support_email else []),
                    *([{"title": "Contact", "body": "Email support with your question."}] if support_email else []),
                ],
            ),
            "highlights": payload.get(
                "support_highlights",
                [
                    *([{"title": "Support email", "body": support_email}] if support_email else []),
                    {"title": "Coverage", "body": "Answers about available app features."},
                ],
            ),
        },
    }
    return contexts[page_kind]


def render_page_main(payload: dict, page_kind: str, spec: dict) -> str:
    if page_kind == "index":
        return render_overview_sections(payload, spec)
    if page_kind == "privacy":
        return render_privacy_sections(payload)
    if page_kind == "terms":
        return render_terms_sections(payload)
    return render_support_sections(payload)


def render_page_intro(payload: dict, context: dict[str, object]) -> str:
    subtitle_class = "page-last-updated" if str(context["eyebrow"]) in {"Privacy", "Terms"} else "page-subtitle"
    return (
        '<section class="page-intro">'
        f'<span class="page-label">{esc(payload["app_name"])} · {esc(context["eyebrow"])}</span>'
        f'<h1 class="page-title">{esc(context["title"])}</h1>'
        f'<p class="{subtitle_class}">{esc(context["subtitle"])}</p>'
        "</section>"
    )


def render_page_side(context: dict[str, object], *, include_highlights: bool = False) -> str:
    blocks: list[str] = []
    if context.get("outline_items"):
        blocks.append(render_policy_outline(list(context["outline_items"])))
    if context.get("cards"):
        blocks.append(render_context_cards(list(context["cards"])))
    if include_highlights and context.get("highlights"):
        blocks.append(render_context_cards(list(context["highlights"]), extra_class="context-card--accent"))
    if context.get("meta_badges"):
        blocks.append(
            '<section class="context-card"><h3>At a Glance</h3>'
            + render_badge_list([str(item) for item in context["meta_badges"]])
            + "</section>"
    )
    return '<aside class="page-side">' + "".join(blocks) + "</aside>"


def footer_note(payload: dict, page_kind: str) -> str:
    app_name = str(payload["app_name"])
    if page_kind == "index":
        return sanitize_visible_text(payload["index_subtitle"])
    return f"{app_name} · {payload.get('last_updated', '')}"


def render_top_nav(payload: dict, page_kind: str, spec: dict, context: dict[str, object]) -> str:
    brand = render_brand_lockup(str(payload["app_name"]), str(context["descriptor"]))
    nav = ""
    meta = (
        '<div class="topbar-meta">'
        f'<span class="topbar-kicker">{esc(context["eyebrow"])} pages</span>'
        f'<p class="topbar-note">{esc(context["descriptor"])}</p>'
        "</div>"
    )
    badges = ""
    if context.get("meta_badges"):
        badges = render_badge_list([str(item) for item in list(context["meta_badges"])[:3]])

    style = header_style(spec)
    if style == "nav-band":
        inner = nav + brand + meta
    elif style == "compact-row":
        inner = brand + meta
    elif style == "editorial-bar":
        inner = meta + nav + brand
    elif style == "stacked-frame":
        inner = brand + meta + badges + nav
    elif style == "policy-hero":
        inner = brand + meta + ('<div class="topbar-nav-group">' + badges + "</div>" if badges else "")
    elif style == "document-ribbon":
        inner = meta + badges + brand + nav
    elif style == "store-strip":
        inner = brand + ('<div class="topbar-nav-group">' + badges + "</div>" if badges else "") + meta
    elif style == "quiet-legal":
        inner = brand + meta
    else:
        inner = brand
    return f'<section class="page-topbar page-topbar--{esc(style)}">{inner}</section>'


def render_page_head(payload: dict, page_kind: str, spec: dict, context: dict[str, object]) -> str:
    intro = render_page_intro(payload, context)
    return '<div class="page-head">' + render_top_nav(payload, page_kind, spec, context) + intro + "</div>"


def render_footer_nav(payload: dict, page_kind: str, spec: dict) -> str:
    note = footer_note(payload, page_kind)
    return (
        '<footer class="page-footer page-footer--note-only">'
        f'<p class="footer-note">{esc(note)}</p>'
        "</footer>"
    )


def render_stacked_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    return (
        f'<div class="{shell_class_names(spec, "stacked")}">'
        '<div class="surface-block">'
        '<div class="page-main">'
        f'{render_page_head(payload, page_kind, spec, context)}'
        f'{main_html}'
        f'{render_footer_nav(payload, page_kind, spec)}'
        "</div>"
        "</div></div>"
    )


def render_split_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    return (
        f'<div class="{shell_class_names(spec, "split")}">'
        '<div class="surface-block">'
        '<div class="page-main">'
        f'{render_page_head(payload, page_kind, spec, context)}'
        '<div class="page-grid">'
        f'<div class="main-column">{main_html}</div>'
        f'{render_page_side(context)}'
        "</div>"
        f'{render_footer_nav(payload, page_kind, spec)}'
        "</div>"
        "</div></div>"
    )


def render_sidebar_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    return (
        f'<div class="{shell_class_names(spec, "sidebar")}">'
        '<div class="surface-block">'
        '<div class="page-main">'
        f'{render_page_head(payload, page_kind, spec, context)}'
        '<div class="page-grid">'
        f'<div class="main-column">{main_html}</div>'
        f'{render_page_side(context, include_highlights=True)}'
        "</div>"
        f'{render_footer_nav(payload, page_kind, spec)}'
        "</div></div></div>"
    )


def render_billboard_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    return (
        f'<div class="{shell_class_names(spec, "billboard")}">'
        '<div class="surface-block">'
        '<div class="page-main">'
        f'{render_page_head(payload, page_kind, spec, context)}'
        f'{main_html}'
        f'{render_page_side(context, include_highlights=True)}'
        f'{render_footer_nav(payload, page_kind, spec)}'
        "</div>"
        "</div></div>"
    )


def render_editorial_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    return (
        f'<div class="{shell_class_names(spec, "editorial")}">'
        '<div class="surface-block">'
        '<div class="page-main">'
        f'{render_page_head(payload, page_kind, spec, context)}'
        '<div class="page-grid">'
        f'<div class="main-column">{main_html}</div>'
        f'{render_page_side(context, include_highlights=True)}'
        "</div>"
        f'{render_footer_nav(payload, page_kind, spec)}'
        "</div>"
        "</div></div>"
    )


def render_shell(payload: dict, page_kind: str, spec: dict, context: dict[str, object], main_html: str) -> str:
    shell = str(spec["shell"])
    if shell == "split":
        return render_split_shell(payload, page_kind, spec, context, main_html)
    if shell == "sidebar":
        return render_sidebar_shell(payload, page_kind, spec, context, main_html)
    if shell == "billboard":
        return render_billboard_shell(payload, page_kind, spec, context, main_html)
    if shell == "editorial":
        return render_editorial_shell(payload, page_kind, spec, context, main_html)
    return render_stacked_shell(payload, page_kind, spec, context, main_html)


def render_page(
    title: str,
    description: str,
    theme: dict[str, str],
    body: str,
    template_id: str,
    page_kind: str,
    spec: dict,
) -> str:
    styles = build_style(theme, spec)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
        f'  <meta name="theme-color" content="{esc(theme["theme_color"])}">\n'
        f"  <title>{esc(title)}</title>\n"
        f'  <meta name="description" content="{esc(description)}">\n'
        f'  <meta name="app-listing-template" content="{esc(template_id)}">\n'
        "  <style>\n"
        f"{styles}\n"
        "  </style>\n"
        "</head>\n"
        f'<body data-template-id="{esc(template_id)}" data-page-kind="{esc(page_kind)}" data-visual-style="{esc(visual_style(spec))}">\n'
        '  <a class="skip-link" href="#main-content">Skip to content</a>\n'
        '  <main id="main-content" class="page-root">\n'
        f"{body}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


ONBOARDING_MANIFEST_PATH = ASSET_ROOT / "onboarding-templates-manifest.json"


def load_onboarding_manifest() -> dict:
    return json.loads(ONBOARDING_MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_onboarding(payload: dict, template_id: str) -> None:
    template_spec(load_onboarding_manifest(), template_id)
    onboarding = payload.get("onboarding")
    if not isinstance(onboarding, dict):
        raise ValueError("onboarding must contain project-authored carousel content")
    cards = onboarding.get("cards")
    if not isinstance(cards, list) or not 3 <= len(cards) <= 5:
        raise ValueError("onboarding carousel requires 3 to 5 cards")
    profile = payload.get("project_profile", {})
    confirmed_ids = {
        str(feature.get("id"))
        for feature in profile.get("features", [])
        if isinstance(feature, dict) and feature.get("status") == "confirmed"
    } if isinstance(profile, dict) else set()
    for card in cards:
        if not isinstance(card, dict) or not all(isinstance(card.get(key), str) and sanitize_visible_text(card[key]) for key in ("title", "body")):
            raise ValueError("each onboarding card needs a visible title and body")
        if len(card["title"]) > 60 or len(card["body"]) > 240:
            raise ValueError("onboarding card text exceeds the title/body budget (60/240)")
        fact_id = card.get("fact_id")
        if fact_id is not None and str(fact_id) not in confirmed_ids:
            raise ValueError("onboarding card references an unconfirmed project feature")
    texts = [payload.get("app_name", ""), onboarding.get("tagline", ""), onboarding.get("cta_label", "Continue")]
    texts += [card[key] for card in cards for key in ("title", "body")]
    if any(not isinstance(text, str) or re.search(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text) for text in texts):
        raise ValueError("onboarding visible copy must be English; provide an English app name and copy")
    if not str(onboarding.get("cta_label", "Continue")).strip():
        raise ValueError("onboarding CTA label cannot be empty")
    interval = onboarding.get("autoplay_interval_ms", 5000)
    if isinstance(interval, bool) or not isinstance(interval, int) or not 3000 <= interval <= 15000:
        raise ValueError("autoplay_interval_ms must be an integer between 3000 and 15000")


def render_onboarding_page(payload: dict, template_id: str) -> str:
    validate_onboarding(payload, template_id)
    onboarding = payload.get("onboarding", {})
    cards = onboarding.get("cards", []) if isinstance(onboarding, dict) else []
    cards = sanitize_visible_cards(cards)
    if len(cards) != len(onboarding["cards"]):
        raise ValueError("onboarding contains a hidden metadata or blocked card")
    app_name = sanitize_visible_text(payload.get("app_name", "App")) or "App"
    tagline = sanitize_visible_text(onboarding.get("tagline", payload.get("index_subtitle", "")))
    button_label = sanitize_visible_text(onboarding.get("cta_label", "Continue")) or "Continue"
    cards_html = "".join(
        f'<article class="onboarding-card{" is-active" if index == 0 else ""}" data-slide="{index}" aria-hidden="{str(index != 0).lower()}">'
        f'<div class="onboarding-visual" aria-hidden="true"><span>{index + 1:02d}</span></div>'
        f'<h2>{esc(card["title"])}</h2><p>{esc(card["body"])}</p></article>'
        for index, card in enumerate(cards)
    )
    dots_html = "".join(
        f'<button class="onboarding-dot{" is-active" if index == 0 else ""}" type="button" data-slide-to="{index}" aria-label="Show slide {index + 1}" aria-current="{"true" if index == 0 else "false"}"></button>'
        for index in range(len(cards))
    )
    visual_class = f"onboarding-page onboarding-page--{template_id.removeprefix('onboarding-')}"
    styles = f"""
html, body {{ margin: 0; min-height: 100%; }}
body {{ background: {esc(derive_theme_tokens(payload, template_spec(load_manifest(), "aurora-stack"))["page-bg"])}; }}
.onboarding-page {{ min-height: 100svh; min-height: 100dvh; padding: calc(24px + env(safe-area-inset-top, 0px)) calc(20px + env(safe-area-inset-right, 0px)) calc(20px + env(safe-area-inset-bottom, 0px)) calc(20px + env(safe-area-inset-left, 0px)); display: grid; place-items: center; font-family: system-ui, -apple-system, sans-serif; color: #172033; }}
.onboarding-page, .onboarding-page * {{ box-sizing: border-box; }}
.onboarding-frame {{ width: min(100%, 980px); min-height: min(720px, calc(100dvh - 40px)); display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: 20px; padding: clamp(22px, 5vw, 54px); border-radius: 32px; background: rgba(255,255,255,.88); box-shadow: 0 24px 70px rgba(20,30,60,.14); }}
.onboarding-header {{ display: grid; gap: 8px; }}
.onboarding-brand {{ font-size: clamp(22px, 3vw, 34px); font-weight: 800; letter-spacing: -.04em; }}
.onboarding-tagline {{ max-width: 620px; margin: 0; color: #5d687c; font-size: clamp(14px, 1.8vw, 18px); }}
.onboarding-stage {{ min-height: 0; display: grid; align-items: center; }}
.onboarding-card {{ display: none; width: min(100%, 650px); margin: auto; padding: clamp(22px, 5vw, 52px); border-radius: 26px; background: linear-gradient(145deg, #eef4ff, #ffffff); }}
.onboarding-card.is-active {{ display: block; animation: onboarding-in 220ms ease both; }}
.onboarding-visual {{ display: grid; place-items: center; width: clamp(76px, 12vw, 124px); aspect-ratio: 1; margin-bottom: 24px; border-radius: 30%; background: linear-gradient(135deg, #5b6ff5, #9b7bff); color: white; font-size: clamp(22px, 4vw, 42px); font-weight: 800; }}
.onboarding-card h2 {{ margin: 0 0 10px; font-size: clamp(26px, 5vw, 54px); line-height: 1.03; letter-spacing: -.045em; }}
.onboarding-card p {{ max-width: 560px; margin: 0; color: #5d687c; font-size: clamp(16px, 2vw, 21px); line-height: 1.5; }}
.onboarding-controls {{ display: grid; grid-template-columns: 1fr; align-items: center; gap: 16px; }}
.onboarding-dots {{ display: flex; justify-content: center; gap: 9px; }}
.onboarding-dot {{ width: 10px; height: 10px; padding: 0; border: 0; border-radius: 50%; background: #cbd3e5; cursor: pointer; }}
.onboarding-dot.is-active {{ width: 26px; border-radius: 99px; background: #5b6ff5; }}
.onboarding-action {{ grid-column: 1 / -1; justify-self: stretch; width: 100%; min-height: 60px; border: 0; border-radius: 999px; padding: 16px 24px; background: #18233b; color: white; font: inherit; font-size: 17px; font-weight: 750; cursor: pointer; }}
.onboarding-action:focus-visible, .onboarding-dot:focus-visible {{ outline: 3px solid #9b7bff; outline-offset: 4px; }}
@keyframes onboarding-in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.onboarding-page--compact .onboarding-frame {{ width: min(100%, 760px); min-height: min(560px, calc(100dvh - 40px)); padding: clamp(20px, 4vw, 36px); gap: 14px; }}
.onboarding-page--compact .onboarding-card {{ padding: clamp(20px, 4vw, 34px); }}
.onboarding-page--compact .onboarding-visual {{ width: 72px; margin-bottom: 16px; }}
.onboarding-page--minimal .onboarding-frame {{ width: min(100%, 680px); min-height: min(500px, calc(100dvh - 40px)); padding: clamp(20px, 4vw, 34px); gap: 12px; background: rgba(255,255,255,.94); box-shadow: 0 18px 54px rgba(20,30,60,.10); }}
.onboarding-page--minimal .onboarding-card {{ padding: clamp(18px, 4vw, 30px); background: transparent; }}
.onboarding-page--minimal .onboarding-visual {{ width: 58px; margin-bottom: 16px; border-radius: 18px; }}
.onboarding-page--feature-list .onboarding-frame {{ width: min(100%, 860px); }}
.onboarding-page--feature-list .onboarding-card {{ background: #f7f9ff; border: 1px solid #e2e8f8; }}
.onboarding-page--feature-list .onboarding-card h2 {{ letter-spacing: -.025em; }}
@media (min-width: 900px) {{ .onboarding-page--spotlight .onboarding-frame {{ grid-template-columns: .8fr 1.2fr; grid-template-rows: auto 1fr; }} .onboarding-page--spotlight .onboarding-header {{ align-self: start; }} .onboarding-page--spotlight .onboarding-stage {{ grid-column: 2; grid-row: 1 / span 2; }} .onboarding-page--spotlight .onboarding-controls {{ grid-column: 1; align-self: end; grid-template-columns: 1fr; }} .onboarding-page--spotlight .onboarding-action {{ justify-self: stretch; }} }}
@media (max-height: 720px) and (max-width: 600px) {{ .onboarding-frame {{ min-height: 0; padding: 20px; gap: 14px; }} .onboarding-card {{ padding: 20px; }} .onboarding-visual {{ width: 64px; margin-bottom: 14px; }} .onboarding-card h2 {{ font-size: 30px; }} .onboarding-card p {{ font-size: 15px; }} }}
@media (prefers-reduced-motion: reduce) {{ .onboarding-card.is-active {{ animation: none; }} }}
"""
    script = f"""
function continueToApp() {{
  if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {{
    window.AppBridge.postMessage('continue');
    return;
  }}
  window.location.href = 'go://continue';
}}
(function() {{
  const cards = Array.from(document.querySelectorAll('.onboarding-card'));
  const dots = Array.from(document.querySelectorAll('.onboarding-dot'));
  let current = 0;
  let timer = null;
  const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let hovered = false;
  let focused = false;
  function show(index) {{
    current = (index + cards.length) % cards.length;
    cards.forEach((card, slideIndex) => {{ card.classList.toggle('is-active', slideIndex === current); card.setAttribute('aria-hidden', String(slideIndex !== current)); }});
    dots.forEach((dot, slideIndex) => {{ dot.classList.toggle('is-active', slideIndex === current); dot.setAttribute('aria-current', String(slideIndex === current)); }});
    restart();
  }}
  function stop() {{ if (timer) {{ window.clearInterval(timer); timer = null; }} }}
  function restart() {{ stop(); if (!reduced && !document.hidden && !hovered && !focused && cards.length > 1) timer = window.setInterval(() => show(current + 1), {onboarding.get('autoplay_interval_ms', 5000)}); }}
  dots.forEach((dot, slideIndex) => dot.addEventListener('click', () => show(slideIndex)));
  const frame = document.querySelector('.onboarding-frame');
  frame.addEventListener('mouseenter', () => {{ hovered = true; stop(); }});
  frame.addEventListener('mouseleave', () => {{ hovered = false; restart(); }});
  frame.addEventListener('focusin', () => {{ focused = true; stop(); }});
  frame.addEventListener('focusout', (event) => {{ if (!frame.contains(event.relatedTarget)) {{ focused = false; restart(); }} }});
  document.querySelector('.onboarding-action').addEventListener('click', continueToApp);
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : restart());
  restart();
}})();
"""
    body = f'<div class="{visual_class}"><div class="onboarding-frame"><header class="onboarding-header"><div class="onboarding-brand">{esc(app_name)}</div><p class="onboarding-tagline">{esc(tagline)}</p></header><main class="onboarding-stage">{cards_html}</main><div class="onboarding-controls"><div class="onboarding-dots">{dots_html}</div><button class="onboarding-action" type="button">{esc(button_label)}</button></div></div></div>'
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"><title>{esc(app_name)}</title><style>{styles}</style></head><body data-template-id="{esc(template_id)}">{body}<script>{script}</script></body></html>'


def build_pages(payload: dict, template_id: str, onboarding_template_id: str | None = None) -> dict[str, str]:
    manifest = load_manifest()
    spec = template_spec(manifest, template_id)
    theme = derive_theme_tokens(payload, spec)
    app_name = str(payload["app_name"])
    index_title_suffix = str(payload.get("index_title_suffix", "Overview"))

    pages: dict[str, tuple[str, str, str]] = {
        "index.html": ("index", f"{app_name} | {index_title_suffix}", str(payload["index_meta_description"])),
        "PrivacyPolicy.html": ("privacy", f"{app_name} | Privacy Policy", str(payload["privacy_meta_description"])),
        "Terms&Conditions.html": ("terms", f"{app_name} | Terms & Conditions", str(payload["terms_meta_description"])),
        "Support.html": ("support", f"{app_name} | Support", str(payload["support_meta_description"])),
    }

    rendered: dict[str, str] = {}
    for filename, (page_kind, title, description) in pages.items():
        if page_kind == "index":
            selected = onboarding_template_id or payload.get("onboarding", {}).get("template_id") or payload.get("index_layout") or "onboarding-cards"
            rendered[filename] = render_onboarding_page(payload, str(selected))
            continue
        context = page_context(payload, page_kind)
        main_html = render_page_main(payload, page_kind, spec)
        body = render_shell(payload, page_kind, spec, context, main_html)
        rendered[filename] = render_page(title, description, theme, body, template_id, page_kind, spec)
    return rendered


def write_pages(output_dir: Path, pages: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, contents in pages.items():
        (output_dir / filename).write_text(contents, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render AppListing site pages with layout variants.")
    parser.add_argument("--payload-json", required=True, help="Path to rendering payload JSON")
    parser.add_argument("--output-dir", required=True, help="Path to site output directory")
    parser.add_argument("--template-id", help="Optional fixed template id")
    parser.add_argument("--onboarding-template-id", help="Optional independent launch-guide template id")
    parser.add_argument("--seed", help="Optional seed for deterministic random template choice")
    args = parser.parse_args()

    payload = json.loads(Path(args.payload_json).read_text(encoding="utf-8"))
    manifest = load_manifest()
    template_id = args.template_id or choose_template_id(manifest, args.seed)
    pages = build_pages(payload, template_id, args.onboarding_template_id)
    write_pages(Path(args.output_dir), pages)
    print(json.dumps({"template_id": template_id, "onboarding_template_id": args.onboarding_template_id or payload.get("onboarding", {}).get("template_id", "onboarding-cards"), "files": sorted(pages)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
