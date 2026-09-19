"""Generate the handwritten ornament, ROSE.md B.6.

    python -m scripts.brand.gen_ornaments

Writes static/img/ornament/: four brush strokes, three hearts, a scribbled
underline, a curly arrow, a spark burst, a hand-drawn circle and a soft blob.
Everything is a static svg, generated once and committed. Nothing is drawn in
the browser: B.6 bans feTurbulence and the rest of the filter primitives
outright, because a page carrying a dozen of them drops frames on a phone the
moment it scrolls.

The seed is fixed, so a second run writes the same bytes and `git diff` stays
empty. That is the point of committing generated art: the strokes are stable
enough to review, and re-running the script is not a redesign.

**Why these are strokes and not ovals.** A rounded rectangle at an angle reads
as a shape; a brush reads as a gesture. The difference is in three things and
this file does all three: the width varies along the stroke rather than being
constant, both edges carry low-frequency noise so they are never parallel, and
the body is broken by dry streaks where the bristles ran out of paint.

The noise is a sum of three sines with fixed phases — smooth, periodic and
repeatable, which random() per point is not: per-point randomness gives a
sawtooth edge that reads as a rendering fault rather than as a brush.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "img" / "ornament"

SEED = 20260919

# The two tones a stroke is painted with, B.6: the body and the dry streaks
# inside it. Both are currentColor at different strengths rather than two
# custom properties, and that is not the first thing this tried.
#
# B.6 asks for --brush-a and --brush-b. They do not survive the trip: an
# ornament is referenced with <use> from a separate file, and while `color` is
# a real inherited property and does cascade into the shadow tree that builds —
# which is what static/icons/sprite.svg has always relied on — a var() in a
# presentation attribute inside an externally referenced document resolves to
# nothing in Chrome, not even to its own fallback, and the stroke lands black.
# Measured, not assumed: the same attribute inline resolves both the variable
# and the fallback correctly.
#
# So one colour drives both tones and the class sets `color`. A stroke is still
# recoloured by a class, which is what B.6 was after; it just reads the colour
# from a property that is allowed to cross the boundary. .u-brush-strong in
# app.css is the second tone.
BODY_OPACITY = "0.42"
STREAK_OPACITY = "0.72"


def num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".") or "0"


class Wobble:
    """Smooth repeatable noise in [-1, 1], as a sum of three sines."""

    def __init__(self, rng: random.Random, scale: float = 1.0) -> None:
        self.terms = [
            (rng.uniform(1.5, 3.0), rng.uniform(0, math.tau), 0.55),
            (rng.uniform(4.0, 7.0), rng.uniform(0, math.tau), 0.30),
            (rng.uniform(9.0, 14.0), rng.uniform(0, math.tau), 0.15),
        ]
        self.scale = scale

    def __call__(self, t: float) -> float:
        return self.scale * sum(
            amp * math.sin(freq * t * math.tau + phase) for freq, phase, amp in self.terms
        )


def bezier(points: list[tuple[float, float]], t: float) -> tuple[float, float]:
    """De Casteljau on a cubic, so the centreline is a curve and not a polyline."""
    pts = list(points)
    while len(pts) > 1:
        pts = [
            (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            for a, b in zip(pts, pts[1:], strict=False)
        ]
    return pts[0]


def normal(points: list[tuple[float, float]], t: float, eps: float = 1e-3) -> tuple[float, float]:
    ax, ay = bezier(points, max(0.0, t - eps))
    bx, by = bezier(points, min(1.0, t + eps))
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) or 1.0
    return -dy / length, dx / length


def taper(t: float, head: float, tail: float) -> float:
    """1 in the middle, thin at both ends, and not symmetrically.

    A stroke pressed down and lifted has a longer tail than head, which is what
    ``tail`` is for. Smoothstep rather than a straight ramp, so the width does
    not change direction at a corner.
    """
    up = min(1.0, t / head) if head else 1.0
    down = min(1.0, (1.0 - t) / tail) if tail else 1.0
    edge = min(up, down)
    return edge * edge * (3 - 2 * edge)


def stroke(
    spine: list[tuple[float, float]],
    width: float,
    rng: random.Random,
    *,
    steps: int = 44,
    head: float = 0.07,
    tail: float = 0.42,
    ragged: float = 0.30,
) -> str:
    """One brush stroke as a closed path, both edges wobbling independently.

    The defaults are asymmetric on purpose: a brush lands, is dragged, and is
    lifted, so the start is blunt and the end runs out to a whisker. Equal ends
    read as a leaf, which is what the first pass of this looked like.
    """
    left_noise, right_noise = Wobble(rng, ragged), Wobble(rng, ragged)
    body = Wobble(rng, 0.18)

    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        x, y = bezier(spine, t)
        nx, ny = normal(spine, t)
        half = width * 0.5 * taper(t, head, tail) * (1 + body(t))
        left.append((x + nx * half * (1 + left_noise(t)), y + ny * half * (1 + left_noise(t))))
        right.append((x - nx * half * (1 + right_noise(t)), y - ny * half * (1 + right_noise(t))))

    points = left + right[::-1]
    head_pt = points[0]
    return (
        "M"
        + num(head_pt[0])
        + ","
        + num(head_pt[1])
        + "".join("L" + num(x) + "," + num(y) for x, y in points[1:])
        + "Z"
    )


def streaks(
    spine: list[tuple[float, float]],
    width: float,
    rng: random.Random,
    count: int,
    *,
    steps: int = 26,
) -> list[str]:
    """The dry lines a worn brush leaves inside its own stroke."""
    out = []
    for _ in range(count):
        offset = rng.uniform(-0.52, 0.52)
        start, end = sorted((rng.uniform(0.04, 0.40), rng.uniform(0.55, 0.98)))
        thin = width * rng.uniform(0.018, 0.048)
        edge = Wobble(rng, 0.5)
        upper: list[tuple[float, float]] = []
        lower: list[tuple[float, float]] = []
        for i in range(steps + 1):
            t = start + (end - start) * i / steps
            x, y = bezier(spine, t)
            nx, ny = normal(spine, t)
            centre = width * 0.5 * taper(t, 0.07, 0.42) * offset
            half = thin * taper(i / steps, 0.25, 0.35) * (1 + edge(t))
            upper.append((x + nx * (centre + half), y + ny * (centre + half)))
            lower.append((x + nx * (centre - half), y + ny * (centre - half)))
        pts = upper + lower[::-1]
        out.append(
            "M"
            + num(pts[0][0])
            + ","
            + num(pts[0][1])
            + "".join("L" + num(x) + "," + num(y) for x, y in pts[1:])
            + "Z"
        )
    return out


def brush(
    name: str,
    width: float,
    height: float,
    spine: list[tuple[float, float]],
    thickness: float,
    *,
    dry: int = 6,
    head: float = 0.07,
    tail: float = 0.42,
    ragged: float = 0.30,
) -> str:
    rng = random.Random(f"{SEED}:{name}")
    body = stroke(spine, thickness, rng, head=head, tail=tail, ragged=ragged)
    inner = streaks(spine, thickness, rng, dry)
    return symbol(
        name,
        width,
        height,
        f'<g fill="currentColor"><path fill-opacity="{BODY_OPACITY}" d="{body}"/>'
        + "".join(f'<path fill-opacity="{STREAK_OPACITY}" d="{d}"/>' for d in inner)
        + "</g>",
    )


# --- the single-stroke marks ---------------------------------------------


def hand_line(points: list[tuple[float, float]], rng: random.Random, jitter: float = 1.4) -> str:
    """A cubic run with its control points nudged, so no two curves match."""
    out = ["M" + num(points[0][0]) + "," + num(points[0][1])]
    for i in range(1, len(points) - 1, 2):
        cx, cy = points[i]
        ex, ey = points[i + 1]
        out.append(
            "Q"
            + num(cx + rng.uniform(-jitter, jitter))
            + ","
            + num(cy + rng.uniform(-jitter, jitter))
            + " "
            + num(ex)
            + ","
            + num(ey)
        )
    return "".join(out)


def heart(name: str, rng: random.Random, lean: float) -> str:
    """One continuous stroke, closed at the point and open at the cleft.

    The owner draws theirs with a gap at the top left, which is what stops it
    looking like a dingbat. ``lean`` tilts the whole thing a degree or two.
    """
    w = 1.0
    path = (
        f"M{num(50 + lean)},{num(86)}"
        f"C{num(4)},{num(50)} {num(10)},{num(10)} {num(34)},{num(14)}"
        f"C{num(45)},{num(16)} {num(49)},{num(26)} {num(50 + lean)},{num(34)}"
        f"C{num(53 + lean)},{num(25)} {num(58)},{num(14)} {num(70)},{num(13)}"
        f"C{num(93)},{num(12)} {num(97)},{num(52)} {num(50 + lean)},{num(86)}"
    )
    return symbol(
        name,
        100,
        100,
        f'<path fill="none" stroke="currentColor" stroke-width="{num(9 * w)}" '
        f'stroke-linecap="round" stroke-linejoin="round" d="{path}"/>',
    )


def scribble() -> str:
    rng = random.Random(f"{SEED}:scribble")
    spine = [(3, 14), (32, 4), (68, 20), (97, 8)]
    return symbol(
        "scribble-underline",
        100,
        24,
        '<path fill="none" stroke="currentColor" stroke-width="5.5" '
        f'stroke-linecap="round" d="{hand_line(spine, rng, 2.2)}"/>',
    )


def arrow() -> str:
    rng = random.Random(f"{SEED}:arrow")
    spine = [(6, 6), (52, 10), (58, 46), (86, 62)]
    head = "M76,50L88,63L70,70"
    return symbol(
        "arrow-curly",
        100,
        80,
        '<g fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" '
        'stroke-linejoin="round">'
        f'<path d="{hand_line(spine, rng, 2.6)}"/><path d="{head}"/></g>',
    )


def sparks() -> str:
    rng = random.Random(f"{SEED}:sparks")
    rays = []
    for i in range(5):
        angle = math.radians(-64 + i * 32 + rng.uniform(-5, 5))
        inner = 20 + rng.uniform(-3, 3)
        outer = inner + 22 + rng.uniform(-6, 8)
        x1, y1 = 8 + inner * math.cos(angle), 50 + inner * math.sin(angle)
        x2, y2 = 8 + outer * math.cos(angle), 50 + outer * math.sin(angle)
        rays.append(f"M{num(x1)},{num(y1)}L{num(x2)},{num(y2)}")
    return symbol(
        "sparks",
        70,
        100,
        '<path fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" '
        f'd="{"".join(rays)}"/>',
    )


def circle_hand() -> str:
    """The ring an icon sits in, C.1 block 2. Not a border: a drawn ring."""
    rng = random.Random(f"{SEED}:circle")
    steps = 40
    points = []
    wobble = Wobble(rng, 0.035)
    for i in range(steps + 1):
        t = i / steps
        # A little past a full turn, so the ends overlap the way a pen does.
        angle = t * math.tau * 1.06 - 0.35
        r = 44 * (1 + wobble(t))
        points.append((50 + r * math.cos(angle), 50 + r * math.sin(angle) * 0.985))
    d = (
        "M"
        + num(points[0][0])
        + ","
        + num(points[0][1])
        + "".join("L" + num(x) + "," + num(y) for x, y in points[1:])
    )
    return symbol(
        "circle-hand",
        100,
        100,
        '<path fill="none" stroke="currentColor" stroke-width="4.5" '
        f'stroke-linecap="round" d="{d}"/>',
    )


def blob() -> str:
    """The soft bloom behind a block. The owner's own file is full of them."""
    rng = random.Random(f"{SEED}:blob")
    steps = 36
    wobble = Wobble(rng, 0.09)
    points = []
    for i in range(steps):
        t = i / steps
        angle = t * math.tau
        r = 46 * (1 + wobble(t))
        points.append((50 + r * math.cos(angle), 50 + r * math.sin(angle)))
    d = (
        "M"
        + num(points[0][0])
        + ","
        + num(points[0][1])
        + "".join("L" + num(x) + "," + num(y) for x, y in points[1:])
        + "Z"
    )
    return symbol("blob", 100, 100, f'<path fill="currentColor" fill-opacity="0.34" d="{d}"/>')


