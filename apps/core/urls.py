"""Core routes, tech.md section 5.

The url map puts /kontakt/ on core.views.contact and tech.md section 7 names
the route core:contact in NAV, so both live here.
"""

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("kontakt/", views.contact, name="contact"),
]
