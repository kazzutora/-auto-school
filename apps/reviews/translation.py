"""Translated fields, the [tr] markers in tech.md section 4.7."""

from modeltranslation.translator import TranslationOptions, register

from apps.reviews.models import Testimonial


@register(Testimonial)
class TestimonialTranslationOptions(TranslationOptions):
    fields = ("text",)