# --- files ----------------------------------------------------------------


def symbol(name: str, width: float, height: float, body: str) -> str:
    """The shape as a <symbol>, ready for both the sprite and its own file."""
    return f'<symbol id="{name}" viewBox="0 0 {num(width)} {num(height)}">{body}</symbol>'


def standalone(sym: str) -> str:
    """One symbol in a file of its own, so <use href="file.svg#id"> resolves."""
    return '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + sym + "</svg>\n"


BRUSHES = {
    # A long flat sweep for the edge of a section.
    "brush-1": (420, 80, [(4, 58), (130, 14), (292, 70), (416, 22)], 26.0),
    # The corner hook that sits behind the hero, C.1 block 1.
    "brush-2": (260, 260, [(10, 18), (186, 30), (232, 158), (104, 250)], 34.0),
    # The band under the figures, C.1 block 4: wide, nearly straight, ragged.
    "brush-3": (520, 110, [(2, 60), (170, 40), (350, 76), (518, 52)], 52.0),
    # A short curl, for a corner that needs a comma rather than a line.
    "brush-4": (190, 190, [(24, 168), (10, 40), (150, 18), (172, 124)], 21.0),
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int]] = []

    def write(name: str, content: str) -> None:
        path = OUT / name
        path.write_text(content, encoding="utf-8")
        written.append((name, len(content.encode())))

    brush_symbols = {}
    for name, (w, h, spine, thickness) in BRUSHES.items():
        sym = brush(name, w, h, spine, thickness, dry=8 if thickness > 40 else 6)
        brush_symbols[name] = sym
        write(f"{name}.svg", standalone(sym))

    small = [
        heart("heart-1", random.Random(f"{SEED}:h1"), 0.0),
        heart("heart-2", random.Random(f"{SEED}:h2"), 3.0),
        heart("heart-3", random.Random(f"{SEED}:h3"), -3.5),
        scribble(),
        arrow(),
        sparks(),
        circle_hand(),
        blob(),
    ]
    for sym in small:
        name = sym.split('id="', 1)[1].split('"', 1)[0]
        write(f"{name}.svg", standalone(sym))

    # One sprite for the small marks, so a page that uses three hearts and an
    # arrow makes one request instead of four. The brushes stay out of it: they
    # are ten times the weight and a page rarely wants more than two.
    sprite = (
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="display:none">'
        + "".join(small)
        + "</svg>\n"
    )
    write("sprite.svg", sprite)

    total = sum(size for _, size in written)
    for name, size in written:
        flag = "  OVER 6 KB" if size > 6144 else ""
        print(f"{name:24} {size / 1024:5.1f} KB{flag}")
    print(f"{'total':24} {total / 1024:5.1f} KB   budget 40 KB")
    over = [name for name, size in written if size > 6144]
    if over or total > 40 * 1024:
        print(f"\nbudget exceeded: {over or 'total'}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
