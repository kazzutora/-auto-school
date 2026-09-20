from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    # What the admin index calls this group. Django prints the module
    # name otherwise, and "Core" means nothing to the person who runs
    # the school.
    verbose_name = _("Ośrodek i strony")

    def ready(self) -> None:
        # The admin's own title and the thumbnail mixin. Importing for the
        # side effect is how Django expects a branded admin to be wired.
        from apps.core import admin_site  # noqa: F401
