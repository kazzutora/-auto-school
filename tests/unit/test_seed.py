"""The seed is the single source of fixtures, DEV.md S0.8."""

from datetime import time
from decimal import Decimal

import pytest

from apps.core.models import DownloadFile, OpeningHours, Page, PassRate, SiteSettings
from apps.courses.models import Course, PriceItem
from apps.gallery.models import Certificate, GalleryImage
from apps.links.models import Faq, UsefulLink
from apps.people.models import Instructor, Vehicle
from apps.reviews.models import Testimonial
from scripts.seed import (
    CONFIRMED_PASS_RATE_YEAR,
    PRICE_ITEMS,
    TODO,
    owner_data_gaps,
    run,
)

pytestmark = pytest.mark.django_db

# What the seed produces for this client. tech.md section 1: one category, ten
# priced lines, one confirmed year of results, five documents.
EXPECTED_ROWS = {
    Course: 1,
    PriceItem: len(PRICE_ITEMS),
    PassRate: 1,
    DownloadFile: 5,
    UsefulLink: 6,
    Faq: 8,
    Page: 4,
    OpeningHours: 7,  # one department, seven days
}

# What the seed deliberately does not create. Every one of these would be either
# somebody else's property or a fact nobody supplied.
EXPECTED_EMPTY = (Instructor, Vehicle, GalleryImage, Certificate, Testimonial)


def counts() -> dict[str, int]:
    return {model.__name__: model.objects.count() for model in EXPECTED_ROWS}


@pytest.fixture
def seeded() -> None:
    run()


def test_seed_produces_the_documented_volume(seeded: None) -> None:
    assert counts() == {model.__name__: total for model, total in EXPECTED_ROWS.items()}
    assert SiteSettings.objects.count() == 1


@pytest.mark.parametrize("model", EXPECTED_EMPTY, ids=[m.__name__ for m in EXPECTED_EMPTY])
def test_the_seed_invents_no_people_pictures_or_reviews(seeded: None, model: type) -> None:
    """The photographs on the old site are the school's, not ours.

    A placeholder instructor is worse than an absent section: the section knows
    how to not render, and a made up name does not know it is made up.
    """
    assert model.objects.count() == 0


def test_seed_is_idempotent(seeded: None) -> None:
    """Running twice must not duplicate a single row."""
    before = counts()
    run()
    assert counts() == before


def test_the_first_run_is_already_complete(seeded: None) -> None:
    """update_or_create's create_defaults replaces defaults, it does not add.

    Splitting the two without merging left a freshly created course with no
    kind, no title and no price until somebody happened to seed twice — which
    every developer does and no fresh deploy does.
    """
    course = Course.objects.get(slug="kat-b")

    assert course.kind == Course.Kind.LICENSE
    assert course.code == "B"
    assert course.title
    assert course.price_gross == Decimal("3700.00")
    assert course.entitlements.strip()
    assert course.requirements.strip()


def test_the_offer_is_one_category(seeded: None) -> None:
    """tech.md section 1: this school teaches B and nothing else."""
    assert set(Course.objects.filter(is_active=True).values_list("slug", flat=True)) == {"kat-b"}


def test_every_published_price_is_on_the_record(seeded: None) -> None:
    """tech.md section 1, transcribed to the złoty. No figure is rounded here."""
    prices = dict(PriceItem.objects.values_list("title_pl", "price_gross"))

    assert prices["Kurs kategorii B"] == Decimal("3700.00")
    assert prices["Kurs przyspieszony"] == Decimal("4300.00")
    assert prices["Skrzynia automatyczna"] == Decimal("4300.00")
    assert prices["Jazda doszkalająca — manual"] == Decimal("160.00")
    assert prices["Jazda doszkalająca — manual, dla naszych kursantów"] == Decimal("140.00")
    assert prices["Jazda doszkalająca — automat"] == Decimal("140.00")
    assert prices["Badanie lekarskie"] == Decimal("200.00")
    assert prices["Egzamin państwowy"] == Decimal("230.00")
    assert prices["Zaświadczenie o zameldowaniu"] == Decimal("17.00")
    assert prices["Dowóz na egzamin"] == Decimal("0.00")


