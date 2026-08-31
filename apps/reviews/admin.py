"""Testimonials admin, tech.md section 4.7.

The app shipped without one, so a review could be seeded but never edited,
unpublished or removed by the owner — the only way out was a shell.

is_published is editable from the list because that is the whole workflow here:
a review arrives unpublished by default and somebody has to confirm it against
its source before it reaches a page.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.reviews.models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(TranslationAdmin):
    list_display = ("author_name", "rating", "source", "published_on", "is_published", "order")
    list_filter = ("is_published", "source", "rating")
    list_editable = ("is_published", "order")
    search_fields = ("author_name", "text", "source_url")
    ordering = ("order", "id")
    date_hierarchy = "published_on"
