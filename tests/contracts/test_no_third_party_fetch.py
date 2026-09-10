"""No page fetches anything from a third party, tech.md section 2, OSTRYCHARZ.md O7.

The rule is not "no trackers". It is that a visitor who has not clicked anything
has told nobody outside this server that they are reading. That is what makes
the site work without a cookie gate, and it is one careless `<iframe>` away from
being untrue.

The home page carries a promotional clip. YouTube's own embed pulls google's
javascript and its cookies; its thumbnail on i.ytimg.com is a request to google
before the reader has done anything at all. So the clip is a poster the owner
uploaded plus a link that opens in a new tab, and this module is what keeps it
that way.
"""

import re

import pytest
from django.test import Client

from apps.core.models import PassRate, SiteSettings
from apps.courses.models import Course, PriceItem
from apps.links.models import Faq
from tests.factories import notify_site

pytestmark = pytest.mark.django_db

# Hosts that must never appear in an attribute the browser fetches on its own.
# ytimg is the thumbnail cdn and is the one people reach for by accident.
FORBIDDEN_HOSTS = (
    "youtube.com",
    "youtu.be",
    "ytimg.com",
    "youtube-nocookie.com",
    "google.com",
    "googleapis.com",
    "gstatic.com",
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "facebook.net",
    "fbcdn.net",
)

# Attributes a browser resolves without being asked. href is absent on purpose:
# a link is a thing the reader chooses to follow, which is the whole design.
FETCHED_ATTRIBUTES = ("src", "srcset", "data-src", "poster", "action", "content")

PAGES = ("/", "/kursy/kat-b/", "/cennik/", "/zdawalnosc/", "/do-pobrania/", "/zapisy/", "/o-nas/")


@pytest.fixture
def filled_site(db: None) -> SiteSettings:
    """A site with every optional block switched on, including the clip.

    Takes `db` explicitly. Without it the fixture is free to be set up before
    pytest-django opens the per test transaction, and every row it writes
    survives into the next test — which shows up as a duplicate slug on
    whichever test happens to run second.
    """
    site = notify_site()
    site.youtube_url = "https://www.youtube.com/channel/UCbXki-U-CJjcQ36tZ5GZ4lw"
    site.youtube_video_url = "https://www.youtube.com/watch?v=abeQhB0RfV4"
    site.facebook_url = "https://pl-pl.facebook.com/osrodekostrycharz/"
    site.save()

    from apps.core.models import Page

    Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-b",
        code="B",
        title="Prawo jazdy kat. B",
        price_gross=3700,
        min_age=18,
        is_active=True,
    )
    PriceItem.objects.create(title="Kurs kategorii B", group="Kurs", price_gross=3700)
    PassRate.objects.create(year=2025, students=92, passed_1st=68, passed_2nd=16)
    Faq.objects.create(question="Ile kosztuje kurs?", answer="3700 zł.")
    for slug, title in (("o-nas", "O nas"), ("zapisy", "Zapisy i dokumenty")):
        Page.objects.create(slug=slug, title=title, body="## Tekst", is_published=True)
    return site


def fetched_urls(body: str) -> list[str]:
    """Every value the browser would go and get without a click."""
    attributes = "|".join(FETCHED_ATTRIBUTES)
    return re.findall(rf"(?:{attributes})\s*=\s*[\"']([^\"']+)[\"']", body, re.I)


@pytest.mark.parametrize("url", PAGES)
def test_a_page_fetches_nothing_from_a_third_party(
    client: Client, filled_site: SiteSettings, url: str
) -> None:
    response = client.get(url)
    assert response.status_code == 200, url

    for value in fetched_urls(response.content.decode()):
        for host in FORBIDDEN_HOSTS:
            assert host not in value.lower(), f"{url} fetches {value}"


def test_the_home_page_carries_the_clip_and_still_fetches_nothing(
    client: Client, filled_site: SiteSettings
) -> None:
    """The section has to be there, or this proves nothing at all."""
    body = client.get("/").content.decode()

    assert 'id="wideo"' in body, "the video section did not render; the test is vacuous"
    assert "abeQhB0RfV4" in body, "the clip is not on the page"

    for value in fetched_urls(body):
        assert "youtu" not in value.lower()


def test_the_clip_is_a_link_the_reader_chooses_to_follow(
    client: Client, filled_site: SiteSettings
) -> None:
    """An anchor, never an iframe. And it leaves this tab alone."""
    body = client.get("/").content.decode()

    assert "<iframe" not in body
    anchor = re.search(r'<a[^>]*href="https://www\.youtube\.com/watch\?v=[^"]*"[^>]*>', body)
    assert anchor, "the clip is not an anchor"
    assert 'target="_blank"' in anchor.group(0)
    assert "noopener" in anchor.group(0)


def test_no_page_embeds_a_google_map(client: Client, filled_site: SiteSettings) -> None:
    """tech.md section 2: the map is Leaflet on OpenStreetMap tiles.

    A google map is a script and a cookie, which is what puts a consent gate on
    a page that otherwise does not need one.
    """
    for url in ("/", "/kontakt/"):
        body = client.get(url).content.decode()
        assert "maps.google" not in body, url
        assert "maps.googleapis" not in body, url
