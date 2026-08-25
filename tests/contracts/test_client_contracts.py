"""External client seam, tech.md sections 6 and 9.

The fake is the seam: it validates what a slice sends and fails loudly on junk,
and it can play the error paths a slice has to survive.
"""

from pathlib import Path

import pytest

from apps.core.clients import (
    ClientPayloadError,
    ClientServerError,
    ClientTimeout,
    FakeMailClient,
    FakeSmsClient,
    MailClient,
    SmsClient,
    get_mail_client,
    get_sms_client,
)

GOOD_MAIL = {
    "to": ["biuro@example.com"],
    "subject": "Nowe zgłoszenie",
    "body_html": "<p>hi</p>",
    "body_text": "hi",
}


def test_fakes_satisfy_the_protocols() -> None:
    assert isinstance(FakeMailClient(), MailClient)
    assert isinstance(FakeSmsClient(), SmsClient)


def test_settings_resolve_to_fakes_in_tests() -> None:
    assert isinstance(get_mail_client(), FakeMailClient)
    assert isinstance(get_sms_client(), FakeSmsClient)


def test_mail_lands_in_the_outbox(tmp_path: Path) -> None:
    client = FakeMailClient(outbox=tmp_path)
    message_id = client.send(**GOOD_MAIL)

    messages = client.messages()
    assert len(messages) == 1
    assert messages[0]["message_id"] == message_id
    assert messages[0]["to"] == ["biuro@example.com"]


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("to", [], "non empty list"),
        ("to", ["not-an-address"], "invalid recipient"),
        ("to", "biuro@example.com", "non empty list"),
        ("subject", "   ", "subject must not be empty"),
    ],
)
def test_junk_is_rejected(tmp_path: Path, field: str, value: object, match: str) -> None:
    client = FakeMailClient(outbox=tmp_path)
    payload = {**GOOD_MAIL, field: value}

    with pytest.raises(ClientPayloadError, match=match):
        client.send(**payload)  # type: ignore[arg-type]
    assert client.messages() == []


def test_empty_body_is_rejected(tmp_path: Path) -> None:
    client = FakeMailClient(outbox=tmp_path)
    with pytest.raises(ClientPayloadError, match="text or an html body"):
        client.send(**{**GOOD_MAIL, "body_html": "", "body_text": " "})


def test_server_error_mode(tmp_path: Path) -> None:
    client = FakeMailClient(outbox=tmp_path, fail_with=500)
    with pytest.raises(ClientServerError) as exc:
        client.send(**GOOD_MAIL)

    assert exc.value.status == 500
    assert client.messages() == []


def test_timeout_mode(tmp_path: Path) -> None:
    client = FakeMailClient(outbox=tmp_path, fail_with="timeout")
    with pytest.raises(ClientTimeout):
        client.send(**GOOD_MAIL)
    assert client.messages() == []


def test_bad_payload_beats_the_failure_mode(tmp_path: Path) -> None:
    """A slice sending junk must hear about the junk, not about the outage."""
    client = FakeMailClient(outbox=tmp_path, fail_with="timeout")
    with pytest.raises(ClientPayloadError):
        client.send(**{**GOOD_MAIL, "to": []})


def test_sms_validates_and_records() -> None:
    client = FakeSmsClient()
    message_id = client.send(to="+48605065795", text="Dziękujemy")

    assert client.sent == [{"message_id": message_id, "to": "+48605065795", "text": "Dziękujemy"}]


def test_sms_rejects_junk() -> None:
    client = FakeSmsClient()
    with pytest.raises(ClientPayloadError, match="invalid recipient"):
        client.send(to="call me", text="hi")
    with pytest.raises(ClientPayloadError, match="must not be empty"):
        client.send(to="+48605065795", text="  ")
