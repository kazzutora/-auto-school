"""What the admin calls itself, and a thumbnail for the rows that carry one.

The owner opens this to add a photograph of their own car or to fix a price.
Django's stock header says "Django administration" and its file fields say
"Currently: people/piotr.jpg" — a path, not a picture. Neither is wrong; both
are written for a developer, and the person who logs in here runs a driving
school.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import ImageField
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("OSK Ostrycharz — panel")
admin.site.site_title = _("OSK Ostrycharz")
admin.site.index_title = _("Co chcesz zmienić?")


class ThumbnailAdminMixin:
    """A picture in the list, not a file path.

    `thumbnail_field` names the ImageField; the column is added to
    list_display by whichever admin mixes this in, because where it belongs in
    the row is that admin's decision.
    """

    thumbnail_field = "image"
    thumbnail_size = 64

    @admin.display(description=_("Podgląd"))
    def thumbnail(self, obj: Any) -> str:
        image = getattr(obj, self.thumbnail_field, None)
        if not image:
            return format_html('<span style="color:#999">{}</span>', _("brak"))
        # The row's own name as the alt. An admin changelist is a table of
        # rows and the picture is the row: a screen reader with alt="" is told
        # there is an image and not which one, in the one column whose whole
        # job is telling them apart.
        return format_html(
            '<img src="{}" alt="{}" style="height:{}px;width:auto;'
            'border-radius:6px;object-fit:cover;display:block">',
            image.url,
            str(obj),
            self.thumbnail_size,
        )


def image_fields(model: Any) -> list[str]:
    """Every ImageField on a model, by name."""
    return [f.name for f in model._meta.get_fields() if isinstance(f, ImageField)]
