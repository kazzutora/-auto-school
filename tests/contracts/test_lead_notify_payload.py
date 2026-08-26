"""Both lead tasks against tech.md section 6, and against the mail seam.

Two contracts meet here. The payload the caller hands the task, and the message
the task hands the mail client: the fake validates the second one and refuses
junk, tech.md section 9.
"""

from typing import Any

import pytest
from celery.exceptions import Retry

from apps.core.clients.mail import validate_mail
from apps.core.contracts import ContractError, validate_payload
from apps.leads import emails
from apps.leads.tasks import NOTIFY_OWNER, SEND_CONFIRMATION, notify_owner, send_confirmation
from config.celery import app
from tests.factories import LeadFactory, notify_site

TASKS = {NOTIFY_OWNER: notify_owner, SEND_CONFIRMATION: send_confirmation}


def cause(error: BaseException) -> BaseException:
    """What actually went wrong inside the task.

    tech.md section 6 puts every task under autoretry_for=(Exception,), so
    celery answers a failed eager run with a Retry that carries the original
    exception. The slice is judged on that original, not on the wrapper.
    """
    return error.exc if isinstance(error, Retry) and error.exc else error


def test_tasks_are_registered_under_the_contract_names() -> None:
    assert NOTIFY_OWNER == "leads.tasks.notify_owner"
    assert SEND_CONFIRMATION == "leads.tasks.send_confirmation"
    for name in TASKS:
        assert name in app.tasks


@pytest.mark.parametrize("name", TASKS)
def test_contract_payload_validates(name: str) -> None:
    validate_payload(name, {"lead_id": 7})


@pytest.mark.parametrize("name", TASKS)
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"lead_id": "7"},
        {"lead_id": 7, "language": "ru"},
        {"lead": 7},
    ],
)
def test_junk_payload_is_rejected(name: str, payload: dict[str, Any]) -> None:
    with pytest.raises(ContractError):
        validate_payload(name, payload)


@pytest.mark.django_db
@pytest.mark.parametrize("task", TASKS.values())
def test_the_task_itself_refuses_a_bad_payload(task: Any) -> None:
    """The seam has to bite at call time, not only in a unit test."""
    notify_site()
    lead = LeadFactory()

    with pytest.raises(BaseException) as error:  # noqa: B017, PT011
        task.apply(kwargs={"lead_id": str(lead.pk)}).get()

    assert isinstance(cause(error.value), ContractError)


@pytest.mark.django_db
def test_owner_message_passes_the_mail_contract() -> None:
    notify_site()
    message = emails.owner_message(LeadFactory(message="Proszę o kontakt po 16."))

    validate_mail(
        to=message.to,
        subject=message.subject,
        body_html=message.body_html,
        body_text=message.body_text,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["pl", "ru", "uk"])
def test_confirmation_message_passes_the_mail_contract(language: str) -> None:
    notify_site()
    message = emails.confirmation_message(LeadFactory(preferred_language=language))

    validate_mail(
        to=message.to,
        subject=message.subject,
        body_html=message.body_html,
        body_text=message.body_text,
    )


@pytest.mark.django_db
def test_a_subject_is_a_single_line() -> None:
    """A newline in a subject header is how header injection starts."""
    notify_site()
    lead = LeadFactory(first_name="Anna\nBcc: kto@example.com")

    for message in (emails.owner_message(lead), emails.confirmation_message(lead)):
        assert "\n" not in message.subject
        assert "\r" not in message.subject
