"""Links views, tech.md section 5.

Same shape as the reference slice in apps/gallery: selectors fetch, services
shape, the view assembles the section 8 SEO contract and renders.
"""

from collections.abc import Mapping
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.markdown import render_markdown
from apps.core.seo import Label, build_description, page_seo
from apps.links import selectors, services
from apps.links.models import Faq, UsefulLink

# Reading order on the page: what a candidate needs first comes first.
GROUP_ORDER = (
    UsefulLink.Group.EXAM,
    UsefulLink.Group.GOV,
    UsefulLink.Group.TESTS,
    UsefulLink.Group.LOCAL,
)

# Page copy, not data. The choice labels on the model are english until the
# locale catalogs are compiled, and this page is polish today.
GROUP_LABELS: dict[str, Label] = {
    UsefulLink.Group.EXAM: _("Egzamin"),
    UsefulLink.Group.GOV: _("Urzędy i e-usługi"),
    UsefulLink.Group.TESTS: _("Testy i przepisy"),
    UsefulLink.Group.LOCAL: _("Wieluń i okolice"),
}

DESCRIPTION = _(
    "Rezerwacja egzaminu, punkty karne, testy i urzędy w Wieluniu. "
    "Linki, których kandydat na kierowcę potrzebuje najczęściej."
)


def useful_links(request: HttpRequest) -> HttpResponse:
    """Every link the school sends people to, tech.md section 5."""
    links = services.publishable(list(selectors.active_links()))
    trail: list[tuple[Label, str]] = [
        (_("Start"), "/"),
        (_("Przydatne linki"), reverse("links:useful")),
    ]

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
                subject=_("Przydatne linki"),
                description=DESCRIPTION,
                breadcrumbs=trail,
            ),
            "groups": groups,
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
        },
    )


FAQ_DESCRIPTION = (
    "Odpowiedzi na pytania, które słyszymy przez telefon: wiek, dokumenty, PKK, "
    "ceny i terminy kursów w Wieluniu."
)


def faq_jsonld(questions: list[Faq], answers: Mapping[int, str]) -> dict[str, Any]:
    """schema.org FAQPage, tech.md section 8.

    The answer goes in rendered rather than as raw markdown: schema.org allows
    html in an answer, and a search result should not show a visitor the
    asterisks the owner typed around a bold word.
    """
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question.question,
                "acceptedAnswer": {"@type": "Answer", "text": answers[question.pk]},
            }
            for question in questions
        ],
    }


def faq(request: HttpRequest) -> HttpResponse:
    """Questions the office answers over and over, tech.md section 5."""
    questions = list(selectors.published_faqs())
    answers = {item.pk: render_markdown(item.answer) for item in questions}
    trail: list[tuple[Label, str]] = [(_("Start"), "/"), ("FAQ", reverse("links:faq"))]

    groups = [
        {
            "label": label,
            "questions": [
                {"question": item.question, "answer": answers[item.pk]} for item in items
            ],
        }
        for label, items in services.group_questions(questions)
    ]

    return render(
        request,
        "links/faq.html",
        {
            "seo": page_seo(
                request,
                subject=_("Najczęstsze pytania"),
                description=build_description(FAQ_DESCRIPTION),
                breadcrumbs=trail,
                # An empty FAQPage says nothing, so it is only emitted with
                # questions in it.
                extra_jsonld=[faq_jsonld(questions, answers)] if questions else [],
            ),
            "groups": groups,
            "questions": questions,
            "breadcrumbs": [{"title": name, "url": url} for name, url in trail],
        },
    )
