"""The legacy url table, tech.md sections 4.8 and 15, DEV.md S8.

Every url the old site had is still in a search index and in somebody's
bookmarks. One 301, straight to the page that replaced it.
"""

from urllib.parse import quote

import pytest
from django.contrib.redirects.models import Redirect
from django.test import Client

from apps.core.models import Page
from apps.core.redirects import load_redirects, read_table
from scripts.import_legacy import import_courses
from tests.unit.test_import_legacy import LEGACY

pytestmark = [pytest.mark.django_db, pytest.mark.redirects]

# tech.md section 4.8, the frozen minimum. The csv is generated from this list
# and this test is what keeps the two in step.
TECH_MD_TABLE = {
    "/KAT. AM": "/kursy/kat-am/",
    "/KAT. A1": "/kursy/kat-a1/",
    "/KAT. A2": "/kursy/kat-a2/",
    "/KAT. A": "/kursy/kat-a/",
    "/KAT. B": "/kursy/kat-b/",
    "/KAT. BE": "/kursy/kat-be/",
    "/KAT. C": "/kursy/kat-c/",
    "/KAT. CE": "/kursy/kat-ce/",
    "/KAT. D": "/kursy/kat-d/",
    "/Szkolenia okresowe": "/kierowca-zawodowy/szkolenia-okresowe/",
    "/Kwalifikacja wstępna": "/kierowca-zawodowy/kwalifikacja-wstepna/",
    "/Kwalifikacja wstępna przyspieszona": (
        "/kierowca-zawodowy/kwalifikacja-wstepna-przyspieszona/"
    ),
    "/Badania psychologiczne": "/badania-psychologiczne/",
    "/Kurs ADR": "/kierowca-zawodowy/adr/",
    "/Wózki widłowe": "/wozki-widlowe/",
    "/Oferta": "/kursy/",
    "/O nas": "/o-nas/",
    "/Kontakt": "/kontakt/",
    "/Galeria": "/galeria/",
    "/Certyfikaty": "/certyfikaty/",
    "/Przydatne strony": "/przydatne-linki/",
}

TABLE = read_table()


@pytest.fixture
def old_site() -> None:
    """The courses and pages the old urls now point at."""
    load_redirects()
    import_courses(LEGACY)
    Page.objects.create(slug="o-nas", title="O nas", body="## Kim jesteśmy", is_published=True)


# --------------------------------------------------------------------------
# the table itself


def test_the_csv_holds_every_path_tech_md_freezes() -> None:
    assert dict(TABLE) | TECH_MD_TABLE == dict(TABLE)


def test_every_path_is_there_in_both_spellings() -> None:
    """A crawler sends /KAT.%20B, a pasted link may arrive with the space."""
    spellings = {old for old, _new in TABLE}

    for old_path in TECH_MD_TABLE:
        assert old_path in spellings, old_path
        assert quote(old_path) in spellings, old_path


def test_loading_twice_leaves_one_row_each(old_site: None) -> None:
    """The loader runs on every deploy, tech.md section 4.8."""
    first = Redirect.objects.count()

    load_redirects()

    assert Redirect.objects.count() == first == len(TABLE)


# --------------------------------------------------------------------------
# what a visitor gets


@pytest.mark.parametrize(("old_path", "new_path"), TABLE, ids=[old for old, _ in TABLE])
def test_the_old_url_moves_permanently(
    client: Client, old_site: None, old_path: str, new_path: str
) -> None:
    response = client.get(old_path)

    assert response.status_code == 301
    assert response.headers["Location"] == new_path


@pytest.mark.parametrize("new_path", sorted(set(TECH_MD_TABLE.values())))
def test_the_target_is_a_real_page(client: Client, old_site: None, new_path: str) -> None:
    """A 301 into a 404 loses the visitor and the ranking with them."""
    assert client.get(new_path).status_code == 200


@pytest.mark.parametrize(("old_path", "new_path"), TABLE, ids=[old for old, _ in TABLE])
def test_nobody_is_bounced_twice(
    client: Client, old_site: None, old_path: str, new_path: str
) -> None:
    """One hop, tech.md section 4.8: chains cost speed and dilute the signal."""
    final = client.get(old_path, follow=True)

    assert len(final.redirect_chain) == 1
    assert final.status_code == 200


def test_an_unknown_old_url_still_answers_404(client: Client, old_site: None) -> None:
    assert client.get("/Czegos-takiego-nigdy-nie-bylo").status_code == 404
