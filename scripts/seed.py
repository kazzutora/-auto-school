"""The single source of demo data, DEV.md S0.8.

Idempotent: every row is written with update_or_create keyed on a natural key,
so running it twice changes nothing and creates no duplicates.

**Every fact in this file is transcribed from the school's own site**, tech.md
section 1 and OSTRYCHARZ.md part A. Nothing here is invented. Where the school
publishes no figure, the row carries a ``TODO_OWNER:`` marker and
``owner_data_gaps()`` reports it; ``pytest -m owner_data`` fails while the list
is not empty, and production does not ship until it is.

Two things this seed deliberately does not create:

* ``Testimonial`` rows. tech.md section 4.7 forbids invented reviews, and the
  school's "110 opinii, 96% bardzo dobrych" is prose with no source behind it.
  Real reviews arrive with a source_url or not at all, and the section on the
  page renders only when there are at least two.
* ``Instructor``, ``Vehicle`` and ``Certificate`` rows. The photographs on the
  old site are the school's property, not ours, and a placeholder person is
  worse than an absent section.
"""

from __future__ import annotations

import os
import pathlib
from decimal import Decimal

TODO = "TODO_OWNER:"

HEADING_ABOUT = "# Kim jesteśmy" + chr(10) + chr(10)


def _setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


# --------------------------------------------------------------------------
# sections


def seed_site_settings() -> None:
    """Contact details, tech.md section 1. Transcribed from oskostrycharz.pl."""
    from apps.core.models import SiteSettings

    site = SiteSettings.get_solo()
    site.legal_name = "OSK Ostrycharz — Ośrodek Szkolenia Kierowców"
    site.short_name = "OSK Ostrycharz"
    site.street = "ul. Asnyka 7"
    site.postal_code = "98-300"
    site.city = "Wieluń"
    # The school publishes no NIP and no founding year. Both stay empty rather
    # than guessed: a made up tax number reaches the DrivingSchool json-ld.
    site.nip = ""
    site.founded_year = None
    site.email = "oskostrycharz@poczta.onet.pl"
    site.phone_primary = "691 570 489"
    site.phone_secondary = ""
    site.phone_tertiary = ""
    # Town centre. The exact office pin is confirmed by the owner.
    site.map_lat = Decimal("51.220600")
    site.map_lng = Decimal("18.569700")
    site.facebook_url = "https://pl-pl.facebook.com/osrodekostrycharz/"
    site.youtube_url = "https://www.youtube.com/channel/UCbXki-U-CJjcQ36tZ5GZ4lw"
    site.youtube_video_url = "https://www.youtube.com/watch?v=abeQhB0RfV4"
    site.lead_notify_emails = "oskostrycharz@poczta.onet.pl"
    site.bank_account_public = False
    site.analytics_enabled = False
    site.save()


def seed_opening_hours() -> None:
    """The office answers by prior arrangement, which is a note, not a schedule.

    The school's own site says only "po wcześniejszym ustaleniu telefonicznym".
    Inventing 9-17 would be the one lie on the page a visitor can catch by
    turning up, so every day is closed and carries that sentence instead.
    """
    from apps.core.models import OpeningHours

    note = "Po wcześniejszym ustaleniu telefonicznym"
    for weekday in range(7):
        OpeningHours.objects.update_or_create(
            department=OpeningHours.DEPT.OFFICE,
            weekday=weekday,
            defaults={"opens": None, "closes": None, "note": note},
        )
    # No psychology lab at this school. The rows would render an empty table.
    OpeningHours.objects.filter(department=OpeningHours.DEPT.PSYCHOLOGY).delete()


# The legal requirements for category B are statute, identical for every school
# in Poland, so this copy carries over from the first project unchanged.
KAT_B_ENTITLEMENTS = "\n".join(
    (
        "- pojazdem samochodowym o dopuszczalnej masie całkowitej do 3,5 t",
        "- zespołem pojazdów o dmc do 3,5 t",
        "- ciągnikiem rolniczym",
        "- pojazdami kategorii AM",
    )
)

KAT_B_REQUIREMENTS = "\n".join(
    (
        "- ukończone 18 lat, kurs można rozpocząć trzy miesiące wcześniej",
        "- orzeczenie lekarskie o braku przeciwwskazań zdrowotnych",
        "- numer PKK z wieluńskiego starostwa",
        "- zgoda rodziców, jeżeli nie masz jeszcze 18 lat",
    )
)

