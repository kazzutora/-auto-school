"""The contact page in a browser, DEV.md S4.

Three things only a browser answers: does leaflet actually draw the map, does
the page reach a third party while doing it, and are the numbers tappable on a
phone.
"""

from collections.abc import Iterator
from datetime import time
from decimal import Decimal
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page

from apps.core.models import OpeningHours, SiteSettings

pytestmark = pytest.mark.django_db

# The tiles are the one third party the map is allowed to touch, tech.md
# section 2: openstreetmap sets no cookies, which is why it beat google maps.
TILE_HOST = "tile.openstreetmap.org"


@pytest.fixture
def office() -> SiteSettings:
    site = SiteSettings.get_solo()
    site.legal_name = "OKiDZ Adam Nawrocki, Mariola Nawrocka S.C."
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "osk.adam.nawrocki@wp.pl"
    site.phone_primary = "43 843 29 11"
    site.phone_secondary = "605 065 795"
    site.phone_tertiary = "667 615 184"
    site.map_lat = Decimal("51.220600")
    site.map_lng = Decimal("18.569700")
    site.save()

    for weekday in range(5):
        OpeningHours.objects.create(
            department=OpeningHours.DEPT.OFFICE,
            weekday=weekday,
            opens=time(9, 0),
            closes=time(17, 0),
        )
    return site


@pytest.fixture
def watched_page(page: Page) -> Iterator[tuple[Page, list[str]]]:
    """The page plus every host it asks for something."""
    hosts: list[str] = []
    page.on("request", lambda request: hosts.append(urlsplit(request.url).netloc))
    yield page, hosts


def scroll_to_map(page: Page) -> None:
    """The map is built when it comes into view, not on load.

    The tiles are the only third party the site touches, so fetching them before
    anyone has scrolled to the map spends the first screen budget in A.11 on
    something nobody is looking at. Every assertion about the map therefore has
    to put it on screen first, exactly as a visitor would.
    """
    page.locator("[data-testid='map']").scroll_into_view_if_needed()


def test_the_map_draws_a_marker(live_server, office: SiteSettings, page: Page) -> None:
    page.goto(f"{live_server.url}/kontakt/")
    scroll_to_map(page)

    page.wait_for_selector("[data-testid='map'].leaflet-container")
    assert page.locator(".leaflet-marker-icon").count() == 1


def test_the_map_is_not_built_before_anyone_scrolls_to_it(
    live_server, office: SiteSettings, page: Page
) -> None:
    page.goto(f"{live_server.url}/kontakt/")
    page.wait_for_selector("h1")

    assert page.locator("[data-testid='map'].leaflet-container").count() == 0


def test_the_page_talks_to_nobody_but_the_tile_server(
    live_server, office: SiteSettings, watched_page: tuple[Page, list[str]]
) -> None:
    """The acceptance criterion: no analytics host, no google script."""
    page, hosts = watched_page
    page.goto(f"{live_server.url}/kontakt/")
    scroll_to_map(page)
    page.wait_for_selector(".leaflet-tile")

    allowed = {urlsplit(live_server.url).netloc, TILE_HOST}
    assert set(hosts) <= allowed, f"unexpected hosts: {sorted(set(hosts) - allowed)}"


def test_every_number_is_tappable_on_a_phone(live_server, office: SiteSettings, page: Page) -> None:
    """390x844, the phone the visitor arrives on, tech.md section 1."""
    page.goto(f"{live_server.url}/kontakt/")

    numbers = page.locator("[data-testid='details'] a[href^='tel:']")
    assert numbers.count() == 3

    for index in range(numbers.count()):
        link = numbers.nth(index)
        box = link.bounding_box()
        assert box is not None
        # A finger needs something to hit, not a line of text.
        assert box["height"] >= 44


def test_the_call_bar_sticks_to_the_bottom(live_server, office: SiteSettings, page: Page) -> None:
    page.goto(f"{live_server.url}/kontakt/")
    page.mouse.wheel(0, 4000)

    bar = page.locator("[data-testid='call-bar']")
    box = bar.bounding_box()

    assert box is not None
    assert box["y"] + box["height"] <= 844 + 1


def test_the_page_does_not_move_sideways(live_server, office: SiteSettings, page: Page) -> None:
    page.goto(f"{live_server.url}/kontakt/")

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )

    assert overflow <= 0
