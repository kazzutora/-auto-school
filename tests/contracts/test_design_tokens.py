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

# Core v44, light theme. Channel triplets, the form app.css declares.
#
# Two layers, and the split is the contract. BRAND names each colour once, in
# the owner's own words; LIGHT is the role vocabulary the templates were built
# on and every one of its entries is an alias pointing into BRAND or a literal
# of its own. That is what let the palette change twice without touching a
# single class in a single template.
BRAND = {
    # Red, white, graphite, and no fourth. The mark carries a blue as well,
    # and v44 takes it off the page rather than into the palette: the header
    # and footer show the school's own white-on-red lockup instead.
    #
    # The red is four percent darker than the mark's #EA232C, because white
    # on that measures 4.40 and the primary button carries a white label.
    "brand-red": (225, 20, 29),
    "brand-red-dark": (192, 16, 23),
    "brand-red-light": (253, 236, 237),
    # Graphite. Every heading and paragraph, the outline button, the dark
    # band and the footer. Neutral, with no cast in it.
    "brand-ink": (28, 28, 30),
    "ink-soft": (44, 44, 48),
    # Its opposite, on the same terms: white is a fill where the pair must not
    # swap with the theme, and --surface is the role that does.
    "brand-paper": (255, 255, 255),
    "muted": (107, 107, 112),
    # The quiet grey on graphite. --muted measures 3.21 there and fails.
    "on-ink-muted": (161, 161, 170),
    "surface": (255, 255, 255),
    "surface-alt": (244, 244, 245),
    "border": (228, 228, 231),
}

LIGHT = {
    "brand-50": (255, 255, 255),
    "brand-100": (244, 244, 245),
    "brand-200": (253, 236, 237),
    "brand-300": (247, 195, 198),
    "brand-500": (225, 20, 29),
    "brand-600": (192, 16, 23),
    "brand-link": (192, 16, 23),
    # The accent that is not the action: the outline button's frame, the
    # icons beside the advantages. Graphite at v44 — it was the blue.
    "brand-700": (28, 28, 30),
    "brand-900": (28, 28, 30),
    "ink": (28, 28, 30),
    "ink-500": (107, 107, 112),
    "ink-300": (156, 156, 162),
    "line": (228, 228, 231),
    "state-ok": (19, 107, 66),
    # A form error is red and may not be the brand's red: a field that has
    # gone wrong and a button that is working must not be the same colour.
    "state-err": (164, 38, 44),
    "state-warn": (132, 84, 0),
    "fixed-paper": (255, 255, 255),
    "fixed-ink": (28, 28, 30),
    "on-wine": (255, 255, 255),
    "on-wine-muted": (161, 161, 170),
}

