"""Celery wiring against the frozen contract in tech.md section 6."""

from celery.schedules import crontab

from apps.core.tasks import BaseTask, ping
from config.celery import app

# tech.md section 6, the beat rows: task name -> (hour, minute).
TECH_MD_SCHEDULE = {
    "core.tasks.db_backup": (2, 0),
    "links.tasks.check_links": (3, 20),
    "core.tasks.ping_sitemap": (4, 0),
}


def test_beat_schedule_matches_tech_md() -> None:
    scheduled = {entry["task"]: entry["schedule"] for entry in app.conf.beat_schedule.values()}
    assert set(scheduled) == set(TECH_MD_SCHEDULE)

    for task_name, (hour, minute) in TECH_MD_SCHEDULE.items():
        schedule = scheduled[task_name]
        assert isinstance(schedule, crontab)
        assert schedule.hour == {hour}, task_name
        assert schedule.minute == {minute}, task_name


def test_task_names_drop_the_apps_package_prefix() -> None:
    """tech.md names tasks core.tasks.x, while the modules live in apps/."""
    assert "core.tasks.ping" in app.tasks
    on_contract = [name for name in app.tasks if not name.startswith("celery.")]
    assert not [name for name in on_contract if name.startswith("apps.")]


def test_base_task_carries_the_retry_policy() -> None:
    assert ping.autoretry_for == (Exception,)
    assert ping.retry_backoff is True
    assert ping.retry_backoff_max == 600
    assert ping.max_retries == 5
    assert ping.acks_late is True


def test_autoretry_wrapping_is_actually_engaged() -> None:
    """Attributes alone prove nothing: celery must have wrapped run()."""
    assert isinstance(ping, BaseTask)
    assert hasattr(ping, "_orig_run")


def test_default_queue_is_default() -> None:
    assert app.conf.task_default_queue == "default"
