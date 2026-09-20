"""Core views."""

from datetime import date
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

from django import forms
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.markdown import render_markdown
from apps.core.models import Page, PassRate, SiteSettings
from apps.core.seo import Label, Seo, build_title, page_seo
from apps.core.services import (
    attempt_percents,
    average_attempts,
    first_attempt_percent,
    human_size,
    not_passed,
    youtube_id,
)

_PLACEHOLDER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">'
    '<rect width="400" height="400" fill="#F2F2F1"/>'
    '<text x="200" y="210" font-family="sans-serif" font-size="28" fill="#5C5C66"'
    ' text-anchor="middle">OSK</text></svg>'
)
PLACEHOLDER = "data:image/svg+xml," + quote(_PLACEHOLDER_SVG)


class KitchenSinkForm(forms.Form):
    """Only used by the kitchen sink, to render c-field against a real BoundField."""

    first_name = forms.CharField(label="Imię", max_length=80)
    email = forms.EmailField(label="E-mail", help_text="Odpowiemy w ciągu jednego dnia roboczego")
    consent_rodo = forms.BooleanField(label="Zgadzam się na przetwarzanie danych")


def _sample_image(alt: str, caption: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        image=SimpleNamespace(url=PLACEHOLDER, webp=None), alt=alt, caption=caption
    )


def kitchen_sink(request: HttpRequest) -> HttpResponse:
    """Every cotton primitive in every prop variant, DEV.md S0.7.

    Debug only: it is a review surface for the design system, not a page.
    """
    from django.conf import settings

    if not settings.DEBUG:
        raise Http404

    def _course(code: str, title: str, min_age: int, price: str | None) -> SimpleNamespace:
        return SimpleNamespace(
            code=code,
            title=title,
            slug=code.lower().replace("+", "-"),
            get_absolute_url=f"/kursy/kat-{code.lower()}/",
            min_age=min_age,
            price_gross=price,
        )

    courses = [
        _course("B", "Kurs standardowy", 18, "3700.00"),
        _course("B", "Kurs przyspieszony", 18, "4300.00"),
        _course("B", "Skrzynia automatyczna", 18, "4300.00"),
    ]
    intakes = [
        SimpleNamespace(
            id=index,
            start_date=date(2026, 9, 14),
            course=SimpleNamespace(title="Kategoria B"),
            get_mode_display=lambda: "Stacjonarny",
            language="pl",
            status=status,
            note="Zajęcia po rosyjsku" if status == "planned" else "",
        )
        for index, status in enumerate(("open", "full", "closed", "planned"), start=1)
    ]
    images = [_sample_image(f"Plac manewrowy {n}", f"Podpis {n}") for n in range(1, 7)]
    testimonials = [
        SimpleNamespace(
            author_name="Anna K.",
            rating=rating,
            text="Instruktor tłumaczy spokojnie i konkretnie. Zdałam za pierwszym razem.",
            published_on=date(2026, 5, 1),
            source_url="https://example.com/opinia",
        )
        for rating in (5, 4, 3)
    ]
    sample_year = SimpleNamespace(
        year=2025, students=92, passed_1st=68, passed_2nd=16, passed_3rd=3, passed_4th=3, note=""
    )

    context: dict[str, Any] = {
        "seo": Seo(
            title=build_title("Kitchen sink"),
            description="Podgląd wszystkich komponentów UI.",
            canonical=request.build_absolute_uri(),
            robots="noindex,nofollow",
        ),
        # Distinct auto_id per rendering: this page shows three forms that share
        # field names, and one id used twice makes a label focus the other copy.
        "form": KitchenSinkForm(auto_id="ks_empty_%s"),
        "bound_form": KitchenSinkForm(
            data={"first_name": "", "email": "nie-email"}, auto_id="ks_bound_%s"
        ),
        # FRONTEND.md F7 wants all six form states on this page.
        "lead_form": _lead_form(),
        "courses": courses,
        "intakes": intakes,
        "images": images,
        "testimonials": testimonials,
        "pass_rate_rows": [_pass_rate_row(sample_year)],
        "documents": [
            {
                "title": "Regulamin",
                "description": "Zasady szkolenia w naszym ośrodku.",
                "url": "#",
                "size": "182,4 KB",
            }
        ],
        "breadcrumbs": [
            {"title": "Start", "url": "/"},
            {"title": "Kursy", "url": "/kursy/"},
            {"title": "Kategoria B", "url": ""},
        ],
        "select_options": [("b", "Kategoria B"), ("c", "Kategoria C")],
        # A header may be a plain string or carry numeric, which right aligns
        # the column the way A.5 asks for a column of figures.
        "price_headers": [
            "Pozycja",
            {"title": "Uwagi"},
            {"title": "Cena", "numeric": True},
        ],
    }
    return render(request, "core/kitchen_sink.html", context)


