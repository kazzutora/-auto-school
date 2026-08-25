"""Celery application and beat schedule.

tech.md section 6 freezes both the task names and the schedule. The schedule
lives here and nowhere else, so a feature slice cannot quietly add a periodic
job.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")


class OskCelery(Celery):
    """Celery app that names tasks the way tech.md section 6 spells them.

    Task modules live under apps/, so the default naming would produce
    apps.core.tasks.ping while the contract says core.tasks.ping. Stripping the
    package prefix here keeps every task on contract without repeating an
    explicit name= on each one.
    """

    def gen_task_name(self, name: str, module: str) -> str:
        if module.startswith("apps."):
            module = module.removeprefix("apps.")
        return super().gen_task_name(name, module)


app = OskCelery("osk")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "db-backup": {
        "task": "core.tasks.db_backup",
        "schedule": crontab(hour="2", minute="0"),
    },
    "check-links": {
        "task": "links.tasks.check_links",
        "schedule": crontab(hour="3", minute="20"),
    },
    "ping-sitemap": {
        "task": "core.tasks.ping_sitemap",
        "schedule": crontab(hour="4", minute="0"),
    },
}
