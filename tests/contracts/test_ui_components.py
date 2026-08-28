"""Cotton primitives against the component table in tech.md section 7."""

import re
from pathlib import Path

import pytest
from django.conf import settings

COTTON = Path(settings.BASE_DIR) / "templates" / "cotton"

# tech.md section 7 at core v3: component file -> the props its row declares.
# Slot only components carry an empty set. Cotton maps <c-gallery-grid> to
# gallery_grid and <c-accordion.item> to accordion/item.
TECH_MD_COMPONENTS: dict[str, set[str]] = {
    "button": {"variant", "size", "href", "type", "full"},
    "card": {"href", "padded"},
    "badge": {"tone"},
    "section": {"id", "tone"},
    "heading": {"level", "eyebrow"},
    "table": {"headers"},
    "accordion": set(),
    "accordion/item": {"title", "open"},
    "modal": {"id", "title"},
    "field": {"field", "label", "help", "required"},
    "input": {"name", "type", "value", "error", "placeholder"},
    "select": {"name", "options", "value", "error"},
    "textarea": {"name", "rows", "value", "error"},
    "checkbox": {"name", "checked", "error"},
    "alert": {"tone", "title"},
    "breadcrumbs": {"items"},
    "picture": {"image", "alt", "sizes", "loading", "ratio"},
    "gallery_grid": {"images", "columns"},
    "lightbox": {"images"},
    "cta_bar": {"title", "phone", "href"},
    "price_tile": {"title", "price", "note", "href"},
    "course_card": {"course"},
    "intake_row": {"intake"},
    "hours_table": {"department"},
    "map": {"lat", "lng", "zoom", "label", "height"},
    "icon": {"name", "size", "label"},
    "lang_switcher": set(),
    "cookie_banner": set(),
    "testimonials": {"items"},
    "nav": set(),
}


def source(name: str) -> str:
    return (COTTON / f"{name}.html").read_text(encoding="utf-8")


def declared_vars(name: str) -> set[str]:
    match = re.search(r"<c-vars([^/>]*)/?>", source(name))
    if not match:
        return set()
    return set(re.findall(r'([\w-]+)=\s*"', match.group(1)))


@pytest.mark.parametrize("name", TECH_MD_COMPONENTS)
def test_component_exists(name: str) -> None:
    """DEV.md S0.7: build all of them, not half."""
    assert (COTTON / f"{name}.html").is_file(), f"<c-{name}> from tech.md section 7 is missing"


@pytest.mark.parametrize(("name", "props"), TECH_MD_COMPONENTS.items())
def test_component_declares_its_props(name: str, props: set[str]) -> None:
    """Undeclared props leak into attrs and get rendered twice."""
    missing = props - declared_vars(name)
    assert not missing, f"<c-{name}> does not declare {missing}"


def test_no_component_invents_props_outside_tech_md() -> None:
    extra = {
        name: declared_vars(name) - props
        for name, props in TECH_MD_COMPONENTS.items()
        if declared_vars(name) - props
    }
    assert not extra, f"props not in tech.md section 7: {extra}"


def test_picture_forces_a_lazy_default_and_an_alt() -> None:
    body = source("picture")
    assert 'loading="lazy"' in body  # the c-vars default
    assert 'alt="{{ alt }}"' in body


def test_mobile_menu_opens_on_click_not_hover() -> None:
    """tech.md section 7: the mobile menu must never depend on hover."""
    body = source("nav")
    assert "x-on:click" in body
    assert "hover:" not in re.sub(r'class="[^"]*"', "", body)
    assert "x-bind:aria-expanded" in body


def test_map_carries_no_inline_script() -> None:
    """Production CSP is script-src 'self', so init data rides on data-*."""
    # The component documents the tags a page must add, inside a comment, and
    # one of them is the leaflet <script>. Both comment forms come out.
    body = re.sub(r"\{#.*?#\}|\{% comment %\}.*?\{% endcomment %\}", "", source("map"), flags=re.S)
    assert "<script" not in body
    assert "data-lat" in body and "data-lng" in body


def test_csp_permits_exactly_what_the_primitives_need() -> None:
    """Two documented exceptions, tech.md sections 2, 7 and 19."""
    policy = settings.CONTENT_SECURITY_POLICY

    # Alpine 3 evaluates x-* expressions with new Function(), and the modal and
    # lightbox rows in section 7 specify Alpine.
    assert policy["script-src"] == ["'self'", "'unsafe-eval'"]

    # Leaflet pulls OpenStreetMap tiles. No other host is allowed anywhere.
    assert policy["img-src"] == ["'self'", "data:", "https://tile.openstreetmap.org"]

    allowed_hosts = {"https://tile.openstreetmap.org"}
    for directive, values in policy.items():
        for value in values:
            if value.startswith(("http://", "https://", "//")):
                assert value in allowed_hosts, f"{directive} allows {value}"
            assert "*" not in value, f"{directive} allows a wildcard: {value}"


def test_csp_middleware_writes_the_header() -> None:
    from django.http import HttpResponse

    from config.middleware import ContentSecurityPolicyMiddleware

    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    response = middleware(None)  # type: ignore[arg-type]

    header = response["Content-Security-Policy"]
    assert "script-src 'self' 'unsafe-eval'" in header
    assert "img-src 'self' data: https://tile.openstreetmap.org" in header
