"""The enrolment form in a browser, DEV.md S3.1.

The form is the main breakage the rebuild fixes, so the things only a browser
can answer are worth pinning: does the htmx swap actually land, does a failed
submission explain itself to a screen reader, and does the whole thing still
work for somebody whose javascript never arrives.
"""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page

from apps.core.models import SiteSettings
from apps.leads.models import Lead

pytestmark = pytest.mark.django_db

MOBILE = {"width": 390, "height": 844}


@pytest.fixture
def school() -> SiteSettings:
    site = SiteSettings.get_solo()
    site.legal_name = "OKiDZ Adam Nawrocki, Mariola Nawrocka S.C."
    site.short_name = "OSK Nawrocki"
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "biuro@example.com"
    site.phone_primary = "43 843 29 11"
    site.lead_notify_emails = "biuro@example.com"
    site.save()
    return site


@pytest.fixture
def no_script(browser: Browser) -> Iterator[Page]:
    """A visitor whose javascript never arrived.

    Not a rare case: a blocked cdn, a corporate proxy, a phone on a train. The
    form has to reach the school anyway, which is why it posts normally and
    redirects when htmx is not there to intercept it.
    """
    context = browser.new_context(viewport=MOBILE, java_script_enabled=False)
    page = context.new_page()
    yield page
    context.close()


def fill(page: Page) -> None:
    page.fill("#lead-form [name=first_name]", "Marek")
    page.fill("#lead-form [name=phone]", "605 065 795")
    page.check("#lead-form [name=consent_rodo]")


def test_the_confirmation_swaps_in_where_the_form_was(
    live_server, school: SiteSettings, page: Page
) -> None:
    page.goto(f"{live_server.url}/zapisz-sie/")
    fill(page)
    page.click("#lead-form button[type=submit]")

    page.wait_for_selector("text=Zgłoszenie przyjęte")
    # Swapped in place: the page never navigated.
    assert page.url.endswith("/zapisz-sie/")
    assert page.locator("#lead-form button[type=submit]").count() == 0
    assert Lead.objects.count() == 1


def test_a_failed_submission_says_why_to_a_screen_reader(
    live_server, school: SiteSettings, page: Page
) -> None:
    """DEV.md S3.1: every field has a label and points at its error.

    aria-invalid on its own only announces "invalid". The reason has to be
    reachable through aria-describedby, and the markup htmx swaps in never went
    through the page load that wires it.
    """
    page.goto(f"{live_server.url}/zapisz-sie/")
    page.fill("#lead-form [name=first_name]", "Marek")
    page.fill("#lead-form [name=phone]", "12")
    page.click("#lead-form button[type=submit]")

    page.wait_for_selector("[aria-invalid='true']")

    explained = page.evaluate(
        """() => [...document.querySelectorAll('#lead-form [aria-invalid="true"]')].map(el => {
            const ids = (el.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean);
            return {
                name: el.name,
                reasons: ids
                    .map(id => (document.getElementById(id) || {}).textContent || '')
                    .filter(text => text.trim()),
            };
        })"""
    )

    assert explained, "nothing was marked invalid"
    for control in explained:
        assert control["reasons"], f"{control['name']} says invalid without saying why"
    assert Lead.objects.count() == 0


def test_every_control_has_a_label(live_server, school: SiteSettings, page: Page) -> None:
    page.goto(f"{live_server.url}/zapisz-sie/")

    unlabelled = page.evaluate(
        """() => [...document.querySelectorAll(
            '#lead-form input:not([type=hidden]), #lead-form select, #lead-form textarea'
        )].filter(el => !document.querySelector(`label[for="${el.id}"]`) && !el.closest('label'))
          .map(el => el.name)"""
    )
    assert unlabelled == []


def test_the_honeypot_is_out_of_the_tab_order(
    live_server, school: SiteSettings, page: Page
) -> None:
    """A keyboard user must never land in the trap."""
    page.goto(f"{live_server.url}/zapisz-sie/")
    assert page.locator("[name=website]").get_attribute("tabindex") == "-1"


def test_the_form_reaches_the_school_without_javascript(
    live_server, school: SiteSettings, no_script: Page
) -> None:
    page = no_script
    page.goto(f"{live_server.url}/zapisz-sie/")
    fill(page)
    page.click("#lead-form button[type=submit]")

    page.wait_for_url("**/zapisz-sie/dziekujemy/")
    assert "Dziękujemy" in page.content()
    assert Lead.objects.count() == 1


def test_the_form_is_on_the_course_page_with_the_course_chosen(
    live_server, school: SiteSettings, page: Page
) -> None:
    """F5 and DEV.md S3.1: the visitor has just read about it, and should not
    have to say which course they mean."""
    from apps.courses.models import Course

    course = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B", is_active=True
    )
    page.goto(f"{live_server.url}/kursy/kat-b/")

    chosen = page.locator("#lead-form [name=course]").input_value()
    assert chosen == str(course.pk)