# Frozen in tech.md section 5, ships with S3.1. The course pages point at the
# same string rather than reverse(), so the link survives until leads.urls lands.
ENROL_URL = "/zapisz-sie/"

# The one category this school sells, tech.md section 1.
MAIN_COURSE_SLUG = "kat-b"

CONTACT_DESCRIPTION = _(
    "Adres, telefon i dojazd do OSK Ostrycharz w Wieluniu. "
    "Zapisy po wcześniejszym ustaleniu telefonicznym."
)

# FRONTEND.md A.9: five questions and the reviews strip.
FAQS_ON_HOME = 5
TESTIMONIALS_ON_HOME = 3
# A.9 point 7: fewer than two and the section does not render at all.
TESTIMONIALS_MINIMUM = 2

# tech.md section 8 fixes the suffix as "— OSK Ostrycharz Wieluń", so the subject
# does not repeat the town.
HOME_SUBJECT = _("Prawo jazdy kat. B")
HOME_DESCRIPTION = _(
    "Kurs prawa jazdy kategorii B w Wieluniu: standardowy, przyspieszony "
    "w dwa tygodnie i na skrzyni automatycznej. Ceny, zdawalność i zapisy. "
    "Dowóz na egzamin gratis."
)

DOWNLOADS_SUBJECT = _("Do pobrania")
DOWNLOADS_DESCRIPTION = _(
    "Regulamin, umowa i oświadczenia do pobrania. Dokumenty, które warto "
    "przeczytać i podpisać przed pierwszymi zajęciami."
)


def faq_jsonld(faqs: list[Any]) -> dict[str, Any]:
    """schema.org FAQPage, tech.md section 8 and FRONTEND.md A.9 point 8.

    Only the questions actually on the page. Marking up answers a reader cannot
    see is what the guideline calls hidden content, and it is the fastest way to
    lose the rich result entirely.
    """
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }


def aggregate_rating_jsonld(testimonials: list[Any]) -> dict[str, Any] | None:
    """schema.org AggregateRating, built only from reviews that can be checked.

    Nothing is invented here under any circumstances. The school's own site
    prints "110 opinii, 96% bardzo dobrych" as prose with no source behind it,
    and turning that into markup would be a rating Google cannot verify and we
    cannot either — which is a manual action, not a rich result.

    So the aggregate counts the rows in apps/reviews that carry a source_url,
    and returns None when there are none.
    """
    if not testimonials:
        return None

    ratings = [item.rating for item in testimonials if item.rating]
    if not ratings:
        return None

    return {
        "@type": "AggregateRating",
        "ratingValue": round(sum(ratings) / len(ratings), 1),
        "reviewCount": len(ratings),
        "bestRating": 5,
        "worstRating": 1,
    }


def _pass_rate_row(entry: PassRate | Any) -> dict[str, Any]:
    """One year, with the percentages the template must not compute itself."""
    percents = attempt_percents(entry)
    return {
        "year": entry.year,
        "students": entry.students,
        "note": entry.note,
        "attempts": list(
            zip(
                (entry.passed_1st, entry.passed_2nd, entry.passed_3rd, entry.passed_4th),
                percents,
                strict=True,
            )
        ),
        "first_percent": percents[0],
        "average": average_attempts(entry),
        # The people the four columns leave out. Printed on the page, not
        # quietly dropped: see the docstring on services.not_passed.
        "not_passed": not_passed(entry),
    }


