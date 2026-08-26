"""Useful links layout, DEV.md S7.1.

A long government url is the classic way a card pushes a page sideways, and
only a browser can measure whether the wrapping holds.
"""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page

from apps.links.models import UsefulLink

pytestmark = pytest.mark.django_db

NARROW = {"width": 320, "height": 720}

LONG_URL = (
    "https://www.gov.pl/web/infrastruktura/testy-na-prawo-jazdy-kategorii-b"
    "-pytania-egzaminacyjne-i-odpowiedzi-2026"
)


@pytest.fixture
def narrow_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=NARROW)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def links() -> None:
    UsefulLink.objects.create(
        group=UsefulLink.Group.EXAM,
        title="Info-Car",
        description="Rezerwacja terminu egzaminu państwowego.",
        url="https://info-car.pl/",
    )
    UsefulLink.objects.create(
        group=UsefulLink.Group.TESTS,
        title="Testy na prawo jazdy",
        description="Oficjalna baza pytań egzaminacyjnych.",
        url=LONG_URL,
    )


def test_a_long_url_does_not_push_the_page_sideways(
    live_server, narrow_page: Page, links: None
) -> None:
    narrow_page.goto(f"{live_server.url}/przydatne-linki/")

    widest = narrow_page.evaluate(
        """() => Math.max(...Array.from(document.querySelectorAll('main *'))
               .map(node => node.getBoundingClientRect().right))"""
    )

    assert widest <= NARROW["width"]


def test_the_cards_are_real_links(live_server, narrow_page: Page, links: None) -> None:
    """The whole card is the target, not just the title."""
    narrow_page.goto(f"{live_server.url}/przydatne-linki/")

    card = narrow_page.get_by_role("link", name="Info-Car")

    assert card.get_attribute("href") == "https://info-car.pl/"
    assert card.get_attribute("target") == "_blank"
    assert card.get_attribute("rel") == "noopener noreferrer"
