"""Every img in every template carries an alt, tech.md section 8.

The per page checks only see the templates a fixture happens to render. This
one reads the files, so a picture on a page nobody has written a test for yet
still cannot ship without alt text.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

# The whole attribute list of one tag, however many lines it spans.
IMG_TAG = re.compile(r"<img\b[^>]*>", re.S)
ALT_ATTRIBUTE = re.compile(r"\balt=(\"[^\"]*\"|'[^']*')", re.S)

# The cotton component that renders the img, tech.md section 7. It hands alt
# straight to the tag, so a caller that forgets the prop ships an empty one.
PICTURE_TAG = re.compile(r"<c-picture\b[^>]*>", re.S)


def template_files() -> list[Path]:
    roots = [Path(directory) for directory in settings.TEMPLATES[0]["DIRS"]]
    roots += [Path(settings.BASE_DIR) / "apps"]
    return sorted({path for root in roots for path in root.rglob("*.html")})


def alt_of(tag: str) -> str | None:
    """The alt value as written, or None when the attribute is absent."""
    found = ALT_ATTRIBUTE.search(tag)
    return found.group(1)[1:-1].strip() if found else None


def offenders_for(pattern: re.Pattern[str]) -> list[str]:
    return [
        f"{path.relative_to(settings.BASE_DIR)}: {tag}"
        for path in template_files()
        for tag in pattern.findall(path.read_text(encoding="utf-8"))
        if not alt_of(tag)
    ]


def test_the_sweep_actually_finds_templates() -> None:
    """A broken path would make every assertion below pass on an empty list."""
    assert len(template_files()) > 10


@pytest.mark.a11y
def test_no_template_ships_an_img_without_alt() -> None:
    assert not offenders_for(IMG_TAG)


@pytest.mark.a11y
def test_every_picture_component_is_given_its_alt() -> None:
    """The img itself lives in cotton/picture.html, the alt comes from here."""
    assert not offenders_for(PICTURE_TAG)
