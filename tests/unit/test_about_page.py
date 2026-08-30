"""The about page and the flat pages, DEV.md S5 acceptance criteria."""

import json
import re
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import Page, SiteSettings
from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.courses.models import Course
from apps.people.models import Instructor, Vehicle
from tests.factories import image_bytes

pytestmark = pytest.mark.django_db

ABOUT = "/o-nas/"


@pytest.fixture
def about_page() -> Page:
    site = SiteSettings.get_solo()
    site.short_name = "OSK Nawrocki"
    site.founded_year = 1996
    site.phone_primary = "43 843 29 11"
    site.save()

    return Page.objects.create(
        slug="o-nas",
        title="O nas",
        lead="Jesteśmy firmą rodzinną, szkolimy kierowców w Wieluniu od 1996 roku.",
        body=(
            "## Kim jesteśmy\n\nOśrodek szkolenia kierowców w Wieluniu.\n\n"
            "- kursy kat. B\n- badania"
        ),
        is_published=True,
    )


@pytest.fixture
def category() -> Course:
    return Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )


def make_instructor(**overrides: Any) -> Instructor:
    values: dict[str, Any] = {
        "full_name": "Adam Nawrocki",
        "role": "Instruktor kat. B",
        "since_year": 1996,
        "photo": image_bytes(),
    }
    values.update(overrides)
    return Instructor.objects.create(**values)


def make_vehicle(course: Course, **overrides: Any) -> Vehicle:
    values: dict[str, Any] = {
        "course": course,
        "make": "Skoda",
        "model": "Fabia",
        "year": 2021,
        "photo": image_bytes(),
    }
    values.update(overrides)
    return Vehicle.objects.create(**values)


def page(client: Client, url: str = ABOUT) -> str:
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode()


def tile(facts: str, description: str) -> str:
    """The figure whose description says this, so a label cannot pass for its
    value.

    A.9 point 6 lays a fact out as the number first and what it means under it,
    which is the shape the about page borrows.
    """
    found = re.search(
        rf"<p[^>]*>(?:<[^>]+>)*\s*([^<]+?)\s*(?:</[^>]+>)*</p>\s*"
        rf"<p[^>]*>[^<]*{re.escape(description)}",
        facts,
        re.S,
    )
    assert found, f"no fact described as {description!r}"
    return found.group(1).strip()


def block(body: str, testid: str) -> str:
    rest = body[body.index(f'data-testid="{testid}"') :]
    ends = [
        found for found in (rest.find('data-testid="', 1), rest.find("</section>")) if found > 0
    ]
    return rest[: min(ends, default=len(rest))]


# --------------------------------------------------------------------------
# route and seo


def test_route_matches_the_url_map(client: Client, about_page: Page) -> None:
    """tech.md section 5, and the nav route name in section 7."""
    assert reverse("core:page", kwargs={"slug": "o-nas"}) == ABOUT
    assert client.get(ABOUT).status_code == 200


def test_the_nav_can_reach_the_page(about_page: Page) -> None:
    from apps.core.navigation import NAV

    o_nas = next(item for item in NAV if item.route == "core:page")
    assert o_nas.url() == ABOUT


def test_the_other_flat_pages_answer_on_the_same_view(client: Client) -> None:
    """tech.md section 5 puts rodo and the privacy policy on page_detail too."""
    Page.objects.create(slug="rodo", title="RODO", body="## Klauzula", is_published=True)

    body = page(client, "/rodo/")
    assert "RODO" in body


def test_an_unpublished_page_is_not_reachable(client: Client, about_page: Page) -> None:
    Page.objects.filter(slug="o-nas").update(is_published=False)

    assert client.get(ABOUT).status_code == 404


def test_a_page_that_does_not_exist_is_a_404(client: Client) -> None:
    assert client.get("/rodo/").status_code == 404


def test_the_flat_route_does_not_swallow_the_other_slices(client: Client, category: Course) -> None:
    """A <slug> pattern at the root would answer for every page on the site."""
    assert client.get("/kursy/").resolver_match.view_name == "courses:list"
    assert client.get("/cennik/").resolver_match.view_name == "courses:pricing"
    assert client.get("/galeria/").resolver_match.view_name == "gallery:index"


@pytest.mark.seo
def test_page_meets_the_seo_contract(client: Client, about_page: Page) -> None:
    body = page(client)

    assert len(re.findall(r"<h1[ >]", body)) == 1

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert "Wieluń" in title
    assert len(title) <= TITLE_LIMIT

    description = re.search(r'name="description" content="(.*?)"', body).group(1)
    assert description.strip()
    assert len(description) <= DESCRIPTION_LIMIT

    canonical = re.search(r'rel="canonical" href="(.*?)"', body).group(1)
    assert canonical.endswith(ABOUT)

    types = [
        json.loads(found)["@type"]
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]
    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types