KAT_B_BODY = "\n\n".join(
    (
        "## Kurs standardowy",
        "Zajęcia teoretyczne i praktyczne w tempie, które da się pogodzić ze "
        "szkołą albo pracą. Cena 3700 zł obejmuje pełen kurs kategorii B "
        "i dowóz na egzamin państwowy.",
        "## Kurs przyspieszony",
        "Ten sam program w dwa tygodnie, dla osób, które potrzebują prawa jazdy "
        "na konkretną datę. Cena 4300 zł.",
        "## Skrzynia automatyczna",
        "Jeżeli sprzęgło i zmiana biegów są tym, co blokuje Cię najbardziej, "
        "cały kurs możesz zrobić na automacie. Cena 4300 zł. Prawo jazdy "
        "zdobyte na automacie uprawnia do jazdy wyłącznie autem "
        "z automatyczną skrzynią biegów.",
    )
)


KAT_B_LEAD = (
    "Kurs na prawo jazdy kategorii B w Wieluniu — standardowy, "
    "przyspieszony w dwa tygodnie albo na skrzyni automatycznej."
)

# Fields the seed owns and rewrites on every run.
KAT_B_MANAGED: dict[str, object] = {
    "code": "B",
    "title": "Prawo jazdy kat. B",
    "lead": KAT_B_LEAD,
    "min_age": 18,
    # The school publishes prices but not the hour breakdown. The statutory
    # minimum is 30 h theory and 30 h practice, but what this school actually
    # runs is its own to state.
    "theory_hours": None,
    "practice_hours": None,
    "price_gross": Decimal("3700.00"),
    "price_note": "cena kursu standardowego, dowóz na egzamin w cenie",
    "languages": ["pl", "ru", "uk"],
    "is_active": True,
    "order": 10,
}

# Fields an editor curates in the admin. Written once, when the row is first
# created, so a rerun never overwrites somebody's work.
KAT_B_EDITORIAL: dict[str, object] = {
    "entitlements": KAT_B_ENTITLEMENTS,
    "requirements": KAT_B_REQUIREMENTS,
    "body": KAT_B_BODY,
}


def seed_courses() -> None:
    """One course. This school teaches category B and nothing else.

    create_defaults *replaces* defaults on creation rather than adding to it —
    Django 5.0 — so the create branch has to carry both dicts. Splitting them
    without merging leaves a freshly created row with no kind, no title and no
    price until somebody happens to run the seed a second time.
    """
    from apps.courses.models import Course

    Course.objects.update_or_create(
        slug="kat-b",
        defaults={"kind": Course.Kind.LICENSE, **KAT_B_MANAGED},
        create_defaults={"kind": Course.Kind.LICENSE, **KAT_B_MANAGED, **KAT_B_EDITORIAL},
    )

    # Anything the previous client sold and this one does not. Deactivated
    # rather than deleted, so a stray row in an existing database stops
    # answering instead of 404-ing halfway through a page.
    Course.objects.exclude(slug="kat-b").update(is_active=False)


# What every course variant buys, OSTRYCHARZ.md part A. The same four lines on
# all three, because the course is the same course — the variants differ by
# tempo and by gearbox, and that difference is the fifth line.
#
# The prices in the owner's mockup are 3700, 3900 and 4200. Two of those three
# are invented: this school charges 4300 for both the fast track and the
# automatic. ROSE.md A.3 — the look comes from the mockup, the numbers come
# from here.
COURSE_INCLUDES = (
    "Zajęcia teoretyczne i praktyczne w pełnym wymiarze",
    "Egzamin wewnętrzny przed państwowym",
    "Dowóz na egzamin państwowy — gratis",
    "Klimatyzowane auto z bogatym wyposażeniem",
)

