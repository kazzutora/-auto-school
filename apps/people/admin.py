"""People admin, DEV.md S5. This is where the owner fills in the team and the fleet."""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.people.models import Instructor, Vehicle
from apps.core.admin_site import ThumbnailAdminMixin

@admin.register(Instructor)
class InstructorAdmin(ThumbnailAdminMixin, TranslationAdmin):
    thumbnail_field = "photo"
    list_display = ("thumbnail", "full_name", "role", "since_year", "order", "is_active")
    list_display_links = ("thumbnail", "full_name")
    list_filter = ("is_active", "categories")
    search_fields = ("full_name", "role", "bio")
    list_editable = ("order", "is_active")
    filter_horizontal = ("categories",)
    ordering = ("order", "id")


@admin.register(Vehicle)
class VehicleAdmin(ThumbnailAdminMixin, TranslationAdmin):
    thumbnail_field = "photo"
    list_display = (
        "thumbnail",
        "make",
        "model",
        "course",
        "year",
        "gearbox",
        "is_exam_spec",
        "order",
        "is_active",
    )
    list_display_links = ("thumbnail", "make", "model")
    list_filter = ("course", "gearbox", "is_exam_spec", "is_active")
    search_fields = ("make", "model", "note")
    list_editable = ("order", "is_active")
    ordering = ("course", "order", "id")
