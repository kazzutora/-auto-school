"""End to end pass over the gallery, DEV.md S0.9.

This is the only test that runs the real javascript. It is what proves Alpine is
actually loaded and self hosted, which no server side assertion can show.

Needs a browser: `playwright install chromium`. Run with `make e2e`.
"""

import pytest
from playwright.sync_api import Browser, Page, expect

from apps.gallery.models import GalleryImage
from tests.factories import GalleryImageFactory, photo_bytes

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


# --------------------------------------------------------------------------
# DEV.md S6.1


def test_the_focus_comes_back_to_the_tile(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    """The acceptance criterion: closing from the keyboard returns the focus.

    Without it a keyboard visitor lands back on <body> and has to tab through
    the whole page again to reach the next photo.
    """
    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_function("() => window.Alpine !== undefined")

    second = page.locator("button:has(picture)").nth(1)
    second.click()
    page.locator('[role="dialog"]').wait_for(state="visible")

    page.keyboard.press("Escape")
    page.locator('[role="dialog"]').wait_for(state="hidden")

    # Alpine hands the focus back on the next tick, so wait for it rather than
    # reading document.activeElement the instant the dialog disappears.
    page.wait_for_function("() => document.activeElement.tagName === 'BUTTON'")
    assert second.evaluate("node => node === document.activeElement")


def test_the_arrows_walk_through_the_photos(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_function("() => window.Alpine !== undefined")

    page.locator("button:has(picture)").first.click()
    dialog = page.locator('[role="dialog"]')
    dialog.wait_for(state="visible")

    shown = dialog.locator("figure:visible img")
    expect(shown).to_have_attribute("alt", "Zdjęcie 1")

    page.keyboard.press("ArrowRight")
    expect(shown).to_have_attribute("alt", "Zdjęcie 2")

    page.keyboard.press("ArrowLeft")
    expect(shown).to_have_attribute("alt", "Zdjęcie 1")

    # Walking left off the first photo wraps to the last one.
    page.keyboard.press("ArrowLeft")
    expect(shown).to_have_attribute("alt", "Zdjęcie 3")


def test_no_original_is_downloaded_before_the_lightbox_opens(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    """DEV.md S6.1 allows 400 KB above the fold.

    The tiles are renditions of a few kilobytes each. The originals behind them
    are the whole gallery in full size, and a hidden image with no loading
    attribute is fetched anyway.
    """
    fetched: list[str] = []
    page.on("request", lambda request: fetched.append(request.url))

    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_load_state("networkidle")

    originals = [url for url in fetched if "/media/gallery/" in url]
    assert not originals, f"originals downloaded before anyone asked: {originals}"

    page.locator("button:has(picture)").first.click()
    page.locator('[role="dialog"]').wait_for(state="visible")
    page.wait_for_function(
        "() => performance.getEntriesByType('resource')"
        ".some(entry => entry.name.includes('/media/gallery/'))"
    )


def test_the_filter_works_without_javascript(live_server, browser: Browser) -> None:
    """Plain links, so the sections survive a phone that blocks scripts."""
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL, alt="Biuro")
    GalleryImageFactory(section=GalleryImage.Section.VEHICLES, alt="Pojazd")

    context = browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
    page = context.new_page()
    page.goto(f"{live_server.url}/galeria/")

    assert page.locator("picture img").count() == 2

    page.get_by_role("link", name="Pojazdy").click()
    page.wait_for_url("**/galeria/?section=vehicles")

    assert page.locator("picture img").count() == 1
    assert page.locator("h2").inner_text() == "Pojazdy"
    context.close()


def test_the_page_stays_inside_its_weight_budget(live_server, page: Page) -> None:
    """DEV.md S6.1: 400 KB above the fold, on photographs rather than swatches.

    Twelve of these originals are 1.4 MB together. The page is allowed to fetch
    the renditions behind them and nothing else.
    """
    for section in GalleryImage.Section:
        for number in range(3):
            GalleryImageFactory(
                section=section, alt=f"Zdjęcie {section} {number}", image=photo_bytes()
            )

    page.goto(f"{live_server.url}/galeria/")
    page.wait_for_load_state("networkidle")

    images = page.evaluate(
        """() => performance.getEntriesByType('resource')
               .filter(entry => entry.initiatorType === 'img')
               .map(entry => entry.transferSize || entry.encodedBodySize || 0)"""
    )
    widths = page.evaluate(
        "() => Array.from(document.images).filter(img => img.complete && img.naturalWidth)"
        ".map(img => img.naturalWidth)"
    )

    assert images, "no image was fetched at all"
    assert sum(images) <= 400 * 1024, f"{round(sum(images) / 1024)} KB of images on first load"
    # A full size photo on the page would mean the renditions were bypassed.
    assert max(widths) <= 960
