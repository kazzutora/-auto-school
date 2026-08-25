"""Site navigation as data, tech.md section 7.

The menu is a list of NavItem, never markup. templates/layout/nav.html renders
this list and nothing else.
"""

from dataclasses import dataclass, field

from django.urls import reverse


@dataclass(frozen=True)
class NavItem:
    title: str
    route: str
    kwargs: dict[str, str] = field(default_factory=dict)
    children: tuple["NavItem", ...] = ()

    def url(self) -> str:
        """Resolved lazily: routes appear as their slices ship."""
        return reverse(self.route, kwargs=self.kwargs or None)


# Kontakt is a first level item. Hiding it in a submenu is forbidden: that was
# the main defect of the old site, tech.md section 7.
NAV: tuple[NavItem, ...] = (
    NavItem("Kursy", "courses:list"),
    NavItem("Kierowca zawodowy", "courses:pro_hub"),
    NavItem("Cennik", "courses:pricing"),
    NavItem("Terminy", "courses:intakes"),
    NavItem("O nas", "core:page", kwargs={"slug": "o-nas"}),
    NavItem("Galeria", "gallery:index"),
    NavItem("Kontakt", "core:contact"),
)
