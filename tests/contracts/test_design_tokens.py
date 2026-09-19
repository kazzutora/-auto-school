"""Design tokens and self hosted fonts, ROSE.md B.2 through B.5.

Core v29 replaced REDESIGN.md part B with ROSE.md part B: the owner's own
crimson and pink instead of a blue and a yellow, a page ground that is never
white, and a dark theme that rearranges the roles rather than inverting them.

The shape of the contract is unchanged. Colours are CSS variables in app.css
that tailwind.config.js reads through rgb(var(--x) / <alpha-value>), which is
what lets `bg-brand-100` mean the blush page in one theme and the near black in
the other without a second set of utilities. So these tests check the variables
and the wiring between the two files rather than the config alone.

Every ratio B.3 prints measures, and scripts/check_contrast.py is where they
are measured on every build. What is here instead is the shape: that the table
is complete, that both doors into the dark theme agree, that the grounds which
do not swap publish a fixed pair, and that nothing off the palette reaches a
template.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

CONFIG = Path(settings.BASE_DIR) / "tailwind.config.js"
APP_CSS = Path(settings.BASE_DIR) / "static" / "src" / "css" / "app.css"
FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"
SPRITE = Path(settings.BASE_DIR) / "static" / "icons" / "sprite.svg"

# ROSE.md B.2, light theme. Channel triplets, the form app.css declares.
LIGHT = {
    "brand-50": (255, 251, 250),
    "brand-100": (251, 237, 239),
    "brand-200": (242, 184, 198),
    "brand-300": (233, 138, 163),
    "brand-500": (212, 56, 94),
    "brand-600": (196, 45, 85),
    "brand-link": (196, 45, 85),
    "brand-700": (161, 64, 82),
    "brand-900": (126, 43, 69),
    "ink": (34, 27, 30),
    "ink-500": (94, 74, 82),
    "ink-300": (156, 138, 145),
    "line": (235, 211, 217),
    "state-ok": (30, 122, 86),
    "state-err": (142, 27, 18),
    # Not in B.2, which gives ok and err only. The site had a third state
    # before this core did, and it is measured the same way: 5.68 on the page.
    "state-warn": (132, 84, 0),
    "fixed-paper": (255, 255, 255),
    "fixed-ink": (34, 27, 30),
    "on-wine": (255, 251, 250),
    "on-wine-muted": (242, 184, 198),
}

# B.2, dark theme. Only the roles that move.
#
# The fills are not here, and that is the whole idea: brand.200, brand.500,
# brand.600 and brand.900 are the school's own colours rather than a role, so
# they are the same in both themes and their labels are fixed to match. What
# moves is the page, the cards, the ink ramp, the hairline, the states, and the
# crimson used as *text* — which has to lighten to read on a near black page,
# and which is a separate token from the crimson used as a fill for exactly
# that reason. One token for both would paint white on #FF8FAB, at 1.90, on
# every hovered button in the dark theme.
DARK = {
    "brand-100": (26, 20, 23),
    "brand-50": (37, 28, 32),
    "brand-link": (255, 143, 171),
    "ink": (246, 233, 236),
    "ink-500": (201, 179, 187),
    "ink-300": (138, 116, 125),
    "line": (58, 42, 48),
    "state-ok": (74, 190, 145),
    "state-warn": (232, 176, 61),
    "state-err": (240, 130, 120),
}

# B.4. The three families and the weights the woff2 subsets are cut to. All
# three carry cyrillic, which is what core v29 finally closed: Public Sans had
# none and went at v25, Archivo had none and went here.
FAMILIES = {
    "Rubik": "display: h1, h2, PRAWO JAZDY, the figures, the wordmark",
    "Nunito": "text: paragraphs, buttons, fields, the menu, h3, prices",
    "Caveat": "handwriting: margin notes, eyebrows, captions, the slogan",
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
    """B.3 forbids white on brand.200 outright: 1.69:1.

    Three grounds never swap with the theme, because they are the brand rather
    than a role: the crimson fill, the pink tile and the wine band. A component
    sitting on one of them that reached for --ink would be right in one theme
    and wrong in the other — on the pink tile it would land on exactly the pair
    B.3 bans. So each publishes a fixed pair and every child reads that.
    """
    for theme in ("light", "dark"):
        tokens = themes[theme]
        assert contrast(tokens["fixed-ink"], tokens["brand-200"]) >= 4.5, theme
        assert contrast(tokens["fixed-paper"], tokens["brand-500"]) >= 4.5, theme
        assert contrast(tokens["fixed-paper"], tokens["brand-600"]) >= 4.5, theme
        assert contrast(tokens["on-wine"], tokens["brand-900"]) >= 4.5, theme

    grounds = (
        ("u-ground-pink", "--fixed-ink"),
        ("u-ground-brand", "--fixed-paper"),
        ("u-ground-wine", "--on-wine"),
    )
    for ground, variable in grounds:
        assert f"rgb(var({variable}))" in block(f".{ground},"), (
            f".{ground} must take its text colour from {variable}, not a token that swaps"
        )


def test_white_on_the_pink_tile_is_never_emitted(themes: dict) -> None:
    """1.69:1, the one pair B.3 refuses outright."""
    for theme in ("light", "dark"):
        assert contrast((255, 255, 255), themes[theme]["brand-200"]) < 2.0
    assert "text-brand-50" not in block(".u-ground-pink,")
    assert "text-fixed-paper" not in block(".u-ground-pink,")


def test_the_fill_crimson_and_the_text_crimson_are_separate(themes: dict) -> None:
    """One token for both is unreadable in the dark theme.

    B.2 lightens the red *text* to #FF8FAB so it reads on the near black page,
    and leaves the fills alone because they are the brand. White on the
    lightened red is 1.90, so a single token would have painted every hovered
    button in the dark theme at 1.90 the moment the text was made legible.
    """
    assert themes["light"]["brand-600"] == themes["light"]["brand-link"]
    assert themes["dark"]["brand-600"] != themes["dark"]["brand-link"]
    assert contrast(themes["dark"]["brand-link"], themes["dark"]["brand-100"]) >= 4.5
    assert contrast(themes["dark"]["fixed-paper"], themes["dark"]["brand-600"]) >= 4.5


def test_the_page_is_never_white(themes: dict) -> None:
    """B.8: the owner does not want a white page and there is no white ground.

    White survives as a card face only, and brand.50 is not it — it is a blush
    off-white with the page's own hue in it.
    """
    for theme in ("light", "dark"):
        assert themes[theme]["brand-100"] != (255, 255, 255)
        assert themes[theme]["brand-50"] != (255, 255, 255)
    body = block("  body {")
    assert "bg-brand-100" in body
    assert "bg-white" not in css() and "background: #fff" not in css().lower()


def test_every_token_is_wired_into_the_config(themes: dict) -> None:
    """A colour the config cannot reach is a colour no template can use.

    The brush pair is deliberately not wired: --brush-a and --brush-b are read
    by the ornament files in static/img/ornament/ and never by a template.
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
        "brand",
        "ink",
        "fixed",
        "wine",
        "state",
        "line",
    }


