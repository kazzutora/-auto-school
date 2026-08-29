"""Lead admin, DEV.md S3.1.

The screen the owner actually works from: what came in, who has been called
back, and a way to get the week out into a spreadsheet.
"""

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from apps.leads.models import Lead
from apps.leads.views import leads_csv


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "first_name", "last_name", "phone", "course", "status")
    list_filter = ("status", "course", "preferred_language", "consent_marketing")
    search_fields = ("first_name", "last_name", "phone", "email")
    date_hierarchy = "created_at"
    list_select_related = ("course", "intake")
    autocomplete_fields = ()
    actions = ("mark_contacted", "export_csv")

    # Everything below arrives with the request or from a task. Editing any of
    # it in the admin would be editing the record of what happened.
    readonly_fields = (
        "created_at",
        "updated_at",
        "ip_hash",
        "user_agent",
        "source_path",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "notified_at",
        "confirmed_at",
    )
    fieldsets = (
        (None, {"fields": ("status", "first_name", "last_name", "phone", "email")}),
        (_("Kurs"), {"fields": ("course", "intake", "preferred_language", "message")}),
        (_("Zgody"), {"fields": ("consent_rodo", "consent_marketing")}),
        (
            _("Skąd przyszło"),
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "source_path",
                    "utm_source",
                    "utm_medium",
                    "utm_campaign",
                    "ip_hash",
                    "user_agent",
                    "notified_at",
                    "confirmed_at",
                ),
            },
        ),
    )

    @admin.action(description=_("Oznacz jako skontaktowane"))
    def mark_contacted(self, request: HttpRequest, queryset: QuerySet[Lead]) -> None:
        """The one status change that happens in bulk, after a round of calls."""
        changed = queryset.exclude(status=Lead.Status.CONTACTED).update(
            status=Lead.Status.CONTACTED
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d zgłoszenie oznaczone jako skontaktowane.",
                "%(count)d zgłoszeń oznaczonych jako skontaktowane.",
                changed,
            )
            % {"count": changed},
            messages.SUCCESS,
        )

    @admin.action(description=_("Eksportuj zaznaczone do CSV"))
    def export_csv(self, request: HttpRequest, queryset: QuerySet[Lead]) -> HttpResponse:
        return leads_csv(queryset)

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Leads arrive through the form. One typed in here is a lead nobody
        consented to being contacted about."""
        return False
