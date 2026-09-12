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

# The one image that may carry an empty alt: a decorative one that says so.
#
# c-picture's own contract spells this out — "a decorative image passes alt=''
# together with aria-hidden and says so" — and so does tech.md section 8. An
# empty alt on its own is a forgotten attribute; an empty alt beside
# aria-hidden is a decision, and it is the right decision for a mark sitting
# next to the same words in text, where alt text makes a screen reader read the
# school's name twice.
#
# The pair is what is accepted, never the empty alt alone: that is the whole
# difference between the convention and the bug it looks like.
ARIA_HIDDEN = re.compile(r"\baria-hidden=(\"true\"|'true')")


def template_files() -> list[Path]:
    roots = [Path(directory) for directory in settings.TEMPLATES[0]["DIRS"]]
    roots += [Path(settings.BASE_DIR) / "apps"]
    return sorted({path for root in roots for path in root.rglob("*.html")})


# Both comment forms django understands. A tag named in prose is documentation,
# not markup: without this, explaining why a template does something with
# <c-picture> is enough to fail the gate.
COMMENTS = re.compile(r"\{#.*?#\}|\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.S)


def markup_of(path: Path) -> str:
    """The template with its comments taken out."""
    return COMMENTS.sub("", path.read_text(encoding="utf-8"))


def alt_of(tag: str) -> str | None:
    """The alt value as written, or None when the attribute is absent."""
    found = ALT_ATTRIBUTE.search(tag)
    return found.group(1)[1:-1].strip() if found else None


def is_decorative(tag: str) -> bool:
    """An empty alt that was meant: the tag also declares itself decorative."""
    return alt_of(tag) == "" and bool(ARIA_HIDDEN.search(tag))


def offenders_for(pattern: re.Pattern[str]) -> list[str]:
    return [
        f"{path.relative_to(settings.BASE_DIR)}: {tag}"
        for path in template_files()
        for tag in pattern.findall(markup_of(path))
        if not alt_of(tag) and not is_decorative(tag)
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


@pytest.mark.a11y
def test_a_decorative_image_has_to_declare_itself() -> None:
    """The exception above is narrow, and this is what keeps it narrow.

    An empty alt with no aria-hidden beside it is indistinguishable from a
    forgotten attribute, so it stays an offender. This test exists so that the
    day somebody widens is_decorative() to accept a bare empty alt, the reason
    the pair is required goes red rather than quiet.
    """
    assert not is_decorative('<img src="x" alt="">')
    assert is_decorative('<img src="x" alt="" aria-hidden="true">')
    assert not is_decorative('<img src="x" aria-hidden="true">')
