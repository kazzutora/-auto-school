"""Property tests for the SEO text rules, tech.md sections 8 and 9."""

from hypothesis import given
from hypothesis import strategies as st

from apps.core.seo import (
    DESCRIPTION_LIMIT,
    TITLE_LIMIT,
    TITLE_SUFFIX,
    build_description,
    build_title,
    truncate_text,
)


@given(st.text(), st.integers(min_value=1, max_value=300))
def test_truncation_never_exceeds_the_limit(text: str, limit: int) -> None:
    assert len(truncate_text(text, limit)) <= limit


@given(st.text(), st.integers(min_value=1, max_value=300))
def test_truncation_keeps_a_prefix_of_the_source(text: str, limit: int) -> None:
    collapsed = " ".join(text.split())
    assert collapsed.startswith(truncate_text(text, limit))


@given(st.text(), st.integers(min_value=1, max_value=300))
def test_truncation_does_not_split_a_word(text: str, limit: int) -> None:
    collapsed = " ".join(text.split())
    result = truncate_text(text, limit)
    if result == collapsed:
        return

    # Either the cut landed on a space, or the very first word is itself longer
    # than the limit and there is nowhere to cut.
    cut_on_space = collapsed[len(result) : len(result) + 1] == " "
    first_word = collapsed.split(" ")[0]
    assert cut_on_space or len(first_word) > limit


@given(st.text())
def test_short_text_passes_through_with_whitespace_collapsed(text: str) -> None:
    collapsed = " ".join(text.split())
    if len(collapsed) <= DESCRIPTION_LIMIT:
        assert build_description(text) == collapsed


@given(st.text())
def test_title_fits_the_limit(subject: str) -> None:
    assert len(build_title(subject)) <= TITLE_LIMIT


@given(st.text())
def test_title_always_carries_wielun(subject: str) -> None:
    """tech.md section 8: commercial page titles must contain Wieluń."""
    assert "Wieluń" in build_title(subject)
    assert build_title(subject).endswith(TITLE_SUFFIX)


@given(st.text(), st.integers(min_value=1, max_value=300))
def test_truncation_leaves_no_dangling_space(text: str, limit: int) -> None:
    """DEV.md S8: a description must not end mid air.

    Cutting on a word boundary is the easy way to leave the space that boundary
    was made of, and it shows up in a search result as a gap before the ellipsis.
    """
    result = truncate_text(text, limit)

    assert result == result.strip()


@given(st.text(), st.integers(min_value=1, max_value=300))
def test_truncation_never_invents_whitespace(text: str, limit: int) -> None:
    """Every run of whitespace in the source collapses to one plain space."""
    result = truncate_text(text, limit)

    assert "  " not in result
    assert "\n" not in result
    assert "\t" not in result
