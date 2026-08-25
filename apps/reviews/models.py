"""Testimonials, tech.md section 4.7.

Entered by hand from real sources with a source_url. Synthetic reviews are
forbidden.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Testimonial(TimeStampedModel):
    class Source(models.TextChoices):
        GOOGLE = "google", "Google"
        MANUAL = "manual", _("Manual")
        FACEBOOK = "facebook", "Facebook"

    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    source = models.CharField(choices=Source.choices, max_length=10, default=Source.MANUAL)
    source_url = models.URLField(blank=True)
    published_on = models.DateField(null=True, blank=True)
    # Only manually confirmed reviews go public.
    is_published = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return f"{self.author_name} {self.rating}/5"
