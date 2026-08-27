"""SEO contract, tech.md section 8.

Every public view puts a Seo instance in the context. The rules the gate checks
live here so no slice reimplements them.

CONTRACT GAP: DEV.md S8 wants a default og image taken from SiteSettings, and
tech.md section 4.1 freezes that model without an image field. Until the field
exists, og_image is whatever the page itself owns: a course hands over its
hero_image, every other page ships no og:image at all. A tag pointing at a
picture that does not exist is worse than the missing tag, so nothing is
invented here.
"""

from dataclasses import dataclass, field
from typing import Any

TITLE_SUFFIX = "OSK Nawrocki Wieluń"
TITLE_SEPARATOR = " — "
TITLE_LIMIT = 70
DESCRIPTION_LIMIT = 170


@dataclass
class Seo:
    title: str
    description: str
    canonical: str
    og_image: str | None = None
    robots: str = "index,follow"
    jsonld: list[dict[str, Any]] = field(default_factory=list)


def truncate_text(text: str, limit: int) -> str:
    """Shorten to limit characters without splitting a word.

    A single word longer than the limit has no word boundary to cut on, so it
    is cut hard. Everything else ends on a whole word.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed

    # One past the limit, so a boundary landing exactly on it still counts.
    head = collapsed[: limit + 1]
    if " " in head:
        return head[: head.rindex(" ")].rstrip()
    return collapsed[:limit]


def build_description(text: str, limit: int = DESCRIPTION_LIMIT) -> str:
    """Meta description, filled from lead when the database field is empty."""
    return truncate_text(text, limit)


def build_title(subject: str, limit: int = TITLE_LIMIT) -> str:
    """Compose "<subject> — OSK Nawrocki Wieluń" within the limit."""
    room = limit - len(TITLE_SEPARATOR) - len(TITLE_SUFFIX)
    if room <= 0:
        return truncate_text(subject, limit)
    head = truncate_text(subject, room)
    if not head:
        return TITLE_SUFFIX
    return f"{head}{TITLE_SEPARATOR}{TITLE_SUFFIX}"


def driving_school_jsonld(site: Any) -> dict[str, Any]:
    """schema.org DrivingSchool built from SiteSettings, tech.md section 8.

    The bank account never appears here: it stays out of public pages,
    tech.md section 1.
    """
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "DrivingSchool",
        "name": site.legal_name,
        "alternateName": site.short_name,
        "email": site.email,
        "telephone": site.phone_primary,
        "vatID": site.nip,
        "foundingDate": str(site.founded_year),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": site.street,
            "postalCode": site.postal_code,
            "addressLocality": site.city,
            "addressCountry": "PL",
        },
    }

    phones = [site.phone_secondary, site.phone_tertiary]
    extra = [phone for phone in phones if phone]
    if extra:
        data["contactPoint"] = [
            {"@type": "ContactPoint", "telephone": phone, "contactType": "customer service"}
            for phone in extra
        ]

    if site.map_lat is not None and site.map_lng is not None:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(site.map_lat),
            "longitude": float(site.map_lng),
        }

    same_as = [url for url in (site.facebook_url, site.google_business_url) if url]
    if same_as:
        data["sameAs"] = same_as

    return data


def breadcrumb_jsonld(items: list[tuple[str, str]]) -> dict[str, Any]:
    """schema.org BreadcrumbList from (title, absolute url) pairs."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": position, "name": name, "item": url}
            for position, (name, url) in enumerate(items, start=1)
        ],
    }


def page_seo(
    request: Any,
    *,
    subject: str,
    description: str,
    breadcrumbs: list[tuple[str, str]] | None = None,
    og_image: str | None = None,
    robots: str = "index,follow",
    extra_jsonld: list[dict[str, Any]] | None = None,
) -> Seo:
    """Assemble the section 8 contract for a public page.

    Every public view goes through here, so no slice has to remember that the
    canonical drops the query string or that DrivingSchool belongs on every page.
    """
    from apps.core.models import SiteSettings

    jsonld: list[dict[str, Any]] = [driving_school_jsonld(SiteSettings.get_solo())]
    if breadcrumbs:
        jsonld.append(
            breadcrumb_jsonld(
                [(name, request.build_absolute_uri(path)) for name, path in breadcrumbs]
            )
        )
    jsonld.extend(extra_jsonld or [])

    return Seo(
        title=build_title(subject),
        description=build_description(description),
        # The canonical never carries the query string.
        canonical=request.build_absolute_uri(request.path),
        og_image=og_image,
        robots=robots,
        jsonld=jsonld,
    )
