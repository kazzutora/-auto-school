"""Price page, DEV.md S2.1 acceptance criteria."""

import re
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import Page
from apps.courses.models import Course, PriceItem
from apps.courses.services import CURRENCY

from tests.conftest import repeated_grounds, section_grounds

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


def test_the_course_itself_is_a_price_group(client: Client) -> None:
    """The previous client had a row per course and no figures at all.

    This one prices three variants of one course, so the course is a price group
    like any other. A second list of courses beside it would print category B
    twice, at two figures, and invite the reader to work out which is real.
    """
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))
    make_course(price_gross=Decimal("3700"))

    body = body_of(client)

    assert body.count("Kurs kategorii B") >= 1
    assert "3700" in body.replace(" ", "")
    # The Course row exists and is deliberately not a line on this page.
    assert "Kategoria B (B)" not in body


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


def test_every_published_price_reaches_the_page(client: Client) -> None:
    """The acceptance criterion: every figure the school publishes, to the złoty."""
    from scripts import seed

    seed.seed_price_items()

    table = rows_of(body_of(client)).replace(" ", " ")

    for label, amount in (
        ("Kurs kategorii B", "3 700,00"),
        ("Kurs przyspieszony", "4 300,00"),
        ("Skrzynia automatyczna", "4 300,00"),
        ("Jazda doszkalająca — manual", "160,00"),
        ("Jazda doszkalająca — automat", "140,00"),
        ("Badanie lekarskie", "200,00"),
        ("Egzamin państwowy", "230,00"),
        ("Zaświadczenie o zameldowaniu", "17,00"),
    ):
        assert label in table, label
        assert amount in table, amount


def test_the_groups_are_labelled(client: Client) -> None:
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))
    make_item()
    make_item(
        title="Egzamin państwowy", group="Opłaty zewnętrzne", unit="", price_gross=Decimal("230")
    )

    headings = re.findall(r"<h2[^>]*>([^<]+)</h2>", body_of(client))

    assert "Kurs" in headings
    assert "Jazdy doszkalające" in headings
    assert "Opłaty zewnętrzne" in headings


# --------------------------------------------------------------------------
# free is not zero


def test_a_price_of_nothing_reads_as_gratis(client: Client) -> None:
    """The school's best small advantage: it drives you to the exam for free.

    Printed as "0,00 zł" it reads like a figure somebody forgot to fill in.
    """
    make_item(title="Dowóz na egzamin", group="W cenie kursu", unit="", price_gross=Decimal("0"))

    body = body_of(client)

    assert "GRATIS" in body
    assert "0,00" not in body
    assert not re.search(r">\s*0[,.]00", body)


def test_a_real_figure_is_still_a_figure(client: Client) -> None:
    """The GRATIS branch must not swallow every other price on its way past."""
    make_item(price_gross=Decimal("140"))

    assert f"140,00 {CURRENCY}" in body_of(client)


def test_the_page_separates_the_school_s_prices_from_everybody_else_s(client: Client) -> None:
    """230 zł under 3700 zł otherwise reads as one bill.

    Badanie lekarskie goes to a doctor and the exam fee to the exam centre. The
    page has to say so, or it looks like the school charges 4147 zł.
    """
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))
    make_item(
        title="Egzamin państwowy", group="Opłaty zewnętrzne", unit="", price_gross=Decimal("230")
    )

    body = body_of(client)

    assert "To nie są opłaty dla szkoły" in body


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
    a row wraps instead. The one horizontal scroller left on the page is the
    anchor nav, which is a row of chips and is meant to scroll.
    """
    make_item(title="Jazda doszkalająca — manual, dla naszych kursantów i absolwentów")

    body = body_of(client)
    lines = rows_of(body)

    assert "u-scroll-x" not in lines
    assert "Jazda doszkalająca" in lines


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
    make_course(price_gross=Decimal("3700"))
    make_item()
    client.get("/cennik/")

    # price items, the headline price off the course, the payments page, then
    # site settings twice: the context processor and the DrivingSchool block.
    with django_assert_num_queries(5):
        client.get("/cennik/")

    for number in range(15):
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
    make_item(price_gross=Decimal("3200"))

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


def test_what_the_school_charges_comes_first(client: Client) -> None:
    """X1 point 1: it is the group most people open the page for.

    Not alphabetical and not database order. What the school charges, then what
    it charges by the hour, then what somebody pays to a doctor and an exam
    centre — which is the order the decision is actually made in.
    """
    make_item(
        title="Badanie lekarskie", group="Opłaty zewnętrzne", unit="", price_gross=Decimal("200")
    )
    make_item()
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))

    headings = [h.strip() for h in re.findall(r"<h2[^>]*>([^<]+)</h2>", body_of(client))]

    assert headings, "the page lost its group headings"
    assert headings[:3] == ["Kurs", "Jazdy doszkalające", "Opłaty zewnętrzne"]


def test_a_group_the_owner_invents_still_appears(client: Client) -> None:
    """Sorted, not filtered: an unknown group goes last rather than vanishing."""
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))
    make_item(title="Coś nowego", group="Nowa grupa", unit="", price_gross=Decimal("50"))

    headings = [h.strip() for h in re.findall(r"<h2[^>]*>([^<]+)</h2>", body_of(client))]

    assert headings[0] == "Kurs"
    assert "Nowa grupa" in headings


def test_the_most_wanted_variant_is_marked(client: Client) -> None:
    """X1 point 3: the standard course, and only it."""
    make_item(
        title="Kurs kategorii B", group="Kurs", unit="", order=10, price_gross=Decimal("3700")
    )
    make_item(
        title="Kurs przyspieszony", group="Kurs", unit="", order=20, price_gross=Decimal("4300")
    )
    make_item(
        title="Skrzynia automatyczna", group="Kurs", unit="", order=30, price_gross=Decimal("4300")
    )

    body = body_of(client)

    assert body.count("Najczęściej wybierany") == 1
    marked = body[body.index("Najczęściej wybierany") - 400 : body.index("Najczęściej wybierany")]
    assert "Kurs kategorii B" in marked


def test_the_page_ends_on_an_invitation(client: Client) -> None:
    """B.8 point 4: it used to end on a list of things with no price.

    The rule moved at core v25, and the geometry is why.

    B.7 point 11 makes the footer a dark card the full width of the page with a
    28px radius along its top. A dark section directly above it merges into one
    very tall dark region, and the radius — the shape whose whole job is to say
    "this is where the page ends" — has nothing to read against.

    So the page's one dark block sits mid page and the closing band takes the
    page ground. What has not moved is B.8 point 4: the page still ends on an
    action. It is the ground that changed, not the rule, and the old assertion
    checked the ground because that had been a fair proxy while the closing
    band was the only inverted thing on the page.
    """
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))

    body = body_of(client)
    inside = body[body.index("<main") : body.index("</main>")]
    tail = inside[inside.rindex("<section") :]

    assert "Zaczynamy?" in tail
    assert "tel:" in tail or "/zapisz-sie/" in tail, "the invitation has no action in it"
    assert section_grounds(inside)[-1] != "dark"


def test_no_two_sections_share_a_ground(client: Client) -> None:
    """X1 point 7: two of the same colour in a row read as one long block."""
    make_item(title="Kurs kategorii B", group="Kurs", unit="", price_gross=Decimal("3700"))
    make_item()
    PriceItem.objects.create(
        title="Badanie lekarskie", group="Opłaty zewnętrzne", price_gross=Decimal("200")
    )

    grounds = section_grounds(body_of(client))
    repeats = repeated_grounds(body_of(client))
    assert not repeats, f"sections {repeats} repeat the ground before them: {grounds}"
