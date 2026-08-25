"""Core views."""

from datetime import date
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

from django import forms
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.core.seo import Seo, build_title

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