@pytest.mark.a11y
def test_every_photo_carries_an_alt(client: Client, about_page: Page, category: Course) -> None:
    """DEV.md S5: every photo goes through c-picture with a non empty alt."""
    make_instructor()
    make_vehicle(category)
    images = re.findall(r"<img[^>]*>", page(client))

    assert len(images) >= 2
    assert not [image for image in images if not re.search(r'alt="[^"]+"', image)]


def test_the_photos_are_served_as_webp(client: Client, about_page: Page, category: Course) -> None:
    make_instructor()
    make_vehicle(category)
    body = page(client)

    assert body.count('<source type="image/webp"') == 2


# --------------------------------------------------------------------------
# the body and the facts


def test_the_page_body_is_rendered_markdown(client: Client, about_page: Page) -> None:
    body = page(client)

    # The renderer shifts markdown headings down: the h1 belongs to the template.
    assert "<h3>Kim jesteśmy</h3>" in body
    assert "<li>kursy kat. B</li>" in body
    # The single h1 belongs to the template, tech.md section 8.
    assert "## Kim jesteśmy" not in body


def test_the_facts_come_from_the_database(
    client: Client, about_page: Page, category: Course
) -> None:
    for number in range(3):
        make_instructor(full_name=f"Instruktor {number}", photo=None)
    Course.objects.create(kind=Course.Kind.LICENSE, slug="kat-c", code="C", title="Kategoria C")
    # Neither an inactive category nor another kind is a licence category.
    Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-a", title="Kategoria A", is_active=False
    )
    Course.objects.create(kind=Course.Kind.PSYCHOTEST, slug="psycho", title="Badania")

    facts = block(page(client), "facts")

    # The year is the figure now, with what it means underneath, A.9 point 6.
    assert "1996" in facts
    assert "rok założenia" in facts
    assert tile(facts, "instruktorów") == "3"
    assert tile(facts, "kategorii prawa jazdy") == "2"
    # The fourth tile is the fleet count, and it is only there when there are
    # cars: a row of figures does not print a zero to keep its shape.
    assert "plac manewrowy" not in facts


def test_the_facts_stay_off_the_other_flat_pages(client: Client) -> None:
    Page.objects.create(slug="rodo", title="RODO", body="## Klauzula", is_published=True)

    assert 'data-testid="facts"' not in page(client, "/rodo/")


# --------------------------------------------------------------------------
# instructors and vehicles


def test_the_team_and_the_fleet_are_listed(
    client: Client, about_page: Page, category: Course
) -> None:
    make_instructor()
    make_vehicle(category)
    body = page(client)

    assert "Adam Nawrocki" in block(body, "instructors")
    assert "Instruktor kat. B" in block(body, "instructors")
    assert "Skoda Fabia" in block(body, "vehicles")
    assert "Kategoria B" in block(body, "vehicles")


def test_the_fleet_is_grouped_by_category(
    client: Client, about_page: Page, category: Course
) -> None:
    other = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-c", code="C", title="Kategoria C"
    )
    make_vehicle(category)
    make_vehicle(other, make="MAN", model="TGL")

    fleet = block(page(client), "vehicles")
    assert fleet.index("Kategoria B") < fleet.index("Skoda Fabia") < fleet.index("Kategoria C")


def test_the_page_survives_an_empty_team_and_an_empty_fleet(
    client: Client, about_page: Page
) -> None:
    """The acceptance criterion: nothing to show means no section, not a crash."""
    body = page(client)

    assert 'data-testid="instructors"' not in body
    assert 'data-testid="vehicles"' not in body
    assert ">Instruktorzy</h2>" not in body
    assert "Nasze pojazdy" not in body
    # The page itself still holds together.
    assert "O nas" in body
    assert 'data-testid="facts"' in body


def test_an_instructor_without_a_photo_still_renders(
    client: Client, about_page: Page, category: Course
) -> None:
    make_instructor(photo=None)
    make_vehicle(category, photo=None)
    body = page(client)

    assert "Adam Nawrocki" in body
    assert "Skoda Fabia" in body
    assert "<img" not in block(body, "instructors")


def test_inactive_records_stay_off_the_page(
    client: Client, about_page: Page, category: Course
) -> None:
    make_instructor(full_name="Były instruktor", is_active=False)
    make_vehicle(category, make="Sprzedany", model="Pojazd", is_active=False)
    body = page(client)

    assert "Były instruktor" not in body
    assert "Sprzedany" not in body


