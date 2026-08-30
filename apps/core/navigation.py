"""Site navigation as data, tech.md section 7.

Titles are lazy: the module is imported once at startup, while the language is
chosen per request, so a plain gettext here would freeze the whole menu into
whichever language happened to be active when the worker booted.

The menu is a list of NavItem, never markup. templates/layout/nav.html renders
this list and nothing else.
"""

from dataclasses import dataclass, field

from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


@dataclass(frozen=True)
class NavItem:
    title: str | Promise
    route: str
    kwargs: dict[str, str] = field(default_factory=dict)
    children: tuple["NavItem", ...] = ()

    def url(self) -> str:
        """Resolved lazily: routes appear as their slices ship."""
        return reverse(self.route, kwargs=self.kwargs or None)


# Kontakt is a first level item. Hiding it in a submenu is forbidden: that was
# the main defect of the old site, tech.md section 7.
NAV: tuple[NavItem, ...] = (
    NavItem(_("Kursy"), "courses:list"),
    # pgettext, not gettext: the same polish words head a page and a section,
    # where there is room for them, and sit in a menu bar that has none. In
    # russian the full phrase is 118px wider than the polish and pushed the row
    # into the language switcher. The heading keeps the full wording; only the
    # menu gets the short one.
    NavItem(pgettext_lazy("nav", "Kierowca zawodowy"), "courses:pro_hub"),
    NavItem(_("Cennik"), "courses:pricing"),
    NavItem(pgettext_lazy("nav", "Terminy"), "courses:intakes"),
    NavItem(_("O nas"), "core:page", kwargs={"slug": "o-nas"}),
    NavItem(_("Galeria"), "gallery:index"),
    NavItem(_("Kontakt"), "core:contact"),
)
