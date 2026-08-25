"""Database queries for the courses slice.

Every query lives here, and anything that crosses a relation prefetches it. The
detail page must not grow a query per intake or per vehicle.
"""

from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.courses.models import Course, CourseIntake, PriceItem
from apps.people.models import Vehicle

UPCOMING_ON_DETAIL = 3


def active_courses(kind: str | None = None) -> QuerySet[Course]:
    courses = Course.objects.filter(is_active=True)
    if kind:
        courses = courses.filter(kind=kind)
    return courses.order_by("kind", "order", "id")


def _upcoming_intakes() -> QuerySet[CourseIntake]:
    """Starts still ahead of us, soonest first.

    select_related on the course because the intake row prints the course title,
    and a closed intake is not something to advertise.
    """
    return (
        CourseIntake.objects.filter(start_date__gte=timezone.localdate())
        .exclude(status=CourseIntake.Status.CLOSED)
        .select_related("course")
        .order_by("start_date")
    )


def course_by_slug(slug: str, kind: str | None = None) -> Course:
    """One active course with its intakes and vehicles already loaded.

    kind is passed by the url patterns, so a professional course is not also
    reachable under /kursy/. Two urls for one page is duplicate content.
    """
    courses = active_courses(kind).prefetch_related(
        Prefetch("intakes", queryset=_upcoming_intakes(), to_attr="upcoming"),
        Prefetch(
            "vehicles",
            queryset=Vehicle.objects.filter(is_active=True).order_by("order", "id"),
            to_attr="active_vehicles",
        ),
    )
    return get_object_or_404(courses, slug=slug)


def prefetched_intakes(course: Course, limit: int = UPCOMING_ON_DETAIL) -> list[CourseIntake]:
    """The intakes course_by_slug already loaded.

    Read through here rather than off the attribute directly: to_attr is
    invisible to the type checker, and touching course.intakes instead would
    quietly issue another query.
    """
    return list(getattr(course, "upcoming", []))[:limit]


def prefetched_vehicles(course: Course) -> list[Vehicle]:
    return list(getattr(course, "active_vehicles", []))


def priced_courses() -> QuerySet[Course]:
    """Active courses that have a price to show."""
    return active_courses().exclude(price_gross=None)


def unpriced_courses() -> QuerySet[Course]:
    """Active courses whose price is still agreed case by case."""
    return active_courses().filter(price_gross=None)


def active_price_items() -> QuerySet[PriceItem]:
    return PriceItem.objects.filter(is_active=True).order_by("group", "order", "id")
