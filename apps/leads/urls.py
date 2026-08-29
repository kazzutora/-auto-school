"""Enrolment routes, tech.md section 5."""

from django.urls import path

from apps.leads import views

app_name = "leads"

urlpatterns = [
    path("zapisz-sie/", views.enroll, name="enroll"),
    # HTMX partial, tech.md section 5. Also the target of a plain form post.
    path("zapisz-sie/submit/", views.submit, name="submit"),
    path("zapisz-sie/dziekujemy/", views.thanks, name="thanks"),
]
