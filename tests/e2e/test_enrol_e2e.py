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


# --------------------------------------------------------------------------
# the six states, FRONTEND.md F7


def test_refusing_consent_keeps_the_form_and_says_why(
    live_server, school: SiteSettings, page: Page
) -> None:
    """F7: the RODO error is shown at the checkbox itself.

    The one field a visitor is most likely to skip, and the one refusal that
    has to be explained rather than just marked.
    """
    page.goto(f"{live_server.url}/zapisz-sie/")
    page.fill("#lead-form [name=first_name]", "Marek")
    page.fill("#lead-form [name=phone]", "605 065 795")
    # consent deliberately left unticked
    page.click("#lead-form button[type=submit]")

    page.wait_for_selector("[name=consent_rodo][aria-invalid='true']")

    described_by = page.locator("[name=consent_rodo]").get_attribute("aria-describedby")
    assert described_by
    message = page.locator(f"#{described_by}").inner_text()
    assert "zgody" in message.lower()

    # Still a form, and what was typed is still in it.
    assert page.locator("#lead-form button[type=submit]").count() == 1
    assert page.locator("#lead-form [name=first_name]").input_value() == "Marek"
    assert Lead.objects.count() == 0


def test_the_button_says_it_is_sending(live_server, school: SiteSettings, page: Page) -> None:
    """F7 point 4. The label swaps and the button stops being pressable.

    Driven by the class htmx puts on the form for the duration of a request
    rather than by racing a real one. Holding the network open long enough to
    look at leaves a route in flight that outlives the test and closes the next
    one's browser; that htmx sets the class at all is its documented behaviour,
    and that it drives this form is what the confirmation test above proves.
    What is ours is the markup and the css, and that is what is checked here.
    """
    page.goto(f"{live_server.url}/zapisz-sie/")

    # Ours: the button is taken out of reach for the duration.
    form = page.locator("#lead-form")
    assert form.get_attribute("hx-disabled-elt") == "find button[type=submit]"

    idle = page.locator("#lead-form [data-when-idle]")
    sending = page.locator("#lead-form [data-when-sending]")
    assert idle.is_visible()
    assert not sending.is_visible()

    form.evaluate("el => el.classList.add('htmx-request')")

    assert sending.is_visible()
    assert "Wysyłanie" in sending.inner_text()
    assert not idle.is_visible()


def test_a_server_error_keeps_the_data_and_offers_the_phone(
    live_server, school: SiteSettings, page: Page
) -> None:
    """F7 point 6: nobody gets lost because our side fell over."""
    page.route("**/zapisz-sie/submit/", lambda route: route.fulfill(status=500, body="boom"))

    page.goto(f"{live_server.url}/zapisz-sie/")
    fill(page)
    page.click("#lead-form button[type=submit]")

    alert = page.locator("#lead-form [data-form-error]")
    alert.wait_for(state="visible")
    assert "zadzwoń" in alert.inner_text().lower()
    assert alert.locator("a[href^='tel:']").count() == 1

    # Nothing was swapped, so everything typed is still there.
    assert page.locator("#lead-form [name=first_name]").input_value() == "Marek"
    assert page.locator("#lead-form [name=phone]").input_value() == "605 065 795"

    page.unroute_all(behavior="ignoreErrors")


def test_the_form_is_walkable_from_the_first_field_to_the_button(
    live_server, school: SiteSettings, page: Page
) -> None:
    """F7: reachable end to end with a keyboard, and the trap is never in it."""
    page.goto(f"{live_server.url}/zapisz-sie/")
    page.focus("#lead-form [name=first_name]")

    seen = []
    for _ in range(12):
        seen.append(
            page.evaluate(
                "() => { const a = document.activeElement;"
                " return a.name || a.tagName.toLowerCase(); }"
            )
        )
        if seen[-1] == "button":
            break
        page.keyboard.press("Tab")

    assert "website" not in seen, "the honeypot is in the tab order"
    for name in ("first_name", "phone", "consent_rodo"):
        assert name in seen, f"{name} cannot be reached with a keyboard"
    assert seen[-1] == "button", f"the submit button was never reached: {seen}"


def test_the_phone_asks_for_a_phone_keypad(live_server, school: SiteSettings, page: Page) -> None:
    """F7: inputmode and autocomplete, which is most of what makes a form on a
    phone bearable."""
    page.goto(f"{live_server.url}/zapisz-sie/")

    phone = page.locator("#lead-form [name=phone]")
    assert phone.get_attribute("type") == "tel"
    assert phone.get_attribute("inputmode") == "tel"
    assert phone.get_attribute("autocomplete") == "tel"
    assert page.locator("#lead-form [name=email]").get_attribute("autocomplete") == "email"


def test_the_trap_is_hidden_without_being_skipped_by_a_bot(
    live_server, school: SiteSettings, page: Page
) -> None:
    """F7: not display:none on the container, which is what a scraper skips."""
    page.goto(f"{live_server.url}/zapisz-sie/")

    container = page.locator("#lead-form div.u-trap")
    style = container.evaluate("el => getComputedStyle(el).display")
    assert style != "none", "a trap a bot skips catches nothing"
    assert container.get_attribute("aria-hidden") == "true"

    # Gone for a person all the same. Measured rather than asked: playwright
    # calls a clipped element visible because it still has a box, which is
    # exactly the property that keeps a bot filling it in.
    box = page.locator("#lead-form [name=website]").bounding_box()
    assert box is not None
    assert box["width"] <= 1 and box["height"] <= 1, box
