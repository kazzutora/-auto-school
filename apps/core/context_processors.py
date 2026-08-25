"""Context processors, tech.md section 3."""

from typing import Any

from django.http import HttpRequest

from apps.core.models import SiteSettings


def site_settings(request: HttpRequest) -> dict[str, Any]:
    """SiteSettings on every template, so no view has to pass it."""
    return {"site_settings": SiteSettings.get_solo()}
