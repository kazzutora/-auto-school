"""DEV.md S3.2 acceptance criteria: content, language and the error path."""

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from celery.exceptions import Retry

from apps.core.clients import ClientServerError, ClientTimeout, FakeMailClient
from apps.core.tasks import BaseTask
from apps.courses.models import Course, CourseIntake
from apps.leads import emails
from apps.leads.models import Lead
from apps.leads.tasks import notify_owner, send_confirmation
from tests.factories import LeadFactory, notify_site

pytestmark = pytest.mark.django_db

# One retry past what the policy allows, tech.md section 6: max_retries is five.
PAST_THE_LIMIT = BaseTask.max_retries + 1


class CountingMail(FakeMailClient):
    """A fake that also says how many times the task reached for it."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.attempts = 0

    def send(self, **kwargs: Any) -> str:
        self.attempts += 1
        return super().send(**kwargs)


@pytest.fixture
def failing_mail(monkeypatch: pytest.MonkeyPatch) -> Any:
    def install(fail_with: int | str | None) -> CountingMail:
        client = CountingMail(fail_with=fail_with)
        monkeypatch.setattr("apps.leads.tasks.get_mail_client", lambda: client)
        return client

    return install


def sent(outbox: Path) -> list[str]:
    return [path.read_text(encoding="utf-8") for path in sorted(outbox.glob("*.json"))]


def only_message(outbox: Path) -> str:
    messages = sent(outbox)
    assert len(messages) == 1
    return messages[0]


# --------------------------------------------------------------------------
# what the owner gets


def test_the_owner_mail_carries_the_lead() -> None:
    notify_site("biuro@example.com, adam@example.com")
    course = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )
    lead = LeadFactory(
        first_name="Marek",
        last_name="Nowak",
        phone="+48605065795",
        course=course,
        message="Proszę o kontakt po 16.",
    )

    message = emails.owner_message(lead)

    assert message.to == ["biuro@example.com", "adam@example.com"]
    for body in (message.body_html, message.body_text):
        assert "Marek" in body
        assert "+48605065795" in body
        assert "Kategoria B" in body
        assert "Proszę o kontakt po 16." in body
        assert f"/admin/leads/lead/{lead.pk}/change/" in body


def test_the_owner_mail_names_the_intake() -> None:
    notify_site()
    course = Course.objects.create(kind=Course.Kind.LICENSE, slug="kat-c", title="Kategoria C")
    intake = CourseIntake.objects.create(
        course=course,
        start_date=date(2026, 9, 14),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.OPEN,
    )
    lead = LeadFactory(course=course, intake=intake)

    body = emails.owner_message(lead).body_text

    assert "14.09.2026" in body


def test_the_admin_link_is_absolute() -> None:
    """A relative path in an email client is not a link at all."""
    notify_site()
    lead = LeadFactory()

    assert emails.admin_lead_url(lead).startswith("https://")


def test_an_empty_notify_list_is_not_an_outage(outbox: Path) -> None:
    """A misconfigured SiteSettings must not burn five retries on nothing."""
    notify_site("")
    lead = LeadFactory()

    result = notify_owner.apply(kwargs={"lead_id": lead.pk}).get()

    assert result["sent"] is False
    assert result["reason"] == "no recipients"
    assert sent(outbox) == []
    lead.refresh_from_db()
    assert lead.notified_at is None
    assert lead.status == Lead.Status.NEW


# --------------------------------------------------------------------------
# what the applicant gets


@pytest.mark.parametrize(
    ("language", "greeting"),
    [("pl", "Dzień dobry"), ("ru", "Здравствуйте"), ("uk", "Доброго дня")],
)
def test_the_confirmation_is_written_in_the_chosen_language(
    outbox: Path, language: str, greeting: str
) -> None:
    notify_site()
    lead = LeadFactory(preferred_language=language)

    send_confirmation.apply(kwargs={"lead_id": lead.pk}).get()

    assert greeting in only_message(outbox)


@pytest.mark.parametrize("language", ["en", "de", "", "xx"])
def test_an_unknown_language_falls_back_to_polish(outbox: Path, language: str) -> None:
    notify_site()
    lead = LeadFactory(preferred_language=language)

    send_confirmation.apply(kwargs={"lead_id": lead.pk}).get()

    assert emails.email_language(language) == "pl"
    assert "Dzień dobry" in only_message(outbox)


def test_the_confirmation_goes_to_the_applicant() -> None:
    notify_site()
    lead = LeadFactory(email="marek@example.com")

    assert emails.confirmation_message(lead).to == ["marek@example.com"]


def test_a_lead_without_an_email_gets_no_confirmation(outbox: Path) -> None:
    notify_site()
    lead = LeadFactory(email="")

    result = send_confirmation.apply(kwargs={"lead_id": lead.pk}).get()

    assert result["sent"] is False
    assert result["reason"] == "no email"
    assert sent(outbox) == []
    lead.refresh_from_db()
    assert lead.confirmed_at is None


@pytest.mark.parametrize("task", [notify_owner, send_confirmation])
def test_a_spam_lead_generates_no_mail(outbox: Path, task: Any) -> None:
    """The honeypot lead exists only for the admin, DEV.md S3.1."""
    notify_site()
    lead = LeadFactory(status=Lead.Status.SPAM)

    result = task.apply(kwargs={"lead_id": lead.pk}).get()

    assert result["sent"] is False
    assert result["reason"] == "spam"
    assert sent(outbox) == []


# --------------------------------------------------------------------------
# the error path, tech.md section 9


def cause(error: BaseException) -> BaseException:
    """What actually went wrong inside the task.

    A task under autoretry_for=(Exception,) answers a failed eager run with a
    Retry carrying the original exception. The slice is judged on that original.
    """
    return error.exc if isinstance(error, Retry) and error.exc else error


@pytest.mark.parametrize("task", [notify_owner, send_confirmation])
@pytest.mark.parametrize(
    ("fail_with", "error"), [(500, ClientServerError), ("timeout", ClientTimeout)]
)
def test_a_failing_mail_client_is_retried_and_the_lead_survives(
    outbox: Path, failing_mail: Any, task: Any, fail_with: int | str, error: type[Exception]
) -> None:
    notify_site()
    lead = LeadFactory()
    client = failing_mail(fail_with)

    with pytest.raises(BaseException) as raised:  # noqa: B017, PT011
        task.apply(kwargs={"lead_id": lead.pk}).get()

    # The task asked for another attempt instead of swallowing the outage.
    assert isinstance(cause(raised.value), error)
    assert client.attempts == 1
    assert sent(outbox) == []
    lead.refresh_from_db()
    # The lead stays in the admin as unfinished work, DEV.md S3.2.
    assert lead.status == Lead.Status.NEW
    assert lead.notified_at is None
    assert lead.confirmed_at is None


@pytest.mark.parametrize("task", [notify_owner, send_confirmation])
def test_the_last_attempt_gives_up_without_stamping(failing_mail: Any, task: Any) -> None:
    """Out of retries the original error surfaces, and the stamp stays empty.

    Entering the task with the retry count already spent is how the worker
    reaches the last attempt.
    """
    notify_site()
    lead = LeadFactory()
    client = failing_mail(500)

    with pytest.raises(ClientServerError):
        task.apply(kwargs={"lead_id": lead.pk}, retries=PAST_THE_LIMIT).get()

    assert client.attempts == 1
    lead.refresh_from_db()
    assert lead.notified_at is None
    assert lead.confirmed_at is None


def test_the_attempt_after_a_failure_sends_exactly_one_mail(
    outbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead attempt leaves no trace, so the retry is not a second mail."""
    notify_site()
    lead = LeadFactory()
    down = FakeMailClient(fail_with="timeout")
    monkeypatch.setattr("apps.leads.tasks.get_mail_client", lambda: down)

    with pytest.raises(BaseException):  # noqa: B017, PT011
        notify_owner.apply(kwargs={"lead_id": lead.pk}).get()

    assert sent(outbox) == []
    monkeypatch.setattr("apps.leads.tasks.get_mail_client", FakeMailClient)

    result = notify_owner.apply(kwargs={"lead_id": lead.pk}).get()

    assert result["sent"] is True
    assert len(sent(outbox)) == 1
    lead.refresh_from_db()
    assert lead.notified_at is not None


def test_a_missing_lead_does_not_pass_silently() -> None:
    """A deleted lead is a bug in the caller, not a no-op."""
    notify_site()

    with pytest.raises(BaseException) as raised:  # noqa: B017, PT011
        notify_owner.apply(kwargs={"lead_id": 10_000}).get()

    assert isinstance(cause(raised.value), Lead.DoesNotExist)
