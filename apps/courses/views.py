"""Course pages, tech.md section 5.

Same shape as the reference slice in apps/gallery: selectors fetch, services
shape, the view assembles the section 8 SEO contract and renders.
"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from apps.core.markdown import render_markdown
from apps.core.seo import build_description, page_seo
from apps.courses import selectors, services
from apps.courses.models import Course, CourseIntake
from apps.courses.services import format_price, min_start_age, split_age

ENROL_URL = "/zapisz-sie/"  # frozen in tech.md section 5, ships with S3
INTAKE_HEADERS = ["Start", "Kurs", "Tryb", "Język", "Status"]


def _crumbs(trail: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"title": name, "url": url} for name, url in trail]


def seo_subject(course: Course) -> str:
    """tech.md section 8 wants "Prawo jazdy kat. B — OSK Nawrocki Wieluń"."""
    if course.kind == Course.Kind.LICENSE and course.code:
        return f"Prawo jazdy kat. {course.code}"
    return course.title


def course_jsonld(course: Course, url: str, site: Any) -> dict[str, Any]:
    """schema.org Course, tech.md section 8."""
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": course.title,
        "description": build_description(course.lead or course.title),
        "url": url,
        "provider": {
            "@type": "DrivingSchool",
            "name": site.legal_name or site.short_name,
            "areaServed": site.city,
        },
        "inLanguage": course.languages or ["pl"],
    }
    if course.min_age:
        data["typicalAgeRange"] = f"{course.min_age}-"
    return data


def _grid(
    request: HttpRequest,
    *,
    kind: str,
    subject: str,
    description: str,
    route: str,
    heading: str,
    intro: str,
) -> HttpResponse:
    courses = list(selectors.active_courses(kind))
    trail = [("Start", "/"), (heading, reverse(route))]

    return render(
        request,
        "courses/course_list.html",
        {
            "seo": page_seo(request, subject=subject, description=description, breadcrumbs=trail),
            "courses": courses,
            "breadcrumbs": _crumbs(trail),
            # Not "heading": a cotton component reads the page context, and
            # <c-section> would take that key as its own heading slot and print
            # the title a second time above the h1.
            "page_heading": heading,
            "intro": intro,
            "show_other_kinds": kind == Course.Kind.LICENSE,
            "enrol_url": ENROL_URL,
        },
    )


def course_list(request: HttpRequest) -> HttpResponse:
    """Licence categories, tech.md section 5."""
    return _grid(
        request,
        kind=Course.Kind.LICENSE,
        subject="Kursy prawa jazdy",
        description=(
            "Kursy prawa jazdy wszystkich kategorii w Wieluniu: AM, A1, A2, A, B, "
            "B+E, C, C+E i D. Zajęcia także w języku rosyjskim."
        ),
        route="courses:list",
        heading="Kursy prawa jazdy",
        intro="Wybierz kategorię. Kurs możesz rozpocząć trzy miesiące przed osiągnięciem wieku.",
    )


def pro_hub(request: HttpRequest) -> HttpResponse:
    """Professional driver training, tech.md section 5."""
    return _grid(
        request,
        kind=Course.Kind.PROFESSIONAL,
        subject="Kierowca zawodowy",
        description=(
            "Kwalifikacja wstępna, szkolenia okresowe i kurs ADR dla kierowców "
            "zawodowych w Wieluniu."
        ),
        route="courses:pro_hub",
        heading="Kierowca zawodowy",
        intro="Kwalifikacja wstępna, szkolenia okresowe i przewóz towarów niebezpiecznych.",
    )


def course_detail(request: HttpRequest, slug: str, kind: str) -> HttpResponse:
    from apps.core.models import SiteSettings

    course = selectors.course_by_slug(slug, kind)
    canonical = request.build_absolute_uri(course.get_absolute_url())

    if kind == Course.Kind.PROFESSIONAL:
        parent = ("Kierowca zawodowy", reverse("courses:pro_hub"))
    elif kind == Course.Kind.LICENSE:
        parent = ("Kursy", reverse("courses:list"))
    else:
        parent = None

    trail = [("Start", "/")]
    if parent:
        trail.append(parent)
    trail.append((course.title, course.get_absolute_url()))

    seo = page_seo(
        request,
        subject=seo_subject(course),
        description=course.seo_desc or course.lead or course.title,
        breadcrumbs=trail,
        # What a link to this course shows when it is shared, DEV.md S8.
        og_image=request.build_absolute_uri(course.hero_image.url) if course.hero_image else None,
        extra_jsonld=[course_jsonld(course, canonical, SiteSettings.get_solo())],
    )

    return render(
        request,
        "courses/course_detail.html",
        {
            "seo": seo,
            "course": course,
            # BLOCKS.md B10: the other categories, at the end of the page. The
            # same tile the home page draws — the component is reused, not the
            # markup copied.
            "other_courses": [
                other
                for other in selectors.active_courses().filter(kind=course.kind)
                if other.pk != course.pk
            ][:5],
            "breadcrumbs": _crumbs(trail),
            "price": format_price(course.price_gross, course.price_note),
            "start_age": split_age(months) if (months := min_start_age(course)) else None,
            # No header row on the summary table, the row labels carry it.
            "fact_headers": [],
            "intake_headers": INTAKE_HEADERS,
            "entitlements": render_markdown(course.entitlements),
            "requirements": render_markdown(course.requirements),
            "body": render_markdown(course.body),
            "intakes": selectors.prefetched_intakes(course),
            "vehicles": selectors.prefetched_vehicles(course),
            "enrol_url": ENROL_URL,
            # The form ends the page with this course already chosen, DEV.md
            # S3.1. Imported inside the function: apps/courses must not depend
            # on another slice at import time.
            "lead_form": _lead_form(course),
        },
    )


def _lead_form(course: Course) -> Any:
    from apps.leads.forms import LeadForm

    return LeadForm(initial={"course": course.pk})


# tech.md section 4.2 kinds, in the order the price page reads best.
PRICE_GROUPS = (
    (Course.Kind.LICENSE, "Kategorie prawa jazdy"),
    (Course.Kind.PROFESSIONAL, "Kierowca zawodowy"),
    (Course.Kind.PSYCHOTEST, "Badania psychologiczne"),
    (Course.Kind.OPERATOR, "Uprawnienia operatora"),
)
PRICE_HEADERS = ["Usługa", "Cena brutto", "Uwagi"]


def pricing(request: HttpRequest) -> HttpResponse:
    """One page that answers "how much", tech.md section 5."""
    from apps.core.models import Page

    # Every active course, not only the priced ones: see course_rows.
    offered = list(selectors.active_courses())
    groups = [
        (label, services.course_rows(course for course in offered if course.kind == kind))
        for kind, label in PRICE_GROUPS
    ]
    groups = [(label, rows) for label, rows in groups if rows]
    groups += services.group_price_items(selectors.active_price_items())

    trail = [("Start", "/"), ("Cennik", reverse("courses:pricing"))]
    payments = Page.objects.filter(slug="platnosci", is_published=True).first()

    return render(
        request,
        "courses/pricing.html",
        {
            "seo": page_seo(
                request,
                subject="Cennik",
                description=(
                    "Cennik kursów prawa jazdy, szkoleń dla kierowców zawodowych i badań "
                    "psychologicznych w Wieluniu."
                ),
                breadcrumbs=trail,
            ),
            "breadcrumbs": _crumbs(trail),
            "groups": groups,
            "headers": PRICE_HEADERS,
            "payments": render_markdown(payments.body) if payments else "",
            "payments_title": payments.title if payments else "",
            "enrol_url": ENROL_URL,
        },
    )


INTAKE_HEADERS_FULL = ["Start", "Kurs", "Tryb", "Język", "Status", ""]
ANY = ""


def _intake_filters(request: HttpRequest) -> dict[str, str]:
    """The three dimensions from tech.md section 5, as given in the query string."""
    return {
        "course": request.GET.get("course", ANY).strip(),
        "language": request.GET.get("language", ANY).strip(),
        "mode": request.GET.get("mode", ANY).strip(),
    }


def _intake_context(request: HttpRequest) -> dict[str, Any]:
    from django.conf import settings

    chosen = _intake_filters(request)
    rows = list(selectors.filtered_intakes(**chosen))

    return {
        "intakes": [
            {
                "intake": intake,
                "seats_left": services.seats_left(intake),
                "bookable": services.is_bookable(intake),
                "enrol_url": f"{ENROL_URL}?intake={intake.pk}",
            }
            for intake in rows
        ],
        "chosen": chosen,
        "headers": INTAKE_HEADERS_FULL,
        "course_options": [(ANY, "Wszystkie kursy")]
        + [(course.slug, course.title) for course in selectors.courses_with_upcoming_intakes()],
        "language_options": [(ANY, "Wszystkie języki")]
        + [(code, label) for code, label in settings.LANGUAGES],
        "mode_options": [(ANY, "Wszystkie tryby"), *CourseIntake.Mode.choices],
    }


def intakes(request: HttpRequest) -> HttpResponse:
    """The schedule, tech.md section 5.

    The same filters answer here and on the htmx endpoint, so the plain GET form
    gives a visitor without javascript exactly the same result.
    """
    trail = [("Start", "/"), ("Terminy", reverse("courses:intakes"))]

    return render(
        request,
        "courses/intakes.html",
        {
            "seo": page_seo(
                request,
                subject="Terminy kursów",
                description=(
                    "Najbliższe terminy kursów prawa jazdy i szkoleń dla kierowców "
                    "zawodowych w Wieluniu."
                ),
                breadcrumbs=trail,
            ),
            "breadcrumbs": _crumbs(trail),
            "enrol_url": ENROL_URL,
            **_intake_context(request),
        },
    )


def intake_filter(request: HttpRequest) -> HttpResponse:
    """HTMX partial: table rows only, tech.md section 5."""
    return render(request, "courses/_intake_rows.html", _intake_context(request))
