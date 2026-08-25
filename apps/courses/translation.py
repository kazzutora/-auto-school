"""Translated fields, the [tr] markers in tech.md section 4.2."""

from modeltranslation.translator import TranslationOptions, register

from apps.courses.models import Course, CourseIntake, PriceItem


@register(Course)
class CourseTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "lead",
        "entitlements",
        "requirements",
        "body",
        "price_note",
        "hero_alt",
        "seo_title",
        "seo_desc",
    )


@register(CourseIntake)
class CourseIntakeTranslationOptions(TranslationOptions):
    fields = ("note",)


@register(PriceItem)
class PriceItemTranslationOptions(TranslationOptions):
    fields = ("title", "note", "unit", "group")