def _stat_items(row: dict[str, Any]) -> list[dict[str, Label]]:
    """The four figures the home page band prints, tech.md section 1.

    Built here rather than in the template because three of the four are derived
    and one of them may not exist: a year in which nobody has passed yet has no
    mean number of attempts, and printing 0,0 would claim the opposite of what
    happened.
    """
    first_count, _first_percent = row["attempts"][0]
    items: list[dict[str, Label]] = [
        {"value": f"{row['first_percent']}%", "label": _("zdaje za pierwszym razem")},
        {"value": str(row["students"]), "label": _("kursantów w tym roczniku")},
        {"value": str(first_count), "label": _("zdało od razu, bez poprawki")},
    ]
    if row["average"] is not None:
        items.append(
            {
                "value": str(row["average"]).replace(".", ","),
                "label": _("średnia liczba podejść do egzaminu"),
            }
        )
    return items


def home(request: HttpRequest) -> HttpResponse:
    """The home page, tech.md section 5 and FRONTEND.md A.9.

    Rebuilt around what this school actually has: one category, three ways to
    take it, published prices and the best pass rate in the district. Sections
    that have no data do not render — a database seeded an hour ago still gives
    a page that reads.

    The slice selectors are imported inside the function on purpose, the same
    way page_detail does it: apps/core is shared and must not depend on a
    feature slice at import time.
    """
    from apps.gallery import selectors as gallery_selectors
    from apps.core.selectors import latest_pass_rate
    from apps.courses.models import Course, PriceItem
    from apps.links.selectors import published_faqs
    from apps.reviews.selectors import published_testimonials

    site = SiteSettings.get_solo()
    faqs = list(published_faqs()[:FAQS_ON_HOME])
    testimonials = list(published_testimonials()[:TESTIMONIALS_ON_HOME])
    latest = latest_pass_rate()

    course = Course.objects.filter(slug=MAIN_COURSE_SLUG, is_active=True).first()
    # The three ways to take the same category. Data, not markup: the owner
    # renames or reprices one in the admin and the cards follow.
    variants = list(
        PriceItem.objects.filter(is_active=True, group=COURSE_PRICE_GROUP)
        .exclude(price_gross=0)
        .order_by("order", "id")
    )
    row = _pass_rate_row(latest) if latest else None

    return render(
        request,
        "pages/home.html",
        {
            "seo": page_seo(
                request,
                subject=HOME_SUBJECT,
                description=HOME_DESCRIPTION,
                extra_jsonld=[faq_jsonld(faqs)] if faqs else None,
            ),
            "course": course,
            "variants": variants,
            "pass_rate": row,
            "stat_items": _stat_items(row) if row else [],
            "first_attempt": first_attempt_percent(latest) if latest else None,
            "video_id": youtube_id(site.youtube_video_url),
            "video_url": site.youtube_video_url,
            # A.9 point 7: two is the floor, and one review is not a strip.
            "testimonials": testimonials if len(testimonials) >= TESTIMONIALS_MINIMUM else [],
            "faqs": faqs,
            # Four for the home page's strip, and the strip renders its own
            # empty frames when there are none: the owner uploads in the
            # admin and the pictures appear without anyone touching a
            # template.
            "gallery_preview": list(gallery_selectors.published_images()[:4]),
            "directions": directions(site),
            "enrol_url": ENROL_URL,
            "lead_form": _lead_form(),
            "fragment_map": _fragment_map(),
        },
    )


def _fragment_map() -> dict[str, str]:
    """The anchors of the old one-page site, for static/js/app.js.

    A browser never sends a fragment, so django.contrib.redirects cannot answer
    /#pliki — the jump has to happen in the page. The table is read from the
    same csv the server side redirects come from, apps/core/redirects.py.
    """
    from apps.core.redirects import fragment_map

    try:
        return fragment_map()
    except (OSError, KeyError):
        # A missing or malformed csv costs the old anchors, not the home page.
        return {}


