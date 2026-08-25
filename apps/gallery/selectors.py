"""Database queries for the gallery slice.

Every query lives here, and every query that crosses a relation says so with
select_related or prefetch_related.
"""

from django.db.models import QuerySet

from apps.gallery.models import Certificate, GalleryImage


def published_images() -> QuerySet[GalleryImage]:
    return GalleryImage.objects.filter(is_published=True).order_by("section", "order", "id")


def published_images_in(section: str) -> QuerySet[GalleryImage]:
    return published_images().filter(section=section)


def published_image(pk: int) -> GalleryImage:
    from django.shortcuts import get_object_or_404

    return get_object_or_404(GalleryImage, pk=pk, is_published=True)


def published_certificates() -> QuerySet[Certificate]:
    return Certificate.objects.filter(is_published=True).order_by("order", "id")
