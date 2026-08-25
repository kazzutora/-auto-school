"""Property tests for the courses domain logic, DEV.md S1.1."""

from dataclasses import dataclass
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.courses.services import (
    CURRENCY,
    CURRENCY_SEPARATOR,
    DECIMAL_SEPARATOR,
    MONTHS_IN_YEAR,
    START_LEAD_MONTHS,
    THOUSANDS_SEPARATOR,
    format_price,
    min_start_age,
    split_age,
)


@dataclass
class Course:
    min_age: int | None


@given(st.integers(min_value=14, max_value=30))
def test_start_age_is_three_months_below_the_legal_age(min_age: int) -> None:
    assert min_start_age(Course(min_age)) == min_age * MONTHS_IN_YEAR - START_LEAD_MONTHS


@given(st.integers(min_value=0, max_value=120))
def test_start_age_is_never_negative(min_age: int) -> None:
    result = min_start_age(Course(min_age))
    assert result is not None
    assert result >= 0


def test_no_age_limit_means_no_answer() -> None:
    """Psychotests and forklift courses declare no minimum age."""
    assert min_start_age(Course(None)) is None


def test_category_b_reads_as_seventeen_and_nine_months() -> None:
    months = min_start_age(Course(18))
    assert months is not None
    assert split_age(months) == (17, 9)


prices = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("99999"), allow_nan=False, allow_infinity=False
)


@given(prices)
def test_price_carries_two_decimals_and_the_currency(value: Decimal) -> None:
    rendered = format_price(value)

    assert rendered.endswith(CURRENCY)
    amount = rendered.removesuffix(CURRENCY).strip()
    assert len(amount.rsplit(DECIMAL_SEPARATOR, 1)[1]) == 2


@given(prices)
def test_price_rounds_rather_than_truncating(value: Decimal) -> None:
    rendered = format_price(value)
    digits = (
        rendered.removesuffix(CURRENCY)
        .replace(CURRENCY_SEPARATOR, "")
        .replace(THOUSANDS_SEPARATOR, "")
        .replace(DECIMAL_SEPARATOR, ".")
        .strip()
    )
    assert abs(Decimal(digits) - value) <= Decimal("0.5")


@given(prices, st.text(max_size=40))
def test_the_note_is_appended_not_swallowed(value: Decimal, note: str) -> None:
    rendered = format_price(value, note)
    if note.strip():
        assert rendered.endswith(note.strip())
    assert CURRENCY in rendered


@pytest.mark.parametrize("value", [None, "", "not a number", object()])
def test_a_missing_price_never_renders_as_none(value: object) -> None:
    """A page showing "None zł" is worse than a page showing nothing."""
    assert format_price(value) == ""  # type: ignore[arg-type]
    assert format_price(value, "cena od") == "cena od"  # type: ignore[arg-type]


def test_thousands_are_grouped() -> None:
    thousands = f"3{THOUSANDS_SEPARATOR}200{DECIMAL_SEPARATOR}00{CURRENCY_SEPARATOR}{CURRENCY}"
    assert format_price(Decimal("3200")) == thousands
    assert format_price(Decimal("120.5")) == (
        f"120{DECIMAL_SEPARATOR}50{CURRENCY_SEPARATOR}{CURRENCY}"
    )
    assert format_price(Decimal("3200"), "cena od") == f"{thousands} cena od"
