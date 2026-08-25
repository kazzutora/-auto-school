"""Intake schedule and its filter, DEV.md S2.2 acceptance criteria."""

import re
from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteSettings
from apps.courses.models import Course, CourseIntake

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def offer() -> dict[str, Course]:
    return {
        "b": Course.objects.create(
            kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
        ),
        "c": Course.objects.create(
            kind=Course.Kind.LICENSE, slug="kat-c", code="C", title="Kategoria C"
        ),
    }


def make_intake(course: Course, **overrides: object) -> CourseIntake:
    values: dict = {
        "course": course,
        "start_date": timezone.localdate() + timedelta(days=7),
        "mode": CourseIntake.Mode.STATIONARY,
        "language": "pl",
        "status": CourseIntake.Status.OPEN,
    }
    values.update(overrides)
    return CourseIntake.objects.create(**values)


def table(body: str) -> str:
    """Just the table body.

    The whole page also carries the course titles in the filter select and a
    "Zapisz się" label on the sticky bar, and the table head has a <tr> of its
    own. Matching against the page would pass on any of those.
    """
    found = re.search(r"<tbody[^>]*>(.*?)</tbody>", body, re.S)
    return found.group(1) if found else body  # the partial is already rows


def rows(body: str) -> list[str]:
    return re.findall(r"<tr>(.*?)</tr>", table(body), re.S)


def page(client: Client, **params: str) -> str:
    response = client.get(reverse("courses:intakes"), params)
    assert response.status_code == 200
    return response.content.decode()


def partial(client: Client, **params: str) -> str:
    response = client.get(reverse("courses:intake_filter"), params, **HTMX)
    assert response.status_code == 200
    return response.content.decode()


# --------------------------------------------------------------------------
# routes


def test_the_routes_match_the_url_map() -> None:
    """tech.md sections 5 and 7."""
    assert reverse("courses:intakes") == "/terminy/"
    assert reverse("courses:intake_filter") == "/terminy/filter/"


def test_exactly_one_h1(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"])
    assert len(re.findall(r"<h1[ >]", page(client))) == 1


# --------------------------------------------------------------------------
# what is listed


def test_a_past_intake_is_not_listed(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], start_date=timezone.localdate() - timedelta(days=1))

    assert "Kategoria B" not in table(page(client))


def test_a_closed_intake_is_not_listed(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], status=CourseIntake.Status.CLOSED)

    assert "Kategoria B" not in table(page(client))


def test_a_full_intake_is_still_listed(client: Client, offer: dict[str, Course]) -> None:
    """Better to say brak miejsc than to hide a group that exists."""
    make_intake(offer["b"], status=CourseIntake.Status.FULL)

    body = table(page(client))
    assert "Kategoria B" in body
    assert "Brak miejsc" in body


def test_a_planned_intake_is_listed(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], status=CourseIntake.Status.PLANNED)

    body = table(page(client))
    assert "Kategoria B" in body
    assert "Planowany" in body


def test_intakes_are_sorted_by_date(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], start_date=timezone.localdate() + timedelta(days=30))
    make_intake(offer["c"], start_date=timezone.localdate() + timedelta(days=5))

    listed = rows(page(client))
    assert "Kategoria C" in listed[0]
    assert "Kategoria B" in listed[1]


# --------------------------------------------------------------------------
# filters


def test_filter_by_course(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"])
    make_intake(offer["c"])

    body = table(page(client, course="kat-b"))

    assert "Kategoria B" in body
    assert "Kategoria C" not in body


def test_filter_by_language(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], language="pl")
    make_intake(offer["c"], language="ru")

    body = table(page(client, language="ru"))

    assert "Kategoria C" in body
    assert "Kategoria B" not in body


def test_filter_by_mode(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], mode=CourseIntake.Mode.STATIONARY)
    make_intake(offer["c"], mode=CourseIntake.Mode.ELEARNING)

    body = table(page(client, mode="elearning"))

    assert "Kategoria C" in body
    assert "Kategoria B" not in body


