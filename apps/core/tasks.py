"""Shared Celery base class and the queue smoke task."""

from celery import Task, shared_task


class BaseTask(Task):
    """Retry policy every task in the project inherits, tech.md section 6.

    Celery reads these off the task instance in add_autoretry_behaviour, so a
    slice only has to pass base=BaseTask instead of repeating the options.
    """

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    max_retries = 5
    acks_late = True


@shared_task(bind=True, base=BaseTask)
def ping(self: Task) -> str:
    """Prove the broker, the worker and the result backend are wired up."""
    return "pong"
