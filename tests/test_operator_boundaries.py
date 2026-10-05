"""Local trust-boundary regressions; no credentials or live provider access."""

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from breeze.cli import load_decisions
from breeze.importing import ImportValidationError, Snapshot, plan_import
from breeze.journal import Journal, apply_plan, inspect_journal
from breeze.models import FundAllocation, Person
from breeze.storage import read_json
from tests.test_import_workflow import Gateway, policy, record


@pytest.mark.parametrize(
    "payload",
    [
        '{"1":{"action":"skip"},"1":{"action":"create"}}',
        '{"1":{"action":"skip","action":"create"}}',
        '{"currency":"USD","precision":2,"precision":0}',
        '{"nested":{"amount":NaN}}',
    ],
)
def test_ambiguous_or_nonfinite_operator_json_is_rejected(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "operator.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ImportValidationError):
        read_json(str(path))


@pytest.mark.parametrize("ordinal", ["01", "+1", " 1", "1.0", "0", "100001"])
def test_review_ordinals_cannot_alias_or_exceed_source_rows(tmp_path: Path, ordinal: str) -> None:
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps({ordinal: {"action": "skip"}}), encoding="utf-8")
    with pytest.raises(ImportValidationError):
        load_decisions(path)


def test_credential_reader_rejects_nonregular_files_without_blocking(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    os.mkfifo(path, 0o600)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from breeze.configuration import breeze_credentials; breeze_credentials(sys.argv[1])",
            str(path),
        ],
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 1
    assert b"regular" in result.stderr


@pytest.mark.parametrize("change", ["account", "currency", "funds", "people"])
def test_changed_destination_refuses_apply_before_submission(tmp_path: Path, change: str) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    if change == "account":
        gateway.account_id = "another-account"
    elif change == "people":
        gateway.records = ()
    with (
        patch.object(
            gateway, "account_currency", return_value="EUR" if change == "currency" else "USD"
        ),
        patch.object(gateway, "fund_ids", return_value=set() if change == "funds" else {"5"}),
        Journal(tmp_path / "journal.sqlite", plan, retention_days=30) as journal,
        pytest.raises(ImportValidationError),
    ):
        try:
            apply_plan(plan, gateway, journal)
        finally:
            assert journal.states() == {1: "planned"}
            assert not gateway.writes


