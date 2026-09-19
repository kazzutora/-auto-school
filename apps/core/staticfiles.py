"""A static finder that never serves the ``source/`` directories.

Two trees under ``static/`` hold originals rather than assets:

``static/img/brand/source/``
    the owner's raster logo, the generated mockup of the home page and their
    style sheet, ROSE.md A.1. The mockup is the reason this is not merely
    tidiness: it carries invented numbers — a 98% pass rate, 1000+ graduates,
    categories the school does not teach — and collecting it would publish
    those on our own domain under a guessable file name.

``static/img/source/``
    the 2400px photographs the crops are cut from, PHOTOS.md. Three times the
    weight of anything a page asks for.

Filtering in the finder rather than passing ``--ignore`` to collectstatic
covers the dev server and ``{% static %}`` as well, and cannot be forgotten on
a deploy. Overriding the command itself would not work here anyway:
``apps.core`` is listed after ``django.contrib.staticfiles``, so the original
wins the name.
"""

from collections.abc import Iterable
from pathlib import PurePath
from typing import Any

from django.contrib.staticfiles.finders import FileSystemFinder

PRIVATE_DIRS = frozenset({"source"})


def is_private(path: str) -> bool:
    """True when any segment of the relative path is a private directory."""
    return bool(PRIVATE_DIRS.intersection(PurePath(path.replace("\\", "/")).parts))


class PrivateSourceFilteredFinder(FileSystemFinder):
    """FileSystemFinder minus the originals."""

    def list(self, ignore_patterns: Iterable[str] | None) -> Any:
        for path, storage in super().list(ignore_patterns):
            if is_private(path):
                continue
            yield path, storage

    def find_location(self, root: str, path: str, prefix: str | None = None) -> str | None:
        if is_private(path):
            return None
        return super().find_location(root, path, prefix)
