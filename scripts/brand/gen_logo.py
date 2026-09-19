"""Build the logo kit from the owner's raster, ROSE.md K1.

    python -m scripts.brand.gen_logo

Writes static/img/brand/: the lockups, the two marks, the favicon and the app
icons. Nothing here is traced. The wheel, the plate and the cap are geometry
from scripts/brand/geometry.py, measured off the owner's file; the lettering is
cut from the same woff2 the site serves, so no svg carries a <text> element and
none of them waits on a webfont to be right.

The wordmark is set in Rubik 800 italic, ROSE.md B.4. The owner's file uses a
condensed brush face, so our word runs wider than theirs at the same cap
height. That is the one deliberate difference, and it is the trade ROSE.md
already made: Rubik carries cyrillic and the site is in three languages, so a
lockup a few percent wider beats one that cannot spell the russian page.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.brand import geometry as g
from scripts.brand.outline_text import set_line
from scripts.brand.svgpath import annular_sector, circle, num, polygon, rounded_rect

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "img" / "brand"

# ROSE.md B.2. brand.700 is the crimson of the owner's logo, brand.500 the
# lighter pink of the cap and the handwriting.
INK = "#A14052"  # brand.700
PINK = "#D4385E"  # brand.500
SOFT = "#F2B8C6"  # brand.200
FACE = "#FFFBFA"  # brand.50

# The wheel radius, and the unit everything else is stated in. Ten times the
# size the mark is ever painted at, so the path data can be whole numbers: the
# lettering is thousands of coordinates and a decimal point on each of them is
# a third of the file.
R = 430.0

WORD = "OSTRYCHARZ"
SUBLINE = "OŚRODEK SZKOLENIA KIEROWCÓW"
SLOGAN = "Twoja droga do niezależności"

TITLE = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"


# --- the wheel -----------------------------------------------------------


def wheel_path(cx: float, cy: float, r: float) -> str:
    """One path, nonzero fill: a disc with the rim, spokes and holes cut out."""
    parts = [circle(cx, cy, r)]
    for cut in g.cutouts():
        parts.append(
            annular_sector(
                cx,
                cy,
                r_out=r * (1 - g.RIM),
                r_in=r * g.HUB_OUTER,
                start=cut.start,
                end=cut.end,
                corner=r * g.CUT_CORNER,
            )
        )
    parts.append(circle(cx, cy, r * g.HUB_INNER, hole=True))
    for dist, angle in g.holes():
        hx, hy = g.polar(cx, cy, r * dist, angle)
        parts.append(circle(hx, hy, r * g.HOLE_R, hole=True))
    return "".join(parts)


# --- the L plate and the graduation cap ----------------------------------


def plate_paths(
    x: float, y: float, w: float, *, face: str = FACE, aspect: float | None = None
) -> list[str]:
    """Frame, face and letter, in painting order.

    ``aspect`` overrides the proportion for the favicon, which is square: a
    plate at the owner's 1.28 leaves a 16px icon twelve pixels wide, and the
    letter in it stops reading before the browser has finished scaling it.
    """
    h = w * (g.PLATE_ASPECT if aspect is None else aspect)
    r = w * g.PLATE_RADIUS
    b = w * g.PLATE_BORDER
    lw, lh = w * g.L_WIDTH, w * g.L_HEIGHT
    lx = x + (w - lw) / 2
    ly = y + (h - lh) / 2
    stem, foot_h = w * g.L_STEM, w * g.L_FOOT_H
    letter = polygon(
        [
            (lx, ly),
            (lx + stem, ly),
            (lx + stem, ly + lh - foot_h),
            (lx + lw, ly + lh - foot_h),
            (lx + lw, ly + lh),
            (lx, ly + lh),
        ]
    )
    inner = rounded_rect(x + b, y + b, w - 2 * b, h - 2 * b, r - b)
    return [
        '<path fill="' + INK + '" d="' + rounded_rect(x, y, w, h, r) + '"/>',
        '<path fill="' + face + '" d="' + inner + '"/>',
        '<path fill="' + INK + '" d="' + letter + '"/>',
    ]


def cap_paths(x: float, y: float, w: float) -> list[str]:
    """The academic cap that sits on the plate: crown, board, button, tassel."""

    def at(px: float, py: float) -> tuple[float, float]:
        return x + px * w, y + py * w

    crown_x, crown_y, crown_w, crown_h = g.CAP_CROWN
    crown = rounded_rect(*at(crown_x, crown_y), crown_w * w, crown_h * w, 0.10 * w)
    board = polygon([at(px, py) for px, py in g.CAP_BOARD])
    bx, by, br = g.CAP_BUTTON
    button_x, button_y = at(bx, by)
    start = at(*g.CAP_TASSEL_CORD[0])
    bend = at(*g.CAP_TASSEL_CORD[1])
    end = at(*g.CAP_TASSEL_CORD[2])
    tx, ty, tw, th = g.CAP_TASSEL
    tassel_x, tassel_y = at(tx - tw / 2, ty)
    cord = (
        "M"
        + num(start[0])
        + ","
        + num(start[1])
        + "Q"
        + num(bend[0])
        + ","
        + num(bend[1])
        + " "
        + num(end[0])
        + ","
        + num(end[1])
    )
    return [
        '<path fill="' + INK + '" d="' + crown + '"/>',
        '<path fill="' + PINK + '" d="' + board + '"/>',
        '<path fill="' + SOFT + '" d="' + circle(button_x, button_y, br * w) + '"/>',
        '<path fill="none" stroke="'
        + PINK
        + '" stroke-width="'
        + num(0.045 * w)
        + '" stroke-linecap="round" d="'
        + cord
        + '"/>',
        '<path fill="'
        + PINK
        + '" d="'
        + rounded_rect(tassel_x, tassel_y, tw * w, th * w, tw * w / 2)
        + '"/>',
    ]


def heart_path(cx: float, cy: float, w: float) -> str:
    """A small filled heart. One of the three the owner drew on the logo."""
    return (
        "M"
        + num(cx)
        + ","
        + num(cy + 0.32 * w)
        + "C"
        + num(cx - 0.52 * w)
        + ","
        + num(cy - 0.06 * w)
        + " "
        + num(cx - 0.50 * w)
        + ","
        + num(cy - 0.46 * w)
        + " "
        + num(cx - 0.18 * w)
        + ","
        + num(cy - 0.42 * w)
        + "C"
        + num(cx - 0.05 * w)
        + ","
        + num(cy - 0.40 * w)
        + " "
        + num(cx - 0.01 * w)
        + ","
        + num(cy - 0.30 * w)
        + " "
        + num(cx)
        + ","
        + num(cy - 0.23 * w)
        + "C"
        + num(cx + 0.01 * w)
        + ","
        + num(cy - 0.30 * w)
        + " "
        + num(cx + 0.05 * w)
        + ","
        + num(cy - 0.40 * w)
        + " "
        + num(cx + 0.18 * w)
        + ","
        + num(cy - 0.42 * w)
        + "C"
        + num(cx + 0.50 * w)
        + ","
        + num(cy - 0.46 * w)
        + " "
        + num(cx + 0.52 * w)
        + ","
        + num(cy - 0.06 * w)
        + " "
        + num(cx)
        + ","
        + num(cy + 0.32 * w)
        + "Z"
    )


# --- assembly ------------------------------------------------------------


def svg(width: float, height: float, body: str, *, title: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '
        + num(width)
        + " "
        + num(height)
        + '" width="'
        + num(width)
        + '" height="'
        + num(height)
        + '" role="img" aria-label="'
        + title
        + '">'
        + "<title>"
        + title
        + "</title>"
        + body
        + "</svg>\n"
    )


def lockup(*, slogan: bool, cap: bool, dark: bool) -> str:
    ink = FACE if dark else INK
    soft = SOFT if dark else INK
    pad = 80.0
    gap = 0.34 * R

    word_size = 0.767 * R / 0.70
    sub_size = 0.215 * R / 0.71
    word = set_line(WORD, face="rubik-italic", size=word_size, tracking=-0.015)
    sub = set_line(SUBLINE, face="nunito", weight=800, size=sub_size, tracking=0.16)

    text_w = max(word.width, sub.width)
    plate_w = 1.35 * R
    body_top = pad + (0.38 * plate_w if cap else 0.0)
    cy = body_top + R

    x_text = pad + 2 * R + gap
    x_plate = x_text + text_w + gap
    width = x_plate + plate_w * (1.26 if cap else 1.0) + pad
    bottom = cy + R + (0.34 * R if slogan else 0.0)
    height = bottom + pad

    parts = ['<path fill="' + ink + '" d="' + wheel_path(pad + R, cy, R) + '"/>']

    word_line = set_line(
        WORD,
        face="rubik-italic",
        size=word_size,
        tracking=-0.015,
        x=x_text,
        y=cy + 0.07 * R,
    )
    parts.append('<path fill="' + ink + '" d="' + word_line.path + '"/>')

    sub_y = cy + 0.56 * R
    sub_x = x_text + (text_w - sub.width) / 2
    sub_line = set_line(
        SUBLINE,
        face="nunito",
        weight=800,
        size=sub_size,
        tracking=0.16,
        x=sub_x,
        y=sub_y,
    )
    parts.append('<path fill="' + soft + '" d="' + sub_line.path + '"/>')

    rule = 0.20 * R
    rule_y = sub_y - 0.075 * R
    rules = (
        "M"
        + num(sub_x - rule - 0.22 * R)
        + ","
        + num(rule_y)
        + "h"
        + num(rule)
        + "M"
        + num(sub_x + sub.width + 0.22 * R)
        + ","
        + num(rule_y)
        + "h"
        + num(rule)
    )
    parts.append(
        '<path stroke="'
        + soft
        + '" stroke-width="'
        + num(0.032 * R)
        + '" stroke-linecap="round" d="'
        + rules
        + '"/>'
    )

    if slogan:
        slog_x = x_text + 0.34 * R
        slog_y = cy + 1.24 * R
        slog = set_line(SLOGAN, face="caveat", weight=700, size=0.62 * R, x=slog_x, y=slog_y)
        parts.append('<path fill="' + PINK + '" d="' + slog.path + '"/>')
        parts.append(
            '<path fill="'
            + PINK
            + '" d="'
            + heart_path(x_text + 0.13 * R, slog_y - 0.13 * R, 0.24 * R)
            + '"/>'
        )
        swash_x = slog_x + slog.width * 0.52
        swash_w = slog.width * 0.48
        parts.append(
            '<path fill="none" stroke="'
            + PINK
            + '" stroke-width="'
            + num(0.035 * R)
            + '" stroke-linecap="round" d="M'
            + num(swash_x)
            + ","
            + num(slog_y + 0.17 * R)
            + "q"
            + num(swash_w / 2)
            + ","
            + num(0.09 * R)
            + " "
            + num(swash_w)
            + ",0"
            + '"/>'
        )

    plate_y = cy - 0.62 * R
    parts.extend(plate_paths(x_plate, plate_y, plate_w))
    if cap:
        parts.extend(cap_paths(x_plate, plate_y, plate_w))

    return svg(width, height, "".join(parts), title=TITLE)


def write(name: str, content: str) -> None:
    path = OUT / name
    path.write_text(content, encoding="utf-8")
    print(f"{path.relative_to(ROOT)}  {len(content.encode()) / 1024:.1f} KB")


def symbol_file(name: str, symbol_id: str, content: str) -> None:
    """The lockup as a <symbol>, for the pages to reference with <use>.

    Three arrangements were tried and this is the only one right on every
    count.

    Two <img>, one hidden per theme, is two requests for one picture and the
    browser fetches both — 138 KB of logo on every page, against the 400 KB the
    whole first screen gets in REDESIGN.md C.6.

    One inlined copy fixes the theme, because currentColor reaches it, and
    costs no request. But the header and the footer both carry the lockup, so
    the page then carries it twice: 33 KB of html on every page of the site,
    uncached.

    A <symbol> referenced twice is one cacheable file, one request for the
    whole site, and `color` still crosses into the shadow tree that <use>
    builds — static/icons/sprite.svg has relied on that since the first core.

    The crimson of the cap stays a literal. It is a fill rather than a role and
    does not swap with the theme, B.2.
    """
    body = content.replace(f'fill="{INK}"', 'fill="currentColor"')
    body = body.replace(f'stroke="{INK}"', 'stroke="currentColor"')
    box = re.search(r'viewBox="([^"]+)"', body)
    assert box, "no viewBox on the lockup"
    inner = body[body.index(">") + 1 : body.rindex("</svg>")]
    # The <title> goes: the page names the lockup with aria-label on the <svg>
    # that references it, and two names on one image is one name read twice.
    inner = inner[inner.index("</title>") + len("</title>") :]
    write(
        name,
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        f'<symbol id="{symbol_id}" viewBox="{box[1]}">{inner}</symbol></svg>\n',
    )



def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    full = lockup(slogan=True, cap=True, dark=False)
    compact = lockup(slogan=False, cap=False, dark=False)
    write("logo-full.svg", full)
    write("logo-full-dark.svg", lockup(slogan=True, cap=True, dark=True))
    write("logo-compact.svg", compact)
    write("logo-compact-dark.svg", lockup(slogan=False, cap=False, dark=True))

    # What the pages actually use. The files above stay for the places that
    # need a picture rather than a reference — an email, a press kit.
    symbol_file("lockup-compact.svg", "lockup-compact", compact)

    size = 2 * R + 60
    wheel = '<path fill="' + INK + '" d="' + wheel_path(size / 2, size / 2, R) + '"/>'
    write("mark-wheel.svg", svg(size, size, wheel, title="OSK Ostrycharz"))

    w = 600.0
    mark = plate_paths(100, 0.60 * w, w) + cap_paths(100, 0.60 * w, w)
    write("mark-l.svg", svg(w * 1.42, w * 1.94, "".join(mark), title="Tabliczka L"))

    # The cap is dropped from the favicon: at 16px it is three pixels of noise
    # on top of the only shape that still reads, ROSE.md K1 step 4.
    fav = 640.0
    plate = plate_paths(30, 30, fav - 60, aspect=1.0)
    write("favicon.svg", svg(fav, fav, "".join(plate), title="L"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
