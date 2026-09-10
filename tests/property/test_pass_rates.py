"""Property tests for the pass rate arithmetic, OSTRYCHARZ.md O1.

The one page on this site whose numbers a reader will check with a calculator,
so the invariants get stated rather than sampled.
"""

from dataclasses import dataclass

from hypothesis import given
from hypothesis import strategies as st

from apps.core.services import (
    PERCENT,
    attempt_percents,
    average_attempts,
    first_attempt_percent,
    not_passed,
    pass_rate_percent,
)


@dataclass
class Cohort:
    year: int
    students: int
    passed_1st: int
    passed_2nd: int
    passed_3rd: int
    passed_4th: int


counts = st.integers(min_value=0, max_value=10_000)


@st.composite
def cohorts(draw: st.DrawFn) -> Cohort:
    """A year of results. The four attempts never exceed the headcount.

    Generated that way because that is the only shape a real cohort has: the
    columns are a partition of the people who sat. The malformed case — columns
    over headcount — is pinned by its own example in tests/unit.
    """
    students = draw(st.integers(min_value=0, max_value=5_000))
    remaining = students
    attempts = []
    for _ in range(4):
        taken = draw(st.integers(min_value=0, max_value=remaining))
        attempts.append(taken)
        remaining -= taken
    return Cohort(2025, students, *attempts)


@given(counts, counts)
def test_a_percentage_is_always_a_percentage(passed: int, students: int) -> None:
    assert 0 <= pass_rate_percent(passed, students) <= PERCENT


@given(st.integers(max_value=0), counts)
def test_nobody_and_nothing_are_both_nought(passed: int, students: int) -> None:
    """A year with no candidates has no rate, and it is 0, not a crash."""
    assert pass_rate_percent(passed, students) == 0


@given(cohorts())
def test_every_attempt_column_is_a_percentage(entry: Cohort) -> None:
    percents = attempt_percents(entry)

    assert len(percents) == 4
    for percent in percents:
        assert 0 <= percent <= PERCENT


@given(cohorts())
def test_the_columns_never_claim_more_than_everybody(entry: Cohort) -> None:
    """The sum is allowed to overshoot 100 by rounding, and by nothing else.

    Four percentages each rounded on their own can total 101 while every one of
    them is the honest rounding of its own count — that is why /zdawalnosc/
    prints the counts beside them and says so. What must never happen is a total
    that overshoots by more than those four half-percent errors can account for.
    """
    total = sum(attempt_percents(entry))

    assert total <= PERCENT + 2


@given(cohorts())
def test_the_headline_is_the_first_column(entry: Cohort) -> None:
    assert first_attempt_percent(entry) == attempt_percents(entry)[0]


@given(cohorts())
def test_everybody_is_accounted_for(entry: Cohort) -> None:
    """Passed at some attempt, or still waiting. There is no third state."""
    passed = entry.passed_1st + entry.passed_2nd + entry.passed_3rd + entry.passed_4th

    assert passed + not_passed(entry) == entry.students


@given(cohorts())
def test_nobody_is_left_behind_twice(entry: Cohort) -> None:
    assert 0 <= not_passed(entry) <= entry.students


@given(cohorts())
def test_the_mean_lies_between_one_and_four_attempts_or_does_not_exist(
    entry: Cohort,
) -> None:
    """Nobody passes in fewer than one try and this table records at most four.

    None when nobody has passed: a mean over an empty set does not exist, and
    0,0 would claim everyone passed without sitting the exam.
    """
    mean = average_attempts(entry)
    passed = entry.passed_1st + entry.passed_2nd + entry.passed_3rd + entry.passed_4th

    if passed == 0:
        assert mean is None
    else:
        assert mean is not None
        assert 1.0 <= mean <= 4.0


@given(cohorts())
def test_a_perfect_year_reads_as_a_hundred_percent(entry: Cohort) -> None:
    """Everyone through at the first attempt is 100%, not 99 and not 101."""
    perfect = Cohort(entry.year, entry.students, entry.students, 0, 0, 0)

    if entry.students:
        assert first_attempt_percent(perfect) == PERCENT
        assert average_attempts(perfect) == 1.0
        assert not_passed(perfect) == 0