# tech.md section 1, transcribed to the złoty. Group, title, note, unit, price,
# what it includes, and whether the pricing page presses it.
#
# The group name is what the pricing page splits on and what the home page reads
# as "the course itself", so it is not decoration.
#
# The basic course is the pressed one. The mockup presses its middle card and
# the fast track sat there for a while to match, but the badge reads
# "Najczęściej wybierany" — most often chosen — and that is a claim about what
# this school's customers do, not a layout preference. Nobody has told us the
# 4300 course outsells the 3700 one. BLOCKS.md B9, FRONTEND_FIXES.md X1 point 3
# and OSTRYCHARZ.md all put the badge on kat. B, and it stays there until the
# owner says otherwise — which they do by ticking another row in the admin.
PRICE_ITEMS: list[tuple[str, str, str, str, str, tuple[str, ...], bool]] = [
    (
        "Kurs",
        "Kurs kategorii B",
        "pełny kurs, dowóz na egzamin w cenie",
        "",
        "3700.00",
        (*COURSE_INCLUDES, "Tempo dopasowane do szkoły albo pracy"),
        True,
    ),
    (
        "Kurs",
        "Kurs przyspieszony",
        "ten sam program w dwa tygodnie",
        "",
        "4300.00",
        (*COURSE_INCLUDES, "Ten sam program w dwa tygodnie"),
        False,
    ),
    (
        "Kurs",
        "Skrzynia automatyczna",
        "cały kurs na automacie",
        "",
        "4300.00",
        (*COURSE_INCLUDES, "Cały kurs i egzamin na skrzyni automatycznej"),
        False,
    ),
    (
        "Jazdy doszkalające",
        "Jazda doszkalająca — manual",
        "",
        "za godzinę",
        "160.00",
        (),
        False,
    ),
    (
        "Jazdy doszkalające",
        "Jazda doszkalająca — manual, dla naszych kursantów",
        "cena dla osób, które robią u nas kurs",
        "za godzinę",
        "140.00",
        (),
        False,
    ),
    (
        "Jazdy doszkalające",
        "Jazda doszkalająca — automat",
        "",
        "za godzinę",
        "140.00",
        (),
        False,
    ),
    (
        "Opłaty zewnętrzne",
        "Badanie lekarskie",
        "opłata poza szkołą, u lekarza uprawnionego",
        "",
        "200.00",
        (),
        False,
    ),
    (
        "Opłaty zewnętrzne",
        "Egzamin państwowy",
        "opłata poza szkołą, w ośrodku egzaminowania",
        "",
        "230.00",
        (),
        False,
    ),
    (
        "Opłaty zewnętrzne",
        "Zaświadczenie o zameldowaniu",
        "opłata poza szkołą, w urzędzie gminy",
        "",
        "17.00",
        (),
        False,
    ),
    ("W cenie kursu", "Dowóz na egzamin", "w cenie kursu", "", "0.00", (), False),
]


def seed_price_items() -> None:
    from apps.courses.models import PriceItem

    for order, (group, title, note, unit, price, includes, featured) in enumerate(
        PRICE_ITEMS, start=10
    ):
        PriceItem.objects.update_or_create(
            title=title,
            defaults={
                "group": group,
                "unit": unit,
                "price_gross": Decimal(price),
                "note": note,
                "includes": "\n".join(includes),
                "featured": featured,
                "order": order,
                "is_active": True,
            },
        )

    # Whatever the previous client priced and this one does not.
    PriceItem.objects.exclude(title__in=[title for _, title, *_ in PRICE_ITEMS]).update(
        is_active=False
    )


def seed_pass_rates() -> None:
    """The school's own figures, tech.md section 1.

    One confirmed year: 92 candidates, 68 of them through at the first attempt.
    The site also carries images labelled 2019, 2020 and 2021, but the numbers
    inside them cannot be read from the page, so those years are not invented
    here — owner_data_gaps() asks for them instead.
    """
    from apps.core.models import PassRate

    PassRate.objects.update_or_create(
        year=CONFIRMED_PASS_RATE_YEAR,
        defaults={
            "students": 92,
            "passed_1st": 68,
            "passed_2nd": 16,
            "passed_3rd": 3,
            "passed_4th": 3,
            "note": "",
            "is_published": True,
        },
    )


# The site prints the figures without a year beside them. This is the year they
# were published under, and the owner confirms or corrects it.
CONFIRMED_PASS_RATE_YEAR = 2025

# The years the old site shows only as images: obrazy/galeria/statystyka/*.jpg.
UNREAD_PASS_RATE_YEARS = (2019, 2020, 2021)


# tech.md section 1: the five documents the old site offered for download. The
# pdf files themselves belong to the school and are not in this repository, so
# the rows are created empty and the selector keeps them off the page until the
# owner uploads one.
# The school's own two groups, kept from their old site.
BEFORE_START = "Pobierz przed rozpoczęciem kursu"
EXTRA_FILES = "Dodatkowe pliki"

