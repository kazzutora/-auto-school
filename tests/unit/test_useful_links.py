"""The useful links page, DEV.md S7.1 acceptance criteria."""

import json
import re
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.links.models import UsefulLink

pytestmark = pytest.mark.django_db

PAGE = "/przydatne-linki/"

ROWS = [
    ("exam", "Info-Car", "Rezerwacja terminu egzaminu państwowego.", "https://info-car.pl/"),
    (
        "gov",
        "Sprawdź punkty karne",
        "Liczba punktów karnych po zalogowaniu profilem zaufanym.",
        "https://www.gov.pl/web/gov/sprawdz-punkty-karne",
    ),
    (
        "tests",
        "Testy na prawo jazdy",
        "Oficjalna baza pytań egzaminacyjnych.",
        "https://www.gov.pl/web/infrastruktura/testy",
    ),
    (
        "local",
        "Starostwo Powiatowe w Wieluniu",
        "Tu odbierzesz numer PKK i gotowe prawo jazdy.",
        "https://powiat.wielun.pl/",
    ),
]


def make_link(**overrides: Any) -> UsefulLink:
    values: dict[str, Any] = {
        "group": UsefulLink.Group.EXAM,
        "title": "Info-Car",
        "description": "Rezerwacja terminu egzaminu państwowego.",
        "url": "https://info-car.pl/",
    }
    values.update(overrides)
    return UsefulLink.objects.create(**values)


@pytest.fixture
def links() -> None:
    for order, (group, title, description, url) in enumerate(ROWS):
        make_link(group=group, title=title, description=description, url=url, order=order)


def page(client: Client) -> str:
    response = client.get(PAGE)
    assert response.status_code == 200
    return response.content.decode()


def headings(body: str) -> list[str]:
    return re.findall(r"<h2[^>]*>(.*?)</h2>", body)


def anchors(body: str) -> list[tuple[str, str]]:
    """Every outbound link on the page, with the attributes that follow it."""
    return re.findall(r'<a href="(https?://[^"]+)"([^>]*)>', body)


# --------------------------------------------------------------------------
# route and seo


def test_route_matches_the_url_map(client: Client, links: None) -> None:
    """tech.md section 5."""
    assert reverse("links:useful") == PAGE
    assert client.get(PAGE).status_code == 200


@pytest.mark.seo
def test_page_meets_the_seo_contract(client: Client, links: None) -> None:
    body = page(client)

    assert len(re.findall(r"<h1[ >]", body)) == 1

    title = re.search(r"<title>(.*?)</title>", body).group(1)
    assert "Wieluń" in title
    assert len(title) <= TITLE_LIMIT

    description = re.search(r'name="description" content="(.*?)"', body).group(1)
    assert description.strip()
    assert len(description) <= DESCRIPTION_LIMIT

    canonical = re.search(r'rel="canonical" href="(.*?)"', body).group(1)
    assert canonical.endswith(PAGE)

    types = [
        json.loads(found)["@type"]
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]
    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types


@pytest.mark.a11y
def test_no_image_ships_an_empty_alt(client: Client, links: None) -> None:
    images = re.findall(r"<img[^>]*>", page(client))
    assert not [image for image in images if not re.search(r'alt="[^"]+"', image)]


# --------------------------------------------------------------------------
# grouping


def test_links_are_grouped_in_reading_order(client: Client, links: None) -> None:
    """tech.md section 4.6 groups: exam, gov, tests, local."""
    assert headings(page(client)) == [
        "Egzamin",
        "Urzędy i e-usługi",
        "Testy i przepisy",
        "Wieluń i okolice",
    ]


def test_a_link_sits_under_its_own_group(client: Client, links: None) -> None:
    body = page(client)
    sections = re.split(r"<h2[^>]*>", body)[1:]
    under = {section.split("</h2>")[0]: section for section in sections}

    assert "Info-Car" in under["Egzamin"]
    assert "Starostwo Powiatowe w Wieluniu" in under["Wieluń i okolice"]
    assert "Info-Car" not in under["Wieluń i okolice"]


def test_an_empty_group_gets_no_heading(client: Client) -> None:
    make_link(group=UsefulLink.Group.EXAM)

    assert headings(page(client)) == ["Egzamin"]


def test_an_empty_list_says_so_instead_of_breaking(client: Client) -> None:
    body = page(client)

    assert "Lista w przygotowaniu" in body
    assert not anchors(body)


