"""The legacy url table, tech.md sections 4.8 and 15.

django.contrib.redirects and its middleware are already wired up. What was
missing is the data: every old path answers 404 until these rows exist, and the
old site is what search engines still hold.

The rows live in data/legacy/redirects.csv. The loader is idempotent, so it can
run on every deploy.

The old site was a single page with anchors, so half the table is fragments:
``/#pliki``, ``/#kontakt`` and the rest. A browser never sends the fragment, so
those rows cannot be served by django.contrib.redirects and are deliberately
kept out of it — ``fragment_map()`` hands them to the home page instead, where
static/js/app.js does the jump. One file stays the source of truth for both.
"""

import csv
from pathlib import Path

from django.conf import settings
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site

CSV_PATH = Path(settings.BASE_DIR) / "data" / "legacy" / "redirects.csv"

FRAGMENT = "#"


def read_table(path: Path | None = None) -> list[tuple[str, str]]:
    """The (old_path, new_path) pairs, in file order. Fragments included."""
    source = path or CSV_PATH
    with source.open(encoding="utf-8", newline="") as handle:
        return [(row["old_path"], row["new_path"]) for row in csv.DictReader(handle)]


def server_table(path: Path | None = None) -> list[tuple[str, str]]:
    """The rows a request can actually carry: everything without a fragment."""
    return [(old, new) for old, new in read_table(path) if FRAGMENT not in old]


def fragment_map(path: Path | None = None) -> dict[str, str]:
    """``{"ofirmie": "/o-nas/"}`` — the anchors of the old one-page site.

    A fragment never reaches the server, so this is the half of the table the
    browser has to resolve. Keyed on the bare anchor, which is what
    ``location.hash`` gives once the ``#`` is stripped.
    """
    return {
        old.split(FRAGMENT, 1)[1]: new
        for old, new in read_table(path)
        if FRAGMENT in old and old.split(FRAGMENT, 1)[1]
    }


def load_redirects(path: Path | None = None) -> int:
    """Put the table in the database, once. Returns the number of rows.

    update_or_create on the old path: running this twice changes nothing, and
    editing a target in the csv moves the existing row rather than leaving two.
    """
    site = Site.objects.get_current()
    pairs = server_table(path)

    for old_path, new_path in pairs:
        Redirect.objects.update_or_create(
            site=site, old_path=old_path, defaults={"new_path": new_path}
        )
    return len(pairs)