def downloads(request: HttpRequest) -> HttpResponse:
    """/do-pobrania/ — regulamin, umowa, oświadczenia, tech.md section 5."""
    from apps.core.selectors import published_downloads

    trail: list[tuple[Label, str]] = [
        (_("Start"), "/"),
        (_("Do pobrania"), reverse("core:downloads")),
    ]

    # Grouped, in the order the rows come back, and the group headings come
    # from the rows themselves. The school splits its papers into the ones a
    # candidate needs before the course starts and the ones they may never
    # need at all — which is the distinction the old site drew and the one
    # that costs a second trip to the office when it is missing.
    #
    # A row with no group joins the first one rather than starting a nameless
    # heading: the field is blank by default, and a new document the owner
    # adds in a hurry belongs somewhere.
    groups: list[tuple[str, list[dict[str, str]]]] = []
    for row in published_downloads():
        entry = {
            "title": row.title,
            "description": row.description,
            "url": row.file.url,
            "size": human_size(row.size_bytes),
        }
        label = row.group or (groups[0][0] if groups else "")
        for name, items in groups:
            if name == label:
                items.append(entry)
                break
        else:
            groups.append((label, [entry]))

    documents = [entry for _label, items in groups for entry in items]

    return render(
        request,
        "core/downloads.html",
        {
            "seo": page_seo(
                request,
                subject=DOWNLOADS_SUBJECT,
                description=DOWNLOADS_DESCRIPTION,
                breadcrumbs=trail,
            ),
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
            "documents": documents,
            "document_groups": groups,
            "enrol_url": ENROL_URL,
        },
    )


def directions(site: SiteSettings) -> dict[str, str]:
    """Links that start the navigation, tech.md section 5.

    geo: hands the point to whatever navigation app the phone already has, and
    the openstreetmap route is the desktop fallback. No google script either way.
    """
    if site.map_lat is None or site.map_lng is None:
        return {}

    point = f"{site.map_lat},{site.map_lng}"
    label = ", ".join(part for part in (site.short_name, site.street) if part)
    return {
        "geo": f"geo:{point}?q={quote(point)}({quote(label)})",
        # An empty first waypoint means "from where I am now".
        "osm": f"https://www.openstreetmap.org/directions?route=%3B{quote(point)}",
    }


def contact(request: HttpRequest) -> HttpResponse:
    """The page people call and drive from, tech.md section 5."""
    site = SiteSettings.get_solo()
    trail: list[tuple[Label, str]] = [(_("Start"), "/"), (_("Kontakt"), reverse("core:contact"))]

    return render(
        request,
        "core/contact.html",
        {
            "seo": page_seo(
                request,
                subject=_("Kontakt"),
                description=CONTACT_DESCRIPTION,
                breadcrumbs=trail,
            ),
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
            "directions": directions(site),
            "enrol_url": ENROL_URL,
            "lead_form": _lead_form(),
        },
    )


def _lead_form() -> Any:
    """The enrolment form, DEV.md S3.1.

    Imported inside the call rather than at module level: apps/core is shared
    and must not depend on a feature slice at import time.
    """
    from apps.leads.forms import LeadForm

    return LeadForm()


# tech.md section 4.1 names the flat pages. "zapisy" joined them for this
# school: signing up is a phone call and a list of papers, not a funnel, and
# that is a page of text with two blocks around it.
FLAT_PAGE_SLUGS = ("o-nas", "zapisy", "polityka-prywatnosci", "rodo")
ABOUT_SLUG = "o-nas"
ENROL_PAGE_SLUG = "zapisy"

# The price group the home page and the pricing page read as "the course
# itself", as opposed to extra lessons and third party fees.
COURSE_PRICE_GROUP = "Kurs"

# tech.md section 1, transcribed from the school's own page. Kept as data in one
# place rather than typed into a template, so the list on /zapisy/ and the list
# in the FAQ cannot drift apart.
REQUIRED_DOCUMENTS: tuple[tuple[Label, Label], ...] = (
    (_("Orzeczenie lekarskie"), _("O badaniu piszemy niżej — możesz je zrobić u nas w Wieluniu.")),
    (_("Fotografia 3,5 x 4,5 cm"), _("Taka sama jak do dowodu osobistego.")),
    (_("Dowód osobisty lub paszport"), _("Do wglądu przy zapisie.")),
    (_("Zaświadczenie o zameldowaniu"), _("Jedyny płatny dokument z tej listy: 17 zł.")),
    (_("Zgoda rodziców"), _("Tylko dla osób niepełnoletnich.")),
)


