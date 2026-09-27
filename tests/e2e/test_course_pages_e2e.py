"""Course pages in a real browser, DEV.md S1.2.

The acceptance criterion is about what a visitor on a 390px phone can see
without scrolling, which only a browser can answer.
"""

import pytest
from playwright.sync_api import Page

from apps.core.models import SiteSettings
from apps.courses.models import Course

pytestmark = pytest.mark.django_db


@pytest.fixture
def course() -> Course:
    site = SiteSettings.get_solo()
    site.phone_primary = "605 065 795"
    site.short_name = "OSK Ostrycharz"
    site.save()
    return Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-b",
        code="B",
        title="Kategoria B",
        min_age=18,
        lead="Kurs prawa jazdy kategorii B.",
        entitlements="- pojazdem do 3,5 t\n- ciągnikiem rolniczym",
        requirements="- ukończone 18 lat\n- numer PKK",
    )


def test_the_page_does_not_scroll_sideways(live_server, page: Page, course: Course) -> None:
    page.goto(f"{live_server.url}/kursy/kat-b/")

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0


def test_the_listing_leads_to_the_course(live_server, page: Page, course: Course) -> None:
    page.goto(f"{live_server.url}/kursy/")

    # Scoped to the page, not the chrome: the menu now points at this same url,
    # and an unscoped .first picks the nav link — which is hidden at this
    # viewport, so the click waited for a visibility that was never coming.
    page.locator('main a[href="/kursy/kat-b/"]').first.click()
    page.wait_for_url("**/kursy/kat-b/")

    # casefold, because REDESIGN.md B.3 sets every h1 and h2 in upper case and
    # inner_text() returns what is painted. The words are unchanged; only the
    # rendering is, and asserting on the rendering would pin a design decision
    # in a test about routing.
    assert page.locator("h1").inner_text().casefold() == "kategoria b"
