"""End to end fixtures.

Playwright's sync api drives the browser from a greenlet with an event loop
running, and django then refuses ordinary orm calls on that thread. The opt out
is scoped to this directory so the rest of the suite keeps the guard.
"""

import os
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from apps.core.models import OpeningHours, SiteSettings

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

# tech.md section 9 wants the mobile viewport covered: the visitor arrives from
# a phone searching "prawo jazdy Wieluń".
MOBILE = {"width": 390, "height": 844}


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """One browser for the whole session.

    Shared on purpose. Opening a second sync_playwright() while the first is
    still alive puts the sync api inside a running asyncio loop and it refuses.
    """
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport=MOBILE)
    new_page = context.new_page()
    yield new_page
    context.close()


# Every public route in tech.md section 5 that answers without an argument,
# plus one course page, which is the template the other fourteen share.
PAGES = (
    "/",
    "/kursy/",
    "/kursy/kat-b/",
    "/kierowca-zawodowy/",
    "/cennik/",
    "/terminy/",
    "/galeria/",
    "/certyfikaty/",
    "/przydatne-linki/",
    "/faq/",
    "/kontakt/",
    "/o-nas/",
    "/rodo/",
    "/zapisz-sie/",
)


@pytest.fixture
def site(db: None) -> SiteSettings:
    """A school with everything filled in, so no page renders half empty."""
    from datetime import date, time, timedelta
    from decimal import Decimal

    from apps.core.models import Page as FlatPage
    from apps.courses.models import Course, CourseIntake, PriceItem
    from apps.links.models import Faq, UsefulLink
    from apps.reviews.models import Testimonial
    from tests.factories import CertificateFactory, GalleryImageFactory

    settings_row = SiteSettings.get_solo()
    settings_row.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    settings_row.short_name = "OSK Ostrycharz"
    settings_row.street = "ul. Asnyka 7"
    settings_row.postal_code = "98-300"
    settings_row.city = "Wieluń"
    settings_row.nip = "7671234567"
    settings_row.email = "biuro@example.com"
    settings_row.phone_primary = "691 570 489"
    settings_row.phone_secondary = "605 065 795"
    settings_row.map_lat = Decimal("51.220600")
    settings_row.map_lng = Decimal("18.569700")
    settings_row.lead_notify_emails = "biuro@example.com"
    settings_row.save()

    for weekday in range(5):
        OpeningHours.objects.create(
            department=OpeningHours.DEPT.OFFICE,
            weekday=weekday,
            opens=time(9, 0),
            closes=time(17, 0),
        )

    course = Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-b",
        code="B",
        title="Kategoria B",
        lead="Kurs na prawo jazdy kategorii B.",
        entitlements="- samochód osobowy do 3,5 t",
        requirements="- ukończone 18 lat",
        min_age=18,
        theory_hours=30,
        practice_hours=30,
        price_gross=Decimal("3200"),
        is_active=True,
    )
    # A licence course with no price, which is what puts the quote tiles on the
    # price page. Without one the axe sweep never saw that block at all — and
    # it was the block where a white card on the purple band printed white on
    # white, invisible to the eye and to the gate alike.
    Course.objects.create(
        kind=Course.Kind.LICENSE,
        slug="kat-am",
        code="AM",
        title="Kategoria AM",
        lead="Motorower.",
        is_active=True,
    )
    Course.objects.create(
        kind=Course.Kind.PROFESSIONAL,
        slug="adr",
        code="ADR",
        title="ADR",
        lead="Przewóz towarów niebezpiecznych.",
        total_hours=24,
        is_active=True,
    )
    CourseIntake.objects.create(
        course=course,
        start_date=date.today() + timedelta(days=14),
        mode=CourseIntake.Mode.STATIONARY,
        language="pl",
        status=CourseIntake.Status.OPEN,
        seats_total=20,
        seats_taken=17,
    )
    PriceItem.objects.create(
        title="Jazda doszkalająca", group="Jazdy", price_gross=Decimal("120"), unit="za godzinę"
    )

    for slug, title in (("o-nas", "O nas"), ("rodo", "RODO")):
        FlatPage.objects.create(
            slug=slug,
            title=title,
            body="# Sekcja pierwsza\n\nTreść akapitu.\n\n# Sekcja druga\n\n- punkt",
            is_published=True,
        )

    Faq.objects.create(question="Ile trwa kurs?", answer="Około trzech miesięcy.")
    UsefulLink.objects.create(
        title="Info-Car", url="https://info-car.pl/", description="Rezerwacja egzaminu."
    )
    for index in range(2):
        Testimonial.objects.create(
            author_name=f"Anna {index}",
            rating=5,
            text="Zdałam za pierwszym razem.",
            source_url=f"https://example.com/{index}",
            is_published=True,
        )
    GalleryImageFactory(alt="Plac manewrowy")
    CertificateFactory(title="Certyfikat ADR")

    return settings_row
