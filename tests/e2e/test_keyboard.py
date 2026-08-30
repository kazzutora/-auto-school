"""Every public page walked with a keyboard, FRONTEND.md F11 point 4.

Three things go wrong and none of them show up in a screenshot: focus lands on
something nobody can see, focus lands outside the viewport with no scroll, or
focus disappears into a element with no visible ring. A.11 asks for full
keyboard traversal with the focus visible everywhere.
"""

import pytest
from playwright.sync_api import Browser, Page

from apps.core.models import SiteSettings
from tests.e2e.conftest import PAGES

pytestmark = pytest.mark.django_db

MOBILE = {"width": 390, "height": 844}

# Enough to clear the header, the whole of a short page, and well into a long
# one. The pages that carry more stops are covered by the same rules.
TAB_STOPS = 40


def focus_report(page: Page) -> dict:
    return page.evaluate(
        """() => {
            const el = document.activeElement;
            if (!el || el === document.body) return { tag: 'body' };
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            return {
                tag: el.tagName.toLowerCase(),
                name: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40),
                cls: (el.className || '').toString().slice(0, 60),
                width: Math.round(r.width),
                height: Math.round(r.height),
                top: Math.round(r.top),
                left: Math.round(r.left),
                viewportHeight: window.innerHeight,
                viewportWidth: window.innerWidth,
                display: cs.display,
                visibility: cs.visibility,
            };
        }"""
    )


