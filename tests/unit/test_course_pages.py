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
    # The seventh is the course select in the enrolment form the page now ends
    # with, DEV.md S3.1 — one query for the whole list, not one per option.
    with django_assert_num_queries(8):
        client.get("/kursy/kat-b/")


def test_more_intakes_and_vehicles_do_not_add_queries(
    client: Client, django_assert_num_queries
) -> None:
    """The real guarantee behind the fixed count: nothing here is N+1."""
    course = make_course()
    _load(client, course, intakes=1, vehicles=1)
    client.get("/kursy/kat-b/")

    with django_assert_num_queries(8):
        client.get("/kursy/kat-b/")

    _load(client, course, intakes=20, vehicles=20)

    with django_assert_num_queries(8):
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


# --------------------------------------------------------------------------
# the listing composition, FRONTEND.md F4


def category_tiles(html: str) -> list[str]:
    """Every licence tile on the page, markup and all.

    Found by a test hook rather than by its classes. This helper matched on the
    grid's exact class string and on the anchor's class starting with "group",
    and both broke the moment the tile learned to lift — the anchor gained
    u-card ahead of group and the search quietly returned nothing at all, which
    reads as "the page renders no tiles" rather than "the test lost them".
    """
    return re.findall(
        r'<a [^>]*data-testid="category-tile"[^>]*>.*?</a>',
        html,
        re.S,
    )


def test_the_listing_draws_one_tile_per_active_course(client: Client) -> None:
    for number in range(4):
        make_course(slug=f"kat-{number}", code=str(number), title=f"Kategoria {number}")
    make_course(slug="kat-x", code="X", title="Kategoria X", is_active=False)

    tiles = category_tiles(body_of(client, "/kursy/"))
    assert len(tiles) == Course.objects.filter(is_active=True).count() == 4


def test_the_tile_is_the_same_markup_as_on_the_home_page(client: Client) -> None:
    """F4's first acceptance criterion, checked the only way that settles it.

    Both pages include courses/_category_grid.html, so this passes by
    construction — and fails the moment someone copies the grid into one of
    them and edits it there.

    The heading tag is the one thing allowed to differ, and it has to: on the
    listing the grid sits straight under the h1, so its titles are h2, while on
    the home page they sit inside a section that already has one and stay h3.
    Identical there would mean a skipped level on one of the two pages. Nothing
    visual changes — the tag carries no styling of its own.
    """
    make_course()

    on_home = category_tiles(body_of(client, reverse("core:home")))
    on_listing = category_tiles(body_of(client, "/kursy/"))

    assert len(on_home) == len(on_listing) == 1

    def without_heading_level(tile: str) -> list[str]:
        return re.sub(r"</?h[1-6]([ >])", r"<h", tile).split()

    assert without_heading_level(on_home[0]) == without_heading_level(on_listing[0])

    # And the levels really are the ones each page needs.
    assert re.search(r"<h3[^>]*>\s*Kategoria B", on_home[0])
    assert re.search(r"<h2[^>]*>\s*Kategoria B", on_listing[0])


def test_the_listing_never_prints_a_zero_price(client: Client) -> None:
    """F4: cena na zapytanie, never 0 zł."""
    make_course(price_gross=None)

    html = body_of(client, "/kursy/")
    assert "cena na zapytanie" in html
    assert not re.search(r">\s*(od\s*)?0([,.]00)?\s*zł", html)


def test_the_listing_title_names_the_town(client: Client) -> None:
    """tech.md section 8 fixes the suffix, so the town is always in the title."""
    make_course()
    title = re.search(r"<title>(.*?)</title>", body_of(client, "/kursy/"), re.S)
    assert title
    assert "Wieluń" in title.group(1)


def test_the_listing_carries_no_filter(client: Client) -> None:
    """F4: fifteen courses, and a filter over fifteen rows costs more than it
    saves."""
    make_course()
    html = body_of(client, "/kursy/")
    section = html[html.index("<main") : html.index("</main>")]
    assert "<form" not in section
    assert "<select" not in section


# --------------------------------------------------------------------------
# the detail card, FRONTEND.md F5


