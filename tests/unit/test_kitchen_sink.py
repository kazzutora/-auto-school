"""The kitchen sink is the review surface for the design system, DEV.md S0.7."""

import re

import pytest
from django.http import Http404
from django.test import RequestFactory, override_settings

from apps.core.views import kitchen_sink

from tests.conftest import images_without_alt

pytestmark = pytest.mark.django_db


def render_sink() -> str:
    request = RequestFactory().get("/__kitchen-sink/")
    return kitchen_sink(request).content.decode()


@override_settings(DEBUG=True)
def test_every_primitive_renders() -> None:
    body = render_sink()

    # An unresolved component would still be sitting there as a c- tag.
    assert not re.findall(r"<c-[a-z.-]+", body)


@override_settings(DEBUG=True)
def test_exactly_one_h1() -> None:
    """tech.md section 8: one h1 per page, no more and no less."""
    assert len(re.findall(r"<h1[ >]", render_sink())) == 1


@override_settings(DEBUG=True)
@pytest.mark.a11y
def test_no_image_ships_an_empty_alt() -> None:
    body = render_sink()
    assert re.findall(r"<img[^>]*>", body), "no images rendered; the check would be vacuous"
    offenders = images_without_alt(body)
    assert not offenders, f"{len(offenders)} images with an empty alt: {offenders}"


@override_settings(DEBUG=True)
def test_nothing_is_loaded_from_a_third_party_host() -> None:
    """tech.md section 2: no cdn script, font or stylesheet on a public page.

    Only assets the browser fetches count. canonical and hreflang links are
    absolute on purpose, tech.md section 8.
    """
    body = render_sink()
    loaded = [
        *re.findall(r'<script[^>]+src="([^"]+)"', body),
        *re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', body),
        *re.findall(r'<img[^>]+src="([^"]+)"', body),
    ]
    assert loaded, "no assets on the page at all"
    external = [url for url in loaded if url.startswith(("http://", "https://", "//"))]
    assert not external, f"third party assets: {external}"


@override_settings(DEBUG=True)
def test_kontakt_stays_a_first_level_menu_item() -> None:
    """Hiding it in a submenu was the main defect of the old site."""
    body = render_sink()
    menu = re.search(r'<nav aria-label="Główna nawigacja".*?</nav>', body, re.S)
    assert menu, "c-nav did not render"

    # First level items are the direct children of the one list in c-nav. A
    # submenu entry sits inside its own nested <ul> under a button, so an <a>
    # matched straight after an <li> is top level by construction.
    top_level = re.findall(r"<li[^>]*>\s*<a[^>]*>([^<]+)</a>", menu.group())
    assert "Kontakt" in [title.strip() for title in top_level]


@override_settings(DEBUG=True)
def test_robots_keeps_the_sink_out_of_the_index() -> None:
    assert 'content="noindex,nofollow"' in render_sink()


def test_the_sink_is_unavailable_without_debug() -> None:
    with pytest.raises(Http404):
        kitchen_sink(RequestFactory().get("/__kitchen-sink/"))
