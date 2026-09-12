"""The size budgets in REDESIGN.md C.6, as a gate rather than a hope.

Measured on the built files the way a browser receives them: gzipped, because
that is what goes over the wire, and against the thresholds C.6 fixes.

A budget nobody checks is a budget that has already been spent. This is the
test that goes red the day somebody adds a css framework — or, now that C.2
forbids one by name, an animation library.

The same numbers are enforced by scripts/check_budget.py, which is what CI runs
before pytest and what `make budget` runs locally. Two callers, one set of
thresholds: this module imports them rather than keeping a second copy.
"""

import gzip
import importlib.util
from pathlib import Path

import pytest
from django.conf import settings

STATIC = Path(settings.BASE_DIR) / "static"
BUILT_CSS = STATIC / "css" / "app.css"
BUILT_MOTION_CSS = STATIC / "css" / "motion.css"


def _budget_module():
    """scripts/ is not a package, so the gate is loaded by path."""
    path = Path(settings.BASE_DIR) / "scripts" / "check_budget.py"
    spec = importlib.util.spec_from_file_location("check_budget", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUDGET = _budget_module()
CSS_BUDGET = dict((label, limit) for label, _, limit in BUDGET.BUDGETS)["css"]
JS_BUDGET = dict((label, limit) for label, _, limit in BUDGET.BUDGETS)["js"]

# htmx, alpine and our own two, on every page. Leaflet is deliberately not here:
# it rides on the two pages that carry a map and base.html stays free of it, so
# it is not part of what every visitor downloads.
SITE_WIDE_JS = ("htmx.min.js", "alpine.min.js", "app.js", "motion.js")


def gzipped(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


@pytest.fixture(scope="module")
def built_css() -> Path:
    if not BUILT_CSS.exists():
        pytest.skip("run `make css` first: the built stylesheet is gitignored")
    return BUILT_CSS


def test_the_stylesheet_fits_its_budget(built_css: Path) -> None:
    size = gzipped(built_css)
    if BUILT_MOTION_CSS.exists():
        size += gzipped(BUILT_MOTION_CSS)
    assert size <= CSS_BUDGET, f"css is {size} B gzipped, budget is {CSS_BUDGET} B"


def test_the_stylesheet_is_actually_built(built_css: Path) -> None:
    """A truncated or empty file would pass the budget by being nothing."""
    assert built_css.stat().st_size > 10_000
    assert "--ink" in built_css.read_text(encoding="utf-8")


def test_the_javascript_fits_its_budget() -> None:
    total = sum(gzipped(STATIC / "js" / name) for name in SITE_WIDE_JS)
    assert total <= JS_BUDGET, f"js is {total} B gzipped, budget is {JS_BUDGET} B"


def test_the_motion_script_stays_small() -> None:
    """C.2 caps our own motion script at 3 KB, and R10 point 10 re-checks it.

    The number is what stops a library arriving one helper at a time. See the
    note on MOTION_GZIP_MAX for why it is measured gzipped.
    """
    size = gzipped(STATIC / "js" / "motion.js")
    assert size <= BUDGET.MOTION_GZIP_MAX, (
        f"motion.js is {size} B gzipped, budget is {BUDGET.MOTION_GZIP_MAX} B"
    )


def test_no_animation_library_anywhere() -> None:
    """C.2 bans GSAP, Motion and AOS by name; R10 point 9 checks the whole tree.

    Comments are stripped first, because C.2's reasoning names the very
    libraries it forbids and quoting a rule is not breaking it.
    """
    for path in list((STATIC / "js").glob("*.js")) + list((STATIC / "css").glob("*.css")):
        text = BUDGET.strip_comments(path.read_text(encoding="utf-8", errors="ignore")).lower()
        for banned in BUDGET.BANNED:
            assert banned not in text, f"{path.name} mentions {banned}"


def test_no_stylesheet_reaches_a_third_party() -> None:
    """C.6: zero requests to a third party domain, and the css is where a font
    host would sneak back in."""
    for built in (BUILT_CSS, BUILT_MOTION_CSS):
        css = built.read_text(encoding="utf-8") if built.exists() else ""
        for host in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.", "unpkg.com", "jsdelivr"):
            assert host not in css, f"{built.name} reaches {host}"


def test_every_font_the_first_screen_needs_is_local() -> None:
    fonts = sorted((STATIC / "fonts").glob("*.woff2"))
    assert fonts, "no fonts shipped at all"
    # latin and latin-ext are what a polish page pulls; the cyrillic subsets
    # only load on /ru/ and /uk/.
    polish = [font for font in fonts if "cyrillic" not in font.name]
    weight = sum(font.stat().st_size for font in polish)
    # Fonts are already compressed, so this is the wire weight as it stands.
    assert weight < 250 * 1024, f"the polish faces come to {weight} B"


def test_public_sans_is_gone() -> None:
    """B.3 replaced it with Manrope, and R1 point 3 says to delete it.

    A face nobody references is dead weight in the image and one @font-face
    away from coming back by accident.
    """
    leftovers = list((STATIC / "fonts").glob("public-sans*"))
    assert not leftovers, f"Public Sans is still shipped: {leftovers}"

    # The declaration, not the name. app.css explains at length why the face was
    # swapped and what that closed, and a test that reads prose would fail over
    # the record of the change it is checking for.
    source = (STATIC / "src" / "css" / "app.css").read_text(encoding="utf-8")
    assert "font-family: 'Public Sans'" not in source, "app.css still declares Public Sans"
    assert "public-sans" not in source, "app.css still points at a Public Sans file"


def test_manrope_carries_cyrillic() -> None:
    """The half of the old CONTRACT GAP that B.3 closed.

    Public Sans shipped no cyrillic at all, so /ru/ and /uk/ fell back to the
    system sans for every paragraph. If the cyrillic subsets ever stop being
    shipped, that regression comes straight back and nothing else would catch
    it — the pages still render, just in the wrong face.
    """
    for subset in ("cyrillic", "cyrillic-ext"):
        assert (STATIC / "fonts" / f"manrope-{subset}.woff2").exists(), (
            f"manrope-{subset}.woff2 is missing"
        )
