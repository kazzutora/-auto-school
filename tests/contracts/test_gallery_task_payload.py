"""Payload of gallery.tasks.build_renditions against tech.md section 6."""

import pytest

from apps.core.contracts import ContractError, validate_payload
from apps.gallery.tasks import TASK_NAME, build_renditions
from config.celery import app
from tests.factories import GalleryImageFactory


def test_task_is_registered_under_the_contract_name() -> None:
    assert TASK_NAME == "gallery.tasks.build_renditions"
    assert TASK_NAME in app.tasks


def test_contract_payload_validates() -> None:
    validate_payload(TASK_NAME, {"model": "gallery.GalleryImage", "pk": 7})


@pytest.mark.parametrize(
    "payload",
    [
        {"pk": 7},
        {"model": "gallery.GalleryImage"},
        {"model": "gallery.GalleryImage", "pk": "7"},
        {"model": 1, "pk": 7},
        {"model": "gallery.GalleryImage", "pk": 7, "width": 480},
    ],
)
def test_junk_payload_is_rejected(payload: dict) -> None:
    with pytest.raises(ContractError):
        validate_payload(TASK_NAME, payload)


@pytest.mark.django_db
def test_the_task_itself_refuses_a_bad_payload() -> None:
    """The seam has to bite at call time, not only in a unit test."""
    image = GalleryImageFactory()
    with pytest.raises(ContractError):
        build_renditions.apply(kwargs={"model": 1, "pk": image.pk}).get()
