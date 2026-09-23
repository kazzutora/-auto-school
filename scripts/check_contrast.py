"""Contrast gate for the design tokens, ROSE.md B.2 and B.3 as amended at v44.

B.3 prints a table of ratios and says outright that they are measured rather
than estimated. This is the measuring. Every pair the design actually puts on
screen lives here as data and the build fails when one of them drops below its
threshold. Body text needs 4.5:1 and large text 3:1, WCAG 2.2 1.4.3; a focus
indicator needs 3:1 against its surround, 1.4.11.

One pair is forbidden outright rather than held to a number: white on the pale
tint brand.200, which is 1.14. It is checked below the table, together with the
one literal that may not appear in the stylesheet at all — the logo's own red,
#EA232C, which measures 4.40 under white and is the reason --brand-red is four
percent darker than the mark it came from. The mark keeps that colour; the
stylesheet may not borrow it back.

The tokens are read out of static/src/css/app.css rather than repeated here.
A second copy of the palette is a copy that drifts, and the one thing this
script must never do is pass because it was checking last week's colours.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parent.parent / "static" / "src" / "css" / "app.css"

# Each entry: (theme, foreground token, background token, minimum, what it is).
# "large" pairs are the display and h1 steps, which clear 24px bold everywhere
# they are used, so 3:1 is the threshold WCAG gives them.
PAIRS: list[tuple[str, str, str, float, str]] = [
    # ---- light: the page and the cards ------------------------------
    ("light", "ink", "brand-100", 4.5, "body text on the page"),
    ("light", "ink", "brand-50", 4.5, "body text on a card"),
    ("light", "ink-500", "brand-100", 4.5, "secondary text on the page"),
    ("light", "ink-500", "brand-50", 4.5, "secondary text on a card"),
    ("light", "state-err", "brand-50", 4.5, "a field error on a card"),
    ("light", "state-ok", "brand-100", 4.5, "an open intake on the page"),
    # A state chip fills itself with a tenth of the ground's foreground, so the
    # pair that has to read is the colour against that wash, not against the
    # bare ground. Two of the three cleared the ground and failed the chip.
    ("light", "state-ok", "chip-on-page", 4.5, "an open intake, on its own chip"),
    ("light", "state-warn", "chip-on-page", 4.5, "a planned intake, on its own chip"),
    ("light", "state-err", "chip-on-page", 4.5, "a closed intake, on its own chip"),
    ("light", "state-warn", "brand-100", 4.5, "a warning on the page"),
    # ---- light: the red ---------------------------------------------
    # brand.500 is a fill and a heading, never small text: the text red is
    # brand.link, which is darker and clears 4.5 on both light grounds.
    ("light", "fixed-paper", "brand-500", 4.5, "button label on the red"),
    ("light", "fixed-paper", "brand-600", 4.5, "button label, hovered"),
    ("light", "brand-500", "brand-100", 3.0, "a heading, and the button as an object"),
    ("light", "brand-500", "brand-50", 3.0, "the same on a card"),
    ("light", "brand-link", "brand-100", 4.5, "links and small red text on the page"),
    ("light", "brand-link", "brand-50", 4.5, "the same on a card"),
    # ---- light: the graphite ----------------------------------------
    # The third colour, and the one that carries every heading and paragraph
    # on the site. All of it is small text — the outline button's label, the
    # icons beside the advantages — so it is held to 4.5 rather than to a
    # heading's 3.0.
    ("light", "brand-700", "brand-100", 4.5, "the graphite accent on the page"),
    ("light", "brand-700", "brand-50", 4.5, "the same on a card"),
    # ---- light: the tinted tile and the dark band -------------------
    ("light", "fixed-ink", "brand-200", 4.5, "text on a tinted tile"),
    ("light", "on-wine", "brand-900", 4.5, "text on the dark band"),
    ("light", "on-wine-muted", "brand-900", 4.5, "secondary text on the dark band"),
    ("light", "fixed-paper", "brand-900", 4.5, "white on the dark band"),
    # The band is a block rather than text, so 3.0: it has to separate from
    # the page it interrupts, and the red button standing on it has to
    # separate from the band. The second is what stops the dark theme's band
    # being lightened any further than it already is.
    ("light", "brand-900", "brand-100", 3.0, "the dark band against the page"),
    ("light", "brand-500", "brand-900", 3.0, "the button as an object, on the band"),
    # The footer is graphite too, and its quiet line is its own token: the
    # page's --muted measures 3.21 there and fails.
    ("light", "on-ink-muted", "brand-900", 4.5, "secondary text in the footer"),
    # ---- dark: the same rows, roles rearranged ----------------------
    ("dark", "ink", "brand-100", 4.5, "body text on the page"),
    ("dark", "ink", "brand-50", 4.5, "body text on a card"),
    ("dark", "ink-500", "brand-100", 4.5, "secondary text on the page"),
    ("dark", "ink-500", "brand-50", 4.5, "secondary text on a card"),
    ("dark", "state-err", "brand-50", 4.5, "a field error on a card"),
    ("dark", "state-ok", "brand-50", 4.5, "an open intake on a card"),
    ("dark", "state-warn", "brand-50", 4.5, "a warning on a card"),
    # The fills do not swap, so their labels do not either.
    ("dark", "fixed-paper", "brand-500", 4.5, "button label on the red"),
    ("dark", "fixed-paper", "brand-600", 4.5, "button label, hovered"),
    ("dark", "brand-500", "brand-100", 3.0, "the button as an object on the page"),
    ("dark", "brand-500", "brand-50", 3.0, "the same on a card"),
    ("dark", "brand-link", "brand-100", 4.5, "links and small red text on the page"),
    ("dark", "brand-link", "brand-50", 4.5, "the same on a card"),
    ("dark", "brand-700", "brand-100", 4.5, "the graphite accent on the page"),
    ("dark", "brand-700", "brand-50", 4.5, "the same on a card"),
    ("dark", "fixed-ink", "brand-200", 4.5, "text on a tinted tile"),
    ("dark", "on-wine", "brand-900", 4.5, "text on the dark band"),
    ("dark", "on-wine-muted", "brand-900", 4.5, "secondary text on the dark band"),
    ("dark", "brand-500", "brand-900", 3.0, "the button as an object, on the band"),
    # ---- the focus ring, 1.4.11: 3:1 against what surrounds it ------
    # The ring is --focus with a halo of the ground's own foreground under it,
    # so both edges are checked against the ground they sit on. Red on every
    # light ground since core v44, which took the blue out of the palette: on
    # a red band or a graphite one the ground overrides it with its own
    # foreground, because a red ring on red is a ring nobody can see.
    ("light", "brand-500", "brand-100", 3.0, "focus ring on the page"),
    ("light", "brand-500", "brand-50", 3.0, "focus ring on a card"),
    ("light", "ink", "brand-100", 3.0, "focus halo on the page"),
    ("light", "ink", "brand-50", 3.0, "focus halo on a card"),
    ("light", "fixed-paper", "brand-500", 3.0, "focus ring on a red fill"),
    ("light", "fixed-ink", "brand-200", 3.0, "focus ring on a tinted tile"),
    ("light", "on-wine", "brand-900", 3.0, "focus ring on the dark band"),
    ("dark", "brand-500", "brand-100", 3.0, "focus ring on the page"),
    ("dark", "brand-500", "brand-50", 3.0, "focus ring on a card"),
    ("dark", "ink", "brand-100", 3.0, "focus halo on the page"),
    ("dark", "ink", "brand-50", 3.0, "focus halo on a card"),
]

# B.3 refuses these outright. They are not thresholds to hold but colours that
# must not be put together at all, so the gate looks for the pairing rather
# than for a ratio.
FORBIDDEN: list[tuple[str, tuple[int, int, int], str]] = [
    ("white on brand.200", (255, 255, 255), "brand-200"),
]

# And the one colour that may not become a token: the logo's own red. White on
# it is 4.40 and the primary button carries a white label, so the fill is
# #E1141D instead. The artwork keeps #EA232C; this file keeps it out of the
# stylesheet, because "correcting" the token back to the mark's exact hex is
# the obvious thing for the next person to do.
FORBIDDEN_LITERALS = {"#ea232c": "the logo's own red, 4.40 under white — use --brand-red"}


def mix(fg: tuple[int, int, int], bg: tuple[int, int, int], alpha: float):
    return tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg, strict=True))


def read_tokens(text: str) -> dict[str, dict[str, tuple[int, int, int]]]:
    """The light and dark token tables, straight out of the stylesheet.

    Light comes from the bare :root block, dark from the explicit
    :root[data-theme="dark"] one. The media-query block is deliberately not
    read: B.2 requires every colour to exist in the light table first, so a
    token that only appears under prefers-color-scheme is a bug this script
    should report as a missing token rather than quietly use.
    """
    themes: dict[str, dict[str, tuple[int, int, int]]] = {"light": {}, "dark": {}}
    aliases: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    for theme, pattern in (
        ("light", r":root\s*\{(.*?)\n  \}"),
        ("dark", r':root\[data-theme=[\'"]dark[\'"]\]\s*\{(.*?)\n  \}'),
    ):
        for block in re.findall(pattern, text, re.S):
            for name, r, g, b in re.findall(
                r"--([a-z0-9-]+):\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s*;", block
            ):
                themes[theme].setdefault(name, (int(r), int(g), int(b)))
            # Since core v43 the table has two layers: the brand names each
            # colour once — --brand-red, --surface, --ink — and the role
            # vocabulary the templates were built on points at it with var().
            # Both are real tokens as far as the cascade is concerned, so both
            # have to be real here, or every pair naming a role reports as a
            # missing token.
            for name, target in re.findall(
                r"--([a-z0-9-]+):\s*var\(--([a-z0-9-]+)\)\s*;", block
            ):
                aliases[theme].setdefault(name, target)
    # The dark theme redefines only what changes role; everything else it
    # inherits from the light table, exactly as the cascade does it. Its own
    # literals are kept aside first, because they have to beat an alias the
    # light table declared for the same name: --brand-link is var(--brand-red-
    # dark) in the light theme and a literal pale red in the dark one, and
    # resolving the inherited alias over it would have put the light theme's
    # red back on the dark page at 1.55.
    dark_literals = set(themes["dark"])
    merged = dict(themes["light"])
    merged.update(themes["dark"])
    themes["dark"] = merged
    aliases["dark"] = {
        name: target
        for name, target in {**aliases["light"], **aliases["dark"]}.items()
        if name not in dark_literals
    }

    # Now resolve, per theme. Doing it after the merge rather than before is
    # what makes the dark theme work at all: it redefines --surface, and
    # --brand-50 points at --surface, so the card token has to be resolved
    # against the dark table even though the alias was written in the light
    # one.
    #
    # An alias may point at another alias — --fixed-ink is --brand-ink is a
    # literal — so it walks, and refuses to go round in a circle.
    for theme, table in themes.items():
        for name, first in aliases[theme].items():
            seen, target = {name}, first
            while target not in table and target in aliases[theme]:
                if target in seen:
                    raise SystemExit(f"--{name} resolves in a circle in the {theme} theme")
                seen.add(target)
                target = aliases[theme][target]
            if target in table:
                table[name] = table[target]
    # Not a token: the fill a state chip paints for itself, which is a tenth of
    # the ground's own foreground over the ground. app.css says the same in one
    # declaration, and the colours on it have to be checked against it rather
    # than against the bare page.
    for table in themes.values():
        table["chip-on-page"] = mix(table["ink"], table["brand-100"], 0.1)
        table["chip-on-card"] = mix(table["ink"], table["brand-50"], 0.1)
    return themes


def luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        c = value / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    a, b = luminance(fg), luminance(bg)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def main() -> int:
    themes = read_tokens(CSS.read_text(encoding="utf-8"))
    failures: list[str] = []
    for theme, fg, bg, minimum, what in PAIRS:
        table = themes[theme]
        missing = [name for name in (fg, bg) if name not in table]
        if missing:
            failures.append(f"{theme}: token(s) {', '.join(missing)} not defined ({what})")
            continue
        value = ratio(table[fg], table[bg])
        mark = "ok  " if value >= minimum else "FAIL"
        print(f"{mark} {theme:5} {fg:14} on {bg:14} {value:5.2f}:1  (min {minimum})  {what}")
        if value < minimum:
            failures.append(
                f"{theme}: --{fg} on --{bg} is {value:.2f}:1, below {minimum}:1 — {what}"
            )

    # Comments are stripped first: B.3's own reasoning names the colours it
    # forbids, and a gate that fails on its own documentation is a gate people
    # learn to skip.
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S).lower()
    for literal, why in FORBIDDEN_LITERALS.items():
        if literal in text:
            failures.append(f"{literal} is in the stylesheet — {why}")

    for (
        what,
        fg,
        bg,
    ) in ((name, rgb, token) for name, rgb, token in FORBIDDEN):
        for theme in ("light", "dark"):
            value = ratio(fg, themes[theme][bg])
            print(f"     {theme:5} {what:31} {value:5.2f}:1  forbidden outright")

    if failures:
        print("\ncontrast gate failed:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"\n{len(PAIRS)} pairs, all above threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
