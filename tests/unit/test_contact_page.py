"""The contact page, DEV.md S4 acceptance criteria."""

import json
import re
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.models import OpeningHours, SiteSettings
from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT

pytestmark = pytest.mark.django_db

PHONES = ("691 570 489", "605 065 795", "667 615 184")


@pytest.fixture
def site() -> SiteSettings:
    """The office as the seed leaves it, tech.md section 1."""
    settings = SiteSettings.get_solo()
    settings.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    settings.short_name = "OSK Ostrycharz"
    settings.street = "ul. Asnyka 7"
    settings.postal_code = "98-300"
    settings.city = "Wieluń"
    settings.nip = "8321916014"
    settings.email = "oskostrycharz@poczta.onet.pl"
    settings.phone_primary, settings.phone_secondary, settings.phone_tertiary = PHONES
    settings.map_lat = Decimal("51.220600")
    settings.map_lng = Decimal("18.569700")
    settings.bank_account = "PL61109010140000071219812874"
    settings.bank_account_public = False
    settings.save()
    return settings


def page(client: Client) -> str:
    response = client.get(reverse("core:contact"))
    assert response.status_code == 200
    return response.content.decode()


def block(body: str, testid: str) -> str:
    """The markup of one data-testid element, so the footer cannot answer for it.

    Cut at whatever comes first: the next tagged element or the end of the
    section. The sticky call bar sits outside any section, so neither is
    guaranteed and the tail of the document is the fallback.
    """
    rest = body[body.index(f'data-testid="{testid}"') :]
    ends = [
        found for found in (rest.find('data-testid="', 1), rest.find("</section>")) if found > 0
    ]
    return rest[: min(ends, default=len(rest))]


# --------------------------------------------------------------------------
# route and seo


def test_route_matches_the_url_map(client: Client, site: SiteSettings) -> None:
    """tech.md section 5, and the nav route name in section 7."""
    assert reverse("core:contact") == "/kontakt/"
    assert client.get("/kontakt/").status_code == 200


def test_the_nav_can_reach_the_page(site: SiteSettings) -> None:
    """Kontakt is a first level nav item, and it has to resolve to a real url."""
    from apps.core.navigation import NAV

    kontakt = next(item for item in NAV if item.title == "Kontakt")
    assert kontakt.url() == "/kontakt/"


@pytest.mark.seo
def test_page_meets_the_seo_contract(client: Client, site: SiteSettings) -> None:
    body = page(client)

    assert len(re.findall(r"<h1[ >]", body)) == 1

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert "Wieluń" in title
    assert len(title) <= TITLE_LIMIT

    description = re.search(r'name="description" content="(.*?)"', body).group(1)
    assert description.strip()
    assert len(description) <= DESCRIPTION_LIMIT

    canonical = re.search(r'rel="canonical" href="(.*?)"', body).group(1)
    assert canonical.endswith("/kontakt/")
    assert "?" not in canonical

    types = [
        json.loads(found)["@type"]
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]
    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types


@pytest.mark.seo
def test_page_offers_every_language(client: Client, site: SiteSettings) -> None:
    links = dict(
        re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)"', page(client))
    )

    assert set(links) == {"pl", "ru", "uk", "x-default"}
    assert links["x-default"] == links["pl"]


@pytest.mark.a11y
def test_no_image_ships_an_empty_alt(client: Client, site: SiteSettings) -> None:
    images = re.findall(r"<img[^>]*>", page(client))
    assert not [image for image in images if not re.search(r'alt="[^"]+"', image)]


# --------------------------------------------------------------------------
# calling and writing


def test_every_phone_is_tappable(client: Client, site: SiteSettings) -> None:
    """All three numbers, on the page itself and not only in the footer."""
    details = block(page(client), "details")

    for phone in PHONES:
        assert f'href="tel:{phone.replace(" ", "")}"' in details
        # The number follows an icon now, so it is no longer tight against the
        # tag before it.
        assert re.search(rf">\s*{re.escape(phone)}\s*<", details), phone


def test_the_email_is_a_mailto(client: Client, site: SiteSettings) -> None:
    assert f'href="mailto:{site.email}"' in block(page(client), "details")


