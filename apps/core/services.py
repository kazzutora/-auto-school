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


# --------------------------------------------------------------------------
# Pass rates, tech.md section 4.1.


class ExamYear(Protocol):
    """Shape shared by PassRate rows and by test fixtures."""

    year: int
    students: int
    passed_1st: int
    passed_2nd: int
    passed_3rd: int
    passed_4th: int


PERCENT = 100


def pass_rate_percent(passed: int, students: int) -> int:
    """``passed`` as a whole percent of ``students``.

    Rounded rather than truncated, and clamped into 0..100 at both ends. A year
    with no candidates is 0 %, not a crash: the row exists before the numbers
    do, and a division by zero on the page that carries the school's best
    argument is the worst place to find that out.

    Whole percents on purpose. "75,8 %" invites the reader to check the
    arithmetic against a headcount the page does not publish.
    """
    if students <= 0 or passed <= 0:
        return 0
    return min(PERCENT, round(passed * PERCENT / students))


def first_attempt_percent(entry: ExamYear) -> int:
    """The one number the school leads with."""
    return pass_rate_percent(entry.passed_1st, entry.students)


def attempt_percents(entry: ExamYear) -> list[int]:
    """The four attempts as percents, in order.

    Each is rounded on its own, so the four can add up to 99 or 101 while every
    single one is the honest rounding of its own count. The page therefore
    prints counts as the primary figure and percents beside them, and never
    sums the percents.
    """
    counts = (entry.passed_1st, entry.passed_2nd, entry.passed_3rd, entry.passed_4th)
    return [pass_rate_percent(count, entry.students) for count in counts]


def not_passed(entry: ExamYear) -> int:
    """Candidates in this cohort who have not passed yet.

    ``students`` counts everybody who sat the exam; the four attempt columns
    count everybody who got through. The difference is the people still without
    a licence, and it is the reason the four percentages do not add up to 100.

    Printing it is not modesty, it is what makes the other four figures
    checkable. The school's own site prints 76% for the first attempt, which is
    68 of the 90 who eventually passed rather than 68 of the 92 who sat — and a
    reader who cannot see the 2 has no way to tell those two claims apart.

    Never negative: a cohort whose columns exceed its headcount is a data entry
    error, not minus two people.
    """
    counts = (entry.passed_1st, entry.passed_2nd, entry.passed_3rd, entry.passed_4th)
    return max(0, entry.students - sum(counts))


def average_attempts(entry: ExamYear) -> float | None:
    """Mean number of tries per candidate who passed, to one decimal.

    None when nobody has passed yet, because a mean over an empty set is not
    zero — it does not exist, and printing 0,0 would claim everyone passed
    without sitting the exam.
    """
    counts = (entry.passed_1st, entry.passed_2nd, entry.passed_3rd, entry.passed_4th)
    passed = sum(counts)
    if passed <= 0:
        return None
    tries = sum(count * position for position, count in enumerate(counts, start=1))
    return round(tries / passed, 1)


# --------------------------------------------------------------------------
# File sizes, tech.md section 4.1.

_UNITS = ("B", "KB", "MB", "GB")
_STEP = 1024


def human_size(size_bytes: int | None, decimal_sep: str = ",") -> str:
    """``1258291`` as ``"1,2 MB"``.

    Binary steps, one decimal from KB up, none for bytes — half a byte is not a
    thing. The separator is a parameter because the site is polish first and
    polish writes a decimal comma, while a test reads more plainly with a dot.

    Returns an empty string for a missing size, so a template can print it
    unguarded and get nothing rather than "None".
    """
    if not size_bytes or size_bytes < 0:
        return ""

    value = float(size_bytes)
    unit = _UNITS[0]
    for candidate in _UNITS:
        unit = candidate
        if value < _STEP or candidate == _UNITS[-1]:
            break
        value /= _STEP

    if unit == _UNITS[0]:
        return f"{int(value)} {unit}"
    return f"{value:.1f}".replace(".", decimal_sep) + f" {unit}"


# --------------------------------------------------------------------------
# YouTube, without youtube's javascript. tech.md section 2.

_YOUTUBE_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be")
_YOUTUBE_ID_LENGTH = 11


def youtube_id(url: str) -> str:
    """The video id inside a watch, share or embed url. "" if there is none.

    Parsed rather than fetched: the page must make no request to youtube.com
    until the reader clicks, so the poster frame and the link are both built
    out of this id and nothing else.
    """
    from urllib.parse import parse_qs, urlparse

    if not url:
        return ""

    parts = urlparse(url)
    if parts.hostname not in _YOUTUBE_HOSTS:
        return ""

    if parts.hostname == "youtu.be":
        candidate = parts.path.lstrip("/")
    elif parts.path.startswith(("/embed/", "/shorts/", "/v/")):
        candidate = parts.path.split("/")[2] if len(parts.path.split("/")) > 2 else ""
    else:
        candidate = parse_qs(parts.query).get("v", [""])[0]

    candidate = candidate.split("/")[0]
    valid = len(candidate) == _YOUTUBE_ID_LENGTH and all(
        character.isalnum() or character in "-_" for character in candidate
    )
    return candidate if valid else ""
