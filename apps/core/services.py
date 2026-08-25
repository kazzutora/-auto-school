"""Pure domain logic for core. No ORM here, tech.md test doctrine section 9."""

from collections.abc import Iterable
from datetime import datetime, time
from typing import Protocol


class DayHours(Protocol):
    """Shape shared by OpeningHours rows and by test fixtures."""

    weekday: int
    opens: time | None
    closes: time | None


def is_open_at(schedule: Iterable[DayHours], moment: datetime) -> bool:
    """Is the department open at moment.

    A row with either bound missing means closed that day, tech.md section 4.1.
    A range that does not move forward (closes at or before opens) is treated as
    closed rather than as an overnight shift: no department here works nights.
    """
    for day in schedule:
        if day.weekday != moment.weekday():
            continue
        if day.opens is None or day.closes is None:
            return False
        if day.closes <= day.opens:
            return False
        return day.opens <= moment.time() < day.closes
    return False
