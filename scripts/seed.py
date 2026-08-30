"""The single source of demo data, DEV.md S0.8.

Idempotent: every row is written with update_or_create keyed on a natural key,
so running it twice changes nothing and creates no duplicates.

Values the owner has not supplied yet (tech.md section 16) are seeded as
plausible placeholders and marked so they can be listed:

* text fields carry the ``TODO_OWNER:`` prefix;
* media files are named ``todo_owner_*``;
* genuinely unknown numbers stay NULL.

``owner_data_gaps()`` turns all of that into a report. ``pytest -m owner_data``
fails while the list is not empty, and production does not ship until it is.
"""

from __future__ import annotations

import os
from datetime import date, time, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any

# What a licence course asks for before anything else. Seeded only when the
# course is new: the real list comes from data/legacy through import_legacy.
# The about page opens on one section; what it offers is a card grid now,
# BLOCKS.md B5, so the bulleted copy of the same navigation has gone.
HEADING_ABOUT = "# Kim jesteśmy" + chr(10) + chr(10)

BASIC_REQUIREMENTS = chr(10).join(
    ("- ukończone {age} lat", "- orzeczenie lekarskie", "- numer PKK")
)

TODO = "TODO_OWNER:"
PLACEHOLDER_PREFIX = "todo_owner_"

# Stand-in values for content the owner has not supplied. They used to carry
# the TODO_OWNER prefix, which meant the word TODO was printed at visitors on
# the price list, the FAQ and every instructor card — the marker is for us, and
# a demo the owner is looking at should still read like a website.
#
# owner_data_gaps() keys on these exact strings instead of on a prefix, so
# nothing is lost: the report still lists every one of them.
DEMO_INSTRUCTOR = "Instruktor"
DEMO_VEHICLE = "Pojazd"
DEMO_CERTIFICATE = "Certyfikat"
DEMO_REVIEW = "Opinia"


def _setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


# --------------------------------------------------------------------------
# helpers


def _placeholder(name: str, label: str) -> Any:
    """A branded stand-in image, so the pipeline is exercised end to end."""
    from django.core.files.base import ContentFile
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (960, 640), "#EBE6F8")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 560, 960, 640), fill="#2A1F55")
    draw.text((24, 590), label[:60], fill="#FFD400")
    draw.text((24, 24), "TODO_OWNER", fill="#5B47A8")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{PLACEHOLDER_PREFIX}{name}.png")


def _attach_placeholder(obj: Any, field: str, name: str, label: str) -> None:
    """Attach once. Re-saving on every run would pile up suffixed copies."""
    if getattr(obj, field):
        return
    getattr(obj, field).save(
        f"{PLACEHOLDER_PREFIX}{name}.png", _placeholder(name, label), save=True
    )


# --------------------------------------------------------------------------
# sections


def seed_site_settings() -> None:
    from apps.core.models import SiteSettings

    site = SiteSettings.get_solo()
    site.legal_name = (
        "Ośrodek Kształcenia i Doskonalenia Zawodowego Adam Nawrocki, Mariola Nawrocka S.C."
    )
    site.short_name = "OSK Nawrocki"
    site.street = "ul. Zielona 45"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    site.nip = "8321916014"
    site.email = "osk.adam.nawrocki@wp.pl"
    site.phone_primary = "43 843 29 11"
    site.phone_secondary = "605 065 795"
    site.phone_tertiary = "667 615 184"
    site.founded_year = 1996
    # Town centre. The exact office pin is confirmed by the owner.
    site.map_lat = Decimal("51.220600")
    site.map_lng = Decimal("18.569700")
    site.lead_notify_emails = "osk.adam.nawrocki@wp.pl"
    site.bank_account_public = False
    site.analytics_enabled = False
    site.save()