# Title, description, group, and the pdf in data/documents/ — the school's own
# files, fetched from oskostrycharz.pl at the owner's request. The file names
# are theirs and are left alone: they are what every link anybody has ever
# shared points at, and data/legacy/redirects.csv maps those links here.
DOWNLOADS: list[tuple[str, str, str, str]] = [
    (
        "Regulamin",
        "Zasady szkolenia w naszym ośrodku. Do przeczytania przed startem.",
        BEFORE_START,
        "Regulamin_-_OSK_Ostrycharz.pdf",
    ),
    (
        "Umowa z kursantem",
        "Umowa, którą podpisujesz przy zapisie.",
        BEFORE_START,
        "umowa_z_kursantem_OSK_Ostrycharz.pdf",
    ),
    (
        "Oświadczenie dot. stanu zdrowia",
        "Wypełniasz przed pierwszymi zajęciami praktycznymi.",
        BEFORE_START,
        "oswiadczenie_dot_stanu_zdrowia.pdf",
    ),
    (
        "Wzór — opłata za egzamin",
        "Jak i gdzie opłacić egzamin państwowy.",
        EXTRA_FILES,
        "wzor_oplata_za_egzamin.pdf",
    ),
    (
        "Zgoda rodziców — osoby niepełnoletnie",
        "Podpisana przez oboje rodziców lub opiekunów.",
        EXTRA_FILES,
        "zgoda_rodzicow_niepelnoletni.pdf",
    ),
]

DOCUMENT_SOURCE = pathlib.Path(__file__).resolve().parents[1] / "data" / "documents"


# The county office's tables, as the school published them on their old site.
# Every caption is read off the scan itself rather than off the file name: the
# alt text on the old page had 2020_2 labelled with a paragraph of marketing
# copy, and the scan says it is the whole of 2020 rather than a quarter.
SCAN_SOURCE = pathlib.Path(__file__).resolve().parents[1] / "data" / "passrate-scans"

PASS_RATE_SCANS: list[tuple[int, str, str]] = [
    (2021, "I kwartał 2021", "2021_1.jpg"),
    (2020, "Cały 2020 rok", "2020_2.jpg"),
    (2020, "I kwartał 2020", "2020_1.jpg"),
    (2019, "IV kwartał 2019", "2019_4.jpg"),
    (2019, "III kwartał 2019", "2019_3.jpg"),
    (2019, "II kwartał 2019", "2019_2.jpg"),
]


def seed_pass_rate_scans() -> None:
    """One row per scan, with the image attached once.

    Same rule as the documents: a row that already has an image keeps it, so
    re-running the seed never overwrites what the owner uploaded.
    """
    from django.core.files import File

    from apps.core.models import PassRateScan

    for order, (year, title, filename) in enumerate(PASS_RATE_SCANS, start=10):
        row, _created = PassRateScan.objects.update_or_create(
            title=title,
            defaults={"year": year, "order": order, "is_published": True},
        )

        if row.image:
            continue

        source = SCAN_SOURCE / filename
        if not source.exists():
            print(f"  PassRateScan {title}: {filename} not in data/passrate-scans/")
            continue

        with source.open("rb") as handle:
            row.image.save(filename, File(handle), save=True)


def seed_downloads() -> None:
    """The rows, and the pdf on each of them.

    The file is attached only when the row has none: re-running the seed must
    not replace a pdf the owner uploaded in the admin with the copy that came
    off their old site. That is the whole idempotency rule of tech.md section
    12 applied to a file field.
    """
    from django.core.files import File

    from apps.core.models import DownloadFile

    for order, (title, description, group, filename) in enumerate(DOWNLOADS, start=10):
        row, _created = DownloadFile.objects.update_or_create(
            title=title,
            defaults={
                "description": description,
                "group": group,
                "order": order,
                "is_published": True,
            },
        )

        if row.file:
            continue

        source = DOCUMENT_SOURCE / filename
        if not source.exists():
            print(f"  DownloadFile {title}: {filename} not in data/documents/")
            continue

        with source.open("rb") as handle:
            row.file.save(filename, File(handle), save=True)


