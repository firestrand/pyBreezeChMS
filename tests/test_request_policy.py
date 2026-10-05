"""R01 regressions reuse existing synthetic response/connection contracts."""

from collections.abc import Callable
from typing import cast

import pytest
import requests

from breeze.breeze import BreezeApi
from breeze.errors import (
    BreezeAuthenticationError,
    BreezeDeadlineError,
    BreezeError,
    BreezeRateLimitError,
    BreezeResponseError,
    BreezeTransportError,
)
from breeze.policy import RateLimiter
from tests.conftest import Clock
from tests.test_client_boundaries import KEY, URL, Connection, Response


@pytest.mark.parametrize("interval", [0, 1.75, 3.5])
def test_shared_pacing_applies_to_reads_and_writes(interval: float) -> None:
    clock = Clock()
    limiter = RateLimiter(interval=interval, clock=clock.now, sleep=clock.sleep)
    connection = Connection()
    with (
        BreezeApi(URL, KEY, connection=connection, rate_limiter=limiter) as first,
        BreezeApi(URL, KEY, connection=connection, rate_limiter=limiter) as second,
    ):
        first.get_people()
        second.assign_tag(1, 2)
        first.get_people()
    assert clock.waits == ([] if interval == 0 else [interval, interval])
    assert connection.calls == 3


def test_pacing_budget_expires_before_dispatch() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock.now, sleep=clock.sleep)
    connection = Connection()
    with BreezeApi(
        URL, KEY, connection=connection, rate_limiter=limiter, operation_timeout=1
    ) as client:
        client.get_people()
        with pytest.raises(BreezeDeadlineError):
            client.get_people()
    assert connection.calls == 1
    assert not clock.waits


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
@pytest.mark.parametrize("setting", ["request_timeout", "operation_timeout"])
def test_deadlines_require_finite_positive_values(value: float, setting: str) -> None:
    with pytest.raises(ValueError):
        BreezeApi(
            URL,
            KEY,
            connection=Connection(),
            request_timeout=value if setting == "request_timeout" else 60,
            operation_timeout=value if setting == "operation_timeout" else 60,
        )


@pytest.mark.parametrize("interval", [-1, float("nan"), float("inf")])
def test_pacing_intervals_require_finite_nonnegative_values(interval: float) -> None:
    with pytest.raises(ValueError):
        RateLimiter(interval=interval)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, float("nan"), float("inf")])
def test_response_limits_require_positive_integers(value: int | float) -> None:
    with pytest.raises(ValueError):
        BreezeApi(URL, KEY, connection=Connection(), max_response_bytes=cast(int, value))


