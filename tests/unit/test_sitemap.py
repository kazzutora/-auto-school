"""sitemap.xml and robots.txt, tech.md sections 5 and 8, DEV.md S8."""

import re
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localtime

from apps.core.models import Page
from apps.core.sitemaps import CONDITIONAL_ROUTES, STATIC_ROUTES
from apps.courses.models import Course

pytestmark = pytest.mark.django_db


@pytest.fixture
def offer() -> Course:
    Page.objects.create(slug="o-nas", title="O nas", body="## Kim", is_published=True)
    Page.objects.create(slug="rodo", title="RODO", body="## Klauzula", is_published=True)
    return Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )


def sitemap(client: Client) -> str:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["Content-Type"]
    return response.content.decode()


def locations(body: str) -> list[str]:
    return re.findall(r"<loc>(.*?)</loc>", body)


def paths(body: str) -> list[str]:
    return [re.sub(r"^https?://[^/]+", "", url) for url in locations(body)]


# --------------------------------------------------------------------------
# what is in the file


# Routes that only join the file once they have something in them.
UNCONDITIONAL = [route for route in STATIC_ROUTES if route not in CONDITIONAL_ROUTES]


def test_the_static_routes_are_listed(client: Client, offer: Course) -> None:
    """Every route the file names by hand and does not gate, resolved and present."""
    listed = paths(sitemap(client))

    for route in UNCONDITIONAL:
        assert reverse(route) in listed, route
    for path in ("/", "/kursy/", "/cennik/", "/kontakt/"):
        assert path in listed, path


def test_a_page_with_nothing_in_it_is_not_advertised(client: Client, offer: Course) -> None:
    """It answers 200 and shows its empty state, which is right for a visitor.

    It is the wrong thing to hand a crawler: a sitemap of placeholders is how a
    small site teaches Google that most of it is thin. This school has no
    photographs, no certificates and no published intake calendar.
    """
    listed = paths(sitemap(client))

    for path in ("/galeria/", "/certyfikaty/", "/terminy/"):
        assert path not in listed, path
        assert client.get(path).status_code == 200, f"{path} still has to answer"


def test_a_route_rejoins_the_file_the_moment_it_has_content(client: Client, offer: Course) -> None:
    """Evaluated per request, so nothing has to be remembered or rerun."""
    from apps.core.models import PassRate

    assert "/zdawalnosc/" not in paths(sitemap(client))

    PassRate.objects.create(year=2025, students=92, passed_1st=68)

    assert "/zdawalnosc/" in paths(sitemap(client))


def test_a_course_brings_its_own_url_and_date(client: Client, offer: Course) -> None:
    """The date is the local one, which is not always the UTC one.

    django.contrib.sitemaps renders lastmod through localtime, and this
    compared it against updated_at.date() in UTC. The two differ for the two
    hours each night between 22:00 UTC and midnight in Warsaw, so the test was
    red between 00:00 and 02:00 local and green the rest of the day. Found at
    00:57 on a full suite run; nothing about the sitemap changed.
    """
    body = sitemap(client)

    assert "/kursy/kat-b/" in paths(body)
    assert localtime(offer.updated_at).date().isoformat() in body


def test_a_flat_page_is_listed_with_its_date(client: Client, offer: Course) -> None:
    listed = paths(sitemap(client))

    assert "/o-nas/" in listed
    assert "/rodo/" in listed


def test_nothing_is_listed_twice(client: Client, offer: Course) -> None:
    """A psychotest course has a url of its own and a static route to match."""
    Course.objects.create(
        kind=Course.Kind.PSYCHOTEST, slug="badania-psychologiczne", title="Badania"
    )
    Course.objects.create(kind=Course.Kind.OPERATOR, slug="wozki-widlowe", title="Wózki")

    listed = paths(sitemap(client))

    assert sorted(listed) == sorted(set(listed))
    assert "/badania-psychologiczne/" in listed
    assert "/wozki-widlowe/" in listed


def test_the_file_advertises_the_host_that_asked(
    client: Client, offer: Course, settings: Any
) -> None:
    """Not the django.contrib.sites row, which says example.com out of the box.

    A sitemap naming another domain sends every crawler that reads it away from
    the site it was meant to describe.
    """
    settings.ALLOWED_HOSTS = ["oskostrycharz.pl"]

    body = client.get("/sitemap.xml", headers={"host": "oskostrycharz.pl"}).content.decode()

    assert locations(body)
    for url in locations(body):
        assert url.startswith("http://oskostrycharz.pl/"), url


def test_the_file_is_not_itself_indexed(client: Client, offer: Course) -> None:
    response = client.get("/sitemap.xml")

    assert "noindex" in response.headers["X-Robots-Tag"]


def test_every_listed_url_answers(client: Client, offer: Course) -> None:
    """A sitemap is a promise: everything in it exists."""
    for path in paths(sitemap(client)):
        assert client.get(path).status_code == 200, path


# --------------------------------------------------------------------------
# what is kept out


def test_an_inactive_course_is_not_advertised(client: Client, offer: Course) -> None:
    Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-a", title="Kategoria A", is_active=False
    )

    assert "/kursy/kat-a/" not in paths(sitemap(client))


def test_an_unpublished_page_is_not_advertised(client: Client, offer: Course) -> None:
    Page.objects.filter(slug="rodo").update(is_published=False)

    assert "/rodo/" not in paths(sitemap(client))


def test_a_page_without_a_url_does_not_break_the_file(client: Client, offer: Course) -> None:
    """Page also holds blocks that other pages include, like platnosci."""
    Page.objects.create(slug="platnosci", title="Płatności", body="## Raty", is_published=True)

    listed = paths(sitemap(client))

    assert "/platnosci/" not in listed
    assert "/o-nas/" in listed


def test_the_admin_is_not_in_the_sitemap(client: Client, offer: Course) -> None:
    assert not [path for path in paths(sitemap(client)) if path.startswith("/admin")]


# --------------------------------------------------------------------------
# robots.txt


def robots(client: Client) -> str:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/plain")
    return response.content.decode()


def test_robots_keeps_crawlers_out_of_the_admin(client: Client) -> None:
    body = robots(client)

    assert "Disallow: /admin/" in body
    assert "Disallow: /__kitchen-sink/" in body
    assert "Allow: /" in body


def test_robots_points_at_the_sitemap(client: Client) -> None:
    """An absolute url: a crawler will not guess the host from a relative one."""
    found = re.search(r"^Sitemap: (\S+)$", robots(client), re.M)

    assert found
    assert found.group(1) == "http://testserver/sitemap.xml"


def test_the_crawler_files_carry_no_language_prefix(client: Client) -> None:
    """One sitemap for the site, tech.md section 5."""
    assert client.get("/ru/robots.txt").status_code == 404
    assert client.get("/ru/sitemap.xml").status_code == 404
