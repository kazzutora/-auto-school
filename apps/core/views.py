"""Core views."""

from datetime import date
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

from django import forms
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.core.markdown import render_markdown
from apps.core.models import Page, SiteSettings
from apps.core.seo import Seo, build_title, page_seo

_PLACEHOLDER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">'
    '<rect width="400" height="400" fill="#EBE6F8"/>'
    '<text x="200" y="210" font-family="sans-serif" font-size="28" fill="#5B47A8"'
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

    course = SimpleNamespace(
        title="Kategoria B",
        code="B",
        lead="Kurs na prawo jazdy kategorii B, teoria i praktyka w Wieluniu.",
        min_age=18,
        theory_hours=30,
        practice_hours=30,
        price_gross="3200.00",
        price_note="cena od",
        languages=["pl", "ru", "uk"],
    )
    intakes = [
        SimpleNamespace(
            start_date=date(2026, 9, 14),
            course=SimpleNamespace(title="Kategoria B"),
            get_mode_display=lambda: "Stacjonarny",
            language="pl",
            status=status,
        )
        for status in ("open", "full", "closed", "planned")
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

    context: dict[str, Any] = {
        "seo": Seo(
            title=build_title("Kitchen sink"),
            description="Podgląd wszystkich komponentów UI.",
            canonical=request.build_absolute_uri(),
            robots="noindex,nofollow",
        ),
        "form": KitchenSinkForm(),
        "bound_form": KitchenSinkForm(data={"first_name": "", "email": "nie-email"}),
        "course": course,
        "intakes": intakes,
        "images": images,
        "testimonials": testimonials,
        "breadcrumbs": [
            {"title": "Start", "url": "/"},
            {"title": "Kursy", "url": "/kursy/"},
            {"title": "Kategoria B", "url": ""},
        ],
        "select_options": [("b", "Kategoria B"), ("c", "Kategoria C")],
        "intake_headers": ["Start", "Kurs", "Tryb", "Język", "Status"],
    }
    return render(request, "core/kitchen_sink.html", context)


# Frozen in tech.md section 5, ships with S3.1. The course pages point at the
# same string rather than reverse(), so the link survives until leads.urls lands.
ENROL_URL = "/zapisz-sie/"

CONTACT_DESCRIPTION = (
    "Adres, telefony i godziny otwarcia OSK Nawrocki w Wieluniu. "
    "Biuro, pracownia psychologiczna i dojazd na ul. Zieloną 45."
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
    trail = [("Start", "/"), ("Kontakt", reverse("core:contact"))]

    return render(
        request,
        "core/contact.html",
        {
            "seo": page_seo(
                request,
                subject="Kontakt",
                description=CONTACT_DESCRIPTION,
                breadcrumbs=trail,
            ),
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
            "directions": directions(site),
            "enrol_url": ENROL_URL,
        },
    )


# tech.md section 4.1 names the flat pages: o-nas, polityka-prywatnosci, rodo.
FLAT_PAGE_SLUGS = ("o-nas", "polityka-prywatnosci", "rodo")
ABOUT_SLUG = "o-nas"


def page_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """A flat page, tech.md section 5.

    The about page carries more than its own text: the url map gives it
    Instructor and Vehicle as well, so the team and the fleet are assembled
    here. The slice selectors are imported inside the function on purpose,
    since apps/core is shared and must not depend on a feature slice at import
    time.
    """
    from apps.courses.models import Course
    from apps.courses.selectors import active_courses
    from apps.people import selectors as people

    page = get_object_or_404(Page, slug=slug, is_published=True)
    about = slug == ABOUT_SLUG
    trail = [("Start", "/"), (page.title, reverse("core:page", kwargs={"slug": slug}))]

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
            "instructors": people.active_instructors() if about else [],
            "vehicle_groups": people.vehicles_by_course() if about else [],
            "category_count": active_courses(Course.Kind.LICENSE).count() if about else 0,
            "enrol_url": ENROL_URL,
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
