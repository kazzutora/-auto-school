"""tech.md section 6: build_renditions is idempotent on rendition presence."""

import pytest

from apps.core.imaging import RENDITION_WIDTHS, renditions
from apps.gallery.tasks import build_renditions
from tests.factories import GalleryImageFactory

pytestmark = pytest.mark.django_db

PAYLOAD = {"model": "gallery.GalleryImage", "pk": 0}


def run(pk: int) -> dict:
    return build_renditions.apply(kwargs={**PAYLOAD, "pk": pk}).get()


def test_first_run_generates_every_width() -> None:
    image = GalleryImageFactory()

    result = run(image.pk)

    assert result["generated"] == list(RENDITION_WIDTHS)
    for _width, cache_file in renditions(image.image):
        assert cache_file.storage.exists(cache_file.name)


def test_second_run_generates_nothing() -> None:
    """Two runs, one effect. Without this the task does not merge."""
    image = GalleryImageFactory()
    run(image.pk)

    stamps = {
        cache_file.name: cache_file.storage.get_modified_time(cache_file.name)
        for _width, cache_file in renditions(image.image)
    }

    result = run(image.pk)

    assert result["generated"] == []
    for name, before in stamps.items():
        storage = renditions(image.image)[0][1].storage
        assert storage.get_modified_time(name) == before


def test_a_row_without_a_file_is_a_no_op() -> None:
    image = GalleryImageFactory(image=None)
    assert run(image.pk)["generated"] == []
