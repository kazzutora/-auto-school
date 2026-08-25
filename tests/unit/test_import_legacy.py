"""Legacy import, DEV.md S1.1 acceptance criteria."""

from pathlib import Path

import pytest
from django.conf import settings

from apps.courses.models import Course
from scripts.import_legacy import NEEDS_WORK, TYPO_FIXES, fix_typos, import_courses

pytestmark = pytest.mark.django_db

LEGACY = Path(settings.BASE_DIR) / "data" / "legacy"

# tech.md section 5 url map and the section 4.8 redirect table agree on these.
EXPECTED_SLUGS = {
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

TEXT_FIELDS = ("title", "lead", "entitlements", "requirements", "body")


def all_text() -> str:
    return " ".join(
        " ".join(str(getattr(course, name) or "") for name in TEXT_FIELDS)
        for course in Course.objects.all()
    )


def test_import_creates_fifteen_courses() -> None:
    report = import_courses(LEGACY)

    assert len(report.created) == 15
    assert Course.objects.count() == 15


def test_a_second_run_does_not_duplicate() -> None:
    import_courses(LEGACY)
    report = import_courses(LEGACY)

    assert report.created == []
    assert len(report.updated) == 15
    assert Course.objects.count() == 15


def test_the_kinds_match_the_school_offer() -> None:
    import_courses(LEGACY)

    counts = {
        kind: Course.objects.filter(kind=kind).count()
        for kind in ("license", "professional", "psychotest", "operator")
    }
    assert counts == {"license": 9, "professional": 4, "psychotest": 1, "operator": 1}


def test_every_licence_category_is_present() -> None:
    import_courses(LEGACY)

    codes = set(Course.objects.filter(kind="license").values_list("code", flat=True))
    assert codes == {"AM", "A1", "A2", "A", "B", "B+E", "C", "C+E", "D"}


def test_slugs_match_the_url_map() -> None:
    """A slug that drifts breaks the redirect table in tech.md section 4.8."""
    import_courses(LEGACY)

    assert set(Course.objects.values_list("slug", flat=True)) == EXPECTED_SLUGS


@pytest.mark.parametrize("wrong", TYPO_FIXES)
def test_no_source_typo_survives_the_import(wrong: str) -> None:
    import_courses(LEGACY)

    assert wrong not in all_text()


@pytest.mark.parametrize(("wrong", "right"), TYPO_FIXES.items())
def test_the_correction_actually_lands(wrong: str, right: str) -> None:
    """Absence alone would also pass if the importer dropped the text entirely."""
    import_courses(LEGACY)

    assert right in all_text()


@pytest.mark.parametrize(("wrong", "right"), TYPO_FIXES.items())
def test_typo_correction_in_isolation(wrong: str, right: str) -> None:
    assert fix_typos(wrong) == right


def test_correction_does_not_reach_inside_a_longer_word() -> None:
    """A bare replace would turn "otrzymujacy" into "otrzymująсy" style nonsense."""
    assert fix_typos("otrzymujacy") == "otrzymujacy"
    assert fix_typos("prowadzanego") == "prowadzanego"


def test_the_two_unreadable_fragments_are_flagged() -> None:
    """tech.md section 15 names both places."""
    report = import_courses(LEGACY)

    assert set(report.needs_work) == {"kat-a2", "kwalifikacja-wstepna-przyspieszona"}
    assert NEEDS_WORK in Course.objects.get(slug="kat-a2").entitlements
    assert NEEDS_WORK in Course.objects.get(slug="kwalifikacja-wstepna-przyspieszona").body


def test_a_rerun_keeps_a_title_edited_in_the_admin() -> None:
    """The old site shouted its headings. An editor's fix must survive."""
    import_courses(LEGACY)
    course = Course.objects.get(slug="kat-b")
    course.title = "Kategoria B"
    course.save()

    import_courses(LEGACY)

    assert Course.objects.get(slug="kat-b").title == "Kategoria B"


def test_a_rerun_does_refresh_the_imported_body() -> None:
    """The content fields are the import's own, so they follow the export."""
    import_courses(LEGACY)
    course = Course.objects.get(slug="kat-b")
    course.body = "stale"
    course.save()

    import_courses(LEGACY)

    assert Course.objects.get(slug="kat-b").body != "stale"


def test_entitlements_and_requirements_are_split_apart() -> None:
    import_courses(LEGACY)
    course = Course.objects.get(slug="kat-b")

    assert "3,5 t" in course.entitlements
    assert "PKK" in course.requirements
    assert "PKK" not in course.entitlements


def test_the_export_is_still_the_reconstruction() -> None:
    """Fails the day the real export lands, which is exactly when to revisit."""
    report = import_courses(LEGACY)
    assert len(report.reconstructed) == 15, "real export present, update data/legacy/README.md"
