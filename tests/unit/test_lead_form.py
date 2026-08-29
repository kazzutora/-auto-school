"""The enrolment form, DEV.md S3.1 acceptance criteria.

The old site had no form at all, so these are the assertions that say the main
breakage is actually fixed: a lead arrives, the owner hears about it, consent is
not optional, and neither a bot nor a flood costs the school anything.
"""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.courses.models import Course, CourseIntake
from apps.leads.models import Lead
from apps.leads.views import RATE

pytestmark = pytest.mark.django_db

SUBMIT = "/zapisz-sie/submit/"

VALID = {
    "first_name": "Marek",
    "last_name": "Nowak",
    "phone": "605 065 795",
    "email": "marek@example.com",
    "message": "Proszę o kontakt po 16.",
    "consent_rodo": "on",
    "website": "",
}


@pytest.fixture
def queued(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """What the view put on the queue, without running any of it.

    Celery is eager in the suite, so a real delay() would send the mail and
    prove something S3.2 already covers. What S3.1 owns is the decision to
    queue.
    """
    calls: list[str] = []

    def record(name: str) -> Any:
        def delay(lead_id: int) -> None:
            calls.append(name)

        return delay

    monkeypatch.setattr("apps.leads.views.notify_owner.delay", record("notify_owner"))
    monkeypatch.setattr("apps.leads.views.send_confirmation.delay", record("send_confirmation"))
    return calls


def post(client: Client, **overrides: Any) -> Any:
    data = {**VALID, **overrides}
    return client.post(SUBMIT, data)


# --------------------------------------------------------------------------
# the happy path


def test_a_valid_submission_creates_one_lead_and_queues_two_tasks(
    client: Client, queued: list[str]
) -> None:
    response = post(client)

    assert response.status_code == 302
    assert response["Location"] == reverse("leads:thanks")
    assert Lead.objects.count() == 1
    assert queued == ["notify_owner", "send_confirmation"]


def test_without_an_email_only_the_owner_is_told(client: Client, queued: list[str]) -> None:
    """The confirmation has nowhere to go, DEV.md S3.1."""
    post(client, email="")

    assert Lead.objects.count() == 1
    assert queued == ["notify_owner"]


def test_the_phone_is_stored_in_one_canonical_form(client: Client, queued: list[str]) -> None:
    post(client, phone="+48 605-065-795")
    assert Lead.objects.get().phone == "+48605065795"


def test_an_unusable_phone_is_refused(client: Client, queued: list[str]) -> None:
    response = post(client, phone="12")

    assert Lead.objects.count() == 0
    assert queued == []
    assert "Podaj polski numer telefonu" in response.content.decode()


def test_htmx_gets_the_confirmation_in_place(client: Client, queued: list[str]) -> None:
    """tech.md section 5: the partial replaces the form, the page does not move."""
    response = client.post(SUBMIT, VALID, headers={"hx-request": "true"})

    assert response.status_code == 200
    body = response.content.decode()
    assert "Zgłoszenie przyjęte" in body
    assert "<form" not in body


# --------------------------------------------------------------------------
# consent


def test_without_consent_no_lead_is_created(client: Client, queued: list[str]) -> None:
    """DEV.md S3.1: the box has to be ticked, and the error lands on it."""
    response = post(client, consent_rodo="")

    assert Lead.objects.count() == 0
    assert queued == []
    assert response.status_code == 200
    assert "Bez tej zgody nie możemy" in response.content.decode()


def test_marketing_consent_stays_optional(client: Client, queued: list[str]) -> None:
    post(client)
    assert Lead.objects.get().consent_marketing is False

    Lead.objects.all().delete()
    post(client, consent_marketing="on", phone="605 065 796")
    assert Lead.objects.get().consent_marketing is True


# --------------------------------------------------------------------------
# the honeypot


def test_a_filled_honeypot_is_spam_and_tells_nobody(client: Client, queued: list[str]) -> None:
    """DEV.md S3.1: the sender sees the same success, the owner hears nothing.

    Saying "we caught you" would only teach the next bot to leave the field
    alone.
    """
    response = post(client, website="http://spam.example")

    assert response.status_code == 302
    assert response["Location"] == reverse("leads:thanks")

    lead = Lead.objects.get()
    assert lead.status == Lead.Status.SPAM
    assert queued == []


def test_the_honeypot_is_not_a_hidden_input(client: Client) -> None:
    """type=hidden is the first thing a scraper skips, so it would never fill
    it and the trap would catch nothing.

    u-trap hides it by clipping instead, which leaves a real field in the form
    for a bot to fill and nothing at all for a person to see.
    """
    form = client.get(reverse("leads:enroll")).content.decode()
    field = form[form.index('name="website"') - 300 : form.index('name="website"') + 300]
    assert 'type="hidden"' not in field
    assert "u-trap" in field
    assert 'tabindex="-1"' in field
    assert 'aria-hidden="true"' in field


# --------------------------------------------------------------------------
# privacy, tech.md section 4.3


def test_the_raw_address_is_never_stored(client: Client, queued: list[str]) -> None:
    address = "203.0.113.9"
    client.post(SUBMIT, VALID, REMOTE_ADDR=address)

    lead = Lead.objects.get()
    assert lead.ip_hash
    assert len(lead.ip_hash) == 64
    # Not in the hash column and not smuggled into any other one either.
    stored = " ".join(str(value) for value in Lead.objects.values().first().values())
    assert address not in stored


# --------------------------------------------------------------------------
# rate limit


def test_the_sixth_submission_from_one_address_is_refused(
    client: Client, queued: list[str]
) -> None:
    """DEV.md S3.1: five an hour. 429 rather than 403 — later, not never."""
    allowed = int(RATE.split("/")[0])

    for number in range(allowed):
        response = client.post(
            SUBMIT, {**VALID, "phone": f"60506579{number}"}, REMOTE_ADDR="198.51.100.7"
        )
        assert response.status_code == 302, number

    refused = client.post(SUBMIT, VALID, REMOTE_ADDR="198.51.100.7")

    assert refused.status_code == 429
    assert Lead.objects.count() == allowed
    assert "Za dużo zgłoszeń" in refused.content.decode()


def test_the_limit_is_per_address(client: Client, queued: list[str]) -> None:
    allowed = int(RATE.split("/")[0])
    for number in range(allowed):
        client.post(SUBMIT, {**VALID, "phone": f"60506579{number}"}, REMOTE_ADDR="198.51.100.7")

    fresh = client.post(SUBMIT, VALID, REMOTE_ADDR="198.51.100.8")
    assert fresh.status_code == 302


# --------------------------------------------------------------------------
# prefill, DEV.md S3.1


def test_the_course_is_prefilled_from_the_query(client: Client) -> None:
    course = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )
    body = client.get(f"{reverse('leads:enroll')}?course={course.pk}").content.decode()
    assert f'value="{course.pk}" selected' in body


