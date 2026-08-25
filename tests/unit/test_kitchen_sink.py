"""The kitchen sink is the review surface for the design system, DEV.md S0.7."""

import re

import pytest
from django.http import Http404
from django.test import RequestFactory, override_settings

from apps.core.views import kitchen_sink

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
    images = re.findall(r"<img[^>]*>", render_sink())
    assert images
    without_alt = [img for img in images if not re.search(r'alt="[^"]+"', img)]
    assert not without_alt, f"{len(without_alt)} images with an empty alt"


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
    menu = re.search(r'<ul id="main-menu".*?</ul>\s*</nav>', body, re.S)
    assert menu

    top_level = re.findall(r'<li class="lg:relative">\s*\n?\s*<a[^>]*>([^<]+)</a>', menu.group())
    assert "Kontakt" in [title.strip() for title in top_level]


@override_settings(DEBUG=True)
def test_robots_keeps_the_sink_out_of_the_index() -> None:
    assert 'content="noindex,nofollow"' in render_sink()


def test_the_sink_is_unavailable_without_debug() -> None:
    with pytest.raises(Http404):
        kitchen_sink(RequestFactory().get("/__kitchen-sink/"))
