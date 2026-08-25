"""Property tests for the gallery grouping, tech.md section 9."""

from dataclasses import dataclass

from hypothesis import given
from hypothesis import strategies as st

from apps.gallery.services import group_by_section

ORDER = ("school", "vehicles", "yard", "events")


@dataclass
class Img:
    section: str


images = st.lists(st.sampled_from([*ORDER, "unknown"]).map(Img), max_size=30)


@given(images)
def test_no_image_is_lost(items: list[Img]) -> None:
    grouped = sum((bucket for _name, bucket in group_by_section(items, ORDER)), [])
    assert len(grouped) == len(items)


@given(images)
def test_no_empty_section_is_rendered(items: list[Img]) -> None:
    for _name, bucket in group_by_section(items, ORDER):
        assert bucket


@given(images)
def test_declared_sections_keep_their_order(items: list[Img]) -> None:
    names = [name for name, _bucket in group_by_section(items, ORDER) if name in ORDER]
    assert names == [name for name in ORDER if name in names]


@given(images)
def test_a_section_outside_the_order_still_shows_up(items: list[Img]) -> None:
    """A new choice in the enum must not silently hide rows."""
    grouped = dict(group_by_section(items, ORDER))
    if any(image.section == "unknown" for image in items):
        assert "unknown" in grouped
