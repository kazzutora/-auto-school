"""The home page in a browser at 390x844, FRONTEND.md F3.

The phone the visitor actually arrives on, searching "prawo jazdy Wieluń".
Three things only a browser answers: is the hero on screen without scrolling,
can a thumb reach the call button, and does a category tile go where it says.
"""

from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page

from apps.core.models import SiteSettings
from apps.courses.models import Course, CourseIntake

pytestmark = pytest.mark.django_db

TILE_HOST = "tile.openstreetmap.org"


@pytest.fixture
def school() -> SiteSettings:
    site = SiteSettings.get_solo()
    site.legal_name = "OKiDZ Adam Nawrocki, Mariola Nawrocka S.C."
    site.short_name = "OSK Nawrocki"
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "osk.adam.nawrocki@wp.pl"
    site.phone_primary = "43 843 29 11"
    site.founded_year = 1996
    site.map_lat = Decimal("51.220600")
    site.map_lng = Decimal("18.569700")
    site.save()

    course = Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-b",
        code="B",
        title="Kategoria B",
        min_age=18,
        price_gross=Decimal("3200"),
        is_active=True,
    )
    CourseIntake.objects.create(
        course=course,
        start_date=date.today() + timedelta(days=21),
        mode=CourseIntake.Mode.STATIONARY,
        language="pl",
        status=CourseIntake.Status.OPEN,
    )
    return site


def test_the_hero_is_on_screen_without_scrolling(
    live_server, school: SiteSettings, page: Page
) -> None:
    page.goto(live_server.url)

    heading = page.locator("h1")
    assert heading.count() == 1
    box = heading.bounding_box()
    assert box is not None
    # 844 tall: the headline has to be readable before a finger moves.
    assert box["y"] + box["height"] < 844


def test_the_call_button_is_reachable_with_a_thumb(
    live_server, school: SiteSettings, page: Page
) -> None:
    page.goto(live_server.url)

    call = page.locator("section a[href^='tel:']").first
    call.wait_for(state="visible")
    box = call.bounding_box()
    assert box is not None
    assert box["height"] >= 44, "a finger needs something to hit"
    # Clickable means nothing is sitting on top of it.
    call.click(trial=True)


def test_a_category_tile_opens_its_course(live_server, school: SiteSettings, page: Page) -> None:
    page.goto(live_server.url)

    tile = page.locator("#kategorie a[href='/kursy/kat-b/']").first
    tile.wait_for(state="visible")
    tile.click()

    page.wait_for_url("**/kursy/kat-b/")
    assert page.locator("h1").inner_text().strip()


def test_the_page_never_moves_sideways_on_a_phone(
    live_server, school: SiteSettings, page: Page
) -> None:
    """A.4: not at any width from 320px up, and 390 is the common one."""
    page.goto(live_server.url)

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"the page scrolls {overflow}px sideways"


def test_the_sticky_bar_never_covers_the_consent_buttons(
    live_server, school: SiteSettings, page: Page
) -> None:
    """A.5: the banner is always above the bar, or consent cannot be given."""
    page.goto(live_server.url)

    accept = page.locator("[data-cookie-accept]")
    accept.wait_for(state="visible")
    accept.click(trial=True)


def test_the_first_screen_reaches_no_third_party(
    live_server, school: SiteSettings, page: Page
) -> None:
    """The tiles are the one third party allowed, and the map is the last
    section: nothing should be fetched from it before the visitor scrolls."""
    hosts: list[str] = []
    page.on("request", lambda request: hosts.append(urlsplit(request.url).netloc))

    page.goto(live_server.url)
    page.wait_for_selector("h1")

    assert TILE_HOST not in hosts, "the map loaded before anyone scrolled to it"
    assert set(hosts) <= {urlsplit(live_server.url).netloc}, (
        f"unexpected hosts: {sorted(set(hosts) - {urlsplit(live_server.url).netloc})}"
    )
