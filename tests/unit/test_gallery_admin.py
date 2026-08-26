"""Gallery admin, DEV.md S6.1: an image without an alt is not saved."""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.gallery.models import GalleryImage
from tests.factories import image_bytes

pytestmark = pytest.mark.django_db

ADD = "admin:gallery_galleryimage_add"


@pytest.fixture
def staff(client: Client) -> None:
    user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass-1234-pass")
    client.force_login(user)


def payload(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "section": GalleryImage.Section.SCHOOL,
        "alt_pl": "Plac manewrowy ośrodka",
        "alt_ru": "",
        "alt_uk": "",
        "caption_pl": "",
        "caption_ru": "",
        "caption_uk": "",
        "order": 100,
        "legacy_name": "",
        "is_published": "on",
        "image": image_bytes(),
    }
    values.update(overrides)
    return values


def test_an_image_with_an_alt_is_saved(client: Client, staff: None) -> None:
    response = client.post(reverse(ADD), payload())

    assert response.status_code == 302
    assert GalleryImage.objects.get().alt == "Plac manewrowy ośrodka"


@pytest.mark.parametrize("alt", ["", "   "])
def test_an_image_without_an_alt_is_refused(client: Client, staff: None, alt: str) -> None:
    """The a11y gate starts here: an empty alt must not reach the database."""
    response = client.post(reverse(ADD), payload(alt_pl=alt))

    # The form comes back with the error instead of redirecting to the list.
    assert response.status_code == 200
    assert "alt_pl" in response.context["adminform"].form.errors
    assert not GalleryImage.objects.exists()


def test_the_other_languages_stay_optional(client: Client, staff: None) -> None:
    """Polish carries the alt, russian and ukrainian fall back to it."""
    client.post(reverse(ADD), payload(alt_ru="", alt_uk=""))

    image = GalleryImage.objects.get()
    assert image.alt_pl == "Plac manewrowy ośrodka"
    assert image.alt == image.alt_pl
