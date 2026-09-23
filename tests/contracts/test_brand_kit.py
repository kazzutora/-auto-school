"""The logo kit holds its shape, ROSE.md K1.

The mark is generated — scripts/brand/gen_logo.py — and the point of these is
that a regeneration cannot quietly break the two properties the lockup depends
on: that it is curves rather than type, and that it is vector rather than a png
in a wrapper. Both fail silently. A <text> element looks right on the machine
that made it and reflows on every machine without Rubik installed; an embedded
raster looks right until somebody opens the footer at 2x.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

BRAND = Path(settings.BASE_DIR) / "static" / "img" / "brand"

VECTOR = [
    "logo-full.svg",
    "logo-full-dark.svg",
    "logo-compact.svg",
    "logo-compact-dark.svg",
    "mark-wheel.svg",
    "mark-l.svg",
    "favicon.svg",
]

RASTER = [
    "favicon-96.png",
    "apple-touch-icon-180.png",
    "icon-192.png",
    "icon-512.png",
    "maskable-512.png",
    "og-default.jpg",
]

# Core v43. Nothing in the kit may reach outside this list, and in particular
# nothing may keep the crimson family of cores v29 to v42.
#
# The two brand colours here are the mark's own, measured out of the file the
# owner sent: #EA232C and #2A61AE. The red is deliberately not the stylesheet's
# --brand-red, which is four percent darker so that a white button label
# clears 4.5 — a drawn letterform carries no white text on it and has no such
# constraint. scripts/check_contrast.py holds the other side of that line: it
# fails if #EA232C ever turns up in app.css.
ALLOWED = {"#EA232C", "#2A61AE", "#FDECED", "#FFFFFF", "#F5F6F8", "#16181D"}
HEX = re.compile(r"#[0-9A-Fa-f]{3,8}")


@pytest.mark.parametrize("name", VECTOR)
def test_the_file_is_there(name: str) -> None:
    assert (BRAND / name).exists(), name


@pytest.mark.parametrize("name", RASTER)
def test_the_raster_is_there(name: str) -> None:
    assert (BRAND / name).exists(), name


@pytest.mark.parametrize("name", VECTOR)
def test_no_text_element(name: str) -> None:
    """Lettering is outlines. A <text> waits on a webfont; a path does not."""
    svg = (BRAND / name).read_text(encoding="utf-8")
    assert "<text" not in svg
    assert "font-family" not in svg


@pytest.mark.parametrize("name", VECTOR)
def test_no_embedded_raster(name: str) -> None:
    svg = (BRAND / name).read_text(encoding="utf-8")
    assert "<image" not in svg
    assert "data:image" not in svg


@pytest.mark.parametrize("name", VECTOR)
def test_only_the_palette(name: str) -> None:
    svg = (BRAND / name).read_text(encoding="utf-8")
    found = {value.upper() for value in HEX.findall(svg)}
    assert found <= ALLOWED, sorted(found - ALLOWED)


@pytest.mark.parametrize("name", VECTOR)
def test_it_scales(name: str) -> None:
    """A viewBox is what lets the header ask for 40px and get 40px."""
    svg = (BRAND / name).read_text(encoding="utf-8")
    assert "viewBox=" in svg


def test_the_favicon_is_square() -> None:
    """At 16px a plate at the owner's 1.28 is twelve pixels wide and mush."""
    svg = (BRAND / "favicon.svg").read_text(encoding="utf-8")
    box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    assert box is not None
    assert box[1] == box[2], box.group(0)


def test_the_header_lockup_stays_light() -> None:
    """It ships on every page, so it is the one with a budget."""
    weight = (BRAND / "logo-compact.svg").stat().st_size
    assert weight < 24_000, weight
