"""Fill django.contrib.redirects from the legacy table, tech.md section 4.8.

    docker compose exec web python manage.py load_redirects

tech.md wants a data migration for this. A migration is written in LEAD mode,
so the loader lives here meanwhile: the command is idempotent and the migration
can call load_redirects() when it lands.
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.core.redirects import load_redirects


class Command(BaseCommand):
    help = "Load the legacy url table from data/legacy/redirects.csv."

    def handle(self, *args: Any, **options: Any) -> None:
        loaded = load_redirects()
        self.stdout.write(self.style.SUCCESS(f"{loaded} redirects in place"))
