"""Database queries for the gallery slice.

Every query lives here, and every query that crosses a relation says so with
select_related or prefetch_related.
"""

from django.db.models import Count, QuerySet

from apps.gallery.models import Certificate, GalleryImage


def published_images() -> QuerySet[GalleryImage]:
    return GalleryImage.objects.filter(is_published=True).order_by("section", "order", "id")


def published_images_in(section: str) -> QuerySet[GalleryImage]:
    return published_images().filter(section=section)


def published_section_counts() -> dict[str, int]:
    """How many published images each section holds.

    The filter is built from this: a chip that leads to an empty page is a dead
    end, and counting in one query keeps the page at a fixed number of them.
    """
    # order_by() is cleared on purpose: the default ordering would join order
    # and id into the GROUP BY and every row would count itself.
    rows = published_images().order_by().values("section").annotate(total=Count("id"))
    return {row["section"]: row["total"] for row in rows}


def published_image(pk: int) -> GalleryImage:
    from django.shortcuts import get_object_or_404

    return get_object_or_404(GalleryImage, pk=pk, is_published=True)


def published_certificates() -> QuerySet[Certificate]:
    return Certificate.objects.filter(is_published=True).order_by("order", "id")
