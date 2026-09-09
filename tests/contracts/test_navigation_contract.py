"""Navigation against tech.md section 7."""

from apps.core.navigation import NAV, NavItem

# tech.md section 7, in order. Seven items, one level, no submenus: this school
# sells one category, so there is no course tree to fold away.
TECH_MD_NAV = [
    ("Kurs kat. B", "courses:detail"),
    ("Cennik", "courses:pricing"),
    ("Zapisy", "core:page"),
    ("Zdawalność", "core:pass_rates"),
    ("O nas", "core:page"),
    ("Do pobrania", "core:downloads"),
    ("Kontakt", "core:contact"),
]


def test_nav_matches_tech_md() -> None:
    assert [(item.title, item.route) for item in NAV] == TECH_MD_NAV


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

    assert "core:pass_rates" in routes
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
