"""Pure domain logic for the courses slice. No ORM here."""

from decimal import Decimal, InvalidOperation
from typing import Protocol

# A candidate may start the course three months before reaching the legal age.
START_LEAD_MONTHS = 3
MONTHS_IN_YEAR = 12

# Polish typography: thousands are spaced, decimals follow a comma. Both
# separators below are U+00A0, so an amount never breaks across two lines.
# Anything rendering a price compares against these names, never a literal.
THOUSANDS_SEPARATOR = " "
CURRENCY_SEPARATOR = " "
DECIMAL_SEPARATOR = ","
CURRENCY = "zł"


class HasMinAge(Protocol):
    min_age: int | None


def min_start_age(course: HasMinAge) -> int | None:
    """Age in months from which enrolment is allowed.

    Months rather than years because the answer is rarely a whole year: a
    category B candidate may enrol at seventeen years and nine months. None when
    the course declares no age limit at all.
    """
    if course.min_age is None:
        return None
    return max(0, course.min_age * MONTHS_IN_YEAR - START_LEAD_MONTHS)


def split_age(months: int) -> tuple[int, int]:
    """Months as (years, remaining months)."""
    return divmod(months, MONTHS_IN_YEAR)


def format_price(value: Decimal | int | float | str | None, note: str = "") -> str:
    """Price the way it appears on a page, with the note appended.

    Returns the note alone when there is no price yet, and an empty string when
    there is neither: a missing price must never render as "None zł".
    """
    note = (note or "").strip()

    try:
        amount = Decimal(value) if value is not None else None
    except (InvalidOperation, TypeError, ValueError):
        amount = None

    if amount is None:
        return note

    whole, _, fraction = f"{amount:.2f}".partition(".")
    negative, digits = whole.startswith("-"), whole.lstrip("-")
    grouped = f"{int(digits):,}".replace(",", THOUSANDS_SEPARATOR)
    sign = "-" if negative else ""
    price = f"{sign}{grouped}{DECIMAL_SEPARATOR}{fraction}{CURRENCY_SEPARATOR}{CURRENCY}"

    return f"{price} {note}" if note else price
