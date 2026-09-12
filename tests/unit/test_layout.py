"""The frame: header, navigation, footer, error pages. FRONTEND.md F2.

Every assertion here is one of F2's acceptance criteria. They are checked
against rendered html rather than against the templates, because what matters
is what a visitor's browser receives.
"""

import re

import pytest
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse

from apps.core.models import SiteSettings

pytestmark = pytest.mark.django_db

FOCUSABLE = re.compile(
    r'<(?:a\s[^>]*href=|button\b|input\b|select\b|textarea\b|[a-z]+\s[^>]*tabindex="(?!-1))',
    re.I,
)


@pytest.fixture
def settings_row() -> SiteSettings:
    row = SiteSettings.get_solo()
    row.legal_name = "OSK Ostrycharz Ośrodek Szkolenia Kierowców"
    row.short_name = "OSK Ostrycharz"
    row.street = "ul. Asnyka 7"
    row.postal_code = "98-300"
    row.city = "Wieluń"
    row.nip = "7671234567"
    row.email = "biuro@example.com"
    row.phone_primary = "691 570 489"
    row.bank_account = "12 3456 7890 1234 5678 9012 3456"
    row.bank_account_public = True
    row.save()
    return row


def body(client: Client, url: str = "/") -> str:
    """The chrome is the same on every page, so the test takes the one page that
    always renders. /kursy/ used to be it; a listing with no courses is a 404
    now, and these tests are about the header and the footer, not the offer."""
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode()


def test_the_skip_link_is_the_first_focusable_thing(
    client: Client, settings_row: SiteSettings
) -> None:
    """F2 point 1. A keyboard user must reach it before anything else."""
    html = body(client)
    first = FOCUSABLE.search(html)
    assert first, "nothing focusable on the page at all"
    assert 'href="#content"' in html[first.start() : first.start() + 200]
    assert 'id="content"' in html


def test_the_skip_link_is_hidden_until_it_takes_focus(
    client: Client, settings_row: SiteSettings
) -> None:
    html = body(client)
    link = re.search(r'<a\s[^>]*href="#content"[^>]*>', html)
    assert link
    assert "sr-only" in link.group()
    assert "focus:not-sr-only" in link.group()


def first_level_titles(markup: str) -> list[str]:
    """The text of every first level menu item, however it is marked up.

    The anchors carry more than a word now — B.7 gives each row in the mobile
    panel a travelling arrow — so a pattern that only matched bare text stopped
    seeing any of them and the assertion silently had nothing to look at. This
    strips the tags instead of assuming there are none.
    """
    rows = re.findall(r"<li[^>]*>\s*(<a[^>]*>.*?</a>)", markup, re.S)
    return [re.sub(r"<[^>]+>", " ", row).strip() for row in rows]


def test_kontakt_is_first_level_on_the_desktop_menu(
    client: Client, settings_row: SiteSettings
) -> None:
    """tech.md section 7 forbids hiding it in a submenu."""
    html = body(client)
    nav = re.search(r'<nav aria-label="Główna nawigacja"(?![^>]*hidden).*?</nav>', html, re.S)
    assert nav, "the desktop nav did not render"
    assert "Kontakt" in first_level_titles(nav.group())


def test_kontakt_is_first_level_on_the_mobile_panel(
    client: Client, settings_row: SiteSettings
) -> None:
    html = body(client)
    panel = re.search(r'<dialog id="main-menu".*?</dialog>', html, re.S)
    assert panel, "the mobile panel did not render"
    assert "Kontakt" in first_level_titles(panel.group())


def test_the_burger_announces_the_panel_it_controls(
    client: Client, settings_row: SiteSettings
) -> None:
    """F2 point 4: aria-expanded, and a name, because it is an icon alone."""
    html = body(client)
    burger = re.search(r'<button[^>]*data-modal-open="main-menu"[^>]*>', html)
    assert burger
    assert 'aria-expanded="false"' in burger.group()
    assert 'aria-controls="main-menu"' in burger.group()
    assert "aria-label=" in burger.group()


def test_the_menus_never_render_at_the_same_time(
    client: Client, settings_row: SiteSettings
) -> None:
    """One is xl and up, the other below it. Two menus at once is two tab stops
    through the same links."""
    html = body(client)
    nav = re.search(r'<nav aria-label="Główna nawigacja"[^>]*class="([^"]*)"', html)
    panel = re.search(r'<dialog id="main-menu"[^>]*class="([^"]*)"', html)
    assert nav and panel
    assert "hidden xl:block" in nav.group(1)
    assert "xl:hidden" in panel.group(1)


