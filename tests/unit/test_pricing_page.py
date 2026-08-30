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
    """Every price line on the page.

    X1 replaced the three column table with rows, so there is no tbody to slice
    any more — the lines are list items carrying a c-price-row.
    """
    return "".join(re.findall(r"<li[^>]*>(.*?)</li>", body, re.S))


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


def test_a_course_without_a_price_is_in_the_list_all_the_same(client: Client) -> None:
    """Reversed on purpose, X1 point 1.

    This test used to assert the opposite, and the opposite was the worst thing
    the page did: the licence categories have no price_gross, so they were
    filtered out of every group, the first group came out empty and was
    dropped, and someone arriving to learn what category B costs found no line
    about category B anywhere.
    """
    make_course(price_gross=None)

    body = body_of(client)

    assert "Kategoria B" in body
    assert "wycena indywidualna" in body


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


def test_a_long_name_does_not_push_the_page_sideways(client: Client) -> None:
    """There is no table to scroll now, X1 point 2.

    The three column table needed its own scroll box because it could not fit;
    a row wraps instead, and what has to hold is that nothing sticks out.
    """
    make_course(title="Kwalifikacja wstępna przyspieszona dla kierowców zawodowych")

    body = body_of(client)
    assert "u-scroll-x" not in body
    assert "Kwalifikacja wstępna" in rows_of(body)


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

    # active courses, price items, payments page, then site settings twice:
    # the context processor and the DrivingSchool block. One fewer than before
    # — priced and unpriced are one query now, not two.
    with django_assert_num_queries(5):
        client.get("/cennik/")

    for number in range(15):
        make_course(
            slug=f"kat-{number}", code=str(number), title=f"K{number}", price_gross=Decimal("100")
        )
        make_item(title=f"Usługa {number}")

    with django_assert_num_queries(5):
        client.get("/cennik/")


# --------------------------------------------------------------------------
# how the table is built, FRONTEND.md F6


def test_the_figures_are_still_set_as_figures(client: Client) -> None:
    """A.5: the data face and tabular numerals, wherever the figure sits.

    The column moved out of a table cell and into the end of a row, but the
    reason for the mono is unchanged — a proportional 1 is narrower than a 0
    and the place values wander.
    """
    make_course(price_gross=Decimal("3200"))
    make_item()

    for row in re.findall(r'<span class="data[^"]*">[^<]*zł[^<]*</span>', body_of(client)):
        assert "data" in row, row


def test_every_line_joins_its_name_to_its_figure(client: Client) -> None:
    """X1 point 2 and finding A.2 number 10.

    The old table put the figure at 63% of a 1240px page and a nearly empty
    "Uwagi" column at 87%, so 700px of nothing separated a service from its
    price. A row with a leader between the two replaced all three columns.
    """
    make_course(price_gross=Decimal("3200"))

    body = body_of(client)
    assert "<table" not in body
    assert "Uwagi" not in body
    assert "border-dotted" in body, "the leader joining name to figure is gone"


def test_the_table_never_stripes_its_rows(client: Client) -> None:
    """A.5 parts rows with a hairline and nothing else."""
    make_course(price_gross=Decimal("3200"))
    body = body_of(client)
    assert "odd:" not in body
    assert "even:" not in body
    assert "divide-y" not in body


# --------------------------------------------------------------------------
# FRONTEND_FIXES.md X1


def test_a_category_without_a_price_still_has_a_line(client: Client) -> None:
    """X1 point 1, and the worst finding of the review.

    The groups were built from priced courses only, so the licence categories —
    which have no price_gross yet — vanished from the page entirely. Somebody
    arriving to find out what category B costs found no line about category B
    at all, only a block at the very bottom saying some things are quoted
    individually.
    """
    make_course(slug="kat-b", code="B", title="Kategoria B", price_gross=None)

    body = body_of(client)
    assert "Kategoria B (B)" in body
    assert "wycena indywidualna" in body


def test_the_licence_categories_come_first(client: Client) -> None:
    """X1 point 1: it is the group most people open the page for."""
    make_course(slug="kat-b", code="B", title="Kategoria B", price_gross=None)
    PriceItem.objects.create(title="Badanie", group="Badania", price_gross=Decimal("150"))

    headings = re.findall(r"<h2[^>]*>([^<]+)</h2>", body_of(client))
    assert headings, "the page lost its group headings"
    assert headings[0].strip() == "Kategorie prawa jazdy"


def test_the_most_wanted_category_is_marked(client: Client) -> None:
    """X1 point 3."""
    make_course(slug="kat-b", code="B", title="Kategoria B", price_gross=None)
    make_course(slug="kat-a", code="A", title="Kategoria A", price_gross=None)

    body = body_of(client)
    assert body.count("Najczęściej wybierany") == 1
    marked = body[body.index("Najczęściej wybierany") - 400 : body.index("Najczęściej wybierany")]
    assert "Kategoria B" in marked


def test_the_page_ends_on_an_invitation(client: Client) -> None:
    """X1 point 9: it used to end on a list of things with no price."""
    make_course(slug="kat-b", code="B", title="Kategoria B", price_gross=None)

    body = body_of(client)
    tail = body[body.rindex("</main>") - 2000 : body.rindex("</main>")]
    assert "Nie wiesz, którą kategorię wybrać?" in tail
    assert "u-ground-ink" in tail


def test_no_two_sections_share_a_ground(client: Client) -> None:
    """X1 point 7: two of the same colour in a row read as one long block."""
    for code in ("B", "A", "C"):
        make_course(slug=f"kat-{code.lower()}", code=code, title=f"Kategoria {code}")
    PriceItem.objects.create(title="Badanie", group="Badania", price_gross=Decimal("150"))

    sections = re.findall(r'<section[^>]*class="([^"]*)"', body_of(client))
    grounds = [
        "muted" if "bg-paper-50" in cls else "ink" if "u-ground-ink" in cls else "paper"
        for cls in sections
    ]
    repeats = [i for i in range(1, len(grounds)) if grounds[i] == grounds[i - 1]]
    assert not repeats, f"sections {repeats} repeat the ground before them: {grounds}"
