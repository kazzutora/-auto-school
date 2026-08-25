"""Translated fields, the [tr] markers in tech.md section 4.1."""

from modeltranslation.translator import TranslationOptions, register

from apps.core.models import OpeningHours, Page


@register(OpeningHours)
class OpeningHoursTranslationOptions(TranslationOptions):
    fields = ("note",)


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "lead", "body", "seo_title", "seo_desc")
