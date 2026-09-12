"""axe-core over every public page, REDESIGN.md R9 point 3.

axe is vendored into tests/vendor rather than pulled from a cdn at test time:
tech.md section 2 bans third party hosts on the site, and a test suite that
needs the network to tell you whether the site is accessible is a test suite
that goes red when a cdn does.

Only serious and critical are enforced. Minor and moderate are advisory in
axe's own taxonomy and mostly stylistic; failing the gate on them would train
everyone to skip the gate.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page

from apps.core.models import SiteSettings
from tests.e2e.conftest import PAGES

pytestmark = pytest.mark.django_db

AXE = Path(__file__).parent.parent / "vendor" / "axe.min.js"

BLOCKING = ("serious", "critical")


def audit(page: Page, url: str) -> list[dict[str, Any]]:
    """Run axe over the page and return the blocking violations.

    Audited with reduced motion on. REDESIGN.md C.3 row 1 brings every section
    in with a scroll-driven animation, so on a page that has just loaded
    everything below the fold sits at the start of its range — opacity 0 — and
    axe reports colour-contrast failures against text it cannot see. The colours
    themselves measure 14:1; what axe is looking at is the fade.

    prefers-reduced-motion is the honest way to stop that rather than a
    wait-and-scroll dance: C.5 makes the whole motion layer resolve to
    "everything visible, nothing moving", which is the same page with the same
    colours and no animation state to race. It is also a state real readers are
    in, so anything this finds is something somebody actually sees.
    """
    page.emulate_media(reduced_motion="reduce")
    page.goto(url)
    page.wait_for_selector("h1")
    page.add_script_tag(path=str(AXE))

    result = page.evaluate(
        """async () => {
            const run = await axe.run(document, {
                resultTypes: ['violations'],
                runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
            });
            return run.violations.map(v => ({
                id: v.id,
                impact: v.impact,
                help: v.help,
                nodes: v.nodes.slice(0, 3).map(n => n.html.slice(0, 160)),
            }));
        }"""
    )
    return [item for item in result if item["impact"] in BLOCKING]


@pytest.mark.a11y
@pytest.mark.parametrize("path", PAGES)
def test_the_page_has_no_serious_accessibility_violations(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    violations = audit(page, f"{live_server.url}{path}")
    assert not violations, f"{path}\n{json.dumps(violations, indent=2, ensure_ascii=False)}"


@pytest.mark.a11y
@pytest.mark.parametrize("path", ["/", "/kursy/kat-b/", "/kontakt/", "/cennik/"])
def test_the_header_is_told_apart_from_the_page_it_floats_on(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """B.7 point 0, and the defect this replaced.

    The header used to be an ink band over a light page, because the palette
    before v25 had no other way to separate the two: it had tried taking the
    page ground with a hairline underneath, and in a dark theme both went near
    black and the band dissolved into the page at 1.4:1.

    B.2 gave it a third option and B.7 point 0 takes it. The bar is the page's
    own ground at 82% with a saturating blur behind it, so what separates the
    two is not a colour at all — it is the blur, and, once the page has
    scrolled, a hairline in --line. So the colour ratio is expected to be about
    1:1 and asserting otherwise would be asserting the old contract.

    What has to hold instead is that the separation exists and is not
    transparent: the bar must carry a background, or the menu ends up as words
    floating over whatever scrolls under it — which is what the @supports
    fallback in motion.css is there to prevent.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    found = page.evaluate(
        """() => {
            const bar = document.querySelector('.u-header');
            const style = getComputedStyle(bar);
            const [r, g, b, a] = style.backgroundColor.match(/[0-9.]+/g).map(Number);
            return {
                alpha: a === undefined ? 1 : a,
                blur: style.backdropFilter || style.webkitBackdropFilter || 'none',
                sticky: style.position,
            };
        }"""
    )

    assert found["sticky"] == "sticky", "the header has to stay with the reader"
    assert found["alpha"] >= 0.8, (
        f"{path}: the header background is {found['alpha']} opaque; below that the "
        "menu reads over whatever scrolls under it"
    )
    assert "blur" in found["blur"], f"{path}: B.7 point 0 asks for the saturating blur"


