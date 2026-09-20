"""The owner's whole loop, through the admin and back out onto the page.

tests/unit/test_admin_coverage.py already proves every model is reachable and
deletable. This proves the part that actually matters to the person logging in:
that a row they add in the admin appears on the site, and that deleting it
takes it off again.

Every case here posts the real add form rather than calling Model.objects
.create — the form is what the owner uses, and a field the admin never renders
is a field they cannot fill. An upload goes through as a real file, because
"can I put a photograph on the site" is the question this file exists to
answer.
"""

from __future__ import annotations

import io
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from PIL import Image

pytestmark = pytest.mark.django_db


@pytest.fixture
def about_page() -> Any:
    """/o-nas/ is a flat page, so it 404s until the row exists."""
    from apps.core.models import Page, SiteSettings

    site = SiteSettings.get_solo()
    site.short_name = "OSK Ostrycharz"
    site.phone_primary = "691 570 489"
    site.save()

    return Page.objects.create(
        slug="o-nas",
        title="O nas",
        lead="Szkolimy kierowców kategorii B w Wieluniu.",
        body="## Kim jesteśmy\n\nOśrodek szkolenia kierowców w Wieluniu.",
        is_published=True,
    )


@pytest.fixture
def owner(client: Client) -> Client:
    """Logged in as the person who runs the school."""
    user = get_user_model().objects.create_superuser("owner", "o@example.com", "pass-1234-pass")
    client.force_login(user)
    return client


