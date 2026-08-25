"""SEO contract, tech.md section 8.

Every public view puts a Seo instance in the context. The rules the gate checks
live here so no slice reimplements them.
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
