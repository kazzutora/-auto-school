"""The legacy url table, tech.md sections 4.8 and 15.

django.contrib.redirects and its middleware are already wired up. What was
missing is the data: every old path answers 404 until these rows exist, and the
old site is what search engines still hold.

The rows live in data/legacy/redirects.csv, frozen in tech.md section 4.8. The
loader is idempotent, so it can run on every deploy.
"""

import csv
from pathlib import Path

from django.conf import settings
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site

CSV_PATH = Path(settings.BASE_DIR) / "data" / "legacy" / "redirects.csv"


def read_table(path: Path | None = None) -> list[tuple[str, str]]:
    """The (old_path, new_path) pairs, in file order."""
    source = path or CSV_PATH
    with source.open(encoding="utf-8", newline="") as handle:
        return [(row["old_path"], row["new_path"]) for row in csv.DictReader(handle)]


def load_redirects(path: Path | None = None) -> int:
    """Put the table in the database, once. Returns the number of rows.

    update_or_create on the old path: running this twice changes nothing, and
    editing a target in the csv moves the existing row rather than leaving two.
    """
    site = Site.objects.get_current()
    pairs = read_table(path)

    for old_path, new_path in pairs:
        Redirect.objects.update_or_create(
            site=site, old_path=old_path, defaults={"new_path": new_path}
        )
    return len(pairs)
