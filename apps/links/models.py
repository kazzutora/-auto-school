"""Useful links and faq, tech.md section 4.6."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

# Anything from here up is a broken link, tech.md section 4.6.
HTTP_ERROR = 400


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

    def clean(self) -> None:
        """A bare url with no explanation is not allowed, tech.md section 4.6.

        On the model and not only on the admin form: the starting set arrives
        through a script, and an imported row without a description would put a
        naked url in front of a visitor. The message carries no field name,
        because modeltranslation replaces description with description_pl on
        the form and an error keyed to a missing field breaks the admin.
        """
        super().clean()
        if not (self.description or "").strip():
            raise ValidationError(_("Link musi mieć opis."))

    @property
    def is_broken(self) -> bool:
        """What the last check found, for the admin to flag, DEV.md S7.1.

        A timeout counts as well: it leaves no status at all, and a link nobody
        can reach is as broken as one answering 404. The site keeps showing it
        either way until the owner switches is_active off.
        """
        return bool(self.last_error) or (
            self.last_status is not None and self.last_status >= HTTP_ERROR
        )

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
