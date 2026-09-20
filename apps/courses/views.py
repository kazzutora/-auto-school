"""Course pages, tech.md section 5.

Same shape as the reference slice in apps/gallery: selectors fetch, services
shape, the view assembles the section 8 SEO contract and renders.
"""

from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.markdown import render_markdown
from apps.core.seo import Label, build_description, page_seo
from apps.courses import selectors, services
from apps.courses.models import Course, CourseIntake
from apps.courses.services import format_price, min_start_age, split_age

ENROL_URL = "/zapisz-sie/"  # frozen in tech.md section 5, ships with S3
INTAKE_HEADERS = [_("Start"), _("Kurs"), _("Tryb"), _("Język"), _("Status")]


def _crumbs(trail: list[tuple[Label, str]]) -> list[dict[str, Label]]:
    return [{"title": name, "url": url} for name, url in trail]


def seo_subject(course: Course) -> str:
    """tech.md section 8 wants "Prawo jazdy kat. B — OSK Ostrycharz Wieluń"."""
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

    # The price, which is the one thing the previous client could not publish
    # and this one leads with. schema.org wants it on an Offer rather than on
    # the Course, and it wants the currency: a bare 3700 is not a price.
    if course.price_gross:
        data["offers"] = {
            "@type": "Offer",
            "price": f"{course.price_gross:.2f}",
            "priceCurrency": "PLN",
            "category": "Paid",
            "url": url,
            "availability": "https://schema.org/InStock",
        }

    # Google asks a Course for at least one instance of it. This school runs the
    # same course continuously and enrols by telephone, so what is honest here
    # is the mode and the language, not a date it never published.
    data["hasCourseInstance"] = {
        "@type": "CourseInstance",
        "courseMode": "onsite",
        "courseWorkload": "P3M" if course.kind == Course.Kind.LICENSE else "P1M",
        "location": {
            "@type": "Place",
            "name": site.legal_name or site.short_name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": site.street,
                "postalCode": site.postal_code,
                "addressLocality": site.city,
                "addressCountry": "PL",
            },
        },
    }
    return data


def _grid(
    request: HttpRequest,
    *,
    kind: str,
    subject: Label,
    description: Label,
    route: str,
    heading: Label,
    intro: Label,
) -> HttpResponse:
    courses = list(selectors.active_courses(kind))
    # A listing with nothing in it is not a page. This school sells one kind, so
    # /kierowca-zawodowy/ has no courses behind it and used to answer 200 with a
    # heading over an empty grid — a thin page, in the sitemap, competing with
    # the pages that do have something to say.
    if not courses:
        raise Http404(f"no active courses of kind {kind}")

    trail: list[tuple[Label, str]] = [(_("Start"), "/"), (heading, reverse(route))]

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
        subject=_("Kursy prawa jazdy"),
        description=(
            "Kursy prawa jazdy wszystkich kategorii w Wieluniu: AM, A1, A2, A, B, "
            "B+E, C, C+E i D. Zajęcia także w języku rosyjskim."
        ),
        route="courses:list",
        heading=_("Kursy prawa jazdy"),
        intro=_("Wybierz kategorię. Kurs możesz rozpocząć trzy miesiące przed osiągnięciem wieku."),
    )