def seed_opening_hours() -> None:
    """Psychology hours are known, tech.md section 16. Office hours are not."""
    from apps.core.models import OpeningHours

    for weekday in range(7):
        # Tuesday and Friday 8:00-16:00, the one schedule we actually have.
        psychology = weekday in (1, 4)
        OpeningHours.objects.update_or_create(
            department=OpeningHours.DEPT.PSYCHOLOGY,
            weekday=weekday,
            defaults={
                "opens": time(8, 0) if psychology else None,
                "closes": time(16, 0) if psychology else None,
                "note": "",
            },
        )
        OpeningHours.objects.update_or_create(
            department=OpeningHours.DEPT.OFFICE,
            weekday=weekday,
            defaults={
                "opens": time(9, 0) if weekday < 5 else None,
                "closes": time(17, 0) if weekday < 5 else None,
                "note": "",
            },
        )


LICENSE_COURSES = [
    ("kat-am", "AM", "Kategoria AM", 14, "motorower i czterokołowiec lekki"),
    ("kat-a1", "A1", "Kategoria A1", 16, "motocykl do 125 cm3"),
    ("kat-a2", "A2", "Kategoria A2", 18, "motocykl o mocy do 35 kW"),
    ("kat-a", "A", "Kategoria A", 24, "motocykl bez ograniczeń"),
    ("kat-b", "B", "Kategoria B", 18, "samochód osobowy do 3,5 t"),
    ("kat-be", "B+E", "Kategoria B+E", 18, "samochód osobowy z przyczepą"),
    ("kat-c", "C", "Kategoria C", 21, "samochód ciężarowy powyżej 3,5 t"),
    ("kat-ce", "C+E", "Kategoria C+E", 21, "samochód ciężarowy z przyczepą"),
    ("kat-d", "D", "Kategoria D", 24, "autobus"),
]

PROFESSIONAL_COURSES = [
    ("szkolenia-okresowe", "", "Szkolenia okresowe", "odnowienie uprawnień kierowcy zawodowego"),
    (
        "kwalifikacja-wstepna",
        "",
        "Kwalifikacja wstępna",
        "pełna kwalifikacja dla kierowcy zawodowego",
    ),
    (
        "kwalifikacja-wstepna-przyspieszona",
        "",
        "Kwalifikacja wstępna przyspieszona",
        "skrócony wariant kwalifikacji wstępnej",
    ),
    ("adr", "ADR", "Kurs ADR", "przewóz towarów niebezpiecznych"),
]


def seed_courses() -> None:
    """9 license categories, 4 professional, psychotests and forklifts."""
    from apps.courses.models import Course

    for order, (slug, code, title, min_age, entitlement) in enumerate(LICENSE_COURSES, start=10):
        Course.objects.update_or_create(
            slug=slug,
            defaults={
                "kind": Course.Kind.LICENSE,
                "code": code,
                "title": title,
                "min_age": min_age,
                # Hours and prices are owner data, tech.md section 16.
                "theory_hours": None,
                "practice_hours": None,
                "price_gross": None,
                "price_note": "",
                "languages": ["pl"],
                "is_active": True,
                "order": order,
            },
            create_defaults={
                # Written only when the course does not exist yet.
                #
                # These three belong to import_legacy, which reads the real
                # text out of data/legacy. In `defaults` they were rewritten on
                # every seed run, so an imported list of four entitlements came
                # back as one templated line — which is exactly what the review
                # found on kat-b and blamed on the importer.
                "lead": f"Kurs prawa jazdy {title.lower()} w Wieluniu.",
                "entitlements": f"- {entitlement}",
                "requirements": BASIC_REQUIREMENTS.format(age=min_age),
            },
        )

    for order, (slug, code, title, lead) in enumerate(PROFESSIONAL_COURSES, start=10):
        Course.objects.update_or_create(
            slug=slug,
            defaults={
                "kind": Course.Kind.PROFESSIONAL,
                "code": code,
                "title": title,
                "lead": f"{title}: {lead}.",
                "price_gross": None,
                "price_note": "",
                "languages": ["pl"],
                "is_active": True,
                "order": order,
            },
        )

    Course.objects.update_or_create(
        slug="badania-psychologiczne",
        defaults={
            "kind": Course.Kind.PSYCHOTEST,
            "title": "Badania psychologiczne",
            "lead": "Badania psychologiczne dla kierowców i operatorów.",
            "body": "Pracownia czynna we wtorki i piątki w godzinach 8:00-16:00.",
            "price_gross": None,
            "price_note": "",
            "languages": ["pl"],
            "is_active": True,
            "order": 10,
        },
    )
    Course.objects.update_or_create(
        slug="wozki-widlowe",
        defaults={
            "kind": Course.Kind.OPERATOR,
            "title": "Wózki widłowe",
            "lead": "Uprawnienia operatora wózków jezdniowych podnośnikowych.",
            "price_gross": None,
            "price_note": "",
            "languages": ["pl"],
            "is_active": True,
            "order": 10,
        },
    )


