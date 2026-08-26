"""Gallery views, tech.md section 5.

Reference shape for every slice: selectors fetch, services shape, the view puts
the section 8 SEO contract in the context and renders.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from apps.core.seo import page_seo
from apps.gallery import selectors, services
from apps.gallery.models import GalleryImage

# Reading order on the page, not the enum order.
SECTION_ORDER = (
    GalleryImage.Section.SCHOOL,
    GalleryImage.Section.VEHICLES,
    GalleryImage.Section.YARD,
    GalleryImage.Section.EVENTS,
)

# Page copy, not data. The choice labels on the model are english until the
# locale catalogs are compiled, and this page is polish today.
SECTION_LABELS: dict[str, str] = {
    GalleryImage.Section.SCHOOL: "Ośrodek",
    GalleryImage.Section.VEHICLES: "Pojazdy",
    GalleryImage.Section.YARD: "Plac manewrowy",
    GalleryImage.Section.EVENTS: "Zajęcia",
}

SECTION_PARAM = "section"
ALL_SECTIONS = ""


def chosen_section(request: HttpRequest) -> str:
    """The section asked for, or every section.

    An unknown value falls back to everything rather than to an error page: a
    stale link from a search engine should still show the gallery.
    """
    asked = request.GET.get(SECTION_PARAM, ALL_SECTIONS)
    return asked if asked in SECTION_LABELS else ALL_SECTIONS


def section_filters(chosen: str, counts: dict[str, int]) -> list[dict[str, object]]:
    """The filter chips, one per section that has something to show.

    Nothing at all when the gallery holds a single section: "Wszystkie" and
    that one section would lead to the same page, which is noise, not a filter.
    """
    filled = [name for name in SECTION_ORDER if counts.get(name)]
    if len(filled) < 2:
        return []

    path = reverse("gallery:index")
    options: list[tuple[str, str, int]] = [(ALL_SECTIONS, "Wszystkie", sum(counts.values()))]
    options += [(name, SECTION_LABELS[name], counts[name]) for name in filled]
    return [
        {
            "value": value,
            "label": label,
            "total": total,
            "url": path if value == ALL_SECTIONS else f"{path}?{SECTION_PARAM}={value}",
            "is_active": value == chosen,
        }
        for value, label, total in options
    ]


def _crumbs(trail: list[tuple[str, str]]) -> list[dict[str, str]]:
    """The same trail feeds the json-ld and the breadcrumbs component."""
    return [{"title": name, "url": url} for name, url in trail]


def gallery(request: HttpRequest) -> HttpResponse:
    chosen = chosen_section(request)
    images = list(selectors.published_images_in(chosen) if chosen else selectors.published_images())
    sections = services.group_by_section(images, SECTION_ORDER)
    trail = [("Start", "/"), ("Galeria", reverse("gallery:index"))]

    seo = page_seo(
        request,
        subject="Galeria",
        description=(
            "Zdjęcia ośrodka szkolenia kierowców OSK Nawrocki w Wieluniu: biuro, "
            "plac manewrowy i pojazdy szkoleniowe."
        ),
        breadcrumbs=trail,
    )
    return render(
        request,
        "gallery/gallery.html",
        {
            "seo": seo,
            "sections": [
                {"label": SECTION_LABELS[name], "images": items} for name, items in sections
            ],
            "images": images,
            "filters": section_filters(chosen, selectors.published_section_counts()),
            "chosen": chosen,
            "chosen_label": SECTION_LABELS.get(chosen, "Wszystkie"),
            "breadcrumbs": _crumbs(trail),
        },
    )


def certificates(request: HttpRequest) -> HttpResponse:
    items = list(selectors.published_certificates())
    trail = [("Start", "/"), ("Certyfikaty", reverse("gallery:certificates"))]

    seo = page_seo(
        request,
        subject="Certyfikaty",
        description=(
            "Certyfikaty i uprawnienia ośrodka szkolenia kierowców OSK Nawrocki w Wieluniu."
        ),
        breadcrumbs=trail,
    )
    return render(
        request,
        "gallery/certificates.html",
        {"seo": seo, "certificates": items, "breadcrumbs": _crumbs(trail)},
    )


def lightbox_image(request: HttpRequest, pk: int) -> HttpResponse:
    """HTMX partial: one image for the lightbox, tech.md section 5."""
    image = selectors.published_image(pk)
    return render(request, "gallery/_lightbox_image.html", {"image": image})
