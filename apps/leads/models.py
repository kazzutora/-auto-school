"""Lead model, tech.md section 4.3."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.courses.models import Course, CourseIntake


class Lead(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", _("New")
        CONTACTED = "contacted", _("Contacted")
        ENROLLED = "enrolled", _("Enrolled")
        REJECTED = "rejected", _("Rejected")
        SPAM = "spam", _("Spam")

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    intake = models.ForeignKey(
        CourseIntake, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    preferred_language = models.CharField(max_length=2, default="pl")
    message = models.TextField(blank=True, max_length=2000)
    # Mandatory at form level: a lead without consent is never created.
    consent_rodo = models.BooleanField(default=False)
    consent_marketing = models.BooleanField(default=False)
    status = models.CharField(
        choices=Status.choices, max_length=10, default=Status.NEW, db_index=True
    )
    source_path = models.CharField(max_length=200, blank=True)
    utm_source = models.CharField(max_length=80, blank=True)
    utm_medium = models.CharField(max_length=80, blank=True)
    utm_campaign = models.CharField(max_length=80, blank=True)
    # sha256(ip + salt). The raw address is never stored.
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    # Idempotency keys for the two notification tasks, tech.md section 6.
    notified_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} {self.phone}".strip()
