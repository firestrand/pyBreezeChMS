"""Importer regression tests using synthetic financial records."""

import importlib.util
import json
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import requests

from breeze.breeze import BreezeApi, BreezeError, HttpResponse

# The sample is deliberately not part of the published Breeze package.
_spec = importlib.util.spec_from_file_location(
    "easytithe_importer", Path(__file__).parents[1] / "samples" / "easytithe_importer.py"
)
assert _spec is not None and _spec.loader is not None
_importer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_importer)
Contribution = _importer.Contribution
import_contributions = _importer.import_contributions

ROW = {
    "Name": "A.* Person",
    "Date": "10/01/2026",
    "Fund": 'A "quoted" fund',
    "Amount": "$1,000.25",
    "Type": "onCARD",
    "Email": "test@example.invalid",
    "PersonID": "42",
}


class Response(requests.Response):
    def __init__(self, value: object) -> None:
        super().__init__()
        self._content = json.dumps(value).encode()
        self._content_consumed = True
        self.status_code = 200


class Connection:
    def __init__(self, people: object, existing: object = None) -> None:
        self.people = people
        self.existing = [] if existing is None else existing
        self.writes: list[dict[str, list[str]]] = []
        self.calls = 0

    def get(
        self,
        url: str,
        *,
        verify: bool,
        params: Mapping[str, str],
        headers: Mapping[str, str],
        timeout: float,
        stream: bool,
        allow_redirects: bool,
    ) -> HttpResponse:
        self.calls += 1
        parsed = urlsplit(url)
        if parsed.path == "/api/people/?":
            return Response(self.people)
        if parsed.path == "/api/people/":
            return Response(self.people)
        if parsed.path == "/api/giving/list":
            return Response(self.existing)
        assert parsed.path == "/api/giving/add"
        self.writes.append(parse_qs(parsed.query))
        return Response({"payment_id": "test-payment"})


@pytest.mark.parametrize("amount", ["invalid", "NaN", "Infinity", "-1"])
def test_invalid_amount_fails_before_import(amount: str) -> None:
    with pytest.raises(ValueError):
        Contribution({**ROW, "Amount": amount})


def test_contribution_does_not_mutate_caller_and_formats_date() -> None:
    row = dict(ROW)
    contribution = Contribution(row)
    contribution.fund = "other"
    assert row == ROW
    assert contribution.date == "2026-10-01"
    assert contribution.amount == "1000.25"


def test_exact_name_match_and_fund_json_round_trip() -> None:
    connection = Connection([{"id": "1", "first_name": "A.*", "last_name": "Person"}])
    with BreezeApi("https://demo.breezechms.com", "synthetic-key", connection=connection) as client:
        assert import_contributions(client, [Contribution(ROW)]) == 1
    assert connection.writes[0]["person_id"] == ["1"]
    assert json.loads(connection.writes[0]["funds_json"][0]) == [
        {"name": 'A "quoted" fund', "amount": "1000.25"},
    ]


def test_regex_like_name_does_not_match_other_person() -> None:
    connection = Connection([{"id": "2", "first_name": "Alice", "last_name": "Person"}])
    with BreezeApi("https://demo.breezechms.com", "synthetic-key", connection=connection) as client:
        assert import_contributions(client, [Contribution(ROW)]) == 1
    assert "person_id" not in connection.writes[0]


def test_duplicates_are_skipped() -> None:
    connection = Connection(
        [{"id": "1", "first_name": "A.*", "last_name": "Person"}], [{"id": "old"}]
    )
    with BreezeApi("https://demo.breezechms.com", "synthetic-key", connection=connection) as client:
        assert import_contributions(client, [Contribution(ROW)]) == 0
    assert not connection.writes


def test_ambiguous_name_fails_without_writing() -> None:
    connection = Connection(
        [{"id": n, "first_name": "A.*", "last_name": "Person"} for n in ("1", "2")]
    )
    with (
        BreezeApi("https://demo.breezechms.com", "synthetic-key", connection=connection) as client,
        pytest.raises(BreezeError, match="Ambiguous"),
    ):
        import_contributions(client, [Contribution(ROW)])
    assert not connection.writes


def test_dry_run_without_requests() -> None:
    connection = Connection([])
    with BreezeApi(
        "https://demo.breezechms.com", "synthetic-key", connection=connection, dry_run=True
    ) as client:
        assert import_contributions(client, [Contribution(ROW)]) == 0
    assert connection.calls == 0


@pytest.mark.parametrize(
    "people", [{}, [None], [{"id": True, "first_name": "A", "last_name": "B"}]]
)
def test_invalid_people_fail_without_writing(people: object) -> None:
    connection = Connection(people)
    with (
        BreezeApi("https://demo.breezechms.com", "synthetic-key", connection=connection) as client,
        pytest.raises(BreezeError),
    ):
        import_contributions(client, [Contribution(ROW)])
    assert not connection.writes