@pytest.mark.a11y
@pytest.mark.parametrize("path", PAGES)
def test_focus_never_lands_somewhere_nobody_can_see(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.evaluate("() => document.body.focus()")

    seen = []
    for step in range(TAB_STOPS):
        page.keyboard.press("Tab")
        spot = focus_report(page)
        if spot["tag"] == "body":
            break
        seen.append(spot)

        assert spot["display"] != "none", f"{path} step {step}: focus on a display:none element"
        assert spot["visibility"] != "hidden", f"{path} step {step}: focus on a hidden element"
        # A focused control with no box is one nobody can see the ring on.
        assert spot["width"] > 0 and spot["height"] > 0, f"{path} step {step}: {spot}"
        # The browser scrolls focus into view, so anything still off screen is
        # pinned somewhere it cannot come back from.
        assert -1 <= spot["top"] <= spot["viewportHeight"], f"{path} step {step}: {spot}"
        assert -1 <= spot["left"] <= spot["viewportWidth"], f"{path} step {step}: {spot}"

    assert seen, f"{path} has nothing focusable at all"
    # F2: the skip link is the way past the header, and it is first.
    assert "treści" in seen[0]["name"], f"{path} does not start with the skip link: {seen[0]}"


@pytest.mark.a11y
@pytest.mark.parametrize("path", ["/", "/kontakt/", "/zapisz-sie/"])
def test_every_focused_control_shows_a_ring(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.2: a 2px ring with a 2px offset, and it has to actually paint.

    The ring plugins are switched off in tailwind.config.js, so a stray
    focus-visible:ring-* class generates nothing and the focus silently
    disappears. This is what catches that.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.evaluate("() => document.body.focus()")

    ringless = []
    for _ in range(TAB_STOPS):
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)
        found = page.evaluate(
            """() => {
                const el = document.activeElement;
                if (!el || el === document.body) return null;
                const cs = getComputedStyle(el);
                const outline = parseFloat(cs.outlineWidth) || 0;
                const shadow = cs.boxShadow && cs.boxShadow !== 'none';
                const border = cs.borderColor;
                return {
                    ok: outline > 0 || shadow,
                    what: (el.getAttribute('aria-label') || el.textContent || el.tagName)
                        .trim().slice(0, 40),
                    outline: cs.outline,
                    border,
                };
            }"""
        )
        if found is None:
            break
        if not found["ok"]:
            ringless.append(found)

    assert not ringless, f"{path}: focused with nothing to show for it: {ringless[:3]}"


@pytest.mark.a11y
@pytest.mark.parametrize("path", ["/", "/kontakt/", "/zapisz-sie/", "/cennik/"])
def test_the_focus_ring_stands_out_from_what_is_behind_it(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """WCAG 1.4.11: a focus indicator needs 3:1 against what surrounds it.

    A.2 asks for the ring to be yellow, and #FFD400 is 1.6:1 on white paper and
    1.3:1 on the inverted hero once the dark theme turns it near white — so the
    yellow on its own fails on most of the site. The halo under it is what
    carries the contrast; this measures the pair that actually reads.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")
    page.evaluate("() => document.body.focus()")

    worst = []
    for _ in range(TAB_STOPS):
        page.keyboard.press("Tab")
        # A.6 puts outline-color and box-shadow on the 120ms transition, so the
        # ring is still on its way to the colour it will settle at. Reading it
        # any sooner measures the frame in between, which is neither colour.
        page.wait_for_timeout(200)
        found = page.evaluate(
            r"""() => {
                const el = document.activeElement;
                if (!el || el === document.body) return null;

                const lum = (colour) => {
                    const m = colour.match(/[\d.]+/g);
                    if (!m) return null;
                    const [r, g, b] = m.map(Number);
                    const ch = (v) => {
                        v /= 255;
                        return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
                    };
                    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
                };
                const ratio = (a, b) => {
                    const x = lum(a), y = lum(b);
                    if (x === null || y === null) return null;
                    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
                };

                const cs = getComputedStyle(el);
                // Whatever is painted behind the ring.
                let node = el, ground = null;
                while (node && !ground) {
                    const bg = getComputedStyle(node).backgroundColor;
                    if (bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(bg)) ground = bg;
                    node = node.parentElement;
                }
                ground = ground || getComputedStyle(document.documentElement).backgroundColor;

                const halo = (cs.boxShadow.match(/rgb\([^)]*\)/g) || []).pop();
                // The indicator reads if either edge of it does: the ring
                // against the halo, or the halo against the ground.
                const best = Math.max(
                    ratio(cs.outlineColor, ground) || 0,
                    halo ? (ratio(halo, ground) || 0) : 0,
                    halo ? (ratio(cs.outlineColor, halo) || 0) : 0
                );
                return {
                    what: (el.getAttribute('aria-label') || el.textContent || el.tagName)
                        .trim().slice(0, 36),
                    best: Math.round(best * 100) / 100,
                    outline: cs.outlineColor,
                    ground,
                };
            }"""
        )
        if found is None:
            break
        if found["best"] < 3.0:
            worst.append(found)

    assert not worst, f"{path}: focus rings under 3:1 against their ground: {worst[:3]}"


# --------------------------------------------------------------------------
# motion, FRONTEND.md A.6


@pytest.mark.parametrize("path", ["/cennik/", "/galeria/", "/"])
def test_a_section_below_the_fold_fades_in_when_reached(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """A.6 point 3: opacity 0 to 1, once, and nothing moves."""
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    # How much waits depends on how tall the fixture's page comes out, so what
    # is asserted is the rule rather than a count: anything below the fold
    # waits, anything already on screen was never touched.
    hidden_now = page.evaluate(
        """() => [...document.querySelectorAll('[data-reveal]')].map(s => ({
            below: s.getBoundingClientRect().top >= window.innerHeight,
            waiting: s.classList.contains('is-waiting'),
        }))"""
    )
    for section in hidden_now:
        assert section["below"] == section["waiting"], f"{path}: {hidden_now}"

    page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(700)

    left = page.evaluate(
        "() => [...document.querySelectorAll('[data-reveal]')]"
        ".filter(s => getComputedStyle(s).opacity !== '1').length"
    )
    assert left == 0, f"{path} left {left} section(s) invisible after scrolling to the bottom"


@pytest.mark.parametrize("path", ["/cennik/", "/galeria/", "/kontakt/"])
def test_nothing_is_hidden_when_the_script_never_arrives(
    live_server, browser: Browser, site: SiteSettings, path: str
) -> None:
    """The failure this reveal is built to avoid.

    Hiding every section in css and having javascript hand them back is one
    stale cache from a blank page — it happened while this was being written.
    The hiding is done by the script itself now, so with javascript off there
    is nothing to hand back.
    """
    context = browser.new_context(viewport=MOBILE, java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}{path}")
        page.wait_for_selector("h1")
        invisible = page.evaluate(
            "() => [...document.querySelectorAll('[data-reveal]')]"
            ".filter(s => getComputedStyle(s).opacity !== '1').length"
        )
        assert invisible == 0, f"{path} hides {invisible} section(s) with no script to reveal them"
        assert page.locator("h1").is_visible()
    finally:
        context.close()


@pytest.mark.parametrize("path", ["/cennik/", "/"])
def test_asking_for_less_motion_hides_nothing(
    live_server, browser: Browser, site: SiteSettings, path: str
) -> None:
    """A.6: all of it switches off inside prefers-reduced-motion."""
    context = browser.new_context(viewport=MOBILE, reduced_motion="reduce")
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}{path}")
        page.wait_for_selector("h1")
        page.wait_for_timeout(300)
        invisible = page.evaluate(
            "() => [...document.querySelectorAll('[data-reveal]')]"
            ".filter(s => getComputedStyle(s).opacity !== '1').length"
        )
        assert invisible == 0, f"{path} still fades {invisible} section(s) under reduced motion"
    finally:
        context.close()


READERS = {
    "self": "el => getComputedStyle(el).transform",
    "svg": "el => getComputedStyle(el.querySelector('svg')).transform",
    "img": "el => getComputedStyle(el.querySelector('img')).transform",
    "code": "el => getComputedStyle(el.querySelector('p')).transform",
}

# What is hovered, what is measured, and what it should become. The card moves
# itself; the button moves the icon inside it, so the two cannot share a reader
# — "the svg in here, or failing that the element" quietly measured the arrow
# inside a card and reported that nothing had moved.
HOVER_MOVES = [
    # A card and a price tile rise; the tile had no answer to a pointer at all
    # before, and neither did a schedule row or the accordion's own indicator.
    ("/kursy/", ".u-card[href]", "self", "matrix(1, 0, 0, 1, 0, -4)"),
    ("/cennik/", ".u-tile", "self", "matrix(1, 0, 0, 1, 0, -4)"),
    ("/galeria/", ".u-photo", "img", "matrix(1.04, 0, 0, 1.04, 0, 0)"),
    ("/faq/", "summary", "svg", "matrix(1.15, 0, 0, 1.15, 0, 0)"),
    # An arrow travels along its own axis rather than swelling in place.
    (
        "/kontakt/",
        ".u-btn:has(svg[data-icon=external])",
        "svg",
        "matrix(1, 0, 0, 1, 2, -2)",
    ),
    # The category tile is the first thing anyone touches on the home page and
    # it had a border and a shadow but never moved. Its code letter leads.
    ("/kursy/", ".u-card.group", "self", "matrix(1, 0, 0, 1, 0, -4)"),
    ("/kursy/", ".u-card.group", "code", "matrix(1, 0, 0, 1, 0, -2)"),
]


@pytest.mark.parametrize(("path", "selector", "measure", "expected"), HOVER_MOVES)
def test_the_two_hover_moves_happen(
    live_server,
    site: SiteSettings,
    page: Page,
    path: str,
    selector: str,
    measure: str,
    expected: str,
) -> None:
    """A.6 point 4, added at the owner's request in core v7.

    A card lifts 2px and an icon inside a button grows to 1.08. Both over the
    same 120ms everything else uses, and neither moves anything but itself.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    target = page.locator(f"main {selector}:visible").first
    target.scroll_into_view_if_needed()

    read = READERS[measure]
    assert target.evaluate(read) == "none", "it should be still until pointed at"

    target.hover()
    page.wait_for_timeout(400)
    assert target.evaluate(read) == expected


@pytest.mark.parametrize(("path", "selector", "measure", "_expected"), HOVER_MOVES)
def test_neither_hover_move_happens_under_reduced_motion(
    live_server,
    browser: Browser,
    site: SiteSettings,
    path: str,
    selector: str,
    measure: str,
    _expected: str,
) -> None:
    """Zeroing the duration is not enough: it leaves the move happening in one
    frame, which is a jump rather than an answer. Asked for less motion, both
    get none — the border and the shadow still respond."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}{path}")
        page.wait_for_selector("h1")
        target = page.locator(f"main {selector}:visible").first
        target.scroll_into_view_if_needed()
        target.hover()
        page.wait_for_timeout(300)

        assert target.evaluate(READERS[measure]) == "none"
    finally:
        context.close()


def test_a_schedule_row_answers_the_pointer(live_server, site: SiteSettings, page: Page) -> None:
    """A.6 point 1 — background, which needed no new permission and had simply
    never been used on the one thing people scan straight down."""
    page.goto(f"{live_server.url}/terminy/")
    page.wait_for_selector("h1")

    row = page.locator("main [data-testid=intake-row]:visible").first
    row.scroll_into_view_if_needed()
    assert row.evaluate("el => getComputedStyle(el).backgroundColor") == "rgba(0, 0, 0, 0)"

    row.hover()
    page.wait_for_timeout(300)
    assert row.evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(250, 250, 250)"


# The row of menu items only exists from xl; below that it is a burger and a
# panel, so a mobile viewport has no pseudo element to measure at all.
DESKTOP = {"width": 1440, "height": 900}

BAR_HIDDEN = "matrix(0, 0, 0, 1, 0, 0)"
BAR_DRAWN = "matrix(1, 0, 0, 1, 0, 0)"
READ_BAR = "el => getComputedStyle(el, '::after').transform"


def test_the_menu_underline_sweeps_rather_than_appears(
    live_server, browser: Browser, site: SiteSettings
) -> None:
    """A.6 point 4. A border-colour fade told you an item was hovered without
    anything appearing to move; the bar now grows from the left."""
    context = browser.new_context(viewport=DESKTOP)
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}/")
        page.wait_for_selector("h1")

        item = page.locator(".u-header .u-navlink:not([aria-current])").first
        assert item.evaluate(READ_BAR) == BAR_HIDDEN, "the bar should start at nothing"

        item.hover()
        page.wait_for_timeout(300)
        assert item.evaluate(READ_BAR) == BAR_DRAWN
    finally:
        context.close()


def test_the_current_page_keeps_its_underline(
    live_server, browser: Browser, site: SiteSettings
) -> None:
    """aria-current is the hook, so the marker cannot drift from what a screen
    reader is told."""
    context = browser.new_context(viewport=DESKTOP)
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}/kursy/")
        page.wait_for_selector("h1")

        current = page.locator('.u-header .u-navlink[aria-current="page"]').first
        assert current.count() == 1
        assert current.evaluate(READ_BAR) == BAR_DRAWN
    finally:
        context.close()


def test_the_map_never_covers_the_header(live_server, site: SiteSettings, page: Page) -> None:
    """Leaflet numbers its panes from 400 and its controls to 1000, and those
    are absolute figures. Straight on the page they beat a sticky header at
    z-30, so scrolling drove the map over the menu."""
    page.goto(f"{live_server.url}/kontakt/")
    page.wait_for_selector("h1")

    page.locator("[data-map]").scroll_into_view_if_needed()
    page.wait_for_selector(".leaflet-tile")
    page.wait_for_timeout(300)

    # What is actually painted in the middle of the header band.
    on_top = page.evaluate(
        """() => {
            const header = document.querySelector('.u-header').getBoundingClientRect();
            const el = document.elementFromPoint(header.width / 2, header.top + header.height / 2);
            return {
                inHeader: !!(el && el.closest('.u-header')),
                inMap: !!(el && el.closest('[data-map]')),
                tag: el ? el.tagName.toLowerCase() : null,
            };
        }"""
    )
    assert on_top["inHeader"], f"the header is not on top where it should be: {on_top}"
    assert not on_top["inMap"], f"the map is painting over the header: {on_top}"


def test_an_answer_opens_over_time(live_server, site: SiteSettings, page: Page) -> None:
    """A.6 point 2 gives the accordion 180ms and <details> has none of its own:
    the content is not rendered while it is shut, so there is no height to
    travel from."""
    page.goto(f"{live_server.url}/faq/")
    page.wait_for_selector("h1")

    item = page.locator("[data-accordion]").first
    body = item.locator("[data-accordion-body]")
    item.locator("summary").click()

    # Caught in the middle: open, but not yet at its full height.
    page.wait_for_timeout(60)
    mid = body.evaluate("el => el.getBoundingClientRect().height")
    page.wait_for_timeout(400)
    settled = body.evaluate("el => el.getBoundingClientRect().height")

    assert settled > 0, "the answer never appeared"
    assert mid < settled, f"it arrived at once: {mid} then {settled}"
    assert item.evaluate("el => el.open")


def test_an_answer_still_opens_without_javascript(
    live_server, browser: Browser, site: SiteSettings
) -> None:
    """<details> is the reason this degrades: with no script it toggles on its
    own, instantly, which is what it did before any of this."""
    context = browser.new_context(viewport=MOBILE, java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(f"{live_server.url}/faq/")
        page.wait_for_selector("h1")
        item = page.locator("[data-accordion]").first
        item.locator("summary").click()
        assert item.evaluate("el => el.open")
        assert item.locator("[data-accordion-body]").is_visible()
    finally:
        context.close()
