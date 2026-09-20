"""Cut the owner's own lockup into the two files the pages use.

Everything else in `scripts/brand/` draws the mark from numbers. This one does
not draw anything: the owner sent a finished piece of artwork — brush strokes,
hand-drawn hearts, a torn edge on every letter — and asked for that, not for a
redrawing of it. None of it is describable as geometry, so it ships as pixels.

Two things still have to happen to it before a page can use it.

**It is cropped to the part that reads at 44px.** The full piece is 3.03:1 and
carries a slogan in handwriting and a second, tiny OSTRYCHARZ scribbled above
the first. In a header row 44px tall the slogan would be six pixels of pink
fuzz — and the footer already sets the same words as selectable text in Caveat
right under the mark. So the pages get the core band: wheel, word, subline,
plate with the cap, and the two hearts beside them.

**The ink is repainted for the dark theme.** The word, the wheel and the
subline are near black. On the dark page that is black on black; the crimson
would float there on its own. ROSE.md B.2 again: fills do not swap with the
theme, roles do — the crimson is a fill and stays put, the ink is a role and
becomes the pale token.

    python -m scripts.brand.gen_lockup_raster
"""

from __future__ import annotations

import colorsys
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "static" / "img" / "brand" / "source" / "lockup-owner.png"
OUT = ROOT / "static" / "img" / "brand"

# The slogan is erased, not cropped off. Everything in the piece was measured
# rather than eyeballed, and the measurement says a horizontal cut cannot do
# this job: below the gap under the subline there are four separate things,
# and only two of them are the slogan.
#
#   x 0.073..0.210   the wheel's lower arc
#   x 0.380..0.720   the slogan
#   x 0.728..0.759   the heart at the end of it
#   x 0.821..0.961   the plate's lower edge and the right hand heart
#
# The wheel bottoms out at 0.812 of the height and the plate at 0.763, both
# below the slogan's own top at 0.725. Cutting straight across at the slogan
# takes a slice off the wheel and the plate with it — which is exactly what the
# first attempt did.
SLOGAN = (0.375, 0.722, 0.765)  # left, top, right — all fractions

# Twice the 56px the header draws it at. Three times would be sharper on a
# modern phone and costs half as much again per theme: this artwork is brush
# texture edge to edge, which is the one thing image codecs cannot throw away,
# so its weight tracks its pixel count almost exactly. Against the 17 KB the
# drawn svg cost — and the first screen's 400 KB in REDESIGN.md C.6 — 2x is
# the trade, and only one of the two files is ever fetched.
OUT_HEIGHT = 112

# What the ink becomes on the dark ground: --ink at core v29, 246 233 236.
PALE = (246, 233, 236)

# A pixel is ink rather than crimson when it is dark and unsaturated. The
# artwork has exactly two colour families — near black around #1E1E2E and
# crimson around #DC0040 — so the line between them is wide. The test is
# deliberately loose on saturation and tight on value: a dark crimson stroke is
# still crimson, and painting it pale would take the brush edges with it.
INK_MAX_VALUE = 0.42
INK_MAX_SATURATION = 0.55


# Below this the pixel is not part of the artwork. Image.getbbox() counts any
# alpha above nothing at all, and this piece has a haze of 1s and 2s reaching
# every edge of the canvas — so the plain call trimmed nothing, and after the
# slogan was erased it went on reporting the full height of a frame whose
# bottom eighth was empty.
FAINT = 8


def bbox(art: Image.Image) -> tuple[int, int, int, int]:
    """Where the artwork actually is, ignoring the haze."""
    solid = art.getchannel("A").point(lambda v: 255 if v > FAINT else 0)
    box = solid.getbbox()
    if box is None:
        raise SystemExit("the source has no opaque pixels")
    return box


def trimmed() -> Image.Image:
    """The artwork with its transparent margin removed."""
    art = Image.open(SOURCE).convert("RGBA")
    return art.crop(bbox(art))


def core(art: Image.Image) -> Image.Image:
    """The piece without its slogan, retrimmed to what is left."""
    left, top, right = SLOGAN
    out = art.copy()
    out.paste(
        (0, 0, 0, 0),
        (
            round(out.width * left),
            round(out.height * top),
            round(out.width * right),
            out.height,
        ),
    )

    # Retrim: the slogan reached further down than anything that stays, so the
    # piece is shorter now, and it started further left than the wheel does.
    return out.crop(bbox(out))


def is_ink(r: int, g: int, b: int) -> bool:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    del h
    return v <= INK_MAX_VALUE and s <= INK_MAX_SATURATION


def repaint(art: Image.Image) -> Image.Image:
    """The same artwork with its ink pale, for the dark ground.

    The alpha is untouched, so every antialiased edge keeps the shape it had:
    what changes is which colour those edges are fading from.
    """
    out = art.copy()
    pixels = list(out.getdata())
    swapped = [
        (*PALE, a) if a and is_ink(r, g, b) else (r, g, b, a) for r, g, b, a in pixels
    ]
    out.putdata(swapped)
    return out


def save(art: Image.Image, stem: str) -> None:
    """Two formats. No png: nothing that runs today needs one.

    webp has been in every browser since Safari 14 in 2020, and the pages
    reference these through `image-set()` in the stylesheet, which falls back
    from avif to webp on its own.
    """
    scaled = art.resize(
        (round(art.width * OUT_HEIGHT / art.height), OUT_HEIGHT), Image.LANCZOS
    )
    # 74, not 82. The piece grew by half again when the lockup went from 44px
    # to 56px, and 82 put the dark file over the 34 KB the contract allows.
    # Brush texture is the one subject where the quality dial is nearly free:
    # a codec's artefacts are noise, and every pixel here is already noise.
    for suffix, options in (
        (".avif", {"quality": 74}),
        (".webp", {"quality": 74, "method": 6}),
    ):
        path = OUT / (stem + suffix)
        scaled.save(path, **options)
        print(f"    {path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KB")


def main() -> int:
    art = core(trimmed())
    print(f"core band {art.width}x{art.height}, {art.width / art.height:.2f}:1")
    save(art, "lockup-owner")
    save(repaint(art), "lockup-owner-dark")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
