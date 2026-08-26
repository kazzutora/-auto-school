"""People admin, DEV.md S5: this is where the owner fills the team and the fleet."""

import re

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.courses.models import Course
from apps.people.models import Instructor, Vehicle
from tests.factories import image_bytes

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(client: Client) -> None:
    user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass-1234-pass")
    client.force_login(user)


@pytest.fixture
def category() -> Course:
    return Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )


def changelist(client: Client, model: str) -> str:
    response = client.get(reverse(f"admin:people_{model}_changelist"))
    assert response.status_code == 200
    return response.content.decode()


def test_both_models_are_registered() -> None:
    assert Instructor in site._registry
    assert Vehicle in site._registry


def test_the_instructor_photo_shows_in_the_list(
    client: Client, staff: None, category: Course
) -> None:
    """The preview is the point: the owner cannot tell rows apart by name alone."""
    instructor = Instructor.objects.create(full_name="Adam Nawrocki", photo=image_bytes())
    instructor.categories.add(category)

    row = changelist(client, "instructor")
    image = re.search(r"<img[^>]*people[^>]*>", row)

    assert image, "no photo preview in the changelist"
    assert 'alt="Adam Nawrocki"' in image.group(0)


def test_a_row_without_a_photo_does_not_break_the_list(client: Client, staff: None) -> None:
    Instructor.objects.create(full_name="Bez zdjęcia")

    assert "Bez zdjęcia" in changelist(client, "instructor")


def test_the_vehicle_photo_shows_in_the_list(client: Client, staff: None, category: Course) -> None:
    Vehicle.objects.create(course=category, make="Skoda", model="Fabia", photo=image_bytes())

    row = changelist(client, "vehicle")
    image = re.search(r"<img[^>]*vehicles[^>]*>", row)

    assert image
    assert 'alt="Skoda Fabia"' in image.group(0)


def add_rows(category: Course, how_many: int, offset: int = 0) -> None:
    for number in range(offset, offset + how_many):
        instructor = Instructor.objects.create(full_name=f"Instruktor {number}")
        instructor.categories.add(category)
        Vehicle.objects.create(course=category, make=f"Marka {number}", model="Model")


def queries(client: Client, model: str) -> int:
    with CaptureQueriesContext(connection) as captured:
        changelist(client, model)
    return len(captured)


@pytest.mark.parametrize("model", ["instructor", "vehicle"])
def test_more_rows_do_not_add_queries(
    client: Client, staff: None, category: Course, model: str
) -> None:
    """The changelist reads a category per row, and must not do it row by row.

    Django adds the select_related for a related field in list_display by
    itself. The guard is here for the day list_display grows a field it cannot
    see through, which is when the owner would feel it.
    """
    add_rows(category, 1)
    queries(client, model)  # warm the session and the template cache
    baseline = queries(client, model)

    add_rows(category, 15, offset=1)

    assert queries(client, model) == baseline


def test_the_owner_can_filter_and_search(client: Client, staff: None, category: Course) -> None:
    Instructor.objects.create(full_name="Adam Nawrocki", role="Instruktor kat. B")
    Instructor.objects.create(full_name="Były instruktor", is_active=False)

    url = reverse("admin:people_instructor_changelist")
    active = client.get(url, {"is_active__exact": "1"}).content.decode()
    found = client.get(url, {"q": "Nawrocki"}).content.decode()

    assert "Adam Nawrocki" in active
    assert "Były instruktor" not in active
    assert "Adam Nawrocki" in found
