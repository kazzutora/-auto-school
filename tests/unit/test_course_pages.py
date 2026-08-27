"""Course pages, DEV.md S1.2 acceptance criteria."""

import json
import re
from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.courses.models import Course, CourseIntake
from apps.people.models import Vehicle
from scripts.import_legacy import import_courses
from tests.unit.test_import_legacy import LEGACY

pytestmark = pytest.mark.django_db


@pytest.fixture
def offer() -> list[Course]:
    import_courses(LEGACY)
    return list(Course.objects.all())


def make_course(**overrides: object) -> Course:
    values: dict = {
        "kind": Course.Kind.LICENSE,
        "slug": "kat-b",
        "code": "B",
        "title": "Kategoria B",
        "min_age": 18,
        "is_active": True,
    }
    values.update(overrides)
    return Course.objects.create(**values)


def body_of(client: Client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == 200, url
    return response.content.decode()


# --------------------------------------------------------------------------
# routes


def test_the_routes_match_the_url_map() -> None:
    """tech.md section 5."""
    assert reverse("courses:list") == "/kursy/"
    assert reverse("courses:pro_hub") == "/kierowca-zawodowy/"
    assert reverse("courses:detail", kwargs={"slug": "kat-b"}) == "/kursy/kat-b/"
    assert reverse("courses:pro_detail", kwargs={"slug": "adr"}) == "/kierowca-zawodowy/adr/"
    assert reverse("courses:psychotests") == "/badania-psychologiczne/"
    assert reverse("courses:forklifts") == "/wozki-widlowe/"


def test_every_course_answers_200(client: Client, offer: list[Course]) -> None:
    assert len(offer) == 15
    for course in offer:
        assert client.get(course.get_absolute_url()).status_code == 200, course.slug


def test_every_course_page_has_exactly_one_h1(client: Client, offer: list[Course]) -> None:
    for course in offer:
        body = body_of(client, course.get_absolute_url())
        assert len(re.findall(r"<h1[ >]", body)) == 1, course.slug


@pytest.mark.parametrize(
    ("url", "title"),
    [("/kursy/", "Kursy prawa jazdy"), ("/kierowca-zawodowy/", "Kierowca zawodowy")],
)
def test_a_listing_prints_its_title_once(
    client: Client, offer: list[Course], url: str, title: str
) -> None:
    """A cotton component reads the page context.

    Handing the view's title over under the key `heading` made <c-section> take
    it for its own slot and print it again, as an h2 right above the h1.
    """
    headings = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", body_of(client, url))

    assert headings.count(title) == 1


def test_an_inactive_course_is_gone(client: Client) -> None:
    course = make_course(is_active=False)
    assert client.get("/kursy/kat-b/").status_code == 404
    assert course.get_absolute_url() == "/kursy/kat-b/"


def test_a_course_is_not_reachable_under_the_wrong_section(client: Client) -> None:
    """One page on two urls is duplicate content."""
    make_course(kind=Course.Kind.PROFESSIONAL, slug="adr", code="ADR", title="ADR", min_age=None)

    assert client.get("/kierowca-zawodowy/adr/").status_code == 200
    assert client.get("/kursy/adr/").status_code == 404


def test_the_listing_only_shows_its_own_kind(client: Client, offer: list[Course]) -> None:
    licences = body_of(client, "/kursy/")
    professional = body_of(client, "/kierowca-zawodowy/")

    assert "/kursy/kat-b/" in licences
    assert "/kierowca-zawodowy/adr/" not in licences
    assert "/kierowca-zawodowy/adr/" in professional


def test_an_inactive_course_leaves_the_listing(client: Client) -> None:
    make_course()
    make_course(slug="kat-c", code="C", title="Kategoria C", is_active=False)

    body = body_of(client, "/kursy/")
    assert "/kursy/kat-b/" in body
    assert "/kursy/kat-c/" not in body


# --------------------------------------------------------------------------
# price


def test_a_course_without_a_price_asks_for_one(client: Client) -> None:
    make_course(price_gross=None)

    body = body_of(client, "/kursy/kat-b/")

    assert "Zapytaj o cenę" in body
    assert not re.search(r">\s*0[,.]00", body), "a missing price must never read as zero"


def test_a_course_with_a_price_shows_it(client: Client) -> None:
    make_course(price_gross=Decimal("3200"), price_note="cena od")

    body = body_of(client, "/kursy/kat-b/")

    assert "3" in body and "200" in body
    assert "cena od" in body
    assert "Zapytaj o cenę" not in body


def test_the_listing_offers_the_price_question_too(client: Client) -> None:
    make_course(price_gross=None)
    assert "Zapytaj o cenę" in body_of(client, "/kursy/")


# --------------------------------------------------------------------------
# content


def test_markdown_reaches_the_page_as_html(client: Client, offer: list[Course]) -> None:
    body = body_of(client, "/kursy/kat-b/")

    assert "<li>" in body
    assert "3,5 t" in body  # from the entitlements list
    assert "- pojazdem" not in body, "raw markdown leaked through"


def test_only_the_next_three_intakes_are_listed(client: Client) -> None:
    course = make_course()
    today = timezone.localdate()
    for offset in (5, 10, 15, 20, 25):
        CourseIntake.objects.create(
            course=course,
            start_date=today + timedelta(days=offset),
            mode=CourseIntake.Mode.STATIONARY,
            status=CourseIntake.Status.OPEN,
        )

    body = body_of(client, "/kursy/kat-b/")
    assert body.count("Zapisy otwarte") == 3


def test_past_and_closed_intakes_stay_off_the_page(client: Client) -> None:
    course = make_course()
    today = timezone.localdate()
    CourseIntake.objects.create(
        course=course,
        start_date=today - timedelta(days=3),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.OPEN,
    )
    CourseIntake.objects.create(
        course=course,
        start_date=today + timedelta(days=3),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.CLOSED,
    )

    body = body_of(client, "/kursy/kat-b/")
    assert "Najbliższe terminy" not in body


def test_vehicles_of_the_course_are_shown(client: Client) -> None:
    course = make_course()
    Vehicle.objects.create(course=course, make="Skoda", model="Fabia", year=2021)
    Vehicle.objects.create(course=course, make="Ukryty", model="Pojazd", is_active=False)

    body = body_of(client, "/kursy/kat-b/")

    assert "Skoda" in body
    assert "Ukryty" not in body


def test_the_call_button_is_pinned_to_the_bottom(client: Client) -> None:
    """tech.md section 7: on a phone the call must not need a scroll."""
    from apps.core.models import SiteSettings

    site = SiteSettings.get_solo()
    site.phone_primary = "605 065 795"
    site.save()
    make_course()
    body = body_of(client, "/kursy/kat-b/")

    assert "fixed inset-x-0 bottom-0" in body
    assert "tel:" in body


# --------------------------------------------------------------------------
# seo


@pytest.mark.seo
def test_the_title_follows_the_contract(client: Client) -> None:
    make_course()
    body = body_of(client, "/kursy/kat-b/")

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert title == "Prawo jazdy kat. B — OSK Nawrocki Wieluń"
    assert len(title) <= TITLE_LIMIT


@pytest.mark.seo
def test_every_page_meets_the_seo_contract(client: Client, offer: list[Course]) -> None:
    urls = ["/kursy/", "/kierowca-zawodowy/"] + [c.get_absolute_url() for c in offer]

    for url in urls:
        body = body_of(client, url)

        title = re.search(r"<title>(.*?)</title>", body).group(1)
        assert "Wieluń" in title, url
        assert len(title) <= TITLE_LIMIT, url

        description = re.search(r'name="description" content="(.*?)"', body).group(1)
        assert description.strip(), url
        assert len(description) <= DESCRIPTION_LIMIT, url

        canonical = re.search(r'rel="canonical" href="(.*?)"', body).group(1)
        assert canonical.startswith("http") and "?" not in canonical, url

        for code in ("pl", "ru", "uk", "x-default"):
            assert f'hreflang="{code}"' in body, url


@pytest.mark.seo
def test_a_detail_page_carries_course_json_ld(client: Client, offer: list[Course]) -> None:
    body = body_of(client, "/kursy/kat-b/")
    blocks = {
        json.loads(raw)["@type"]: json.loads(raw)
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    }

    assert set(blocks) == {"DrivingSchool", "BreadcrumbList", "Course"}
    assert blocks["Course"]["name"] == Course.objects.get(slug="kat-b").title
    assert blocks["Course"]["provider"]["@type"] == "DrivingSchool"


@pytest.mark.a11y
def test_no_image_ships_an_empty_alt(client: Client, offer: list[Course]) -> None:
    for url in ("/kursy/", "/kierowca-zawodowy/", "/kursy/kat-b/"):
        images = re.findall(r"<img[^>]*>", body_of(client, url))
        assert not [img for img in images if not re.search(r'alt="[^"]+"', img)], url


# --------------------------------------------------------------------------
# queries


def _load(client: Client, course: Course, intakes: int, vehicles: int) -> None:
    today = timezone.localdate()
    for offset in range(1, intakes + 1):
        CourseIntake.objects.create(
            course=course,
            start_date=today + timedelta(days=offset),
            mode=CourseIntake.Mode.STATIONARY,
            status=CourseIntake.Status.OPEN,
        )
    for number in range(vehicles):
        Vehicle.objects.create(course=course, make=f"Marka {number}", model="Model")


def test_the_detail_page_holds_its_query_count(client: Client, django_assert_num_queries) -> None:
    course = make_course()
    _load(client, course, intakes=5, vehicles=5)
    client.get("/kursy/kat-b/")  # warm the template cache

    # course, intakes, vehicles, then site settings three times: the context
    # processor, the DrivingSchool block and the Course block each call
    # get_solo(). django-solo can cache that, see the note in the handover.
    with django_assert_num_queries(6):
        client.get("/kursy/kat-b/")


def test_more_intakes_and_vehicles_do_not_add_queries(
    client: Client, django_assert_num_queries
) -> None:
    """The real guarantee behind the fixed count: nothing here is N+1."""
    course = make_course()
    _load(client, course, intakes=1, vehicles=1)
    client.get("/kursy/kat-b/")

    with django_assert_num_queries(6):
        client.get("/kursy/kat-b/")

    _load(client, course, intakes=20, vehicles=20)

    with django_assert_num_queries(6):
        client.get("/kursy/kat-b/")


def test_the_listing_holds_its_query_count(
    client: Client, offer: list[Course], django_assert_num_queries
) -> None:
    client.get("/kursy/")

    # courses, then site settings twice: the context processor and the
    # DrivingSchool json-ld.
    with django_assert_num_queries(3):
        client.get("/kursy/")


def test_a_longer_offer_does_not_add_queries(client: Client, django_assert_num_queries) -> None:
    make_course()
    client.get("/kursy/")

    with django_assert_num_queries(3):
        client.get("/kursy/")

    for number in range(20):
        make_course(slug=f"kat-{number}", code=str(number), title=f"Kategoria {number}")

    with django_assert_num_queries(3):
        client.get("/kursy/")
