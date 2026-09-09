"""Core routes, tech.md section 5.

The url map puts /kontakt/, the two data pages and the flat pages on core.views,
and tech.md section 7 names core:contact, core:pass_rates, core:downloads and
core:page in NAV, so all four live here.
"""

from django.urls import path, re_path

from apps.core import views

app_name = "core"

# The flat pages tech.md section 4.1 lists, spelled out rather than left as
# <slug:slug>. A slug pattern at the root would answer for every one segment
# url on the site, and a feature slice has no business claiming that namespace.
FLAT_PAGES = "|".join(views.FLAT_PAGE_SLUGS)

urlpatterns = [
    # tech.md section 5 puts the home page on core.views.home. It is first so a
    # bare "" never reaches the flat page pattern below.
    path("", views.home, name="home"),
    path("kontakt/", views.contact, name="contact"),
    # The school's strongest argument gets a url of its own, tech.md section 1.
    path("zdawalnosc/", views.pass_rates, name="pass_rates"),
    path("do-pobrania/", views.downloads, name="downloads"),
    re_path(rf"^(?P<slug>{FLAT_PAGES})/$", views.page_detail, name="page"),
]
