"""The ornament library, ROSE.md B.6 and B.7.

The marks are generated art committed to the repository, which only works if
two things hold: a rerun of the generator writes the same bytes, so a diff on
static/img/ornament/ means somebody changed the design rather than the seed;
and nothing in there can reach a screen reader, a pointer or a scroll thread.

The last one is the reason for the filter check. B.6 bans feTurbulence and its
relatives outright — not because they look wrong, but because a page carrying a
dozen of them drops frames on a phone the moment it scrolls, and nothing in a
screenshot says why.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings

ROOT = Path(settings.BASE_DIR)
ORNAMENT = ROOT / "static" / "img" / "ornament"

BRUSHES = ["brush-1", "brush-2", "brush-3", "brush-4"]
MARKS = [
    "heart-1",
    "heart-2",
    "heart-3",
    "scribble-underline",
    "arrow-curly",
    "sparks",
    "circle-hand",
    "blob",
]

# B.6 names these by name. feImage and feFlood are here too: they are the other
# two ways to smuggle a raster or a repaint into what should be a path.
BANNED_FILTERS = (
    "feTurbulence",
    "feDisplacementMap",
    "feGaussianBlur",
    "feImage",
    "feFlood",
    "filter=",
)

FILES = BRUSHES + MARKS


@pytest.mark.parametrize("name", FILES)
def test_the_mark_is_there(name: str) -> None:
    assert (ORNAMENT / f"{name}.svg").exists(), name


def test_the_sprite_carries_every_small_mark() -> None:
    """One request for the hearts and the arrows a page uses together."""
    sprite = (ORNAMENT / "sprite.svg").read_text(encoding="utf-8")
    ids = set(re.findall(r'<symbol id="([\w-]+)"', sprite))
    assert ids == set(MARKS), ids ^ set(MARKS)


def test_the_brushes_stay_out_of_the_sprite() -> None:
    """Ten times the weight of a heart, and a page rarely wants two."""
    sprite = (ORNAMENT / "sprite.svg").read_text(encoding="utf-8")
    for name in BRUSHES:
        assert f'id="{name}"' not in sprite, name


@pytest.mark.parametrize("name", FILES + ["sprite"])
def test_nothing_is_announced(name: str) -> None:
    svg = (ORNAMENT / f"{name}.svg").read_text(encoding="utf-8")
    assert 'aria-hidden="true"' in svg, name
    assert "<text" not in svg, name
    assert "<title" not in svg, name


@pytest.mark.parametrize("name", FILES + ["sprite"])
def test_no_filter_runs_at_paint_time(name: str) -> None:
    svg = (ORNAMENT / f"{name}.svg").read_text(encoding="utf-8")
    for banned in BANNED_FILTERS:
        assert banned not in svg, f"{name} uses {banned}"


@pytest.mark.parametrize("name", FILES + ["sprite"])
def test_each_file_stays_under_six_kilobytes(name: str) -> None:
    size = (ORNAMENT / f"{name}.svg").stat().st_size
    assert size <= 6144, f"{name}.svg is {size} B"


def test_the_whole_set_stays_under_forty() -> None:
    total = sum(path.stat().st_size for path in ORNAMENT.glob("*.svg"))
    assert total <= 40 * 1024, f"the set comes to {total} B"


def test_a_stroke_takes_the_colour_of_what_it_is_on() -> None:
    """currentColor rather than a literal, so a class can recolour it.

    B.6 asks for --brush-a and --brush-b. They do not survive an external
    <use>: `color` cascades into that shadow tree and a var() in a presentation
    attribute inside it does not, so the stroke landed black. The generator
    says the same thing at greater length.
    """
    for name in BRUSHES:
        svg = (ORNAMENT / f"{name}.svg").read_text(encoding="utf-8")
        assert 'fill="currentColor"' in svg, name
        assert "fill-opacity" in svg, name
        assert not re.search(r"#[0-9A-Fa-f]{3,8}", svg), f"{name} has a literal colour"


def test_rerunning_the_generator_changes_nothing() -> None:
    """A fixed seed is what makes generated art reviewable.

    Without it every touch of the script rewrites thirteen files and the diff
    stops meaning anything.
    """
    before = {path.name: path.read_bytes() for path in sorted(ORNAMENT.glob("*.svg"))}
    subprocess.run(
        [sys.executable, "-m", "scripts.brand.gen_ornaments"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    after = {path.name: path.read_bytes() for path in sorted(ORNAMENT.glob("*.svg"))}
    changed = [name for name in before if before[name] != after.get(name)]
    assert not changed, changed
    assert set(before) == set(after)
