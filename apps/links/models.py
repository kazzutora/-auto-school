"""Useful links and faq, tech.md section 4.6."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class UsefulLink(TimeStampedModel):
    class Group(models.TextChoices):
        EXAM = "exam", _("Exam")
        GOV = "gov", _("Government")
        TESTS = "tests", _("Tests")
        LOCAL = "local", _("Local")

    group = models.CharField(choices=Group.choices, max_length=8, db_index=True)
    title = models.CharField(max_length=160)
    # Mandatory: a bare url with no explanation is not allowed.
    description = models.CharField(max_length=240)
    url = models.URLField()
    order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    # Filled by links.tasks.check_links, tech.md section 6.
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_status = models.PositiveSmallIntegerField(null=True, blank=True)
    last_error = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("group", "order", "id")

    def __str__(self) -> str:
        return self.title


class Faq(TimeStampedModel):
    question = models.CharField(max_length=240)
    answer = models.TextField()
    group = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(default=100)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQ")

    def __str__(self) -> str:
        return self.question
