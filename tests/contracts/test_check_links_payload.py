"""links.tasks.check_links against tech.md section 6."""

from typing import Any

import pytest
from celery.exceptions import Retry

from apps.core.contracts import ContractError, validate_payload
from apps.links.tasks import TASK_NAME, check_links
from config.celery import app


def cause(error: BaseException) -> BaseException:
    """What actually went wrong inside the task.

    Every task runs under autoretry_for=(Exception,), tech.md section 6, so a
    failed eager run comes back as a Retry carrying the original exception.
    """
    return error.exc if isinstance(error, Retry) and error.exc else error


def test_the_task_is_registered_under_the_contract_name() -> None:
    assert TASK_NAME == "links.tasks.check_links"
    assert TASK_NAME in app.tasks


@pytest.mark.django_db
def test_the_beat_entry_reaches_the_implementation() -> None:
    """The schedule named this task for weeks before the module existed."""
    scheduled = {entry["task"] for entry in app.conf.beat_schedule.values()}
    assert TASK_NAME in scheduled

    result = app.tasks[TASK_NAME].apply().get()

    assert result == {"checked": 0, "failed": 0}


def test_the_contract_payload_is_empty() -> None:
    validate_payload(TASK_NAME, {})


@pytest.mark.parametrize("payload", [{"limit": 5}, {"url": "https://example.com/"}])
def test_junk_payload_is_rejected(payload: dict[str, Any]) -> None:
    with pytest.raises(ContractError):
        validate_payload(TASK_NAME, payload)


def test_the_task_takes_no_arguments() -> None:
    """Payloads carry primitives, and this one carries nothing at all."""
    with pytest.raises(BaseException) as raised:  # noqa: B017, PT011
        check_links.apply(kwargs={"limit": 5}).get()

    assert isinstance(cause(raised.value), TypeError)
