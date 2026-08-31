"""Everything the owner owns is reachable from the admin, and removable.

Three models shipped without an admin — intakes, price rows and testimonials —
so they could be seeded and then only ever reached from a shell. The owner
asked to be able to delete things and found there was nothing to click.

The other half of that story is CourseIntake.course being PROTECT: a course
with dates on it refuses to be deleted, and with no intake admin there was no
way to clear the block at all.
"""

from datetime import date
from typing import Any

import pytest
from django.apps import apps as django_apps
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.courses.models import Course, CourseIntake

pytestmark = pytest.mark.django_db

# The apps whose rows are the school's own content. Django's own tables and the
# celery ones are not the owner's to curate.
OWNED = ("core", "courses", "gallery", "leads", "links", "people", "reviews")

# A singleton row that is created once and edited forever. Deleting it would
# leave every page without an address or a phone number.
NO_DELETE = {"core.SiteSettings"}


@pytest.fixture
def staff(client: Client) -> None:
    user = get_user_model().objects.create_superuser("owner", "o@example.com", "pass-1234-pass")
    client.force_login(user)


def make_course(**overrides: Any) -> Course:
    values: dict[str, Any] = {
        "slug": "kat-b",
        "code": "B",
        "kind": Course.Kind.LICENSE,
        "title": "Kategoria B",
        "is_active": True,
    }
    values.update(overrides)
    return Course.objects.create(**values)


def owned_models() -> list[Any]:
    return [m for m in django_apps.get_models() if m._meta.app_label in OWNED]


def test_every_model_the_owner_owns_has_an_admin() -> None:
    """A model with no admin is a model the owner cannot touch."""
    missing = [m._meta.label for m in owned_models() if m not in site._registry]
    assert not missing, f"no admin for: {missing}"


def test_every_admin_but_the_settings_row_can_delete(rf, staff) -> None:
    """Delete is the whole point of this pass. SiteSettings is the one row that
    must survive, because every page reads its address and phone."""
    request = rf.get("/admin/")
    request.user = get_user_model().objects.get(username="owner")

    for model in owned_models():
        admin_class = site._registry[model]
        allowed = admin_class.has_delete_permission(request)
        expected = model._meta.label not in NO_DELETE
        assert allowed is expected, f"{model._meta.label}: delete={allowed}"


@pytest.mark.parametrize(
    "route",
    [
        "admin:courses_courseintake_changelist",
        "admin:courses_priceitem_changelist",
        "admin:reviews_testimonial_changelist",
    ],
)
def test_the_new_pages_open(client: Client, staff, route: str) -> None:
    assert client.get(reverse(route)).status_code == 200


def test_a_course_with_intakes_refuses_a_plain_delete(client: Client, staff) -> None:
    """PROTECT is doing its job, and this is the wall the owner walked into."""
    course = make_course()
    CourseIntake.objects.create(
        course=course, start_date=date(2026, 9, 1), mode=CourseIntake.Mode.STATIONARY
    )

    response = client.post(
        reverse("admin:courses_course_delete", args=[course.pk]), {"post": "yes"}
    )

    assert Course.objects.filter(pk=course.pk).exists(), "the course went in spite of PROTECT"
    assert response.status_code in (200, 403)


def test_the_action_removes_the_course_and_its_intakes(client: Client, staff) -> None:
    """The same removal, asked for out loud. One transaction, so a course whose
    intakes went but which stayed behind is not a state the database can be in.
    """
    course = make_course()
    for day in (1, 15):
        CourseIntake.objects.create(
            course=course, start_date=date(2026, 9, day), mode=CourseIntake.Mode.STATIONARY
        )

    response = client.post(
        reverse("admin:courses_course_changelist"),
        {"action": "delete_with_intakes", "_selected_action": [str(course.pk)]},
        follow=True,
    )

    assert response.status_code == 200
    assert not Course.objects.filter(pk=course.pk).exists()
    assert not CourseIntake.objects.filter(course_id=course.pk).exists()


def test_the_course_list_shows_what_blocks_the_delete(client: Client, staff) -> None:
    """The count is on the list so the refusal stops being a surprise."""
    course = make_course()
    CourseIntake.objects.create(
        course=course, start_date=date(2026, 9, 1), mode=CourseIntake.Mode.STATIONARY
    )

    body = client.get(reverse("admin:courses_course_changelist")).content.decode()
    assert "Nabory" in body, "the intake column is missing from the course list"
