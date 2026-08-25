"""Price page, DEV.md S2.1 acceptance criteria."""

import re
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import Page
from apps.courses.models import Course, PriceItem
from apps.courses.services import CURRENCY

pytestmark = pytest.mark.django_db


def make_course(**overrides: object) -> Course:
    values: dict = {
        "kind": Course.Kind.LICENSE,
        "slug": "kat-b",
        "code": "B",
        "title": "Kategoria B",
        "is_active": True,
    }
    values.update(overrides)
    return Course.objects.create(**values)


def make_item(**overrides: object) -> PriceItem:
    values: dict = {
        "title": "Jazda doszkalająca",
        "group": "Jazdy doszkalające",
        "unit": "za godzinę",
        "price_gross": Decimal("120"),
        "is_active": True,
    }
    values.update(overrides)
    return PriceItem.objects.create(**values)


def body_of(client: Client) -> str:
    response = client.get(reverse("courses:pricing"))
    assert response.status_code == 200
    return response.content.decode()


def rows_of(body: str) -> str:
    """Everything inside the tables, so the tiles below do not confuse a check."""
    return "".join(re.findall(r"<tbody[^>]*>(.*?)</tbody>", body, re.S))


def test_the_route_matches_the_url_map() -> None:
    """tech.md sections 5 and 7."""
    assert reverse("courses:pricing") == "/cennik/"


def test_the_page_answers(client: Client) -> None:
    assert client.get("/cennik/").status_code == 200


def test_exactly_one_h1(client: Client) -> None:
    make_course(price_gross=Decimal("3200"))
    assert len(re.findall(r"<h1[ >]", body_of(client))) == 1


# --------------------------------------------------------------------------
# what lands in the table


def test_a_priced_course_is_in_the_table(client: Client) -> None:
    make_course(price_gross=Decimal("3200"), price_note="cena od")

    table = rows_of(body_of(client))

    assert "Kategoria B" in table
    assert "200" in table
    assert "cena od" in table


def test_an_active_price_item_is_in_the_table(client: Client) -> None:
    make_item()

    table = rows_of(body_of(client))

    assert "Jazda doszkalająca" in table
    assert "za godzinę" in table


def test_an_inactive_price_item_is_not_rendered(client: Client) -> None:
    make_item(title="Ukryta usługa", is_active=False)

    assert "Ukryta usługa" not in body_of(client)


def test_an_inactive_course_is_not_rendered(client: Client) -> None:
    make_course(title="Ukryty kurs", price_gross=Decimal("100"), is_active=False)

    assert "Ukryty kurs" not in body_of(client)


def test_every_active_priced_record_appears(client: Client) -> None:
    """The acceptance criterion, checked as a whole rather than one row at a time."""
    make_course(price_gross=Decimal("3200"))
    make_course(slug="kat-c", code="C", title="Kategoria C", price_gross=Decimal("5000"))
    make_course(
        kind=Course.Kind.OPERATOR,
        slug="wozki",
        code="",
        title="Wózki",
        price_gross=Decimal("800"),
    )
    make_item()
    make_item(title="Egzamin wewnętrzny", group="Egzaminy", price_gross=Decimal("50"))

    table = rows_of(body_of(client))

    expected = (
        "Kategoria B",
        "Kategoria C",
        "Wózki",
        "Jazda doszkalająca",
        "Egzamin wewnętrzny",
    )
    for label in expected:
        assert label in table, label


def test_the_groups_are_labelled(client: Client) -> None:
    make_course(price_gross=Decimal("3200"))
    make_course(
        kind=Course.Kind.PROFESSIONAL,
        slug="adr",
        code="ADR",
        title="ADR",
        price_gross=Decimal("900"),
    )
    make_item()

    headings = re.findall(r"<h2[^>]*>([^<]+)</h2>", body_of(client))

    assert "Kategorie prawa jazdy" in headings
    assert "Kierowca zawodowy" in headings
    assert "Jazdy doszkalające" in headings


# --------------------------------------------------------------------------
# courses with no price


def test_a_course_without_a_price_stays_out_of_the_table(client: Client) -> None:
    make_course(price_gross=None)

    body = body_of(client)

    assert "Kategoria B" not in rows_of(body)
    assert "Cena ustalana indywidualnie" in body


def test_a_course_without_a_price_never_reads_as_zero(client: Client) -> None:
    make_course(price_gross=None)

    body = body_of(client)

    assert not re.search(r">\s*0[,.]00", body)
    assert f"0,00 {CURRENCY}" not in body
    assert "Zapytaj o cenę" in body


def test_the_individual_block_disappears_when_every_price_is_set(client: Client) -> None:
    make_course(price_gross=Decimal("3200"))

    assert "Cena ustalana indywidualnie" not in body_of(client)


# --------------------------------------------------------------------------
# payments block


def test_the_payments_block_shows_when_published(client: Client) -> None:
    Page.objects.create(
        slug="platnosci",
        title="Płatności i raty",
        body="## Raty\n\n- płatność w dwóch ratach",
        is_published=True,
    )

    body = body_of(client)

    assert "Płatności i raty" in body
    assert "<li>płatność w dwóch ratach</li>" in body


def test_the_payments_block_stays_hidden_when_unpublished(client: Client) -> None:
    Page.objects.create(slug="platnosci", title="Płatności", body="tajne", is_published=False)

    assert "tajne" not in body_of(client)


def test_no_payments_page_is_not_an_error(client: Client) -> None:
    assert client.get("/cennik/").status_code == 200


# --------------------------------------------------------------------------
# layout and seo


def test_each_table_scrolls_inside_its_own_container(client: Client) -> None:
    """A wide row must scroll in place, not push the page sideways."""
    make_course(price_gross=Decimal("3200"))
    make_item()

    body = body_of(client)
    tables = body.count("<table")

    assert tables >= 2
    assert body.count("overflow-x-auto") >= tables


@pytest.mark.seo
def test_the_page_meets_the_seo_contract(client: Client) -> None:
    make_course(price_gross=Decimal("3200"))
    body = body_of(client)

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert "Wieluń" in title
    assert re.search(r'name="description" content="(.+?)"', body).group(1).strip()
    assert 'rel="canonical"' in body
    assert '"BreadcrumbList"' in body


def test_the_price_query_count_does_not_grow_with_the_offer(
    client: Client, django_assert_num_queries
) -> None:
    make_course(price_gross=Decimal("3200"))
    make_item()
    client.get("/cennik/")

    # priced courses, unpriced courses, price items, payments page, then
    # site settings twice: the context processor and the DrivingSchool block.
    with django_assert_num_queries(6):
        client.get("/cennik/")

    for number in range(15):
        make_course(
            slug=f"kat-{number}", code=str(number), title=f"K{number}", price_gross=Decimal("100")
        )
        make_item(title=f"Usługa {number}")

    with django_assert_num_queries(6):
        client.get("/cennik/")