def card_of(html: str) -> str:
    """The sticky card in the right column."""
    aside = re.search(r"<aside\b.*?</aside>", html, re.S)
    assert aside, "the detail page lost its card"
    return aside.group()


def test_the_card_offers_to_agree_a_term_when_there_is_none(client: Client) -> None:
    """F5: never an empty slot where a date belongs."""
    make_course()
    card = card_of(body_of(client, "/kursy/kat-b/"))
    assert "Zadzwoń, ustalimy termin" in card


def test_the_card_shows_the_nearest_start_when_there_is_one(client: Client) -> None:
    course = make_course()
    CourseIntake.objects.create(
        course=course,
        start_date=timezone.localdate() + timedelta(days=9),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.OPEN,
    )

    card = card_of(body_of(client, "/kursy/kat-b/"))
    assert "Zadzwoń, ustalimy termin" not in card
    assert (timezone.localdate() + timedelta(days=9)).strftime("%d.%m") in card


def test_the_card_asks_for_the_price_when_there_is_none(client: Client) -> None:
    make_course(price_gross=None)
    card = card_of(body_of(client, "/kursy/kat-b/"))
    assert "Zapytaj o cenę" in card
    assert "Zapisz się" not in card


def test_a_price_note_alone_never_fills_the_figure_slot(client: Client) -> None:
    """format_price returns the note on its own when there is no amount.

    So the template has to decide on course.price_gross, not on the formatted
    string — otherwise a note like "cena do potwierdzenia" lands in the slot
    sized for a number and the page claims to have a price it does not have.
    """
    make_course(price_gross=None, price_note="cena do potwierdzenia")

    card = card_of(body_of(client, "/kursy/kat-b/"))
    assert "Zapytaj o cenę" in card
    assert "cena do potwierdzenia" not in card


def test_the_card_only_sticks_from_lg(client: Client) -> None:
    """F5: it unsticks on mobile, where it belongs in the flow rather than on
    top of what the reader came for."""
    make_course()
    aside = re.search(r'<aside\b[^>]*class="([^"]*)"', body_of(client, "/kursy/kat-b/"))
    assert aside
    classes = aside.group(1).split()
    assert "lg:sticky" in classes
    assert "lg:self-start" in classes, "a stretched grid item has nothing to stick against"
    # Bare and unprefixed would stick it on a phone too.
    assert "sticky" not in classes


# --------------------------------------------------------------------------
# FRONTEND_FIXES.md X3


def test_the_course_page_alternates_its_grounds(client: Client) -> None:
    """X3 point 5: the whole page used to be one section, so nothing changed."""
    course = make_course()

    body = body_of(client, course.get_absolute_url())
    sections = re.findall(r'<section[^>]*class="([^"]*)"', body)
    grounds = [
        "muted" if "bg-paper-50" in cls else "ink" if "u-ground-ink" in cls else "paper"
        for cls in sections
    ]
    repeats = [i for i in range(1, len(grounds)) if grounds[i] == grounds[i - 1]]
    assert not repeats, f"sections {repeats} repeat the ground before them: {grounds}"
    assert grounds[-1] == "ink", "the page does not end on the invitation"


def test_the_closing_words_follow_the_kind_of_course(client: Client) -> None:
    """X3 point 8: a category and a professional qualification are not booked
    for the same reason."""
    category = make_course(slug="kat-b", code="B", title="Kategoria B")
    assert "Nie wiesz, czy ta kategoria" in body_of(client, category.get_absolute_url())

    pro = make_course(
        slug="adr", code="", title="ADR", kind=Course.Kind.PROFESSIONAL, price_gross=None
    )
    assert "Potrzebujesz tych uprawnień do pracy?" in body_of(client, pro.get_absolute_url())


def test_the_sticky_card_clears_the_header(client: Client) -> None:
    """X3 keeps the sticky card as it is, but its offset was the header height
    written out by hand. It reads the variable X0 introduced, so moving the
    header moves the card with it."""
    course = make_course()
    body = body_of(client, course.get_absolute_url())
    assert "lg:sticky" in body
    assert "var(--header-h)" in body
