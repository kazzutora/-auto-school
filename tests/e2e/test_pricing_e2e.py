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


def test_a_wide_table_scrolls_inside_its_own_container(
    live_server, narrow_page: Page, offer: None
) -> None:
    """The table may overflow. The document may not."""
    narrow_page.goto(f"{live_server.url}/cennik/")

    scrollers = narrow_page.locator("div.overflow-x-auto:has(table)")
    assert scrollers.count() >= 1

    for index in range(scrollers.count()):
        box = scrollers.nth(index).bounding_box()
        assert box is not None
        assert box["width"] <= NARROW["width"], "a table container is wider than the screen"


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
