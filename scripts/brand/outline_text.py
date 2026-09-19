"""Set a line of text and hand back svg path data, ROSE.md K1 step 2.

The logo must not depend on a webfont having loaded: a lockup that reflows when
Rubik arrives late is a lockup that is wrong for the first second of every cold
visit, and wrong forever in a mail client. So the lettering in
static/img/brand/*.svg is curves, cut here from the same woff2 files the site
serves.

    from scripts.brand.outline_text import set_line
    line = set_line("OSTRYCHARZ", face="rubik-italic", size=100, tracking=-0.015)
    line.path      # the d= attribute, baseline at y=0, y already flipped
    line.width     # advance width at that size
    line.cap       # cap height at that size, for vertical centring

Glyphs are looked up across the subset files of a face, because the polish
diacritics live in latin-ext while the plain letters live in latin. Both are
the same instance of the same variable font, so the outlines match.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "static" / "fonts"

# Ordered: the first file carrying a character wins. latin before latin-ext
# because it is the smaller lookup and covers most of what we set.
SUBSETS = ("latin", "latin-ext", "cyrillic", "cyrillic-ext")


@dataclass(frozen=True)
class Line:
    path: str
    width: float
    cap: float


@cache
def _faces(face: str, weight: float | None = None) -> tuple[TTFont, ...]:
    """The subset files of a face, pinned to ``weight`` if they are variable.

    Nunito and Caveat ship as one variable file per subset, and drawing from
    one straight off gives the default master — 400 — whatever the css asks
    for. Pinning the axis first is what makes the 800 in the subline actually
    800.
    """
    fonts = []
    for subset in SUBSETS:
        path = FONT_DIR / f"{face}-{subset}.woff2"
        if not path.exists():
            continue
        font = TTFont(path, fontNumber=0)
        if weight is not None and "fvar" in font:
            font = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
        fonts.append(font)
    if not fonts:
        raise FileNotFoundError(f"no {face}-*.woff2 in {FONT_DIR}")
    return tuple(fonts)


def _find(face: str, char: str, weight: float | None) -> tuple[TTFont, str]:
    for font in _faces(face, weight):
        name = font.getBestCmap().get(ord(char))
        if name:
            return font, name
    raise KeyError(f"{face} has no glyph for {char!r} (U+{ord(char):04X})")


def set_line(
    text: str,
    *,
    face: str = "rubik-italic",
    weight: float | None = None,
    size: float = 100.0,
    tracking: float = 0.0,
    x: float = 0.0,
    y: float = 0.0,
) -> Line:
    """Lay out ``text`` left to right with the baseline on ``y``.

    ``tracking`` is letter spacing as a fraction of ``size``, the way a
    designer says it: -0.015 is the -1.5% the wordmark is set at.
    """
    commands: list[str] = []
    pen_x = x
    upem = _faces(face, weight)[0]["head"].unitsPerEm
    scale = size / upem
    step = tracking * size

    for char in text:
        if char == " ":
            font, name = _find(face, " ", weight)
            pen_x += font["hmtx"][name][0] * scale + step
            continue
        font, name = _find(face, char, weight)
        glyphs = font.getGlyphSet()
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip(".") or "0")
        # y is flipped: font space grows upward, svg space downward.
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, pen_x, y)))
        drawn = pen.getCommands()
        if drawn:
            commands.append(drawn)
        pen_x += font["hmtx"][name][0] * scale + step

    font = _faces(face, weight)[0]
    cap = getattr(font.get("OS/2"), "sCapHeight", None) or font["head"].unitsPerEm * 0.7
    return Line(
        path=" ".join(commands),
        width=pen_x - x - (step if text else 0),
        cap=cap * scale,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Print svg path data for a line.")
    parser.add_argument("text")
    parser.add_argument("--face", default="rubik-italic")
    parser.add_argument("--weight", type=float, default=None)
    parser.add_argument("--size", type=float, default=100.0)
    parser.add_argument("--tracking", type=float, default=0.0)
    args = parser.parse_args()
    line = set_line(
        args.text,
        face=args.face,
        weight=args.weight,
        size=args.size,
        tracking=args.tracking,
    )
    print(f"<!-- width {line.width:.2f}, cap {line.cap:.2f} -->")
    print(f'<path d="{line.path}"/>')
