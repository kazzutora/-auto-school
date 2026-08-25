"""Translated fields, the [tr] markers in tech.md section 4.4."""

from modeltranslation.translator import TranslationOptions, register

from apps.people.models import Instructor, Vehicle


@register(Instructor)
class InstructorTranslationOptions(TranslationOptions):
    fields = ("role", "bio")


@register(Vehicle)
class VehicleTranslationOptions(TranslationOptions):
    fields = ("note",)