def test_retention_expiry_during_open_run_stops_dispatch(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    with (
        patch("breeze.journal.time.time", return_value=1000) as clock,
        Journal(tmp_path / "journal.sqlite", plan, retention_days=1) as journal,
    ):
        clock.return_value = 1000 + 86401
        with pytest.raises(ImportValidationError, match="retention"):
            apply_plan(plan, gateway, journal)
        assert journal.states() == {1: "planned"}
    assert not gateway.writes


@pytest.mark.parametrize("value", [None, "12.34", 12.34, True])
def test_typed_funds_reject_nondecimal_amounts(value: object) -> None:
    with pytest.raises(ValueError, match="exact decimal"):
        FundAllocation("general", cast(Decimal, value))


@pytest.mark.parametrize("identifier", [None, True, "", " "])
def test_direct_person_records_preserve_validation(identifier: object) -> None:
    from breeze.errors import BreezeResponseError

    with pytest.raises(BreezeResponseError):
        Person(cast(str, identifier), "Test", "Donor")


@pytest.mark.parametrize(
    "start,end",
    [
        (None, None),
        ("20261001", "2026-10-03"),
        ("2026-W40-4", "2026-10-03"),
        ("2026-10-04", "2026-10-03"),
        ("2026-99-01", "2026-10-03"),
    ],
)
def test_invalid_export_window_is_rejected_before_provider_access(
    tmp_path: Path, start: str | None, end: str | None
) -> None:
    from breeze import cli

    arguments = ["export", "contributions", "--output", str(tmp_path / "export.jsonl")]
    if start is not None:
        arguments += ["--start", start]
    if end is not None:
        arguments += ["--end", end]
    with patch.object(cli, "breeze_credentials", side_effect=AssertionError("No provider access")):
        assert cli.main(arguments) == 1
    assert not (tmp_path / "export.jsonl").exists()


def test_library_export_selection_checks_window_and_preserves_valid_parameters() -> None:
    from breeze.breeze import BreezeApi
    from breeze.exporting import breeze_records
    from tests.test_client_boundaries import KEY, URL, Connection

    with (
        BreezeApi(URL, KEY, connection=Connection()) as client,
        patch.object(client, "list_contributions", return_value=[]) as read,
    ):
        with pytest.raises(ImportValidationError):
            list(breeze_records(client, "contributions", start="20261001", end="2026-10-03"))
        read.assert_not_called()
        assert (
            list(breeze_records(client, "contributions", start="2026-10-01", end="2026-10-03"))
            == []
        )
        read.assert_called_once_with(start_date="2026-10-01", end_date="2026-10-03")


def test_explicit_anonymous_write_cannot_trigger_server_donor_matching() -> None:
    from urllib.parse import parse_qs, urlsplit

    from breeze.breeze import BreezeApi
    from breeze.importing import Action, BreezeImportGateway, ReviewDecision
    from tests.test_client_boundaries import KEY, URL, Connection, Response

    plan = plan_import(
        Snapshot((record("Unknown"),), "a" * 64),
        policy(),
        Gateway(),
        {1: ReviewDecision(Action.CREATE, anonymous=True)},
    )
    connection = Connection(Response(b'{"payment_id":"synthetic-receipt"}'))
    with BreezeApi(URL, KEY, connection=connection) as client:
        assert BreezeImportGateway(client).create(plan.entries[0]) == "synthetic-receipt"
    parameters = parse_qs(urlsplit(connection.url).query)
    assert not {"name", "uid", "person_id"} & parameters.keys()
    assert parameters["method"] == ["Cash"]
    assert parameters["amount"] == ["12.34"]
    assert json.loads(parameters["funds_json"][0]) == [{"name": "", "amount": "12.34", "id": "5"}]


@pytest.mark.parametrize("anonymous,reason", [(True, "unique_match"), (False, "donor_review")])
def test_plan_cannot_disguise_an_unreviewed_decision_as_create(
    anonymous: bool, reason: str
) -> None:
    from breeze.importing import Action, PlanEntry

    with pytest.raises(ImportValidationError):
        PlanEntry(
            1, record(), "5", None if anonymous else "1", anonymous, False, Action.CREATE, reason
        )


@pytest.mark.parametrize("existing", [False, True])
def test_recovery_cannot_initialize_a_new_journal(tmp_path: Path, existing: bool) -> None:
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), Gateway())
    path = tmp_path / "journal.sqlite"
    if existing:
        path.touch(mode=0o600)
    with (
        pytest.raises((ImportValidationError, FileNotFoundError)),
        Journal(path, plan, retention_days=30, recovery_only=True),
    ):
        pass
    assert path.exists() == existing
    if existing:
        assert path.stat().st_size == 0


@pytest.mark.parametrize("receipt", [None, False, "", " ", "x" * 257])
def test_invalid_receipt_leaves_uncertainty_and_never_replays(
    tmp_path: Path, receipt: object
) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path = tmp_path / "journal.sqlite"
    with (
        patch.object(gateway, "create", return_value=cast(str, receipt)) as create,
        Journal(path, plan, retention_days=30) as journal,
    ):
        with pytest.raises(ImportValidationError):
            apply_plan(plan, gateway, journal)
        with pytest.raises(ImportValidationError):
            apply_plan(plan, gateway, journal)
    assert create.call_count == 1
    assert inspect_journal(str(path)) == {"uncertain": 1}


@pytest.mark.parametrize("decision", ["received", "skip"])
def test_expired_reconciliation_keeps_audit_and_never_dispatches(
    tmp_path: Path, decision: str
) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path = tmp_path / "journal.sqlite"
    with (
        patch("breeze.journal.time.time", return_value=1000),
        Journal(path, plan, retention_days=1) as journal,
    ):
        journal.submit(1)
    with (
        patch("breeze.journal.time.time", return_value=1000 + 86401),
        Journal(path, plan, retention_days=1, recovery_only=True) as journal,
    ):
        journal.reconcile(1, decision, "verified-receipt" if decision == "received" else None)
        assert apply_plan(plan, gateway, journal) == 0
        assert journal.db.execute("SELECT count(*) FROM audit").fetchone() == (4,)
        with pytest.raises(ImportValidationError, match="Recovery-only"):
            journal.submit(1)
    assert not gateway.writes