@pytest.mark.parametrize(
    "status,category",
    [
        (401, BreezeAuthenticationError),
        (403, BreezeAuthenticationError),
        (429, BreezeRateLimitError),
    ],
)
def test_status_categories_remain_base_errors(status: int, category: type[BreezeError]) -> None:
    response = Response(b"{}", status)
    connection = Connection(response)
    with BreezeApi(URL, KEY, connection=connection) as client, pytest.raises(category) as caught:
        client.get_people()
    assert isinstance(caught.value, BreezeError)
    assert response.closed
    assert connection.calls == 1


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda client: client.add_person("A.*", "Person"), id="add-person"),
        pytest.param(lambda client: client.update_person(1, "[]"), id="update-person"),
        pytest.param(lambda client: client.add_event("event", 0), id="add-event"),
        pytest.param(lambda client: client.event_check_in(1, 2), id="check-in"),
        pytest.param(lambda client: client.event_check_out(1, 2), id="check-out"),
        pytest.param(lambda client: client.add_contribution(), id="add-contribution"),
        pytest.param(lambda client: client.edit_contribution(payment_id=1), id="edit-contribution"),
        pytest.param(lambda client: client.delete_contribution(1), id="delete-contribution"),
        pytest.param(lambda client: client.assign_tag(1, 2), id="assign-tag"),
        pytest.param(lambda client: client.unassign_tag(1, 2), id="unassign-tag"),
    ],
)
def test_mutation_timeout_is_never_replayed(
    mutation: Callable[[BreezeApi], object], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG", logger="breeze.breeze")
    connection = requests.Session()
    from unittest.mock import patch

    with (
        patch.object(connection, "get", side_effect=requests.Timeout("offline")) as request,
        BreezeApi(URL, KEY, connection=connection) as client,
        pytest.raises(BreezeTransportError),
    ):
        mutation(client)
    assert request.call_count == 1
    assert "outcome=transport count=1" in caplog.text
    assert "offline" not in caplog.text
    connection.close()


def test_invalid_json_category_and_cleanup(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG", logger="breeze.breeze")
    response = Response(b"html")
    with (
        BreezeApi(URL, KEY, connection=Connection(response)) as client,
        pytest.raises(BreezeResponseError),
    ):
        client.get_people()
    assert response.closed
    assert "outcome=response count=1" in caplog.text
    assert "html" not in caplog.text


def test_account_pacing_survives_short_lived_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    import gc

    from breeze.policy import account_limiter

    monkeypatch.setattr("breeze.policy._limiters", {})
    first = account_limiter("short-lived.breezechms.com", KEY)
    clock = Clock()
    first.clock = clock.now
    first.sleep = clock.sleep
    first.wait(60)
    del first
    gc.collect()
    account_limiter("short-lived.breezechms.com", KEY).wait(60)
    assert clock.waits == [3.5]


def test_stream_deadline_closes_response(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG", logger="breeze.breeze")
    from collections.abc import Iterator

    clock = Clock()

    class LateResponse(Response):
        def iter_content(
            self, chunk_size: int | None = 1, decode_unicode: bool = False
        ) -> Iterator[bytes]:
            clock.value += 2
            yield b"{}"

    response = LateResponse()
    limiter = RateLimiter(clock=clock.now, sleep=clock.sleep)
    with (
        BreezeApi(
            URL, KEY, connection=Connection(response), rate_limiter=limiter, operation_timeout=1
        ) as client,
        pytest.raises(BreezeDeadlineError),
    ):
        client.get_people()
    assert response.closed
    assert "outcome=deadline count=1" in caplog.text


def test_dry_run_consumes_no_pacing_slot() -> None:
    clock = Clock()
    limiter = RateLimiter(clock=clock.now, sleep=clock.sleep)
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection, rate_limiter=limiter, dry_run=True) as client:
        assert client.get_people() is None
        assert client.assign_tag(1, 2) is None
    with BreezeApi(URL, KEY, connection=connection, rate_limiter=limiter) as client:
        client.get_people()
    assert not clock.waits
    assert connection.calls == 1


@pytest.mark.parametrize(
    "status,outcome",
    [(200, "success"), (401, "authentication"), (429, "rate_limit"), (500, "http")],
)
def test_request_observation_is_bounded_and_private(
    status: int, outcome: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG", logger="breeze.breeze")
    with BreezeApi(URL, KEY, connection=Connection(Response(b"{}", status))) as client:
        if status == 200:
            client.assign_tag(1, 2)
        else:
            with pytest.raises(BreezeError):
                client.assign_tag(1, 2)
    events = [record.getMessage() for record in caplog.records if "outcome=" in record.getMessage()]
    assert len(events) == 1
    assert f"outcome={outcome} count=1 elapsed_seconds=" in events[0]
    assert KEY not in caplog.text
    assert URL not in caplog.text
    assert "person_id" not in caplog.text
    assert "tag_id" not in caplog.text


def test_dry_run_has_no_request_observation(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG", logger="breeze.breeze")
    with BreezeApi(URL, KEY, connection=Connection(), dry_run=True) as client:
        client.assign_tag(1, 2)
    assert not caplog.records
