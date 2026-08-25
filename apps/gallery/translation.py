"""Translated fields, the [tr] markers in tech.md section 4.5."""

from modeltranslation.translator import TranslationOptions, register

from apps.gallery.models import Certificate, GalleryImage


@register(GalleryImage)
class GalleryImageTranslationOptions(TranslationOptions):
    fields = ("alt", "caption")


@register(Certificate)
class CertificateTranslationOptions(TranslationOptions):
    fields = ("title", "issuer", "description")
