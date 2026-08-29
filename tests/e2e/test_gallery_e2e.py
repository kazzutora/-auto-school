"""End to end pass over the gallery, DEV.md S0.9 and FRONTEND.md F9.

This is the only test that runs the real javascript. It is what proves Alpine is
actually loaded and self hosted, which no server side assertion can show.

The lightbox is a native <dialog>, so it carries the dialog role implicitly and
there is no [role="dialog"] to select on. The selector is the element itself,
scoped to the grid that owns it — the header's mobile menu is a <dialog> too.

Needs a browser: `playwright install chromium`. Run with `make e2e`.
"""

import pytest
from playwright.sync_api import Browser, Page, expect

from apps.gallery.models import GalleryImage
from tests.factories import CertificateFactory, GalleryImageFactory, photo_bytes

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

    dialog = page.locator("[data-testid] > dialog")
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
    page.locator("[data-testid] > dialog").wait_for(state="visible")

    page.keyboard.press("Escape")
    page.locator("[data-testid] > dialog").wait_for(state="hidden")

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
    dialog = page.locator("[data-testid] > dialog")
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
    page.locator("[data-testid] > dialog").wait_for(state="visible")
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


def test_a_certificate_scan_opens_and_gives_the_focus_back(live_server, page: Page) -> None:
    """DEV.md S6.2: the preview opens the big scan, and the keyboard gets out."""
    CertificateFactory(title="Certyfikat ADR")
    CertificateFactory(title="Zaświadczenie o wpisie")

    page.goto(f"{live_server.url}/certyfikaty/")
    page.wait_for_function("() => window.Alpine !== undefined")

    dialog = page.locator("[data-testid] > dialog")
    assert dialog.is_hidden()

    second = page.locator("button:has(picture)").nth(1)
    second.click()
    dialog.wait_for(state="visible")
    expect(dialog.locator("figure:visible img")).to_have_attribute("alt", "Zaświadczenie o wpisie")

    page.keyboard.press("Escape")
    dialog.wait_for(state="hidden")

    page.wait_for_function("() => document.activeElement.tagName === 'BUTTON'")
    assert second.evaluate("node => node === document.activeElement")


def test_the_certificate_page_does_not_preload_the_scans(live_server, page: Page) -> None:
    CertificateFactory.create_batch(3, image=photo_bytes())

    fetched: list[str] = []
    page.on("request", lambda request: fetched.append(request.url))

    page.goto(f"{live_server.url}/certyfikaty/")
    page.wait_for_load_state("networkidle")

    originals = [url for url in fetched if "/media/certificates/" in url]
    assert not originals, f"scans downloaded before anyone asked: {originals}"


# --------------------------------------------------------------------------
# FRONTEND.md F9


def test_the_lightbox_is_reachable_with_a_keyboard_alone(
    live_server, page: Page, images: list[GalleryImage]
) -> None:
    """F9: open, walk, close, and land back where you started — no mouse.

    A gallery that only answers a click is a gallery half the people who need
    the big version cannot open.
    """
    page.goto(f"{live_server.url}/galeria/")

    first = page.locator("[data-testid=gallery-grid] button[aria-haspopup=dialog]").first
    first.focus()
    page.keyboard.press("Enter")

    dialog = page.locator("[data-testid] > dialog")
    dialog.wait_for(state="visible")
    assert page.evaluate("() => document.querySelector('dialog[open]').matches(':modal')")

    # expect(), not evaluate(): alpine updates on the next tick, so reading the
    # dom the instant the key goes down reads the frame before the change.
    shown = dialog.locator("figure:visible img")
    expect(shown).to_have_attribute("alt", "Zdjęcie 1")

    page.keyboard.press("ArrowRight")
    expect(shown).to_have_attribute("alt", "Zdjęcie 2")

    page.keyboard.press("ArrowLeft")
    expect(shown).to_have_attribute("alt", "Zdjęcie 1")

    page.keyboard.press("Escape")
    dialog.wait_for(state="hidden")

    # Back on the tile that opened it, which is where the reader was.
    assert page.evaluate(
        "() => document.activeElement === "
        "document.querySelector('[data-testid=gallery-grid] button[aria-haspopup=dialog]')"
    )


