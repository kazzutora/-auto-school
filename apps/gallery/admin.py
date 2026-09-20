"""Gallery admin, the shape every slice copies."""

from django.contrib import admin
from django.http import HttpRequest
from modeltranslation.admin import TranslationAdmin

from apps.gallery.models import Certificate, GalleryImage
from apps.gallery.tasks import build_renditions
from apps.core.admin_site import ThumbnailAdminMixin


@admin.register(GalleryImage)
class GalleryImageAdmin(ThumbnailAdminMixin, TranslationAdmin):
    list_display = ("thumbnail", "alt", "section", "order", "is_published", "legacy_name")
    list_filter = ("section", "is_published")
    search_fields = ("alt", "caption", "legacy_name")
    list_editable = ("order", "is_published")
    ordering = ("section", "order", "id")

    def save_model(
        self, request: HttpRequest, obj: GalleryImage, form: object, change: bool
    ) -> None:
        super().save_model(request, obj, form, change)
        # Renditions are built off the request, tech.md section 6.
        build_renditions.delay(model="gallery.GalleryImage", pk=obj.pk)


@admin.register(Certificate)
class CertificateAdmin(ThumbnailAdminMixin, TranslationAdmin):
    list_display = ("thumbnail", "title", "issuer", "issued_on", "order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "issuer", "description")
    ordering = ("order", "id")

    def save_model(
        self, request: HttpRequest, obj: Certificate, form: object, change: bool
    ) -> None:
        super().save_model(request, obj, form, change)
        build_renditions.delay(model="gallery.Certificate", pk=obj.pk)