def seed_intakes() -> None:
    """Six upcoming group starts. The real dates come from the owner."""
    from apps.courses.models import Course, CourseIntake

    plan = [
        ("kat-b", 14, CourseIntake.Mode.STATIONARY, "pl", CourseIntake.Status.OPEN),
        ("kat-b", 45, CourseIntake.Mode.MIXED, "pl", CourseIntake.Status.PLANNED),
        ("kat-c", 21, CourseIntake.Mode.STATIONARY, "pl", CourseIntake.Status.OPEN),
        ("kwalifikacja-wstepna", 30, CourseIntake.Mode.MIXED, "pl", CourseIntake.Status.PLANNED),
        ("adr", 60, CourseIntake.Mode.STATIONARY, "pl", CourseIntake.Status.PLANNED),
        ("wozki-widlowe", 10, CourseIntake.Mode.STATIONARY, "pl", CourseIntake.Status.FULL),
    ]
    today = date.today()
    for slug, offset, mode, language, status in plan:
        course = Course.objects.get(slug=slug)
        CourseIntake.objects.update_or_create(
            course=course,
            start_date=today + timedelta(days=offset),
            language=language,
            defaults={
                "mode": mode,
                "status": status,
                "seats_total": 20,
                "seats_taken": 0,
                "note": "",
            },
        )


def seed_price_items() -> None:
    from apps.courses.models import PriceItem

    items = [
        ("Jazda doszkalająca kat. B", "Jazdy doszkalające", "za godzinę", "120.00"),
        ("Jazda doszkalająca kat. C", "Jazdy doszkalające", "za godzinę", "180.00"),
        ("Egzamin wewnętrzny teoretyczny", "Egzaminy", "za osobę", "50.00"),
        ("Egzamin wewnętrzny praktyczny", "Egzaminy", "za osobę", "100.00"),
        ("Badanie psychologiczne kierowcy", "Badania", "za osobę", "150.00"),
        ("Wynajem pojazdu na egzamin", "Pozostałe", "za godzinę", "200.00"),
    ]
    for order, (title, group, unit, price) in enumerate(items, start=10):
        PriceItem.objects.update_or_create(
            title=title,
            defaults={
                "group": group,
                "unit": unit,
                "price_gross": Decimal(price),
                "note": "",
                "order": order,
                "is_active": True,
            },
        )


def seed_people() -> None:
    from apps.courses.models import Course
    from apps.people.models import Instructor, Vehicle

    for number in range(1, 5):
        instructor, _ = Instructor.objects.update_or_create(
            full_name=f"{DEMO_INSTRUCTOR} {number}",
            defaults={
                "role": "Instruktor nauki jazdy",
                "bio": "",
                "since_year": None,
                "order": number * 10,
                "is_active": True,
            },
        )
        _attach_placeholder(instructor, "photo", f"instructor_{number}", "Instruktor")

    kat_b = Course.objects.get(slug="kat-b")
    for number in range(1, 6):
        vehicle, _ = Vehicle.objects.update_or_create(
            course=kat_b,
            make=DEMO_VEHICLE,
            model=f"szkoleniowy {number}",
            defaults={
                "year": None,
                "gearbox": Vehicle.Gearbox.MANUAL,
                "note": "",
                "is_exam_spec": True,
                "order": number * 10,
                "is_active": True,
            },
        )
        _attach_placeholder(vehicle, "photo", f"vehicle_{number}", "Pojazd")


