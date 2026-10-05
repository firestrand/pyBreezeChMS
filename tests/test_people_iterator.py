"""R05 pagination regressions using the existing importer fixture records."""

from unittest.mock import patch

import pytest

from breeze.breeze import BreezeApi
from breeze.errors import BreezeResponseError
from tests.fixtures import MATCHED_PEOPLE, OTHER_PEOPLE
from tests.test_client_boundaries import KEY, URL, Connection


def test_full_pages_then_empty_preserve_people() -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(client, "get_people", side_effect=[MATCHED_PEOPLE, OTHER_PEOPLE, []]) as get,
    ):
        people = list(client.iter_people(page_size=1))
    assert [person.id for person in people] == ["1", "2"]
    assert [call.kwargs["offset"] for call in get.call_args_list] == [0, 1, 2]


def test_partial_page_terminates() -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(client, "get_people", return_value=MATCHED_PEOPLE) as get,
    ):
        assert len(list(client.iter_people(page_size=2))) == 1
    assert get.call_count == 1


def test_repeated_page_is_not_silent_partial_success() -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(client, "get_people", side_effect=[MATCHED_PEOPLE, MATCHED_PEOPLE]),
        pytest.raises(BreezeResponseError, match="repeated"),
    ):
        list(client.iter_people(page_size=1))


@pytest.mark.parametrize("limits", [{"max_pages": 1}, {"max_items": 1}])
def test_limits_raise_instead_of_pretending_index_complete(limits: dict[str, int]) -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(client, "get_people", side_effect=[MATCHED_PEOPLE, OTHER_PEOPLE]),
        pytest.raises(BreezeResponseError, match="limit"),
    ):
        list(
            client.iter_people(
                page_size=1,
                max_pages=limits.get("max_pages", 1000),
                max_items=limits.get("max_items", 100_000),
            )
        )


@pytest.mark.parametrize("value", [0, -1])
def test_page_size_requires_positive_value(value: int) -> None:
    with BreezeApi(URL, KEY, connection=Connection()) as client, pytest.raises(ValueError):
        list(client.iter_people(page_size=value))


def test_dry_run_preserves_no_request_behavior() -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection, dry_run=True) as client:
        assert list(client.iter_people()) == []
    assert connection.calls == 0


def test_malformed_response_is_rejected() -> None:
    # Empty object is an existing successful raw response fixture, not a people list.
    with BreezeApi(URL, KEY, connection=Connection()) as client, pytest.raises(BreezeResponseError):
        list(client.iter_people())


def test_later_failure_is_not_a_successful_complete_index() -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(
            client, "get_people", side_effect=[MATCHED_PEOPLE, BreezeResponseError("page failed")]
        ),
        pytest.raises(BreezeResponseError, match="page failed"),
    ):
        list(client.iter_people(page_size=1))


def test_numeric_and_text_ids_cannot_hide_a_repeated_person() -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(
            client,
            "get_people",
            side_effect=[
                [{"id": 1, "first_name": "Test", "last_name": "Donor"}],
                [{"id": "1", "first_name": "Test", "last_name": "Donor"}],
            ],
        ),
        pytest.raises(BreezeResponseError, match="repeated"),
    ):
        list(client.iter_people_records(page_size=1))
