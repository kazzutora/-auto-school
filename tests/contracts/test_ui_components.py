"""Cotton primitives against the component table in tech.md section 7."""

import re
from pathlib import Path

import pytest
from django.conf import settings

COTTON = Path(settings.BASE_DIR) / "templates" / "cotton"

# tech.md section 7 at core v29: component file -> the props its row declares.
# Slot only components carry an empty set. Cotton maps <c-gallery-grid> to
# gallery_grid and <c-accordion.item> to accordion/item.
TECH_MD_COMPONENTS: dict[str, set[str]] = {
    "button": {"variant", "size", "href", "type", "full"},
    # tone=light|dark since v25: the same card on the ink ground, REDESIGN.md
    # B.1. It is a prop rather than a second component because everything else
    # about it — the radius, the shadow, the hover lift — is identical.
    "card": {"href", "padded", "level", "tone"},
    "badge": {"tone"},
    # reveal since v25. A section animates its own arrival by default, C.3
    # row 1; the prop is for the handful that must not, such as the one above
    # the fold on a page whose hero is already staggering in.
    #
    # edge and corner since v29: they place a brush stroke, ROSE.md B.7, and
    # they are props rather than classes on the call site because B.7 allows a
    # stroke only at the edge of a section and behind a picture. A prop can
    # only put it where the rule allows.
    "section": {"id", "tone", "size", "reveal", "edge", "corner"},
    "quote": {"text", "author", "role"},
    "steps": {"steps"},
    "fact_card": {"label", "value", "note", "action", "href"},
    "price_row": {"title", "price", "note", "badge", "href"},
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
    "course_card": {"course", "level"},
    "intake_row": {"intake"},
    "hours_table": {"department"},
    "map": {"lat", "lng", "zoom", "label", "height"},
    "icon": {"name", "size", "label"},
    "lang_switcher": set(),
    "cookie_banner": set(),
    "testimonials": {"items"},
    "nav": set(),
    # The four REDESIGN.md B.5 added at core v25, plus the tab strip B.5 lists
    # among the redrawn ones and the site had no component for.
    "group_card": {"intake", "featured", "disabled", "href"},
    "carousel": {"id", "per_view", "label"},
    "video_card": {"poster", "photo", "url", "ratio", "alt", "title"},
    "bento": {"items"},
    "bento/item": {
        "title", "text", "image", "photo", "alt", "large", "cover", "width", "height",
    },
    "photo": {"stem", "crop", "crop_mobile", "alt", "sizes", "priority", "decorative"},
    "tabs": {"id", "label", "items"},
    # The six ROSE.md B.5 and C.1 added at core v29.
    "ornament": {"kind", "variant"},
    "course_tile": {"course", "active"},
    "feature": {"icon", "title"},
    "stat": {"value", "label", "note"},
    "polaroid": {"src", "alt", "caption", "tilt", "width", "height"},
    "review_card": {"item"},
    # plain since v29: it turns the header's brush stroke off, and two pages
    # pass it — the privacy policy and the RODO notice, where B.7 point 4 says
    # there is no ornament at all.
    "page_header": {"eyebrow", "title", "lead", "level", "plain"},
}


def source(name: str) -> str:
    return (COTTON / f"{name}.html").read_text(encoding="utf-8")


# Not a prop: the html attribute every element has. A component declares it so
# cotton hands it over as a variable instead of leaving it in attrs, where it
# would be emitted as a second class attribute on a tag that already has one and
# be dropped on the floor by the parser.
ATTRIBUTE_HOOKS = {"class"}


def declared_vars(name: str) -> set[str]:
    match = re.search(r"<c-vars([^/>]*)/?>", source(name))
    if not match:
        return set()
    return set(re.findall(r'([\w-]+)=\s*"', match.group(1))) - ATTRIBUTE_HOOKS


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


def test_a_component_never_emits_two_class_attributes() -> None:
    """A class handed to a component has to reach the element, not vanish.

    Cotton puts undeclared attributes into attrs. If the component's own tag
    already carries class="...", attrs adds a second one and the parser keeps
    the first, so the caller's class is silently lost. A component whose tag has
    a class must therefore declare class and merge it in by hand.
    """
    offenders = []
    for name in TECH_MD_COMPONENTS:
        body = re.sub(
            r"\{#.*?#\}|\{% comment %\}.*?\{% endcomment %\}", "", source(name), flags=re.S
        )
        for hit in re.finditer(r"\{\{ attrs \}\}", body):
            start = body.rfind("<", 0, hit.start())
            if start == -1:
                continue
            tag = body[start : hit.start()]
            if 'class="' in tag and "{{ class }}" not in tag:
                offenders.append(name)
    assert not offenders, f"these drop an incoming class: {sorted(set(offenders))}"


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
    # The component explains itself in a comment, which talks about the frame it
    # does not contain. Both comment forms come out.
    body = re.sub(r"\{#.*?#\}|\{% comment %\}.*?\{% endcomment %\}", "", source("map"), flags=re.S)
    assert "<script" not in body
    assert "data-lat" in body and "data-lng" in body

    # The google map is built by static/js/app.js on the click, core v26. The
    # markup itself frames nothing and names no google url.
    assert "<iframe" not in body
    assert "google.com" not in body
    assert "data-map-load" in body


def test_csp_permits_exactly_what_the_primitives_need() -> None:
    """Two documented exceptions, tech.md sections 2, 7 and 19."""
    policy = settings.CONTENT_SECURITY_POLICY

    # Alpine 3 evaluates x-* expressions with new Function(), and the modal and
    # lightbox rows in section 7 specify Alpine.
    assert policy["script-src"] == ["'self'", "'unsafe-eval'"]

    # The google map, framed only after the visitor presses its button, core
    # v26. Images are ours alone now that no tile server draws the map.
    assert policy["frame-src"] == ["https://www.google.com"]
    assert policy["img-src"] == ["'self'", "data:"]

    allowed_hosts = {"https://www.google.com"}
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
    directives = {
        name: value
        for name, _, value in (part.strip().partition(" ") for part in header.split(";"))
        if name
    }
    assert directives["script-src"] == "'self' 'unsafe-eval'"
    assert directives["img-src"] == "'self' data:"
    assert directives["frame-src"] == "https://www.google.com"
