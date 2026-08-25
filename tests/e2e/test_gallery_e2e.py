"""End to end pass over the gallery, DEV.md S0.9.

This is the only test that runs the real javascript. It is what proves Alpine is
actually loaded and self hosted, which no server side assertion can show.

Needs a browser: `playwright install chromium`. Run with `make e2e`.
"""

import pytest
from playwright.sync_api import Page

from apps.gallery.models import GalleryImage
from tests.factories import GalleryImageFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def images() -> list[GalleryImage]:
    return [
        GalleryImageFactory(section=GalleryImage.Section.SCHOOL, alt=f"Zdjęcie {n}")
        for n in range(1, 4)
    ]


def test_gallery_renders_on_a_phone(live_server, page: Page, images: list[GalleryImage]) -> None:
    page.goto(f"{live_server.url}/galeria/")

    assert page.locator("h1").count() == 1
    assert "Galeria" in page.title()
    assert page.locator("picture img").count() == len(images)


def test_page_does_not_scroll_sideways(live_server, page: Page, images: list[GalleryImage]) -> None:
    """A horizontal scrollbar on a 390px phone is a layout bug."""
    page.goto(f"{live_server.url}/galeria/")

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0


def test_alpine_is_running_and_the_lightbox_opens(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_function("() => window.Alpine !== undefined")

    dialog = page.locator('[role="dialog"]')
    assert dialog.is_hidden()

    page.locator("button:has(picture)").first.click()
    dialog.wait_for(state="visible")
    assert dialog.is_visible()

    page.keyboard.press("Escape")
    dialog.wait_for(state="hidden")
    assert dialog.is_hidden()


def test_mobile_menu_opens_on_click(live_server, page: Page) -> None:
    """tech.md section 7: click only, and Kontakt stays on the first level."""
    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_function("() => window.Alpine !== undefined")

    menu = page.locator("#main-menu")
    toggle = page.get_by_role("button", name="Menu")
    assert menu.is_hidden()

    toggle.click()
    menu.wait_for(state="visible")
    assert menu.get_by_role("link", name="Kontakt").is_visible()


def test_no_asset_comes_from_a_third_party_host(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    """tech.md section 2: nothing on a public page may be fetched off site."""
    external: list[str] = []
    page.on(
        "request",
        lambda request: (
            external.append(request.url)
            if not request.url.startswith((live_server.url, "data:", "blob:"))
            else None
        ),
    )

    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_load_state("networkidle")

    assert not external, f"off site requests: {external}"