@pytest.mark.a11y
def test_no_picture_anywhere_ships_an_empty_alt(live_server, page: Page) -> None:
    """F9: every image here is content, so every one of them says what it shows.

    A decorative image would carry alt="" and aria-hidden, and there are none —
    the school's own photographs are the whole point of these three pages.
    """
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL, alt="Plac manewrowy")
    CertificateFactory(title="Certyfikat ADR")

    for path in ("/galeria/", "/certyfikaty/"):
        page.goto(f"{live_server.url}{path}")
        bad = page.evaluate(
            "() => [...document.querySelectorAll('main img')]"
            ".filter(i => !(i.getAttribute('alt') || '').trim())"
            ".map(i => i.currentSrc || i.src)"
        )
        assert bad == [], f"{path} ships {len(bad)} image(s) with no alt"


@pytest.mark.a11y
def test_every_picture_reserves_its_own_box(live_server, page: Page) -> None:
    """F9: width and height on every image, so nothing jumps as they land.

    That is the CLS budget in A.11: a grid that reflows while the photos arrive
    moves whatever the reader was about to tap.
    """
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL, alt="Plac manewrowy")
    page.goto(f"{live_server.url}/galeria/")

    missing = page.evaluate(
        "() => [...document.querySelectorAll('main img')]"
        ".filter(i => !i.getAttribute('width') || !i.getAttribute('height'))"
        ".map(i => i.alt)"
    )
    assert missing == []


def test_a_long_legal_page_gets_a_contents_list(live_server, page: Page) -> None:
    """F10: a contents list past five sections, and nothing under six.

    Built in the browser rather than by the renderer, so this is the only place
    it can be checked. A reader without javascript loses a shortcut, not text.
    """
    from apps.core.models import Page as FlatPage

    def publish(sections: int) -> None:
        # One hash, not two: render_markdown shifts headings down a level, so a
        # page owns exactly one h1 and it comes from the template. A top level
        # section in the source is "#" and arrives as an h2.
        FlatPage.objects.all().delete()
        body = "\n\n".join(f"# Sekcja {n}\n\nTreść {n}." for n in range(1, sections + 1))
        FlatPage.objects.create(slug="rodo", title="RODO", body=body, is_published=True)

    publish(4)
    page.goto(f"{live_server.url}/rodo/")
    page.wait_for_function("() => window.htmx !== undefined")
    assert page.locator("[data-toc]").is_hidden(), "four sections do not need an index"

    publish(7)
    page.goto(f"{live_server.url}/rodo/")
    toc = page.locator("[data-toc]")
    toc.wait_for(state="visible")

    links = toc.locator("a")
    assert links.count() == 7

    # Every entry actually lands on its heading.
    first = links.first
    target = first.get_attribute("href")
    assert target and target.startswith("#")
    assert page.locator(f"h2{target}").count() == 1

    first.click()
    assert page.evaluate("() => location.hash") == target


def test_a_long_url_in_a_policy_never_pushes_the_page_sideways(live_server, page: Page) -> None:
    """F10, checked at 390px where it would actually happen."""
    from apps.core.models import Page as FlatPage

    FlatPage.objects.all().delete()
    FlatPage.objects.create(
        slug="rodo",
        title="RODO",
        body=(
            "# Klauzula\n\nSzczegóły: "
            "https://uodo.gov.pl/pl/file/bardzo-dluga-nazwa-dokumentu-informacyjnego-"
            "o-przetwarzaniu-danych-osobowych-kandydatow-na-kierowcow-2024.pdf"
        ),
        is_published=True,
    )

    page.goto(f"{live_server.url}/rodo/")
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"the policy scrolls {overflow}px sideways"
