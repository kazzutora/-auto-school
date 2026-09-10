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
    # pgettext on every one of them, and that is the point. The same polish
    # words head a page, where there is room for them, and sit in a menu bar
    # that has none — but the binding case is not polish. Measured at xl the row
    # has 583px for the menu; the full polish labels came to 550px and the
    # russian translations of them to 1136px of header against 1104px of
    # container. A nav context on every item is what lets each language pick a
    # label that fits without any of them dragging the others short.
    NavItem(pgettext_lazy("nav", "Kurs B"), "courses:detail", kwargs={"slug": "kat-b"}),
    NavItem(pgettext_lazy("nav", "Cennik"), "courses:pricing"),
    NavItem(pgettext_lazy("nav", "Zapisy"), "core:page", kwargs={"slug": "zapisy"}),
    NavItem(pgettext_lazy("nav", "Zdawalność"), "core:pass_rates"),
    NavItem(pgettext_lazy("nav", "O nas"), "core:page", kwargs={"slug": "o-nas"}),
    NavItem(pgettext_lazy("nav", "Pliki"), "core:downloads"),
    NavItem(pgettext_lazy("nav", "Kontakt"), "core:contact"),
)
