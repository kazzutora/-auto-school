from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PeopleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.people"
    # What the admin index calls this group. Django prints the module
    # name otherwise, and "Core" means nothing to the person who runs
    # the school.
    verbose_name = _("Instruktorzy i pojazdy")
