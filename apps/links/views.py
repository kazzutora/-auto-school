"""Links views, tech.md section 5.

Same shape as the reference slice in apps/gallery: selectors fetch, services
shape, the view assembles the section 8 SEO contract and renders.
"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from apps.core.seo import page_seo
from apps.links import selectors, services
from apps.links.models import UsefulLink

# Reading order on the page: what a candidate needs first comes first.
GROUP_ORDER = (
    UsefulLink.Group.EXAM,
    UsefulLink.Group.GOV,
    UsefulLink.Group.TESTS,
    UsefulLink.Group.LOCAL,
)

# Page copy, not data. The choice labels on the model are english until the
# locale catalogs are compiled, and this page is polish today.
GROUP_LABELS: dict[str, str] = {
    UsefulLink.Group.EXAM: "Egzamin",
    UsefulLink.Group.GOV: "Urzędy i e-usługi",
    UsefulLink.Group.TESTS: "Testy i przepisy",
    UsefulLink.Group.LOCAL: "Wieluń i okolice",
}

DESCRIPTION = (
    "Rezerwacja egzaminu, punkty karne, testy i urzędy w Wieluniu. "
    "Linki, których kandydat na kierowcę potrzebuje najczęściej."
)


def useful_links(request: HttpRequest) -> HttpResponse:
    """Every link the school sends people to, tech.md section 5."""
    links = services.publishable(list(selectors.active_links()))
    trail = [("Start", "/"), ("Przydatne linki", reverse("links:useful"))]

    groups: list[dict[str, Any]] = [
        {"label": GROUP_LABELS.get(name, name), "links": items}
        for name, items in services.group_links(links, GROUP_ORDER)
    ]

    return render(
        request,
        "links/useful_links.html",
        {
            "seo": page_seo(
                request,
                subject="Przydatne linki",
                description=DESCRIPTION,
                breadcrumbs=trail,
            ),
            "groups": groups,
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
        },
    )
