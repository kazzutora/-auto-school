"""Three languages, as a gate rather than a promise.

tech.md section 1 says the site is served in polish, russian and ukrainian.
Until the catalogues existed that was true of the url prefixes only: /ru/ was a
different address for the same polish page. These tests hold the two halves of
the fix in place — gettext for the interface, modeltranslation for the rows —
and the three ways it broke silently while it was being built.
"""

from pathlib import Path

import pytest
from django.test import Client
from django.utils import translation

from apps.core.models import SiteSettings
from apps.courses.models import Course

pytestmark = pytest.mark.django_db

LOCALE = Path(__file__).resolve().parents[2] / "locale"

# One word per language from the chrome every page carries: the navigation and
# the footer. Checking a whole page instead would only prove what the fixtures
# happen to contain.
CHROME = {
    "pl": ("Cennik", "Zdawalność", "Kontakt"),
    "ru": ("Цены", "Сдача экзамена", "Контакты"),
    "uk": ("Ціни", "Складання іспиту", "Контакти"),
}


@pytest.fixture
def site() -> SiteSettings:
    return SiteSettings.objects.create(
        legal_name="OSK Ostrycharz",
        short_name="OSK Ostrycharz",
        street="Asnyka 7",
        postal_code="98-300",
        city="Wieluń",
        phone_primary="691 570 489",
        email="biuro@example.com",
    )


@pytest.mark.parametrize("language", ["pl", "ru", "uk"])
def test_the_chrome_speaks_the_language_of_the_prefix(
    client: Client, site: SiteSettings, language: str
) -> None:
    prefix = "" if language == "pl" else f"/{language}"
    response = client.get(f"{prefix}/")
    assert response.status_code == 200

    body = response.content.decode()
    for word in CHROME[language]:
        assert word in body, f"{language} page is missing {word!r}"

    # And carries none of the other two, which is what a missing catalogue
    # looks like: the prefix changes, the words do not.
    for other, words in CHROME.items():
        if other == language:
            continue
        assert words[0] not in body, f"{language} page still says {words[0]!r}"


def test_the_polish_page_never_shows_an_english_key(client: Client, site: SiteSettings) -> None:
    """The model choices carry english msgids.

    Course modes and lead statuses were written as _("Stationary"), which needs
    a pl catalogue to come out polish. Without one the polish site printed the
    key itself, and nobody noticed because a mode only reaches a page once an
    intake exists.
    """
    # Keys whose polish differs from the key. E-learning is deliberately not
    # here: polish spells it the same way, so an identical string is the right
    # answer and proves nothing either way.
    with translation.override("pl"):
        for key in ("Stationary", "Planned", "Office", "Psychology lab", "Full", "Closed"):
            assert translation.gettext(key) != key, f"{key} has no polish translation"


def test_every_catalogue_is_compiled_and_free_of_guesses() -> None:
    """A fuzzy entry is a guess makemessages made from a similar string, and
    msgfmt drops it: the page then shows the source language while the .po
    looks perfectly translated."""
    for language in ("pl", "ru", "uk"):
        po = LOCALE / language / "LC_MESSAGES" / "django.po"
        assert po.exists(), f"{language} has no catalogue"

        text = po.read_text(encoding="utf-8")
        assert "#, fuzzy" not in text, f"{language} carries fuzzy entries msgfmt will drop"

        mo = po.with_suffix(".mo")
        assert mo.exists(), f"{language} is not compiled; run make messages"


@pytest.mark.parametrize("language", ["ru", "uk"])
def test_a_row_answers_in_the_asked_language(
    client: Client, site: SiteSettings, language: str
) -> None:
    """A course title lives in a row, not in a template, so gettext never sees
    it. modeltranslation carries it and scripts/seed_translations.py fills it.
    """
    Course.objects.create(
        slug="kat-b",
        code="B",
        kind=Course.Kind.LICENSE,
        title="Kategoria B",
        title_ru="Категория B",
        title_uk="Категорія B",
        is_active=True,
    )

    response = client.get(f"/{language}/kursy/")
    assert response.status_code == 200

    body = response.content.decode()
    expected = "Категория B" if language == "ru" else "Категорія B"
    assert expected in body, f"the {language} listing did not use the translated title"
    assert "Kategoria B" not in body, f"the {language} listing still names the polish title"


def test_a_row_with_no_translation_falls_back_to_polish(client: Client, site: SiteSettings) -> None:
    """MODELTRANSLATION_FALLBACK_LANGUAGES is what keeps a half translated
    database readable: an empty _ru shows the polish text, never an empty gap.
    """
    Course.objects.create(
        slug="kat-c",
        code="C",
        kind=Course.Kind.LICENSE,
        title="Kategoria C",
        is_active=True,
    )

    body = client.get("/ru/kursy/").content.decode()
    assert "Kategoria C" in body, "an untranslated row rendered as nothing at all"


def test_the_language_row_offers_all_three(client: Client, site: SiteSettings) -> None:
    body = client.get("/").content.decode()
    for code in ("pl", "ru", "uk"):
        assert f'hreflang="{code}"' in body, f"{code} is missing from the language row"
