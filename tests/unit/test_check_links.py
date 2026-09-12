"""The nightly link sweep, DEV.md S7.2 acceptance criteria."""

from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from apps.core.models import SiteSettings
from apps.links import checker
from apps.links.models import UsefulLink
from apps.links.tasks import check_links

pytestmark = pytest.mark.django_db


class FakeInternet:
    """Answers instead of the network, and records what it was asked.

    The seam the doctrine asks for, tech.md section 9. It lives here rather than
    in apps/core/clients because there is no HttpClient protocol yet, see the
    contract gap in apps/links/checker.py.
    """

    def __init__(self, answers: dict[str, Any] | None = None) -> None:
        self.answers = answers or {}
        self.asked: list[tuple[str, str, float]] = []

    def __call__(
        self, url: str, *, timeout: float = checker.TIMEOUT, agent: str | None = None
    ) -> checker.CheckResult:
        self.asked.append((url, agent or "", timeout))
        answer = self.answers.get(url, checker.CheckResult(status=200))
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture
def internet(monkeypatch: pytest.MonkeyPatch) -> Any:
    def install(answers: dict[str, Any] | None = None) -> FakeInternet:
        fake = FakeInternet(answers)
        monkeypatch.setattr(checker, "check", fake)
        return fake

    return install


@pytest.fixture
def site() -> SiteSettings:
    settings = SiteSettings.get_solo()
    settings.short_name = "OSK Ostrycharz"
    settings.save()
    return settings


def make_link(number: int, **overrides: Any) -> UsefulLink:
    values: dict[str, Any] = {
        "group": UsefulLink.Group.GOV,
        "title": f"Link {number}",
        "description": "Opis linku.",
        "url": f"https://example.com/{number}",
    }
    values.update(overrides)
    return UsefulLink.objects.create(**values)


def run() -> dict[str, Any]:
    return check_links.apply().get()


# --------------------------------------------------------------------------
# the sweep


def test_the_sweep_records_every_link(internet: Any, site: SiteSettings) -> None:
    for number in range(3):
        make_link(number)
    internet()

    result = run()

    assert result == {"checked": 3, "failed": 0}
    for link in UsefulLink.objects.all():
        assert link.last_status == 200
        assert link.last_error == ""
        assert link.last_checked_at is not None


def test_two_bad_links_out_of_twelve_do_not_stop_the_others(
    internet: Any, site: SiteSettings
) -> None:
    """The acceptance criterion, in the numbers the task names."""
    for number in range(12):
        make_link(number)
    internet(
        {
            "https://example.com/3": checker.CheckResult(status=500, error="HTTP 500"),
            "https://example.com/7": checker.CheckResult(error="timeout after 10s"),
        }
    )

    result = run()

    assert result == {"checked": 12, "failed": 2}
    assert UsefulLink.objects.filter(last_checked_at__isnull=True).count() == 0
    assert UsefulLink.objects.get(url="https://example.com/3").last_status == 500
    assert UsefulLink.objects.get(url="https://example.com/7").last_error == "timeout after 10s"


def test_a_crash_inside_the_checker_costs_only_its_own_link(
    internet: Any, site: SiteSettings
) -> None:
    """The checker promises not to raise. The sweep survives it breaking that."""
    for number in range(3):
        make_link(number)
    internet({"https://example.com/1": RuntimeError("boom")})

    result = run()

    assert result == {"checked": 3, "failed": 1}
    broken = UsefulLink.objects.get(url="https://example.com/1")
    assert "RuntimeError: boom" in broken.last_error
    assert broken.last_checked_at is not None
    assert UsefulLink.objects.get(url="https://example.com/2").last_status == 200


def test_an_inactive_link_is_not_visited(internet: Any, site: SiteSettings) -> None:
    make_link(1)
    sleeping = make_link(2, is_active=False)
    fake = internet()

    assert run()["checked"] == 1
    assert [url for url, _agent, _timeout in fake.asked] == ["https://example.com/1"]
    sleeping.refresh_from_db()
    assert sleeping.last_checked_at is None


def test_a_link_that_came_back_loses_its_error(internet: Any, site: SiteSettings) -> None:
    """A stale error would keep the row flagged in the admin for good."""
    link = make_link(1)
    UsefulLink.objects.filter(pk=link.pk).update(last_status=500, last_error="HTTP 500")
    internet()

    run()

    link.refresh_from_db()
    assert link.last_status == 200
    assert link.last_error == ""
    assert link.is_broken is False


def test_the_sweep_asks_with_the_agreed_timeout_and_a_named_agent(
    internet: Any, site: SiteSettings
) -> None:
    """tech.md section 6: ten seconds, and a user agent an admin can read."""
    make_link(1)
    fake = internet()

    run()

    _url, agent, timeout = fake.asked[0]
    assert timeout == 10.0
    assert "OSK Ostrycharz" in agent
    assert "link checker" in agent


