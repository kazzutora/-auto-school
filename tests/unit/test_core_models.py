"""Core models against tech.md section 4.1."""

from datetime import time
from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.test import RequestFactory
from django.utils import translation

from apps.core.context_processors import site_settings as site_settings_processor
from apps.core.models import OpeningHours, Page, SiteSettings
from apps.core.seo import driving_school_jsonld

pytestmark = pytest.mark.django_db


def test_timestamps_come_from_the_base_model() -> None:
    page = Page.objects.create(slug="rodo", title="RODO", body="tekst")
    assert page.created_at is not None
    assert page.updated_at is not None


def test_page_slug_is_unique() -> None:
    Page.objects.create(slug="o-nas", title="O nas", body="x")
    with pytest.raises(IntegrityError):
        Page.objects.create(slug="o-nas", title="Duplikat", body="y")


def test_opening_hours_are_unique_per_department_and_weekday() -> None:
    OpeningHours.objects.create(department=OpeningHours.DEPT.OFFICE, weekday=0)
    with pytest.raises(IntegrityError):
        OpeningHours.objects.create(department=OpeningHours.DEPT.OFFICE, weekday=0)


def test_missing_bounds_read_as_closed() -> None:
    row = OpeningHours.objects.create(department=OpeningHours.DEPT.PSYCHOLOGY, weekday=6)
    assert row.is_closed is True

    open_row = OpeningHours.objects.create(
        department=OpeningHours.DEPT.PSYCHOLOGY,
        weekday=1,
        opens=time(8, 0),
        closes=time(16, 0),
    )
    assert open_row.is_closed is False


def test_translated_field_follows_the_active_language() -> None:
    page = Page.objects.create(slug="o-nas", title="O nas", body="tekst")
    page.title_ru = "О нас"
    page.title_uk = "Про нас"
    page.save()

    page.refresh_from_db()
    with translation.override("pl"):
        assert page.title == "O nas"
    with translation.override("ru"):
        assert page.title == "О нас"
    with translation.override("uk"):
        assert page.title == "Про нас"


def test_notify_emails_splits_the_settings_field() -> None:
    site = SiteSettings.get_solo()
    site.lead_notify_emails = "a@example.com, b@example.com ,"
    assert site.notify_emails == ["a@example.com", "b@example.com"]


def test_context_processor_exposes_site_settings() -> None:
    context = site_settings_processor(RequestFactory().get("/"))
    assert isinstance(context["site_settings"], SiteSettings)


def test_driving_school_jsonld_from_site_settings() -> None:
    site = SiteSettings.get_solo()
    site.legal_name = "Ośrodek Kształcenia Adam Nawrocki S.C."
    site.short_name = "OSK Nawrocki"
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.nip = "8321916014"
    site.email = "osk.adam.nawrocki@wp.pl"
    site.phone_primary = "43 843 29 11"
    site.phone_secondary = "605 065 795"
    site.map_lat = Decimal("51.220000")
    site.map_lng = Decimal("18.570000")
    site.bank_account = "PL61109010140000071219812874"
    site.save()

    data = driving_school_jsonld(site)

    assert data["@type"] == "DrivingSchool"
    assert data["address"]["addressLocality"] == "Wieluń"
    assert data["address"]["addressCountry"] == "PL"
    assert data["geo"] == {
        "@type": "GeoCoordinates",
        "latitude": 51.22,
        "longitude": 18.57,
    }
    assert data["contactPoint"][0]["telephone"] == "605 065 795"


def test_driving_school_jsonld_never_leaks_the_bank_account() -> None:
    """tech.md section 1: the account number stays off public pages."""
    site = SiteSettings.get_solo()
    site.bank_account = "PL61109010140000071219812874"
    site.save()

    assert "PL61109010140000071219812874" not in repr(driving_school_jsonld(site))