def test_the_type_scale_is_the_whole_vocabulary() -> None:
    """B.4. A heading picks a step; a size of its own is off contract."""
    text = config()
    steps = re.search(r"fontSize:\s*\{(.*?)\n    \},", text, re.S)
    assert steps
    named = set(re.findall(r'\n      "?([\w-]+)"?:', steps.group(1)))
    assert named == {
        "display",
        "h1",
        "h2",
        "h3",
        # The handwriting, B.4: one note in the margin of a section.
        "script",
        "script-sm",
        "body-lg",
        "body",
        "small",
        "label",
        # Prices, phones and the figures in the stat band, in four steps.
        "data",
        "data-lg",
        "data-xl",
        "data-2xl",
    }


def test_radii_are_only_the_ones_the_contract_allows() -> None:
    """B.5: card 20, tile 18, field 14, polaroid 4, picture 16, button a pill.

    A closed list, so `rounded-2xl` cannot be typed by accident and a seventh
    radius cannot appear without this going red.
    """
    text = config()
    radii = re.search(r"borderRadius:\s*\{(.*?)\n    \},", text, re.S)
    assert radii
    assert dict(re.findall(r"\n      (\w+):\s*\"([^\"]+)\"", radii.group(1))) == {
        "none": "0",
        "polaroid": "4px",
        "DEFAULT": "14px",
        "field": "14px",
        "image": "16px",
        "tile": "18px",
        "card": "20px",
        "hero": "28px",
        "full": "999px",
    }


