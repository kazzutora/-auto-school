"""Course models, tech.md section 4.2. The schema is frozen: no extra fields."""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Course(TimeStampedModel):
    class Kind(models.TextChoices):
        LICENSE = "license", "Kategoria prawa jazdy"
        PROFESSIONAL = "professional", "Kierowca zawodowy"
        PSYCHOTEST = "psychotest", "Badania psychologiczne"
        OPERATOR = "operator", "Uprawnienia operatora"

    kind = models.CharField(choices=Kind.choices, max_length=16, db_index=True)
    slug = models.SlugField(unique=True)  # kat-b, kwalifikacja-wstepna …
    code = models.CharField(max_length=16, blank=True)  # "B", "B+E", "ADR"
    title = models.CharField(max_length=160)
    lead = models.TextField(blank=True)  # one or two sentences on the card
    entitlements = models.TextField(blank=True)  # markdown list
    requirements = models.TextField(blank=True)  # markdown list
    body = models.TextField(blank=True)  # markdown
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    theory_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    practice_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    total_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    price_gross = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_note = models.CharField(max_length=160, blank=True)
    languages = ArrayField(models.CharField(max_length=2), default=list)  # ["pl","ru","uk"]
    hero_image = models.ImageField(upload_to="courses/", blank=True)
    hero_alt = models.CharField(max_length=160, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_desc = models.CharField(max_length=170, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ("kind", "order", "id")
        indexes = [models.Index(fields=["kind", "is_active"])]

    def __str__(self) -> str:
        return self.title


class CourseIntake(TimeStampedModel):
    """A group start, tech.md section 4.2."""

    class Mode(models.TextChoices):
        STATIONARY = "stationary", _("Stationary")
        ELEARNING = "elearning", _("E-learning")
        MIXED = "mixed", _("Mixed")

    class Status(models.TextChoices):
        PLANNED = "planned", _("Planned")
        OPEN = "open", _("Open")
        FULL = "full", _("Full")
        CLOSED = "closed", _("Closed")

    course = models.ForeignKey(Course, related_name="intakes", on_delete=models.PROTECT)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True)
    mode = models.CharField(choices=Mode.choices, max_length=12)
    language = models.CharField(max_length=2, default="pl")
    seats_total = models.PositiveSmallIntegerField(null=True, blank=True)
    seats_taken = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        choices=Status.choices, max_length=8, default=Status.PLANNED, db_index=True
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("start_date",)
        indexes = [models.Index(fields=["status", "start_date"])]

    def __str__(self) -> str:
        return f"{self.course} {self.start_date}"


class PriceItem(TimeStampedModel):
    """Extra services priced outside a course, tech.md section 4.2."""

    title = models.CharField(max_length=160)
    note = models.CharField(max_length=200, blank=True)
    price_gross = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=40, blank=True)  # "za godzinę", "za osobę"
    group = models.CharField(max_length=40, blank=True)  # "Jazdy doszkalające"
    order = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("group", "order", "id")

    def __str__(self) -> str:
        return self.title
