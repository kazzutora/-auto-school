"""Intake filter in a browser, DEV.md S2.2.

Two things only a browser can answer: does htmx actually swap the rows, and does
the same filter still work once javascript is switched off.
"""

from collections.abc import Iterator
from datetime import timedelta

import pytest
from django.utils import timezone
from playwright.sync_api import Browser, Page

from apps.courses.models import Course, CourseIntake

pytestmark = pytest.mark.django_db


@pytest.fixture
def schedule() -> None:
    polish = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )
    russian = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-c", code="C", title="Kategoria C"
    )
    today = timezone.localdate()
    CourseIntake.objects.create(
        course=polish,
        start_date=today + timedelta(days=7),
        mode=CourseIntake.Mode.STATIONARY,
        language="pl",
        status=CourseIntake.Status.OPEN,
    )
    CourseIntake.objects.create(
        course=russian,
        start_date=today + timedelta(days=14),
        mode=CourseIntake.Mode.ELEARNING,
        language="ru",
        status=CourseIntake.Status.OPEN,
    )


@pytest.fixture
def no_js_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
    page = context.new_page()
    yield page
    context.close()


def visible_courses(page: Page) -> str:
    return page.locator("#intake-table tbody").inner_text()


def test_htmx_swaps_only_the_rows(live_server, page: Page, schedule: None) -> None:
    page.goto(f"{live_server.url}/terminy/")
    page.wait_for_function("() => window.htmx !== undefined")

    assert "Kategoria B" in visible_courses(page)
    assert "Kategoria C" in visible_courses(page)

    page.select_option("#id_language", "ru")
    page.wait_for_function(
        "() => !document.querySelector('#intake-table tbody').innerText.includes('Kategoria B')"
    )

    assert "Kategoria C" in visible_courses(page)
    # The page itself never reloaded, only the tbody changed.
    assert page.locator("h1").inner_text() == "Terminy"


def test_the_filter_still_works_without_javascript(
    live_server, no_js_page: Page, schedule: None
) -> None:
    """The acceptance criterion, checked with javascript genuinely off."""
    no_js_page.goto(f"{live_server.url}/terminy/")

    assert "Kategoria B" in visible_courses(no_js_page)

    no_js_page.select_option("#id_language", "ru")
    no_js_page.get_by_role("button", name="Pokaż terminy").click()
    no_js_page.wait_for_url("**/terminy/?*")

    assert "Kategoria C" in visible_courses(no_js_page)
    assert "Kategoria B" not in visible_courses(no_js_page)


def test_an_empty_result_offers_a_phone_number(live_server, page: Page, schedule: None) -> None:
    page.goto(f"{live_server.url}/terminy/?course=kat-b&language=ru")

    body = visible_courses(page)
    assert "Nic nie pasuje" in body
