"""The measurable half of FRONTEND.md A.11, on the four pages F11 names.

Lighthouse itself needs node and there is none in this image, so the score is
not what is asserted here. What is asserted is the things the score is made of
and that a test can measure honestly: layout shift, first screen weight, third
party requests, and whether every image reserves its box before it lands.
"""

import contextlib
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page

from apps.core.models import SiteSettings

pytestmark = pytest.mark.django_db

# F11 point 5 names these four.
PAGES = ("/", "/kursy/kat-b/", "/cennik/", "/kontakt/")

# A.11.
CLS_BUDGET = 0.05
FIRST_SCREEN_BUDGET = 400 * 1024

# The tiles are the one third party the design allows, tech.md section 2: no
# cookies, which is why openstreetmap beat google maps.
ALLOWED_THIRD_PARTY = {"tile.openstreetmap.org"}


def layout_shift(page: Page) -> float:
    """Cumulative layout shift, as the browser scores it."""
    return page.evaluate(
        """() => new Promise(resolve => {
            let total = 0;
            new PerformanceObserver(list => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) total += entry.value;
                }
            }).observe({ type: 'layout-shift', buffered: true });
            // One more frame, then report what accumulated.
            requestAnimationFrame(() => requestAnimationFrame(() => resolve(total)));
        })"""
    )


@pytest.mark.parametrize("path", PAGES)
def test_the_page_barely_shifts_while_it_loads(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.11: CLS under 0.05.

    Every c-picture carries width and height, so the box is reserved before the
    bytes arrive. This is what proves it end to end.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.wait_for_timeout(500)

    shift = layout_shift(page)
    assert shift <= CLS_BUDGET, f"{path} shifts {shift:.4f}, budget is {CLS_BUDGET}"


@pytest.mark.parametrize("path", PAGES)
def test_the_first_screen_stays_inside_its_weight(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.11: under 400 KB above the fold."""
    weights: dict[str, int] = {}

    def record(response) -> None:  # noqa: ANN001 - playwright's own type
        # A redirect or a cancelled request has no body to measure.
        with contextlib.suppress(Exception):
            weights[response.url] = len(response.body())

    page.on("response", record)
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.wait_for_timeout(400)

    total = sum(weights.values())
    assert total <= FIRST_SCREEN_BUDGET, (
        f"{path} loads {total // 1024} KB before a scroll, budget is "
        f"{FIRST_SCREEN_BUDGET // 1024} KB"
    )


@pytest.mark.parametrize("path", PAGES)
def test_the_first_screen_reaches_no_third_party(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.11: zero third party requests, and the map does not count until the
    reader has scrolled to it."""
    hosts: list[str] = []
    page.on("request", lambda request: hosts.append(urlsplit(request.url).netloc))

    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.wait_for_timeout(400)

    ours = urlsplit(live_server.url).netloc
    strangers = {host for host in hosts if host and host != ours}
    assert not strangers, f"{path} reaches {sorted(strangers)} before anyone scrolls"


def test_the_map_page_touches_only_the_tile_server(
    live_server, site: SiteSettings, page: Page
) -> None:
    """And once the reader does scroll to it, one host and no other."""
    hosts: list[str] = []
    page.on("request", lambda request: hosts.append(urlsplit(request.url).netloc))

    page.goto(f"{live_server.url}/kontakt/")
    page.locator("[data-map]").scroll_into_view_if_needed()
    page.wait_for_selector(".leaflet-tile")

    ours = urlsplit(live_server.url).netloc
    strangers = {host for host in hosts if host and host != ours}
    assert strangers <= ALLOWED_THIRD_PARTY, f"unexpected hosts: {sorted(strangers)}"


@pytest.mark.parametrize("path", PAGES)
def test_the_stylesheet_and_scripts_do_not_block_the_parser(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """Every script is deferred, so none of them holds up the first paint."""
    page.goto(f"{live_server.url}{path}")

    blocking = page.evaluate(
        """() => [...document.querySelectorAll('script[src]')]
            .filter(s => !s.defer && !s.async)
            .map(s => s.src)"""
    )
    assert blocking == [], f"{path} blocks the parser on {blocking}"
