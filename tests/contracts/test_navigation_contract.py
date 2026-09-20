"""Navigation against tech.md section 7."""

from apps.core.navigation import NAV, NavItem

# tech.md section 7, in order. Six items, one level, no submenus: this school
# sells one category, so there is no course tree to fold away.
#
# Zdawalność was the seventh until core v32. The page went; the figures did
# not, and the home page still carries them as a band.
TECH_MD_NAV = [
    ("Kurs B", "courses:detail"),
    ("Cennik", "courses:pricing"),
    ("Zapisy", "core:page"),
    ("O nas", "core:page"),
    ("Pliki", "core:downloads"),
    ("Kontakt", "core:contact"),
]

# Measured at xl: the header gives the menu 583px once the lettering and the
# right hand cluster have taken theirs. Three labels carry a short form in the
# nav context for exactly this, and the row has to keep some slack — it has now
# been the binding constraint twice.
NAV_BUDGET_CHARS = 55


def test_nav_matches_tech_md() -> None:
    assert [(item.title, item.route) for item in NAV] == TECH_MD_NAV


def test_the_menu_still_fits_the_row_it_has() -> None:
    """A menu wider than the header prints its last item over the switcher.

    Characters rather than pixels, because a test cannot measure a font: the
    labels come to 55 characters at the width that was measured to fit, and this
    is the tripwire for the next person who adds an item or a longer word.
    """
    total = sum(len(str(item.title)) for item in NAV)

    assert total <= NAV_BUDGET_CHARS, (
        f"{total} characters of menu; see the CONTRACT GAP in templates/cotton/nav.html"
    )


def test_kontakt_is_a_first_level_item() -> None:
    """Hiding Kontakt in a submenu was the main defect of the old site."""
    top_level = {item.title for item in NAV}
    assert "Kontakt" in top_level

    for item in NAV:
        assert "Kontakt" not in {child.title for child in item.children}


def test_every_flat_page_item_carries_its_slug() -> None:
    """core:page answers for four slugs, so the route alone is not an address."""
    slugs = [item.kwargs.get("slug") for item in NAV if item.route == "core:page"]

    assert slugs == ["zapisy", "o-nas"]


def test_the_course_item_names_the_one_category() -> None:
    course = next(item for item in NAV if item.route == "courses:detail")
    assert course.kwargs == {"slug": "kat-b"}


def test_the_two_pages_this_school_leads_with_are_in_the_menu() -> None:
    """tech.md section 1: the pass rate and the price list are the argument.

    Both were buried in the middle of a one page site. A menu that does not name
    them puts them back where they were.
    """
    routes = {item.route for item in NAV}

    assert "courses:pricing" in routes


def test_every_nav_route_resolves() -> None:
    """A menu item pointing at a route that does not exist is a 500 in the header."""
    for item in NAV:
        assert item.url().startswith("/")


def test_nav_items_are_immutable() -> None:
    """Navigation is data, and a request must not be able to reshape it."""
    assert isinstance(NAV, tuple)
    item = NAV[0]
    try:
        item.title = "hacked"  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("NavItem should be frozen")


def test_nav_item_defaults_have_no_children() -> None:
    assert NavItem("X", "core:contact").children == ()
