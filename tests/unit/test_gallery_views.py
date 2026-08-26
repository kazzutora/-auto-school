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


# --------------------------------------------------------------------------
# section filter, DEV.md S6.1


def get_with(client: Client, **params: str) -> str:
    response = client.get(reverse("gallery:index"), params)
    assert response.status_code == 200
    return response.content.decode()


def headings(body: str) -> list[str]:
    return re.findall(r"<h2[^>]*>(.*?)</h2>", body)


def chips(body: str) -> list[tuple[str, str, str]]:
    found = re.search(r'data-testid="filters".*?</nav>', body, re.S)
    return re.findall(r'<a href="([^"]*)"[^>]*>\s*([^<]+?)\s*<span[^>]*>(\d+)', found.group(0))


def test_without_a_filter_every_section_is_shown(client: Client, content: None) -> None:
    assert headings(get_with(client)) == ["Ośrodek", "Pojazdy", "Plac manewrowy", "Zajęcia"]


def test_a_chosen_section_is_the_only_one_shown(client: Client, content: None) -> None:
    body = get_with(client, section="vehicles")

    assert headings(body) == ["Pojazdy"]
    assert body.count("<picture") == 2


def test_an_unknown_section_falls_back_to_everything(client: Client, content: None) -> None:
    """A stale link out of a search engine still shows the gallery."""
    assert len(headings(get_with(client, section="nie-ma-takiej"))) == 4


def test_the_chips_carry_the_url_and_the_count(client: Client, content: None) -> None:
    GalleryImageFactory(section=GalleryImage.Section.YARD)

    assert chips(get_with(client)) == [
        ("/galeria/", "Wszystkie", "9"),
        ("/galeria/?section=school", "Ośrodek", "2"),
        ("/galeria/?section=vehicles", "Pojazdy", "2"),
        ("/galeria/?section=yard", "Plac manewrowy", "3"),
        ("/galeria/?section=events", "Zajęcia", "2"),
    ]


def test_a_chip_never_leads_to_an_empty_page(client: Client) -> None:
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL)
    GalleryImageFactory(section=GalleryImage.Section.VEHICLES)
    GalleryImageFactory(section=GalleryImage.Section.YARD, is_published=False)

    labels = [label for _url, label, _total in chips(get_with(client))]

    assert labels == ["Wszystkie", "Ośrodek", "Pojazdy"]


def test_the_chosen_chip_is_marked_for_a_screen_reader(client: Client, content: None) -> None:
    found = re.search(
        r'data-testid="filters".*?</nav>', get_with(client, section="yard"), re.S
    ).group(0)
    active = re.findall(r'<a href="([^"]*)"[^>]*aria-current="page"', found)

    assert active == ["/galeria/?section=yard"]


def test_a_single_section_hides_the_filter(client: Client) -> None:
    """One chip and nothing to choose between is noise, not a filter."""
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL)

    assert 'data-testid="filters"' not in get_with(client)


def test_an_empty_section_offers_a_way_out(client: Client) -> None:
    """The section is filtered out of the chips, but a bookmark can still hit it."""
    GalleryImageFactory(section=GalleryImage.Section.SCHOOL)
    body = get_with(client, section="events")

    assert "Nic w tej sekcji" in body
    assert "Zobacz całą galerię" in body
    assert "<picture" not in body


def test_the_section_headings_are_polish(client: Client, content: None) -> None:
    """The choice labels on the model are english until the catalogs exist."""
    body = get_with(client)

    for english in ("School", "Vehicles", "Yard", "Events"):
        assert f">{english}<" not in body


# --------------------------------------------------------------------------
# page weight, DEV.md S6.1: 400 KB above the fold


def test_the_lightbox_does_not_preload_the_originals(client: Client, content: None) -> None:
    """A hidden image with no loading attribute is downloaded anyway.

    Eight photos on the reference data came to 16 MB before this. The browser
    side of it is measured in tests/e2e/test_gallery_e2e.py.
    """
    body = get_with(client)
    originals = re.findall(r"<img[^>]*/media/gallery/[^>]*>", body)

    assert originals
    assert not [image for image in originals if 'loading="lazy"' not in image]
