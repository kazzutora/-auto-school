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
from collections import deque
from dataclasses import dataclass

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = ROOT / "static" / "img" / "brand" / "source"
OUT = ROOT / "static" / "img" / "brand"

# The owner has sent more than one of these. Each is named here with what has
# to come out of it, so swapping the site's mark is a one word change and the
# pieces that are not in use keep their measurements rather than losing them.
#
# `slogan` is the rectangle to erase, in fractions — left, top, right, down to
# the bottom edge — or None where the piece has no slogan in it.
#
# Why a rectangle and not a crop: in the first piece, below the gap under the
# subline there are four separate things and only two of them are the slogan.
#
#   x 0.073..0.210   the wheel's lower arc
#   x 0.380..0.720   the slogan
#   x 0.728..0.759   the heart at the end of it
#   x 0.821..0.961   the plate's lower edge and the right hand heart
#
# The wheel bottoms out at 0.812 of the height and the plate at 0.763, both
# below the slogan's own top at 0.725, so a straight cut takes a slice off
# each. The first attempt did exactly that.
@dataclass(frozen=True)
class Piece:
    file: str
    # The slogan's rectangle to erase, or None where there is no slogan.
    slogan: tuple[float, float, float] | None = None
    # True where the file arrives on an opaque white card rather than on
    # transparency, and the card has to be lifted off before anything else.
    keyed: bool = False
    # Set where the piece *is* a plate — artwork on a solid coloured field
    # that stays. The number is how much air to leave around the ink, as a
    # fraction of the ink's own height, and the file's own uneven margin is
    # trimmed back to it. Mutually exclusive with `keyed`: one lifts the
    # background off, the other keeps it.
    plate: float | None = None


PIECES = {
    "wheel": Piece("lockup-owner.png", slogan=(0.375, 0.722, 0.765)),
    "crown": Piece("lockup-owner-v2.png"),
    "outline": Piece("lockup-owner-v3.png", keyed=True),
    "owner": Piece("lockup-owner-v4-light.png", keyed=True),
    "owner-red": Piece("lockup-owner-v4-red.png", plate=0.18),
}

# Which one the site shows.
#
# `owner-red` since core v44. The first three are the record of what was tried
# and all of them are the same mistake: an image generated from a description
# of the school's mark rather than the mark itself — a crown, a steering
# wheel, hand-drawn hearts, and a crimson that belongs to none of it.
#
# `owner` and `owner-red` are both the real mark, in the school's own two
# versions. v43 shipped `owner`, which is red and blue on transparency; v44
# ships the plate, because the palette went to red, white and graphite and the
# blue in `owner` was then the only blue on the site — a colour with nothing
# on the page to answer it. On graphite the blue subline all but disappeared
# as well. `owner` stays here: it is the one to come back to the day a blue
# earns a place again.
ACTIVE = "owner-red"

# How far from white a pixel may be and still count as the card it was sent
# on. Generous, because the edge where the artwork meets the card is a ramp
# and half-lifted pixels leave a bright halo — at the size this ships, six and
# a half times smaller than the file, a pixel of over-eager keying is nothing
# and a pixel of halo is a visible outline.
CARD = 40

# Twice the 56px the header draws it at. Three times would be sharper on a
# modern phone and costs half as much again per theme: this artwork is brush
# texture edge to edge, which is the one thing image codecs cannot throw away,
# so its weight tracks its pixel count almost exactly. Against the 17 KB the
# drawn svg cost — and the first screen's 400 KB in REDESIGN.md C.6 — 2x is
# the trade, and only one of the two files is ever fetched.
OUT_HEIGHT = 112

# What the ink becomes on the dark ground: --ink in the dark theme.
PALE = (237, 240, 245)

# And what the blue becomes there. The mark is two colours, and only one of
# them is a fill: app.css B.2 keeps the red where it is in both themes and
# lightens the blue, because #2A61AE on the dark page measures 2.0 and this
# measures 8.9. It is the dark theme's own --brand-700, so the subline under
# the wordmark and a link in the paragraph below it are the same blue.
PALE_BLUE = (143, 180, 236)

# A pixel is ink rather than crimson when it is dark and not red.
#
# It used to ask for dark and *unsaturated*, which held for the first two
# pieces and broke on the third: its subline is a near black with a blue cast,
# (15, 33, 47), and hsv saturation is measured against the largest channel —
# so 47 against 15 reads as 0.68, more saturated than a pastel. Darkness and
# hue are the two facts that actually separate the families here; saturation
# only says how confident the hue is.
INK_MAX_VALUE = 0.45

# Everything within this much of pure red in hue, with enough colour in it to
# mean the hue, is red and stays red whatever its brightness — a dark brush
# edge is still part of the stroke.
RED_ARC = 0.08
RED_MIN_SATURATION = 0.25

# The blue arc. The mark's blue sits at hue 0.597 with a saturation of 0.76,
# and the band is wide enough to take the antialiased edges with it: a pixel
# halfway between the blue and the white it sits on keeps the hue and loses
# the saturation, which is why the floor is low.
BLUE_ARC = (0.52, 0.70)
BLUE_MIN_SATURATION = 0.18


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


