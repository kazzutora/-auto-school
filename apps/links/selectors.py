"""Database queries for the links slice."""

from django.db.models import QuerySet

from apps.links.models import Faq, UsefulLink


def active_links() -> QuerySet[UsefulLink]:
    """Links the owner still stands behind.

    A broken link stays in the list on purpose, DEV.md S7.1: the check runs at
    night and a redirect or a moment of downtime must not silently empty a
    section. Only is_active takes a link off the page.
    """
    return UsefulLink.objects.filter(is_active=True).order_by("group", "order", "id")


def published_faqs() -> QuerySet[Faq]:
    """Questions the owner has answered, in the order they set."""
    return Faq.objects.filter(is_published=True).order_by("order", "id")