# The dark theme. Only the roles that move.
#
# The fills are not here, and that is the whole idea: brand.200, brand.500 and
# brand.600 are the school's own colours rather than a role, so they are the
# same in both themes and their labels are fixed to match. What moves is the
# page, the cards, the ink ramp, the hairline, the states, the red used as
# *text*, the graphite accent — and the band, which is a fill that has no
# choice: it cannot be darker than a page that is already near black.
DARK = {
    "brand-100": (14, 14, 16),
    "brand-50": (26, 26, 28),
    "brand-link": (255, 138, 144),
    "brand-700": (212, 212, 216),
    "brand-900": (37, 37, 41),
    "ink": (237, 237, 240),
    "ink-500": (161, 161, 170),
    "ink-300": (107, 107, 112),
    "line": (46, 46, 51),
    "state-ok": (74, 190, 145),
    "state-warn": (232, 176, 61),
    "state-err": (255, 154, 147),
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
    # Where a photograph is going to be, core v38. It marks a frame the owner
    # has not filled yet, so it sits with the pictograms rather than with the
    # brand marks below.
    "image",
    # The four accounts the school posts on, core v36. They are in
    # FILLED_ICONS: see the note there.
    "facebook",
    "instagram",
    "tiktok",
    "youtube",
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

# The symbols drawn as a fill rather than a stroke.
#
# B.6 sets the whole sprite at a 1.75 stroke on a 24 grid, and every pictogram
# on the site obeys it. A play mark does not: it is a solid triangle everywhere
# anybody has ever seen one, and an outlined one reads as a cursor rather than
# as "press this". Named here so the exception is one line in a tuple rather
# than a hole in the rule.
#
# The four social marks joined it at core v36, and for a reason of the same
# kind: they are the brands' own shapes, and being recognised at a glance is
# the whole of their job. The first attempt drew them on the 1.75 grid like
# everything else and produced three rounded squares nobody could tell apart.
# They keep currentColor, so the rule they do obey is the one that matters —
# an icon takes the colour of the text beside it.
FILLED_ICONS = ("play", "facebook", "instagram", "tiktok", "youtube")


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


def aliases(body: str) -> dict[str, str]:
    """The tokens declared as `var(--other)` rather than as a triplet.

    Since core v43 the table has two layers and the second one is nothing but
    these: --brand-500 is var(--brand-red), --line is var(--border). They are
    real tokens as far as the cascade is concerned, so they have to be real
    here too.
    """
    return dict(re.findall(r"--([a-z0-9-]+):\s*var\(--([a-z0-9-]+)\)\s*;", body))


def resolve(table: dict, links: dict[str, str], theme: str) -> dict:
    """Follow each alias to a triplet, in the table it belongs to.

    After the merge rather than before: the dark theme redefines --surface and
    --brand-50 points at it, so the card colour has to be worked out against
    the dark table even though the alias itself was written in the light one.
    """
    for name, first in links.items():
        seen, target = {name}, first
        while target not in table and target in links:
            assert target not in seen, f"--{name} resolves in a circle in {theme}"
            seen.add(target)
            target = links[target]
        if target in table:
            table[name] = table[target]
    return table


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
    light_body = block("  :root {")
    media_body = block("    :root:not([data-theme='light']) {")
    explicit_body = block("  :root[data-theme='dark'] {")

    light, light_links = declarations(light_body), aliases(light_body)
    media, media_links = declarations(media_body), aliases(media_body)
    explicit, explicit_links = declarations(explicit_body), aliases(explicit_body)

    # A literal in the dark block beats an alias the light block declared for
    # the same name: --brand-link is var(--brand-red-dark) in the light theme
    # and a pale red of its own in the dark one, and resolving the inherited
    # alias over it would put the light theme's red back on the dark page.
    dark_links = {
        name: target
        for name, target in {**light_links, **explicit_links}.items()
        if name not in explicit
    }
    tables = {
        "light": resolve({**light}, light_links, "light"),
        "dark": resolve({**light, **explicit}, dark_links, "dark"),
        # The two doors are compared as written, aliases and all, so a block
        # that spells a colour one way and its twin the other still fails.
        "media": {**media, **{k: ("var", v) for k, v in media_links.items()}},
        "explicit": {**explicit, **{k: ("var", v) for k, v in explicit_links.items()}},
    }

    # Not a token: the fill a state chip paints for itself, which is a tenth of
    # the ground's own foreground over the ground. scripts/check_contrast.py
    # builds the same two and says why — the colours on a chip have to be
    # checked against the chip, not against the bare page, and two of the three
    # cleared the page and failed the chip.
    def mix(fg, bg, alpha=0.1):
        return tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg, strict=True))

    for name in ("light", "dark"):
        table = tables[name]
        table["chip-on-page"] = mix(table["ink"], table["brand-100"])
        table["chip-on-card"] = mix(table["ink"], table["brand-50"])
    return tables


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
        assert f"rgb(var({variable}))" in block(f".{ground} {{"), (
            f".{ground} must take its text colour from {variable}, not a token that swaps"
        )


def test_white_on_the_pink_tile_is_never_emitted(themes: dict) -> None:
    """1.69:1, the one pair B.3 refuses outright."""
    for theme in ("light", "dark"):
        assert contrast((255, 255, 255), themes[theme]["brand-200"]) < 2.0
    assert "text-brand-50" not in block(".u-ground-pink {")
    assert "text-fixed-paper" not in block(".u-ground-pink {")


def test_the_fill_crimson_and_the_text_crimson_are_separate(themes: dict) -> None:
    """One token for both is unreadable in the dark theme.

    B.2 lightens the red *text* to #FF8FAB so it reads on the near black page,
    and leaves the fills alone because they are the brand. White on the
    lightened red is 1.90, so a single token would have painted every hovered
    button in the dark theme at 1.90 the moment the text was made legible.
    """
    assert themes["light"]["brand-600"] == themes["light"]["brand-link"]
    assert themes["dark"]["brand-600"] != themes["dark"]["brand-link"]
    # And the same for the graphite accent: it is the ink in the light theme
    # and has to turn over in the dark one, where graphite on graphite is
    # nothing.
    assert themes["light"]["brand-700"] == themes["light"]["brand-ink"]
    assert themes["dark"]["brand-700"] != themes["light"]["brand-ink"]
    assert contrast(themes["dark"]["brand-link"], themes["dark"]["brand-100"]) >= 4.5
    assert contrast(themes["dark"]["fixed-paper"], themes["dark"]["brand-600"]) >= 4.5


def test_the_card_sits_above_the_page(themes: dict) -> None:
    """The card is lighter than the page it sits on, in both themes.

    B.8 used to say the stronger thing — that no ground is white at all —
    because the owner did not want a white page under a pink palette. Core
    v43 took the white back for the card face and kept the rule that matters:
    a card has to read as lifted off the page without a border, and in a
    palette with no hue in the greys the only thing that can say so is the
    step between the two. So the page is still never white, and the card is,
    and the relationship between them is checked rather than assumed.
    """
    for theme in ("light", "dark"):
        assert themes[theme]["brand-100"] != (255, 255, 255), theme
        lit = luminance(themes[theme]["brand-50"]) - luminance(themes[theme]["brand-100"])
        assert lit > 0, f"{theme}: the card is not lighter than the page"

    assert themes["light"]["brand-50"] == (255, 255, 255)
    body = block("  body {")
    assert "bg-brand-100" in body
    # Still no literal white anywhere: the card gets there through --surface.
    assert "bg-white" not in css() and "background: #fff" not in css().lower()


