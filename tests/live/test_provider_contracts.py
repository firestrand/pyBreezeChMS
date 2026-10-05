"""Opt-in probes; no provider data is printed, saved, or treated as a capture."""

from pathlib import Path

import pytest

from breeze.breeze import BreezeApi, BreezeError
from breeze.configuration import breeze_credentials
from breeze.models import Person

pytestmark = pytest.mark.live_provider


def test_breeze_summary_and_bounded_people_contract() -> None:
    try:
        url, key = breeze_credentials(Path(".env"))
        with BreezeApi(url, key) as client:
            summary = client.get_account_summary()
            if not isinstance(summary, dict):
                raise AssertionError("Breeze account-summary object contract changed.")
            # Bounded read probes on the authorized account; do not traverse or
            # retain its full people set, and never claim complete traversal.
            previous: set[str] = set()
            for offset in (0, 2):
                page = client.get_people(limit=2, offset=offset)
                if not isinstance(page, list) or len(page) > 2:
                    raise AssertionError("Breeze bounded people contract changed.")
                current = {str(Person.from_json(item).id) for item in page}
                if previous & current or len(current) != len(page):
                    raise AssertionError("Breeze people pagination repeated identifiers.")
                previous.update(current)
            for response in (client.list_forms(), client.list_funds()):
                if not isinstance(response, list):
                    raise AssertionError("Breeze forms/funds collection contract changed.")
    except BreezeError, ValueError:
        raise AssertionError("Breeze read-only provider contract check failed.") from None
