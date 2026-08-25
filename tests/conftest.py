"""Shared fixtures."""

from pathlib import Path
from typing import Any

import pytest
from django.core.cache import cache


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
