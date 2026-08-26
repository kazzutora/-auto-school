"""tech.md section 6: both lead tasks are idempotent on their stamp.

Each task runs twice over the same lead. One message in the outbox, or the task
does not merge, tech.md section 9.
"""

from pathlib import Path

import pytest

from apps.leads.models import Lead
from apps.leads.tasks import notify_owner, send_confirmation
from tests.factories import LeadFactory, notify_site

pytestmark = pytest.mark.django_db

TASKS = {"notified_at": notify_owner, "confirmed_at": send_confirmation}


def messages(outbox: Path) -> list[str]:
    return [path.read_text(encoding="utf-8") for path in sorted(outbox.glob("*.json"))]


@pytest.mark.parametrize(("stamp", "task"), TASKS.items())
def test_the_first_run_sends_and_stamps(outbox: Path, stamp: str, task: object) -> None:
    notify_site()
    lead = LeadFactory()

    result = task.apply(kwargs={"lead_id": lead.pk}).get()  # type: ignore[attr-defined]

    assert result["sent"] is True
    assert result["message_id"]
    assert len(messages(outbox)) == 1
    lead.refresh_from_db()
    assert getattr(lead, stamp) is not None


@pytest.mark.parametrize(("stamp", "task"), TASKS.items())
def test_the_second_run_sends_nothing(outbox: Path, stamp: str, task: object) -> None:
    notify_site()
    lead = LeadFactory()
    task.apply(kwargs={"lead_id": lead.pk}).get()  # type: ignore[attr-defined]
    lead.refresh_from_db()
    stamped_at = getattr(lead, stamp)

    result = task.apply(kwargs={"lead_id": lead.pk}).get()  # type: ignore[attr-defined]

    assert result["sent"] is False
    assert len(messages(outbox)) == 1
    lead.refresh_from_db()
    # The stamp is the moment the mail went out, not the moment of the last run.
    assert getattr(lead, stamp) == stamped_at


def test_the_two_tasks_do_not_shadow_each_other(outbox: Path) -> None:
    """One lead, both notifications: two messages, two stamps, one each."""
    notify_site()
    lead = LeadFactory()

    for task in TASKS.values():
        task.apply(kwargs={"lead_id": lead.pk}).get()
        task.apply(kwargs={"lead_id": lead.pk}).get()

    assert len(messages(outbox)) == 2
    lead.refresh_from_db()
    assert lead.notified_at is not None
    assert lead.confirmed_at is not None


@pytest.mark.parametrize(("stamp", "task"), TASKS.items())
def test_a_stamped_lead_is_left_untouched(outbox: Path, stamp: str, task: object) -> None:
    """A replay must not resurrect a lead the owner has already worked."""
    notify_site()
    lead = LeadFactory(status=Lead.Status.CONTACTED)
    task.apply(kwargs={"lead_id": lead.pk}).get()  # type: ignore[attr-defined]
    Lead.objects.filter(pk=lead.pk).update(status=Lead.Status.ENROLLED)

    task.apply(kwargs={"lead_id": lead.pk}).get()  # type: ignore[attr-defined]

    lead.refresh_from_db()
    assert lead.status == Lead.Status.ENROLLED
    assert len(messages(outbox)) == 1
