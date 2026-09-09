"""The legacy url table, tech.md sections 4.8 and 15, DEV.md S8.

Every url the old site had is still in a search index and in somebody's
bookmarks. One 301, straight to the page that replaced it.

The old site was a single page with anchor navigation, which splits the table in
two. Paths a request can carry — /index.html, the pdf files — are served by
django.contrib.redirects. Anchors like /#pliki never reach the server at all,
because a browser does not send the fragment, so those rows go to the home page
as json and static/js/app.js performs the jump. Both halves come out of one csv
and this module tests both.
"""

import pytest
from django.contrib.redirects.models import Redirect
from django.test import Client

from apps.core.models import Page
from apps.core.redirects import fragment_map, load_redirects, read_table, server_table

pytestmark = [pytest.mark.django_db, pytest.mark.redirects]

# The anchors the old one page site navigated by, and where each of them now
# lives. Frozen here; the csv is what the code reads and this is what keeps the
# two in step.
OLD_ANCHORS = {
    "ofirmie": "/o-nas/",
    "informacje": "/zapisy/",
    "pliki": "/do-pobrania/",
    "galeriazdjecia": "/galeria/",
    "galeriazdjecia_stat": "/zdawalnosc/",
    "kontakt": "/kontakt/",
}

TABLE = read_table()
SERVER_ROWS = server_table()


@pytest.fixture
def old_site() -> None:
    """The pages the old urls now point at."""
    from scripts import seed

    load_redirects()
    seed.seed_site_settings()
    seed.seed_courses()
    seed.seed_price_items()
    seed.seed_pass_rates()
    seed.seed_pages()


# --------------------------------------------------------------------------
# the table itself


def test_the_csv_holds_every_anchor_the_old_site_had() -> None:
    assert fragment_map() | OLD_ANCHORS == fragment_map()


def test_no_fragment_row_reaches_the_redirect_table() -> None:
    """A browser never sends the fragment, so the server cannot answer one.

    Loading these would put rows in django.contrib.redirects that no request can
    ever match, and hide the fact that the anchors are handled in the page.
    """
    assert not [old for old, _new in SERVER_ROWS if "#" in old]
    assert len(SERVER_ROWS) < len(TABLE)


def test_the_two_halves_add_up_to_the_whole_file() -> None:
    assert len(SERVER_ROWS) + len(fragment_map()) == len(TABLE)


def test_loading_twice_leaves_one_row_each(old_site: None) -> None:
    """The loader runs on every deploy, tech.md section 4.8."""
    first = Redirect.objects.count()

    load_redirects()

    assert Redirect.objects.count() == first == len(SERVER_ROWS)


# --------------------------------------------------------------------------
# what a visitor gets


@pytest.mark.parametrize(("old_path", "new_path"), SERVER_ROWS, ids=[old for old, _ in SERVER_ROWS])
def test_the_old_url_moves_permanently(
    client: Client, old_site: None, old_path: str, new_path: str
) -> None:
    response = client.get(old_path)

    assert response.status_code == 301
    assert response.headers["Location"] == new_path


@pytest.mark.parametrize("new_path", sorted(set(OLD_ANCHORS.values())))
def test_every_anchor_lands_on_a_real_page(client: Client, old_site: None, new_path: str) -> None:
    """A jump into a 404 loses the visitor and the ranking with them."""
    assert client.get(new_path).status_code == 200


@pytest.mark.parametrize(("old_path", "new_path"), SERVER_ROWS, ids=[old for old, _ in SERVER_ROWS])
def test_nobody_is_bounced_twice(
    client: Client, old_site: None, old_path: str, new_path: str
) -> None:
    """One hop, tech.md section 4.8: chains cost speed and dilute the signal."""
    final = client.get(old_path, follow=True)

    assert len(final.redirect_chain) == 1
    assert final.status_code == 200


def test_an_unknown_old_url_still_answers_404(client: Client, old_site: None) -> None:
    assert client.get("/Czegos-takiego-nigdy-nie-bylo").status_code == 404


# --------------------------------------------------------------------------
# the half the browser has to do


def test_the_home_page_carries_the_anchor_table(client: Client, old_site: None) -> None:
    """Without it static/js/app.js has nothing to look the hash up in."""
    body = client.get("/").content.decode()

    assert 'id="legacy-fragments"' in body
    for anchor, target in OLD_ANCHORS.items():
        assert anchor in body
        assert target in body


def test_an_anchor_that_is_also_a_section_here_is_not_a_redirect(
    client: Client, old_site: None
) -> None:
    """ "kontakt" is both an old anchor and a real section of the new home page.

    app.js checks for the element before jumping, so a reader arriving at
    /#kontakt scrolls to the contact block rather than being thrown to
    /kontakt/. The test that the id exists is what makes that branch reachable.
    """
    body = client.get("/").content.decode()

    assert 'id="kontakt"' in body


def test_a_page_that_is_not_home_carries_no_anchor_table(client: Client, old_site: None) -> None:
    """The old anchors only ever hung off the root, so only the root needs them."""
    assert 'id="legacy-fragments"' not in client.get("/cennik/").content.decode()


def test_the_flat_pages_the_anchors_point_at_exist(old_site: None) -> None:
    assert Page.objects.filter(slug="o-nas", is_published=True).exists()
    assert Page.objects.filter(slug="zapisy", is_published=True).exists()
