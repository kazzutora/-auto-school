"""Links admin, DEV.md S7.1: a broken link is flagged, not hidden."""

import re
from typing import Any

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.links.models import Faq, UsefulLink

pytestmark = pytest.mark.django_db

CHANGELIST = "admin:links_usefullink_changelist"


@pytest.fixture
def staff(client: Client) -> None:
    user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass-1234-pass")
    client.force_login(user)


def make_link(**overrides: Any) -> UsefulLink:
    values: dict[str, Any] = {
        "group": UsefulLink.Group.EXAM,
        "title": "Info-Car",
        "description": "Rezerwacja terminu egzaminu.",
        "url": "https://info-car.pl/",
    }
    values.update(overrides)
    return UsefulLink.objects.create(**values)


def changelist(client: Client, **params: str) -> str:
    response = client.get(reverse(CHANGELIST), params)
    assert response.status_code == 200
    return response.content.decode()


def results(body: str) -> str:
    """Just the result rows: the filter sidebar carries labels of its own."""
    found = re.search(r"<tbody[^>]*>.*?</tbody>", body, re.S)
    return found.group(0) if found else ""


def row_of(body: str, title: str) -> str:
    found = re.search(rf"<tr[^>]*>(?:(?!</tr>).)*{re.escape(title)}.*?</tr>", body, re.S)
    assert found, f"no row for {title}"
    return found.group(0)


def test_the_model_is_registered() -> None:
    assert UsefulLink in site._registry


def test_a_failing_link_is_flagged_in_the_list(client: Client, staff: None) -> None:
    """The acceptance criterion: last_status >= 400 is visible to the owner."""
    make_link(title="Zepsuty", last_checked_at=timezone.now(), last_status=404)
    make_link(
        title="Działa", url="https://gov.pl/", last_checked_at=timezone.now(), last_status=200
    )

    body = changelist(client)

    assert "HTTP 404" in row_of(body, "Zepsuty")
    assert "#B3382B" in row_of(body, "Zepsuty")
    assert "HTTP 200" in row_of(body, "Działa")
    assert "#B3382B" not in row_of(body, "Działa")


def test_a_timeout_is_flagged_too(client: Client, staff: None) -> None:
    """No status at all, and the link is just as unreachable."""
    make_link(title="Zepsuty", last_checked_at=timezone.now(), last_error="timeout after 10s")

    assert "timeout after 10s" in row_of(changelist(client), "Zepsuty")


def test_a_link_nobody_checked_yet_claims_nothing(client: Client, staff: None) -> None:
    make_link(title="Nowy")

    row = row_of(changelist(client), "Nowy")
    assert "HTTP" not in row
    assert "#B3382B" not in row


def test_the_owner_can_filter_down_to_the_broken_ones(client: Client, staff: None) -> None:
    make_link(title="Zepsuty", last_checked_at=timezone.now(), last_status=500)
    make_link(
        title="Działa", url="https://gov.pl/", last_checked_at=timezone.now(), last_status=200
    )
    make_link(title="Nowy", url="https://example.com/")

    broken = results(changelist(client, broken="yes"))
    working = results(changelist(client, broken="no"))
    unchecked = results(changelist(client, broken="never"))

    assert "Zepsuty" in broken and "Działa" not in broken and "Nowy" not in broken
    assert "Działa" in working and "Zepsuty" not in working
    assert "Nowy" in unchecked and "Działa" not in unchecked


def test_flagging_a_link_does_not_take_it_off_the_site(client: Client, staff: None) -> None:
    """The admin marks it, the owner decides, DEV.md S7.1."""
    make_link(title="Zepsuty", last_checked_at=timezone.now(), last_status=404)

    assert "Zepsuty" in client.get("/przydatne-linki/").content.decode()


# --------------------------------------------------------------------------
# faq, DEV.md S7.3


def test_the_faq_is_editable(client: Client, staff: None) -> None:
    """A page the owner cannot fill is a page that stays empty."""
    Faq.objects.create(question="Ile trwa kurs?", answer="Około trzech miesięcy.")

    response = client.get(reverse("admin:links_faq_changelist"))

    assert response.status_code == 200
    assert Faq in site._registry
    assert "Ile trwa kurs?" in results(response.content.decode())