def _about_facts(site: SiteSettings, instructors: list[Any]) -> list[dict[str, Any]]:
    """The about page in figures, tech.md section 1.

    The previous client counted instructors, categories and cars, and this
    school has published none of those. What it has published is a pass rate and
    a price, so those are the facts — read from the same rows the rest of the
    site reads, never written down here.

    Two queries, and no more: the pass rate and the course. The instructors are
    handed in already loaded, because the page prints them further down and this
    row has no business asking for them a second time. The count of licence
    categories is deliberately not a tile — "1 kategoria" is not a fact anybody
    is impressed by, and it would cost a third query to say so.

    A tile whose number does not exist is absent rather than zero: a row of
    figures reading "0 instruktorów" is worse than a row of three.
    """
    from apps.core.selectors import latest_pass_rate
    from apps.courses.models import Course

    facts: list[dict[str, Any]] = []

    latest = latest_pass_rate()
    if latest:
        facts.append(
            {
                "value": f"{first_attempt_percent(latest)}%",
                "label": _("zdaje egzamin za pierwszym razem"),
            }
        )
        facts.append({"value": str(latest.students), "label": _("kursantów w ostatnim roczniku")})

    if site.founded_year:
        facts.append({"value": str(site.founded_year), "label": _("rok założenia")})

    course = Course.objects.filter(slug=MAIN_COURSE_SLUG, is_active=True).first()
    if course and course.price_gross:
        facts.append(
            {
                "value": f"{course.price_gross:.0f} zł",
                "label": _("kurs kat. B, dowóz na egzamin w cenie"),
            }
        )

    if instructors:
        facts.append({"value": str(len(instructors)), "label": _("instruktorów prowadzi zajęcia")})

    return facts


def _enrolment_steps(site: SiteSettings) -> list[dict[str, Label]]:
    """How to sign up, tech.md section 1. Five steps, the first is a phone call."""
    phone = site.phone_primary or ""
    return [
        {
            "title": _("Zadzwoń"),
            "text": _("Zapisy prowadzimy po wcześniejszym ustaleniu telefonicznym: %(phone)s.")
            % {"phone": phone},
        },
        {
            "title": _("Ustal termin"),
            "text": _("Umawiamy datę startu i godziny, które Ci pasują."),
        },
        {
            "title": _("Wyrób PKK"),
            "text": _(
                "Profil Kandydata na Kierowcę zakłada Starostwo Powiatowe w Wieluniu, "
                "na podstawie orzeczenia lekarskiego i zdjęcia."
            ),
        },
        {
            "title": _("Przynieś dokumenty"),
            "text": _("Pięć pozycji z listy obok. Komplet zajmuje jedną wizytę."),
        },
        {
            "title": _("Zacznij zajęcia"),
            "text": _("Teoria, potem jazdy. Egzamin wewnętrzny przed państwowym."),
        },
    ]


def _scans_by_year() -> list[tuple[int, list[Any]]]:
    """Pass rate scans grouped by year, newest first.

    The grouping is done here rather than with a regroup tag so the template
    keeps no logic and the order comes from the model's Meta, which is where
    the owner's ordering already lives.
    """
    from apps.core.selectors import published_pass_rate_scans

    years: list[tuple[int, list[Any]]] = []
    for scan in published_pass_rate_scans():
        if years and years[-1][0] == scan.year:
            years[-1][1].append(scan)
        else:
            years.append((scan.year, [scan]))
    return years


