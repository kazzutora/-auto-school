"""Documents for download, tech.md sections 4.1 and 5."""

import re

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.core.models import DownloadFile
from apps.core.selectors import published_downloads
from apps.core.services import human_size
from tests.factories import notify_site

pytestmark = pytest.mark.django_db


def document(name: str = "regulamin.pdf", size: int = 1258291, **overrides: object) -> DownloadFile:
    values: dict = {"title": "Regulamin", "description": "Zasady szkolenia."}
    values.update(overrides)
    row = DownloadFile(**values)
    row.file.save(name, ContentFile(b"x" * size), save=True)
    return row


def body_of(client: Client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == 200, url
    return response.content.decode()


# --------------------------------------------------------------------------
# the size, which the owner never types


@pytest.mark.parametrize(
    ("size_bytes", "expected"),
    [
        (None, ""),
        (0, ""),
        (-5, ""),
        (1, "1 B"),
        (999, "999 B"),
        (1024, "1,0 KB"),
        (1536, "1,5 KB"),
        (1258291, "1,2 MB"),
        (5 * 1024 * 1024, "5,0 MB"),
        (3 * 1024 * 1024 * 1024, "3,0 GB"),
    ],
)
def test_a_size_reads_the_way_a_person_writes_one(size_bytes: int | None, expected: str) -> None:
    assert human_size(size_bytes) == expected


def test_a_missing_size_prints_nothing_rather_than_none() -> None:
    """The template prints this unguarded, so it must never say "None"."""
    assert human_size(None) == ""
    assert "None" not in human_size(0)


def test_the_separator_follows_the_language_it_is_printed_in() -> None:
    assert human_size(1536) == "1,5 KB"
    assert human_size(1536, decimal_sep=".") == "1.5 KB"


def test_saving_fills_the_size_from_the_file() -> None:
    row = document(size=2048)

    assert row.size_bytes == 2048


def test_the_size_follows_the_file_when_it_is_replaced() -> None:
    row = document(size=2048)

    row.file.save("umowa.pdf", ContentFile(b"y" * 4096), save=True)

    assert DownloadFile.objects.get(pk=row.pk).size_bytes == 4096


def test_a_row_with_no_file_advertises_no_size() -> None:
    """A document waiting on the owner must not claim "1,2 MB" of nothing."""
    row = DownloadFile.objects.create(title="Umowa", description="Do podpisu.")

    assert row.size_bytes is None


def test_a_file_the_storage_has_lost_does_not_take_the_page_down() -> None:
    """The media volume can be rebuilt from a database dump without the files."""
    row = document()
    row.file.storage.delete(row.file.name)

    row.save()

    assert row.size_bytes is None


# --------------------------------------------------------------------------
# what reaches a page


def test_a_row_without_a_file_never_reaches_the_page() -> None:
    """A "Pobierz" button pointing at nothing is worse than a shorter list."""
    document()
    DownloadFile.objects.create(title="Umowa", description="Jeszcze nie wgrana.")

    assert [row.title for row in published_downloads()] == ["Regulamin"]


def test_an_unpublished_row_never_reaches_the_page() -> None:
    document(is_published=False)

    assert not published_downloads().exists()


def test_rows_come_in_the_order_the_owner_set() -> None:
    document(name="c.pdf", title="Trzeci", order=30)
    document(name="a.pdf", title="Pierwszy", order=10)
    document(name="b.pdf", title="Drugi", order=20)

    assert [row.title for row in published_downloads()] == ["Pierwszy", "Drugi", "Trzeci"]


# --------------------------------------------------------------------------
# the page


def test_the_route_matches_the_url_map() -> None:
    """tech.md section 5."""
    assert reverse("core:downloads") == "/do-pobrania/"


def test_the_page_lists_what_is_uploaded(client: Client) -> None:
    notify_site()
    document()

    body = body_of(client, "/do-pobrania/")

    assert "Regulamin" in body
    assert "1,2 MB" in body
    assert len(re.findall(r"<h1[ >]", body)) == 1


def test_every_link_is_a_download_and_carries_noopener(client: Client) -> None:
    notify_site()
    document()

    body = body_of(client, "/do-pobrania/")
    anchor = re.search(r'<a href="[^"]*regulamin[^"]*"[^>]*>', body, re.I).group(0)

    assert "download" in anchor
    assert "noopener" in anchor


def test_the_page_renders_with_nothing_uploaded_yet(client: Client) -> None:
    """The owner is still sending the pdfs and the page still has to work."""
    notify_site()
    DownloadFile.objects.create(title="Umowa", description="W drodze.")

    body = body_of(client, "/do-pobrania/")

    assert "691 570 489" in body
    assert len(re.findall(r"<h1[ >]", body)) == 1


def test_the_enrolment_page_shows_the_same_documents(client: Client) -> None:
    from apps.core.models import Page

    notify_site()
    Page.objects.create(
        slug="zapisy",
        title="Zapisy i dokumenty",
        lead="Jak się zapisać.",
        body="# Zapisy",
        is_published=True,
    )
    document()

    assert "Regulamin" in body_of(client, "/zapisy/")