def photo(name: str = "auto.jpg", size: tuple[int, int] = (400, 300)) -> SimpleUploadedFile:
    """A real jpeg, not a text file with a jpg name.

    Pillow opens the upload when the model saves it, and a fake one fails in a
    way that looks like a form error rather than a bad fixture.
    """
    buffer = io.BytesIO()
    Image.new("RGB", size, (214, 56, 94)).save(buffer, "JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def add(client: Client, model: str, data: dict[str, Any]) -> Any:
    """Post the admin's own add form and return the response."""
    return client.post(reverse(f"admin:{model}_add"), data, follow=True)


def rows(model: type[Any], **lookup: Any) -> int:
    return model.objects.filter(**lookup).count()


# --------------------------------------------------------------------------
# a photograph, from the upload form to the gallery and off it again


def test_a_gallery_photograph_reaches_the_page_and_leaves_it(owner: Client) -> None:
    from apps.gallery.models import GalleryImage

    response = add(
        owner,
        "gallery_galleryimage",
        {
            "image": photo("plac.jpg"),
            "alt": "Plac manewrowy o poranku",
            "alt_pl": "Plac manewrowy o poranku",
            "section": "yard",
            "order": "10",
            "is_published": "on",
        },
    )
    assert response.status_code == 200
    assert rows(GalleryImage, alt="Plac manewrowy o poranku") == 1, "the add form was rejected"

    page = owner.get("/galeria/").content.decode()
    assert "Plac manewrowy o poranku" in page, "uploaded but not on the gallery"

    entry = GalleryImage.objects.get(alt="Plac manewrowy o poranku")
    owner.post(reverse("admin:gallery_galleryimage_delete", args=[entry.pk]), {"post": "yes"})

    assert rows(GalleryImage, alt="Plac manewrowy o poranku") == 0
    assert "Plac manewrowy o poranku" not in owner.get("/galeria/").content.decode()


def test_the_home_strip_shows_what_the_gallery_was_given(owner: Client) -> None:
    """The strip added at core v40 reads the same rows, so it has to follow."""
    from apps.gallery.models import GalleryImage

    assert "Miejsce na zdjęcie" in owner.get("/").content.decode(), "no frames before"

    add(
        owner,
        "gallery_galleryimage",
        {
            "image": photo("osrodek.jpg"),
            "alt": "Sala wykładowa",
            "alt_pl": "Sala wykładowa",
            "section": "school",
            "order": "10",
            "is_published": "on",
        },
    )
    assert rows(GalleryImage, alt="Sala wykładowa") == 1

    home = owner.get("/").content.decode()
    assert "Sala wykładowa" in home, "uploaded but the home strip still shows frames"


# --------------------------------------------------------------------------
# an instructor, which is the block /o-nas/ opens on


def test_an_instructor_replaces_the_frames_on_the_about_page(
    owner: Client, about_page: Any
) -> None:
    from apps.people.models import Instructor

    about = owner.get("/o-nas/").content.decode()
    assert "Imię i nazwisko" in about, "no placeholder cards before"

    response = add(
        owner,
        "people_instructor",
        {
            "full_name": "Mariola Ostrycharz",
            "role": "",
            "role_pl": "",
            "bio": "",
            "bio_pl": "",
            "since_year": "2008",
            "photo": photo("instruktor.jpg", (300, 300)),
            "order": "10",
            "is_active": "on",
            "categories": [],
        },
    )
    assert response.status_code == 200
    assert rows(Instructor, full_name="Mariola Ostrycharz") == 1, "the add form was rejected"

    about = owner.get("/o-nas/").content.decode()
    assert "Mariola Ostrycharz" in about
    # D.2 again: the frames exist only while there is no real face to show.
    assert "Imię i nazwisko" not in about, "a real instructor and the placeholder both"

    person = Instructor.objects.get(full_name="Mariola Ostrycharz")
    owner.post(reverse("admin:people_instructor_delete", args=[person.pk]), {"post": "yes"})

    about = owner.get("/o-nas/").content.decode()
    assert "Mariola Ostrycharz" not in about
    assert "Imię i nazwisko" in about, "the frames have to come back"


# --------------------------------------------------------------------------
# the things that are not pictures


def test_a_price_row_added_in_the_admin_shows_on_the_price_list(owner: Client) -> None:
    from apps.courses.models import PriceItem

    add(
        owner,
        "courses_priceitem",
        {
            "title": "Jazda nocna",
            "title_pl": "Jazda nocna",
            "note": "",
            "note_pl": "",
            "price_gross": "180",
            "unit": "za godzinę",
            "unit_pl": "za godzinę",
            "group": "Jazdy doszkalające",
            "group_pl": "Jazdy doszkalające",
            "includes": "",
            "includes_pl": "",
            "order": "50",
            "is_active": "on",
        },
    )
    assert rows(PriceItem, title="Jazda nocna") == 1, "the add form was rejected"
    assert "Jazda nocna" in owner.get("/cennik/").content.decode()

    item = PriceItem.objects.get(title="Jazda nocna")
    owner.post(reverse("admin:courses_priceitem_delete", args=[item.pk]), {"post": "yes"})
    assert "Jazda nocna" not in owner.get("/cennik/").content.decode()


def test_a_question_added_in_the_admin_answers_on_the_page(owner: Client) -> None:
    """The home page printed an empty panel until core v40, so this holds the
    answer as well as the question."""
    from apps.links.models import Faq

    add(
        owner,
        "links_faq",
        {
            "question": "Czy można zapłacić kartą?",
            "question_pl": "Czy można zapłacić kartą?",
            "answer": "Tak, w biurze.",
            "answer_pl": "Tak, w biurze.",
            "group": "",
            "group_pl": "",
            "order": "10",
            "is_published": "on",
        },
    )
    assert rows(Faq, question="Czy można zapłacić kartą?") == 1, "the add form was rejected"

    home = owner.get("/").content.decode()
    assert "Czy można zapłacić kartą?" in home
    assert "Tak, w biurze." in home, "the question is on the page and the answer is not"


def test_a_pass_rate_scan_reaches_the_about_page(owner: Client, about_page: Any) -> None:
    from apps.core.models import PassRateScan

    add(
        owner,
        "core_passratescan",
        {
            "title": "II kwartał 2022",
            "year": "2022",
            "image": photo("2022.jpg", (800, 640)),
            "order": "10",
            "is_published": "on",
        },
    )
    assert rows(PassRateScan, title="II kwartał 2022") == 1, "the add form was rejected"
    assert "II kwartał 2022" in owner.get("/o-nas/").content.decode()


# --------------------------------------------------------------------------
# the index itself


def test_the_index_names_every_group_in_polish(owner: Client) -> None:
    """Django prints the module name otherwise, and "Core" means nothing to
    the person who runs the school."""
    index = owner.get(reverse("admin:index")).content.decode()

    for label in (
        "Ośrodek i strony",
        "Kursy i cennik",
        "Galeria i certyfikaty",
        "Zgłoszenia",
        "Linki i FAQ",
        "Instruktorzy i pojazdy",
        "Opinie",
    ):
        assert label in index, label

    assert "OSK Ostrycharz" in index


def test_every_uploaded_picture_has_a_thumbnail_column(owner: Client) -> None:
    """A file path is not a picture. The owner opens a changelist to see what
    a row carries."""
    from apps.gallery.models import GalleryImage

    add(
        owner,
        "gallery_galleryimage",
        {
            "image": photo("auto.jpg"),
            "alt": "Auto szkoleniowe",
            "alt_pl": "Auto szkoleniowe",
            "section": "vehicles",
            "order": "10",
            "is_published": "on",
        },
    )
    entry = GalleryImage.objects.get(alt="Auto szkoleniowe")

    changelist = owner.get(reverse("admin:gallery_galleryimage_changelist")).content.decode()
    assert entry.image.url in changelist, "the changelist shows no thumbnail"
