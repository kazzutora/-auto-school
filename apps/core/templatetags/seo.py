"""Template tags for the SEO contract, tech.md section 8."""

import json
from typing import Any

from django import template
from django.conf import settings
from django.http import HttpRequest
from django.urls import translate_url
from django.utils.safestring import SafeString, mark_safe

from apps.core.seo import Seo

register = template.Library()

# Same escaping django.utils.html.json_script applies: a payload must never be
# able to close the script element it sits in.
_JSON_ESCAPES = {ord("<"): r"\u003C", ord(">"): r"\u003E", ord("&"): r"\u0026"}


def alternate_links(request: HttpRequest | None) -> list[dict[str, str]]:
    """hreflang for every language plus x-default on polish, tech.md section 8."""
    if request is None:
        return []

    current = request.get_full_path()
    links = [
        {"hreflang": code, "href": request.build_absolute_uri(translate_url(current, code))}
        for code, _label in settings.LANGUAGES
    ]
    links.append(
        {
            "hreflang": "x-default",
            "href": request.build_absolute_uri(translate_url(current, settings.LANGUAGE_CODE)),
        }
    )
    return links


@register.inclusion_tag("seo/meta.html", takes_context=True)
def seo_meta(context: template.Context) -> dict[str, Any]:
    seo = context.get("seo")
    request = context.get("request")
    return {"seo": seo, "alternates": alternate_links(request)}


@register.simple_tag(takes_context=True)
def jsonld(context: template.Context) -> SafeString:
    seo = context.get("seo")
    if not isinstance(seo, Seo) or not seo.jsonld:
        return mark_safe("")

    blocks = []
    for item in seo.jsonld:
        payload = json.dumps(item, ensure_ascii=False).translate(_JSON_ESCAPES)
        blocks.append(f'<script type="application/ld+json">{payload}</script>')
    return mark_safe("".join(blocks))