def test_every_token_is_wired_into_the_config(themes: dict) -> None:
    """A colour the config cannot reach is a colour no template can use.

    The brand layer is deliberately not wired either: --brand-red and the rest
    name the colours, and the roles below them are what a template can reach.
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
    """tech.md section 2 bans third party font hosts on public pages.

    Only the @font-face urls are checked. The stylesheet also carries one data
    uri — the scribbled underline, used as a mask on the ghost button and the
    current menu item — and a data uri fetches nothing from anywhere, which is
    the property this test is actually about.
    """
    text = css()
    faces = re.findall(r"@font-face\s*\{[^}]*\}", text, re.S)
    urls = [url for face in faces for url in re.findall(r"url\(([^)]+)\)", face)]
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
    "#FFFFFF",  # brand.50, the card the letter sits on
    "#F4F4F5",  # brand.100, the page around it
    "#E4E4E7",  # line
    "#1C1C1E",  # ink
    "#6B6B70",  # ink.500
    "#E1141D",  # brand.500 — a fill, and the rule beside a quote
    "#C01017",  # brand.link — the red as text, which brand.500 is too light to be
}


def test_the_emails_use_the_site_palette() -> None:
    """The confirmation should look like the site that sent it.

    Repainted four times now: at core v2 when the palette moved into
    FRONTEND.md, at v25 when the page went warm grey and the purple became a
    blue, at v29 when the whole language came off the owner's logo, and at v43
    when it came off the *right* logo. An email cannot read a css variable —
    many clients strip <style> outright — so inline hex is the only way to
    colour one, and this is what keeps that hand written copy in step.

    It checked nothing at all until core v43. A backspace byte had got into
    the pattern itself — a raw string, so it stayed a control character rather
    than an escape — and it asked for that byte after the six digits. Nothing
    ever matched, every mail reported an empty set of colours, and the test
    passed on all of them. An editor does not show it and neither does a diff;
    the only reason it surfaced is that the palette changed underneath the
    test and the test went on passing.
    """
    strays: dict[str, set[str]] = {}
    for path in sorted(EMAIL_TEMPLATES.glob("*.html")):
        found = re.findall(r"#[0-9A-Fa-f]{6}", path.read_text("utf-8"))
        used = {value.upper() for value in found}
        if used - EMAIL_PALETTE:
            strays[path.name] = used - EMAIL_PALETTE
    assert not strays, f"colours that are not in A.2: {strays}"


def test_the_emails_keep_their_text_readable(themes: dict) -> None:
    """4.5:1 on every pair the mail actually puts together.

    An email has no dark theme to swap into, so these are the light values and
    they have to carry it on their own.

    These were the core v25 colours until v43 — a blue and a warm grey that no
    mail has carried since v29 — and they measured each other rather than
    anything the templates use. They are the real pairs now, and they are
    named out of EMAIL_PALETTE so that changing a colour there fails here
    rather than silently.
    """
    pairs = [
        ("#1C1C1E", "#FFFFFF", "body on the card"),
        ("#6B6B70", "#FFFFFF", "quiet text on the card"),
        ("#6B6B70", "#F4F4F5", "quiet text on the ground"),
        ("#C01017", "#FFFFFF", "the name, the phone number and the links"),
        ("#FFFFFF", "#E1141D", "the label on the one button a mail paints"),
    ]
    for fore, back, what in pairs:
        assert {fore, back} <= EMAIL_PALETTE, f"{what} names a colour off the palette"
        found = contrast(hex_to_rgb(fore), hex_to_rgb(back))
        assert found >= 4.5, f"{what} is {found:.2f}:1"

    # And the mail's palette is the site's: every colour in it is a token.
    site = {tuple(v) for v in themes["light"].values()}
    for value in EMAIL_PALETTE:
        assert hex_to_rgb(value) in site, f"{value} is in no token of the light theme"


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


def test_the_brand_layer_is_declared(themes: dict) -> None:
    """The ten colours of core v43, named once each.

    The role vocabulary above points at these. Checking both tables is what
    catches the change that edits a role back into a literal and leaves the
    brand layer saying something else.
    """
    assert {k: v for k, v in themes["light"].items() if k in BRAND} == BRAND


def test_every_role_is_an_alias_or_its_own_literal() -> None:
    """No role may repeat a value the brand layer already names.

    A second copy is a copy that drifts. The states are the exception and say
    so: a green, an amber and an error red are nobody's brand colour, so they
    are literals in the role table and appear nowhere else.
    """
    body = block("  :root {")
    links = aliases(body)
    literals = declarations(body)
    named = {value: name for name, value in literals.items() if name in BRAND}
    strays = {
        name: value
        for name, value in literals.items()
        if name not in BRAND and name not in links and value in named
    }
    assert not strays, f"these repeat a brand colour instead of pointing at it: {strays}"
