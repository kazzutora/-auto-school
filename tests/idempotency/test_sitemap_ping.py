"""tech.md section 6: the sitemap ping is repeatable by nature.

It writes nothing anywhere, so the night it runs twice has to end exactly like
the night it ran once, DEV.md S8.
"""

from typing import Any

import pytest
from django.contrib.sites.models import Site

from apps.core import tasks
from apps.core.tasks import SEARCH_ENGINES, ping_sitemap

pytestmark = pytest.mark.django_db

DOMAIN = "oskostrycharz.pl"
SITEMAP = f"https%3A%2F%2F{DOMAIN}%2Fsitemap.xml"


class FakeInternet:
    """The seam tech.md section 6 would put behind an HttpClient."""

    def __init__(self, answers: dict[str, int | Exception] | None = None) -> None:
        self.answers: dict[str, int | Exception] = answers or {}
        self.visited: list[str] = []

    def __call__(self, url: str, **options: Any) -> int:
        self.visited.append(url)
        for fragment, answer in self.answers.items():
            if fragment in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer
        return 200


@pytest.fixture
def internet(monkeypatch: pytest.MonkeyPatch) -> FakeInternet:
    fake = FakeInternet()
    monkeypatch.setattr(tasks, "fetch_status", fake)
    return fake


@pytest.fixture
def live_domain() -> None:
    """The site knows its own name, which is what a ping is worth sending."""
    Site.objects.filter(pk=1).update(domain=DOMAIN, name="OSK Ostrycharz")


def run() -> dict[str, Any]:
    return ping_sitemap.apply().get()


# --------------------------------------------------------------------------
# what one run does


def test_every_engine_is_told_where_the_sitemap_is(
    internet: FakeInternet, live_domain: None
) -> None:
    result = run()

    assert result["sitemap"] == f"https://{DOMAIN}/sitemap.xml"
    assert sorted(result["accepted"]) == sorted(SEARCH_ENGINES)
    assert result["failed"] == []
    for url in internet.visited:
        assert url.endswith(SITEMAP), url


def test_the_second_run_changes_nothing(internet: FakeInternet, live_domain: None) -> None:
    first = run()

    second = run()

    assert second == first
    assert len(internet.visited) == 2 * len(SEARCH_ENGINES)


# --------------------------------------------------------------------------
# when the world does not cooperate


def test_one_engine_timing_out_does_not_cost_the_other_its_ping(
    internet: FakeInternet, live_domain: None
) -> None:
    """A best effort ping that raised would retry against a search engine."""
    internet.answers = {"google.com": TimeoutError("timed out")}

    result = run()

    assert result["failed"] == ["google"]
    assert result["accepted"] == ["bing"]
    assert len(internet.visited) == len(SEARCH_ENGINES)


def test_an_engine_answering_with_an_error_counts_as_failed(
    internet: FakeInternet, live_domain: None
) -> None:
    """Google retired its endpoint and answers 404, tech.md section 6."""
    internet.answers = {"google.com": 404}

    result = run()

    assert result["failed"] == ["google"]
    assert result["accepted"] == ["bing"]


def test_a_site_still_called_example_com_is_not_advertised(internet: FakeInternet) -> None:
    """Handing a search engine the default domain is worse than staying quiet."""
    result = run()

    assert result == {"sitemap": "", "accepted": [], "failed": []}
    assert internet.visited == []
