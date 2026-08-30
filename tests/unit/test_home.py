"""The home page, FRONTEND.md A.9 and F3.

The composition itself is not asserted line by line — that is what the design
contract is for. What is asserted here is every rule A.9 states as a rule: the
sections that decide whether they exist at all, the SEO contract, and the empty
data cases, because those are the ones a later change quietly breaks.
"""

import re
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import SiteSettings
from apps.courses.models import Course, CourseIntake
from apps.links.models import Faq
from apps.reviews.models import Testimonial

pytestmark = pytest.mark.django_db


@pytest.fixture
def site() -> SiteSettings:
    row = SiteSettings.get_solo()
    row.legal_name = "OKiDZ Adam Nawrocki, Mariola Nawrocka S.C."
    row.short_name = "OSK Nawrocki"
    row.street = "ul. Zielona 45"
    row.postal_code = "98-300"
    row.city = "Wieluń"
    row.nip = "8321916014"
    row.email = "biuro@example.com"
    row.phone_primary = "43 843 29 11"
    row.founded_year = 1996
    row.map_lat = Decimal("51.220600")
    row.map_lng = Decimal("18.569700")
    row.save()
    return row


def make_course(**kwargs: object) -> Course:
    defaults: dict[str, object] = {
        "kind": Course.Kind.LICENSE,
        "slug": "kat-b",
        "code": "B",
        "title": "Kategoria B",
        "is_active": True,
    }
    defaults.update(kwargs)
    return Course.objects.create(**defaults)


def make_intake(course: Course, **kwargs: object) -> CourseIntake:
    defaults: dict[str, object] = {
        "course": course,
        "start_date": date.today() + timedelta(days=14),
        "mode": CourseIntake.Mode.STATIONARY,
        "language": "pl",
        "status": CourseIntake.Status.OPEN,
    }
    defaults.update(kwargs)
    return CourseIntake.objects.create(**defaults)


def body(client: Client) -> str:
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    return response.content.decode()


def test_the_home_page_answers(client: Client, site: SiteSettings) -> None:
    assert client.get(reverse("core:home")).status_code == 200


def test_it_carries_exactly_one_h1(client: Client, site: SiteSettings) -> None:
    """A.3: one h1 per page, and on this one it is the hero."""
    html = body(client)
    headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.S)
    assert len(headings) == 1
    assert "Wieluniu" in headings[0]


def test_the_title_and_description_are_filled(client: Client, site: SiteSettings) -> None:
    """tech.md section 8: the suffix is fixed and the description has a limit."""
    html = body(client)
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    description = re.search(r'<meta name="description" content="([^"]*)"', html)
    assert title and title.group(1).strip()
    assert title.group(1).strip().endswith("OSK Nawrocki Wieluń")
    assert "Prawo jazdy" in title.group(1)
    assert description and description.group(1).strip()
    assert len(description.group(1)) <= 170


def test_it_ships_the_two_json_ld_blocks(client: Client, site: SiteSettings) -> None:
    """DrivingSchool on every page, FAQPage because this one lists questions."""
    Faq.objects.create(question="Ile trwa kurs?", answer="Około trzech miesięcy.")
    html = body(client)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    types = []
    for block in blocks:
        import json

        types.append(json.loads(block)["@type"])
    assert "DrivingSchool" in types
    assert "FAQPage" in types


def test_the_terms_section_is_absent_without_a_joinable_group(
    client: Client, site: SiteSettings
) -> None:
    """A.9 point 3, in as many words: the section does not render at all."""
    assert CourseIntake.objects.count() == 0
    assert 'id="terminy"' not in body(client)


def test_the_terms_section_appears_once_there_is_one(client: Client, site: SiteSettings) -> None:
    make_intake(make_course())
    assert 'id="terminy"' in body(client)


def test_a_full_group_does_not_take_one_of_the_three_rows(
    client: Client, site: SiteSettings
) -> None:
    """Every row carries a Zapisz się button, so a group nobody can join is not
    a row: A.9 point 3 limits the list to open and planned."""
    make_intake(make_course(), status=CourseIntake.Status.FULL)
    assert 'id="terminy"' not in body(client)


def test_the_reviews_section_is_absent_below_two(client: Client, site: SiteSettings) -> None:
    """A.9 point 7: fewer than two published reviews and there is no strip."""
    assert 'id="opinie"' not in body(client)

    Testimonial.objects.create(
        author_name="Anna K.",
        rating=5,
        text="Zdałam za pierwszym razem.",
        source_url="https://example.com/1",
        is_published=True,
    )
    assert 'id="opinie"' not in body(client), "one review is not a strip"

    Testimonial.objects.create(
        author_name="Piotr M.",
        rating=5,
        text="Instruktor tłumaczy spokojnie.",
        source_url="https://example.com/2",
        is_published=True,
    )
    assert 'id="opinie"' in body(client)


def test_a_review_with_nowhere_to_check_it_never_counts(client: Client, site: SiteSettings) -> None:
    """A.9 point 7 forbids invented reviews, and one nobody can verify is
    indistinguishable from one."""
    for index in range(3):
        Testimonial.objects.create(
            author_name=f"Ktoś {index}",
            rating=5,
            text="Polecam.",
            source_url="",
            is_published=True,
        )
    assert 'id="opinie"' not in body(client)


def test_a_course_without_a_price_says_so(client: Client, site: SiteSettings) -> None:
    """A.9 point 2: cena na zapytanie, never an empty line where a number goes."""
    make_course(price_gross=None)
    html = body(client)
    assert "na zapytanie" in html


def test_a_course_with_a_price_prints_it(client: Client, site: SiteSettings) -> None:
    make_course(price_gross=Decimal("3200"))
    assert "od 3200 zł" in body(client)


def test_the_page_survives_an_empty_database(client: Client, site: SiteSettings) -> None:
    """No courses, no groups, no reviews, no questions: still a page."""
    html = body(client)
    assert "<h1" in html
    for absent in ('id="terminy"', 'id="opinie"', 'id="faq"'):
        assert absent not in html
    # The hero and the way to reach a human are never conditional.
    assert 'href="tel:43843291' in html


def test_the_map_coordinates_are_not_localised(client: Client, site: SiteSettings) -> None:
    """The polish locale writes a decimal with a comma and parseFloat stops at
    it, which would put the marker in the Atlantic."""
    html = body(client)
    assert 'data-lat="51.220600"' in html
    assert 'data-lng="18.569700"' in html
