"""Raster the app icons and the social card, ROSE.md K1 step 4.

    python -m scripts.brand.gen_icons

Browsers and phones still want png, so the L plate and the lockup are drawn a
second time here with Pillow, from the same numbers in scripts/brand/geometry.py
that gen_logo.py writes into svg. Two renderers off one set of parameters is
what keeps the favicon and the header logo the same mark a year from now.

Everything is drawn at four times the final size and scaled down: Pillow's
primitives have no antialiasing of their own, and a rounded corner straight out
of ``rounded_rectangle`` at 96px has steps you can count.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

from scripts.brand import geometry as g
from scripts.brand.outline_text import SUBSETS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "img" / "brand"
FONT_DIR = ROOT / "static" / "fonts"

# Core v43. The same pair gen_logo.py draws the vectors with: the mark's own
# colours, so the red here is the logo's exact #EA232C. An icon carries no
# small white text, so the ratio that rules that red out of a button label
# does not reach it.
INK = (42, 97, 174)  # the logo's blue
PINK = (234, 35, 44)  # the logo's red
SOFT = (253, 236, 237)  # --brand-red-light
FACE = (255, 255, 255)  # --surface
GROUND = (245, 246, 248)  # --surface-alt

SS = 4  # supersampling factor


# --- type ----------------------------------------------------------------


@dataclass
class Face:
    """One typeface at one size, spread over its subset files.

    The woff2 files are cut by unicode range, so no single one of them can set
    `OŚRODEK SZKOLENIA KIEROWCÓW`: the plain letters are in latin and Ś and Ó
    in latin-ext. Pillow has no fallback of its own, so each character is
    looked up in the file that actually carries it.
    """

    parts: list[tuple[set[int], ImageFont.FreeTypeFont]]

    def font_for(self, char: str) -> ImageFont.FreeTypeFont:
        for chars, font in self.parts:
            if ord(char) in chars:
                return font
        return self.parts[0][1]

    def width(self, text: str, tracking: float = 0.0) -> float:
        if not text:
            return 0.0
        total = sum(self.font_for(c).getlength(c) for c in text)
        return total + tracking * (len(text) - 1)


def load_face(slug: str, size: float, weight: float | None = None) -> Face:
    parts = []
    for subset in SUBSETS:
        path = FONT_DIR / f"{slug}-{subset}.woff2"
        if not path.exists():
            continue
        font = TTFont(path)
        if weight is not None and "fvar" in font:
            font = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
        chars = set(font.getBestCmap())
        buf = io.BytesIO()
        font.flavor = None
        font.save(buf)
        buf.seek(0)
        parts.append((chars, ImageFont.truetype(buf, int(round(size)))))
    if not parts:
        raise FileNotFoundError(f"no {slug}-*.woff2 in {FONT_DIR}")
    return Face(parts)


def draw_line(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    face: Face,
    fill: tuple[int, int, int],
    tracking: float = 0.0,
) -> None:
    """Set ``text`` with its baseline on ``xy``, one character at a time."""
    x, y = xy
    for char in text:
        font = face.font_for(char)
        draw.text((x, y), char, font=font, fill=fill, anchor="ls")
        x += font.getlength(char) + tracking


# --- shapes --------------------------------------------------------------


def plate(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, aspect: float) -> None:
    """The L plate: crimson frame, pale face, crimson letter."""
    h = w * aspect
    r = w * g.PLATE_RADIUS
    b = w * g.PLATE_BORDER
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=INK)
    draw.rounded_rectangle([x + b, y + b, x + w - b, y + h - b], radius=r - b, fill=FACE)
    lw, lh = w * g.L_WIDTH, w * g.L_HEIGHT
    lx, ly = x + (w - lw) / 2, y + (h - lh) / 2
    stem, foot = w * g.L_STEM, w * g.L_FOOT_H
    draw.polygon(
        [
            (lx, ly),
            (lx + stem, ly),
            (lx + stem, ly + lh - foot),
            (lx + lw, ly + lh - foot),
            (lx + lw, ly + lh),
            (lx, ly + lh),
        ],
        fill=INK,
    )


def wheel(
    draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, ground, colour=INK
) -> None:
    """The steering wheel, painted rather than cut.

    The svg is one path with the holes wound against it; here they are simply
    repainted in the ground colour, which comes out the same on a flat field
    and needs no winding rule. The cutout corners land square instead of
    rounded — the one difference between the two renderers, invisible below
    about 300px, and written down so nobody goes looking for a bug.
    """
    box = [cx - r, cy - r, cx + r, cy + r]
    INK = colour  # noqa: N806 — one name for the wheel's own ink, below
    draw.ellipse(box, fill=INK)
    # Pulled in by the corner radius the svg rounds its cutouts with, so the
    # spokes come out the same width in both renderers.
    inset = math.degrees(g.CUT_CORNER / (1 - g.RIM)) * 0.5
    for cut in g.cutouts():
        draw.pieslice(box, start=cut.start + inset, end=cut.end - inset, fill=ground)
    draw.ellipse(box, outline=INK, width=max(1, int(round(r * g.RIM))))
    for radius, colour in ((g.HUB_OUTER, INK), (g.HUB_INNER, ground)):
        rr = r * radius
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=colour)
    for dist, angle in g.holes():
        a = math.radians(angle)
        hx, hy = cx + r * dist * math.cos(a), cy + r * dist * math.sin(a)
        hr = r * g.HOLE_R
        draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=ground)


# --- the files -----------------------------------------------------------


def icon(size: int, *, ground: tuple[int, int, int] | None, share: float) -> Image.Image:
    """A square icon holding the plate at ``share`` of its width."""
    s = size * SS
    im = Image.new(
        "RGBA" if ground is None else "RGB", (s, s), (0, 0, 0, 0) if ground is None else ground
    )
    draw = ImageDraw.Draw(im)
    w = s * share
    plate(draw, (s - w) / 2, (s - w) / 2, w, aspect=1.0)
    return im.resize((size, size), Image.LANCZOS)


def social_card() -> Image.Image:
    """1200x630 for og:image: the ground, a couple of blooms, and the lockup."""
    w, h = 1200 * SS, 630 * SS
    im = Image.new("RGB", (w, h), GROUND)
    draw = ImageDraw.Draw(im, "RGBA")

    # The soft blooms of the owner's own light file, at the weight they sit
    # there: present, never competing with the lettering.
    for bx, by, br in ((0.06, 0.14, 0.21), (0.94, 0.82, 0.27), (0.82, 0.08, 0.12)):
        px, py, pr = bx * w, by * h, br * h
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(*SOFT, 105))

    r = 0.115 * h
    word = load_face("rubik-italic", 1.55 * r)
    sub = load_face("nunito", 0.30 * r, weight=800)
    slogan = load_face("caveat", 0.62 * r, weight=700)

    gap = 0.34 * r
    word_w = word.width("OSTRYCHARZ", tracking=-0.015 * 1.55 * r)
    sub_track = 0.16 * 0.30 * r
    sub_w = sub.width("OŚRODEK SZKOLENIA KIEROWCÓW", tracking=sub_track)
    text_w = max(word_w, sub_w)
    plate_w = 1.35 * r
    total = 2 * r + gap + text_w + gap + plate_w

    x0 = (w - total) / 2
    cy = 0.47 * h
    wheel(draw, x0 + r, cy, r, GROUND, PINK)

    x_text = x0 + 2 * r + gap
    # Red word, blue subline: the school's own mark, and the reason the og
    # card is not one flat slab of a single colour.
    draw_line(draw, (x_text, cy + 0.07 * r), "OSTRYCHARZ", word, PINK, -0.015 * 1.55 * r)
    draw_line(
        draw,
        (x_text + (text_w - sub_w) / 2, cy + 0.56 * r),
        "OŚRODEK SZKOLENIA KIEROWCÓW",
        sub,
        INK,
        sub_track,
    )
    draw_line(
        draw,
        (x_text + 0.34 * r, cy + 1.30 * r),
        "Twoja droga do niezależności",
        slogan,
        PINK,
    )
    plate(draw, x_text + text_w + gap, cy - 0.62 * r, plate_w, g.PLATE_ASPECT)
    return im.resize((1200, 630), Image.LANCZOS)


def save(im: Image.Image, name: str, **kwargs: object) -> None:
    path = OUT / name
    im.save(path, **kwargs)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KB")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    save(icon(96, ground=None, share=0.94), "favicon-96.png")
    save(icon(180, ground=GROUND, share=0.72), "apple-touch-icon-180.png")
    save(icon(192, ground=GROUND, share=0.74), "icon-192.png")
    save(icon(512, ground=GROUND, share=0.74), "icon-512.png")
    # Android crops a maskable icon to whatever shape the launcher likes, and
    # only the middle 80% is guaranteed to come through it.
    save(icon(512, ground=GROUND, share=0.52), "maskable-512.png")
    save(social_card(), "og-default.jpg", quality=86, optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
