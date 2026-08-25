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


def _crumbs(trail: list[tuple[str, str]]) -> list[dict[str, str]]:
    """The same trail feeds the json-ld and the breadcrumbs component."""
    return [{"title": name, "url": url} for name, url in trail]


def gallery(request: HttpRequest) -> HttpResponse:
    images = list(selectors.published_images())
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
    labels = dict(GalleryImage.Section.choices)
    return render(
        request,
        "gallery/gallery.html",
        {
            "seo": seo,
            "sections": [(labels[name], items) for name, items in sections],
            "images": images,
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