def seed_gallery() -> None:
    from apps.gallery.models import Certificate, GalleryImage

    sections = [
        (GalleryImage.Section.SCHOOL, "Biuro ośrodka szkolenia kierowców", 3),
        (GalleryImage.Section.VEHICLES, "Pojazd szkoleniowy", 3),
        (GalleryImage.Section.YARD, "Plac manewrowy", 3),
        (GalleryImage.Section.EVENTS, "Zajęcia praktyczne", 3),
    ]
    counter = 0
    for section, alt_base, how_many in sections:
        for number in range(1, how_many + 1):
            counter += 1
            image, _ = GalleryImage.objects.update_or_create(
                legacy_name=f"{counter}.JPG",
                defaults={
                    "section": section,
                    "alt": f"{alt_base} {number}",
                    "caption": "",
                    "order": counter * 10,
                    "is_published": True,
                },
            )
            _attach_placeholder(image, "image", f"gallery_{counter}", alt_base)

    for number in range(1, 12):
        certificate, _ = Certificate.objects.update_or_create(
            order=number * 10,
            defaults={
                "title": f"{DEMO_CERTIFICATE} {number}",
                "issuer": "",
                "issued_on": None,
                "description": "",
                "is_published": True,
            },
        )
        _attach_placeholder(certificate, "image", f"certificate_{number}", "Certyfikat")


USEFUL_LINKS = [
    (
        "exam",
        "Info-Car",
        "Rezerwacja terminu egzaminu państwowego i sprawdzenie statusu PKK.",
        "https://info-car.pl/",
    ),
    (
        "gov",
        "Sprawdź punkty karne",
        "Usługa gov.pl: liczba punktów karnych po zalogowaniu profilem zaufanym.",
        "https://www.gov.pl/web/gov/sprawdz-punkty-karne",
    ),
    (
        "gov",
        "Uzyskaj prawo jazdy",
        "Opis procedury krok po kroku: PKK, badania, egzamin, odbiór dokumentu.",
        "https://www.gov.pl/web/gov/uzyskaj-prawo-jazdy",
    ),
    (
        "gov",
        "Sprawdź swoje prawo jazdy",
        "Status dokumentu i uprawnień kierowcy w usłudze gov.pl.",
        "https://www.gov.pl/web/gov/sprawdz-swoje-prawo-jazdy",
    ),
    (
        "gov",
        "Ministerstwo Infrastruktury",
        "Przepisy i komunikaty dotyczące szkolenia kierowców.",
        "https://www.gov.pl/web/infrastruktura",
    ),
    (
        "gov",
        "Mój Pojazd i Kierowca",
        "Dane pojazdu i uprawnień w jednym miejscu.",
        "https://www.gov.pl/web/gov/moj-pojazd",
    ),
    (
        "local",
        "Starostwo Powiatowe w Wieluniu",
        "Tu odbierzesz numer PKK i gotowe prawo jazdy.",
        "https://powiat.wielun.pl/",
    ),
    (
        "local",
        "Urząd Miejski w Wieluniu",
        "Sprawy urzędowe mieszkańców Wielunia.",
        "https://www.wielun.pl/",
    ),
    (
        "local",
        "WORD Sieradz",
        "Ośrodek egzaminowania właściwy dla powiatu wieluńskiego.",
        "https://www.wordsieradz.pl/",
    ),
    (
        "tests",
        "Testy na prawo jazdy gov.pl",
        "Oficjalna baza pytań egzaminacyjnych.",
        "https://www.gov.pl/web/infrastruktura/testy-na-prawo-jazdy",
    ),
    (
        "exam",
        "Kodeks drogowy w ISAP",
        "Aktualny tekst ustawy Prawo o ruchu drogowym.",
        "https://isap.sejm.gov.pl/",
    ),
    (
        "tests",
        "Znaki drogowe",
        "Rozporządzenie o znakach i sygnałach drogowych.",
        "https://www.gov.pl/web/infrastruktura/znaki-i-sygnaly-drogowe",
    ),
]