def test_the_sweep_leaves_the_content_alone(internet: Any, site: SiteSettings) -> None:
    """The night job owns three fields. updated_at belongs to the owner."""
    link = make_link(1)
    before = UsefulLink.objects.get(pk=link.pk)
    internet()

    run()

    after = UsefulLink.objects.get(pk=link.pk)
    assert after.updated_at == before.updated_at
    assert (after.title, after.description, after.url, after.is_active) == (
        before.title,
        before.description,
        before.url,
        before.is_active,
    )


# --------------------------------------------------------------------------
# what one look at a url returns


class FakeOpener:
    """Stands in for urlopen: answers per method, records the requests."""

    def __init__(self, answers: dict[str, Any]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, str, float]] = []

    def __call__(self, request: Any, timeout: float = 0) -> Any:
        self.calls.append((request.full_url, request.get_method(), timeout))
        answer = self.answers[request.get_method()]
        if isinstance(answer, Exception):
            raise answer
        return answer


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exception: object) -> None:
        return None


@pytest.fixture
def opener(monkeypatch: pytest.MonkeyPatch) -> Any:
    def install(answers: dict[str, Any]) -> FakeOpener:
        fake = FakeOpener(answers)
        monkeypatch.setattr(checker, "urlopen", fake)
        return fake

    return install


def http_error(code: int) -> HTTPError:
    return HTTPError("https://example.com/", code, "nope", {}, None)  # type: ignore[arg-type]


def test_a_healthy_url_answers_on_head(opener: Any) -> None:
    fake = opener({"HEAD": FakeResponse(200)})

    assert checker.check("https://example.com/", agent="test") == checker.CheckResult(status=200)
    assert [method for _url, method, _timeout in fake.calls] == ["HEAD"]


def test_a_server_that_refuses_head_is_asked_again_with_get(opener: Any) -> None:
    """Plenty of sites answer 405 to HEAD and serve the page perfectly well."""
    fake = opener({"HEAD": http_error(405), "GET": FakeResponse(200)})

    assert checker.check("https://example.com/", agent="test").status == 200
    assert [method for _url, method, _timeout in fake.calls] == ["HEAD", "GET"]


def test_a_real_404_survives_the_second_question(opener: Any) -> None:
    fake = opener({"HEAD": http_error(404), "GET": http_error(404)})

    result = checker.check("https://example.com/", agent="test")

    assert result == checker.CheckResult(status=404, error="HTTP 404")
    assert len(fake.calls) == 1  # 404 is an answer, not a refusal to answer


def test_a_server_error_is_recorded_with_its_status(opener: Any) -> None:
    opener({"HEAD": http_error(500)})

    result = checker.check("https://example.com/", agent="test")

    assert result == checker.CheckResult(status=500, error="HTTP 500")


@pytest.mark.parametrize(
    "failure",
    [TimeoutError("timed out"), URLError(TimeoutError("timed out"))],
)
def test_a_timeout_is_recorded_as_one(opener: Any, failure: Exception) -> None:
    opener({"HEAD": failure})

    result = checker.check("https://example.com/", agent="test", timeout=10)

    assert result == checker.CheckResult(error="timeout after 10s")


def test_an_unreachable_host_keeps_its_reason(opener: Any) -> None:
    opener({"HEAD": URLError("Name or service not known")})

    result = checker.check("https://example.com/", agent="test")

    assert result.status is None
    assert "Name or service not known" in result.error


def test_a_long_reason_is_cut_to_what_the_column_holds(opener: Any) -> None:
    opener({"HEAD": URLError("x" * 500)})

    assert len(checker.check("https://example.com/", agent="test").error) <= checker.ERROR_LIMIT


def test_the_user_agent_names_the_school(site: SiteSettings) -> None:
    agent = checker.user_agent()

    assert agent.startswith("OSK Ostrycharz link checker")
    assert "https://" in agent


def test_a_redirect_head_cannot_follow_is_asked_again_with_get(opener: Any) -> None:
    """A 302 with no usable Location is what isap.sejm.gov.pl answers to HEAD."""
    fake = opener({"HEAD": http_error(302), "GET": FakeResponse(200)})

    assert checker.check("https://example.com/", agent="test").status == 200
    assert [method for _url, method, _timeout in fake.calls] == ["HEAD", "GET"]


def test_a_redirect_is_not_a_broken_link(opener: Any) -> None:
    """It answers, so the owner has nothing to fix and nothing to be told."""
    opener({"HEAD": http_error(301), "GET": http_error(301)})

    result = checker.check("https://example.com/", agent="test")

    assert result == checker.CheckResult(status=301, error="")


def test_a_redirect_leaves_the_link_unflagged(internet: Any, site: SiteSettings) -> None:
    make_link(1)
    internet({"https://example.com/1": checker.CheckResult(status=301)})

    assert run() == {"checked": 1, "failed": 0}
    assert UsefulLink.objects.get(url="https://example.com/1").is_broken is False
