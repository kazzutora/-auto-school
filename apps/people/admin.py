"""People admin, DEV.md S5. This is where the owner fills in the team and the fleet."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString
from modeltranslation.admin import TranslationAdmin

from apps.people.models import Instructor, Vehicle

THUMBNAIL = (
    '<img src="{}" alt="{}" style="height:56px;width:56px;object-fit:cover;border-radius:6px">'
)


def _thumbnail(photo: object, alt: str) -> SafeString | str:
    """A picture in the changelist, so the owner sees what a row carries.

    The original file is used rather than a rendition: the admin is behind a
    login and a handful of rows costs nothing, while a rendition here would
    have the admin generating files on a page load.
    """
    if not photo:
        return "-"
    return format_html(THUMBNAIL, photo.url, alt)  # type: ignore[attr-defined]


@admin.register(Instructor)
class InstructorAdmin(TranslationAdmin):
    list_display = ("preview", "full_name", "role", "since_year", "order", "is_active")
    list_display_links = ("preview", "full_name")
    list_filter = ("is_active", "categories")
    search_fields = ("full_name", "role", "bio")
    list_editable = ("order", "is_active")
    filter_horizontal = ("categories",)
    ordering = ("order", "id")

    @admin.display(description="Zdjęcie")
    def preview(self, obj: Instructor) -> SafeString | str:
        return _thumbnail(obj.photo, obj.full_name)


@admin.register(Vehicle)
class VehicleAdmin(TranslationAdmin):
    list_display = (
        "preview",
        "make",
        "model",
        "course",
        "year",
        "gearbox",
        "is_exam_spec",
        "order",
        "is_active",
    )
    list_display_links = ("preview", "make", "model")
    list_filter = ("course", "gearbox", "is_exam_spec", "is_active")
    search_fields = ("make", "model", "note")
    list_editable = ("order", "is_active")
    ordering = ("course", "order", "id")

    @admin.display(description="Zdjęcie")
    def preview(self, obj: Vehicle) -> SafeString | str:
        return _thumbnail(obj.photo, f"{obj.make} {obj.model}")
