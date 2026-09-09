"""Exam results, tech.md sections 4.1 and 5.

This is the school's strongest argument and the one number a candidate's parent
will check with a calculator. The arithmetic therefore gets more attention here
than anywhere else on the site.
"""

import json
import re
from types import SimpleNamespace

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import PassRate
from apps.core.services import (
    attempt_percents,
    average_attempts,
    first_attempt_percent,
    not_passed,
    pass_rate_percent,
)
from apps.reviews.models import Testimonial
from tests.factories import notify_site

pytestmark = pytest.mark.django_db


def year(**overrides: object) -> SimpleNamespace:
    """A cohort, as the services see one. No ORM: they take a shape, not a row."""
    values: dict = {
        "year": 2025,
        "students": 92,
        "passed_1st": 68,
        "passed_2nd": 16,
        "passed_3rd": 3,
        "passed_4th": 3,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def body_of(client: Client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == 200, url
    return response.content.decode()


@pytest.fixture
def published() -> PassRate:
    notify_site()
    return PassRate.objects.create(
        year=2025, students=92, passed_1st=68, passed_2nd=16, passed_3rd=3, passed_4th=3
    )


# --------------------------------------------------------------------------
# the arithmetic


def test_the_headline_figure_is_the_first_attempt_over_everyone_who_sat() -> None:
    """68 of 92, not 68 of the 90 who eventually passed.

    The old site prints 76%, which is the second of those. Ours is 74%, because
    the label beside the number says "kursantów".
    """
    assert first_attempt_percent(year()) == 74


def test_a_year_with_nobody_in_it_does_not_divide_by_zero() -> None:
    assert first_attempt_percent(year(students=0, passed_1st=0)) == 0
    assert attempt_percents(year(students=0, passed_1st=0, passed_2nd=0)) == [0, 0, 0, 0]


@pytest.mark.parametrize(
    ("passed", "students", "expected"),
    [
        (0, 10, 0),
        (10, 10, 100),
        (1, 3, 33),
        (2, 3, 67),
        (5, 10, 50),
        # More passes than candidates is a data entry error, not 120%.
        (12, 10, 100),
        (-1, 10, 0),
        (5, -1, 0),
    ],
)
def test_a_percentage_stays_inside_nought_and_a_hundred(
    passed: int, students: int, expected: int
) -> None:
    assert pass_rate_percent(passed, students) == expected


def test_no_single_attempt_can_exceed_the_whole() -> None:
    for percent in attempt_percents(year()):
        assert 0 <= percent <= 100


def test_the_missing_candidates_are_counted_rather_than_hidden() -> None:
    """92 sat, 90 passed. The 2 are why the percentages fall short of 100."""
    assert not_passed(year()) == 2
    assert sum(attempt_percents(year())) < 100


def test_a_cohort_where_everyone_passed_leaves_nobody_behind() -> None:
    assert not_passed(year(students=90)) == 0


def test_a_cohort_whose_columns_exceed_its_headcount_reports_nobody_left() -> None:
    """A data entry slip must not print "minus two people still waiting"."""
    assert not_passed(year(students=10)) == 0


def test_the_mean_number_of_attempts_is_over_those_who_passed() -> None:
    """(68 + 32 + 9 + 12) / 90 = 1.3."""
    assert average_attempts(year()) == 1.3


def test_a_cohort_where_nobody_has_passed_has_no_mean() -> None:
    """Not zero: a mean over an empty set does not exist.

    Printing 0,0 would claim everybody passed without sitting the exam.
    """
    assert average_attempts(year(passed_1st=0, passed_2nd=0, passed_3rd=0, passed_4th=0)) is None


# --------------------------------------------------------------------------
# the model


def test_a_year_is_unique() -> None:
    PassRate.objects.create(year=2025, students=10, passed_1st=8)
    with pytest.raises(Exception):  # noqa: B017, PT011 — IntegrityError under any backend
        PassRate.objects.create(year=2025, students=20, passed_1st=15)


def test_years_come_newest_first() -> None:
    for value in (2021, 2025, 2019):
        PassRate.objects.create(year=value, students=10, passed_1st=8)

    assert list(PassRate.objects.values_list("year", flat=True)) == [2025, 2021, 2019]


def test_an_unpublished_year_is_not_offered_to_a_page(published: PassRate) -> None:
    from apps.core.selectors import latest_pass_rate, published_pass_rates

    PassRate.objects.create(year=2026, students=5, passed_1st=5, is_published=False)

    assert latest_pass_rate() == published
    assert list(published_pass_rates()) == [published]


def test_there_is_no_latest_year_before_the_first_one(client: Client) -> None:
    from apps.core.selectors import latest_pass_rate

    assert latest_pass_rate() is None


# --------------------------------------------------------------------------
# the page


def test_the_route_matches_the_url_map() -> None:
    """tech.md section 5."""
    assert reverse("core:pass_rates") == "/zdawalnosc/"


def test_the_page_leads_with_the_figure(client: Client, published: PassRate) -> None:
    body = body_of(client, "/zdawalnosc/")

    assert "74%" in body
    assert len(re.findall(r"<h1[ >]", body)) == 1


def test_the_page_prints_counts_beside_every_percentage(
    client: Client, published: PassRate
) -> None:
    """A percentage a reader cannot check against a headcount is a slogan."""
    body = body_of(client, "/zdawalnosc/")

    for count in ("68", "16", "92"):
        assert f">{count}<" in body


def test_the_page_explains_why_the_percentages_fall_short(
    client: Client, published: PassRate
) -> None:
    """Two candidates without a licence is the reason, and the reader gets it."""
    assert "prawa jazdy jeszcze nie ma" in body_of(client, "/zdawalnosc/")


def test_the_page_renders_before_the_first_year_is_confirmed(client: Client) -> None:
    """A database seeded an hour ago still has to give a page that reads."""
    notify_site()

    body = body_of(client, "/zdawalnosc/")

    assert "691 570 489" in body
    assert len(re.findall(r"<h1[ >]", body)) == 1


def test_the_home_page_carries_the_figure_above_the_fold(
    client: Client, published: PassRate
) -> None:
    """tech.md section 1: the whole pitch collapses if this is not on screen."""
    body = body_of(client, "/")

    assert "74%" in body
    assert reverse("core:pass_rates") in body


# --------------------------------------------------------------------------
# the markup, which is where a wrong number becomes a penalty


def jsonld(body: str) -> list[dict]:
    return [
        json.loads(found)
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]


def test_no_aggregate_rating_without_a_single_verifiable_review(
    client: Client, published: PassRate
) -> None:
    """The school's "96% bardzo dobrych" has no source, so it is not markup.

    An unverifiable rating is a manual action, not a rich result. This is the
    test that keeps somebody from "just adding the stars".
    """
    body = body_of(client, "/zdawalnosc/")

    assert "aggregateRating" not in body
    for block in jsonld(body):
        assert "aggregateRating" not in json.dumps(block)


def test_an_unpublished_review_does_not_earn_a_rating(client: Client, published: PassRate) -> None:
    Testimonial.objects.create(
        author_name="Anna K.",
        rating=5,
        text="Zdałam.",
        is_published=False,
        source_url="https://example.com/1",
    )

    assert "aggregateRating" not in body_of(client, "/zdawalnosc/")


def test_a_review_with_no_source_does_not_earn_a_rating(
    client: Client, published: PassRate
) -> None:
    """tech.md 4.7: a testimonial nobody can check is indistinguishable from one
    we made up, so it is excluded before it can reach the markup."""
    for number in range(2):
        Testimonial.objects.create(
            author_name=f"Anna {number}",
            rating=5,
            text="Zdałam.",
            is_published=True,
            source_url="",
        )

    assert "aggregateRating" not in body_of(client, "/zdawalnosc/")


def test_verifiable_reviews_do_earn_a_rating(client: Client, published: PassRate) -> None:
    for number, rating in enumerate((5, 4)):
        Testimonial.objects.create(
            author_name=f"Anna {number}",
            rating=rating,
            text="Zdałam.",
            is_published=True,
            source_url=f"https://example.com/{number}",
        )

    blocks = [
        block for block in jsonld(body_of(client, "/zdawalnosc/")) if "aggregateRating" in block
    ]

    assert len(blocks) == 1
    rating = blocks[0]["aggregateRating"]
    assert rating["ratingValue"] == 4.5
    assert rating["reviewCount"] == 2


def test_the_rating_counts_only_what_is_on_the_page(client: Client, published: PassRate) -> None:
    """Marking up reviews a reader cannot see is what the guideline calls
    hidden content, and it costs the rich result outright."""
    for number in range(2):
        Testimonial.objects.create(
            author_name=f"Anna {number}",
            rating=5,
            text=f"Opinia numer {number}.",
            is_published=True,
            source_url=f"https://example.com/{number}",
        )
    Testimonial.objects.create(
        author_name="Ukryta",
        rating=1,
        text="Nie widać mnie.",
        is_published=False,
        source_url="https://example.com/hidden",
    )

    body = body_of(client, "/zdawalnosc/")
    block = next(item for item in jsonld(body) if "aggregateRating" in item)

    assert block["aggregateRating"]["reviewCount"] == 2
    assert "Nie widać mnie" not in body