def seed_links() -> None:
    from apps.links.models import Faq, UsefulLink

    for order, (group, title, description, url) in enumerate(USEFUL_LINKS, start=10):
        UsefulLink.objects.update_or_create(
            url=url,
            defaults={
                "group": group,
                "title": title,
                "description": description,
                "order": order,
                "is_active": True,
            },
        )

    faqs = [
        (
            "Ile trwa kurs na prawo jazdy kategorii B?",
            "Liczbę godzin teorii i praktyki potwierdzamy telefonicznie.",
        ),
        (
            "Od jakiego wieku mogę zapisać się na kurs kategorii B?",
            "Kurs możesz rozpocząć trzy miesiące przed osiemnastymi urodzinami.",
        ),
        (
            "Czy zajęcia są prowadzone po rosyjsku?",
            "O zajęcia po rosyjsku zapytaj przez telefon.",
        ),
        (
            "Co to jest PKK i gdzie go otrzymam?",
            "Profil Kandydata na Kierowcę wydaje Starostwo Powiatowe w Wieluniu.",
        ),
        (
            "Jakie dokumenty są potrzebne do zapisu?",
            "Dowód tożsamości, orzeczenie lekarskie i numer PKK.",
        ),
        (
            "Ile kosztuje kurs?",
            "Aktualny cennik podajemy telefonicznie i w biurze.",
        ),
        (
            "Kiedy rusza najbliższy kurs?",
            "Najbliższe terminy podajemy telefonicznie.",
        ),
        (
            "Czy prowadzicie badania psychologiczne?",
            "Tak. Pracownia jest czynna we wtorki i piątki w godzinach 8:00-16:00.",
        ),
    ]
    for order, (question, answer) in enumerate(faqs, start=10):
        Faq.objects.update_or_create(
            question=question,
            defaults={"answer": answer, "order": order, "is_published": True},
        )


def seed_reviews() -> None:
    """Placeholders only, and never published.

    tech.md section 4.7 forbids synthetic reviews, so these carry the marker and
    stay unpublished until real ones with a source_url arrive.
    """
    from apps.reviews.models import Testimonial

    for number, rating in enumerate([5, 5, 4], start=1):
        Testimonial.objects.update_or_create(
            author_name=f"{DEMO_REVIEW} {number}",
            defaults={
                "rating": rating,
                # The marker stays here, and only here. tech.md section 4.7 forbids
                # invented reviews, and test_no_synthetic_review_can_reach_a_page
                # proves a placeholder is one by this prefix. These rows are
                # unpublished, so nothing of it reaches a visitor.
                "text": f"{TODO} prawdziwa opinia z podanym source_url",
                "source": Testimonial.Source.MANUAL,
                "source_url": "",
                "published_on": None,
                "is_published": False,
                "order": number * 10,
            },
        )


def seed_pages() -> None:
    from apps.core.models import Page

    pages = [
        (
            "o-nas",
            "O nas",
            "Jesteśmy firmą rodzinną, szkolimy kierowców w Wieluniu od 1996 roku.",
            HEADING_ABOUT
            + "Rodzinny ośrodek szkolenia kierowców w Wieluniu. "
            + "Uczymy od 1996 roku, zajęcia prowadzimy także po rosyjsku.",
        ),
        (
            "polityka-prywatnosci",
            "Polityka prywatności",
            "Jak przetwarzamy dane osobowe kandydatów na kierowców.",
            f"# Administrator danych\n\n{TODO} pełna treść polityki do zatwierdzenia.",
        ),
        (
            "rodo",
            "RODO",
            "Obowiązek informacyjny zgodny z RODO.",
            f"# Obowiązek informacyjny\n\n{TODO} pełna treść klauzuli do zatwierdzenia.",
        ),
    ]
    for slug, title, lead, body in pages:
        Page.objects.update_or_create(
            slug=slug,
            defaults={"title": title, "lead": lead, "body": body, "is_published": True},
        )


