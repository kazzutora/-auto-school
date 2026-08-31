"""Design tokens and self hosted fonts, FRONTEND.md A.2 and A.3.

Core v2 moved the palette out of the tech.md section 7 sketch and into
FRONTEND.md part A, which says outright that A.2 wins where the two disagree.
The shape of the contract changed with it: colours are no longer hex literals
in tailwind.config.js, they are CSS variables in app.css that the config reads
through rgb(var(--x) / <alpha-value>). That is what lets the dark theme be a
swap of roles rather than a second set of utilities, so these tests check the
variables and the wiring between the two files rather than the config alone.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

CONFIG = Path(settings.BASE_DIR) / "tailwind.config.js"
APP_CSS = Path(settings.BASE_DIR) / "static" / "src" / "css" / "app.css"
FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"
SPRITE = Path(settings.BASE_DIR) / "static" / "icons" / "sprite.svg"

# FRONTEND.md A.2, light theme. Channel triplets, the form app.css declares.
LIGHT = {
    "paper": (255, 255, 255),
    "paper-50": (250, 250, 250),
    "paper-100": (242, 242, 241),
    "paper-200": (230, 230, 228),
    "ink": (14, 14, 16),
    "ink-700": (51, 51, 58),
    "ink-500": (92, 92, 102),
    "ink-300": (138, 138, 148),
    "line": (26, 26, 30),
    "line-soft": (217, 217, 214),
    "accent": (255, 212, 0),
    "accent-600": (229, 190, 0),
    "accent-100": (255, 246, 204),
    "deep": (42, 32, 96),
    "deep-700": (59, 45, 113),
    "state-ok": (15, 107, 69),
    "state-warn": (138, 90, 0),
    "state-err": (166, 32, 21),
}

# A.2, dark theme. Only the roles that move; the rest inherit from light, and
# the yellow does not move at all because it reads better on black than white.

# A.3. The three families and the exact weights the woff2 subsets are cut to.
FAMILIES = {
    "Archivo": "display: h1, h2, big numbers, category codes",
    "Public Sans": "text: paragraphs, lists, fields, buttons",
    "Roboto Mono": "data: prices, phones, dates, hours, labels",
}

# A.7 calls its list a minimum, so the sprite may carry more. What it may not do
# is carry less, or draw one of them off contract, or grow an icon nobody wrote
# down — an icon that is not accounted for is one nobody finds twice.
EXTRA_ICONS = (
    # A.9 point 7 puts a star rating on every testimonial, and the alternative
    # is a dingbat character, which would be the one place in the interface
    # where an icon is text.
    "star",
    # One vehicle per licence category, mapped in core_ui.CATEGORY_VEHICLES. A
    # category tile that only says "A2" asks the reader to know the code
    # already; the silhouette says motorcycle before the letter is read. They
    # are drawn on the same 24 grid and the same 1.75 stroke as the rest, so
    # they sit beside a clock or a pin without looking imported.
    "moped",
    "motorcycle",
    "car",
    "truck",
    "bus",
    # A combination category is one symbol, not two side by side: a car and a
    # separate trailer needed twice the width of every other marker and left
    # the tile at five columns.
    "car-trailer",
    "truck-trailer",
)

ICONS = (
    "phone",
    "mail",
    "pin",
    "clock",
    "calendar",
    "arrow-right",
    "close",
    "plus",
    "minus",
    "check",
    "menu",
    "globe",
    "download",
    "external",
)


def css() -> str:
    return APP_CSS.read_text(encoding="utf-8")


def config() -> str:
    return CONFIG.read_text(encoding="utf-8")


def uncommented(text: str, *, block_comments: bool = True, line_comments: bool = False) -> str:
    """The same text with its comments cut out.

    Several of the checks below look for a string that must not appear in the
    code, and every one of those strings is also worth naming in a comment that
    explains why. Scanning the raw file makes documenting the rule break it.
    """
    if block_comments:
        text = re.sub(r"/\*.*?\*/|<!--.*?-->", "", text, flags=re.S)
    if line_comments:
        text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return text


def block(selector: str) -> str:
    """The body of the first rule whose selector line matches, braces balanced."""
    text = css()
    start = text.index(selector)
    opening = text.index("{", start)
    depth = 0
    for i in range(opening, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[opening : i + 1]
    raise AssertionError(f"unbalanced braces after {selector!r}")


def declarations(body: str) -> dict[str, tuple[int, ...]]:
    return {
        name: tuple(int(part) for part in value.split())
        for name, value in re.findall(r"--([a-z0-9-]+):\s*(\d+ \d+ \d+)\s*;", body)
    }


def hex_to_rgb(value: str) -> tuple[int, ...]:
    """#RRGGBB to the channel triplet the contrast maths wants."""
    text = value.lstrip("#")
    return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))