def test_filters_combine(client: Client, offer: dict[str, Course]) -> None:
    wanted = make_intake(offer["b"], language="uk", mode=CourseIntake.Mode.MIXED)
    make_intake(offer["b"], language="uk", mode=CourseIntake.Mode.STATIONARY)
    make_intake(offer["c"], language="uk", mode=CourseIntake.Mode.MIXED)

    body = page(client, course="kat-b", language="uk", mode="mixed")

    assert len(rows(body)) == 1
    assert f"intake={wanted.pk}" in body


def test_an_empty_filter_shows_everything(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"])
    make_intake(offer["c"])

    assert len(rows(page(client))) == 2


def test_an_unknown_value_narrows_to_nothing(client: Client, offer: dict[str, Course]) -> None:
    """Silently ignoring it would show rows in a language nobody asked for."""
    make_intake(offer["b"], language="pl")

    assert "Kategoria B" not in table(page(client, language="de"))


def test_the_filter_only_offers_courses_that_have_a_start(
    client: Client, offer: dict[str, Course]
) -> None:
    make_intake(offer["b"])

    options = re.search(r'<select name="course".*?</select>', page(client), re.S).group()
    assert "kat-b" in options
    assert "kat-c" not in options


# --------------------------------------------------------------------------
# empty result


def test_an_empty_result_talks_to_the_visitor(client: Client, offer: dict[str, Course]) -> None:
    """An empty table tells nobody what to do next."""
    site = SiteSettings.get_solo()
    site.phone_primary = "605 065 795"
    site.save()

    body = page(client, course="kat-b")

    assert "Nic nie pasuje do tych filtrów" in body
    assert "tel:605065795" in body


# --------------------------------------------------------------------------
# htmx and the no javascript path


def test_the_htmx_endpoint_returns_a_partial(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"])

    body = partial(client)

    assert "<html" not in body
    assert "<tr>" in body
    assert "Kategoria B" in body


def test_the_plain_page_returns_a_whole_document(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"])

    body = page(client)

    assert "<html" in body
    assert "<tr>" in body


def test_the_form_gives_the_same_rows_as_htmx(client: Client, offer: dict[str, Course]) -> None:
    """The acceptance criterion: the filter has to work with javascript off."""
    make_intake(offer["b"], language="pl")
    make_intake(offer["c"], language="ru")

    without_js = rows(page(client, language="ru"))
    with_htmx = rows(partial(client, language="ru"))

    assert without_js == with_htmx
    assert len(with_htmx) == 1


def test_the_form_posts_to_the_full_page(client: Client, offer: dict[str, Course]) -> None:
    """Without javascript the browser follows action, not hx-get."""
    make_intake(offer["b"])
    body = page(client)

    form = re.search(r"<form[^>]*>", body).group()
    assert 'method="get"' in form
    assert 'action="/terminy/"' in form


# --------------------------------------------------------------------------
# rows


def test_the_enrol_button_carries_the_intake(client: Client, offer: dict[str, Course]) -> None:
    intake = make_intake(offer["b"])

    assert f"/zapisz-sie/?intake={intake.pk}" in page(client)


def test_a_full_group_does_not_offer_enrolment(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], status=CourseIntake.Status.FULL)

    body = table(page(client))
    assert "Zapisz się" not in body
    assert "Zapytaj" in body


def test_free_seats_are_shown_when_known(client: Client, offer: dict[str, Course]) -> None:
    make_intake(offer["b"], seats_total=20, seats_taken=17)

    assert "wolne miejsca: 3" in table(page(client))


def test_the_schedule_holds_its_query_count(
    client: Client, offer: dict[str, Course], django_assert_num_queries
) -> None:
    for _ in range(3):
        make_intake(offer["b"])
    client.get("/terminy/")

    # intakes, filter course options, site settings twice.
    with django_assert_num_queries(4):
        client.get("/terminy/")

    for _ in range(20):
        make_intake(offer["c"])

    with django_assert_num_queries(4):
        client.get("/terminy/")
