"""Enrolment, DEV.md S3.1 and tech.md section 5.

Three routes and one form. The form is embedded on /kontakt/ and on every
course page too, which is why the partial it renders through is a template of
its own rather than markup inside the page.

Works without javascript. htmx swaps the result in place when it is there;
without it the same POST answers with a redirect to the thank you page, so a
visitor with a blocked script still reaches the school.
"""

import csv
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.core.seo import Label, page_seo
from apps.leads.forms import LeadForm, initial_from_query
from apps.leads.models import Lead
from apps.leads.services import client_ip, hash_ip
from apps.leads.tasks import notify_owner, send_confirmation

# DEV.md S3.1: five submissions an hour from one address.
RATE = "5/h"
TOO_MANY_REQUESTS = 429

ENROL_DESCRIPTION = _(
    "Zapisz się na kurs prawa jazdy w OSK Nawrocki w Wieluniu. "
    "Zostaw numer, oddzwonimy i dobierzemy najbliższy termin."
)
THANKS_DESCRIPTION = _("Zgłoszenie przyjęte. Oddzwonimy w godzinach pracy biura.")


def _is_htmx(request: HttpRequest) -> bool:
    return request.headers.get("HX-Request") == "true"


# BLOCKS.md B3. Numbered because the order genuinely matters here: PKK comes
# from the county office and takes days, so somebody who signs up first and
# discovers that second has lost a week.
ENROLMENT_STEPS = (
    {
        "title": _("Wybierz kategorię"),
        "text": _("Nie wiesz którą? Zadzwoń, dobierzemy pod to, co chcesz prowadzić."),
    },
    {
        "title": _("Wyrób PKK w starostwie"),
        "text": _("Profil Kandydata na Kierowcę wydaje Starostwo Powiatowe w Wieluniu."),
    },
    {
        "title": _("Zapisz się"),
        "text": _("Przez formularz obok albo telefonicznie — potwierdzimy termin grupy."),
    },
    {
        "title": _("Zacznij zajęcia"),
        "text": _("Teoria i jazdy ruszają w terminie, który wybrałeś."),
    },
)


ENROL_TRAIL: list[tuple[Label, str]] = [
    (_("Start"), "/"),
    (_("Zapisz się"), "/zapisz-sie/"),
]


def enroll(request: HttpRequest) -> HttpResponse:
    """The form on a page of its own, tech.md section 5."""
    return render(
        request,
        "leads/enroll.html",
        {
            "seo": page_seo(
                request,
                subject=_("Zapisz się na kurs"),
                description=ENROL_DESCRIPTION,
                breadcrumbs=ENROL_TRAIL,
            ),
            "breadcrumbs": [
                {"title": _("Start"), "url": "/"},
                {"title": _("Zapisz się"), "url": reverse("leads:enroll")},
            ],
            "form": LeadForm(initial=initial_from_query(request.GET)),
            "steps": ENROLMENT_STEPS,
        },
    )


def thanks(request: HttpRequest) -> HttpResponse:
    """Where a submission without javascript lands, tech.md section 5."""
    return render(
        request,
        "leads/thanks.html",
        {
            "seo": page_seo(
                request,
                subject=_("Dziękujemy za zgłoszenie"),
                description=THANKS_DESCRIPTION,
                # A confirmation page has nothing to offer a search engine and
                # everything to lose by being indexed instead of the form.
                robots="noindex,follow",
            ),
        },
    )


@require_POST
@ratelimit(key="ip", rate=RATE, method="POST", block=False)
def submit(request: HttpRequest) -> HttpResponse:
    """Take the form, DEV.md S3.1.

    block=False rather than the decorator's own 403: DEV.md asks for 429, which
    is the status that actually says "later, not never".
    """
    if getattr(request, "limited", False):
        return render(
            request,
            "leads/_form_result.html",
            {"form": LeadForm(request.POST), "rate_limited": True},
            status=TOO_MANY_REQUESTS,
        )

    form = LeadForm(request.POST)
    if not form.is_valid():
        return render(request, "leads/_form_result.html", {"form": form})

    lead = _save(request, form)

    # A trap that told the sender it caught them would just teach the next bot
    # to avoid it, DEV.md S3.1: the page looks exactly the same either way.
    if lead.status != Lead.Status.SPAM:
        notify_owner.delay(lead.pk)
        if lead.email:
            send_confirmation.delay(lead.pk)

    if _is_htmx(request):
        return render(request, "leads/_form_result.html", {"sent": True})
    return redirect("leads:thanks")


def _save(request: HttpRequest, form: LeadForm) -> Lead:
    """Persist the lead with everything the request knows and nothing it should
    not keep.

    The raw address never lands in a column, tech.md section 4.3: what is stored
    is sha256(ip + salt), which still lets the owner see two submissions from
    the same place without holding the place itself.
    """
    lead: Lead = form.save(commit=False)
    lead.status = Lead.Status.SPAM if form.looks_automated else Lead.Status.NEW
    # Whatever language the visitor was reading in, so the confirmation mail
    # answers in the same one, DEV.md S3.2.
    language = getattr(request, "LANGUAGE_CODE", "pl") or "pl"
    lead.preferred_language = language[:2]
    lead.source_path = request.headers.get("Referer", "")[:200] or request.path
    lead.utm_source = request.GET.get("utm_source", "")[:80]
    lead.utm_medium = request.GET.get("utm_medium", "")[:80]
    lead.utm_campaign = request.GET.get("utm_campaign", "")[:80]
    lead.ip_hash = hash_ip(client_ip(request.META), settings.IP_HASH_SALT)
    lead.user_agent = request.headers.get("User-Agent", "")[:300]
    lead.save()
    return lead


# --------------------------------------------------------------------------
# admin export, DEV.md S3.1

CSV_COLUMNS = (
    "created_at",
    "status",
    "first_name",
    "last_name",
    "phone",
    "email",
    "course",
    "intake",
    "preferred_language",
    "message",
    "consent_marketing",
    "source_path",
)


def leads_csv(queryset: Any) -> HttpResponse:
    """The selected leads as a spreadsheet.

    utf-8-sig, not utf-8: excel reads a plain utf-8 csv as latin-1 and turns
    every polish name into mojibake.
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    response.write("﻿")

    writer = csv.writer(response)
    writer.writerow(CSV_COLUMNS)
    for lead in queryset.select_related("course", "intake"):
        writer.writerow(
            [
                lead.created_at.isoformat(),
                lead.status,
                lead.first_name,
                lead.last_name,
                lead.phone,
                lead.email,
                lead.course.title if lead.course else "",
                lead.intake.start_date.isoformat() if lead.intake else "",
                lead.preferred_language,
                lead.message.replace("\n", " "),
                lead.consent_marketing,
                lead.source_path,
            ]
        )
    return response
