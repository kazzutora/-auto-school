"""Core models, tech.md section 4.1."""

from typing import Any

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
    # Nullable, and null is the honest default. The previous client had been
    # trading since 1996 and said so; this one publishes no founding year at
    # all, and a template that falls back to a number prints a fact nobody
    # supplied. Every place that shows it checks first.
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    map_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    map_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    facebook_url = models.URLField(blank=True)
    google_business_url = models.URLField(blank=True)
    # The channel, and one promo clip for the home page. Both are urls and
    # neither pulls a script: tech.md section 2 bans third party javascript on
    # public pages, so the clip is rendered as a poster plus a link.
    youtube_url = models.URLField(blank=True)
    youtube_video_url = models.URLField(blank=True)
    # The still frame the clip is shown behind. Uploaded, not fetched: youtube's
    # own thumbnail lives on i.ytimg.com, and a page that pulls it has already
    # told google somebody is reading before they clicked anything.
    youtube_poster = models.ImageField(upload_to="site/", blank=True)
    youtube_poster_alt = models.CharField(max_length=160, blank=True)
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


class PassRate(TimeStampedModel):
    """Exam results by year, tech.md section 4.1.

    The strongest thing this school has to say about itself: three quarters of
    its candidates pass at the first attempt. On the old site it sat as a
    paragraph in the middle of a one-page document, so it is a table with a page
    of its own here.

    Percentages are not stored. They are derived in apps/core/services.py from
    the counts, because a stored percentage and a stored count are two facts
    that can disagree, and the one that would be wrong is the one on screen.
    """

    year = models.PositiveSmallIntegerField(unique=True, db_index=True)
    students = models.PositiveSmallIntegerField()
    passed_1st = models.PositiveSmallIntegerField()
    passed_2nd = models.PositiveSmallIntegerField(default=0)
    passed_3rd = models.PositiveSmallIntegerField(default=0)
    passed_4th = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=200, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("-year",)
        verbose_name = _("Pass rate")
        verbose_name_plural = _("Pass rates")

    def __str__(self) -> str:
        return f"{self.year}: {self.passed_1st}/{self.students}"

    @property
    def attempts(self) -> list[int]:
        """The four counts in order, so a template can loop rather than branch."""
        return [self.passed_1st, self.passed_2nd, self.passed_3rd, self.passed_4th]


class DownloadFile(TimeStampedModel):
    """A document a candidate needs before the course starts, tech.md 4.1.

    Regulamin, umowa, oświadczenia. The size is filled in on save from the file
    itself rather than typed by hand: a number somebody keyed in is a number
    that goes stale the first time the pdf is replaced.
    """

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to="documents/", blank=True)
    size_bytes = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=100)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Keep size_bytes in step with whatever file is attached.

        A missing file clears the size rather than leaving the previous one:
        a row waiting for the owner to upload the pdf must not advertise
        "1,2 MB" of nothing.
        """
        self.size_bytes = self._file_size()
        super().save(*args, **kwargs)

    def _file_size(self) -> int | None:
        """Bytes on disk, or None when there is nothing to measure.

        A row can name a file the storage no longer holds — the owner deleted
        it, or the media volume was rebuilt from a database dump. Asking such a
        field for its size raises, and a document list is not the place to take
        the whole page down over it.
        """
        if not self.file:
            return None
        try:
            return int(self.file.size)
        except (OSError, ValueError):
            return None