@pytest.mark.a11y
@pytest.mark.parametrize("path", ["/cennik/", "/terminy/", "/o-nas/", "/certyfikaty/", "/kontakt/"])
def test_the_dark_band_reads_as_well_as_the_page(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """Every inner page carries one inverted band now, and axe measures what is
    painted on it — the grounds publish their own foreground, so a component
    that named a page colour instead would show up here."""
    violations = audit(page, f"{live_server.url}{path}")
    assert not violations, f"{path}\n{json.dumps(violations, indent=2, ensure_ascii=False)}"

    # u-dark-card since core v25, when B.1 moved the darkness into the cards
    # and dropped the purple ground; u-ground-ink is its alias.
    band = page.locator(".u-dark-card, .u-ground-ink").first
    assert band.count() == 1, f"{path} has no inverted band"


@pytest.mark.parametrize(
    "path", ["/cennik/", "/terminy/", "/o-nas/", "/certyfikaty/", "/kontakt/", "/"]
)
def test_no_dark_section_touches_the_dark_footer(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """The footer is a dark card the full width of the page, B.7 point 11.

    A dark section directly above it makes one very tall dark region, and the
    28px radius along the footer's top — the shape that is supposed to say
    "this is the end of the page" — has nothing to read against. The seam is
    lost exactly where the page is trying to close.

    The rule predates the redesign: it used to be written against two purple
    bands and the purple is gone, but the geometry is identical. So the page's
    one dark block sits mid page and the closing action band takes the page
    ground, which is what makes the footer's corners visible.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    clash = page.evaluate(
        """() => {
            const footer = document.querySelector('footer');
            let previous = footer && footer.previousElementSibling;
            while (previous && !previous.matches('section, div')) {
                previous = previous.previousElementSibling;
            }
            const dark = (el) => !!el && (
                el.classList.contains('u-dark-card') ||
                el.classList.contains('u-ground-ink') ||
                !!el.querySelector(':scope > .u-dark-card, :scope > .u-ground-ink')
            );
            return dark(previous);
        }"""
    )
    assert not clash, f"{path} ends on a dark section, straight above the dark footer"


@pytest.mark.a11y
def test_a_card_on_a_dark_band_takes_the_page_back(
    live_server, site: SiteSettings, page: Page
) -> None:
    """A white card sitting on an inverted band is the page, not the band.

    Without that it kept the band's white foreground and printed white on
    white: the tile title vanished and the outlined button became an empty
    rectangle. The heading rule was the other half — it reached into the card
    and it outranks a text-ink utility, a class plus an element beating a
    class on its own.
    """
    page.emulate_media(reduced_motion="reduce")
    page.goto(f"{live_server.url}/certyfikaty/")
    page.wait_for_selector("h1")

    tile = page.locator(".u-dark-card .u-card, .u-ground-ink .u-card").first
    tile.scroll_into_view_if_needed()

    measured = tile.evaluate(
        """(el) => {
            const lum = (colour) => {
                const [r, g, b] = colour.match(/[0-9.]+/g).map(Number);
                const ch = (v) => {
                    v /= 255;
                    return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
                };
                return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
            };
            const ratio = (a, b) => {
                const x = lum(a), y = lum(b);
                return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
            };
            const bg = getComputedStyle(el).backgroundColor;
            const heading = el.querySelector('h2, h3, h4');
            return {
                heading: heading ? ratio(getComputedStyle(heading).color, bg) : null,
                onGround: getComputedStyle(el).getPropertyValue('--on-ground').trim(),
                pageInk: getComputedStyle(document.documentElement)
                    .getPropertyValue('--ink').trim(),
            };
        }"""
    )
    assert measured["heading"] is not None, "the tile has no heading to check"
    assert measured["heading"] >= 4.5, f"the heading reads {measured['heading']:.2f}:1 on its card"
    # Compared against the page's own --ink rather than a literal triple. The
    # triple changed at core v25 and this assertion is not about which near
    # black it is — it is about the card publishing the page's pair rather than
    # inheriting the band's.
    assert measured["onGround"] == measured["pageInk"], (
        "the card did not take the page ground back"
    )
