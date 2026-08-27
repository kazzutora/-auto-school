"""tech.md section 6: the sweep is repeatable by nature.

It owns three fields and overwrites them, so a second run in the same day has
to leave the same state behind, DEV.md S7.2.
"""

from typing import Any

import pytest

from apps.core.models import SiteSettings
from apps.links import checker
from apps.links.models import UsefulLink
from apps.links.tasks import check_links

pytestmark = pytest.mark.django_db

ANSWERS = {
    "https://example.com/3": checker.CheckResult(status=500, error="HTTP 500"),
    "https://example.com/7": checker.CheckResult(error="timeout after 10s"),
}


class FakeInternet:
    def __init__(self, answers: dict[str, checker.CheckResult]) -> None:
        self.answers = answers
        self.visits = 0

    def __call__(self, url: str, **options: Any) -> checker.CheckResult:
        self.visits += 1
        return self.answers.get(url, checker.CheckResult(status=200))


@pytest.fixture
def internet(monkeypatch: pytest.MonkeyPatch) -> FakeInternet:
    fake = FakeInternet(ANSWERS)
    monkeypatch.setattr(checker, "check", fake)
    return fake


@pytest.fixture
def twelve_links() -> None:
    site = SiteSettings.get_solo()
    site.short_name = "OSK Nawrocki"
    site.save()

    for number in range(12):
        UsefulLink.objects.create(
            group=UsefulLink.Group.GOV,
            title=f"Link {number}",
            description="Opis linku.",
            url=f"https://example.com/{number}",
        )


def state() -> list[tuple[Any, ...]]:
    """Everything the sweep is allowed to change, and everything it is not.

    last_checked_at is left out on purpose: it is the one field that has to
    move, and the run before it wrote a different second.
    """
    return list(
        UsefulLink.objects.order_by("pk").values_list(
            "pk", "title", "description", "url", "is_active", "last_status", "last_error"
        )
    )


def run() -> dict[str, Any]:
    return check_links.apply().get()


def test_the_first_run_checks_every_link(internet: FakeInternet, twelve_links: None) -> None:
    result = run()

    assert result == {"checked": 12, "failed": 2}
    assert internet.visits == 12
    assert UsefulLink.objects.filter(last_checked_at__isnull=True).count() == 0


def test_the_second_run_leaves_the_same_state(internet: FakeInternet, twelve_links: None) -> None:
    run()
    after_first = state()
    stamps = dict(UsefulLink.objects.values_list("pk", "last_checked_at"))

    result = run()

    assert result == {"checked": 12, "failed": 2}
    assert state() == after_first
    assert UsefulLink.objects.count() == 12

    # The only difference a repeat is allowed to make: a fresher stamp.
    for pk, stamp in UsefulLink.objects.values_list("pk", "last_checked_at"):
        assert stamp >= stamps[pk]


def test_a_link_that_recovered_is_not_left_flagged(
    internet: FakeInternet, twelve_links: None
) -> None:
    """A second run is also how a fixed link gets its clean bill back."""
    run()
    assert UsefulLink.objects.get(url="https://example.com/3").is_broken

    internet.answers = {}
    run()

    healed = UsefulLink.objects.get(url="https://example.com/3")
    assert healed.last_status == 200
    assert healed.last_error == ""
    assert healed.is_broken is False
