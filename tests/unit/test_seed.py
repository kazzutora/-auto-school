"""The seed is the single source of fixtures, DEV.md S0.8."""

import pytest
from django.core.files.storage import default_storage

from apps.core.models import OpeningHours, Page, SiteSettings
from apps.courses.models import Course, CourseIntake, PriceItem
from apps.gallery.models import Certificate, GalleryImage
from apps.links.models import Faq, UsefulLink
from apps.people.models import Instructor, Vehicle
from apps.reviews.models import Testimonial
from scripts.seed import TODO, owner_data_gaps, run

pytestmark = pytest.mark.django_db

# DEV.md S0.8 spells out how much of everything the seed produces.
EXPECTED_ROWS = {
    Course: 15,  # 9 licence + 4 professional + psychotests + forklifts
    CourseIntake: 6,
    PriceItem: 6,
    Instructor: 4,
    Vehicle: 5,
    GalleryImage: 12,
    Certificate: 11,
    UsefulLink: 12,
    Faq: 8,
    Testimonial: 3,
    Page: 3,
    OpeningHours: 14,  # two departments, seven days each
}


def counts() -> dict[str, int]:
    return {model.__name__: model.objects.count() for model in EXPECTED_ROWS}


@pytest.fixture
def seeded() -> None:
    run()


def test_seed_produces_the_documented_volume(seeded: None) -> None:
    assert counts() == {model.__name__: total for model, total in EXPECTED_ROWS.items()}
    assert SiteSettings.objects.count() == 1


def test_seed_is_idempotent(seeded: None) -> None:
    """Running twice must not duplicate a single row."""
    before = counts()
    run()
    assert counts() == before


def test_rerunning_does_not_pile_up_media_files(seeded: None) -> None:
    """Re-saving an ImageField would store a new suffixed copy each time."""

    def media_files() -> set[str]:
        found: set[str] = set()
        for folder in ("gallery", "certificates", "people", "vehicles"):
            if default_storage.exists(folder):
                found |= {f"{folder}/{name}" for name in default_storage.listdir(folder)[1]}
        return found

    before = media_files()
    assert before
    run()
    assert media_files() == before


def test_courses_cover_the_slugs_the_redirect_table_points_at(seeded: None) -> None:
    """tech.md section 4.8 sends every legacy url at one of these."""
    expected = {
        "kat-am",
        "kat-a1",
        "kat-a2",
        "kat-a",
        "kat-b",
        "kat-be",
        "kat-c",
        "kat-ce",
        "kat-d",
        "szkolenia-okresowe",
        "kwalifikacja-wstepna",
        "kwalifikacja-wstepna-przyspieszona",
        "adr",
        "badania-psychologiczne",
        "wozki-widlowe",
    }
    assert set(Course.objects.values_list("slug", flat=True)) == expected


def test_psychology_hours_are_the_ones_we_actually_know(seeded: None) -> None:
    """tech.md section 16: tuesday and friday 8:00-16:00, everything else closed."""
    rows = {
        row.weekday: row
        for row in OpeningHours.objects.filter(department=OpeningHours.DEPT.PSYCHOLOGY)
    }
    for weekday in range(7):
        open_day = weekday in (1, 4)
        assert rows[weekday].is_closed is not open_day


def test_no_synthetic_review_can_reach_a_page(seeded: None) -> None:
    """tech.md section 4.7 forbids invented reviews, so placeholders stay unpublished."""
    assert Testimonial.objects.filter(is_published=True).count() == 0
    for review in Testimonial.objects.all():
        assert review.text.startswith(TODO)


def test_bank_account_is_not_public(seeded: None) -> None:
    """tech.md section 1: the account number stays off public pages."""
    assert SiteSettings.get_solo().bank_account_public is False


def test_every_useful_link_explains_itself(seeded: None) -> None:
    """tech.md section 4.6: a bare url with no description is not allowed."""
    for link in UsefulLink.objects.all():
        assert link.description.strip()


def test_every_gallery_image_has_an_alt(seeded: None) -> None:
    for image in GalleryImage.objects.all():
        assert image.alt.strip()


def test_gaps_are_reported_while_owner_data_is_missing(seeded: None) -> None:
    """The report is the mechanism, so it has to actually find something."""
    gaps = owner_data_gaps()
    assert gaps
    assert any("price_gross" in gap for gap in gaps)
