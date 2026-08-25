"""Gallery background work, tech.md section 6."""

from typing import Any

from celery import Task, shared_task
from django.apps import apps

from apps.core.contracts import validate_payload
from apps.core.imaging import renditions
from apps.core.tasks import BaseTask

TASK_NAME = "gallery.tasks.build_renditions"


@shared_task(bind=True, base=BaseTask)
def build_renditions(self: Task, model: str, pk: int) -> dict[str, Any]:
    """Generate the WebP renditions for one row.

    Idempotent on the presence of the rendition files, tech.md section 6: a
    second run over the same row generates nothing and touches no storage.
    """
    validate_payload(TASK_NAME, {"model": model, "pk": pk})

    instance = apps.get_model(model).objects.get(pk=pk)
    source = instance.image
    if not source:
        return {"model": model, "pk": pk, "generated": []}

    generated = []
    for width, cache_file in renditions(source):
        # The idempotency key: an existing rendition is left alone.
        if cache_file.storage.exists(cache_file.name):
            continue
        cache_file.generate()
        generated.append(width)

    return {"model": model, "pk": pk, "generated": generated}