def test_the_footer_carries_the_four_columns(client: Client, settings_row: SiteSettings) -> None:
    """FRONTEND.md A.9 point 10, in the order it fixes them."""
    html = body(client)
    footer = re.search(r"<footer.*?</footer>", html, re.S)
    assert footer
    labels = re.findall(r'<p class="label u-muted-on-ground">([^<]+)</p>', footer.group())
    assert labels == ["Dane firmy", "Kurs", "Formalności", "Ośrodek"]
    for url in (
        reverse("courses:detail", kwargs={"slug": "kat-b"}),
        reverse("courses:pricing"),
        reverse("core:pass_rates"),
        reverse("core:downloads"),
        reverse("core:page", kwargs={"slug": "zapisy"}),
        reverse("gallery:index"),
        reverse("links:useful"),
        reverse("core:page", kwargs={"slug": "polityka-prywatnosci"}),
        reverse("core:page", kwargs={"slug": "rodo"}),
    ):
        assert f'href="{url}"' in footer.group(), f"{url} missing from the footer"


def test_the_footer_names_no_route_this_school_does_not_sell(
    client: Client, settings_row: SiteSettings
) -> None:
    """The professional courses and the psychotests are the previous client's.

    Their routes still exist in the url map with no course behind them, so a
    footer link to one is a 404 on every page of the site.
    """
    footer = re.search(r"<footer.*?</footer>", body(client), re.S).group()

    for absent in ("/kierowca-zawodowy/", "/badania-psychologiczne/", "/wozki-widlowe/"):
        assert absent not in footer


def test_the_footer_never_shows_the_bank_account(
    client: Client, settings_row: SiteSettings
) -> None:
    """A.9 point 10 and tech.md section 1, even with the flag switched on."""
    assert settings_row.bank_account_public is True
    footer = re.search(r"<footer.*?</footer>", body(client), re.S)
    assert footer
    assert settings_row.bank_account not in footer.group()
    assert settings_row.bank_account.replace(" ", "") not in footer.group()


def test_the_footer_is_a_dark_card(client: Client, settings_row: SiteSettings) -> None:
    """B.7 point 11: dark, and rounded 28px along the top only.

    The purple ground it used to sit on went with core v25 — B.1 cut the
    palette to two accents and the purple was a third. The radius is the hero's
    own, so the page opens and closes on the same shape.
    """
    footer = re.search(r"<footer[^>]*>", body(client))
    assert footer
    assert "u-dark-card" in footer.group()
    assert "rounded-t-hero" in footer.group()


def test_the_header_shrinks_from_a_sentinel_rather_than_a_scroll_handler(
    client: Client, settings_row: SiteSettings
) -> None:
    """B.7 point 0 and R4 point 1.

    76px down to 64px with a hairline appearing, and the class that does it is
    toggled from an IntersectionObserver on a one pixel sentinel above the
    header. R4 asks for it that way because the alternative — a scroll
    listener — runs on every frame of every scroll for the life of the page to
    answer a question whose value changes twice.

    The sentinel has to be outside the header: the header is sticky and never
    leaves the viewport, so it can never observe itself.
    """
    html = body(client)
    assert re.search(r'<header[^>]*class="[^"]*u-header', html)

    sentinel = html.index("data-header-sentinel")
    assert sentinel < html.index("<header"), "the sentinel must sit above the header"


@override_settings(DEBUG=False)
def test_the_404_page_offers_a_way_out(client: Client, settings_row: SiteSettings) -> None:
    """A.10: large type, the main sections, and the phone."""
    response = client.get("/nie-ma-takiej-strony/")
    assert response.status_code == 404
    html = response.content.decode()
    assert "<h1" in html
    for url in (reverse("courses:list"), reverse("courses:intakes"), reverse("core:contact")):
        assert f'href="{url}"' in html
    assert f'href="tel:{settings_row.phone_primary.replace(" ", "")}"' in html


def test_the_500_page_stands_on_its_own() -> None:
    """django renders 500.html with no context and no request.

    So it is checked the way django will render it: no context at all. Anything
    that reached for site_settings or the request would raise here, and a 500
    page that raises while rendering has nowhere left to fall.
    """
    html = render_to_string("500.html")
    assert "<h1" in html
    assert 'href="/kontakt/"' in html
    assert "Błąd 500" in html
    # It must not drag in the frame, which needs the context processors.
    assert "u-header" not in html
    assert "<footer" not in html
