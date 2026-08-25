"""Property tests for seat counting, DEV.md S2.2."""

from dataclasses import dataclass

from hypothesis import given
from hypothesis import strategies as st

from apps.courses.services import is_bookable, seats_left

OPEN, FULL, PLANNED, CLOSED = "open", "full", "planned", "closed"


@dataclass
class Intake:
    status: str = OPEN
    seats_total: int | None = None
    seats_taken: int = 0


counts = st.integers(min_value=0, max_value=500)


@given(counts, counts)
def test_seats_left_is_never_negative(total: int, taken: int) -> None:
    """An over booked group reads as full, not as minus two."""
    result = seats_left(Intake(seats_total=total, seats_taken=taken))
    assert result is not None
    assert result >= 0


@given(counts, counts)
def test_seats_left_is_the_difference_while_there_is_room(total: int, taken: int) -> None:
    if taken <= total:
        assert seats_left(Intake(seats_total=total, seats_taken=taken)) == total - taken


@given(counts)
def test_no_declared_capacity_means_no_number(taken: int) -> None:
    assert seats_left(Intake(seats_total=None, seats_taken=taken)) is None


@given(counts)
def test_a_group_with_no_room_is_not_bookable(total: int) -> None:
    """The acceptance criterion: zero places closes enrolment."""
    assert is_bookable(Intake(status=OPEN, seats_total=total, seats_taken=total)) is False


@given(counts, counts)
def test_bookable_needs_an_open_status(total: int, taken: int) -> None:
    for status in (FULL, PLANNED, CLOSED):
        assert is_bookable(Intake(status=status, seats_total=total, seats_taken=taken)) is False


@given(counts, counts)
def test_bookable_agrees_with_seats_left(total: int, taken: int) -> None:
    intake = Intake(status=OPEN, seats_total=total, seats_taken=taken)
    assert is_bookable(intake) is (seats_left(intake) > 0)


def test_an_uncapped_open_group_is_bookable() -> None:
    assert is_bookable(Intake(status=OPEN, seats_total=None, seats_taken=99)) is True
