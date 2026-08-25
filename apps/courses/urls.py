"""Course routes, tech.md section 5.

Each url pins the kind it serves. Without that a professional course would also
answer under /kursy/, and the same page on two urls is duplicate content.
"""

from django.urls import path

from apps.courses import views

app_name = "courses"

urlpatterns = [
    path("kursy/", views.course_list, name="list"),
    path("cennik/", views.pricing, name="pricing"),
    path("terminy/", views.intakes, name="intakes"),
    # HTMX partial, tech.md section 5.
    path("terminy/filter/", views.intake_filter, name="intake_filter"),
    path("kursy/<slug:slug>/", views.course_detail, {"kind": "license"}, name="detail"),
    path("kierowca-zawodowy/", views.pro_hub, name="pro_hub"),
    path(
        "kierowca-zawodowy/<slug:slug>/",
        views.course_detail,
        {"kind": "professional"},
        name="pro_detail",
    ),
    # Single pages, so the slug is fixed by the route, tech.md section 5.
    path(
        "badania-psychologiczne/",
        views.course_detail,
        {"slug": "badania-psychologiczne", "kind": "psychotest"},
        name="psychotests",
    ),
    path(
        "wozki-widlowe/",
        views.course_detail,
        {"slug": "wozki-widlowe", "kind": "operator"},
        name="forklifts",
    ),
]
