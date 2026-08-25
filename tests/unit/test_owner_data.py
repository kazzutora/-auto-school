"""Release gate for content the owner still owes, tech.md section 16.

Excluded from the normal run: it is expected to fail until the list is empty.
Run it on purpose with `pytest -m owner_data`, and do not ship production while
it is red.
"""

import pytest

from scripts.seed import owner_data_gaps, run


@pytest.mark.owner_data
@pytest.mark.django_db
def test_no_owner_data_is_missing() -> None:
    run()
    gaps = owner_data_gaps()
    report = "\n".join(f"  {gap}" for gap in gaps)
    assert not gaps, f"production is blocked on {len(gaps)} items:\n{report}"
