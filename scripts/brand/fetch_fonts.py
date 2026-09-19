"""Pull the three faces of ROSE.md B.4 from the css2 api and self host them.

tech.md section 2 bans third party font hosts on public pages, so the woff2
files live in static/fonts/ and the @font-face blocks in static/src/css/app.css
point at them. This script is the documented way to refresh them: ask the api
for the exact weight range with a modern user agent, keep the unicode-range
that came back beside the file, and write both out.

    python -m scripts.brand.fetch_fonts            download and report
    python -m scripts.brand.fetch_fonts --css      print the @font-face blocks

The api hands back one variable file per subset, already sliced to the range we
asked for. Slicing is what keeps them small, and asking for a range rather than
a list of weights means one file covers 400 through 800 instead of five.

Only four subsets are kept. latin-ext carries the polish diacritics
(ł ą ę ś ć ż ź ń), cyrillic and cyrillic-ext the russian and ukrainian versions
of the site. Greek, hebrew, arabic and vietnamese are dropped: nothing on this
site is written in them.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from fontTools import subset as ft_subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "static" / "fonts"

# A modern agent, or the api answers with ttf.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Declaration order matters and is not ours to choose. Where two subsets claim
# the same character — cyrillic-ext's U+0460-052F swallows cyrillic's
# U+0490-0491, which is the ukrainian ґ — the face declared *last* wins, and
# only one of the two files actually carries the glyph. Google emits them
# rarest first for exactly this reason, so we keep their order and the common
# subset wins every overlap. Reordering this list to read more tidily drops ґ
# into the system sans on every ukrainian page; scripts/check_fonts.py is what
# caught it, and what will catch it again.
KEEP_SUBSETS = ("cyrillic-ext", "cyrillic", "latin-ext", "latin")


# What the handwriting has to be able to write, and nothing else.
#
# Caveat arrives from the api at 102 KB for the two subsets a polish page
# pulls, which is half the font weight of the first screen for a face that sets
# eight short phrases. It can be cut because unlike the other two it never sets
# anything from the database: every string in it is a fixed, translated phrase
# — `Z nami zdasz`, `O nas`, `Nasze kursy`, the slogan under the print.
#
# The set below is deliberately wider than those phrases: all of ascii, the
# polish diacritics and both cyrillic alphabets, so new copy in any of the
# three languages sets correctly without anybody remembering this file exists.
# scripts/check_fonts.py is the gate either way — it opens these files and
# fails the build on a missing glyph.
KEEP_CHARS = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
    + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    + "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    + "ґєіїҐЄІЇ"
    + "—–„”“‘’…·♡«»§№°"
)

# Only the handwriting is cut, and the value is the weight its axis is pinned
# to. Rubik sets headings out of the database and Nunito sets every paragraph
# on the site, so both keep their full subsets and their axes: a course title
# the owner types tomorrow has to render, at whatever weight it lands on.
#
# Caveat is set at 700 everywhere it appears — the .script class in app.css and
# nothing else — so the axis is worth more as bytes than as a range.
SUBSET_FACES = {"caveat": 700.0}


@dataclass(frozen=True)
class Face:
    """One family as ROSE.md B.4 asks for it."""

    slug: str
    family: str
    query: str
    style: str
    weight: str
    role: str


FACES = (
    Face(
        slug="rubik-italic",
        family="Rubik",
        query="Rubik:ital,wght@1,800",
        style="italic",
        weight="800",
        role="display: h1, h2, PRAWO JAZDY, the numerals, the wordmark",
    ),
    Face(
        slug="nunito",
        family="Nunito",
        query="Nunito:wght@400..800",
        style="normal",
        weight="400 800",
        role="text: paragraphs, buttons, fields, menu, h3, prices",
    ),
    Face(
        slug="caveat",
        family="Caveat",
        query="Caveat:wght@600..700",
        style="normal",
        weight="600 700",
        role="handwriting: margin notes, eyebrows, photo captions, the slogan",
    ),
)

BLOCK = re.compile(
    r"/\*\s*(?P<subset>[a-z\-]+)\s*\*/\s*@font-face\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE,
)
SRC = re.compile(r"src:\s*url\((?P<url>[^)]+)\)")
RANGE = re.compile(r"unicode-range:\s*(?P<range>[^;]+);")


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return bytes(response.read())


def cut(payload: bytes, weight: float | None = None) -> bytes:
    """Keep only KEEP_CHARS, and only the glyphs that draw them.

    ``weight`` pins the variable axis and throws the variation tables away
    with it. That is most of the saving on Caveat: a variable font carries a
    delta per point per axis, and this site sets the handwriting at one weight.
    """
    font = TTFont(io.BytesIO(payload))
    if weight is not None and "fvar" in font:
        font = instantiateVariableFont(font, {"wght": weight}, updateFontNames=False)
    options = ft_subset.Options()
    options.flavor = "woff2"
    # Ligatures, kerning and mark placement. Not calt.
    #
    # Caveat's contextual alternates are a second shape for most letters, so a
    # repeated `a` is drawn differently the second time. They are also 104
    # extra glyphs and 21 KB — half the file — on every first visit, for eight
    # short phrases whose repeated letters you have to look for. The letterforms
    # are what make it handwriting; calt only varies them.
    options.layout_features = ["ccmp", "locl", "kern", "liga", "clig", "mark", "mkmk"]
    options.retain_gids = False
    options.drop_tables += ["DSIG"]
    subsetter = ft_subset.Subsetter(options=options)
    subsetter.populate(text=KEEP_CHARS)
    subsetter.subset(font)
    out = io.BytesIO()
    font.flavor = "woff2"
    font.save(out)
    return out.getvalue()


def collect(face: Face) -> list[tuple[str, str, str]]:
    """Return (subset, source url, unicode-range) for the subsets we keep."""
    css = get(f"https://fonts.googleapis.com/css2?family={face.query}&display=swap")
    found = []
    for match in BLOCK.finditer(css.decode("utf-8")):
        subset = match["subset"]
        if subset not in KEEP_SUBSETS:
            continue
        body = match["body"]
        src, rng = SRC.search(body), RANGE.search(body)
        if not src or not rng:
            raise SystemExit(f"{face.family}/{subset}: no src or unicode-range")
        found.append((subset, src["url"], " ".join(rng["range"].split())))
    missing = set(KEEP_SUBSETS) - {s for s, _, _ in found}
    if missing:
        raise SystemExit(f"{face.family}: api returned no {sorted(missing)}")
    return sorted(found, key=lambda item: KEEP_SUBSETS.index(item[0]))


def font_face(face: Face, subset: str, unicode_range: str) -> str:
    return (
        "@font-face {\n"
        f"  font-family: '{face.family}';\n"
        f"  font-style: {face.style};\n"
        f"  font-weight: {face.weight};\n"
        "  font-display: swap;\n"
        f"  src: url(../fonts/{face.slug}-{subset}.woff2) format('woff2');\n"
        f"  unicode-range: {unicode_range};\n"
        "}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--css",
        action="store_true",
        help="print the @font-face blocks instead of downloading",
    )
    args = parser.parse_args()

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    blocks, total = [], 0
    for face in FACES:
        blocks.append(f"/* {face.family} — {face.role}. */")
        for subset, url, unicode_range in collect(face):
            blocks.append(font_face(face, subset, unicode_range))
            if args.css:
                continue
            target = FONT_DIR / f"{face.slug}-{subset}.woff2"
            payload = get(url)
            before = len(payload)
            if face.slug in SUBSET_FACES:
                payload = cut(payload, weight=SUBSET_FACES[face.slug])
            target.write_bytes(payload)
            total += len(payload)
            saved = (
                f"  (was {before / 1024:.1f})" if len(payload) != before else ""
            )
            print(f"{target.relative_to(ROOT)}  {len(payload) / 1024:.1f} KB{saved}")
    if args.css:
        print("\n\n".join(blocks))
    else:
        print(f"\n{total / 1024:.1f} KB in {len(FACES)} families")
    return 0


if __name__ == "__main__":
    sys.exit(main())
