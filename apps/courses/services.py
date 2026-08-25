"""Pure domain logic for the courses slice. No ORM here."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

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


@dataclass(frozen=True)
class PriceRow:
    """One line of the price table: service, gross price, note."""

    label: str
    price: str
    note: str
    url: str = ""


def course_rows(courses: Iterable[Any]) -> list[PriceRow]:
    """Priced courses as table rows. A course with no price does not belong here."""
    rows = []
    for course in courses:
        if course.price_gross is None:
            continue
        label = f"{course.title} ({course.code})" if course.code else course.title
        rows.append(
            PriceRow(
                label=label,
                price=format_price(course.price_gross),
                note=course.price_note or "",
                url=course.get_absolute_url(),
            )
        )
    return rows


def price_item_rows(items: Iterable[Any]) -> list[PriceRow]:
    rows = []
    for item in items:
        note = " ".join(part for part in (item.unit, item.note) if part).strip()
        rows.append(PriceRow(label=item.title, price=format_price(item.price_gross), note=note))
    return rows


def group_price_items(items: Iterable[Any]) -> list[tuple[str, list[PriceRow]]]:
    """Bucket extra services by their group, in first seen order.

    Items with no group land in one unnamed bucket at the end, so nothing is
    dropped just because an editor left the field empty.
    """
    buckets: dict[str, list[Any]] = {}
    for item in items:
        buckets.setdefault(item.group or "", []).append(item)

    named = [(name, price_item_rows(rows)) for name, rows in buckets.items() if name]
    unnamed = buckets.get("")
    if unnamed:
        named.append(("", price_item_rows(unnamed)))
    return named


class HasSeats(Protocol):
    status: str
    seats_total: int | None
    seats_taken: int


def seats_left(intake: HasSeats) -> int | None:
    """Places still free, or None when the group has no declared capacity.

    Never negative: an over booked group reads as full, not as minus two.
    """
    if intake.seats_total is None:
        return None
    return max(0, intake.seats_total - (intake.seats_taken or 0))


def is_bookable(intake: HasSeats) -> bool:
    """Can a visitor still sign up for this start.

    Open, and either uncapped or with a place left. A group marked full or
    planned is visible but not bookable yet.
    """
    if intake.status != "open":
        return False
    free = seats_left(intake)
    return free is None or free > 0
