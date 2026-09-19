from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page

NARROW = {"width": 320, "height": 720}


@pytest.fixture
def narrow_page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=NARROW)
    page = context.new_page()
    yield page
    context.close()


def test_wide(live_server, narrow_page):
    narrow_page.goto(f"{live_server.url}/o-nas/")
    out = narrow_page.evaluate("""() => Array.from(document.querySelectorAll('main *'))
        .map(n => ({r: Math.round(n.getBoundingClientRect().right*10)/10,
                    t: n.tagName, c: (n.getAttribute('class')||'').slice(0,60)}))
        .filter(x => x.r > 320).slice(0, 8)""")
    for o in out:
        print(o)