def page_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """A flat page, tech.md section 5.

    Two of them carry more than their own text. The about page gets the fleet
    and the team, when there are any. The enrolment page gets the five steps,
    the list of papers and whatever documents are uploaded — all of it built
    here rather than parsed out of the body, so the page cannot promise a
    document the media folder does not hold.

    The slice selectors are imported inside the function on purpose, since
    apps/core is shared and must not depend on a feature slice at import time.
    """
    from apps.core.selectors import published_downloads
    from apps.people import selectors as people

    page = get_object_or_404(Page, slug=slug, is_published=True)
    site = SiteSettings.get_solo()
    about = slug == ABOUT_SLUG
    enrolment = slug == ENROL_PAGE_SLUG
    trail: list[tuple[Label, str]] = [
        (_("Start"), "/"),
        (page.title, reverse("core:page", kwargs={"slug": slug})),
    ]

    fleet = people.vehicles_by_course() if about else []
    # Loaded once. The facts row counts them and the team section prints them.
    # Two lists, because the page asks two different questions of them.
    #
    # `instructors` is how many people teach here, and it is a fact about the
    # school — the figure in "W liczbach" counts everyone on the staff whether
    # or not anybody has sent a photograph in.
    #
    # `instructor_cards` is who gets a card, and REDESIGN.md D.2 is strict: an
    # instructor card exists to put a face to a name, and without the face it
    # is a box inviting somebody to fill it with a stock portrait. The
    # filtering is here rather than in the template loop, which is the
    # CONTRACT GAP the template carried — and the template needs the
    # distinction rather than just the shorter list, because a css-only hide
    # left "Imię i nazwisko" in the markup for a screen reader to read out
    # beside a real instructor's name.
    instructors = list(people.active_instructors()) if about else []
    instructor_cards = [person for person in instructors if person.photo]
    documents = (
        [
            {
                "title": row.title,
                "description": row.description,
                "url": row.file.url,
                "size": human_size(row.size_bytes),
            }
            for row in published_downloads()
        ]
        if enrolment
        else []
    )

    return render(
        request,
        "core/page_detail.html",
        {
            "seo": page_seo(
                request,
                subject=page.seo_title or page.title,
                description=page.seo_desc or page.lead or page.title,
                breadcrumbs=trail,
            ),
            "page": page,
            "body": render_markdown(page.body),
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
            "about": about,
            # The county office's tables, grouped by year the way the school's
            # own site grouped them. Only on /o-nas/, and only where the block
            # of figures they back up already is.
            "scan_years": _scans_by_year() if about else [],
            "facts": _about_facts(site, instructors) if about else [],
            "enrolment": enrolment,
            "steps": _enrolment_steps(site) if enrolment else [],
            "required_documents": (
                [{"title": title, "text": text} for title, text in REQUIRED_DOCUMENTS]
                if enrolment
                else []
            ),
            "documents": documents,
            "instructors": instructors,
            "instructor_cards": instructor_cards,
            "vehicle_groups": fleet,
            # Counted from what is already loaded rather than asked for again:
            # the about page has a query budget and this is not worth one.
            "fleet_size": sum(len(group["vehicles"]) for group in fleet),
            "enrol_url": ENROL_URL,
            "lead_form": _lead_form() if enrolment else None,
        },
    )


def robots(request: HttpRequest) -> HttpResponse:
    """robots.txt, tech.md section 5.

    Everything is open except the admin and the design review page. The sitemap
    is named absolutely, which is what a crawler needs to follow it.
    """
    return render(
        request,
        "robots.txt",
        {"sitemap_url": request.build_absolute_uri(reverse("sitemap"))},
        content_type="text/plain; charset=utf-8",
    )


def ornament_sandbox(request: HttpRequest) -> HttpResponse:
    """Every mark in static/img/ornament/ on every ground, ROSE.md K3 point 7.

    Debug only, like the kitchen sink beside it. The point of the page is the
    comparison: a stroke that reads as a brush on the blush page can read as a
    smear on the wine band, and the only way to know is to put it on both.
    """
    from django.conf import settings

    if not settings.DEBUG:
        raise Http404

    return render(
        request,
        "dev/ornament.html",
        {
            "brushes": ["1", "2", "3", "4"],
            "hearts": ["1", "2", "3"],
            "marks": ["scribble", "arrow", "sparks", "circle", "blob"],
        },
    )
