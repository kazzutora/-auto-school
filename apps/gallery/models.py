"""Gallery and certificates, tech.md section 4.5."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class GalleryImage(TimeStampedModel):
    class Section(models.TextChoices):
        SCHOOL = "school", _("School")
        VEHICLES = "vehicles", _("Vehicles")
        YARD = "yard", _("Yard")
        EVENTS = "events", _("Events")

    section = models.CharField(choices=Section.choices, max_length=10, db_index=True)
    image = models.ImageField(upload_to="gallery/")
    # Mandatory: an empty alt fails validation and the a11y gate.
    alt = models.CharField(max_length=160)
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=100)
    is_published = models.BooleanField(default=True)
    # "1.JPG", ties a row to the export of the old site.
    legacy_name = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ("section", "order", "id")

    def __str__(self) -> str:
        return self.alt


class Certificate(TimeStampedModel):
    # Mandatory: the old site showed 11 scans with no captions at all.
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=160, blank=True)
    issued_on = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="certificates/")
    file = models.FileField(upload_to="certificates/pdf/", blank=True)
    order = models.PositiveSmallIntegerField(default=100)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")

    def clean(self) -> None:
        """A scan with no title is exactly what the old site shipped, eleven
        times over, DEV.md S6.2.

        Checked on the model and not only on the admin form, so an import or a
        management command cannot put an unnamed scan in front of a visitor.
        The message is not attached to a field: modeltranslation replaces title
        with title_pl on the form, and an error keyed to a field the form does
        not have would blow up the admin instead of showing the problem.
        """
        super().clean()
        if not (self.title or "").strip():
            raise ValidationError(_("Certyfikat musi mieć tytuł."))

    @property
    def alt(self) -> str:
        """A scan shows the document, so its title is also its alt text.

        Named alt because that is what the picture component and the lightbox
        ask every row for, tech.md section 7.
        """
        return self.title

    def __str__(self) -> str:
        return self.title
