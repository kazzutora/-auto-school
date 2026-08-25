"""Design tokens and self hosted fonts, tech.md sections 2 and 7."""

import re
from pathlib import Path

import pytest
from django.conf import settings

CONFIG = Path(settings.BASE_DIR) / "tailwind.config.js"
APP_CSS = Path(settings.BASE_DIR) / "static" / "src" / "css" / "app.css"
FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"

# tech.md section 7, taken from the OSK NAWROCKI banner.
TECH_MD_TOKENS = {
    "brand": {"900": "#2A1F55", "700": "#3B2D71", "500": "#5B47A8", "100": "#EBE6F8"},
    "accent": {"500": "#FFD400", "600": "#E0BA00"},
    "ink": {"900": "#181328", "700": "#3A3350", "500": "#6B6383"},
    "paper": {"0": "#FFFFFF", "50": "#F7F6FA", "100": "#EFEDF4"},
    "state": {"ok": "#1E7A56", "warn": "#B27C00", "err": "#B3382B"},
}


def parse_group(name: str) -> dict[str, str]:
    body = re.search(rf"\b{name}:\s*\{{(.*?)\}}", CONFIG.read_text(encoding="utf-8"), re.S)
    assert body, f"colour group {name!r} missing from tailwind.config.js"
    return {
        key: value.upper()
        for key, value in re.findall(r'([\w]+):\s*"(#[0-9a-fA-F]{6})"', body.group(1))
    }


@pytest.mark.parametrize("group", TECH_MD_TOKENS)
def test_palette_matches_tech_md(group: str) -> None:
    assert parse_group(group) == TECH_MD_TOKENS[group]


def test_no_extra_colour_groups_crept_in() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    colours = re.search(r"colors:\s*\{(.*?)\n      \},", config, re.S)
    assert colours
    groups = set(re.findall(r"\n\s+(\w+):\s*\{", colours.group(1)))
    assert groups == set(TECH_MD_TOKENS)


def test_both_families_are_declared() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    assert '"Roboto Condensed"' in config  # condensed grotesque, headings
    assert '"Source Sans 3"' in config  # humanist sans, body


def test_fonts_are_self_hosted() -> None:
    """tech.md section 2 bans third party font hosts on public pages."""
    css = APP_CSS.read_text(encoding="utf-8")
    assert re.findall(r"url\(([^)]+)\)", css), "no font urls at all"
    for url in re.findall(r"url\(([^)]+)\)", css):
        assert url.startswith("../fonts/"), f"{url} is not served from our own static files"
    assert "https://" not in css
    assert "fonts.googleapis.com" not in css
    assert "fonts.gstatic.com" not in css


def test_every_declared_font_file_exists() -> None:
    css = APP_CSS.read_text(encoding="utf-8")
    for url in re.findall(r"url\(\.\./fonts/([^)]+)\)", css):
        assert (FONT_DIR / url).is_file(), f"{url} declared but not shipped"


def test_faces_use_display_swap() -> None:
    css = APP_CSS.read_text(encoding="utf-8")
    faces = css.count("@font-face")
    assert faces >= 2
    assert css.count("font-display: swap") == faces


def test_cyrillic_is_covered_for_the_ru_and_uk_versions() -> None:
    """The site ships in pl, ru and uk, so a latin only subset would show tofu."""
    css = APP_CSS.read_text(encoding="utf-8")
    for family in ("roboto-condensed", "source-sans-3"):
        assert f"{family}-cyrillic.woff2" in css
        assert f"{family}-latin-ext.woff2" in css  # polish ł ą ę ś ć ż ź ń
