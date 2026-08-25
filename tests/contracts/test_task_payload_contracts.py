"""Payload schemas against the table in tech.md section 6."""

import pytest

from apps.core.contracts import PAYLOAD_SCHEMAS, ContractError, validate_payload

# tech.md section 6, one row per task.
TECH_MD_PAYLOADS = {
    "leads.tasks.notify_owner": {"lead_id": 1},
    "leads.tasks.send_confirmation": {"lead_id": 1},
    "gallery.tasks.build_renditions": {"model": "gallery.GalleryImage", "pk": 7},
    "links.tasks.check_links": {},
    "core.tasks.ping_sitemap": {},
    "core.tasks.db_backup": {},
}


def test_every_task_in_tech_md_has_a_schema() -> None:
    assert set(PAYLOAD_SCHEMAS) == set(TECH_MD_PAYLOADS)


@pytest.mark.parametrize(("name", "payload"), TECH_MD_PAYLOADS.items())
def test_contract_payload_is_accepted(name: str, payload: dict) -> None:
    validate_payload(name, payload)


def test_unknown_task_is_rejected() -> None:
    with pytest.raises(ContractError, match="unknown task"):
        validate_payload("leads.tasks.invent_something", {})


def test_missing_key_is_rejected() -> None:
    with pytest.raises(ContractError, match="missing keys"):
        validate_payload("leads.tasks.notify_owner", {})


def test_extra_key_is_rejected() -> None:
    with pytest.raises(ContractError, match="unexpected keys"):
        validate_payload("leads.tasks.notify_owner", {"lead_id": 1, "hint": "x"})


def test_wrong_type_is_rejected() -> None:
    with pytest.raises(ContractError, match="must be int"):
        validate_payload("leads.tasks.notify_owner", {"lead_id": "1"})


def test_bool_does_not_pass_as_an_int() -> None:
    """bool subclasses int, and no payload field is a flag."""
    with pytest.raises(ContractError, match="must be int"):
        validate_payload("leads.tasks.notify_owner", {"lead_id": True})


def test_model_instance_is_rejected_payloads_carry_primitives() -> None:
    with pytest.raises(ContractError, match="must be int"):
        validate_payload("gallery.tasks.build_renditions", {"model": "x", "pk": object()})
