"""Translated fields, the [tr] markers in tech.md section 4.6."""

from modeltranslation.translator import TranslationOptions, register

from apps.links.models import Faq, UsefulLink


@register(UsefulLink)
class UsefulLinkTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(Faq)
class FaqTranslationOptions(TranslationOptions):
    fields = ("question", "answer", "group")
