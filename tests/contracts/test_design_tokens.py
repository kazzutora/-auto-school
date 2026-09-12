"""Design tokens and self hosted fonts, REDESIGN.md B.2 and B.3.

Core v25 replaced FRONTEND.md part A with REDESIGN.md part B: a warm grey page
with white and near-black cards on it, two accents with separated roles, and a
dark theme that is back — as a swap of roles rather than an inversion.

The shape of the contract is unchanged. Colours are CSS variables in app.css
that tailwind.config.js reads through rgb(var(--x) / <alpha-value>), which is
what lets `bg-paper` mean the warm grey in one theme and near black in the
other without a second set of utilities. So these tests check the variables and
the wiring between the two files rather than the config alone.

Two values below differ from the numbers printed in B.2, and both are B.2's own
doing: the same section says the contrast is measured rather than estimated, and
those two did not measure. app.css carries the arithmetic beside them.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

CONFIG = Path(settings.BASE_DIR) / "tailwind.config.js"
APP_CSS = Path(settings.BASE_DIR) / "static" / "src" / "css" / "app.css"
FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"
SPRITE = Path(settings.BASE_DIR) / "static" / "icons" / "sprite.svg"

# REDESIGN.md B.2, light theme. Channel triplets, the form app.css declares.
LIGHT = {
    "paper": (233, 232, 228),
    "paper-50": (242, 241, 238),
    "paper-100": (222, 221, 216),
    "surface": (255, 255, 255),
    "surface-muted": (247, 246, 243),
    "ink": (27, 27, 32),
    "ink-800": (38, 38, 44),
    "ink-700": (58, 58, 68),
    # B.2 prints #6B6B78, which measures 4.28:1 on the warm grey page — under
    # the 4.5 the same section demands of it. The nearest value on the hue that
    # clears it. app.css says the same thing beside the declaration.
    "ink-500": (103, 103, 115),
    "ink-300": (156, 156, 168),
    "primary": (63, 58, 230),
    "primary-600": (51, 46, 219),
    "primary-100": (228, 227, 252),
    "accent": (255, 212, 0),
    "accent-600": (229, 190, 0),
    "accent-100": (255, 246, 204),
    # Darkened from the values B.2 prints. They sit on a chip whose fill is a
    # tenth of the ground's own foreground — #D4D4D0 on the warm grey page —
    # and the printed values measured 3.59, 2.56 and 3.61 there. axe found all
    # three on four pages. These clear 4.5 on that fill.
    "state-ok": (26, 104, 73),
    "state-warn": (121, 84, 0),
    "state-err": (167, 50, 37),
    "line": (215, 214, 209),
    "line-dark": (51, 51, 60),
}

# B.2, dark theme. Only the roles that move; the rest inherit from the light
# table, and the yellow itself does not move — it is the school's mark and it
# reads better on black than on white either way. Its pale tint does, since
# core v27, the way primary-100 always has.
DARK = {
    "paper": (18, 18, 22),
    "paper-50": (23, 23, 28),
    "paper-100": (29, 29, 35),
    "surface": (27, 27, 32),
    "surface-muted": (34, 34, 41),
    "ink": (242, 241, 238),
    "ink-800": (226, 225, 220),
    "ink-700": (196, 195, 190),
    "ink-500": (142, 142, 153),
    "ink-300": (99, 99, 110),
    # B.2 prints #6C68F0. White on it is 4.31:1, under the 4.5 a button label
    # needs, and the label is white by contract. This holds both ends: 4.76 for
    # the label and 3.93 for the button read as an object on the near black
    # page, which is what lightening it was for.
    "primary": (100, 95, 238),
    "primary-600": (86, 81, 232),
    "primary-100": (42, 40, 88),
    # The light cream under the accent callout's 50% wash turned khaki on near
    # black, with light muted text on it at 1.2:1. A dark warm tint instead.
    "accent-100": (44, 40, 20),
    "state-ok": (74, 190, 145),
    "state-warn": (232, 176, 61),
    "state-err": (240, 130, 120),
    "line": (46, 46, 55),
    "line-dark": (60, 60, 71),
}

# B.3. The three families and the exact weights the woff2 subsets are cut to.
# Manrope replaced Public Sans at core v25 and brought cyrillic with it, which
# is most of a CONTRACT GAP closed — see test_cyrillic_is_covered_where_the_family_has_it.
FAMILIES = {
    "Archivo": "display: h1, h2, group names",
    "Manrope": "text: paragraphs, lists, fields, buttons, h3",
    "Roboto Mono": "data: prices, phones, dates, hours, labels",
}

# A.7 calls its list a minimum, so the sprite may carry more. What it may not do
# is carry less, or draw one of them off contract, or grow an icon nobody wrote
# down — an icon that is not accounted for is one nobody finds twice.
EXTRA_ICONS = (
    # The star moved up into ICONS at core v25: B.6 names it in the minimum set
    # outright, where A.7 had left it to this list.
    #
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
    # The one course taught on something that is not a road vehicle.
    "forklift",
)

ICONS = (
    "phone",
    "mail",
    "pin",
    "clock",
    "calendar",
    # B.6 names "стрелки" in the plural. The second one arrived with the
    # carousel, which has a previous button.
    "arrow-right",
    "arrow-left",
    "close",
    "plus",
    "minus",
    "check",
    "menu",
    "globe",
    "download",
    "external",
    # B.6's minimum set, and the one symbol on the video card that is not a
    # word. See FILLED_ICONS for why it is the exception to the stroke rule.
    "play",
    "star",
)

# The one symbol drawn as a fill rather than a stroke.
#
# B.6 sets the whole sprite at a 1.75 stroke on a 24 grid, and every pictogram
# on the site obeys it. A play mark does not: it is a solid triangle everywhere
# anybody has ever seen one, and an outlined one reads as a cursor rather than
# as "press this". Named here so the exception is one line in a tuple rather
# than a hole in the rule.
FILLED_ICONS = ("play",)


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
    """The three tables app.css declares, read straight out of it.

    `light` is the bare :root block. `dark` is the explicit
    :root[data-theme="dark"] one, merged over light the way the cascade merges
    it — the dark block redefines only the tokens whose role moves.
    `media` is the prefers-color-scheme block, kept separate because the whole
    point of test_both_doors_into_the_dark_agree is to compare the two.
    """
    light = declarations(block("  :root {"))
    media = declarations(block("    :root:not([data-theme='light']) {"))
    explicit = declarations(block("  :root[data-theme='dark'] {"))
    return {"light": light, "dark": {**light, **explicit}, "media": media, "explicit": explicit}


def test_light_palette_matches_the_contract(themes: dict) -> None:
    assert {k: v for k, v in themes["light"].items() if k in LIGHT} == LIGHT


def test_dark_palette_matches_the_contract(themes: dict) -> None:
    assert {k: v for k, v in themes["dark"].items() if k in DARK} == DARK


def test_both_doors_into_the_dark_agree(themes: dict) -> None:
    """B.2 opens the dark theme two ways, and they must be the same theme.

    prefers-color-scheme for the reader who has told their system, and
    data-theme="dark" for the one who has told the page. Two blocks that have
    drifted apart give the same person two different sites depending on how
    they got there — and nothing on screen would say which one they were
    looking at.
    """
    assert themes["media"], "the prefers-color-scheme block declares no colours"
    assert themes["media"] == themes["explicit"]


def test_no_colour_is_defined_only_inside_a_media_block(themes: dict) -> None:
    """R9 point 1, and the reason it is the first thing on that list.

    A token that exists only under a media query leaves the explicit theme with
    nothing to fall back to: the reader who picked light on a dark machine gets
    half a palette, and the half they get is the half somebody remembered.
    """
    assert themes["light"], "no colour tokens found at all"
    missing = sorted(set(themes["media"]) - set(themes["light"]))
    assert not missing, (
        f"declared only under prefers-color-scheme: {missing}. "
        "Every colour is defined in the light table first."
    )


def contrast_pairs() -> list[tuple[str, str, str, float, str]]:
    """The pairs scripts/check_contrast.py measures, loaded rather than copied.

    That script is the gate CI runs and `make budget` runs; this is the same
    check inside pytest, where a failure names the pair in the test id. Two
    callers, one table — a second copy of it is a copy that drifts, and the one
    thing neither may do is pass because it was checking last week's colours.
    """
    import importlib.util

    path = Path(settings.BASE_DIR) / "scripts" / "check_contrast.py"
    spec = importlib.util.spec_from_file_location("check_contrast", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [(f"{t}-{f}-{b}", t, f, b, floor, what) for t, f, b, floor, what in module.PAIRS]


@pytest.mark.parametrize(
    ("theme", "fore", "back", "floor", "what"),
    [pair[1:] for pair in contrast_pairs()],
    ids=[pair[0] for pair in contrast_pairs()],
)
def test_contrast_holds_across_the_palette(
    themes: dict, theme: str, fore: str, back: str, floor: float, what: str
) -> None:
    """B.2: body text at 4.5:1, large text and anything non text at 3:1.

    "Контраст проверяется, а не прикидывается" — B.2 says so in as many words,
    and this is one of the two places that does the checking.
    """
    table = themes[theme]
    assert fore in table and back in table, f"{fore} or {back} is not declared in the {theme} theme"
    ratio = contrast(table[fore], table[back])
    assert ratio >= floor, f"{theme}: {fore} on {back} is {ratio:.2f}:1 — {what}"


def test_the_grounds_that_do_not_swap_carry_a_fixed_pair(themes: dict) -> None:
    """B.2 forbids white on yellow outright: 1.43:1.

    Two grounds never swap with the theme. The yellow is the school's mark and
    is the same yellow in both; the blue is the action and B.2 fixes its label
    as white. A component sitting on either that reached for --ink or --surface
    would be right in one theme and wrong in the other, so both grounds publish
    a fixed pair instead and every child reads that.
    """
    for theme in ("light", "dark"):
        tokens = themes[theme]
        assert contrast(tokens["fixed-ink"], tokens["accent"]) >= 4.5, theme
        assert contrast(tokens["fixed-paper"], tokens["primary"]) >= 4.5, theme

    grounds = (("u-ground-accent", "--fixed-ink"), ("u-ground-primary", "--fixed-paper"))
    for ground, variable in grounds:
        assert f"rgb(var({variable}))" in block(f".{ground} {{"), (
            f".{ground} must take its text colour from {variable}, not a token that swaps"
        )


def test_white_on_yellow_is_never_emitted(themes: dict) -> None:
    assert contrast((255, 255, 255), themes["light"]["accent"]) < 2.0  # 1.4:1, why it is banned
    assert "text-paper" not in block(".u-ground-accent {")


def test_every_token_is_wired_into_the_config(themes: dict) -> None:
    """A colour the config cannot reach is a colour no template can use.

    The four that are deliberately not wired are the fixed pair and the dark
    card's own foreground ramp: --fixed-ink, --fixed-paper, --on-dark and
    --on-dark-muted. They are read by the ground utilities in app.css and never
    by a template, because the whole point of them is that no call site has to
    know which ground it landed on.
    """
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
        "surface",
        "ink",
        "primary",
        "accent",
        "state",
        "line",
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
        # B.3 gives the data face a range from 1rem to 2.5rem; these are the
        # four steps of it the site actually sets.
        "data",
        "data-lg",
        "data-xl",
        "data-2xl",
    }


def test_radii_are_only_the_ones_the_contract_allows() -> None:
    """B.4: card 20, hero 28, control 12, picture inside a card 16, chip 999.

    Five and the pill, and nothing between them — so `rounded-2xl` cannot be
    typed by accident and a sixth radius cannot appear without this going red.
    """
    text = config()
    radii = re.search(r"borderRadius:\s*\{(.*?)\n    \},", text, re.S)
    assert radii
    assert dict(re.findall(r"\n      (\w+):\s*\"([^\"]+)\"", radii.group(1))) == {
        "none": "0",
        "image": "16px",
        "DEFAULT": "12px",
        "card": "20px",
        "hero": "28px",
        "full": "999px",
    }


def test_there_are_exactly_two_shadows() -> None:
    """B.4: "больше двух уровней теней не заводить".

    The old contract had borders instead of shadows and exactly one hard
    offset. B.1 lifted that ban and B.4 replaced it with a tighter one: two
    levels, a resting card and a lifted one, so the page reads as one light
    source rather than as several rooms.
    """
    text = config()
    shadows = re.search(r"boxShadow:\s*\{(.*?)\n    \},", text, re.S)
    assert shadows
    named = set(re.findall(r'\n      "?([\w-]+)"?:', shadows.group(1)))
    assert named == {"none", "card", "card-hover"}


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
    for stem in ("archivo", "manrope", "roboto-mono"):
        assert f"{stem}-latin-ext.woff2" in text


def test_cyrillic_is_covered_where_the_family_has_it() -> None:
    """The site ships in pl, ru and uk, so a latin only subset would show tofu.

    Most of a CONTRACT GAP closed at core v25. Public Sans shipped no cyrillic
    at all, so every paragraph on /ru/ and /uk/ fell back to the system sans;
    Manrope carries both subsets, and the body text there is now the same face
    as on the polish pages.

    What is still open is narrower and documented at the top of app.css:
    Archivo has no cyrillic either, so headings on those two languages still
    fall back. Closing it means a fourth family or a different display face —
    and the display face is what the school's own wordmark is set in, so it is
    the owner's call rather than ours.
    """
    text = css()
    for stem in ("manrope", "roboto-mono"):
        assert f"{stem}-cyrillic.woff2" in text, stem
        assert f"{stem}-cyrillic-ext.woff2" in text, stem


@pytest.mark.parametrize("icon", ICONS)
def test_the_sprite_carries_the_minimum_icon_set(icon: str) -> None:
    assert f'id="i-{icon}"' in SPRITE.read_text(encoding="utf-8")


def test_the_sprite_carries_nothing_it_has_not_accounted_for() -> None:
    ids = set(re.findall(r'<symbol id="i-([\w-]+)"', SPRITE.read_text(encoding="utf-8")))
    assert ids == set(ICONS) | set(EXTRA_ICONS)


def test_sprite_symbols_travel_with_their_own_presentation() -> None:
    """B.6, and a use element pointing at another file clones the nodes only.

    A stylesheet inside the sprite does not reliably reach the shadow tree the
    clone lands in, so the stroke — or the fill, for the one filled symbol —
    has to be presentation attributes on the node itself.

    Either way the colour is currentColor and nothing else, which is what lets
    an icon take the colour of the text beside it without a class.
    """
    svg = uncommented(SPRITE.read_text(encoding="utf-8"))
    symbols = re.findall(r"<symbol\b[^>]*>", svg)
    assert len(symbols) == len(ICONS) + len(EXTRA_ICONS)

    for symbol in symbols:
        name = re.search(r'id="i-([\w-]+)"', symbol)
        assert name, symbol
        if name.group(1) in FILLED_ICONS:
            assert 'fill="currentColor"' in symbol, name.group(1)
            assert 'stroke="none"' in symbol, name.group(1)
        else:
            assert 'stroke="currentColor"' in symbol, name.group(1)
            assert 'stroke-width="1.75"' in symbol, name.group(1)
    assert "<style" not in svg


# --------------------------------------------------------------------------
# email, DESIGN-REVIEW point 3

EMAIL_TEMPLATES = Path(settings.BASE_DIR) / "templates" / "leads" / "email"

# A mail client cannot read a css variable and many strip <style> outright, so
# inline hex is the only way to colour an email. What it may not do is invent
# colours: these are the A.2 values, written out.
EMAIL_PALETTE = {
    "#FFFFFF",  # surface
    "#E9E8E4",  # paper
    "#D7D6D1",  # line
    "#1B1B20",  # ink
    "#676773",  # ink-500
    "#3F3AE6",  # primary — the action, where the purple used to be
    "#FFD400",  # accent
}


def test_the_emails_use_the_site_palette() -> None:
    """The confirmation should look like the site that sent it.

    Repainted twice now: once when core v2 moved the palette into FRONTEND.md,
    and again at core v25, when B.2 gave the page a warm grey ground and
    dropped the purple for a blue. An email cannot read a css variable — many
    clients strip <style> outright — so inline hex is the only way to colour
    one, and this is what keeps that hand written copy in step.
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
    they have to carry it on their own — which is also why the warm grey ground
    had to be checked again after v25: #676773 on #E9E8E4 is 4.55, and the
    value B.2 prints would have been 4.28.
    """
    pairs = [
        ("#1B1B20", "#FFFFFF", "body on the card"),
        ("#676773", "#FFFFFF", "quiet text on the card"),
        ("#676773", "#E9E8E4", "quiet text on the ground"),
        ("#3F3AE6", "#FFFFFF", "the name and the links"),
        ("#FFFFFF", "#3F3AE6", "a button label, if one is ever painted here"),
    ]
    for fore, back, what in pairs:
        found = contrast(hex_to_rgb(fore), hex_to_rgb(back))
        assert found >= 4.5, f"{what} is {found:.2f}:1"

    # B.2's banned pair, in case anyone paints a button here.
    assert contrast(hex_to_rgb("#FFFFFF"), hex_to_rgb("#FFD400")) < 2.0


# --------------------------------------------------------------------------
# the one place a hex literal is unavoidable

THEME_COLOUR = re.compile(
    r'<meta name="theme-color" content="(#[0-9A-Fa-f]{6})" '
    r'media="\(prefers-color-scheme: (light|dark)\)">'
)


@pytest.mark.parametrize("template", ["base.html", "500.html"])
def test_the_theme_colour_metas_match_the_tokens(themes: dict, template: str) -> None:
    """R10 point 3 asks for no hex literals in the templates. These are the four.

    A <meta> takes a literal and nothing else — it is read by the browser chrome
    before any stylesheet exists, so there is no variable for it to resolve and
    no way to hand it a token. What can be checked is that the literals are the
    right ones, which is what this does: the phone's chrome and the page's own
    ground have to be the same colour, or the browser paints a black bar over a
    warm grey page.

    Two of them, not one, for the same reason: a single dark value was correct
    in the dark theme and wrong in the light one, which is the combination B.2
    never has on screen.
    """
    path = Path(settings.BASE_DIR) / "templates" / template
    found = dict(
        (scheme, colour) for colour, scheme in THEME_COLOUR.findall(path.read_text("utf-8"))
    )

    assert set(found) == {"light", "dark"}, f"{template} must declare both schemes"
    assert hex_to_rgb(found["light"]) == themes["light"]["paper"]
    assert hex_to_rgb(found["dark"]) == themes["dark"]["paper"]


def test_no_other_hex_literal_reaches_a_template() -> None:
    """The exception above stays exactly that: four metas and nothing else.

    Email templates are excluded and say why in their own tests: a mail client
    cannot read a css variable and many strip <style> outright, so inline hex is
    the only way to colour one.
    """
    root = Path(settings.BASE_DIR) / "templates"
    strays: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.html")):
        if "email" in path.parts:
            continue
        markup = THEME_COLOUR.sub("", uncommented(path.read_text("utf-8")))
        markup = re.sub(r"\{#.*?#\}|\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", markup, flags=re.S)
        found = re.findall(r"#[0-9a-fA-F]{6}\b", markup)
        if found:
            strays[str(path.relative_to(root))] = found
    assert not strays, f"hex literals outside the theme-color metas: {strays}"
