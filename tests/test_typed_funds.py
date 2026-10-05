"""Typed serialization using existing contribution fixtures only."""

import json
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest

from breeze.breeze import BreezeApi
from breeze.errors import BreezeResponseError
from breeze.models import FundAllocation
from tests.fixtures import ROW
from tests.test_client_boundaries import KEY, URL, Connection, Response


def test_structured_funds_keep_decimal_precision_and_quotes() -> None:
    # Amount/fund and payment ID already occur in baseline contribution tests.
    allocation = FundAllocation(ROW["Fund"], Decimal("1000.25"))
    connection = Connection(Response(b'{"payment_id":"12345"}'))
    with BreezeApi(URL, KEY, connection=connection) as client:
        result = client.add_allocated_contribution([allocation], date="2026-10-01")
    assert result == "12345"
    params = parse_qs(urlsplit(connection.url).query)
    assert params["amount"] == ["1000.25"]
    assert json.loads(params["funds_json"][0]) == [{"name": ROW["Fund"], "amount": "1000.25"}]


@pytest.mark.parametrize(
    "content",
    [
        b"[]",
        b'{"payment_id":true}',
        b'{"success":true}',
        b'{"payment_id":""}',
        b'{"payment_id":" "}',
    ],
)
def test_typed_write_rejects_existing_malformed_payment_fixtures(content: bytes) -> None:
    allocation = FundAllocation(ROW["Fund"], Decimal("1000.25"))
    response = Response(content)
    connection = Connection(response)
    with (
        BreezeApi(URL, KEY, connection=connection) as client,
        pytest.raises(BreezeResponseError),
    ):
        client.add_allocated_contribution([allocation], date="2026-10-01")
    assert connection.calls == 1
    assert response.closed


def test_empty_allocations_fail_before_write() -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection) as client, pytest.raises(ValueError):
        client.add_allocated_contribution([], date="2026-10-01")
    assert connection.calls == 0


def test_exact_total_exceeds_default_decimal_context_without_rounding() -> None:
    allocations = [
        FundAllocation("synthetic", Decimal("123456789012345678901234567890.12")),
        FundAllocation("synthetic", Decimal("0.01")),
    ]
    connection = Connection(Response(b'{"payment_id":"synthetic-receipt"}'))
    with BreezeApi(URL, KEY, connection=connection) as client:
        client.add_allocated_contribution(allocations, date="2026-10-01")
    params = parse_qs(urlsplit(connection.url).query)
    assert params["amount"] == ["123456789012345678901234567890.13"]


def test_excessive_fund_iterable_is_bounded_before_any_write() -> None:
    allocation = FundAllocation("synthetic", Decimal("1.00"))
    connection = Connection()
    with (
        BreezeApi(URL, KEY, connection=connection) as client,
        pytest.raises(ValueError, match="limit"),
    ):
        client.add_allocated_contribution((allocation for _ in range(1001)), date="2026-10-01")
    assert connection.calls == 0
