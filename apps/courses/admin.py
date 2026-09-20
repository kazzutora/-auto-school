"""Courses admin, DEV.md S1.1. This is where the owner edits the offer."""

from typing import Any

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.text import slugify
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from apps.courses.models import Course, CourseIntake, PriceItem
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
    list_display = ("title", "kind", "code", "price_gross", "intake_count", "is_active", "order")
    list_filter = ("kind", "is_active")
    search_fields = ("title", "slug", "code", "lead", "body")
    list_editable = ("is_active", "order")
    ordering = ("kind", "order", "id")
    inlines = (CourseIntakeInline, VehicleInline)
    actions = ("duplicate_course", "delete_with_intakes")
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

    @admin.display(description="Nabory", ordering="intake_total")
    def intake_count(self, obj: Course) -> int:
        """How many intakes stand between this course and the delete button.

        CourseIntake.course is PROTECT, so a course with dates on it refuses to
        be deleted and django says so in a sentence about foreign keys. Showing
        the number here means the refusal is no longer a surprise.
        """
        # Annotated by get_queryset below; a Course fetched any other way has
        # no such attribute, and the admin is not the only caller of this model.
        return int(getattr(obj, "intake_total", 0))

    def get_queryset(self, request: HttpRequest) -> QuerySet[Course]:
        return super().get_queryset(request).annotate(intake_total=Count("intakes"))

    @admin.action(description="Usuń kurs razem z naborami")
    def delete_with_intakes(self, request: HttpRequest, queryset: QuerySet[Course]) -> None:
        """Delete a course and the intakes that hold it back.

        The plain delete cannot do this and should not: PROTECT is what stops a
        course disappearing under a scheduled group by accident. This is the
        same removal asked for out loud, in one transaction so a half deleted
        course is not a state the database can end up in.
        """
        removed = 0
        for course in queryset:
            with transaction.atomic():
                intakes = course.intakes.count()
                course.intakes.all().delete()
                title = str(course)
                course.delete()
                removed += 1
                self.message_user(
                    request,
                    f"Usunięto kurs {title} wraz z naborami: {intakes}.",
                    messages.WARNING,
                )
        if not removed:
            self.message_user(request, "Nie wybrano żadnego kursu.", messages.INFO)

    def get_prepopulated_fields(self, request: HttpRequest, obj: Any = None) -> dict[str, Any]:
        # Only for a new course: changing the slug of a live one breaks the
        # redirects frozen in tech.md section 4.8.
        return {} if obj else super().get_prepopulated_fields(request, obj)


@admin.register(CourseIntake)
class CourseIntakeAdmin(TranslationAdmin):
    """Intakes on their own, not only as an inline under a course.

    The inline edits the dates of one course; this is the page for the question
    the owner actually asks — what runs in March, what is still open, what can
    go. It is also the only way to clear the intakes that block a course from
    being deleted, short of the action on the course list.
    """

    list_display = ("course", "start_date", "end_date", "mode", "language", "status", "seats")
    list_filter = ("status", "mode", "language", "course")
    search_fields = ("course__title", "note")
    ordering = ("-start_date",)
    date_hierarchy = "start_date"
    autocomplete_fields = ("course",)

    @admin.display(description="Miejsca")
    def seats(self, obj: CourseIntake) -> str:
        if obj.seats_total is None:
            return f"{obj.seats_taken} / —"
        return f"{obj.seats_taken} / {obj.seats_total}"


@admin.register(PriceItem)
class PriceItemAdmin(TranslationAdmin):
    """The rows of the price list that belong to no course."""

    list_display = (
        "title",
        "group",
        "price_gross",
        "unit",
        "featured",
        "is_active",
        "order",
    )
    list_filter = ("is_active", "featured", "group")
    list_editable = ("featured", "is_active", "order")
    search_fields = ("title", "note", "group")
    ordering = ("group", "order", "id")
