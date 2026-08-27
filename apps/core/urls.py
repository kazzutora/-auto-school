"""Core routes, tech.md section 5.

The url map puts /kontakt/ and the flat pages on core.views, and tech.md
section 7 names the routes core:contact and core:page in NAV, so both live here.
"""

from django.urls import path, re_path

from apps.core import views

app_name = "core"

# The three flat pages tech.md section 4.1 lists, spelled out rather than left
# as <slug:slug>. A slug pattern at the root would answer for every one segment
# url on the site, and a feature slice has no business claiming that namespace.
FLAT_PAGES = "|".join(views.FLAT_PAGE_SLUGS)

urlpatterns = [
    path("kontakt/", views.contact, name="contact"),
    re_path(rf"^(?P<slug>{FLAT_PAGES})/$", views.page_detail, name="page"),
]
