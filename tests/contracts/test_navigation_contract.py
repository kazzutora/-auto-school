"""Navigation against tech.md section 7."""

from apps.core.navigation import NAV, NavItem

# tech.md section 7, in order.
TECH_MD_NAV = [
    ("Kursy", "courses:list"),
    ("Kierowca zawodowy", "courses:pro_hub"),
    ("Cennik", "courses:pricing"),
    ("Terminy", "courses:intakes"),
    ("O nas", "core:page"),
    ("Galeria", "gallery:index"),
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


def test_o_nas_carries_its_slug() -> None:
    o_nas = next(item for item in NAV if item.route == "core:page")
    assert o_nas.kwargs == {"slug": "o-nas"}


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
