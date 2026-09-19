"""The faq accordion in a browser, DEV.md S7.3.

The acceptance criterion is about a page with javascript switched off, which is
the one thing no server side assertion can show.
"""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, expect

from apps.links.models import Faq

pytestmark = pytest.mark.django_db

MOBILE = {"width": 390, "height": 844}

ROWS = [
    ("Od jakiego wieku mogę zapisać się na kurs?", "Trzy miesiące przed 18. urodzinami."),
    ("Co to jest PKK i gdzie go otrzymam?", "Wydaje go Starostwo Powiatowe w Wieluniu."),
]


@pytest.fixture
def questions() -> None:
    for order, (question, answer) in enumerate(ROWS):
        Faq.objects.create(question=question, answer=answer, order=order)


@pytest.fixture
def no_js_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=MOBILE, java_script_enabled=False)
    page = context.new_page()
    yield page
    context.close()


def test_the_accordion_opens_without_javascript(
    live_server, no_js_page: Page, questions: None
) -> None:
    """details/summary, so the answer is one tap away with no scripts at all."""
    no_js_page.goto(f"{live_server.url}/faq/")

    answer = no_js_page.get_by_text("Trzy miesiące przed 18. urodzinami.")
    assert answer.is_hidden()

    no_js_page.get_by_text("Od jakiego wieku mogę zapisać się na kurs?").click()

    # expect(), not a bare is_visible(). The panel opens over 260ms now —
    # REDESIGN.md C.3 row 8, animated on ::details-content — so at the instant
    # after the click its box is still zero high and playwright reads that as
    # hidden. expect() polls; the bare assertion measured one frame.
    expect(answer).to_be_visible()


def test_the_accordion_opens_with_javascript_too(live_server, page: Page, questions: None) -> None:
    page.goto(f"{live_server.url}/faq/")
    page.wait_for_function("() => window.Alpine !== undefined")

    answer = page.get_by_text("Wydaje go Starostwo Powiatowe w Wieluniu.")
    assert answer.is_hidden()

    page.get_by_text("Co to jest PKK i gdzie go otrzymam?").click()

    # expect(), not a bare is_visible(). The panel opens over 260ms now —
    # REDESIGN.md C.3 row 8, animated on ::details-content — so at the instant
    # after the click its box is still zero high and playwright reads that as
    # hidden. expect() polls; the bare assertion measured one frame.
    expect(answer).to_be_visible()


def test_the_rows_open_one_by_one(live_server, page: Page, questions: None) -> None:
    """No shared state between rows: opening the second leaves the first alone.

    expect() rather than is_visible(). A panel opens over 180ms, REDESIGN.md
    C.3 row 8, and an element mid-transition is zero pixels tall — which
    is_visible() reports as not visible. The assertion was racing the animation
    and lost about one run in two; expect() retries until the panel has
    finished, which is the question the test is actually asking.
    """
    page.goto(f"{live_server.url}/faq/")

    first = page.get_by_text("Trzy miesiące przed 18. urodzinami.")
    second = page.get_by_text("Wydaje go Starostwo Powiatowe w Wieluniu.")

    page.get_by_text("Od jakiego wieku mogę zapisać się na kurs?").click()
    page.get_by_text("Co to jest PKK i gdzie go otrzymam?").click()

    expect(first).to_be_visible()
    expect(second).to_be_visible()


def test_the_page_does_not_move_sideways(live_server, page: Page, questions: None) -> None:
    page.goto(f"{live_server.url}/faq/")

    widest = page.evaluate(
        """() => Math.max(...Array.from(document.querySelectorAll('main *'))
               .map(node => node.getBoundingClientRect().right))"""
    )

    assert widest <= MOBILE["width"]
