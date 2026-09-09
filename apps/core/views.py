"""Core views."""

from datetime import date
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

from django import forms
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.markdown import render_markdown
from apps.core.models import Page, SiteSettings
from apps.core.seo import Label, Seo, build_title, page_seo

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

    # Five tiles, because A.9 point 2 lays them out five across on lg, and the
    # last one carries no price so the "cena na zapytanie" fallback is on screen
    # rather than described.
    courses = [
        _course("AM", "Motorower", 14, "1200.00"),
        _course("A1", "Motocykl do 125", 16, "2400.00"),
        _course("B", "Samochód osobowy", 18, "3200.00"),
        _course("B+E", "Osobowy z przyczepą", 18, "1800.00"),
        _course("C+E", "Ciężarowy z naczepą", 21, None),
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

CONTACT_DESCRIPTION = _(
    "Adres, telefon i godziny otwarcia OSK Ostrycharz w Wieluniu. "
    "Biuro i dojazd na ul. Asnyka 7. Zapisy telefoniczne."
)

# FRONTEND.md A.9: three rows of terms, five questions, and the reviews strip.
UPCOMING_ON_HOME = 3
FAQS_ON_HOME = 5
TESTIMONIALS_ON_HOME = 3
# A.9 point 7: fewer than two and the section does not render at all.
TESTIMONIALS_MINIMUM = 2

# tech.md section 8 fixes the suffix as "— OSK Ostrycharz Wieluń", so the subject
# does not repeat the town: "Prawo jazdy — OSK Ostrycharz Wieluń" carries the same
# two keywords FRONTEND.md F3 asks for without saying Wieluń twice.
HOME_SUBJECT = _("Prawo jazdy")
HOME_DESCRIPTION = _(
    "Ośrodek szkolenia kierowców w Wieluniu od 1996 roku. Kategorie AM–D, "
    "kwalifikacje zawodowe, ADR i badania psychologiczne. Zajęcia po polsku, "
    "rosyjsku i ukraińsku."
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


def home(request: HttpRequest) -> HttpResponse:
    """The home page, tech.md section 5 and FRONTEND.md A.9.

    Eleven sections in a fixed order, and three of them decide for themselves
    whether they exist at all: no joinable group, fewer than two verifiable
    reviews or no published questions, and the section is simply absent. An
    empty block that says nothing is worse than one section fewer.

    The slice selectors are imported inside the function on purpose, the same
    way page_detail does it: apps/core is shared and must not depend on a
    feature slice at import time.
    """
    from apps.courses import selectors as courses
    from apps.courses.models import Course
    from apps.links.selectors import published_faqs
    from apps.reviews.selectors import published_testimonials

    site = SiteSettings.get_solo()
    faqs = list(published_faqs()[:FAQS_ON_HOME])
    testimonials = list(published_testimonials()[:TESTIMONIALS_ON_HOME])

    # Two numbers the page prints as facts. Counted rather than written down:
    # A.9 point 1 says fifteen courses and A.9 point 6 says years on the market,
    # and both are wrong the moment the owner adds a course or the year turns.
    course_count = courses.active_courses().count()
    years_on_market = timezone.localdate().year - site.founded_year

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
            "course_count": course_count,
            "years_on_market": years_on_market,
            "categories": list(courses.active_courses(Course.Kind.LICENSE)),
            "intakes": list(courses.joinable_intakes()[:UPCOMING_ON_HOME]),
            "professional": list(courses.active_courses(Course.Kind.PROFESSIONAL)),
            "psychotests": list(courses.active_courses(Course.Kind.PSYCHOTEST)),
            "operator_courses": list(courses.active_courses(Course.Kind.OPERATOR)),
            # A.9 point 7: two is the floor, and one review is not a strip.
            "testimonials": testimonials if len(testimonials) >= TESTIMONIALS_MINIMUM else [],
            "faqs": faqs,
            "directions": directions(site),
            "enrol_url": ENROL_URL,
            "lead_form": _lead_form(),
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
    trail: list[tuple[Label, str]] = [
        (_("Start"), "/"),
        (page.title, reverse("core:page", kwargs={"slug": slug})),
    ]

    fleet = people.vehicles_by_course() if about else []

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
            # BLOCKS.md B5: what the school sells, as four places to go. Built
            # here rather than parsed out of the page body, so the cards cannot
            # promise something the offer no longer has.
            "offer": (
                [
                    {
                        "title": _("Prawo jazdy"),
                        "note": _("kategorie AM, A1, A2, A, B, B+E, C, C+E, D"),
                        "url": "/kursy/",
                    },
                    {
                        "title": _("Kierowca zawodowy"),
                        "note": _("kwalifikacja wstępna i szkolenia okresowe"),
                        "url": "/kierowca-zawodowy/",
                    },
                    {
                        "title": _("Badania psychologiczne"),
                        "note": _("kierowcy i operatorzy maszyn"),
                        "url": "/cennik/",
                    },
                    {
                        "title": _("Wózki widłowe"),
                        "note": _("uprawnienia operatora"),
                        "url": "/kursy/wozki-widlowe/",
                    },
                ]
                if about
                else []
            ),
            "instructors": people.active_instructors() if about else [],
            "vehicle_groups": fleet,
            # Counted from what is already loaded rather than asked for again:
            # the about page has a query budget and this is not worth one.
            "fleet_size": sum(len(group["vehicles"]) for group in fleet),
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
