"""Every public page against the SEO contract, tech.md section 8, DEV.md S8.

The per page tests each check their own slice. This one walks the whole site in
one pass, so a page that ships without a description cannot hide behind a suite
that never visits it.
"""

import json
import re
from datetime import timedelta
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.models import Page, SiteSettings
from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.courses.models import Course, CourseIntake, PriceItem
from apps.links.models import Faq, UsefulLink
from scripts.import_legacy import import_courses
from tests.factories import CertificateFactory, GalleryImageFactory, image_bytes
from tests.unit.test_import_legacy import LEGACY

pytestmark = pytest.mark.django_db

# tech.md section 5, every public url a visitor can reach today.
PUBLIC_URLS = [
    "/kursy/",
    "/kursy/kat-b/",
    "/kierowca-zawodowy/",
    "/kierowca-zawodowy/adr/",
    "/badania-psychologiczne/",
    "/wozki-widlowe/",
    "/cennik/",
    "/terminy/",
    "/o-nas/",
    "/galeria/",
    "/certyfikaty/",
    "/przydatne-linki/",
    "/faq/",
    "/kontakt/",
    "/rodo/",
    "/polityka-prywatnosci/",
]


@pytest.fixture
def whole_site() -> None:
    """Enough content that no page falls back to its empty state."""
    site = SiteSettings.get_solo()
    site.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    site.short_name = "OSK Ostrycharz"
    site.street = "ul. Asnyka 7"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.email = "oskostrycharz@poczta.onet.pl"
    site.phone_primary = "691 570 489"
    site.save()

    import_courses(LEGACY)
    for slug, title in (
        ("o-nas", "O nas"),
        ("rodo", "RODO"),
        ("polityka-prywatnosci", "Polityka prywatności"),
    ):
        Page.objects.create(
            slug=slug, title=title, lead=f"{title} ośrodka.", body="## Nagłówek", is_published=True
        )

    course = Course.objects.get(slug="kat-b")
    CourseIntake.objects.create(
        course=course,
        start_date=timezone.localdate() + timedelta(days=7),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.OPEN,
    )
    PriceItem.objects.create(title="Jazdy dodatkowe", price_gross=120, is_active=True)
    GalleryImageFactory.create_batch(2)
    CertificateFactory.create_batch(2)
    UsefulLink.objects.create(
        group=UsefulLink.Group.EXAM,
        title="Info-Car",
        description="Rezerwacja terminu egzaminu.",
        url="https://info-car.pl/",
    )
    Faq.objects.create(question="Ile trwa kurs?", answer="Około trzech miesięcy.")


def body_of(client: Client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == 200, url
    return response.content.decode()


def jsonld(body: str) -> list[dict[str, Any]]:
    return [
        json.loads(found)
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]


# --------------------------------------------------------------------------
# the contract, page by page


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_has_one_h1(client: Client, whole_site: None, url: str) -> None:
    assert len(re.findall(r"<h1[ >]", body_of(client, url))) == 1


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_title_fits_and_names_the_town(client: Client, whole_site: None, url: str) -> None:
    title = re.search(r"<title>(.*?)</title>", body_of(client, url)).group(1)

    assert "Wieluń" in title
    assert 0 < len(title) <= TITLE_LIMIT


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_description_is_filled_and_short(client: Client, whole_site: None, url: str) -> None:
    description = re.search(r'name="description" content="(.*?)"', body_of(client, url)).group(1)

    assert description.strip()
    assert len(description) <= DESCRIPTION_LIMIT


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_points_at_itself(client: Client, whole_site: None, url: str) -> None:
    canonical = re.search(r'rel="canonical" href="(.*?)"', body_of(client, url)).group(1)

    assert canonical.startswith("http")
    assert canonical.endswith(url)
    assert "?" not in canonical


def alternates(body: str) -> dict[str, str]:
    return dict(re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)"', body))


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_offers_every_language(client: Client, whole_site: None, url: str) -> None:
    links = alternates(body_of(client, url))

    assert set(links) == {"pl", "ru", "uk", "x-default"}
    assert links["x-default"] == links["pl"]
    assert "/ru/" in links["ru"]
    assert "/uk/" in links["uk"]


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_every_language_link_answers(client: Client, whole_site: None, url: str) -> None:
    """A hreflang aimed at a 404 is worse than no hreflang at all."""
    for code, href in alternates(body_of(client, url)).items():
        translated = re.sub(r"^https?://[^/]+", "", href)

        assert client.get(translated).status_code == 200, f"{code}: {href}"


@pytest.mark.seo
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_page_carries_the_school_and_its_trail(client: Client, whole_site: None, url: str) -> None:
    types = [block["@type"] for block in jsonld(body_of(client, url))]

    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types


@pytest.mark.a11y
@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_no_image_ships_an_empty_alt(client: Client, whole_site: None, url: str) -> None:
    images = re.findall(r"<img[^>]*>", body_of(client, url))

    assert not [image for image in images if not re.search(r'alt="[^"]+"', image)]


# --------------------------------------------------------------------------
# coverage of the sweep itself


def advertised_paths(client: Client) -> set[str]:
    body = body_of(client, "/sitemap.xml")
    return {re.sub(r"^https?://[^/]+", "", url) for url in re.findall(r"<loc>(.*?)</loc>", body)}


def test_the_sweep_visits_everything_the_sitemap_advertises(
    client: Client, whole_site: None
) -> None:
    """A page in the sitemap and outside this list would never be checked."""
    advertised = advertised_paths(client)

    assert (
        advertised
        - set(PUBLIC_URLS)
        - {f"/kursy/{course.slug}/" for course in Course.objects.filter(kind=Course.Kind.LICENSE)}
        - {
            f"/kierowca-zawodowy/{course.slug}/"
            for course in Course.objects.filter(kind=Course.Kind.PROFESSIONAL)
        }
        == set()
    )


def test_every_public_page_is_advertised(client: Client, whole_site: None) -> None:
    """The other direction: a page outside the sitemap is one nobody crawls."""
    assert set(PUBLIC_URLS) - advertised_paths(client) == set()


# --------------------------------------------------------------------------
# og images, DEV.md S8


def test_a_course_shares_its_own_picture(client: Client, whole_site: None) -> None:
    course = Course.objects.get(slug="kat-b")
    course.hero_image = image_bytes()
    course.hero_alt = "Kurs kategorii B"
    course.save()

    found = re.search(r'property="og:image" content="([^"]+)"', body_of(client, "/kursy/kat-b/"))

    assert found
    assert found.group(1).startswith("http")
    assert course.hero_image.url in found.group(1)


def test_a_course_without_a_picture_claims_none(client: Client, whole_site: None) -> None:
    """An og:image tag pointing at nothing is worse than no tag."""
    assert 'property="og:image"' not in body_of(client, "/kursy/kat-a/")


@pytest.mark.parametrize("url", PUBLIC_URLS)
def test_every_page_says_what_it_is_when_shared(client: Client, whole_site: None, url: str) -> None:
    body = body_of(client, url)

    assert 'property="og:title"' in body
    assert 'property="og:url"' in body
    assert 'property="og:description"' in body