# --------------------------------------------------------------------------
# what a link looks like


def test_a_link_carries_its_title_and_one_line_of_description(client: Client, links: None) -> None:
    body = page(client)

    assert "Info-Car" in body
    assert "Rezerwacja terminu egzaminu państwowego." in body


def test_every_outbound_link_opens_in_a_new_tab_safely(client: Client, links: None) -> None:
    """target=_blank without rel hands the opener to the target page."""
    found = anchors(page(client))

    assert len(found) == len(ROWS)
    for url, attributes in found:
        assert 'target="_blank"' in attributes, url
        assert 'rel="noopener noreferrer"' in attributes, url


def test_the_new_tab_is_announced_to_a_screen_reader(client: Client, links: None) -> None:
    assert page(client).count("otwiera się w nowej karcie") == len(ROWS)


# --------------------------------------------------------------------------
# what stays off the page


def test_an_inactive_link_is_not_shown(client: Client, links: None) -> None:
    make_link(title="Wyłączony", url="https://example.com/off", is_active=False)
    body = page(client)

    assert "Wyłączony" not in body
    assert len(anchors(body)) == len(ROWS)


def test_a_broken_link_still_shows_until_the_owner_says_otherwise(
    client: Client, links: None
) -> None:
    """The acceptance criterion: the night check flags, the owner decides."""
    UsefulLink.objects.filter(title="Info-Car").update(last_status=404, last_error="not found")
    body = page(client)

    assert "Info-Car" in body
    assert len(anchors(body)) == len(ROWS)


def test_a_link_without_a_description_never_renders(client: Client, links: None) -> None:
    """A bare url is what the page exists to avoid, tech.md section 4.6.

    The model refuses one, so this row has to be forced in the way an import or
    a data migration would.
    """
    naked = make_link(title="Goły link", url="https://example.com/naked")
    UsefulLink.objects.filter(pk=naked.pk).update(description="   ")

    body = page(client)

    assert "Goły link" not in body
    assert "https://example.com/naked" not in body


# --------------------------------------------------------------------------
# validation


@pytest.mark.parametrize("description", ["", "   "])
def test_the_model_refuses_a_link_without_a_description(description: str) -> None:
    link = UsefulLink(
        group=UsefulLink.Group.EXAM,
        title="Info-Car",
        description=description,
        url="https://info-car.pl/",
    )

    with pytest.raises(ValidationError):
        link.full_clean()


def test_the_model_accepts_a_described_link() -> None:
    UsefulLink(
        group=UsefulLink.Group.EXAM,
        title="Info-Car",
        description="Rezerwacja terminu egzaminu.",
        url="https://info-car.pl/",
    ).full_clean()


@pytest.mark.parametrize(
    ("status", "error", "broken"),
    [
        (200, "", False),
        (301, "", False),
        (399, "", False),
        (400, "", True),
        (404, "", True),
        (500, "", True),
        (None, "timeout", True),
        (None, "", False),
    ],
)
def test_a_link_knows_whether_the_last_check_failed(
    status: int | None, error: str, broken: bool
) -> None:
    link = UsefulLink(last_status=status, last_error=error)

    assert link.is_broken is broken


# --------------------------------------------------------------------------
# FRONTEND.md F10


def test_no_bare_url_is_printed_anywhere(client: Client, links: None) -> None:
    """F10: the name and one line of description, never the address itself.

    A wall of https://info-car.pl/... tells a reader nothing the name does not,
    and a url with no spaces in it is what pushes a phone screen sideways.
    """
    body = page(client)
    region = body[body.index('data-testid="groups"') :]
    region = region[: region.index("</section>")]

    for url in UsefulLink.objects.values_list("url", flat=True):
        assert f'href="{url}"' in region, "the link itself must still be there"
        # ...but the address is never printed as text.
        assert f">{url}<" not in region
        assert f"> {url}" not in region


def test_the_external_mark_sits_on_every_row(client: Client, links: None) -> None:
    """F10: the icon says the row leaves the site before the click does."""
    body = page(client)
    region = body[body.index('data-testid="groups"') :]
    region = region[: region.index("</section>")]

    rows = region.count('rel="noopener noreferrer"')
    assert rows == UsefulLink.objects.filter(is_active=True).count()
    assert region.count("#i-external") == rows
