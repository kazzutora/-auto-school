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
#
# Seven items, one level, no submenus. The school sells one category, so there
# is no course tree to fold away — what a visitor wants is the price, how to
# sign up, and the proof that people pass here.
NAV: tuple[NavItem, ...] = (
    # pgettext, not gettext, on three of these: the same polish words head a
    # page, where there is room for them, and sit in a menu bar that has none.
    # Measured at xl the row has 583px for the menu; the full labels came to
    # 550px in polish and overflowed outright in russian, which is 40% longer.
    # The short forms come to 465px and leave the row somewhere to grow.
    NavItem(pgettext_lazy("nav", "Kurs B"), "courses:detail", kwargs={"slug": "kat-b"}),
    NavItem(_("Cennik"), "courses:pricing"),
    NavItem(pgettext_lazy("nav", "Zapisy"), "core:page", kwargs={"slug": "zapisy"}),
    NavItem(_("Zdawalność"), "core:pass_rates"),
    NavItem(_("O nas"), "core:page", kwargs={"slug": "o-nas"}),
    NavItem(pgettext_lazy("nav", "Pliki"), "core:downloads"),
    NavItem(_("Kontakt"), "core:contact"),
)
