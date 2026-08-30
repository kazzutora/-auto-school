"""Price page layout, DEV.md S2.1.

The acceptance criterion is about a 320px screen, the narrowest phone still in
use. Only a browser can measure whether the page moves sideways.
"""

from collections.abc import Iterator
from decimal import Decimal

import pytest
from playwright.sync_api import Browser, Page

from apps.courses.models import Course, PriceItem

pytestmark = pytest.mark.django_db

NARROW = {"width": 320, "height": 720}


@pytest.fixture
def narrow_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=NARROW)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def offer() -> None:
    Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-b",
        code="B",
        title="Kategoria B prawa jazdy z egzaminem wewnętrznym",
        price_gross=Decimal("3200"),
        price_note="cena od, płatność w dwóch ratach bez odsetek",
    )
    Course.objects.create(
        kind=Course.Kind.PROFESSIONAL, slug="adr", code="ADR", title="Kurs ADR", price_gross=None
    )
    PriceItem.objects.create(
        title="Jazda doszkalająca kategorii B poza godzinami kursu",
        group="Jazdy doszkalające",
        unit="za godzinę",
        note="minimum dwie godziny",
        price_gross=Decimal("120"),
    )


def test_the_page_does_not_move_sideways_at_320px(
    live_server, narrow_page: Page, offer: None
) -> None:
    narrow_page.goto(f"{live_server.url}/cennik/")

    overflow = narrow_page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"page scrolls sideways by {overflow}px"


def test_a_price_row_keeps_its_figure_beside_its_name(
    live_server, narrow_page: Page, offer: None
) -> None:
    """X1 point 2 replaced the table, so there is no table to scroll.

    The three column table put a nearly empty "Uwagi" column at 87% of the page
    and the figure at 63%, which left 700px between a service and its price. A
    row cannot do that — but it can wrap badly at 320px, and the one thing that
    must not happen is the price ending up on its own line away from what it is
    the price of.
    """
    narrow_page.goto(f"{live_server.url}/cennik/")
    narrow_page.wait_for_selector("h1")

    rows = narrow_page.locator("main li:has(.data), main li:has-text('wycena')")
    assert rows.count() >= 1, "the price list has no rows"

    overflow = narrow_page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"the price list pushes the page {overflow}px sideways"

    # Name and figure share a line: the figure's top is inside the name's line
    # box, not below it.
    apart = narrow_page.evaluate(
        """() => {
            const rows = [...document.querySelectorAll('main li')];
            const bad = [];
            for (const row of rows) {
                const name = row.querySelector('span.font-semibold');
                const price = [...row.querySelectorAll('span')]
                    .find(s => /zł|wycena/.test(s.textContent) && s !== name);
                if (!name || !price) continue;
                const a = name.getBoundingClientRect(), b = price.getBoundingClientRect();
                if (b.top >= a.bottom) bad.push(name.textContent.trim().slice(0, 30));
            }
            return bad;
        }"""
    )
    assert not apart, f"the price left its name behind on: {apart}"


def test_the_price_and_the_ask_block_are_both_visible(
    live_server, narrow_page: Page, offer: None
) -> None:
    narrow_page.goto(f"{live_server.url}/cennik/")
    text = narrow_page.locator("body").inner_text()

    assert "3 200,00" in text.replace(" ", " ")
    assert "Zapytaj o cenę" in text

    # No priced row may read as zero. Checked cell by cell: "0,00" also
    # occurs inside a legitimate "3 200,00".
    cells = narrow_page.locator("td")
    amounts = [cells.nth(i).inner_text().strip() for i in range(cells.count())]
    assert not [value for value in amounts if value.replace(" ", " ") == "0,00 zł"]
