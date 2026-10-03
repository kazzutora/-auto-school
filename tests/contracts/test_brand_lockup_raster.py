"""The lockup the pages actually show, ROSE.md K1 as amended at core v31.

`test_brand_kit.py` guards the drawn mark and says in its own opening that an
embedded raster is a defect. That still holds for everything it lists. This
file covers the one deliberate exception: the owner sent finished artwork —
brush strokes with torn edges, hand-drawn hearts — and asked for it on the
site. None of that is describable as geometry, so it ships as pixels, and the
things that go wrong with pixels need guarding instead.

Three of them, and all three have been wrong once already in this file's
history:

  * the crop, which silently took a slice off the wheel the first time;
  * the dark theme, where whichever part of the artwork is a *role* rather
    than a fill has to move — and on a plate, where nothing is a role, has to
    stay exactly where it is;
  * the weight, because this is in the header of every page on the site.
"""

import colorsys
import re
import sys
from pathlib import Path

import pytest
from django.conf import settings
from PIL import Image

BRAND = Path(settings.BASE_DIR) / "static" / "img" / "brand"
CSS = Path(settings.BASE_DIR) / "static" / "src" / "css" / "app.css"

VARIANTS = ["lockup-owner", "lockup-owner-dark"]
FORMATS = [".avif", ".webp"]

# One of these is fetched per page — never both, because they are declared as
# css backgrounds rather than as two <img> with one hidden. The drawn svg it
# replaced was 17 KB, and the first screen has 400 KB in REDESIGN.md C.6.
WEIGHT_CEILING = 34_000


@pytest.mark.parametrize("stem", VARIANTS)
@pytest.mark.parametrize("suffix", FORMATS)
def test_both_themes_ship_in_both_formats(stem: str, suffix: str) -> None:
    path = BRAND / (stem + suffix)
    assert path.exists(), f"{path.name} is missing — run gen_lockup_raster"
    assert path.stat().st_size < WEIGHT_CEILING, path.stat().st_size


def test_the_shipped_piece_is_trimmed_to_its_own_ink() -> None:
    """The trim is the thing that failed silently.

    Image.getbbox() counts any alpha above nothing at all, and these files
    arrive with a haze of 1s and 2s reaching every edge of the canvas — so the
    plain call trimmed nothing, and after the first piece's slogan was erased
    it went on reporting the full height of a frame whose bottom eighth was
    empty. The box on the page is sized by height, so an untrimmed file is a
    mark that renders small with air around it and nothing that says why.

    The assertion holds whatever piece is active: ink has to reach all four
    edges. It does not care how the piece is composed, which is the point —
    the owner has sent two of them and will send more.
    """
    art = Image.open(BRAND / "lockup-owner.webp").convert("RGBA")
    alpha = art.getchannel("A")
    margin = 0.02  # the trim's own rounding, no more

    def inked(box: tuple[int, int, int, int]) -> bool:
        return any(p > 8 for p in alpha.crop(box).getdata())

    edge_w = max(1, round(art.width * margin))
    edge_h = max(1, round(art.height * margin))

    assert inked((0, 0, edge_w, art.height)), "empty column down the left"
    assert inked((art.width - edge_w, 0, art.width, art.height)), "empty column down the right"
    assert inked((0, 0, art.width, edge_h)), "empty band across the top"
    assert inked((0, art.height - edge_h, art.width, art.height)), "empty band across the bottom"


def test_the_stylesheet_reserves_the_shape_the_file_has() -> None:
    """A wrong aspect-ratio squashes the artwork rather than failing.

    The box is sized by height and its width comes from this one declaration,
    so the number here and the file on disk are the same fact written twice.

    The ratio is compared rather than the pair, because the pair is free to be
    any equivalent one — the source band is 2091x496 and the file that ships
    is that band scaled down. What must not drift is the shape.
    """
    art = Image.open(BRAND / "lockup-owner.webp")
    found = re.search(r"aspect-ratio:\s*([\d.]+)\s*/\s*([\d.]+)\s*;", CSS.read_text("utf-8"))
    assert found, "no aspect-ratio declared for the lockup"

    declared = float(found[1]) / float(found[2])
    assert declared == pytest.approx(art.width / art.height, rel=0.01), (
        found[0],
        f"{art.width}x{art.height}",
    )