# --------------------------------------------------------------------------
# report


def owner_data_gaps() -> list[str]:
    """Everything the owner still owes, tech.md section 16."""
    from apps.core.models import OpeningHours, Page, SiteSettings
    from apps.courses.models import Course, CourseIntake, PriceItem
    from apps.gallery.models import Certificate, GalleryImage
    from apps.links.models import Faq
    from apps.people.models import Instructor, Vehicle
    from apps.reviews.models import Testimonial

    gaps: list[str] = []

    def note(count: int, what: str) -> None:
        if count:
            gaps.append(f"{count} x {what}")

    note(Course.objects.filter(price_gross__isnull=True).count(), "Course.price_gross missing")
    note(
        Course.objects.filter(kind=Course.Kind.LICENSE, theory_hours__isnull=True).count(),
        "Course.theory_hours missing",
    )
    note(
        Course.objects.filter(kind=Course.Kind.LICENSE, practice_hours__isnull=True).count(),
        "Course.practice_hours missing",
    )
    note(
        Course.objects.exclude(languages__contains=["ru"]).count(),
        "Course.languages: which courses run in russian is unconfirmed",
    )
    note(
        OpeningHours.objects.filter(department=OpeningHours.DEPT.OFFICE, note="").count(),
        "OpeningHours office schedule unconfirmed",
    )
    note(CourseIntake.objects.filter(note="").count(), "CourseIntake start unconfirmed")
    note(PriceItem.objects.filter(note="").count(), "PriceItem price unconfirmed")
    note(
        Instructor.objects.filter(full_name__startswith=DEMO_INSTRUCTOR).count(),
        "Instructor unknown",
    )
    note(Vehicle.objects.filter(make=DEMO_VEHICLE).count(), "Vehicle unknown")
    note(
        Certificate.objects.filter(title__startswith=DEMO_CERTIFICATE).count(),
        "Certificate caption missing",
    )
    note(
        GalleryImage.objects.filter(image__contains=PLACEHOLDER_PREFIX).count(),
        "GalleryImage still a placeholder file",
    )
    note(
        Faq.objects.filter(answer__contains="potwierdzamy telefonicznie").count()
        + Faq.objects.filter(answer__contains="podajemy telefonicznie").count()
        + Faq.objects.filter(answer__contains="zapytaj przez telefon").count(),
        "Faq answer unconfirmed",
    )
    note(
        Testimonial.objects.filter(author_name__startswith=DEMO_REVIEW).count(),
        "Testimonial is a placeholder, real ones need a source_url",
    )
    note(Page.objects.filter(body__contains=TODO).count(), "Page body unconfirmed")

    site = SiteSettings.get_solo()
    if not site.facebook_url:
        gaps.append("1 x SiteSettings.facebook_url missing")
    if not site.google_business_url:
        gaps.append("1 x SiteSettings.google_business_url missing")

    return gaps


# --------------------------------------------------------------------------


def run() -> None:
    """Fill the database. Safe to run any number of times."""
    seed_site_settings()
    seed_opening_hours()
    seed_courses()
    seed_intakes()
    seed_price_items()
    seed_people()
    seed_gallery()
    seed_links()
    seed_reviews()
    seed_pages()
    # Last: it writes only the _ru and _uk columns of rows the steps above
    # created, so it has nothing to work on until they have run.
    from scripts import seed_translations

    seed_translations.run()


def main() -> None:
    _setup()
    run()
    gaps = owner_data_gaps()
    print(f"seed done, {len(gaps)} owner data gaps")
    for gap in gaps:
        print(f"  {gap}")


if __name__ == "__main__":
    main()
