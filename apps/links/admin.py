"""Links admin, DEV.md S7.1. This is where the owner keeps the list honest."""

from django.contrib import admin
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString
from modeltranslation.admin import TranslationAdmin

from apps.links.models import HTTP_ERROR, UsefulLink

BROKEN = '<span style="color:#B3382B;font-weight:700">{}</span>'
OK = '<span style="color:#1E7A56">{}</span>'


class BrokenFilter(admin.SimpleListFilter):
    """Straight to the rows the night check could not reach."""

    title = "stan ostatniego sprawdzenia"
    parameter_name = "broken"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [("yes", "Nie działa"), ("no", "Działa"), ("never", "Nie sprawdzono")]

    def queryset(
        self, request: HttpRequest, queryset: QuerySet[UsefulLink]
    ) -> QuerySet[UsefulLink]:
        failing = Q(last_status__gte=HTTP_ERROR) | ~Q(last_error="")
        if self.value() == "yes":
            return queryset.filter(failing)
        if self.value() == "no":
            return queryset.filter(last_checked_at__isnull=False).exclude(failing)
        if self.value() == "never":
            return queryset.filter(last_checked_at__isnull=True)
        return queryset


@admin.register(UsefulLink)
class UsefulLinkAdmin(TranslationAdmin):
    list_display = ("title", "group", "state", "last_checked_at", "order", "is_active")
    list_filter = (BrokenFilter, "group", "is_active")
    search_fields = ("title", "description", "url")
    list_editable = ("order", "is_active")
    ordering = ("group", "order", "id")

    @admin.display(description="Ostatnie sprawdzenie")
    def state(self, obj: UsefulLink) -> SafeString | str:
        """What the night check found, DEV.md S7.1.

        Flagged here and nowhere else: the page keeps showing a broken link
        until the owner switches is_active off, because a redirect or an hour
        of downtime is not a reason to empty a section behind their back.
        """
        if obj.last_checked_at is None:
            return "-"
        if obj.is_broken:
            return format_html(BROKEN, obj.last_error or f"HTTP {obj.last_status}")
        return format_html(OK, f"HTTP {obj.last_status}")
