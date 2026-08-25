"""Courses admin, DEV.md S1.1."""

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.courses.admin import CourseAdmin, CourseIntakeInline, VehicleInline
from apps.courses.models import Course, CourseIntake
from apps.people.models import Vehicle

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(client: Client) -> None:
    user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass-1234-pass")
    client.force_login(user)


@pytest.fixture
def course() -> Course:
    return Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B", min_age=18
    )


def test_list_display_matches_the_task() -> None:
    admin = site._registry[Course]
    # Django normalises these to lists, so compare on content not on type.
    assert tuple(admin.list_display) == (
        "title",
        "kind",
        "code",
        "price_gross",
        "is_active",
        "order",
    )
    assert tuple(admin.list_filter) == ("kind", "is_active")


def test_both_inlines_are_wired() -> None:
    assert set(CourseAdmin.inlines) == {CourseIntakeInline, VehicleInline}
    assert CourseIntakeInline.model is CourseIntake
    assert VehicleInline.model is Vehicle


def test_changelist_renders(client: Client, staff: None, course: Course) -> None:
    response = client.get(reverse("admin:courses_course_changelist"))

    assert response.status_code == 200
    assert "Kategoria B" in response.content.decode()


def test_change_form_renders_with_the_inlines(client: Client, staff: None, course: Course) -> None:
    response = client.get(reverse("admin:courses_course_change", args=[course.pk]))
    body = response.content.decode()

    assert response.status_code == 200
    assert "intakes" in body
    assert "vehicles" in body


def test_add_form_renders(client: Client, staff: None) -> None:
    assert client.get(reverse("admin:courses_course_add")).status_code == 200


def test_duplicate_creates_an_inactive_copy(client: Client, staff: None, course: Course) -> None:
    Vehicle.objects.create(course=course, make="Skoda", model="Fabia")

    client.post(
        reverse("admin:courses_course_changelist"),
        {"action": "duplicate_course", "_selected_action": [str(course.pk)], "index": "0"},
        follow=True,
    )

    copy = Course.objects.get(slug="kat-b-kopia")
    assert copy.pk != course.pk
    assert copy.title == course.title
    assert copy.is_active is False, "a draft must not reach a public page"
    assert copy.vehicles.count() == 1
    assert Course.objects.get(pk=course.pk).is_active is True


def test_duplicating_twice_does_not_collide(client: Client, staff: None, course: Course) -> None:
    for _ in range(2):
        client.post(
            reverse("admin:courses_course_changelist"),
            {"action": "duplicate_course", "_selected_action": [str(course.pk)], "index": "0"},
            follow=True,
        )

    assert Course.objects.filter(slug__startswith="kat-b-kopia").count() == 2
    assert Course.objects.filter(slug="kat-b-kopia-2").exists()


def test_duplicate_leaves_the_intakes_behind(client: Client, staff: None, course: Course) -> None:
    """Copied start dates would advertise a run nobody scheduled."""
    CourseIntake.objects.create(
        course=course, start_date="2026-09-14", mode=CourseIntake.Mode.STATIONARY
    )

    client.post(
        reverse("admin:courses_course_changelist"),
        {"action": "duplicate_course", "_selected_action": [str(course.pk)], "index": "0"},
        follow=True,
    )

    assert Course.objects.get(slug="kat-b-kopia").intakes.count() == 0
    assert course.intakes.count() == 1


def test_slug_is_prepopulated_only_for_a_new_course(course: Course) -> None:
    """Changing a live slug breaks the redirect table in tech.md section 4.8."""
    admin = site._registry[Course]
    request = None

    # modeltranslation rewrites the dependency to the default language field.
    assert admin.get_prepopulated_fields(request) == {"slug": ("title_pl",)}
    assert admin.get_prepopulated_fields(request, course) == {}


def test_translated_fields_are_editable(client: Client, staff: None, course: Course) -> None:
    """modeltranslation must expose the ru and uk columns, tech.md section 4.2."""
    body = client.get(reverse("admin:courses_course_change", args=[course.pk])).content.decode()

    for name in ("title_pl", "title_ru", "title_uk"):
        assert f'name="{name}"' in body
