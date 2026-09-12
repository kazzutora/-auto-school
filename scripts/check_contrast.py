"""Contrast gate for the design tokens, REDESIGN.md B.2 and R9 point 2.

B.2 says the contrast is checked and not estimated, so the pairs that the design
actually puts on screen live here as data and the build fails when one of them
drops below its threshold. Body text needs 4.5:1 and large text 3:1, WCAG 2.2
1.4.3; a focus indicator needs 3:1 against its surround, 1.4.11.

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
    # ---- light: the page itself -------------------------------------
    ("light", "ink", "paper", 4.5, "body text on the page"),
    ("light", "ink", "surface", 4.5, "body text on a white card"),
    ("light", "ink-700", "surface", 4.5, "secondary text on a white card"),
    ("light", "ink-700", "paper", 4.5, "secondary text on the page"),
    ("light", "ink-500", "surface", 4.5, "muted text on a white card"),
    ("light", "ink-500", "paper", 4.5, "muted text on the page"),
    ("light", "ink", "surface-muted", 4.5, "body text on the muted card"),
    ("light", "ink-500", "surface-muted", 4.5, "muted text on the muted card"),
    ("light", "state-err", "surface", 4.5, "a field error on a white card"),
    # ---- light: the two accents -------------------------------------
    # The blue is a fill with a white label on it, never a text colour: B.1
    # gives it the action role, and .u-prose deliberately does not use it for
    # links. So it is checked as a label pair and as an object, not as text.
    ("light", "fixed-paper", "primary", 4.5, "button label on blue"),
    ("light", "fixed-paper", "primary-600", 4.5, "button label on blue, hovered"),
    ("light", "primary", "paper", 3.0, "the blue button read as an object on the page"),
    ("light", "primary", "surface", 3.0, "the blue button read as an object on a card"),
    ("light", "fixed-ink", "accent", 4.5, "badge label on yellow"),
    # The pale yellow, core v27: the current page in the mobile menu, and the
    # accent callout's wash. The wash is the tint at 50% over the ground, so in
    # this theme the page is its darker end and ink-500 on paper covers it.
    ("light", "ink", "accent-100", 4.5, "the current page in the mobile menu"),
    ("light", "ink-500", "accent-100", 4.5, "muted text in the accent callout"),
    # ---- light: the dark card ---------------------------------------
    ("light", "on-dark", "ink", 4.5, "body text on the dark card"),
    ("light", "on-dark-muted", "ink", 4.5, "secondary text on the dark card"),
    ("light", "surface", "ink", 4.5, "white text on the dark card"),
    # ---- dark theme: the same rows, swapped roles -------------------
    ("dark", "ink", "paper", 4.5, "body text on the page"),
    ("dark", "ink", "surface", 4.5, "body text on a card"),
    ("dark", "ink-700", "surface", 4.5, "secondary text on a card"),
    ("dark", "ink-500", "surface", 4.5, "muted text on a card"),
    ("dark", "ink-500", "paper", 4.5, "muted text on the page"),
    ("dark", "ink", "surface-muted", 4.5, "body text on the muted card"),
    ("dark", "state-err", "surface", 4.5, "a field error on a card"),
    ("dark", "fixed-paper", "primary", 4.5, "button label on blue"),
    ("dark", "fixed-paper", "primary-600", 4.5, "button label on blue, hovered"),
    ("dark", "primary", "paper", 3.0, "the blue button read as an object on the page"),
    ("dark", "primary", "surface", 3.0, "the blue button read as an object on a card"),
    ("dark", "fixed-ink", "accent", 4.5, "badge label on yellow"),
    # The pale yellow's dark counterpart. Here the text is light, so the tint at
    # full strength is the lighter end of the callout's 50% wash: if muted text
    # reads on it, it reads on the wash.
    ("dark", "ink", "accent-100", 4.5, "the current page in the mobile menu"),
    ("dark", "ink-500", "accent-100", 4.5, "muted text in the accent callout"),
    ("dark", "on-dark", "ink", 4.5, "body text on the dark card"),
    ("dark", "on-dark-muted", "ink", 4.5, "secondary text on the dark card"),
    # ---- the focus ring, 1.4.11: 3:1 against what surrounds it ------
    # The ring is the yellow with a halo of the ground's own foreground under
    # it, so the pair that has to read is the halo against the ground. The
    # yellow on its own is 1.6:1 on a white card and was never enough alone.
    ("light", "ink", "paper", 3.0, "focus halo on the page"),
    ("light", "ink", "surface", 3.0, "focus halo on a white card"),
    ("light", "on-dark", "ink", 3.0, "focus halo on the dark card"),
    ("dark", "ink", "paper", 3.0, "focus halo on the page"),
    ("dark", "ink", "surface", 3.0, "focus halo on a card"),
]


def read_tokens(text: str) -> dict[str, dict[str, tuple[int, int, int]]]:
    """The light and dark token tables, straight out of the stylesheet.

    Light comes from the bare :root block, dark from the explicit
    :root[data-theme="dark"] one. The media-query block is deliberately not
    read: B.2 and R9 point 1 both require every colour to exist in the light
    table first, so a token that only appears under prefers-color-scheme is a
    bug this script should report as a missing token rather than silently use.
    """
    themes: dict[str, dict[str, tuple[int, int, int]]] = {"light": {}, "dark": {}}
    for theme, pattern in (
        ("light", r":root\s*\{(.*?)\n  \}"),
        ("dark", r':root\[data-theme=[\'"]dark[\'"]\]\s*\{(.*?)\n  \}'),
    ):
        for block in re.findall(pattern, text, re.S):
            for name, r, g, b in re.findall(
                r"--([a-z0-9-]+):\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s*;", block
            ):
                themes[theme].setdefault(name, (int(r), int(g), int(b)))
    # The dark theme redefines only what changes role; everything else it
    # inherits from the light table, exactly as the cascade does it.
    merged = dict(themes["light"])
    merged.update(themes["dark"])
    themes["dark"] = merged
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

    if failures:
        print("\ncontrast gate failed:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"\n{len(PAIRS)} pairs, all above threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
