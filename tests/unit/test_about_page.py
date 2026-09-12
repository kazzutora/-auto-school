"""The about page and the flat pages, DEV.md S5 acceptance criteria."""

import json
import re
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import Page, SiteSettings
from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.courses.models import Course
from apps.people.models import Instructor, Vehicle
from tests.factories import image_bytes

from tests.conftest import images_without_alt, section_grounds

pytestmark = pytest.mark.django_db

ABOUT = "/o-nas/"


@pytest.fixture
def about_page() -> Page:
    site = SiteSettings.get_solo()
    site.short_name = "OSK Ostrycharz"
    site.founded_year = 1996
    site.phone_primary = "691 570 489"
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
        "full_name": "Adam Kowalski",
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
    """core:page answers for four slugs, so the route alone is not an address."""
    from apps.core.navigation import NAV

    o_nas = next(
        item for item in NAV if item.route == "core:page" and item.kwargs.get("slug") == "o-nas"
    )
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
    body = page(client)
    images = re.findall(r"<img[^>]*>", body)

    assert len(images) >= 2
    assert not images_without_alt(body)


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
    """Every figure is read from a row, never written into the template.

    The count of licence categories is deliberately not among them: "1
    kategoria" is not a fact anybody is impressed by, and it would cost a third
    query on a page that has a budget.
    """
    from apps.core.models import PassRate

    for number in range(3):
        make_instructor(full_name=f"Instruktor {number}", photo=None)
    PassRate.objects.create(
        year=2025, students=92, passed_1st=68, passed_2nd=16, passed_3rd=3, passed_4th=3
    )
    Course.objects.filter(pk=category.pk).update(price_gross=Decimal("3700"))

    facts = block(page(client), "facts")

    # The year is the figure, with what it means underneath, A.9 point 6.
    assert "1996" in facts
    assert "rok założenia" in facts
    assert tile(facts, "zdaje egzamin za pierwszym razem") == "74%"
    assert tile(facts, "kursantów w ostatnim roczniku") == "92"
    assert tile(facts, "instruktorów prowadzi zajęcia") == "3"


def test_a_fact_with_no_number_behind_it_is_absent(
    client: Client, about_page: Page, category: Course
) -> None:
    """A row of figures reading "0 instruktorów" is worse than a row of two."""
    facts = block(page(client), "facts")

    assert "instruktorów prowadzi zajęcia" not in facts
    assert "zdaje egzamin za pierwszym razem" not in facts


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

    assert "Adam Kowalski" in block(body, "instructors")
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


def test_a_vehicle_without_a_photo_still_renders_but_an_instructor_does_not(
    client: Client, about_page: Page, category: Course
) -> None:
    """The line REDESIGN.md D.2 draws, and it is drawn between things and people.

    A car card without a photograph is a specification: make, model, year,
    gearbox. Every one of those is a fact out of the database and reads as one,
    so the card is honest with an empty frame or none at all.

    A person card without a photograph is a name in an empty box, and the box
    is an invitation to fill it. D.2's example is exactly that: a stock portrait
    captioned "Piotr, instruktor od 8 lat", a person who does not exist, and a
    client who turns up at the school asking for him. So the instructor half of
    this rule is the strict one — no real photograph, no card — and the vehicle
    half is unchanged.

    This test used to assert that both still rendered. Half of it was reversed
    at core v25 and the half that was not is still here, on purpose: the rule is
    a distinction, not a blanket, and a blanket in either direction would be
    wrong.
    """
    make_instructor(photo=None)
    make_vehicle(category, photo=None)
    body = page(client)

    assert "Skoda Fabia" in body, "a vehicle is a specification and reads as one"
    assert "Adam Kowalski" not in body, (
        "an instructor with no photograph was rendered as a card; REDESIGN.md D.2"
    )
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
    with django_assert_num_queries(9):
        client.get(ABOUT)


def test_more_people_and_more_cars_do_not_add_queries(
    client: Client, about_page: Page, category: Course, django_assert_num_queries: Any
) -> None:
    """The real guarantee behind the fixed count: nothing here is N+1."""
    _load(category, instructors=1, vehicles=1)
    client.get(ABOUT)

    with django_assert_num_queries(9):
        client.get(ABOUT)

    _load(category, instructors=15, vehicles=15)

    with django_assert_num_queries(9):
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


