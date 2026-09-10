"""sitemap.xml, tech.md sections 5 and 8.

Courses and flat pages carry their own updated_at, so lastmod is real. The
static routes have nothing to date and are listed without one rather than with
a made up timestamp.

The view is ours rather than django.contrib.sitemaps.views.sitemap because that
one builds every absolute url from the django.contrib.sites row, which holds
example.com until somebody remembers to edit it in the admin. A sitemap full of
example.com urls is worse than no sitemap, and the rest of the section 8
contract, canonical and hreflang included, already speaks the host that asked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.contrib.sitemaps import Sitemap
from django.contrib.sites.requests import RequestSite
from django.db.models import QuerySet
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.urls import reverse

from apps.core.models import Page
from apps.core.views import FLAT_PAGE_SLUGS
from apps.courses.models import Course

# Routes that are not a row in any table, tech.md section 5.
#
# Psychotests, forklifts and the professional courses are gone from this list:
# they are courses with a url of their own, and this school sells none of them,
# so their pages answer 404. A sitemap that advertises a 404 spends crawl budget
# proving the site is broken.
STATIC_ROUTES = (
    "core:home",
    "courses:list",
    "courses:pricing",
    "courses:intakes",
    "core:pass_rates",
    "core:downloads",
    "gallery:index",
    "gallery:certificates",
    "links:useful",
    "links:faq",
    "core:contact",
)


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self) -> list[str]:
        return list(STATIC_ROUTES)

    def location(self, item: str) -> str:
        return reverse(item)


class CourseSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self) -> QuerySet[Course]:
        return Course.objects.filter(is_active=True).order_by("kind", "order", "id")

    def lastmod(self, item: Course) -> datetime:
        return item.updated_at


class PageSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.4

    def items(self) -> QuerySet[Page]:
        # Only the slugs that have a url. A Page can also be a block on another
        # page, and those have nowhere to point.
        return Page.objects.filter(is_published=True, slug__in=FLAT_PAGE_SLUGS).order_by("slug")

    def location(self, item: Page) -> str:
        return reverse("core:page", kwargs={"slug": item.slug})

    def lastmod(self, item: Page) -> datetime:
        return item.updated_at


SITEMAPS: dict[str, type[Sitemap]] = {
    "static": StaticSitemap,
    "courses": CourseSitemap,
    "pages": PageSitemap,
}

# The file itself is a crawler instruction, not a page to index.
CRAWLER_HEADERS = {"X-Robots-Tag": "noindex, noodp, noarchive"}


def sitemap(request: HttpRequest) -> TemplateResponse:
    """The whole map in one file, tech.md section 5.

    Everything here fits far inside the 50 000 url limit of the format, so
    there is one page and no index file to keep in step with it.
    """
    site = RequestSite(request)
    urls: list[dict[str, Any]] = []
    for section in SITEMAPS.values():
        urls.extend(section().get_urls(site=site, protocol=request.scheme))

    return TemplateResponse(
        request,
        "sitemap.xml",
        {"urlset": urls},
        content_type="application/xml",
        headers=CRAWLER_HEADERS,
    )
