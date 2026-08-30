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


# --------------------------------------------------------------------------
# FRONTEND_FIXES.md X5

BANDED = ["/terminy/", "/kontakt/", "/galeria/", "/certyfikaty/", "/cennik/", "/o-nas/"]

RHYTHM = """() => {
    const sections = [...document.querySelectorAll('main section')];
    const report = sections.map(s => ({
        ground: s.classList.contains('bg-paper-50') ? 'muted'
              : s.classList.contains('u-ground-ink') ? 'ink'
              : s.classList.contains('u-ground-deep') ? 'deep' : 'paper',
        height: Math.round(s.getBoundingClientRect().height),
        chars: s.textContent.replace(/\s+/g, ' ').trim().length,
        media: !!s.querySelector('img, picture, iframe, [data-map]'),
    }));
    let repeats = 0;
    for (let i = 1; i < report.length; i++) {
        if (report[i].ground === report[i - 1].ground) repeats++;
    }
    return {
        count: report.length,
        grounds: report.map(r => r.ground),
        repeats: repeats,
        last: report.length ? report[report.length - 1].ground : null,
        // A section whose content is a map or a wall of photographs is tall
        // for a reason, and counting its characters says nothing about it.
        // The rule is about text with air around it, so only text sections
        // are judged by it.
        airy: report.filter(r => !r.media && r.height > 700 && r.chars < 400)
                    .map(r => r.height + 'px for ' + r.chars + ' characters'),
    };
}"""


@pytest.mark.parametrize("path", BANDED)
def test_the_page_has_a_rhythm(live_server, site: SiteSettings, page: Page, path: str) -> None:
    """X5's acceptance criteria, and X1 and X2's before it.

    Every inner page used to be one or two sections of the same colour running
    from the heading to the footer, which reads as an unfinished page however
    good the words are.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    found = page.evaluate(RHYTHM)
    assert found["count"] >= 3, f"{path} has {found['count']} block(s): {found['grounds']}"
    assert not found["repeats"], f"{path} repeats a ground: {found['grounds']}"
    assert found["last"] == "ink", f"{path} ends on {found['last']}, not an invitation"
    assert not found["airy"], f"{path} has air instead of rhythm: {found['airy']}"


@pytest.mark.parametrize("path", BANDED)
def test_the_eyebrow_says_where_you_are(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """X0 point 3: it read OSK NAWROCKI WIELUŃ on every page, which the
    breadcrumbs above it had already said."""
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    eyebrow = page.locator("main p.label").first
    assert eyebrow.count() == 1
    assert "NAWROCKI" not in eyebrow.inner_text().upper()
