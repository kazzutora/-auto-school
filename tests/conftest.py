"""Shared fixtures."""

import re
from pathlib import Path
from typing import Any

import pytest
from django.conf import settings
from django.core.cache import cache
from django.utils import translation


@pytest.fixture(autouse=True)
def isolated_media(tmp_path: Path, settings: Any) -> None:
    """Keep uploads and renditions out of the working tree.

    Autouse on purpose, and it clears the cache as well: imagekit records
    "this rendition exists" in the django cache, and that state outlives the
    per test media root. Without the clear, a later test believes a file it can
    no longer see is already there and skips generating it.
    """
    settings.MEDIA_ROOT = tmp_path / "media"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def outbox(tmp_path: Path, settings: Any) -> Path:
    """Point FakeMailClient at a throwaway directory.

    Autouse for the same reason as isolated_media: the default outbox is
    tests/outbox/ inside the repository, and no test has any business writing
    there. Tests that assert on the mail take the path as an argument.
    """
    directory = tmp_path / "outbox"
    settings.MAIL_OUTBOX_DIR = directory
    return directory


@pytest.fixture(autouse=True)
def default_language() -> Any:
    """Every test starts in the language the site answers on by default.

    LocaleMiddleware activates the language of the request and never puts it
    back, so a single test that visits /ru/ leaves reverse() prefixing every url
    after it. It showed up as a route assertion that passed alone and failed in
    a full run.
    """
    translation.activate(settings.LANGUAGE_CODE)
    yield
    translation.activate(settings.LANGUAGE_CODE)


# --------------------------------------------------------------------------
# a11y helpers shared by every page test
#
# The alt rule was written out by hand in eight test modules, which is eight
# copies of one decision. It changed once — when tech.md section 8's convention
# for a decorative image finally had to be honoured — and that meant editing all
# eight. It lives here now so the next change is one edit.


_IMG = re.compile(r"<img[^>]*>")
_ALT_TEXT = re.compile(r'alt="[^"]+"')
_ALT_EMPTY = re.compile(r'alt=""')
_ARIA_HIDDEN = re.compile(r'aria-hidden="true"')


def images_without_alt(html: str) -> list[str]:
    """Every <img> in the markup that carries neither alt text nor a reason.

    tech.md section 8 wants alt on every image. The single exception, fixed by
    cotton/picture.html's own contract, is a decorative image that declares
    itself: alt="" *together with* aria-hidden="true". The pair is what makes
    the emptiness a decision rather than a forgotten attribute, which is why
    neither half is accepted on its own.
    """
    return [
        tag
        for tag in _IMG.findall(html)
        if not _ALT_TEXT.search(tag)
        and not (_ALT_EMPTY.search(tag) and _ARIA_HIDDEN.search(tag))
    ]


# The grounds a section can sit on, ROSE.md B.2 and B.8, in the order the class
# list has to be tested: the ones that are a utility of their own before the one
# that is a background colour, because a wine band carries no bg- class.
#
# Shared for the same reason images_without_alt is: two page tests had their own
# copy, neither knew about the card face when it arrived, and both quietly
# reported every pale band as the page itself — which made the alternation they
# were checking look broken where it was not.
#
# There is no white here and there is no `paper` marker either: B.8 gives the
# page one ground, brand.100, and it is what a section falls through to.
_GROUNDS = (
    ("wine", ("u-ground-wine",)),
    ("pink", ("u-ground-pink",)),
    ("brand", ("u-ground-brand",)),
    ("card", ("bg-brand-50",)),
)


def section_grounds(html: str) -> list[str]:
    """The ground of every <section> on the page, in document order."""
    grounds = []
    for classes in re.findall(r'<section[^>]*class="([^"]*)"', html):
        for name, markers in _GROUNDS:
            if any(marker in classes for marker in markers):
                grounds.append(name)
                break
        else:
            grounds.append("paper")
    return grounds


def repeated_grounds(html: str) -> list[int]:
    """Indices of sections whose ground repeats the one before them.

    B.8 point 2: two sections of the same colour in a row read as one long
    block, and the reader loses the seam between two different things.
    """
    grounds = section_grounds(html)
    return [i for i in range(1, len(grounds)) if grounds[i] == grounds[i - 1]]
