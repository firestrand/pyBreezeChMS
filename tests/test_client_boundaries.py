"""Offline contract tests using real Requests serialization and response objects."""

import json
import logging
from collections.abc import Iterator, Mapping
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
import requests

from breeze.breeze import BreezeApi, BreezeError, HttpResponse
from breeze.utils import make_enum

URL = "https://demo.breezechms.com"
KEY = "synthetic-test-key"


class Response(requests.Response):
    def __init__(self, content: bytes = b"{}", status: int = 200) -> None:
        super().__init__()
        self._content = content
        self._content_consumed = True
        self.status_code = status
        self.closed = False

    def close(self) -> None:
        self.closed = True
        super().close()


class Connection:
    def __init__(self, response: HttpResponse | None = None) -> None:
        self.response = Response() if response is None else response
        self.url = ""
        self.headers: Mapping[str, str] = {}
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
        assert verify and stream and not allow_redirects and timeout > 0
        self.calls += 1
        prepared = requests.Request("GET", url, params=params).prepare()
        assert prepared.url is not None
        self.url = prepared.url
        self.headers = headers
        return self.response


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example",
        "https://demo.breezechms.com.evil.example",
        "https://demo.breezechms.com@evil.example",
        "https://user@demo.breezechms.com",
        "https://breezechms.com",
        "https://demo.breezechms.com/path",
        "https://demo.breezechms.com?key=value",
        "https://demo.breezechms.com#fragment",
        "https://demo.breezechms.com:444",
        "https://demo.breezechms.com:invalid",
        "http://demo.breezechms.com",
        "https://.breezechms.com",
    ],
)
def test_url_validation(url: str) -> None:
    with pytest.raises(BreezeError):
        BreezeApi(url, KEY)


@pytest.mark.parametrize("key", ["", " ", "key\r\nOther: value"])
def test_key_validation(key: str) -> None:
    with pytest.raises(BreezeError):
        BreezeApi(URL, key)


def test_independent_sessions_and_cleanup() -> None:
    with BreezeApi(URL, KEY) as first, BreezeApi(URL + "/", KEY) as second:
        assert first.connection is not second.connection
        assert second.breeze_url == URL
        with patch.object(first.connection, "close") as close:
            first.close()
            close.assert_called_once()


def test_injected_transport_is_caller_owned() -> None:
    connection = requests.Session()
    with patch.object(connection, "close") as close:
        with BreezeApi(URL, KEY, connection=connection):
            pass
        close.assert_not_called()
    connection.close()


@pytest.mark.parametrize("status", [301, 302, 400, 401, 429, 500])
def test_http_failure_and_redirects_close_response(status: int) -> None:
    response = Response(b"{}", status)
    connection = Connection(response)
    with (
        BreezeApi(URL, KEY, connection=connection) as client,
        pytest.raises(BreezeError, match=f"HTTP {status}"),
    ):
        client.get_people()
    assert response.closed
    assert connection.calls == 1


@pytest.mark.parametrize(
    "error", [requests.ConnectionError("offline"), requests.Timeout("timeout")]
)
def test_transport_error_preserves_cause(error: requests.RequestException) -> None:
    connection = requests.Session()
    with (
        patch.object(connection, "get", side_effect=error),
        BreezeApi(URL, KEY, connection=connection) as client,
        pytest.raises(BreezeError, match="connection failed") as caught,
    ):
        client.get_people()
    assert caught.value.__cause__ is error
    connection.close()


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"html",
        b"null",
        b"42",
        b'"text"',
        b"false",
        b'{"errors":"private"}',
        b'{"errorCode":123}',
        b'{"nested": [NaN]}',
        b'"\xff"',
    ],
)
def test_invalid_or_failed_response_is_sanitized(content: bytes) -> None:
    response = Response(content)
    with (
        BreezeApi(URL, KEY, connection=Connection(response)) as client,
        pytest.raises(BreezeError) as caught,
    ):
        client.get_people()
    assert "private" not in str(caught.value)
    assert response.closed


@pytest.mark.parametrize("content", [b"[]", b"{}", b"true", b'{"nested":[null,1,1.5,"x"]}'])
def test_successful_json(content: bytes) -> None:
    response = Response(content)
    with BreezeApi(URL, KEY, connection=Connection(response)) as client:
        assert client.get_people() == json.loads(content)
    assert response.closed


def test_response_limit_and_cleanup() -> None:
    response = Response(b'{"name":"too large"}')
    with (
        BreezeApi(URL, KEY, connection=Connection(response), max_response_bytes=4) as client,
        pytest.raises(BreezeError, match="size limit"),
    ):
        client.get_people()
    assert response.closed


