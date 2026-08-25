"""Gallery pages, the reference slice. tech.md sections 5, 8 and 9."""

import json
import re

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.gallery.models import GalleryImage
from tests.factories import CertificateFactory, GalleryImageFactory

pytestmark = pytest.mark.django_db

PAGES = ("gallery:index", "gallery:certificates")


@pytest.fixture
def content() -> None:
    for section in GalleryImage.Section:
        GalleryImageFactory.create_batch(2, section=section)
    CertificateFactory.create_batch(3)


def get(client: Client, route: str) -> str:
    response = client.get(reverse(route))
    assert response.status_code == 200
    return response.content.decode()


def test_routes_match_the_url_map(client: Client, content: None) -> None:
    """tech.md section 5 and the nav route name in section 7."""
    assert reverse("gallery:index") == "/galeria/"
    assert reverse("gallery:certificates") == "/certyfikaty/"
    assert client.get("/galeria/").status_code == 200
    assert client.get("/certyfikaty/").status_code == 200


@pytest.mark.seo
@pytest.mark.parametrize("route", PAGES)
def test_page_meets_the_seo_contract(client: Client, content: None, route: str) -> None:
    body = get(client, route)

    assert len(re.findall(r"<h1[ >]", body)) == 1

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert "Wieluń" in title
    assert len(title) <= TITLE_LIMIT

    description = re.search(r'name="description" content="(.*?)"', body).group(1)
    assert description.strip()
    assert len(description) <= DESCRIPTION_LIMIT

    canonical = re.search(r'rel="canonical" href="(.*?)"', body).group(1)
    assert canonical.startswith("http")
    assert "?" not in canonical

    types = [
        json.loads(block)["@type"]
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]
    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types


@pytest.mark.seo
@pytest.mark.parametrize("route", PAGES)
def test_page_offers_every_language(client: Client, content: None, route: str) -> None:
    body = get(client, route)
    links = dict(re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)"', body))

    assert set(links) == {"pl", "ru", "uk", "x-default"}
    assert links["x-default"] == links["pl"]
    assert "/ru/" in links["ru"]
    assert "/uk/" in links["uk"]


@pytest.mark.a11y
@pytest.mark.parametrize("route", PAGES)
def test_no_image_ships_an_empty_alt(client: Client, content: None, route: str) -> None:
    images = re.findall(r"<img[^>]*>", get(client, route))
    assert images
    assert not [img for img in images if not re.search(r'alt="[^"]+"', img)]


@pytest.mark.parametrize("route", PAGES)
def test_images_are_served_as_webp_and_lazily(client: Client, content: None, route: str) -> None:
    """tech.md section 6 renditions reach the page through c-picture."""
    body = get(client, route)

    sources = re.findall(r'<source type="image/webp" srcset="([^"]+)"', body)
    assert sources
    for srcset in sources:
        # Split the srcset rather than scanning it: django gives a colliding
        # upload a random suffix, and one shaped like "_HDPnQ3w" would look like
        # a width descriptor to a regex.
        widths = [entry.strip().rsplit(" ", 1)[-1] for entry in srcset.split(",")]
        assert widths == ["480w", "960w", "1600w"]
    assert 'loading="lazy"' in body


def test_unpublished_rows_stay_off_the_page(client: Client) -> None:
    GalleryImageFactory(alt="Widoczne", is_published=True)
    GalleryImageFactory(alt="Ukryte", is_published=False)
    CertificateFactory(title="Schowany", is_published=False)

    gallery = get(client, "gallery:index")
    assert "Widoczne" in gallery
    assert "Ukryte" not in gallery
    assert "Schowany" not in get(client, "gallery:certificates")


def test_empty_gallery_says_so_instead_of_breaking(client: Client) -> None:
    body = get(client, "gallery:index")
    assert "Galeria w przygotowaniu" in body
    assert not re.findall(r"<c-[a-z.-]+", body)


def test_lightbox_partial_returns_one_image(client: Client) -> None:
    image = GalleryImageFactory(alt="Plac manewrowy")

    response = client.get(reverse("gallery:lightbox", args=[image.pk]))

    assert response.status_code == 200
    body = response.content.decode()
    assert "Plac manewrowy" in body
    # A partial, never a whole document.
    assert "<html" not in body
    assert body.count("<figure") == 1


def test_lightbox_hides_an_unpublished_image(client: Client) -> None:
    image = GalleryImageFactory(is_published=False)
    assert client.get(reverse("gallery:lightbox", args=[image.pk])).status_code == 404
