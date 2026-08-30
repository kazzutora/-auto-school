"""Template tags the cotton primitives depend on, tech.md section 7.

A cotton component is a template and cannot query anything itself, so the props
frozen in section 7 stay exactly as written and the data arrives through these
tags.
"""

import re
from typing import Any
from urllib.parse import urlsplit

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


@register.filter
def without_lead_in(html: str, heading: str) -> str:
    """The rendered markdown minus a first line that just repeats the heading.

    Course bodies are written with their own lead-in — "Uprawnia do
    kierowania:" — and the template prints a heading saying the same thing
    right above it. That is a duplicate on all fifteen course pages, and it is
    the body's line rather than the heading's that goes: the heading is the one
    the page controls and the one an anchor points at.

    Compared without the colon and without case, because that is the whole of
    the difference between the two in every case seen so far. Anything else is
    left alone: a body that opens on a real sentence keeps it.
    """
    text = str(html or "")
    wanted = str(heading or "").strip().rstrip(":").casefold()
    if not wanted:
        return text

    opening = re.match(r"\s*<p>(.*?)</p>", text, re.S)
    if not opening:
        return text

    first = re.sub(r"<[^>]+>", "", opening.group(1)).strip().rstrip(":").casefold()
    return text[opening.end() :] if first == wanted else text


@register.filter
def domain(url: str) -> str:
    """The host of a link, without the scheme or the www.

    Shown under an outbound card so a reader knows where it goes before they
    go. Not the whole address: FRONTEND.md F10 keeps bare urls off the page,
    and a path tells nobody anything a title has not already said.
    """
    host = urlsplit(str(url or "")).netloc
    return host[4:] if host.startswith("www.") else host


# What each licence category actually lets you drive, as icons from the sprite.
# A tile carrying its code alone made somebody read nine of them to find the
# bus; the shape is recognised before the letters are.
#
# The trailing categories carry two marks — the vehicle and what it tows — so
# B+E reads as a car with a trailer rather than as a letter with a plus in it.
CATEGORY_VEHICLES = {
    "AM": ("moped",),
    "A1": ("motorcycle",),
    "A2": ("motorcycle",),
    "A": ("motorcycle",),
    "B": ("car",),
    "B+E": ("car", "trailer"),
    "C": ("truck",),
    "C+E": ("truck", "trailer"),
    "D": ("bus",),
}


@register.filter
def category_vehicles(code: str) -> tuple[str, ...]:
    """The icons for a category code, or nothing for a course without one.

    Unknown codes get nothing rather than a stand-in: a wrong vehicle beside a
    category is worse than no vehicle, because somebody will believe it.
    """
    return CATEGORY_VEHICLES.get(str(code or "").strip().upper(), ())
