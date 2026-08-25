"""Phone normalisation, DEV.md S3.1.

Every way a visitor writes the same number must land on one string, otherwise
the owner sees the same person twice and calls them twice.
"""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.leads.services import COUNTRY_CODE, NATIONAL_LENGTH, hash_ip, normalize_phone

CANONICAL = "+48605065795"

national = st.text(alphabet="123456789", min_size=1, max_size=1).flatmap(
    lambda head: st.text(
        alphabet="0123456789", min_size=NATIONAL_LENGTH - 1, max_size=NATIONAL_LENGTH - 1
    ).map(lambda rest: head + rest)
)
separators = st.sampled_from(["", " ", "-", " - ", " ", "."])


@pytest.mark.parametrize(
    "written",
    [
        "+48 605-065-795",
        "605065795",
        "48605065795",
        "+48605065795",
        "0048 605 065 795",
        "0 605 065 795",
        "(48) 605-065-795",
        "  605 065 795  ",
        "605-065-795",
    ],
)
def test_the_documented_spellings_all_land_on_one_string(written: str) -> None:
    assert normalize_phone(written) == CANONICAL


@given(national, separators, separators)
def test_any_grouping_of_the_same_digits_agrees(digits: str, first: str, second: str) -> None:
    spaced = f"{digits[:3]}{first}{digits[3:6]}{second}{digits[6:]}"

    assert normalize_phone(spaced) == normalize_phone(digits)
    assert normalize_phone(f"+{COUNTRY_CODE}{spaced}") == normalize_phone(digits)
    assert normalize_phone(f"00{COUNTRY_CODE} {spaced}") == normalize_phone(digits)


@given(national)
def test_the_result_is_always_the_canonical_shape(digits: str) -> None:
    assert re.fullmatch(rf"\+{COUNTRY_CODE}\d{{{NATIONAL_LENGTH}}}", normalize_phone(digits))


@given(national)
def test_normalisation_is_idempotent(digits: str) -> None:
    once = normalize_phone(digits)
    assert normalize_phone(once) == once


@pytest.mark.parametrize("junk", ["", None, "abc", "12", "1234567890123456", "+1 202 555 0143"])
def test_something_unusable_is_rejected_rather_than_stored(junk: str | None) -> None:
    assert normalize_phone(junk) == ""


def test_a_national_number_starting_with_the_country_code_survives() -> None:
    """486050657 is nine digits, not a country code plus seven."""
    assert normalize_phone("486050657") == "+48486050657"


octet = st.integers(min_value=0, max_value=255)
addresses = st.tuples(octet, octet, octet, octet).map(
    lambda parts: ".".join(str(part) for part in parts)
)
salts = st.text(min_size=1, max_size=20)


@given(addresses, salts)
def test_the_ip_hash_never_contains_the_address(ip: str, salt: str) -> None:
    """A single character would appear in any hex digest, so use real addresses."""
    digest = hash_ip(ip, salt)

    assert len(digest) == 64
    assert ip not in digest


@given(addresses, salts)
def test_the_same_address_hashes_the_same_way(ip: str, salt: str) -> None:
    assert hash_ip(ip, salt) == hash_ip(ip, salt)
    assert hash_ip(ip, salt) != hash_ip(ip, salt + "x")


def test_no_address_means_no_hash() -> None:
    assert hash_ip("", "salt") == ""
    assert hash_ip(None, "salt") == ""
