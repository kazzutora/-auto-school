"""Root router. Slice routes land in the i18n block, tech.md section 5."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.health import healthz
from apps.core.sitemaps import sitemap
from apps.core.views import robots

urlpatterns = [
    # Infrastructure, never language prefixed: the deploy smoke step and the
    # container healthcheck both call it, tech.md section 17.
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Crawler files are never language prefixed: one sitemap, one robots.txt,
    # tech.md section 5.
    path("sitemap.xml", sitemap, name="sitemap"),
    path("robots.txt", robots, name="robots"),
]

# Polish carries no prefix, russian and ukrainian get /ru/ and /uk/.
urlpatterns += i18n_patterns(
    path("", include("apps.core.urls")),
    path("", include("apps.courses.urls")),
    path("", include("apps.gallery.urls")),
    path("", include("apps.leads.urls")),
    path("", include("apps.links.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    from apps.core.views import kitchen_sink, ornament_sandbox

    # Review surfaces for the design system, DEV.md S0.7 and ROSE.md K3 point
    # 7. Debug only, and robots.txt keeps them out of the index either way.
    urlpatterns += [
        path("__kitchen-sink/", kitchen_sink, name="kitchen_sink"),
        path("__ornament/", ornament_sandbox, name="ornament_sandbox"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
