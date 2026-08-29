"""The size budgets in FRONTEND.md A.11, as a gate rather than a hope.

Measured on the built files the way a browser receives them: gzipped, because
that is what goes over the wire, and against the thresholds A.11 fixes.

A budget nobody checks is a budget that has already been spent. This is the
test that goes red the day somebody adds a css framework.
"""

import gzip
from pathlib import Path

import pytest
from django.conf import settings

# A.11, in bytes.
CSS_BUDGET = 30 * 1024
JS_BUDGET = 45 * 1024

STATIC = Path(settings.BASE_DIR) / "static"
BUILT_CSS = STATIC / "css" / "app.css"

# htmx, alpine and our own, on every page. Leaflet is deliberately not here: it
# rides on the two pages that carry a map and base.html stays free of it, so it
# is not part of what every visitor downloads.
SITE_WIDE_JS = ("htmx.min.js", "alpine.min.js", "app.js")


def gzipped(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


@pytest.fixture(scope="module")
def built_css() -> Path:
    if not BUILT_CSS.exists():
        pytest.skip("run `make css` first: the built stylesheet is gitignored")
    return BUILT_CSS


def test_the_stylesheet_fits_its_budget(built_css: Path) -> None:
    size = gzipped(built_css)
    assert size <= CSS_BUDGET, f"css is {size} B gzipped, budget is {CSS_BUDGET} B"


def test_the_stylesheet_is_actually_built(built_css: Path) -> None:
    """A truncated or empty file would pass the budget by being nothing."""
    assert built_css.stat().st_size > 10_000
    assert "--ink" in built_css.read_text(encoding="utf-8")


def test_the_javascript_fits_its_budget() -> None:
    total = sum(gzipped(STATIC / "js" / name) for name in SITE_WIDE_JS)
    assert total <= JS_BUDGET, f"js is {total} B gzipped, budget is {JS_BUDGET} B"


def test_no_stylesheet_reaches_a_third_party() -> None:
    """A.11: zero requests to a third party domain, and the css is where a font
    host would sneak back in."""
    css = BUILT_CSS.read_text(encoding="utf-8") if BUILT_CSS.exists() else ""
    for host in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.", "unpkg.com", "jsdelivr"):
        assert host not in css, f"the stylesheet reaches {host}"


def test_every_font_the_first_screen_needs_is_local() -> None:
    fonts = sorted((STATIC / "fonts").glob("*.woff2"))
    assert fonts, "no fonts shipped at all"
    # latin and latin-ext are what a polish page pulls; the cyrillic subsets
    # only load on /ru/ and /uk/.
    polish = [font for font in fonts if "cyrillic" not in font.name]
    weight = sum(font.stat().st_size for font in polish)
    # Fonts are already compressed, so this is the wire weight as it stands.
    assert weight < 250 * 1024, f"the polish faces come to {weight} B"