def test_the_confirmed_year_carries_the_schools_own_counts(seeded: None) -> None:
    entry = PassRate.objects.get(year=CONFIRMED_PASS_RATE_YEAR)

    assert (entry.students, entry.passed_1st) == (92, 68)
    assert (entry.passed_2nd, entry.passed_3rd, entry.passed_4th) == (16, 3, 3)


def test_office_hours_are_the_ones_the_school_publishes(seeded: None) -> None:
    """OSTRYCHARZ.md part A: pn-pt 06:30-19:00, sob 06:30-12:30, niedz. nieczynne,
    from the school's own Google Business profile.

    Inventing hours is the one lie on the page a visitor can catch by turning
    up, so the seed carries exactly these and nothing rounder.
    """
    rows = {
        row.weekday: row for row in OpeningHours.objects.filter(department=OpeningHours.DEPT.OFFICE)
    }

    assert sorted(rows) == list(range(7))
    for weekday in range(5):
        assert (rows[weekday].opens, rows[weekday].closes) == (time(6, 30), time(19, 0))
    assert (rows[5].opens, rows[5].closes) == (time(6, 30), time(12, 30))
    assert rows[6].is_closed


def test_there_is_no_psychology_lab(seeded: None) -> None:
    """The previous client had one; this one does not, so the table is empty."""
    assert not OpeningHours.objects.filter(department=OpeningHours.DEPT.PSYCHOLOGY).exists()


def test_documents_are_created_with_the_school_s_own_files(seeded: None) -> None:
    """The pdfs are the school's and they are in this repository now.

    They used not to be: the rows existed so the admin had somewhere to upload
    them, and the selector kept every one off the page until a file arrived.
    The owner asked for their own five to be brought across from the old site
    at core v33, so they live in data/documents/ and the seed attaches them.

    The selector rule has not changed and is what this still holds: a row with
    no file stays off the page, so a "Pobierz" button never points at nothing.
    """
    from apps.core.selectors import published_downloads

    assert DownloadFile.objects.count() == 5
    assert published_downloads().count() == 5, "the pdfs did not attach"

    for row in published_downloads():
        assert row.file, row.title
        assert row.size_bytes, f"{row.title} has a file and no size"
        assert row.group, f"{row.title} is in no group"


def test_no_synthetic_review_can_reach_a_page(seeded: None) -> None:
    """tech.md section 4.7 forbids invented reviews.

    The school's own "110 opinii, 96% bardzo dobrych" is prose with no source
    behind it, so no Testimonial is created at all.
    """
    assert Testimonial.objects.count() == 0


def test_no_fabricated_identity_reaches_site_settings(seeded: None) -> None:
    """The NIP and the founding year are not published anywhere. They stay empty.

    A guessed tax number would land in the DrivingSchool json-ld, which is the
    worst possible place to be wrong.
    """
    site = SiteSettings.get_solo()

    assert site.nip == ""
    assert site.founded_year is None


def test_bank_account_is_not_public(seeded: None) -> None:
    """tech.md section 1: the account number stays off public pages."""
    assert SiteSettings.get_solo().bank_account_public is False


def test_every_useful_link_explains_itself(seeded: None) -> None:
    """tech.md section 4.6: a bare url with no description is not allowed."""
    for link in UsefulLink.objects.all():
        assert link.description.strip()


def test_the_legal_pages_still_carry_their_marker(seeded: None) -> None:
    """The privacy policy is the owner's text to approve, not ours to write."""
    assert Page.objects.filter(body__contains=TODO).count() == 2


def test_gaps_are_reported_while_owner_data_is_missing(seeded: None) -> None:
    """The report is the mechanism, so it has to actually find something."""
    gaps = owner_data_gaps()

    assert gaps
    assert any("nip" in gap for gap in gaps)
    assert any("photographs" in gap for gap in gaps)


def test_the_denominator_disagreement_is_reported_rather_than_smoothed_over(
    seeded: None,
) -> None:
    """The old site prints 76%; 68 of 92 is 74%.

    Their figure divides by the 90 who eventually passed. Ours divides by the 92
    who sat, because that is what the label beside it says. The difference is a
    question for the owner, not something to quietly pick a side on.
    """
    assert any("76%" in gap and "74%" in gap for gap in owner_data_gaps())