def plate_box(art: Image.Image, pad: float) -> tuple[int, int, int, int]:
    """The plate, trimmed to an even margin around its own ink.

    The file arrives with the artwork off centre — 23% of the height above it
    and 30% below — which at header size reads as a mark sitting high in its
    box. So the ink is found by asking which pixels are not the field colour,
    and the field is then cut back to the same air on all four sides.

    `pad` is a fraction of the ink's height rather than of the frame's: the
    frame is whatever the file happened to be saved at and the ink is the
    thing with a size worth measuring from.
    """
    rgb = art.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    field = pixels[0, 0]

    def is_field(x: int, y: int) -> bool:
        return all(abs(a - b) <= CARD for a, b in zip(pixels[x, y], field, strict=True))

    xs = [x for x in range(width) for y in range(0, height, 2) if not is_field(x, y)]
    ys = [y for y in range(height) for x in range(0, width, 2) if not is_field(x, y)]
    if not xs or not ys:
        raise SystemExit("the plate has no ink on it")

    air = round(pad * (max(ys) - min(ys)))
    return (
        max(0, min(xs) - air),
        max(0, min(ys) - air),
        min(width, max(xs) + air),
        min(height, max(ys) + air),
    )


def trimmed() -> Image.Image:
    """The active artwork, off its card or cut back to its plate."""
    piece = PIECES[ACTIVE]
    art = Image.open(SOURCES / piece.file).convert("RGBA")
    if piece.plate is not None:
        return art.crop(plate_box(art, piece.plate))
    if piece.keyed:
        art = lift_card(art)
    return art.crop(bbox(art))


def core(art: Image.Image) -> Image.Image:
    """The piece without its slogan, retrimmed to what is left."""
    slogan = PIECES[ACTIVE].slogan
    if slogan is None:
        return art

    left, top, right = slogan
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
    if v > INK_MAX_VALUE:
        return False
    reddish = s >= RED_MIN_SATURATION and (h <= RED_ARC or h >= 1 - RED_ARC)
    return not reddish


def is_blue(r: int, g: int, b: int) -> bool:
    """The mark's second colour, whatever the antialiasing did to it."""
    h, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return s >= BLUE_MIN_SATURATION and BLUE_ARC[0] <= h <= BLUE_ARC[1]


def lift_card(art: Image.Image) -> Image.Image:
    """Turn the white card the piece was sent on into transparency.

    A flood from the border rather than a colour key over the whole frame.
    The letters on this piece are crimson with a white line inside them, and a
    key would punch that line out along with the card — the flood cannot reach
    it, because the crimson stroke encloses it.

    The alpha is rebuilt and put back with putalpha. getchannel() returns a
    copy, so writing through its pixel access changes nothing at all: the first
    version of this did that, and the piece came out the full size of the card
    it arrived on with the trim reporting nothing to trim.
    """
    rgb = art.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()

    sr, sg, sb = pixels[0, 0]

    def is_card(x: int, y: int) -> bool:
        r, g, b = pixels[x, y]
        return abs(r - sr) <= CARD and abs(g - sg) <= CARD and abs(b - sb) <= CARD

    seen = bytearray(width * height)
    queue: deque[int] = deque()

    def push(x: int, y: int) -> None:
        index = y * width + x
        if not seen[index] and is_card(x, y):
            seen[index] = 1
            queue.append(index)

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)

    while queue:
        index = queue.popleft()
        x, y = index % width, index // width
        if x:
            push(x - 1, y)
        if x + 1 < width:
            push(x + 1, y)
        if y:
            push(x, y - 1)
        if y + 1 < height:
            push(x, y + 1)

    mask = Image.frombytes("L", (width, height), bytes(0 if f else 255 for f in seen))
    out = art.copy()
    out.putalpha(mask)
    return out


def recolour(r: int, g: int, b: int) -> tuple[int, int, int]:
    """What a pixel of the mark becomes on the dark ground.

    Ink goes pale and blue goes to the light blue. Red is not here on
    purpose: it is a fill rather than a role and does not swap with the
    theme, which is the same rule the buttons follow.
    """
    if is_ink(r, g, b):
        return PALE
    if is_blue(r, g, b):
        return PALE_BLUE
    return (r, g, b)


def repaint(art: Image.Image) -> Image.Image:
    """The same artwork recoloured for the dark ground.

    The alpha is untouched, so every antialiased edge keeps the shape it had:
    what changes is which colour those edges are fading from.
    """
    out = art.copy()
    pixels = list(out.getdata())
    swapped = [(*recolour(r, g, b), a) if a else (r, g, b, a) for r, g, b, a in pixels]
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
    print(f"piece {ACTIVE}: {PIECES[ACTIVE].file}")
    art = core(trimmed())
    print(f"core band {art.width}x{art.height}, {art.width / art.height:.2f}:1")
    save(art, "lockup-owner")
    save(repaint(art), "lockup-owner-dark")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