def test_a_vehicle_of_a_retired_category_is_not_advertised(
    client: Client, about_page: Page
) -> None:
    """The category is off the offer, so its fleet is not a promise to keep."""
    retired = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-a", title="Kategoria A", is_active=False
    )
    make_vehicle(retired, make="Honda", model="CB500")

    assert "Honda" not in page(client)


# --------------------------------------------------------------------------
# query count


def _load(category: Course, instructors: int, vehicles: int) -> None:
    for number in range(instructors):
        make_instructor(full_name=f"Instruktor {number}", photo=None)
    for number in range(vehicles):
        make_vehicle(category, make=f"Marka {number}", photo=None)


def test_the_page_holds_its_query_count(
    client: Client, about_page: Page, category: Course, django_assert_num_queries: Any
) -> None:
    _load(category, instructors=3, vehicles=3)
    client.get(ABOUT)  # warm the template cache

    # page, instructors, their categories, vehicles, the category count, then
    # site settings twice: the context processor and the DrivingSchool block.
    with django_assert_num_queries(7):
        client.get(ABOUT)


def test_more_people_and_more_cars_do_not_add_queries(
    client: Client, about_page: Page, category: Course, django_assert_num_queries: Any
) -> None:
    """The real guarantee behind the fixed count: nothing here is N+1."""
    _load(category, instructors=1, vehicles=1)
    client.get(ABOUT)

    with django_assert_num_queries(7):
        client.get(ABOUT)

    _load(category, instructors=15, vehicles=15)

    with django_assert_num_queries(7):
        client.get(ABOUT)


# --------------------------------------------------------------------------
# FRONTEND_FIXES.md X2


def test_every_figure_in_the_row_is_a_figure(client: Client, about_page: Page) -> None:
    """X2 point 2, A.3 finding 13.

    The fourth tile read "własny", a word among numbers, and a row of figures
    stops being a row the moment one of them is a word. The sentence it carried
    now sits under the count it belongs to.
    """
    from apps.people.models import Vehicle

    make_instructor(full_name="Instruktor 1", photo=None)
    course = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B", is_active=True
    )
    Vehicle.objects.create(course=course, make="Pojazd", model="szkoleniowy 1", is_active=True)

    facts = block(page(client), "facts")
    figures = re.findall(r"<p[^>]*>\s*([^<]+?)\s*</p>\s*<p[^>]*>", facts)
    assert figures, "the row of figures is gone"
    for figure in figures:
        assert figure.isdigit(), f"{figure!r} is not a number"


def test_the_page_ends_on_an_inverted_invitation(client: Client, about_page: Page) -> None:
    """X2 point 6: it used to end on a light section, with the dark block
    stranded in the middle."""
    body = page(client)
    inside = body[body.index("<main") : body.index("</main>")]
    last = inside.rindex("<section")
    assert "u-ground-ink" in inside[last : last + 400]
    assert "Chcesz zacząć kurs?" in inside[last:]


def test_exactly_one_block_is_inverted(client: Client, about_page: Page) -> None:
    """More than one and neither carries any weight.

    Counted inside main: the footer is a deep ground of its own and is not one
    of the page's blocks.
    """
    body = page(client)
    inside = body[body.index("<main") : body.index("</main>")]
    assert inside.count("u-ground-ink") + inside.count("u-ground-deep") == 1


def test_the_body_headings_read_as_headings(client: Client, about_page: Page) -> None:
    """A.1 finding 6, the main reason the page read as plain text.

    render_markdown shifts headings down one, because the page owns its only h1
    and the template writes it. A section inside a body is therefore a single
    hash — written with two it arrived as an h3 and lost to the page lead above
    it.
    """
    Page.objects.filter(slug="o-nas").update(body="# Kim jesteśmy\n\nTreść.")

    body = page(client)
    assert "<h2>Kim jesteśmy</h2>" in body
    assert "u-prose" in body


def test_a_legal_page_gets_no_invitation(client: Client) -> None:
    """A privacy policy has nothing to invite anyone to.

    The sticky call bar stays — it is the site's, not the page's, and it is how
    somebody reaches the school from anywhere. What the page does not get is
    the inverted block asking them to sign up in the middle of a privacy
    notice.
    """
    Page.objects.create(slug="rodo", title="RODO", body="# Klauzula", is_published=True)

    body = page(client, "/rodo/")
    inside = body[body.index("<main") : body.index("</main>")]
    assert "u-ground-ink" not in inside
    assert "Zostaw numer albo zadzwoń" not in inside
