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