def test_the_page_carries_the_registration_details(client: Client, site: SiteSettings) -> None:
    details = block(page(client), "details")

    assert site.legal_name in details
    assert site.street in details
    assert site.postal_code in details
    assert site.nip in details


def test_the_bank_account_stays_private_by_default(client: Client, site: SiteSettings) -> None:
    """tech.md section 4.1: the number shows only when the owner allows it."""
    assert site.bank_account not in page(client)


def test_the_bank_account_shows_once_it_is_public(client: Client, site: SiteSettings) -> None:
    SiteSettings.objects.update(bank_account_public=True)

    assert site.bank_account in block(page(client), "bank-account")


def test_the_call_bar_carries_the_first_number(client: Client, site: SiteSettings) -> None:
    """The sticky call button is the point of the page on a phone."""
    assert 'href="tel:438432911"' in block(page(client), "call-bar")


# --------------------------------------------------------------------------
# opening hours, DEV.md S4: right on the boundaries


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Pin "now", so the boundary cases do not depend on when the suite runs."""

    def freeze(moment: datetime) -> datetime:
        aware = timezone.make_aware(moment)
        monkeypatch.setattr(timezone, "localtime", lambda value=None: aware)
        return aware

    return freeze


def office_hours(weekday: int, opens: time | None, closes: time | None) -> None:
    OpeningHours.objects.create(
        department=OpeningHours.DEPT.OFFICE, weekday=weekday, opens=opens, closes=closes
    )


# A wednesday, so adding days stays inside the same week.
WEDNESDAY = datetime(2026, 9, 16, 12, 0)


def badges(body: str) -> list[str]:
    """The open/closed word from each department's indicator.

    Whitespace tolerant on purpose: the badge carries an icon as well as the
    word, F8, so the text no longer sits tight against the opening tag. What
    matters is which word the badge says, not what precedes it.
    """
    return re.findall(r">\s*(Otwarte teraz|Zamknięte)\s*<", body)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (WEDNESDAY.replace(hour=9, minute=0), "Otwarte teraz"),
        (WEDNESDAY.replace(hour=12, minute=30), "Otwarte teraz"),
        (WEDNESDAY.replace(hour=8, minute=59), "Zamknięte"),
        (WEDNESDAY.replace(hour=17, minute=0), "Zamknięte"),
        (WEDNESDAY.replace(hour=17, minute=1), "Zamknięte"),
    ],
)
def test_the_indicator_is_right_on_the_boundaries(
    client: Client, site: SiteSettings, clock: Any, moment: datetime, expected: str
) -> None:
    clock(moment)
    office_hours(moment.weekday(), time(9, 0), time(17, 0))

    # The psychology lab has no rows at all, so it always reads closed and the
    # office badge is the only one that can move.
    assert badges(page(client)) == [expected, "Zamknięte"]


def test_a_day_off_reads_closed(client: Client, site: SiteSettings, clock: Any) -> None:
    """A weekday without hours is a day off, tech.md section 4.1."""
    sunday = WEDNESDAY + timedelta(days=4)
    clock(sunday)
    office_hours(sunday.weekday(), None, None)

    assert badges(page(client)) == ["Zamknięte", "Zamknięte"]


def test_both_departments_get_their_own_table(client: Client, site: SiteSettings) -> None:
    office_hours(0, time(9, 0), time(17, 0))
    OpeningHours.objects.create(
        department=OpeningHours.DEPT.PSYCHOLOGY, weekday=1, opens=time(8, 0), closes=time(16, 0)
    )
    body = page(client)

    assert "09:00" in block(body, "hours-office")
    assert "08:00" in block(body, "hours-psychology")
    assert "Biuro" in body
    assert "Pracownia psychologiczna" in body


# --------------------------------------------------------------------------
# getting there


def test_the_map_gets_the_coordinates_as_a_machine_reads_them(
    client: Client, site: SiteSettings
) -> None:
    """The polish locale writes 51,2206 and leaflet reads that as 51."""
    node = re.search(r"<div data-map[^>]*>", page(client)).group(0)

    assert 'data-lat="51.220600"' in node
    assert 'data-lng="18.569700"' in node


def test_the_route_buttons_point_at_the_office(client: Client, site: SiteSettings) -> None:
    body = page(client)

    osm = re.search(r'href="(https://www\.openstreetmap\.org/directions[^"]*)"', body).group(1)
    assert "51.220600%2C18.569700" in osm

    geo = re.search(r'href="(geo:[^"]*)"', body).group(1)
    assert geo.startswith("geo:51.220600,18.569700")
    assert "Wyznacz trasę" in body


def test_missing_coordinates_give_an_address_instead_of_a_broken_map(
    client: Client, site: SiteSettings
) -> None:
    SiteSettings.objects.update(map_lat=None, map_lng=None)
    body = page(client)

    assert "data-map" not in body
    assert "geo:" not in body
    assert site.street in body


def test_nothing_on_the_page_comes_from_a_third_party(client: Client, site: SiteSettings) -> None:
    """tech.md section 2: no external script, no external font, no analytics host."""
    body = page(client)

    sources = re.findall(r'<(?:script|link|img)[^>]*(?:src|href)="([^"]+)"', body)
    assert sources
    # Everything is either relative or on our own host. The openstreetmap tiles
    # are fetched by leaflet at runtime, which the browser test watches.
    assert {urlsplit(url).netloc for url in sources} - {""} <= {"testserver"}

    # Leaflet is still ours, it just arrives through the map's data attributes
    # now rather than a tag in the head: it is fetched when the map comes into
    # view, which is what keeps 157 KB off the first screen, A.11.
    leaflet = re.findall(r'data-leaflet-(?:js|css)="([^"]+)"', body)
    assert len(leaflet) == 2, "the map does not carry its own leaflet paths"
    assert {urlsplit(url).netloc for url in leaflet} == {""}
    assert any("leaflet.js" in url for url in leaflet)


# --------------------------------------------------------------------------
# FRONTEND.md F8


def indicator(body: str, department: str) -> str:
    """The open/closed badge of one department, markup and all."""
    region = block(body, f"hours-{department}")
    found = re.search(r"<span[^>]*label[^>]*>.*?</span>", region, re.S)
    assert found, f"the {department} indicator did not render"
    return found.group()


def test_the_two_states_differ_by_more_than_colour(
    client: Client, site: SiteSettings, clock: Any
) -> None:
    """F8, and the commonest sight difference there is.

    Green against grey is invisible to a good few people, so open and closed
    have to be told apart by the word, by the border and by the mark as well.
    """
    clock(WEDNESDAY.replace(hour=12, minute=0))
    office_hours(WEDNESDAY.weekday(), time(9, 0), time(17, 0))

    body = page(client)
    open_now = indicator(body, "office")
    closed = indicator(body, "psychology")

    assert "Otwarte teraz" in open_now
    assert "Zamknięte" in closed

    assert "border-state-ok" in open_now
    assert "border-state-ok" not in closed
    assert "border-line-soft" in closed

    assert "#i-check" in open_now
    assert "#i-clock" in closed


def test_a_phone_number_never_breaks_mid_number(client: Client, site: SiteSettings) -> None:
    """F8: at 320px a wrapped number is a number nobody can read back."""
    details = block(page(client), "details")
    links = re.findall(r'<a[^>]*href="tel:[^"]*"[^>]*>', details)

    assert len(links) == len(PHONES)
    for link in links:
        assert "whitespace-nowrap" in link, link


def test_the_map_is_taller_where_there_is_room(client: Client, site: SiteSettings) -> None:
    """F8: 320px on a phone, 420px on a desktop."""
    node = re.search(r"<div[^>]*data-map[^>]*>", page(client))
    assert node
    assert "h-80" in node.group(), "the mobile height is not the 320px step"
    assert "lg:h-[420px]" in node.group()


def test_the_map_reaches_no_google(client: Client, site: SiteSettings) -> None:
    """tech.md section 2: openstreetmap tiles and nothing else."""
    body = page(client)
    assert "googleapis" not in body
    assert "google.com/maps" not in body
    assert "maps.google" not in body
