"""Heading order and touch targets on every public page, DESIGN-REVIEW 6 and 9.

Both went wrong quietly. A card hardcoded to h3 skipped a level on four pages,
and a control can be four pixels short for months without anyone filing it.
Neither is visible in a screenshot, so neither was caught until something
measured it — which is what this does.
"""

import pytest
from playwright.sync_api import Page

from apps.core.models import SiteSettings
from tests.e2e.conftest import PAGES

pytestmark = pytest.mark.django_db

# A.11.
MIN_TARGET = 44

HEADINGS = """() => {
    const sel = 'main h1, main h2, main h3, main h4, main h5, main h6';
    const hs = [...document.querySelectorAll(sel)];
    const levels = hs.map(h => Number(h.tagName[1]));
    const skips = [];
    for (let i = 1; i < levels.length; i++) {
        if (levels[i] > levels[i - 1] + 1) {
            skips.push('h' + levels[i - 1] + ' -> h' + levels[i]
                + ' at "' + hs[i].textContent.trim().slice(0, 40) + '"');
        }
    }
    return { h1: document.querySelectorAll('main h1').length, skips: skips };
}"""

TARGETS = r"""(minimum) => {
    const small = [];
    const controls = document.querySelectorAll(
        'a[href], button, select, textarea, input:not([type=hidden])'
    );
    for (const el of controls) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        // The trap is meant to be unreachable, and the skip link is off screen
        // until it takes focus.
        if (el.closest('.u-trap') || el.classList.contains('sr-only')) continue;
        // WCAG 2.5.5 exempts a link sitting inside a run of text.
        if (el.tagName === 'A' && el.closest('p, li, address, figcaption, span')) continue;

        // A checkbox is hit through its label, which is the real target.
        const box = (el.type === 'checkbox' ? (el.closest('label') || el) : el)
            .getBoundingClientRect();
        if (box.width === 0 || box.height === 0) continue;

        if (box.width < minimum || box.height < minimum) {
            small.push(Math.round(box.width) + 'x' + Math.round(box.height)
                + ' "' + (el.textContent || el.getAttribute('aria-label') || el.name || '')
                    .trim().slice(0, 30) + '"');
        }
    }
    return small;
}"""


@pytest.mark.a11y
@pytest.mark.parametrize("path", PAGES)
def test_the_headings_run_in_order(live_server, site: SiteSettings, page: Page, path: str) -> None:
    """One h1, and no level skipped on the way down.

    A skipped level is what a screen reader reads out as a section that is not
    there. It is also the thing a card component gets wrong by defaulting: a
    card under the page h1 is a level 2 item, one inside a section with its own
    h2 is a level 3, and only the page knows which.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    found = page.evaluate(HEADINGS)
    assert found["h1"] == 1, f"{path} has {found['h1']} h1 elements"
    assert not found["skips"], f"{path}: {found['skips']}"


@pytest.mark.a11y
@pytest.mark.parametrize("path", PAGES)
def test_every_target_is_big_enough_for_a_finger(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.11: 44x44, measured on the thing a finger actually lands on."""
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    small = page.evaluate(TARGETS, MIN_TARGET)
    assert not small, f"{path} has targets under {MIN_TARGET}px: {small[:5]}"