def test_stream_failure_and_cleanup() -> None:
    class BrokenResponse(Response):
        def iter_content(
            self, chunk_size: int | None = 1, decode_unicode: bool = False
        ) -> Iterator[bytes]:
            yield b"{"
            raise requests.ConnectionError("stream broke")

    response = BrokenResponse()
    with (
        BreezeApi(URL, KEY, connection=Connection(response)) as client,
        pytest.raises(BreezeError, match="read Breeze response") as caught,
    ):
        client.get_people()
    assert isinstance(caught.value.__cause__, requests.ConnectionError)
    assert response.closed


def test_query_values_round_trip_and_do_not_inject_parameters() -> None:
    connection = Connection()
    name = "A & admin=true # + café"
    fields = '[{"response":"x&person_id=999"}]'
    with BreezeApi(URL, KEY, connection=connection) as client:
        client.add_person(name, "Last/Name?", fields)
    assert parse_qs(urlsplit(connection.url).query) == {
        "first": [name],
        "last": ["Last/Name?"],
        "fields_json": [fields],
    }


def test_zero_values_and_false_all_day_are_sent() -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection) as client:
        client.get_people(limit=0, offset=0)
        assert parse_qs(urlsplit(connection.url).query) == {"limit": ["0"], "offset": ["0"]}
        client.add_event("event", 0, end_date=0, all_day=False)
        assert parse_qs(urlsplit(connection.url).query) == {
            "name": ["event"],
            "starts_on": ["0"],
            "ends_on": ["0"],
            "all_day": ["0"],
        }


def test_no_personal_data_or_credentials_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    connection = Connection(Response(b'{"name":"sensitive-contact"}'))
    with (
        caplog.at_level(logging.DEBUG, logger="breeze.breeze"),
        BreezeApi(URL, KEY, connection=connection) as client,
    ):
        client.add_person("sensitive-contact", "Last")
    assert KEY not in caplog.text
    assert "sensitive-contact" not in caplog.text


def test_headers_remain_unchanged() -> None:
    headers = {"Additional-Header": "value"}
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection) as client:
        client._request("/api/people", headers=headers)
    assert headers == {"Additional-Header": "value"}
    assert connection.headers["Api-Key"] == KEY


def test_dry_run_makes_no_requests_including_payment_methods() -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, dry_run=True, connection=connection) as client:
        assert client.get_people() is None
        assert client.add_contribution() is None
        assert client.edit_contribution(payment_id=1) is None
        assert client.delete_contribution(1) is None
    assert connection.calls == 0


@pytest.mark.parametrize("content", [b"[]", b'{"payment_id":true}', b'{"success":true}'])
def test_payment_response_validation(content: bytes) -> None:
    with (
        BreezeApi(URL, KEY, connection=Connection(Response(content))) as client,
        pytest.raises(BreezeError, match="payment"),
    ):
        client.add_contribution()


def test_enum_does_not_mutate_methods() -> None:
    def label(cls: type) -> str:
        return cls.__name__

    methods = {"label": label}
    enum = make_enum("Example", methods=methods, ITEM="value")
    assert methods == {"label": label}
    namespace = vars(enum)
    assert namespace["label"].__get__(None, enum)() == "Example"
    assert namespace["ITEM"] == "value"
    with pytest.raises(RuntimeError):
        enum()


@pytest.mark.parametrize("payload", ["bad", "{}", "[1]", '[{"value":NaN}]'])
def test_json_parameters_fail_before_writes(payload: str) -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection) as client:
        for operation in (
            lambda: client.update_person(1, payload),
            lambda: client.add_person("first", "last", payload),
            lambda: client.add_contribution(funds_json=payload),
            lambda: client.edit_contribution(1, funds_json=payload),
        ):
            with pytest.raises(BreezeError):
                operation()
    assert connection.calls == 0


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_timeouts(timeout: float) -> None:
    with BreezeApi(URL, KEY, connection=Connection()) as client, pytest.raises(ValueError):
        client._request("/api/people", timeout=timeout)


def test_bounds_and_person_path() -> None:
    connection = Connection()
    with BreezeApi(URL, KEY, connection=connection) as client:
        with pytest.raises(ValueError):
            client.get_people(limit=-1)
        with pytest.raises(ValueError):
            client.get_people(offset=-1)
        with pytest.raises(BreezeError):
            client.get_person_details("..")
        with pytest.raises(BreezeError, match="URL limit"):
            client.add_person("x" * 65536, "last")
        client.get_person_details("1?admin=true")
        assert urlsplit(connection.url).query == ""
        assert urlsplit(connection.url).path == "/api/people/1%3Fadmin%3Dtrue"
    assert connection.calls == 1
