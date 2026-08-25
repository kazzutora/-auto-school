"""Celery payload schemas, tech.md section 6.

Payloads carry primitives only. Every task validates its payload here, so a
slice that ships junk fails at the seam instead of deep inside a worker.
"""

from collections.abc import Mapping
from typing import Any, TypedDict, get_type_hints


class ContractError(ValueError):
    """Payload does not match the schema frozen in tech.md section 6."""


class NotifyOwnerPayload(TypedDict):
    lead_id: int


class SendConfirmationPayload(TypedDict):
    lead_id: int


class BuildRenditionsPayload(TypedDict):
    model: str
    pk: int


class EmptyPayload(TypedDict):
    pass


PAYLOAD_SCHEMAS: dict[str, type] = {
    "leads.tasks.notify_owner": NotifyOwnerPayload,
    "leads.tasks.send_confirmation": SendConfirmationPayload,
    "gallery.tasks.build_renditions": BuildRenditionsPayload,
    "links.tasks.check_links": EmptyPayload,
    "core.tasks.ping_sitemap": EmptyPayload,
    "core.tasks.db_backup": EmptyPayload,
}


def validate_payload(name: str, payload: Mapping[str, Any]) -> None:
    """Raise ContractError unless payload matches the schema for task name."""
    try:
        schema = PAYLOAD_SCHEMAS[name]
    except KeyError:
        known = ", ".join(sorted(PAYLOAD_SCHEMAS))
        raise ContractError(f"unknown task {name!r}, tech.md section 6 lists: {known}") from None

    expected = get_type_hints(schema)

    missing = sorted(set(expected) - set(payload))
    if missing:
        raise ContractError(f"{name}: missing keys {missing}")

    unexpected = sorted(set(payload) - set(expected))
    if unexpected:
        raise ContractError(f"{name}: unexpected keys {unexpected}")

    for key, expected_type in expected.items():
        value = payload[key]
        # bool is a subclass of int, and no payload field is a flag.
        if isinstance(value, bool) or not isinstance(value, expected_type):
            got = type(value).__name__
            raise ContractError(f"{name}: {key} must be {expected_type.__name__}, got {got}")
