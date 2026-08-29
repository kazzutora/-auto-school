"""Database queries for the reviews slice.

Same shape as the reference slice in apps/gallery: every query lives here.
"""

from django.db.models import QuerySet

from apps.reviews.models import Testimonial


def published_testimonials() -> QuerySet[Testimonial]:
    """Confirmed reviews that a reader can go and check for themselves.

    FRONTEND.md A.9 point 7 is blunt about the rule underneath this: no invented
    reviews under any circumstances. A testimonial with nowhere to verify it is
    indistinguishable from one, so the empty source_url is excluded here rather
    than left to each template to remember.
    """
    return Testimonial.objects.filter(is_published=True).exclude(source_url="")
