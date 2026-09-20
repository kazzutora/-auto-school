"""Translated fields, the [tr] markers in tech.md section 4.1."""

from modeltranslation.translator import TranslationOptions, register

from apps.core.models import DownloadFile, OpeningHours, Page, PassRate


@register(OpeningHours)
class OpeningHoursTranslationOptions(TranslationOptions):
    fields = ("note",)


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "lead", "body", "seo_title", "seo_desc")


@register(DownloadFile)
class DownloadFileTranslationOptions(TranslationOptions):
    fields = ("title", "description", "group")


@register(PassRate)
class PassRateTranslationOptions(TranslationOptions):
    fields = ("note",)