def luminance(rgb: tuple[int, ...]) -> float:
    def channel(value: int) -> float:
        srgb = value / 255
        return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(c) for c in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(fore: tuple[int, ...], back: tuple[int, ...]) -> float:
    high, low = sorted((luminance(fore), luminance(back)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.fixture(scope="module")
def themes() -> dict[str, dict[str, tuple[int, ...]]]:
    """One theme now. The key stays so the pairs below read as they did."""
    return {"light": declarations(block("  :root {"))}


def test_light_palette_matches_the_contract(themes: dict) -> None:
    assert {k: v for k, v in themes["light"].items() if k in LIGHT} == LIGHT


def test_there_is_one_theme_and_it_is_the_light_one() -> None:
    """The owner's call, and the reason for it.

    The design swapped roles on prefers-color-scheme, which put a near black
    page under a near black header on every page but the home one: the two
    grounds were the same colour and the hairline between them measured 1.4:1,
    so the header dissolved into the page. A dark band over a light page
    replaced it. This is what stops a second palette creeping back in.
    """
    # Uncommented, for the reason the helper exists: the comment above this
    # test names both strings, and so does the stylesheet's own.
    text = uncommented(css())
    assert "prefers-color-scheme" not in text
    assert "data-theme" not in text


def test_no_colour_is_defined_inside_a_media_block() -> None:
    """F0 acceptance criterion 4, and now the stronger form of it.

    A token that exists only under a media query is a token something else has
    no value for. With one theme there is no reason for any of them to sit in
    one.
    """
    tokens = re.findall(r"--[a-z0-9-]+:\s*\d+ \d+ \d+", css())
    in_root = re.findall(r"--[a-z0-9-]+:\s*\d+ \d+ \d+", block("  :root {"))
    assert tokens, "no colour tokens found at all"
    assert len(tokens) == len(in_root), (
        "a colour is declared outside :root — with one theme there is nowhere "
        "else for one to belong"
    )


@pytest.mark.parametrize(
    ("fore", "back", "floor"),
    [
        ("ink", "paper", 4.5),
        ("ink-700", "paper", 4.5),
        ("ink-500", "paper", 4.5),
        ("ink", "paper-50", 4.5),
        ("ink", "paper-100", 4.5),
        ("ink", "paper-200", 4.5),
        ("paper", "ink", 4.5),
        ("state-ok", "paper", 4.5),
        ("state-warn", "paper", 4.5),
        ("state-err", "paper", 4.5),
        ("line", "paper", 3.0),
    ],
)
def test_contrast_holds_across_the_palette(
    themes: dict, fore: str, back: str, floor: float
) -> None:
    """A.2: body text at 4.5:1, large text and anything non text at 3:1."""
    ratio = contrast(themes["light"][fore], themes["light"][back])
    assert ratio >= floor, f"{fore} on {back} is {ratio:.2f}:1"


def test_the_grounds_that_do_not_swap_carry_a_fixed_pair(themes: dict) -> None:
    """A.2 forbids white on yellow outright: 1.4:1.

    The pair exists because these two grounds never swap. It outlived the dark
    theme: the header is an ink ground now, and the machinery that lets a
    ground carry its own foreground is what makes that work without a single
    component naming a colour.
    """
    tokens = themes["light"]
    assert contrast(tokens["fixed-ink"], tokens["accent"]) >= 4.5
    assert contrast(tokens["fixed-paper"], tokens["deep"]) >= 4.5

    grounds = (("u-ground-accent", "--fixed-ink"), ("u-ground-deep", "--fixed-paper"))
    for ground, variable in grounds:
        assert f"rgb(var({variable}))" in block(f".{ground} {{"), (
            f".{ground} must take its text colour from {variable}, not a token that swaps"
        )


def test_white_on_yellow_is_never_emitted(themes: dict) -> None:
    assert contrast((255, 255, 255), themes["light"]["accent"]) < 2.0  # 1.4:1, why it is banned
    assert "text-paper" not in block(".u-ground-accent {")


def test_every_token_is_wired_into_the_config(themes: dict) -> None:
    """A colour the config cannot reach is a colour no template can use."""
    text = config()
    for name in LIGHT:
        assert f'token("{name}")' in text, f"--{name} is declared but not exposed to tailwind"


def test_the_config_holds_no_hex_literals() -> None:
    """Every colour goes through a variable, so a hex here is a colour off contract."""
    code = uncommented(config(), line_comments=True)
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", code)


def test_the_palette_replaces_tailwinds_rather_than_extending_it() -> None:
    """Keeps text-gray-400 and the rest of the default palette untypeable."""
    text = config()
    colours = re.search(r"\n    colors:\s*\{(.*?)\n    \},", text, re.S)
    assert colours, "colors group missing from tailwind.config.js"
    groups = set(re.findall(r"\n      (\w+):", colours.group(1)))
    assert groups == {
        "transparent",
        "current",
        "inherit",
        "paper",
        "ink",
        "line",
        "accent",
        "deep",
        "state",
    }


def test_the_type_scale_is_the_whole_vocabulary() -> None:
    """A.3. A heading picks a step; a size of its own is off contract."""
    text = config()
    steps = re.search(r"fontSize:\s*\{(.*?)\n    \},", text, re.S)
    assert steps
    named = set(re.findall(r'\n      "?([\w-]+)"?:', steps.group(1)))
    assert named == {
        "display",
        "h1",
        "h2",
        "h3",
        "body-lg",
        "body",
        "small",
        "label",
        "data",
        "data-lg",
        "data-xl",
    }


def test_radii_are_only_the_two_the_contract_allows() -> None:
    """A.1: 0 for sections and slabs, 2px for buttons, fields and cards."""
    text = config()
    radii = re.search(r"borderRadius:\s*\{(.*?)\n    \},", text, re.S)
    assert radii
    assert dict(re.findall(r"\n      (\w+):\s*\"([^\"]+)\"", radii.group(1))) == {
        "none": "0",
        "DEFAULT": "2px",
        "full": "9999px",
    }


@pytest.mark.parametrize("family", FAMILIES)
def test_the_three_families_are_declared(family: str) -> None:
    assert f"font-family: '{family}'" in css()


def test_no_other_family_crept_in() -> None:
    declared = set(re.findall(r"font-family: '([^']+)'", css()))
    assert declared == set(FAMILIES)


def test_fonts_are_self_hosted() -> None:
    """tech.md section 2 bans third party font hosts on public pages."""
    text = css()
    urls = re.findall(r"url\(([^)]+)\)", text)
    assert urls, "no font urls at all"
    for url in urls:
        assert url.startswith("../fonts/"), f"{url} is not served from our own static files"
    assert "https://" not in text
    assert "fonts.googleapis.com" not in text
    assert "fonts.gstatic.com" not in text


def test_every_declared_font_file_exists() -> None:
    for url in re.findall(r"url\(\.\./fonts/([^)]+)\)", css()):
        assert (FONT_DIR / url).is_file(), f"{url} declared but not shipped"


def test_no_font_file_is_shipped_unused() -> None:
    declared = set(re.findall(r"url\(\.\./fonts/([^)]+)\)", css()))
    assert {path.name for path in FONT_DIR.glob("*.woff2")} == declared


def test_faces_use_display_swap() -> None:
    text = css()
    faces = text.count("@font-face")
    assert faces >= len(FAMILIES)
    assert text.count("font-display: swap") == faces


def test_polish_diacritics_are_covered_on_every_family() -> None:
    """latin-ext is what carries ł ą ę ś ć ż ź ń, and the whole site is polish."""
    text = css()
    for stem in ("archivo", "public-sans", "roboto-mono"):
        assert f"{stem}-latin-ext.woff2" in text


def test_cyrillic_is_covered_where_the_family_has_it() -> None:
    """The site ships in pl, ru and uk, so a latin only subset would show tofu.

    CONTRACT GAP, documented at the top of app.css: Archivo and Public Sans
    ship no cyrillic glyphs at all, so on /ru/ and /uk/ headings and paragraphs
    fall back to the system sans. Roboto Mono carries its own, which is what
    keeps the data on contract. This test pins the half that is reachable and
    will start failing the moment a cyrillic capable family replaces one of the
    other two, which is the signal that the gap has been closed.
    """
    text = css()
    assert "roboto-mono-cyrillic.woff2" in text
    assert "roboto-mono-cyrillic-ext.woff2" in text


@pytest.mark.parametrize("icon", ICONS)
def test_the_sprite_carries_the_minimum_icon_set(icon: str) -> None:
    assert f'id="i-{icon}"' in SPRITE.read_text(encoding="utf-8")


def test_the_sprite_carries_nothing_it_has_not_accounted_for() -> None:
    ids = set(re.findall(r'<symbol id="i-([\w-]+)"', SPRITE.read_text(encoding="utf-8")))
    assert ids == set(ICONS) | set(EXTRA_ICONS)


def test_sprite_symbols_travel_with_their_own_stroke() -> None:
    """A.7, and a use element pointing at another file clones the nodes only.

    A stylesheet inside the sprite does not reliably reach the shadow tree the
    clone lands in, so the stroke has to be presentation attributes.
    """
    svg = uncommented(SPRITE.read_text(encoding="utf-8"))
    symbols = re.findall(r"<symbol\b[^>]*>", svg)
    assert len(symbols) == len(ICONS) + len(EXTRA_ICONS)
    for symbol in symbols:
        assert 'stroke="currentColor"' in symbol
        assert 'stroke-width="1.75"' in symbol
    assert "<style" not in svg


# --------------------------------------------------------------------------
# email, DESIGN-REVIEW point 3

EMAIL_TEMPLATES = Path(settings.BASE_DIR) / "templates" / "leads" / "email"

# A mail client cannot read a css variable and many strip <style> outright, so
# inline hex is the only way to colour an email. What it may not do is invent
# colours: these are the A.2 values, written out.
EMAIL_PALETTE = {
    "#FFFFFF",  # paper
    "#FAFAFA",  # paper-50
    "#D9D9D6",  # line.soft
    "#0E0E10",  # ink
    "#5C5C66",  # ink-500
    "#2A2060",  # deep
    "#FFD400",  # accent
}


def test_the_emails_use_the_site_palette() -> None:
    """The confirmation should look like the site that sent it.

    They were still painted in the tech.md section 7 sketch that core v2
    replaced, so the mail and the page disagreed on every colour.
    """
    strays: dict[str, set[str]] = {}
    for path in sorted(EMAIL_TEMPLATES.glob("*.html")):
        found = re.findall(r"#[0-9A-Fa-f]{6}", path.read_text("utf-8"))
        used = {value.upper() for value in found}
        if used - EMAIL_PALETTE:
            strays[path.name] = used - EMAIL_PALETTE
    assert not strays, f"colours that are not in A.2: {strays}"


def test_the_emails_keep_their_text_readable(themes: dict) -> None:
    """4.5:1 on every pair the mail actually puts together.

    An email has no dark theme to swap into, so these are the light values and
    they have to carry it on their own.
    """
    pairs = [
        ("#0E0E10", "#FFFFFF", "body on the card"),
        ("#5C5C66", "#FFFFFF", "quiet text on the card"),
        ("#5C5C66", "#FAFAFA", "quiet text on the ground"),
        ("#2A2060", "#FFFFFF", "the name and the links"),
    ]
    for fore, back, what in pairs:
        found = contrast(hex_to_rgb(fore), hex_to_rgb(back))
        assert found >= 4.5, f"{what} is {found:.2f}:1"

    # A.2's banned pair, in case anyone paints a button here.
    assert contrast(hex_to_rgb("#FFFFFF"), hex_to_rgb("#FFD400")) < 2.0
