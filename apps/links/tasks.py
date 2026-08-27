"""Links background work, tech.md section 6 and DEV.md S7.2."""

import logging
from typing import Any

from celery import Task, shared_task
from django.utils import timezone

from apps.core.contracts import validate_payload
from apps.core.tasks import BaseTask
from apps.links import checker, selectors
from apps.links.models import HTTP_ERROR, UsefulLink

logger = logging.getLogger(__name__)

TASK_NAME = "links.tasks.check_links"


def _failed(result: checker.CheckResult) -> bool:
    return bool(result.error) or (result.status is not None and result.status >= HTTP_ERROR)


@shared_task(bind=True, base=BaseTask)
def check_links(self: Task) -> dict[str, Any]:
    """Look at every active link once a night, tech.md section 6.

    Repeatable by nature: the sweep owns three fields and overwrites them, so
    running it twice in a day leaves the same state. It writes with update()
    rather than save() on purpose, because updated_at belongs to the owner's
    edits and a night job has no business touching it.

    Nothing here raises for a single link. A dead host is the normal outcome
    this task exists to record, and it must not cost the other eleven rows
    their check, DEV.md S7.2.
    """
    validate_payload(TASK_NAME, {})

    agent = checker.user_agent()
    checked = 0
    failed = 0

    for link in selectors.active_links():
        try:
            result = checker.check(link.url, agent=agent)
        except Exception as error:  # the checker promises not to, so this is a bug
            logger.exception("link check crashed for %s", link.url)
            result = checker.CheckResult(error=f"{type(error).__name__}: {error}")

        UsefulLink.objects.filter(pk=link.pk).update(
            last_status=result.status,
            last_error=result.error[: checker.ERROR_LIMIT],
            last_checked_at=timezone.now(),
        )
        checked += 1
        if _failed(result):
            failed += 1

    return {"checked": checked, "failed": failed}