def test_an_intake_prefills_its_own_course(client: Client) -> None:
    from datetime import date, timedelta

    course = Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-b", code="B", title="Kategoria B"
    )
    intake = CourseIntake.objects.create(
        course=course,
        start_date=date.today() + timedelta(days=10),
        mode=CourseIntake.Mode.STATIONARY,
        status=CourseIntake.Status.OPEN,
    )

    body = client.get(f"{reverse('leads:enroll')}?intake={intake.pk}").content.decode()
    assert f'value="{course.pk}" selected' in body
    assert f'name="intake" value="{intake.pk}"' in body


def test_a_nonsense_query_prefills_nothing(client: Client) -> None:
    """A stale link is not an error page."""
    assert client.get(f"{reverse('leads:enroll')}?course=nope").status_code == 200
    assert client.get(f"{reverse('leads:enroll')}?intake=99999").status_code == 200


def test_an_inactive_course_cannot_be_chosen(client: Client) -> None:
    Course.objects.create(
        kind=Course.Kind.LICENSE, slug="kat-x", code="X", title="Ukryty", is_active=False
    )
    body = client.get(reverse("leads:enroll")).content.decode()
    assert "Ukryty" not in body


# --------------------------------------------------------------------------
# the routes themselves


def test_the_routes_match_the_url_map() -> None:
    """tech.md section 5."""
    assert reverse("leads:enroll") == "/zapisz-sie/"
    assert reverse("leads:submit") == SUBMIT
    assert reverse("leads:thanks") == "/zapisz-sie/dziekujemy/"


def test_the_thank_you_page_is_not_indexed(client: Client) -> None:
    body = client.get(reverse("leads:thanks")).content.decode()
    assert 'content="noindex,follow"' in body


def test_the_form_page_answers_and_has_one_h1(client: Client) -> None:
    import re

    body = client.get(reverse("leads:enroll")).content.decode()
    assert len(re.findall(r"<h1[ >]", body)) == 1


def test_a_get_on_submit_is_refused(client: Client) -> None:
    assert client.get(SUBMIT).status_code == 405
