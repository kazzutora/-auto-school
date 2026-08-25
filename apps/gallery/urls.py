"""Gallery routes, tech.md section 5."""

from django.urls import path

from apps.gallery import views

app_name = "gallery"

urlpatterns = [
    path("galeria/", views.gallery, name="index"),
    path("certyfikaty/", views.certificates, name="certificates"),
    # HTMX partial, tech.md section 5.
    path("galeria/lightbox/<int:pk>/", views.lightbox_image, name="lightbox"),
]
