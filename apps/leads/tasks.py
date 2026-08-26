"""Lead notifications, tech.md section 6 and DEV.md S3.2.

Both tasks follow the same shape: check the idempotency key, build the message,
hand it to the mail client, and only then write the stamp. Written in that
order on purpose. A lead whose mail never went out keeps status=NEW and an
empty stamp, so the owner still finds it in the admin instead of losing it to a
task that marked work it never did.
"""

import logging
from typing import Any

from celery import Task, shared_task
from django.utils import timezone

from apps.core.clients import get_mail_client
from apps.core.contracts import validate_payload
from apps.core.tasks import BaseTask
from apps.leads import emails
from apps.leads.models import Lead

logger = logging.getLogger(__name__)

NOTIFY_OWNER = "leads.tasks.notify_owner"
SEND_CONFIRMATION = "leads.tasks.send_confirmation"


def _result(
    lead_id: int, *, sent: bool, reason: str = "", message_id: str | None = None
) -> dict[str, Any]:
    return {"lead_id": lead_id, "sent": sent, "reason": reason, "message_id": message_id}


def _stamp(lead_id: int, field: str) -> None:
    """Write the idempotency key, and only it.

    An update() rather than a save(): the task must not overwrite a status the
    owner changed in the admin while the mail was on its way.
    """
    Lead.objects.filter(pk=lead_id).update(**{field: timezone.now()})


@shared_task(bind=True, base=BaseTask)
def notify_owner(self: Task, lead_id: int) -> dict[str, Any]:
    """Mail the owner about a new lead.

    Idempotent on Lead.notified_at, tech.md section 6: a second run over the
    same lead finds the stamp and sends nothing.
    """
    validate_payload(NOTIFY_OWNER, {"lead_id": lead_id})

    lead = Lead.objects.select_related("course", "intake").get(pk=lead_id)
    if lead.notified_at is not None:
        return _result(lead_id, sent=False, reason="already notified")
    if lead.status == Lead.Status.SPAM:
        # The honeypot path never queues this task, DEV.md S3.1. A spam lead
        # replayed by hand must not reach the owner's inbox either.
        return _result(lead_id, sent=False, reason="spam")

    message = emails.owner_message(lead)
    if not message.to:
        # Nobody to tell is a misconfiguration, not an outage: retrying it five
        # times changes nothing, and the lead is safe in the admin regardless.
        logger.warning("lead %s not notified: SiteSettings.lead_notify_emails is empty", lead_id)
        return _result(lead_id, sent=False, reason="no recipients")

    message_id = get_mail_client().send(
        to=message.to,
        subject=message.subject,
        body_html=message.body_html,
        body_text=message.body_text,
    )
    _stamp(lead_id, "notified_at")
    return _result(lead_id, sent=True, message_id=message_id)


@shared_task(bind=True, base=BaseTask)
def send_confirmation(self: Task, lead_id: int) -> dict[str, Any]:
    """Answer the applicant in their own language.

    Idempotent on Lead.confirmed_at, tech.md section 6.
    """
    validate_payload(SEND_CONFIRMATION, {"lead_id": lead_id})

    lead = Lead.objects.select_related("course", "intake").get(pk=lead_id)
    if lead.confirmed_at is not None:
        return _result(lead_id, sent=False, reason="already confirmed")
    if lead.status == Lead.Status.SPAM:
        # A honeypot submission carries someone else's address as often as not.
        return _result(lead_id, sent=False, reason="spam")
    if not lead.email:
        # The email field is optional, DEV.md S3.1, and the form only queues
        # this task when it is filled. Guarded here as well, since a task that
        # sends to an empty address would die on the client's validation.
        return _result(lead_id, sent=False, reason="no email")

    message = emails.confirmation_message(lead)
    message_id = get_mail_client().send(
        to=message.to,
        subject=message.subject,
        body_html=message.body_html,
        body_text=message.body_text,
    )
    _stamp(lead_id, "confirmed_at")
    return _result(lead_id, sent=True, message_id=message_id)
