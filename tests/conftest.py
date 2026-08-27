"""Shared fixtures."""

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
