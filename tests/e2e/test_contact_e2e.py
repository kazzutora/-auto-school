"""The contact page in a browser, DEV.md S4.

Three things only a browser answers: does the google map load when somebody asks
for it, does the page reach a third party before they do, and are the numbers
tappable on a phone.
"""

from collections.abc import Iterator
from datetime import time
from decimal import Decimal
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, Route

from apps.core.models import OpeningHours, SiteSettings

pytestmark = pytest.mark.django_db

# The map is google's since core v26, and google is the one third party the page
# may touch — after the visitor presses the button and not before, tech.md
# section 2.
GOOGLE_MAPS = "https://www.google.com/maps"


@pytest.fixture
def office() -> SiteSettings:
    site = SiteSettings.get_solo()
    site.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    site.street = "ul. Asnyka 7"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "oskostrycharz@poczta.onet.pl"
    site.phone_primary = "691 570 489"
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


def answer_for_google(route: Route) -> None:
    """Stands in for google's embed.

    The test is about what the page does with the click, not about google's
    uptime, and a suite that needs the internet is a suite that fails on a train.
    """
    route.fulfill(body="<!doctype html><title>map</title>", content_type="text/html")


def scroll_to_map(page: Page) -> None:
    """Put the map on screen first, exactly as a visitor would.

    Scrolling to it is not asking for it: the button is. Every assertion about
    what the map fetches has to prove that the scroll alone fetched nothing.
    """
    page.locator("[data-testid='map']").scroll_into_view_if_needed()


def test_the_map_loads_when_asked(live_server, office: SiteSettings, page: Page) -> None:
    page.route(f"{GOOGLE_MAPS}**", answer_for_google)
    page.goto(f"{live_server.url}/kontakt/")
    scroll_to_map(page)

    page.locator("[data-testid='map'] [data-map-load]").click()

    frame = page.locator("[data-testid='map'] iframe")
    frame.wait_for()
    src = frame.get_attribute("src")
    assert src is not None
    assert src.startswith(f"{GOOGLE_MAPS}?q=51.2206,18.5697"), src
    assert "output=embed" in src
    assert page.locator("[data-map-load]").count() == 0, "the button outlived the click"


def test_the_map_is_not_loaded_before_a_click(
    live_server, office: SiteSettings, page: Page
) -> None:
    page.goto(f"{live_server.url}/kontakt/")
    scroll_to_map(page)
    page.wait_for_timeout(300)

    assert page.locator("[data-testid='map'] iframe").count() == 0
    assert page.locator("[data-testid='map'] [data-map-load]").is_visible()


def test_the_page_talks_to_nobody_before_the_click(
    live_server, office: SiteSettings, watched_page: tuple[Page, list[str]]
) -> None:
    """The acceptance criterion: no analytics host, and no google until asked."""
    page, hosts = watched_page
    page.goto(f"{live_server.url}/kontakt/")
    scroll_to_map(page)
    page.wait_for_load_state("networkidle")

    ours = {urlsplit(live_server.url).netloc}
    assert set(hosts) <= ours, f"unexpected hosts: {sorted(set(hosts) - ours)}"


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
        #
        # Rounded, because getBoundingClientRect returns a float and an element
        # sitting at a fractional offset comes back as 43.99993896484375 for a
        # box whose computed min-height is exactly 44px. The target is the
        # right size; the comparison was the thing that could not tell.
        assert round(box["height"]) >= 44


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