def test_there_are_exactly_two_shadows() -> None:
    """B.5: two levels, a resting card and a lifted one.

    Both are wine at low alpha rather than grey, so the page reads as one warm
    light source rather than as a warm page with cold cutouts on it.
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
    for stem in ("rubik-italic", "nunito", "caveat"):
        assert f"{stem}-latin-ext.woff2" in text


def test_cyrillic_is_covered_on_every_family() -> None:
    """The site ships in pl, ru and uk, so a latin only subset would show tofu.

    This is a CONTRACT GAP closed twice over. Public Sans shipped no cyrillic
    at all, so before core v25 every paragraph on /ru/ and /uk/ fell back to
    the system sans; Manrope fixed the paragraphs and left the headings, since
    Archivo had none either. Core v29 took all three faces off B.4, and every
    one of them carries both cyrillic subsets.

    scripts/check_fonts.py is the gate that keeps it true glyph by glyph; this
    only checks that the subsets are linked at all.
    """
    text = css()
    for stem in ("rubik-italic", "nunito", "caveat"):
        assert f"{stem}-cyrillic.woff2" in text, stem
        assert f"{stem}-cyrillic-ext.woff2" in text, stem


def test_the_common_subset_wins_an_overlapping_range() -> None:
    """Declaration order is load bearing, and reads wrong at a glance.

    Where two subsets claim the same character the face declared *last* wins.
    cyrillic-ext claims U+0460-052F, which swallows the ukrainian ґ at U+0490,
    and only the cyrillic file carries it. So cyrillic-ext goes first and
    cyrillic after it; sorting these blocks alphabetically drops ґ into the
    system sans on every ukrainian page, and nothing on screen says why.
    """
    text = css()
    for stem in ("rubik-italic", "nunito", "caveat"):
        assert text.index(f"{stem}-cyrillic-ext.woff2") < text.index(f"{stem}-cyrillic.woff2"), stem


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
    "#FFFBFA",  # brand.50, the card the letter sits on
    "#FBEDEF",  # brand.100, the page around it
    "#EBD3D9",  # line
    "#221B1E",  # ink
    "#5E4A52",  # ink.500
    "#D4385E",  # brand.500 — a fill, and the rule beside a quote
    "#C42D55",  # brand.link — the crimson as text, which brand.500 is too pale to be
}


def test_the_emails_use_the_site_palette() -> None:
    """The confirmation should look like the site that sent it.

    Repainted three times now: at core v2 when the palette moved into
    FRONTEND.md, at v25 when the page went warm grey and the purple became a
    blue, and at v29 when the whole language came off the owner's logo. An
    email cannot read a css variable — many
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
    """No hex literals in the templates. These four are the exception.

    A <meta> takes a literal and nothing else — it is read by the browser chrome
    before any stylesheet exists, so there is no variable for it to resolve and
    no way to hand it a token. What can be checked is that the literals are the
    right ones, which is what this does: the phone's chrome and the page's own
    ground have to be the same colour, or the browser paints a black bar over a
    blush page.

    Two of them, not one, for the same reason: a single dark value was correct
    in the dark theme and wrong in the light one, which is the combination B.2
    never has on screen.
    """
    path = Path(settings.BASE_DIR) / "templates" / template
    found = dict(
        (scheme, colour) for colour, scheme in THEME_COLOUR.findall(path.read_text("utf-8"))
    )

    assert set(found) == {"light", "dark"}, f"{template} must declare both schemes"
    assert hex_to_rgb(found["light"]) == themes["light"]["brand-100"]
    assert hex_to_rgb(found["dark"]) == themes["dark"]["brand-100"]


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
        markup = re.sub(
            r"\{#.*?#\}|\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", markup, flags=re.S
        )
        found = re.findall(r"#[0-9a-fA-F]{6}\b", markup)
        if found:
            strays[str(path.relative_to(root))] = found
    assert not strays, f"hex literals outside the theme-color metas: {strays}"