def test_the_page_ends_on_an_invitation_that_is_not_dark(
    client: Client, about_page: Page
) -> None:
    """B.8 point 4, and B.8 point 2 on where the dark block may not be.

    The rule moved at core v25, and the geometry is why.

    B.7 point 11 makes the footer a dark card the full width of the page with a
    28px radius along its top. A dark section directly above it merges into one
    very tall dark region, and the radius — the shape whose whole job is to say
    "this is where the page ends" — has nothing to read against.

    So the page's one dark block sits mid page and the closing band takes the
    page ground. What has not moved is B.8 point 4: the page still ends on an
    action. It is the ground that changed, not the rule, and the old assertion
    checked the ground because that had been a fair proxy while the closing
    band was the only inverted thing on the page.
    """
    body = page(client)
    inside = body[body.index("<main") : body.index("</main>")]
    last = inside.rindex("<section")
    closing = inside[last:]

    assert "Zaczynamy?" in closing, "the page does not close on an invitation"
    assert "tel:" in closing or "/zapisz-sie/" in closing, "the invitation has no action in it"
    assert section_grounds(inside)[-1] != "dark", (
        "the last section is dark, straight above the dark footer"
    )


def test_at_most_one_block_is_dark(client: Client, about_page: Page) -> None:
    """B.8 point 2. More than one and neither carries any weight.

    "At most", not "exactly": a privacy policy has nothing that deserves the
    treatment, and forcing a dark band onto it is decoration. What the rule is
    against is several of them.

    Counted inside main: the footer is a dark card of its own and is layout
    rather than one of the page's blocks.
    """
    body = page(client)
    inside = body[body.index("<main") : body.index("</main>")]
    assert section_grounds(inside).count("dark") <= 1


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


def test_a_legal_page_asks_about_the_document_and_never_for_a_signup(
    client: Client,
) -> None:
    """A privacy policy has nothing to sell, but it is not a dead end either.

    The original rule here was "a legal page gets no closing block at all", and
    what it was protecting against is right and still enforced below: an
    inverted band asking somebody to sign up in the middle of a privacy notice
    reads as a school that was not listening.

    REDESIGN.md B.8 point 4 asks every page to end on an action, and the two
    only look like a conflict. The action on a legal page is not enrolment — it
    is reaching a person about the document, which is exactly what somebody who
    has just read a data notice may want. So the band is there, it offers the
    telephone, and it carries no enrolment link and no enrolment words.

    The sticky call bar is unaffected either way: it is the site's, not the
    page's, and it is below md only.
    """
    Page.objects.create(slug="rodo", title="RODO", body="# Klauzula", is_published=True)

    body = page(client, "/rodo/")
    inside = body[body.index("<main") : body.index("</main>")]

    # The closing band itself, not everything after the last section: the
    # sticky call bar sits below it and is the site's, not the page's.
    closing = inside[inside.rindex("<section") :]
    closing = closing[: closing.index("</section>")]

    # Ends on an action, B.8 point 4. The contact page rather than the phone,
    # because the phone is conditional on SiteSettings and this band must not
    # be able to render with nothing in it.
    assert "/kontakt/" in closing, "a legal page still has to offer a way to reach a person"

    # And the action is not a signup, which is what the original rule was for.
    assert "Zostaw numer albo zadzwoń" not in inside
    assert "Zapisz się" not in closing
    assert "/zapisz-sie/" not in closing


# --------------------------------------------------------------------------
# photographs, REDESIGN.md part D


def test_an_instructor_without_a_photograph_gets_no_card(
    client: Client, about_page: Page
) -> None:
    """D.2, and R8's acceptance criterion in as many words.

    An instructor card exists to put a face to a name. Without the face it is a
    name in an empty box, and an empty box on a page about people is an
    invitation to fill it — which is exactly how a stock portrait ends up
    captioned "Piotr, instruktor od 8 lat" on a commercial site, describing
    somebody who does not exist. D.2 says what happens next: a client walks into
    the school and asks for him.

    So the rule is not "prefer a photograph". It is: no real photograph, no
    card. This test is what stops that being softened back into a placeholder.
    """
    make_instructor(full_name="Z Fotografią", photo=image_bytes())
    make_instructor(full_name="Bez Fotografii", photo=None)

    body = page(client)

    assert "Z Fotografią" in body
    assert "Bez Fotografii" not in body, (
        "an instructor with no photograph was rendered as a card; REDESIGN.md D.2"
    )


def test_a_block_with_no_photographs_says_so_instead_of_showing_empty_frames(
    client: Client, about_page: Page
) -> None:
    """The other half of D.2: the block does not quietly vanish either.

    Somebody scrolling to "Instruktorzy" came looking for exactly that, so they
    get a sentence and a telephone number rather than a gap — <c-empty>, which
    is the component BLOCKS.md B8 exists for.
    """
    make_instructor(full_name="Bez Fotografii", photo=None)

    body = page(client)
    assert 'data-testid="instructors-empty"' in body
    assert "Zdjęcia instruktorów w przygotowaniu" in body
    assert "Bez Fotografii" not in body
