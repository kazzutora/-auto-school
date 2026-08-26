"""Message bodies for the two lead notifications, DEV.md S3.2.

Copy lives in templates/leads/email/ and nowhere else, so the wording can be
edited without touching python. This module only picks the template, fills the
context and hands the pieces to the caller: sending is the task's job.
"""

from dataclasses import dataclass

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse

from apps.core.models import SiteSettings
from apps.leads.models import Lead

# One template per language, DEV.md S3.2. Anything else falls back to polish.
SUPPORTED_LANGUAGES = tuple(code for code, _label in settings.LANGUAGES)
DEFAULT_LANGUAGE = settings.LANGUAGE_CODE
LANGUAGE_NAMES = dict(settings.LANGUAGES)


@dataclass(frozen=True)
class Message:
    """Exactly the arguments MailClient.send takes, tech.md section 6."""

    to: list[str]
    subject: str
    body_html: str
    body_text: str


def email_language(code: str) -> str:
    """The language to write in. An unknown code means polish, DEV.md S3.2."""
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def absolute_url(path: str) -> str:
    """A link that survives leaving the site.

    A task has no request to build the host from, so it comes from the sites
    framework. The scheme is fixed: production is https only, tech.md section 19.
    """
    return f"https://{Site.objects.get_current().domain.rstrip('/')}{path}"


def admin_lead_url(lead: Lead) -> str:
    """Where the owner opens this lead."""
    try:
        path = reverse("admin:leads_lead_change", args=[lead.pk])
    except NoReverseMatch:
        # LeadAdmin is registered by DEV.md S3.1. Until it lands the change
        # view has no named route, and the owner still needs a working link:
        # the admin lays this path out for every registered model.
        path = f"{reverse('admin:index')}leads/lead/{lead.pk}/change/"
    return absolute_url(path)


def _subject(template: str, context: dict[str, object]) -> str:
    """A subject is one line, whatever whitespace the template file carries."""
    return " ".join(render_to_string(template, context).split())


def owner_message(lead: Lead) -> Message:
    """What lands in the owner's inbox. Polish: the office reads polish."""
    site = SiteSettings.get_solo()
    context: dict[str, object] = {
        "lead": lead,
        "site": site,
        "admin_url": admin_lead_url(lead),
        "language_name": LANGUAGE_NAMES.get(lead.preferred_language, lead.preferred_language),
    }
    return Message(
        to=site.notify_emails,
        subject=_subject("leads/email/notify_owner.subject.txt", context),
        body_html=render_to_string("leads/email/notify_owner.html", context),
        body_text=render_to_string("leads/email/notify_owner.txt", context),
    )


def confirmation_message(lead: Lead) -> Message:
    """The autoreply, written in the language the applicant chose."""
    language = email_language(lead.preferred_language)
    context: dict[str, object] = {
        "lead": lead,
        "site": SiteSettings.get_solo(),
        "language": language,
    }
    return Message(
        to=[lead.email],
        subject=_subject(f"leads/email/confirmation_{language}.subject.txt", context),
        body_html=render_to_string(f"leads/email/confirmation_{language}.html", context),
        body_text=render_to_string(f"leads/email/confirmation_{language}.txt", context),
    )
