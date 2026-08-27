"""The faq page, DEV.md S7.3 acceptance criteria."""

import json
import re
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.seo import DESCRIPTION_LIMIT, TITLE_LIMIT
from apps.links.models import Faq

pytestmark = pytest.mark.django_db

PAGE = "/faq/"

ROWS = [
    (
        "Od jakiego wieku mogę zapisać się na kurs kategorii B?",
        "Trzy miesiące przed 18. urodzinami.",
    ),
    ("Co to jest PKK i gdzie go otrzymam?", "Wydaje go Starostwo Powiatowe w Wieluniu."),
    ("Jakie dokumenty są potrzebne do zapisu?", "Dowód tożsamości, orzeczenie i numer PKK."),
]


def make_question(number: int, **overrides: Any) -> Faq:
    question, answer = ROWS[number % len(ROWS)]
    values: dict[str, Any] = {"question": question, "answer": answer, "order": number}
    values.update(overrides)
    return Faq.objects.create(**values)


@pytest.fixture
def questions() -> list[Faq]:
    return [make_question(number) for number in range(len(ROWS))]


def page(client: Client) -> str:
    response = client.get(PAGE)
    assert response.status_code == 200
    return response.content.decode()


def jsonld(body: str) -> list[dict[str, Any]]:
    return [
        json.loads(found)
        for found in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    ]


def faq_page(body: str) -> dict[str, Any]:
    blocks = [block for block in jsonld(body) if block["@type"] == "FAQPage"]
    assert len(blocks) == 1, "exactly one FAQPage block belongs on this page"
    return blocks[0]


# --------------------------------------------------------------------------
# route and seo


def test_route_matches_the_url_map(client: Client, questions: list[Faq]) -> None:
    """tech.md section 5."""
    assert reverse("links:faq") == PAGE
    assert client.get(PAGE).status_code == 200


@pytest.mark.seo
def test_page_meets_the_seo_contract(client: Client, questions: list[Faq]) -> None:
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

    types = [block["@type"] for block in jsonld(body)]
    assert "DrivingSchool" in types
    assert "BreadcrumbList" in types
    assert "FAQPage" in types


@pytest.mark.a11y
def test_no_image_ships_an_empty_alt(client: Client, questions: list[Faq]) -> None:
    images = re.findall(r"<img[^>]*>", page(client))
    assert not [image for image in images if not re.search(r'alt="[^"]+"', image)]


# --------------------------------------------------------------------------
# the json-ld, tech.md section 8


def test_the_markup_holds_every_published_question(client: Client, questions: list[Faq]) -> None:
    """The acceptance criterion: the count in the markup equals the count in the database."""
    entries = faq_page(page(client))["mainEntity"]

    assert len(entries) == Faq.objects.filter(is_published=True).count() == len(ROWS)
    assert [entry["name"] for entry in entries] == [row.question for row in questions]


def test_every_entry_is_a_question_with_an_answer(client: Client, questions: list[Faq]) -> None:
    for entry in faq_page(page(client))["mainEntity"]:
        assert entry["@type"] == "Question"
        assert entry["acceptedAnswer"]["@type"] == "Answer"
        assert entry["acceptedAnswer"]["text"].strip()


def test_an_unpublished_question_is_in_neither_place(client: Client, questions: list[Faq]) -> None:
    make_question(0, question="Pytanie schowane", answer="Nie widać.", is_published=False)
    body = page(client)

    assert "Pytanie schowane" not in body
    assert len(faq_page(body)["mainEntity"]) == len(ROWS)


def test_the_answer_reaches_the_markup_without_its_markdown(
    client: Client, questions: list[Faq]
) -> None:
    """A search result should not show the asterisks the owner typed."""
    make_question(0, question="Ile kosztuje kurs?", answer="Cena **od** 3200 zł.", order=99)

    entries = faq_page(page(client))["mainEntity"]
    answer = next(entry for entry in entries if entry["name"] == "Ile kosztuje kurs?")

    assert "**" not in answer["acceptedAnswer"]["text"]
    assert "<strong>od</strong>" in answer["acceptedAnswer"]["text"]


def test_an_empty_page_emits_no_faq_block(client: Client) -> None:
    """An FAQPage with nothing in it is worse than none at all."""
    body = page(client)

    assert [block["@type"] for block in jsonld(body) if block["@type"] == "FAQPage"] == []
    assert "Pytania w przygotowaniu" in body


# --------------------------------------------------------------------------
# the accordion


def test_every_question_is_an_accordion_row(client: Client, questions: list[Faq]) -> None:
    body = page(client)

    assert body.count("<details") == len(ROWS)
    summaries = [found.strip() for found in re.findall(r"<summary[^>]*>\s*([^<]+)", body)]
    assert summaries == [row.question for row in questions]


def test_the_accordion_needs_no_javascript(client: Client, questions: list[Faq]) -> None:
    """details/summary opens on its own, DEV.md S7.3."""
    accordion = re.search(r'data-testid="faq".*?</section>', page(client), re.S).group(0)

    assert "<details" in accordion
    assert "<summary" in accordion
    assert "x-data" not in accordion
    assert "x-show" not in accordion


def test_the_answer_is_rendered_markdown(client: Client) -> None:
    make_question(0, answer="Potrzebujesz:\n\n- dowodu\n- orzeczenia")
    body = page(client)

    assert "<li>dowodu</li>" in body
    assert "- dowodu" not in body


def test_questions_keep_the_order_the_owner_set(client: Client) -> None:
    make_question(0, question="Trzecie", order=30)
    make_question(1, question="Pierwsze", order=10)
    make_question(2, question="Drugie", order=20)

    summaries = [found.strip() for found in re.findall(r"<summary[^>]*>\s*([^<]+)", page(client))]

    assert summaries == ["Pierwsze", "Drugie", "Trzecie"]


def test_groups_get_their_own_heading(client: Client) -> None:
    """The group is free text the owner types, and it may well stay empty."""
    make_question(0, question="Bez grupy", order=10)
    make_question(1, question="Z grupą", group="Egzamin", order=20)

    body = page(client)
    headings = re.findall(r"<h2[^>]*>(.*?)</h2>", body)

    assert headings == ["Egzamin"]
    assert body.index("Bez grupy") < body.index("Egzamin")


def test_one_group_for_everything_is_still_one_heading(client: Client) -> None:
    for number in range(3):
        make_question(number, group="Egzamin", order=number)

    assert re.findall(r"<h2[^>]*>(.*?)</h2>", page(client)) == ["Egzamin"]
