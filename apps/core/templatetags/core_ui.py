"""Template tags the cotton primitives depend on, tech.md section 7.

A cotton component is a template and cannot query anything itself, so the props
frozen in section 7 stay exactly as written and the data arrives through these
tags.
"""

from typing import Any

from django import template
from django.conf import settings
from django.http import HttpRequest
from django.urls import NoReverseMatch, translate_url
from django.utils import timezone, translation

from apps.core.imaging import webp_srcset as build_webp_srcset
from apps.core.models import OpeningHours
from apps.core.navigation import NAV, NavItem
from apps.core.services import is_open_at

register = template.Library()

WEEKDAYS = (
    ("Poniedziałek", "Понедельник", "Понеділок"),
    ("Wtorek", "Вторник", "Вівторок"),
    ("Środa", "Среда", "Середа"),
    ("Czwartek", "Четверг", "Четвер"),
    ("Piątek", "Пятница", "П'ятниця"),
    ("Sobota", "Суббота", "Субота"),
    ("Niedziela", "Воскресенье", "Неділя"),
)
_LANGUAGE_COLUMN = {"pl": 0, "ru": 1, "uk": 2}


@register.simple_tag
def webp_srcset(source: Any) -> str:
    """WebP srcset for an ImageField, tech.md section 6."""
    return build_webp_srcset(source)


@register.simple_tag
def nav_items() -> tuple[NavItem, ...]:
    """Navigation is data, tech.md section 7."""
    return NAV


@register.simple_tag
def nav_url(item: NavItem) -> str:
    """Empty string while a slice has not shipped its urls yet."""
    try:
        return item.url()
    except NoReverseMatch:
        return ""


@register.simple_tag
def opening_hours(department: str) -> list[dict[str, Any]]:
    """One row per weekday, including the days the department stays closed."""
    column = _LANGUAGE_COLUMN.get(translation.get_language() or "pl", 0)
    rows = {row.weekday: row for row in OpeningHours.objects.filter(department=department)}
    today = timezone.localtime().weekday()

    return [
        {
            "weekday": weekday,
            "label": names[column],
            "row": rows.get(weekday),
            "is_today": weekday == today,
        }
        for weekday, names in enumerate(WEEKDAYS)
    ]


@register.simple_tag
def is_open_now(department: str) -> bool:
    rows = OpeningHours.objects.filter(department=department)
    return is_open_at(rows, timezone.localtime())


@register.simple_tag(takes_context=True)
def language_links(context: template.Context) -> list[dict[str, str | bool]]:
    """Same path in every language, for the switcher."""
    request: HttpRequest | None = context.get("request")
    active = translation.get_language()
    if request is None:
        return []

    path = request.get_full_path()
    return [
        {
            "code": code,
            "label": label,
            "url": translate_url(path, code),
            "is_active": code == active,
        }
        for code, label in settings.LANGUAGES
    ]


# The seed marks every value the owner still owes with this prefix, tech.md
# section 16, and `pytest -m owner_data` lists them. The marker is for us, not
# for the visitor: whatever the state of the data, a page must never print the
# word TODO at somebody who came to book a driving lesson.
OWNER_TODO = "TODO_OWNER:"


@register.filter
def owner_ready(value: Any) -> str:
    """The text, or nothing at all if it is still a placeholder.

    Empty rather than a stand-in, because every caller already guards on the
    field being empty — a placeholder for a placeholder would just be a second
    thing to explain.
    """
    text = str(value or "").strip()
    return "" if text.startswith(OWNER_TODO) else text
