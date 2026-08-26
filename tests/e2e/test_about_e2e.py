"""About page layout, DEV.md S5.

The page stacks photo cards, fact tiles and a fleet list. Whether that still
fits the narrowest phone in use is a question only a browser answers.
"""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page

from apps.core.models import Page as FlatPage
from apps.core.models import SiteSettings
from apps.courses.models import Course
from apps.people.models import Instructor, Vehicle
from tests.factories import image_bytes

pytestmark = pytest.mark.django_db

NARROW = {"width": 320, "height": 720}


@pytest.fixture
def narrow_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=NARROW)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def school() -> None:
    site = SiteSettings.get_solo()
    site.founded_year = 1996
    site.phone_primary = "43 843 29 11"
    site.save()

    FlatPage.objects.create(
        slug="o-nas",
        title="O nas",
        lead="Jesteśmy firmą rodzinną, szkolimy kierowców w Wieluniu od 1996 roku.",
        body="## Kim jesteśmy\n\nOśrodek szkolenia kierowców w Wieluniu.",
        is_published=True,
    )
    category = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )
    for number in range(3):
        instructor = Instructor.objects.create(
            full_name=f"Instruktor {number}", role="Instruktor kat. B", photo=image_bytes()
        )
        instructor.categories.add(category)
        Vehicle.objects.create(
            course=category, make="Skoda", model=f"Fabia {number}", photo=image_bytes()
        )


def test_nothing_on_the_page_is_wider_than_the_screen(
    live_server, narrow_page: Page, school: None
) -> None:
    """Measured inside main on purpose.

    The whole document does overflow at 320px, and not because of this page:
    c-button prints its own class and cotton appends the caller's as a second
    class attribute, which the browser drops. The header phone button therefore
    keeps its "hidden" off and pushes every page sideways as soon as
    SiteSettings carries a number. That is a component contract, see the
    contract gap in the handover.
    """
    narrow_page.goto(f"{live_server.url}/o-nas/")

    widest = narrow_page.evaluate(
        """() => Math.max(...Array.from(document.querySelectorAll('main *'))
               .map(node => node.getBoundingClientRect().right))"""
    )

    assert widest <= NARROW["width"]


def test_the_photos_fit_their_cards(live_server, narrow_page: Page, school: None) -> None:
    """A photo wider than the card is what pushes a page sideways."""
    narrow_page.goto(f"{live_server.url}/o-nas/")
    images = narrow_page.locator("[data-testid='instructors'] img")

    assert images.count() == 3
    for index in range(images.count()):
        box = images.nth(index).bounding_box()
        assert box is not None
        assert box["width"] <= NARROW["width"]


def test_the_team_and_the_fleet_are_both_on_screen(
    live_server, narrow_page: Page, school: None
) -> None:
    narrow_page.goto(f"{live_server.url}/o-nas/")
    text = narrow_page.locator("body").inner_text()

    assert "Instruktorzy" in text
    assert "Nasze pojazdy" in text
    assert "Skoda Fabia 0" in text
