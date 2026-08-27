"""Links routes, tech.md section 5."""

from django.urls import path

from apps.links import views

app_name = "links"

urlpatterns = [
    path("przydatne-linki/", views.useful_links, name="useful"),
    path("faq/", views.faq, name="faq"),
]
