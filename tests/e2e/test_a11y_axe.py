"""axe-core over every public page, FRONTEND.md F11 point 3.

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
    """Run axe over the page as it stands and return the blocking violations."""
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
def test_the_header_never_becomes_the_page(
    live_server, site: SiteSettings, page: Page, path: str
) -> None:
    """The defect that ended the dark theme, kept from coming back.

    The header used to take the page ground, and a dark theme turned both near
    black — so on every page but the home one the band dissolved into the page
    and the only thing between them was a hairline at 1.4:1. It is an ink band
    over a light page now, and these two must stay far apart.
    """
    page.goto(f"{live_server.url}{path}")
    page.wait_for_selector("h1")

    found = page.evaluate(
        """() => {
            const lum = (colour) => {
                const [r, g, b] = colour.match(/[0-9.]+/g).map(Number);
                const ch = (v) => {
                    v /= 255;
                    return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
                };
                return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
            };
            const header = getComputedStyle(document.querySelector('.u-header')).backgroundColor;
            const body = getComputedStyle(document.body).backgroundColor;
            const a = lum(header), b = lum(body);
            return {
                header: header,
                body: body,
                ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
            };
        }"""
    )
    assert found["ratio"] >= 3.0, f"{path}: header {found['header']} on page {found['body']}"
