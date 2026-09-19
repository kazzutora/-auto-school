"""Font coverage gate, ROSE.md B.4 and K2 step 4.

The site is in three languages and every face on it has to be able to set all
three. B.4 says so and says the check is a script rather than an eye, for a
good reason: a missing glyph does not look broken, it looks like a slightly
different font, and nobody notices until a Polish name on the pricing page is
set in Arial next to a heading that is not.

That is not hypothetical here. Core v25 changed the text face because Public
Sans ships no cyrillic and every paragraph on /ru/ and /uk/ fell back to the
system sans; the display face kept the same fault until core v29 replaced it
with Rubik. This is what stops it coming back a third time.

Each @font-face in static/src/css/app.css names a file and a unicode-range, and
the browser picks per character: of the faces whose range claims it, the one
declared *last* wins. So that is the face this asks, and asking any other would
either miss a fault or invent one — the latin file is not expected to carry Ж.

The rule is not academic. cyrillic-ext claims U+0460-052F, which swallows the
ukrainian ґ at U+0490, and only the cyrillic file actually carries it. Put
cyrillic-ext last and every ukrainian page loses that letter to the system
sans, while every file on its own still looks complete.

    python scripts/check_fonts.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "static" / "src" / "css" / "app.css"
# The url()s are relative to where the stylesheet is served from, not to where
# it is written: `make css` builds static/src/css/app.css into static/css/,
# so ../fonts/ resolves next to it rather than under src/.
BUILT = ROOT / "static" / "css"

# What the three languages actually need beyond ascii, ROSE.md B.4.
POLISH = "ąćęłńóśźż" "ĄĆĘŁŃÓŚŹŻ"
RUSSIAN = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
UKRAINIAN = "ґєії"
REQUIRED = POLISH + RUSSIAN + RUSSIAN.upper() + UKRAINIAN + UKRAINIAN.upper()

FACE = re.compile(r"@font-face\s*\{(?P<body>[^}]*)\}", re.S)
FIELD = {
    name: re.compile(rf"{name}:\s*([^;]+);")
    for name in ("font-family", "font-style", "font-weight", "src", "unicode-range")
}


def parse_ranges(text: str) -> list[tuple[int, int]]:
    """U+0100-02BA, U+0131, U+1EF2-1EFF -> [(0x100, 0x2BA), (0x131, 0x131), ...]"""
    spans = []
    for part in text.split(","):
        part = part.strip().removeprefix("U+").removeprefix("u+")
        if not part:
            continue
        low, _, high = part.partition("-")
        spans.append((int(low, 16), int(high or low, 16)))
    return spans


def in_ranges(code: int, spans: list[tuple[int, int]]) -> bool:
    return any(low <= code <= high for low, high in spans)


def main() -> int:
    css = CSS.read_text(encoding="utf-8")
    faces = list(FACE.finditer(css))
    if not faces:
        print(f"no @font-face in {CSS.relative_to(ROOT)}", file=sys.stderr)
        return 1

    failures: list[str] = []
    # In declaration order, so a later face overrides an earlier one.
    loaded: list[tuple[str, str, list[tuple[int, int]], set[int]]] = []

    for match in faces:
        body = match["body"]
        fields = {}
        for name, pattern in FIELD.items():
            found = pattern.search(body)
            if not found:
                failures.append(f"@font-face without {name}: {body.strip()[:60]}")
                break
            fields[name] = found[1].strip()
        else:
            family = fields["font-family"].strip("'\"")
            url = re.search(r"url\(([^)]+)\)", fields["src"])
            if not url:
                failures.append(f"{family}: src has no url()")
                continue
            path = (BUILT / url[1].strip("'\"")).resolve()
            if not path.exists():
                failures.append(f"{family}: {url[1]} is not in the repository")
                continue
            loaded.append(
                (
                    family,
                    path.name,
                    parse_ranges(fields["unicode-range"]),
                    set(TTFont(path).getBestCmap()),
                )
            )

    families = sorted({family for family, _, _, _ in loaded})
    for family in families:
        subsets = [entry for entry in loaded if entry[0] == family]
        missing: dict[str, list[str]] = {}
        unclaimed: list[str] = []
        for char in REQUIRED:
            serving = [s for s in subsets if in_ranges(ord(char), s[2])]
            if not serving:
                unclaimed.append(char)
                continue
            # Last declaration wins, exactly as the browser resolves it.
            _, name, _, cmap = serving[-1]
            if ord(char) not in cmap:
                missing.setdefault(name, []).append(char)

        if unclaimed:
            failures.append(
                f"{family}: no subset claims {''.join(unclaimed[:12])}"
                f"{'…' if len(unclaimed) > 12 else ''} — a subset is not linked"
            )
        for name, chars in missing.items():
            failures.append(
                f"{family}: {name} is the last face claiming {''.join(chars)}, "
                f"and has none of them — check the order of the @font-face blocks"
            )
        count = len(REQUIRED) - len(unclaimed) - sum(len(c) for c in missing.values())
        mark = "ok  " if count == len(REQUIRED) else "FAIL"
        print(
            f"{mark} {family:10} {count:3}/{len(REQUIRED)} of pl, ru and uk"
            f"   ({len(subsets)} subsets: {', '.join(s[1] for s in subsets)})"
        )

    if failures:
        print("\nfont gate failed:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"\n{len(faces)} faces, {len(families)} families, all three languages covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
