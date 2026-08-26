"""Reads for the people slice, same shape as the reference slice in apps/gallery.

The about page renders every instructor and the whole fleet at once, so the
counts here are small and the queries are fixed: two, whatever the numbers grow
to.
"""

from typing import Any

from django.db.models import QuerySet

from apps.people.models import Instructor, Vehicle


def active_instructors() -> QuerySet[Instructor]:
    """Instructors the owner still employs, with the categories they teach."""
    return (
        Instructor.objects.filter(is_active=True)
        .prefetch_related("categories")
        .order_by("order", "id")
    )


def vehicles_by_course() -> list[dict[str, Any]]:
    """The fleet grouped by licence category, DEV.md S5.

    A car whose category is switched off is left out: that category is missing
    from the offer, the price list and the schedule, so a fleet card for it
    would promise training nobody can book.
    """
    vehicles = (
        Vehicle.objects.filter(is_active=True, course__is_active=True)
        .select_related("course")
        .order_by("course__order", "course__id", "order", "id")
    )

    groups: dict[int, dict[str, Any]] = {}
    for vehicle in vehicles:
        group = groups.setdefault(vehicle.course_id, {"course": vehicle.course, "vehicles": []})
        group["vehicles"].append(vehicle)
    return list(groups.values())
