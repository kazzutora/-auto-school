"""The shapes of the mark, as numbers, ROSE.md K1.

The wheel, the L plate and the cap are described once here and drawn twice:
into svg by gen_logo.py and into png by the same module through Pillow. Keeping
the parameters in one place is what stops the favicon drifting away from the
lockup over time.

Everything is in units of the wheel radius, so the whole mark scales by
changing one number.

Measured off static/img/brand/source/logo-light.png: the wheel there is 86px
across, the rim is a seventh of the radius, the hub sits at three tenths of it,
and the three spokes run left, right and down with six holes drilled in them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- the wheel, in fractions of its radius -------------------------------

RIM = 0.155  # rim thickness
HUB_OUTER = 0.30
HUB_INNER = 0.175
SPOKE_HALF_DEG = 14.0  # half the angular width of a spoke at the inner rim
CUT_CORNER = 0.085  # corner radius of the cutouts between the spokes
HOLE_R = 0.055
HOLES_SIDE = (0.50, 0.68)  # along the left and right spokes
HOLES_DOWN = (0.45, 0.63)  # along the bottom spoke

# Screen angles, y downward: 0 right, 90 down, 180 left, 270 up.
SPOKE_ANGLES = (0.0, 90.0, 180.0)


@dataclass(frozen=True)
class Cutout:
    """One gap between two spokes, as an annular sector."""

    start: float  # degrees, screen space
    end: float  # degrees, sweeping positive


def cutouts() -> list[Cutout]:
    """The three gaps: one wide one above, two below the hub."""
    h = SPOKE_HALF_DEG
    return [
        Cutout(start=180.0 + h, end=360.0 - h),  # over the top
        Cutout(start=90.0 + h, end=180.0 - h),  # lower left
        Cutout(start=0.0 + h, end=90.0 - h),  # lower right
    ]


def holes() -> list[tuple[float, float]]:
    """(distance from centre, angle) for the six drilled holes."""
    out = []
    for d in HOLES_SIDE:
        out.append((d, 0.0))
        out.append((d, 180.0))
    for d in HOLES_DOWN:
        out.append((d, 90.0))
    return out


def polar(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


# --- the L plate and the cap, in fractions of the plate's width ----------

PLATE_ASPECT = 1.28  # taller than wide, as in the owner's file
PLATE_RADIUS = 0.23  # corner radius
PLATE_BORDER = 0.078  # the crimson frame

L_STEM = 0.24  # stem width
L_FOOT_H = 0.215  # foot height
L_HEIGHT = 0.69  # total height of the letter
L_WIDTH = 0.56

# The cap sits on the plate and overlaps it. Coordinates are relative to the
# plate: x from its left edge, y from its top, both in plate widths. Measured
# off the owner's file, where the board is a tilted rhombus, the crown a band
# under it, and the tassel hangs clear of the plate's right corner.
CAP_BOARD = (
    (0.00, -0.26),  # left point
    (0.46, -0.52),  # top point
    (1.12, -0.21),  # right point
    (0.64, 0.06),  # bottom point
)
CAP_CROWN = (0.17, -0.17, 0.64, 0.27)  # x, y, width, height of the crown band
CAP_BUTTON = (0.46, -0.35, 0.055)  # cx, cy, r
CAP_TASSEL_CORD = ((0.46, -0.35), (1.02, -0.33), (1.12, -0.10))
CAP_TASSEL = (1.12, -0.10, 0.125, 0.40)  # cx, top y, width, height
