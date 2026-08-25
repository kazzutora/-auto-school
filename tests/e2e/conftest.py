"""End to end fixtures.

Playwright's sync api drives the browser from a greenlet with an event loop
running, and django then refuses ordinary orm calls on that thread. The opt out
is scoped to this directory so the rest of the suite keeps the guard.
"""

import os
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

# tech.md section 9 wants the mobile viewport covered: the visitor arrives from
# a phone searching "prawo jazdy Wieluń".
MOBILE = {"width": 390, "height": 844}


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """One browser for the whole session.

    Shared on purpose. Opening a second sync_playwright() while the first is
    still alive puts the sync api inside a running asyncio loop and it refuses.
    """
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=MOBILE)
    new_page = context.new_page()
    yield new_page
    context.close()