USEFUL_LINKS = [
    (
        "tests",
        "Zdamyto — testy na prawo jazdy",
        "Baza pytań egzaminacyjnych, z której korzystają nasi kursanci.",
        "https://www.zdamyto.com/",
    ),
    (
        "exam",
        "Sprawdź status PKK",
        "Info-Car: czy Twój Profil Kandydata na Kierowcę jest już gotowy.",
        "https://info-car.pl/infocar/prawo-jazdy/sprawdz-status.html",
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
        "local",
        "Starostwo Powiatowe w Wieluniu",
        "Tu odbierzesz numer PKK i gotowe prawo jazdy.",
        "https://powiat.wielun.pl/",
    ),
    (
        "local",
        "WORD Sieradz",
        "Ośrodek egzaminowania właściwy dla powiatu wieluńskiego.",
        "https://www.wordsieradz.pl/",
    ),
]


# Eight questions, every answer drawn from a figure the school publishes. A
# question whose answer we would have to guess is not asked.
FAQS = [
    (
        "Ile kosztuje kurs na prawo jazdy kategorii B?",
        "Kurs standardowy kosztuje 3700 zł. Kurs przyspieszony, w dwa tygodnie, "
        "oraz kurs na skrzyni automatycznej — po 4300 zł. To ceny brutto, "
        "bez ukrytych dopłat.",
    ),
    (
        "Ile trwa kurs przyspieszony?",
        "Dwa tygodnie. Program jest ten sam co w kursie standardowym, "
        "różni się tylko tempo. Kosztuje 4300 zł.",
    ),
    (
        "Czy można zrobić kurs na automacie?",
        "Tak. Cały kurs na skrzyni automatycznej kosztuje 4300 zł. Pamiętaj, "
        "że prawo jazdy zdobyte na automacie uprawnia do jazdy wyłącznie "
        "autem z automatyczną skrzynią biegów.",
    ),
    (
        "Ile kosztuje jazda doszkalająca?",
        "Manual — 160 zł za godzinę, a dla osób, które robią u nas kurs, "
        "140 zł. Automat — 140 zł za godzinę.",
    ),
    (
        "Czy dowozicie na egzamin?",
        "Tak, i jest to w cenie kursu. Zdajesz autem, którym u nas jeździsz.",
    ),
    (
        "Od ilu lat można zacząć kurs?",
        "Kurs możesz rozpocząć trzy miesiące przed osiemnastymi urodzinami, "
        "czyli od 17 lat i 9 miesięcy. Osoby niepełnoletnie przynoszą "
        "zgodę rodziców.",
    ),
    (
        "Jakie dokumenty są potrzebne do zapisu?",
        "Orzeczenie lekarskie, fotografia 3,5 x 4,5 cm, dowód osobisty lub "
        "paszport, zaświadczenie o zameldowaniu (17 zł) oraz zgoda rodziców "
        "w przypadku osób niepełnoletnich.",
    ),
    (
        "Jak wyrobić PKK?",
        "Profil Kandydata na Kierowcę zakłada Starostwo Powiatowe w Wieluniu "
        "na podstawie orzeczenia lekarskiego, zdjęcia i dowodu osobistego. "
        "Numer PKK podajesz nam przy zapisie.",
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
    UsefulLink.objects.exclude(url__in=[url for *_, url in USEFUL_LINKS]).update(is_active=False)

    for order, (question, answer) in enumerate(FAQS, start=10):
        Faq.objects.update_or_create(
            question=question,
            defaults={"answer": answer, "order": order, "is_published": True},
        )
    Faq.objects.exclude(question__in=[question for question, _ in FAQS]).update(is_published=False)


# tech.md section 1: transcribed word for word from the school's own page.
ABOUT_BODY = HEADING_ABOUT + "\n\n".join(
    (
        "Nasza szkoła jest firmą z dużym doświadczeniem w zakresie szkolenia "
        "przyszłych kierowców kat. B. Pracujący u nas instruktorzy posiadają "
        "wiedzę i kwalifikacje na wysokim poziomie, dzięki doświadczeniu "
        "zdobytemu przez lata praktyki.",
        "Możemy pochwalić się jedną z najwyższych zdawalności w województwie "
        "łódzkim. Posiadamy samochody z bogatym wyposażeniem — klimatyzowane!",
        "Gorąco pozdrawiamy — Kierownictwo Szkoły.",
    )
)

ENROL_BODY = "\n\n".join(
    (
        "# Zapisy",
        "Zapisy prowadzimy po wcześniejszym ustaleniu telefonicznym pod numerem "
        "691 570 489. Dzwoniąc, umówimy termin startu i powiemy, ile potrwa "
        "kompletowanie papierów.",
        "# Dokumenty",
        "- orzeczenie lekarskie",
        "- fotografia 3,5 x 4,5 cm",
        "- dowód osobisty / paszport",
        "- zaświadczenie o zameldowaniu (17 zł)",
        "- zgoda rodziców (osoby niepełnoletnie)",
        "# Badanie lekarskie",
        "Orzeczenie o braku przeciwwskazań zdrowotnych do kierowania pojazdami "
        "kosztuje 200 zł i jest opłatą poza szkołą.",
    )
)


def seed_pages() -> None:
    from apps.core.models import Page

    pages = [
        (
            "o-nas",
            "O nas",
            "Szkolimy kierowców kategorii B w Wieluniu. Jedna z najwyższych "
            "zdawalności w województwie łódzkim.",
            ABOUT_BODY,
        ),
        (
            "zapisy",
            "Zapisy i dokumenty",
            "Jak się zapisać i co przynieść. Pięć kroków, pięć dokumentów, jeden telefon.",
            ENROL_BODY,
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
    """Everything the owner still owes, tech.md section 16.

    This is the list that goes in the letter under "czego brakuje". Every entry
    is something the school has but has not given us, never something we could
    have written ourselves.
    """
    from apps.core.models import DownloadFile, Page, PassRate, SiteSettings
    from apps.courses.models import Course
    from apps.reviews.models import Testimonial

    gaps: list[str] = []

    def note(count: int, what: str) -> None:
        if count:
            gaps.append(f"{count} x {what}")

    site = SiteSettings.get_solo()
    if not site.nip:
        gaps.append("1 x SiteSettings.nip: not published on the old site, ask the owner")
    if site.founded_year is None:
        gaps.append("1 x SiteSettings.founded_year: never stated, ask the owner")
    if not site.google_business_url:
        gaps.append("1 x SiteSettings.google_business_url missing")
    if not site.youtube_poster:
        gaps.append("1 x SiteSettings.youtube_poster: a still frame for the home page clip")

    note(
        _office_hours_gap(),
        "OpeningHours: the office answers by arrangement only, real hours unconfirmed",
    )
    note(
        Course.objects.filter(is_active=True, theory_hours__isnull=True).count(),
        "Course.theory_hours: the school publishes prices but not the hour breakdown",
    )
    note(
        Course.objects.filter(is_active=True, practice_hours__isnull=True).count(),
        "Course.practice_hours unconfirmed",
    )
    note(
        len(UNREAD_PASS_RATE_YEARS)
        - PassRate.objects.filter(year__in=UNREAD_PASS_RATE_YEARS).count(),
        "PassRate: 2019-2021 exist only as images on the old site, ask for the figures",
    )
    note(
        PassRate.objects.filter(year=CONFIRMED_PASS_RATE_YEAR).count(),
        f"PassRate: confirm {CONFIRMED_PASS_RATE_YEAR} is the right year for 92/68/16/3/3",
    )
    if PassRate.objects.filter(year=CONFIRMED_PASS_RATE_YEAR, students=92, passed_1st=68).exists():
        gaps.append(
            "1 x PassRate: the old site prints 76% for the first attempt, which is 68 of the "
            "90 who eventually passed. This site prints 68 of the 92 who sat, which is 74%. "
            "Ask the owner which denominator they mean, and what happened to the other 2"
        )
    note(
        DownloadFile.objects.filter(file="").count(),
        "DownloadFile: pdf not uploaded yet, the row stays off the page",
    )
    note(
        Testimonial.objects.filter(is_published=True, source_url="").count(),
        "Testimonial published without a source_url, which is not allowed",
    )
    if not Testimonial.objects.filter(is_published=True).exists():
        gaps.append("1 x Testimonial: no verifiable reviews yet, the section stays hidden")
    note(Page.objects.filter(body__contains=TODO).count(), "Page body unconfirmed")
    gaps.append("1 x photographs: cars, lessons, the office — none are ours to publish")

    return gaps


def _office_hours_gap() -> int:
    """1 while every office day is closed with only the arrangement note on it."""
    from apps.core.models import OpeningHours

    office = OpeningHours.objects.filter(department=OpeningHours.DEPT.OFFICE)
    return 1 if office.exists() and not office.exclude(opens=None).exists() else 0


# --------------------------------------------------------------------------


def run() -> None:
    """Fill the database. Safe to run any number of times."""
    seed_site_settings()
    seed_opening_hours()
    seed_courses()
    seed_price_items()
    seed_pass_rates()
    seed_pass_rate_scans()
    seed_downloads()
    seed_links()
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
