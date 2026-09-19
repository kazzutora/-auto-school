"""The motion layer, ROSE.md K7 and REDESIGN.md part C.

Part C survived the palette change untouched, and its two hard rules are the
ones worth a gate. Everything moves on CSS — there is no animation library and
CLAUDE.md rule 6c forbids adding one — and everything that moves is written so
that not moving is the correct rendering.

That second rule is what these check. A reveal written the usual way starts at
opacity 0 and is brought back by a keyframe; on a browser that cannot run the
keyframe, or for a reader who asked for less motion, the block simply never
appears. Every animation here is therefore inside @supports and inside
prefers-reduced-motion: no-preference, and the element's own base state is the
finished one.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

SRC = Path(settings.BASE_DIR) / "static" / "src" / "css"
MOTION = SRC / "motion.css"
APP = SRC / "app.css"
JS = Path(settings.BASE_DIR) / "static" / "js"

# ROSE.md K7: the ornament that moves, and the rule for each.
ANIMATED = (
    ".u-scribbled::after",
    '[data-ornament="heart"]',
    ".u-brush-edge-top",
    ".u-brush-corner-tr",
)


def motion() -> str:
    return MOTION.read_text(encoding="utf-8")


def guarded_region() -> str:
    """Everything inside a `@supports (animation-timeline: view())` block."""
    text = motion()
    out = []
    for start in (m.start() for m in re.finditer(r"@supports \(animation-timeline", text)):
        depth = 0
        for i in range(text.index("{", start), len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    out.append(text[start : i + 1])
                    break
    return "\n".join(out)


def test_there_is_a_guarded_region_at_all() -> None:
    """A broken parse would make every assertion below pass on an empty string."""
    assert len(guarded_region()) > 500


@pytest.mark.parametrize("selector", ANIMATED)
def test_the_ornament_only_moves_where_it_can(selector: str) -> None:
    """Scroll driven animation lives inside both guards or not at all.

    Outside them the keyframe's `from` becomes the element's rendering on every
    browser that cannot run it, which for a fade means invisible.
    """
    region = guarded_region()
    assert selector in region, f"{selector} animates outside @supports"
    before = region[: region.index(selector)]
    assert "prefers-reduced-motion: no-preference" in before, (
        f"{selector} is not inside the reduced-motion guard"
    )


@pytest.mark.parametrize("selector", ANIMATED)
def test_nothing_is_left_moving(selector: str) -> None:
    """K7 point 2: the hearts appear once and do not beat.

    An ornament that repeats forever is an element competing with the text
    beside it for the rest of the visit, and this page has three of them.
    """
    text = motion()
    block = text[text.index(selector) : text.index(selector) + 400]
    assert "infinite" not in block, f"{selector} repeats forever"
    assert "alternate" not in block, f"{selector} ping-pongs"


@pytest.mark.parametrize("selector", ANIMATED)
def test_reduced_motion_turns_it_off_by_name(selector: str) -> None:
    """The blanket reduce block has to name every animated selector.

    A rule it does not name keeps its animation, and `animation: … both` holds
    the element at the keyframe's `from` — which is the one arrangement where
    asking for less motion gives you a blank space instead.
    """
    text = motion()
    reduce_block = text[text.index("@media (prefers-reduced-motion: reduce)") :]
    reduce_block = reduce_block[: reduce_block.index("@media print")]
    assert selector in reduce_block, f"{selector} is not switched off under reduce"


def test_print_gets_the_finished_page() -> None:
    printed = motion()[motion().index("@media print") :]
    for selector in ANIMATED:
        assert selector in printed, f"{selector} is not settled for print"


def test_no_animation_library_reached_the_page() -> None:
    """CLAUDE.md rule 6c: not GSAP, not Motion, not AOS.

    Checked against the files that ship rather than against package.json,
    because the ban is on what the visitor downloads.
    """
    shipped = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in JS.glob("*.js")
    ).lower()
    for library in ("gsap", "aos.js", "animejs", "framer-motion", "motion.dev"):
        assert library not in shipped, f"{library} is on the page"


def test_the_motion_script_stays_small() -> None:
    """K7: the animation javascript does not grow. 3 KB gzip is the ceiling."""
    import gzip

    raw = (JS / "motion.js").read_bytes()
    assert len(gzip.compress(raw)) < 3 * 1024, len(gzip.compress(raw))


def test_the_counter_carries_its_own_answer() -> None:
    """C.5: the number is right before the script runs and if it never does."""
    stat = (Path(settings.BASE_DIR) / "templates" / "cotton" / "stat.html").read_text(
        encoding="utf-8"
    )
    assert 'data-count-to="{{ value }}">{{ value }}' in stat


def test_the_polaroid_straightens_rather_than_spins() -> None:
    """K7 point 4, and the reason it is a transition and not an animation."""
    app = APP.read_text(encoding="utf-8")
    block = app[app.index(".u-polaroid {") :]
    block = block[: block.index("@media (hover: hover)") + 200]
    assert "transition: rotate" in block
    assert "rotate: 0deg" in block
