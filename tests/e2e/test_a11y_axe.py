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
def test_the_dark_theme_is_audited_too(live_server, site: SiteSettings, page: Page) -> None:
    """A.2: the dark theme is a swap of roles, and it has to hold the same bar.

    Contrast is the rule most likely to break in one theme and not the other,
    and axe measures it against what is actually painted.
    """
    page.emulate_media(color_scheme="dark")
    for path in ("/", "/kursy/kat-b/", "/kontakt/", "/cennik/"):
        violations = audit(page, f"{live_server.url}{path}")
        assert not violations, (
            f"dark {path}\n{json.dumps(violations, indent=2, ensure_ascii=False)}"
        )
