"""Property tests for "open now", tech.md sections 4.1 and 9."""

from dataclasses import dataclass
from datetime import datetime, time

from hypothesis import given
from hypothesis import strategies as st

from apps.core.services import is_open_at


@dataclass
class Day:
    weekday: int
    opens: time | None
    closes: time | None


moments = st.datetimes(
    min_value=datetime(2026, 1, 1),
    max_value=datetime(2027, 12, 31, 23, 59, 59),
)
times = st.times()


@given(moments)
def test_no_rows_means_closed(moment: datetime) -> None:
    assert is_open_at([], moment) is False


@given(moments, times)
def test_missing_bound_means_closed(moment: datetime, moment_time: time) -> None:
    weekday = moment.weekday()
    assert is_open_at([Day(weekday, None, moment_time)], moment) is False
    assert is_open_at([Day(weekday, moment_time, None)], moment) is False
    assert is_open_at([Day(weekday, None, None)], moment) is False


@given(moments, times, times)
def test_open_exactly_inside_the_range(moment: datetime, a: time, b: time) -> None:
    opens, closes = min(a, b), max(a, b)
    row = Day(moment.weekday(), opens, closes)

    expected = opens < closes and opens <= moment.time() < closes
    assert is_open_at([row], moment) is expected


@given(moments, times, times)
def test_a_row_for_another_weekday_never_opens_the_door(moment: datetime, a: time, b: time) -> None:
    other = (moment.weekday() + 1) % 7
    assert is_open_at([Day(other, min(a, b), max(a, b))], moment) is False


@given(moments, times)
def test_a_range_that_does_not_move_forward_is_closed(moment: datetime, at: time) -> None:
    """Equal or reversed bounds mean closed, not an overnight shift."""
    assert is_open_at([Day(moment.weekday(), at, at)], moment) is False


@given(moments, times, times)
def test_closing_time_is_exclusive(moment: datetime, a: time, b: time) -> None:
    opens, closes = min(a, b), max(a, b)
    if opens >= closes:
        return
    at_close = moment.replace(
        hour=closes.hour, minute=closes.minute, second=closes.second, microsecond=closes.microsecond
    )
    assert is_open_at([Day(at_close.weekday(), opens, closes)], at_close) is False
