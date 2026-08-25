"""Courses admin, DEV.md S1.1. This is where the owner edits the offer."""

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.text import slugify
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from apps.courses.models import Course, CourseIntake
from apps.people.models import Vehicle

COPY_SUFFIX = "kopia"


class CourseIntakeInline(TranslationTabularInline):
    model = CourseIntake
    extra = 0
    fields = ("start_date", "end_date", "mode", "language", "status", "seats_total", "seats_taken")
    ordering = ("start_date",)


class VehicleInline(TranslationTabularInline):
    model = Vehicle
    extra = 0
    fields = ("make", "model", "year", "gearbox", "is_exam_spec", "order", "is_active")
    ordering = ("order", "id")


def _free_slug(base: str) -> str:
    candidate = slugify(f"{base}-{COPY_SUFFIX}")
    suffix = 2
    while Course.objects.filter(slug=candidate).exists():
        candidate = slugify(f"{base}-{COPY_SUFFIX}-{suffix}")
        suffix += 1
    return candidate


@admin.register(Course)
class CourseAdmin(TranslationAdmin):
    list_display = ("title", "kind", "code", "price_gross", "is_active", "order")
    list_filter = ("kind", "is_active")
    search_fields = ("title", "slug", "code", "lead", "body")
    list_editable = ("is_active", "order")
    ordering = ("kind", "order", "id")
    inlines = (CourseIntakeInline, VehicleInline)
    actions = ("duplicate_course",)
    # Declared as an attribute so modeltranslation can rewrite the dependency
    # to the default language field. Overriding the getter instead would hand
    # the admin a plain "title", which is not on the translated form.
    prepopulated_fields = {"slug": ("title",)}

    @admin.action(description="Duplikuj kurs razem z pojazdami")
    def duplicate_course(self, request: HttpRequest, queryset: QuerySet[Course]) -> None:
        """Copy a course as an inactive draft.

        Vehicles come along because they describe the fleet for that category.
        Intakes do not: their dates belong to the run that is already scheduled,
        and copying them would put invented starts in front of a visitor.
        """
        for course in queryset:
            vehicles = list(course.vehicles.all())
            slug = _free_slug(course.slug)

            copy = course
            copy.pk = None
            copy.id = None
            copy._state.adding = True
            copy.slug = slug
            # A draft, so an unfinished copy cannot reach a public page.
            copy.is_active = False
            copy.save()

            for vehicle in vehicles:
                vehicle.pk = None
                vehicle.id = None
                vehicle._state.adding = True
                vehicle.course = copy
                vehicle.save()

            self.message_user(
                request,
                f"Utworzono kopię: {slug}. Kurs jest nieaktywny, intake'ów nie skopiowano.",
                messages.SUCCESS,
            )

    def get_prepopulated_fields(self, request: HttpRequest, obj: Any = None) -> dict[str, Any]:
        # Only for a new course: changing the slug of a live one breaks the
        # redirects frozen in tech.md section 4.8.
        return {} if obj else super().get_prepopulated_fields(request, obj)
