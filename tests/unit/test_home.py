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
    row.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    row.short_name = "OSK Ostrycharz"
    row.street = "ul. Asnyka 7"
    row.postal_code = "98-300"
    row.city = "Wieluń"
    row.nip = ""
    row.email = "biuro@example.com"
    row.phone_primary = "691 570 489"
    row.founded_year = None
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
    assert title.group(1).strip().endswith("OSK Ostrycharz Wieluń")
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


def test_the_variants_section_is_absent_until_the_prices_are_in(
    client: Client, site: SiteSettings
) -> None:
    """A section with nothing to say does not render at all, A.9."""
    assert 'id="kurs"' not in body(client)


def test_the_variants_section_appears_once_there_are_prices(
    client: Client, site: SiteSettings
) -> None:
    from apps.courses.models import PriceItem

    PriceItem.objects.create(
        title="Kurs kategorii B", group="Kurs", price_gross=Decimal("3700"), is_active=True
    )

    body_text = body(client)

    assert 'id="kurs"' in body_text
    assert "Kurs kategorii B" in body_text


def test_a_free_extra_does_not_become_a_course_card(client: Client, site: SiteSettings) -> None:
    """ "Dowóz na egzamin — GRATIS" is priced at zero and lives in its own group.

    Without the exclusion it turned up as a fourth card offering a 0 zł course,
    which is neither what it is nor something anybody can buy.
    """
    from apps.courses.models import PriceItem

    PriceItem.objects.create(
        title="Kurs kategorii B", group="Kurs", price_gross=Decimal("3700"), is_active=True
    )
    PriceItem.objects.create(
        title="Dowóz na egzamin", group="Kurs", price_gross=Decimal("0"), is_active=True
    )

    body_text = body(client)

    assert body_text.count("Dowóz na egzamin</h3>") == 0


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


def test_the_hero_leaves_the_course_price_to_the_price_list(
    client: Client, site: SiteSettings
) -> None:
    """The owner took the lead and the price out of the hero: on the bare
    sunset they could not be read."""
    make_course(price_gross=Decimal("3700"))

    assert "3700 zł" not in body(client)


def test_the_hero_says_nothing_about_price_before_there_is_one(
    client: Client, site: SiteSettings
) -> None:
    """Never an empty slot where a number goes, and never a zero standing in."""
    make_course(price_gross=None)

    html = body(client)

    assert not re.search(r">\s*0\s*zł", html)
    assert "None" not in html


def test_the_page_survives_an_empty_database(client: Client, site: SiteSettings) -> None:
    """No course, no prices, no results, no reviews, no questions: still a page."""
    html = body(client)
    assert "<h1" in html
    for absent in ('id="kurs"', 'id="opinie"', 'id="faq"', 'id="wideo"'):
        assert absent not in html
    # The hero and the way to reach a human are never conditional.
    assert 'href="tel:691570489"' in html


def test_the_map_coordinates_are_not_localised(client: Client, site: SiteSettings) -> None:
    """The polish locale writes a decimal with a comma and parseFloat stops at
    it, which would put the marker in the Atlantic."""
    html = body(client)
    assert 'data-lat="51.220600"' in html
    assert 'data-lng="18.569700"' in html
