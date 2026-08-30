"""Every public page at every breakpoint, FRONTEND.md F11 point 7.

A.4 is blunt: the page never moves sideways at any width from 320px up. One
element with a fixed width, one long word, one table without its scroll box,
and it does — and the reader is left dragging the page to read a sentence.
"""

import pytest
from playwright.sync_api import Browser, Page

from apps.core.models import SiteSettings
from tests.e2e.conftest import PAGES

pytestmark = pytest.mark.django_db

# A.4 fixes the breakpoints; 320 is the narrowest phone still in use and 390 is
# the one most visitors actually arrive on.
WIDTHS = (320, 390, 768, 1024, 1440)


def sideways(page: Page) -> int:
    return page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )


def offenders(page: Page) -> list[str]:
    """What is sticking out, so a failure names the element rather than a number."""
    return page.evaluate(
        """() => {
            const room = document.documentElement.clientWidth;
            return [...document.querySelectorAll('body *')]
                .filter(el => !el.closest('.u-scroll-x')
                           && !el.closest('.leaflet-container')
                           && !el.classList.contains('u-trap')
                           && !el.classList.contains('sr-only'))
                .map(el => ({ el, r: el.getBoundingClientRect() }))
                .filter(x => x.r.right > room + 1 && x.r.width < 5000)
                .sort((a, b) => b.r.right - a.r.right)
                .slice(0, 4)
                .map(x => x.el.tagName.toLowerCase()
                    + '.' + (x.el.className || '').toString().slice(0, 40)
                    + ' -> ' + Math.round(x.r.right) + 'px');
        }"""
    )


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("path", PAGES)
def test_the_page_never_moves_sideways(
    live_server, site: SiteSettings, browser: Browser, path: str, width: int
) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}{path}")
        page.wait_for_selector("h1")
        overflow = sideways(page)
        assert overflow <= 0, f"{path} at {width}px scrolls {overflow}px: {offenders(page)}"
    finally:
        context.close()


@pytest.mark.parametrize("width,shown", [(390, False), (768, True), (1024, True), (1440, True)])
def test_the_language_row_is_reachable_at_every_width(
    live_server, site: SiteSettings, browser: Browser, width: int, shown: bool
) -> None:
    """A reader who does not read polish opens the site looking for one control.

    It used to appear only from 1280, which put it behind the burger on every
    laptop narrower than that and on every tablet. It stands in the bar from md
    now; below md the bar has no room and it lives in the menu panel, which is
    the one place it is allowed to hide.
    """
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}/o-nas/")
        page.wait_for_selector("h1")

        # The panel carries a second copy of the row, so take the one in the
        # bar by document order rather than by a selector the panel also fits.
        bar = page.locator(".u-header nav[aria-label]:has(a[hreflang])").first
        assert bar.is_visible() is shown, f"the language row at {width}px"

        if not shown:
            page.locator("[data-modal-open=main-menu]").click()
            panel = page.locator("#main-menu nav[aria-label]:has(a[hreflang])")
            panel.wait_for(state="visible")
            assert panel.is_visible(), "the menu panel drops the language row too"
    finally:
        context.close()


@pytest.mark.parametrize("prefix", ["", "/ru", "/uk"])
def test_the_header_row_fits_in_every_language(
    live_server, site: SiteSettings, browser: Browser, prefix: str
) -> None:
    """A translated word is a longer word.

    "Kierowca zawodowy" became "Профессиональный водитель", 118px wider, and the
    menu ran into the language switcher and the phone. The bar has no room to
    give — it fits polish with three pixels to spare — so the menu carries its
    own shorter wording through a message context while the headings keep the
    full phrase.
    """
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}{prefix}/")
        page.wait_for_selector("h1")

        measured = page.evaluate(
            """() => {
                const bar = document.querySelector('.u-header .u-container');
                const style = getComputedStyle(bar);
                const content = bar.clientWidth
                    - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
                const gap = parseFloat(style.columnGap) || 0;
                const kids = [...bar.children];
                const need = kids.reduce((sum, el) => sum + el.scrollWidth, 0)
                    + gap * (kids.length - 1);
                const nav = bar.querySelector('nav[aria-label]');
                const list = nav && nav.querySelector('ul');
                return {
                    content: Math.round(content),
                    need: Math.round(need),
                    spill: list
                        ? Math.round(list.getBoundingClientRect().right
                            - nav.getBoundingClientRect().right)
                        : 0,
                };
            }"""
        )
        assert measured["spill"] <= 0, (
            f"{prefix or '/pl'}: the menu runs {measured['spill']}px past its box"
        )
        assert measured["need"] <= measured["content"], (
            f"{prefix or '/pl'}: the header row wants {measured['need']}px "
            f"and has {measured['content']}px"
        )
    finally:
        context.close()
