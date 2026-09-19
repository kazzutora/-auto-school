"""Small path builders shared by the brand generators.

Winding matters here. The wheel is one path filled with the nonzero rule: the
outer circle runs one way and every hole in it runs the other, so a hole that
overlaps a filled part — the cutouts meet the hub ring — still reads as a hole.
Sweep flag 1 is one direction, 0 the other; which is which does not matter as
long as holes disagree with the shape they sit in.
"""

from __future__ import annotations

import math


def num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".") or "0"


def circle(cx: float, cy: float, r: float, *, hole: bool = False) -> str:
    sweep = 0 if hole else 1
    return (
        f"M{num(cx - r)},{num(cy)}"
        f"A{num(r)},{num(r)} 0 1,{sweep} {num(cx + r)},{num(cy)}"
        f"A{num(r)},{num(r)} 0 1,{sweep} {num(cx - r)},{num(cy)}Z"
    )


def rounded_rect(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2, h / 2)
    return (
        f"M{num(x + r)},{num(y)}"
        f"H{num(x + w - r)}A{num(r)},{num(r)} 0 0,1 {num(x + w)},{num(y + r)}"
        f"V{num(y + h - r)}A{num(r)},{num(r)} 0 0,1 {num(x + w - r)},{num(y + h)}"
        f"H{num(x + r)}A{num(r)},{num(r)} 0 0,1 {num(x)},{num(y + h - r)}"
        f"V{num(y + r)}A{num(r)},{num(r)} 0 0,1 {num(x + r)},{num(y)}Z"
    )


def polygon(points: list[tuple[float, float]]) -> str:
    head = f"M{num(points[0][0])},{num(points[0][1])}"
    rest = "".join(f"L{num(x)},{num(y)}" for x, y in points[1:])
    return head + rest + "Z"


def polar(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def annular_sector(
    cx: float,
    cy: float,
    r_out: float,
    r_in: float,
    start: float,
    end: float,
    corner: float,
    *,
    hole: bool = True,
) -> str:
    """A ring segment with all four corners rounded.

    This is the shape of the gaps between the spokes. Drawn from the high angle
    back to the low one along the outer edge, so it winds against the disc it is
    cut from.
    """
    if not hole:
        start, end = end, start
    d_out = math.degrees(corner / r_out)
    d_in = math.degrees(corner / r_in)

    def p(r: float, a: float) -> tuple[float, float]:
        return polar(cx, cy, r, a)

    large_out = 1 if abs(end - start) - 2 * d_out > 180 else 0
    large_in = 1 if abs(end - start) - 2 * d_in > 180 else 0

    a_start = p(r_out, end - d_out)
    a_end = p(r_out, start + d_out)
    c_out_low, b_out_low = p(r_out, start), p(r_out - corner, start)
    c_in_low, b_in_low = p(r_in, start), p(r_in + corner, start)
    a_in_low, a_in_high = p(r_in, start + d_in), p(r_in, end - d_in)
    c_in_high, b_in_high = p(r_in, end), p(r_in + corner, end)
    c_out_high, b_out_high = p(r_out, end), p(r_out - corner, end)

    return (
        f"M{num(a_start[0])},{num(a_start[1])}"
        f"A{num(r_out)},{num(r_out)} 0 {large_out},0 {num(a_end[0])},{num(a_end[1])}"
        f"Q{num(c_out_low[0])},{num(c_out_low[1])} {num(b_out_low[0])},{num(b_out_low[1])}"
        f"L{num(b_in_low[0])},{num(b_in_low[1])}"
        f"Q{num(c_in_low[0])},{num(c_in_low[1])} {num(a_in_low[0])},{num(a_in_low[1])}"
        f"A{num(r_in)},{num(r_in)} 0 {large_in},1 {num(a_in_high[0])},{num(a_in_high[1])}"
        f"Q{num(c_in_high[0])},{num(c_in_high[1])} {num(b_in_high[0])},{num(b_in_high[1])}"
        f"L{num(b_out_high[0])},{num(b_out_high[1])}"
        f"Q{num(c_out_high[0])},{num(c_out_high[1])} {num(a_start[0])},{num(a_start[1])}Z"
    )
