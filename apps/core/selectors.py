"""Database queries for the core slice, the same shape as apps/gallery.

Nothing here computes: percentages and file sizes are apps/core/services.py,
which touches no ORM. This module only decides which rows a page may see.
"""

from django.db.models import QuerySet

from apps.core.models import DownloadFile, PassRate


def published_pass_rates() -> QuerySet[PassRate]:
    """Exam results the owner has confirmed, newest year first."""
    return PassRate.objects.filter(is_published=True).order_by("-year")


def latest_pass_rate() -> PassRate | None:
    """The most recent confirmed year, or None before the first one lands.

    Every caller has to survive the None: the home page leads with this number
    and still has to render on a database seeded an hour ago.
    """
    return published_pass_rates().first()


def published_downloads() -> QuerySet[DownloadFile]:
    """Documents that actually have a file behind them.

    A row waiting for the owner to upload the pdf is excluded here rather than
    in the template: a "Pobierz" button pointing at nothing is worse than a
    shorter list, and the owner_data report already tracks the gap.
    """
    return DownloadFile.objects.filter(is_published=True).exclude(file="").order_by("order", "id")
