"""Core admin, tech.md section 4.1."""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from apps.core.models import OpeningHours, Page, SiteSettings


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