def pro_hub(request: HttpRequest) -> HttpResponse:
    """Professional driver training, tech.md section 5."""
    return _grid(
        request,
        kind=Course.Kind.PROFESSIONAL,
        subject=_("Kierowca zawodowy"),
        description=(
            "Kwalifikacja wstępna, szkolenia okresowe i kurs ADR dla kierowców "
            "zawodowych w Wieluniu."
        ),
        route="courses:pro_hub",
        heading=_("Kierowca zawodowy"),
        intro=_("Kwalifikacja wstępna, szkolenia okresowe i przewóz towarów niebezpiecznych."),
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

    trail: list[tuple[Label, str]] = [(_("Start"), "/")]
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
            # The variants of this one course, as price rows. This school sells
            # category B three ways and the difference between them is the whole
            # decision a visitor is making on this page.
            "variants": services.price_item_rows(
                selectors.active_price_items().filter(group=COURSE_PRICE_GROUP)
            ),
            "facts": _course_facts(course),
            "fleet_facts": FLEET_FACTS,
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


# The price group that holds the course itself, as opposed to extra lessons and
# third party fees. Named in one place; apps/core/views.py reads the same one.
COURSE_PRICE_GROUP = "Kurs"

# What the school says about its own cars, tech.md section 1, transcribed. It
# stands in for photographs we do not own until the owner sends theirs, and
# every line here is a claim they already make in print.
FLEET_FACTS: tuple[dict[str, Label], ...] = (
    {"title": _("Klimatyzacja"), "text": _("we wszystkich autach szkoleniowych")},
    {"title": _("Wyposażenie"), "text": _("bogate, w standardzie egzaminacyjnym")},
    {"title": _("Skrzynia"), "text": _("manualna i automatyczna, do wyboru")},
    {"title": _("Na egzamin"), "text": _("dowozimy tym samym autem, gratis")},
)


def _course_facts(course: Course) -> list[dict[str, Any]]:
    """The spec list beside the heading: what applies to me, in four lines.

    Every entry is skipped when the underlying field is empty, so a course with
    no declared hours shows three facts rather than three facts and a blank.
    """
    facts: list[dict[str, Any]] = []

    if course.min_age:
        facts.append(
            {
                "title": _("Wiek"),
                "text": _("od %(age)s lat") % {"age": course.min_age},
                "numeric": True,
            }
        )
        months = min_start_age(course)
        if months:
            years, rest = split_age(months)
            facts.append(
                {
                    "title": _("Zapisy od"),
                    "text": _("%(years)s lat %(months)s mies.") % {"years": years, "months": rest},
                    "numeric": True,
                }
            )
    if course.theory_hours:
        facts.append({"title": _("Teoria"), "text": f"{course.theory_hours} h", "numeric": True})
    if course.practice_hours:
        facts.append(
            {"title": _("Praktyka"), "text": f"{course.practice_hours} h", "numeric": True}
        )
    if course.price_gross:
        facts.append(
            {
                "title": _("Cena"),
                "text": format_price(course.price_gross),
                "numeric": True,
            }
        )
    facts.append({"title": _("Dowóz na egzamin"), "text": _("gratis")})
    return facts


# The order the price list reads best in: what the school charges first, then
# what it charges by the hour, then what somebody pays to a doctor and an exam
# centre. Groups the seed does not use simply do not appear.
PRICE_GROUP_ORDER = ("Kurs", "Jazdy doszkalające", "W cenie kursu", "Opłaty zewnętrzne")
PRICE_HEADERS = ["Usługa", "Cena brutto", "Uwagi"]

# The one group that is not money the school asks for. It gets its own note on
# the page, because "230 zł egzamin" beside "3700 zł kurs" reads as one bill
# unless the page says otherwise.
EXTERNAL_GROUP = "Opłaty zewnętrzne"

PRICING_DESCRIPTION = _(
    "Cennik kursu prawa jazdy kat. B w Wieluniu: kurs 3700 zł, przyspieszony "
    "i automat po 4300 zł, jazdy doszkalające od 140 zł/h. Ceny brutto, "
    "dowóz na egzamin gratis."
)


def _ordered_groups(groups: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
    """PRICE_GROUP_ORDER first, then whatever else the owner has invented.

    Sorting rather than filtering: a group added in the admin still shows up,
    at the end, instead of silently disappearing off the price list.
    """
    known = {name: position for position, name in enumerate(PRICE_GROUP_ORDER)}
    return sorted(groups, key=lambda pair: known.get(pair[0], len(known)))


def pricing(request: HttpRequest) -> HttpResponse:
    """One page that answers "how much", tech.md section 5.

    Built out of PriceItem alone. The previous client had a row per course and
    no figures at all; this one prices three variants of one course, so the
    course itself is a price group like any other and a second list of courses
    beside it would print category B twice.
    """
    from apps.core.models import Page

    items = selectors.active_price_items()
    groups = _ordered_groups(services.group_price_items(items))

    # The course group is drawn as cards rather than as rows, so the template
    # gets the model objects: a card needs `include_lines` and `featured`, and
    # PriceRow is a flat label/price/note triple by design.
    #
    # Not a second query. The queryset is already evaluated by the grouping
    # above, so this filters the rows in python and leaves the page on one.
    course_cards = [item for item in items if item.group == COURSE_PRICE_GROUP]

    trail: list[tuple[Label, str]] = [(_("Start"), "/"), (_("Cennik"), reverse("courses:pricing"))]
    payments = Page.objects.filter(slug="platnosci", is_published=True).first()

    return render(
        request,
        "courses/pricing.html",
        {
            "seo": page_seo(
                request,
                subject=_("Cennik kursu prawa jazdy"),
                description=PRICING_DESCRIPTION,
                breadcrumbs=trail,
            ),
            "breadcrumbs": _crumbs(trail),
            "groups": groups,
            "external_group": EXTERNAL_GROUP,
            "course_group": COURSE_PRICE_GROUP,
            "course_cards": course_cards,
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
        "course_options": [(ANY, _("Wszystkie kursy"))]
        + [(course.slug, course.title) for course in selectors.courses_with_upcoming_intakes()],
        "language_options": [(ANY, _("Wszystkie języki"))]
        + [(code, label) for code, label in settings.LANGUAGES],
        "mode_options": [(ANY, _("Wszystkie tryby")), *CourseIntake.Mode.choices],
    }


def intakes(request: HttpRequest) -> HttpResponse:
    """The schedule, tech.md section 5.

    The same filters answer here and on the htmx endpoint, so the plain GET form
    gives a visitor without javascript exactly the same result.
    """
    trail: list[tuple[Label, str]] = [(_("Start"), "/"), (_("Terminy"), reverse("courses:intakes"))]

    return render(
        request,
        "courses/intakes.html",
        {
            "seo": page_seo(
                request,
                subject=_("Terminy kursów"),
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
