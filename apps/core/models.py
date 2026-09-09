"""Core models, tech.md section 4.1."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel


class TimeStampedModel(models.Model):
    """Base for every model in the project, tech.md section 4."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Django adds this implicitly. Declared here because django-stubs cannot
    # resolve a manager it never sees, and declaring it on the concrete
    # models instead makes it worse.
    objects = models.Manager()

    class Meta:
        abstract = True


class SiteSettings(SingletonModel, TimeStampedModel):
    legal_name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=80, default="OSK Ostrycharz")
    street = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=80)
    nip = models.CharField(max_length=20)
    email = models.EmailField()
    phone_primary = models.CharField(max_length=32)
    phone_secondary = models.CharField(max_length=32, blank=True)
    phone_tertiary = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    bank_account = models.CharField(max_length=40, blank=True)
    # Never rendered on a public page unless this is switched on, tech.md section 1.
    bank_account_public = models.BooleanField(default=False)
    founded_year = models.PositiveSmallIntegerField(default=1996)
    map_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    map_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    facebook_url = models.URLField(blank=True)
    google_business_url = models.URLField(blank=True)
    lead_notify_emails = models.CharField(max_length=300, help_text=_("comma separated"))
    analytics_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Site settings")

    def __str__(self) -> str:
        return self.short_name

    @property
    def phones(self) -> list[str]:
        """The numbers that are actually filled in, in display order."""
        candidates = (self.phone_primary, self.phone_secondary, self.phone_tertiary)
        return [phone for phone in candidates if phone]

    @property
    def notify_emails(self) -> list[str]:
        """lead_notify_emails split into addresses, tech.md section 6."""
        return [part.strip() for part in self.lead_notify_emails.split(",") if part.strip()]


class OpeningHours(TimeStampedModel):
    class DEPT(models.TextChoices):
        OFFICE = "office", _("Office")
        PSYCHOLOGY = "psychology", _("Psychology lab")

    department = models.CharField(choices=DEPT.choices, max_length=16)
    weekday = models.PositiveSmallIntegerField()  # 0=Mon … 6=Sun
    opens = models.TimeField(null=True, blank=True)  # null = closed that day
    closes = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("department", "weekday")
        ordering = ("department", "weekday")
        verbose_name_plural = _("Opening hours")

    def __str__(self) -> str:
        return f"{self.get_department_display()} {self.weekday}"

    @property
    def is_closed(self) -> bool:
        return self.opens is None or self.closes is None


class Page(TimeStampedModel):
    """Flat pages: o-nas, polityka-prywatnosci, rodo."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    lead = models.TextField(blank=True)
    body = models.TextField()  # markdown
    seo_title = models.CharField(max_length=70, blank=True)
    seo_desc = models.CharField(max_length=170, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("slug",)

    def __str__(self) -> str:
        return self.title
