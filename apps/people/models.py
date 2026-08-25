"""Instructors and vehicles, tech.md section 4.4."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Instructor(TimeStampedModel):
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    since_year = models.PositiveSmallIntegerField(null=True, blank=True)
    categories = models.ManyToManyField(
        Course, blank=True, limit_choices_to={"kind": "license"}, related_name="instructors"
    )
    photo = models.ImageField(upload_to="people/", blank=True)
    order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.full_name


class Vehicle(TimeStampedModel):
    class Gearbox(models.TextChoices):
        MANUAL = "manual", _("Manual")
        AUTO = "auto", _("Automatic")

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="vehicles")
    make = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    gearbox = models.CharField(choices=Gearbox.choices, max_length=8, default=Gearbox.MANUAL)
    note = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to="vehicles/", blank=True)
    is_exam_spec = models.BooleanField(
        default=True, help_text=_("zgodny z wymogami egzaminacyjnymi")
    )
    order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return f"{self.make} {self.model}"
