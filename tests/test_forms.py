"""Published forms endpoint parameters, independent offline response contracts."""

from urllib.parse import parse_qs, urlsplit

import pytest

from breeze.breeze import BreezeApi
from breeze.errors import BreezeAuthenticationError
from breeze.policy import RateLimiter
from tests.conftest import Clock
from tests.test_client_boundaries import KEY, URL, Connection, Response


@pytest.mark.parametrize("content", [b"[]", b'[{"id":"123","name":"Synthetic"}]'])
def test_forms_success_empty_and_safe_field_identifier(content: bytes) -> None:
    connection = Connection(Response(content))
    with BreezeApi(URL, KEY, connection=connection) as client:
        assert isinstance(client.list_forms(), list)
        assert urlsplit(connection.url).path == "/api/forms/list_forms"
        assert parse_qs(urlsplit(connection.url).query) == {"is_archived": ["0"]}
        assert isinstance(client.list_form_fields("1&details=1"), list)
        assert parse_qs(urlsplit(connection.url).query) == {"form_id": ["1&details=1"]}


def test_forms_calls_share_pacing_and_auth_cleanup() -> None:
    clock = Clock()
    response = Response(b"[]", 401)
    connection = Connection(response)
    with BreezeApi(
        URL,
        KEY,
        connection=connection,
        rate_limiter=RateLimiter(clock=clock.now, sleep=clock.sleep),
    ) as client:
        with pytest.raises(BreezeAuthenticationError):
            client.list_forms()
        with pytest.raises(BreezeAuthenticationError):
            client.list_form_fields("123")
    assert clock.waits == [3.5]
    assert response.closed
    assert connection.calls == 2


def test_executable_forms_example_reports_only_counts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import runpy
    from pathlib import Path
    from unittest.mock import patch

    example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/forms.py"))
    main = example["main"]

    monkeypatch.setenv("BREEZE_URL", URL)
    monkeypatch.setenv("BREEZE_API_KEY", KEY)
    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.dict(
            main.__globals__,
            BreezeApi=lambda *args: client,
            breeze_credentials=lambda path: (URL, KEY),
        ),
        patch.object(client, "list_forms", return_value=[{"id": "123", "name": "Private name"}]),
        patch.object(client, "list_form_fields", return_value=[{"id": "1"}]) as fields,
        patch.object(client, "list_form_entries", return_value=[{"id": "2"}]) as entries,
    ):
        assert main() == 0
        fields.assert_called_once_with("123")
        entries.assert_called_once_with("123")
    assert capsys.readouterr().out.strip() == '{"entries": 1, "fields": 1, "forms": 1}'
