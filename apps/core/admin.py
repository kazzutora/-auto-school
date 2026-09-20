"""Core admin, tech.md section 4.1."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from apps.core.models import (
    DownloadFile,
    OpeningHours,
    Page,
    PassRate,
    PassRateScan,
    SiteSettings,
)
from apps.core.services import first_attempt_percent, human_size


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    pass


@admin.register(OpeningHours)
class OpeningHoursAdmin(TranslationAdmin):
    list_display = ("department", "weekday", "opens", "closes", "is_closed")
    list_filter = ("department",)
    ordering = ("department", "weekday")


@admin.register(Page)
class PageAdmin(TranslationAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "body")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(PassRate)
class PassRateAdmin(TranslationAdmin):
    """The owner edits this every year; nothing here should need explaining."""

    list_display = ("year", "students", "passed_1st", "first_attempt", "is_published")
    list_filter = ("is_published",)
    ordering = ("-year",)

    @admin.display(description=_("Za pierwszym razem"))
    def first_attempt(self, obj: PassRate) -> str:
        return f"{first_attempt_percent(obj)} %"


@admin.register(PassRateScan)
class PassRateScanAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "order", "is_published")
    list_filter = ("is_published", "year")
    search_fields = ("title",)
    list_editable = ("order", "is_published")


@admin.register(DownloadFile)
class DownloadFileAdmin(TranslationAdmin):
    list_display = ("title", "readable_size", "order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    # Filled in save() from the file itself, tech.md section 4.1.
    readonly_fields = ("size_bytes",)

    @admin.display(description=_("Rozmiar"))
    def readable_size(self, obj: DownloadFile) -> str:
        return human_size(obj.size_bytes) or "—"