def active_piece():
    """The Piece the generator is set to, loaded rather than described.

    What the dark variant has to do depends on which artwork is active, and
    the one thing this test must not do is keep its own copy of that answer.
    """
    import importlib.util

    path = Path(settings.BASE_DIR) / "scripts" / "brand" / "gen_lockup_raster.py"
    spec = importlib.util.spec_from_file_location("gen_lockup_raster", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves a class's module through sys.modules while the
    # module is still executing, so it has to be there first.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module.PIECES[module.ACTIVE]


def test_the_dark_variant_matches_what_the_artwork_is() -> None:
    """The rule is app.css B.2: a fill stays across the themes, a role moves.

    Which of the two the mark contains depends on the artwork, so this asserts
    against the active piece rather than against a remembered answer.

    A plate — white lettering on the school's red field, which is what v44
    ships — holds no role colour at all. Both of its colours are fills, so the
    dark file is legitimately identical to the light one and the thing worth
    guarding is that the red is the mark's own and the lettering is white.

    The transparent piece is the other case: its blue is structure and has to
    lighten, because #2A61AE on the dark page measures 2.0 against the 8.9 the
    light version manages.

    Counting near-black pixels, which is what the first version of this test
    did, worked only on the drawn pieces that preceded the owner's own files.
    """
    light = Image.open(BRAND / "lockup-owner.webp").convert("RGBA")
    dark = Image.open(BRAND / "lockup-owner-dark.webp").convert("RGBA")
    assert light.size == dark.size

    def family(image: Image.Image, lo: float, hi: float) -> list[tuple[int, int, int]]:
        """The opaque pixels whose hue falls in an arc, as rgb triples."""
        return [
            (r, g, b)
            for r, g, b, a in image.getdata()
            if a > 200 and lo <= colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] <= hi
        ]

    def mean_value(pixels: list[tuple[int, int, int]]) -> float:
        return sum(max(p) for p in pixels) / len(pixels)

    red_light, red_dark = family(light, 0.0, 0.03), family(dark, 0.0, 0.03)
    assert red_light and red_dark, "no red in the mark"
    # The red is a fill either way: it does not move between the themes. A
    # couple of points of slack for the codec.
    assert abs(mean_value(red_dark) - mean_value(red_light)) < 4, (
        mean_value(red_light),
        mean_value(red_dark),
    )

    if active_piece().plate is not None:
        # A plate. Its field is the mark's own red, and the lettering on it is
        # white — the pair app.css forbids anywhere else and the only pair
        # this artwork has.
        assert 224 <= mean_value(red_light) <= 244, mean_value(red_light)
        white = [p for p in light.convert("RGB").getdata() if min(p) > 230]
        assert len(white) > light.width * light.height // 20, "the lettering is not white"
        return

    # Not a plate: the blue is a role and has to lighten. #2A61AE tops out at
    # 174 and #8FB4EC at 236, so the step is one no re-encoding could produce.
    blue_light, blue_dark = family(light, 0.52, 0.70), family(dark, 0.52, 0.70)
    assert blue_light and blue_dark, "no blue in the mark"
    assert mean_value(blue_dark) > mean_value(blue_light) + 30, (
        mean_value(blue_light),
        mean_value(blue_dark),
    )


def test_the_pages_reference_both_variants() -> None:
    """Whichever file the rule names, the theme switch has to reach it.

    `dark:` here is the media query and the [data-theme] attribute both, the
    way tailwind.config.js defines it. A <picture> with a prefers-color-scheme
    source would follow the system preference alone and leave a pale wordmark
    on a light page.
    """
    css = CSS.read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in css
    assert ':root[data-theme="dark"] .u-lockup' in css
    assert css.count("lockup-owner-dark") >= 4
