"""Root router. Slice routes land in the i18n block, tech.md section 5."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
]

# Polish carries no prefix, russian and ukrainian get /ru/ and /uk/.
urlpatterns += i18n_patterns(prefix_default_language=False)

if settings.DEBUG:
    from apps.core.views import kitchen_sink

    # Review surface for the design system, DEV.md S0.7. Debug only.
    urlpatterns += [path("__kitchen-sink/", kitchen_sink, name="kitchen_sink")]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
