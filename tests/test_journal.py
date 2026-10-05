"""Crash/restart evidence for the approved single-writer local journal."""

import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from breeze.importing import (
    Action,
    ImportValidationError,
    PlanEntry,
    ReviewDecision,
    Snapshot,
    plan_import,
)
from breeze.interchange import save_plan
from breeze.journal import Journal, apply_plan, export_journal, inspect_journal
from tests.test_import_workflow import Gateway, policy, record


def test_restart_preserves_acknowledged_rows(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path = tmp_path / "journal.sqlite"
    with Journal(path, plan, retention_days=30) as journal:
        assert apply_plan(plan, gateway, journal) == 1
    with Journal(path, plan, retention_days=30) as journal:
        assert apply_plan(plan, gateway, journal) == 0
        assert journal.states() == {1: "acknowledged"}
    assert len(gateway.writes) == 1


def test_crash_after_submission_never_automatically_resends(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    with Journal(tmp_path / "journal.sqlite", plan, retention_days=30) as journal:
        journal.submit(1)
    with Journal(tmp_path / "journal.sqlite", plan, retention_days=30) as journal:
        assert journal.states() == {1: "uncertain"}
        with pytest.raises(ImportValidationError, match="reconciliation"):
            apply_plan(plan, gateway, journal)
        journal.reconcile(1, "not_applied")
        assert apply_plan(plan, gateway, journal) == 1
    assert len(gateway.writes) == 1


def test_corruption_stops_apply(tmp_path: Path) -> None:
    path = tmp_path / "journal.sqlite"
    path.write_bytes(b"not SQLite")
    path.chmod(0o600)
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    with (
        pytest.raises(ImportValidationError, match="journal"),
        Journal(path, plan, retention_days=30),
    ):
        pass
    assert not gateway.writes


def test_single_writer_and_private_permissions(tmp_path: Path) -> None:
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), Gateway())
    path = tmp_path / "journal.sqlite"
    with (
        Journal(path, plan, retention_days=30),
        pytest.raises(ImportValidationError, match="writer"),
        Journal(path, plan, retention_days=30),
    ):
        pass
    assert path.stat().st_mode & 0o777 == 0o600


def test_unresolved_final_row_means_zero_writes(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(), record("Unknown")), "a" * 64), policy(), gateway)
    with (
        Journal(tmp_path / "journal.sqlite", plan, retention_days=30) as journal,
        pytest.raises(ImportValidationError, match="unresolved"),
    ):
        apply_plan(plan, gateway, journal)
    assert not gateway.writes


def test_identical_reviewed_gifts_remain_distinct(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(
        Snapshot((record(), record()), "a" * 64),
        policy(),
        gateway,
        {1: ReviewDecision(Action.CREATE), 2: ReviewDecision(Action.CREATE)},
    )
    with Journal(tmp_path / "journal.sqlite", plan, retention_days=30) as journal:
        assert apply_plan(plan, gateway, journal) == 2
    assert len(gateway.writes) == 2


@pytest.mark.parametrize(
    "boundary", ["before_submit", "after_submit", "after_write", "before_ack", "after_ack"]
)
def test_crash_at_each_boundary_is_conservative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path = tmp_path / "journal.sqlite"
    with Journal(path, plan, retention_days=30) as journal:
        submit, acknowledge, create = journal.submit, journal.acknowledge, gateway.create

        def crash_submit(row: int) -> None:
            if boundary == "before_submit":
                raise KeyboardInterrupt
            submit(row)
            if boundary == "after_submit":
                raise KeyboardInterrupt

        def crash_create(entry: PlanEntry) -> str:
            receipt = create(entry)
            if boundary == "after_write":
                raise KeyboardInterrupt
            return receipt

        def crash_ack(row: int, receipt: str) -> None:
            if boundary == "before_ack":
                raise KeyboardInterrupt
            acknowledge(row, receipt)
            if boundary == "after_ack":
                raise KeyboardInterrupt

        with monkeypatch.context() as changes:
            changes.setattr(journal, "submit", crash_submit)
            changes.setattr(gateway, "create", crash_create)
            changes.setattr(journal, "acknowledge", crash_ack)
            with pytest.raises(KeyboardInterrupt):
                apply_plan(plan, gateway, journal)
    written = len(gateway.writes)
    with Journal(path, plan, retention_days=30) as journal:
        if boundary == "before_submit":
            assert apply_plan(plan, gateway, journal) == 1
        elif boundary == "after_ack":
            assert apply_plan(plan, gateway, journal) == 0
        else:
            assert journal.states() == {1: "uncertain"}
            with pytest.raises(ImportValidationError, match="reconciliation"):
                apply_plan(plan, gateway, journal)
            assert len(gateway.writes) == written


def test_expired_journal_blocks_apply_but_keeps_readonly_recovery(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path, export = tmp_path / "journal.sqlite", tmp_path / "recovery.jsonl"
    with (
        patch("breeze.journal.time.time", return_value=1000),
        Journal(path, plan, retention_days=1) as journal,
    ):
        journal.submit(1)
    with (
        patch("breeze.journal.time.time", return_value=1000 + 86401),
        pytest.raises(ImportValidationError, match="retention"),
        Journal(path, plan, retention_days=1),
    ):
        pass
    assert inspect_journal(path) == {"submitted": 1}
    assert export_journal(path, export) >= 3
    content = export.read_text()
    assert "12.34" not in content
    assert "Test Donor" not in content
    assert export.stat().st_mode & 0o777 == 0o600
    assert not gateway.writes


def test_logical_journal_corruption_is_not_silent_acknowledgement(tmp_path: Path) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    path = tmp_path / "journal.sqlite"
    with Journal(path, plan, retention_days=30):
        pass
    connection = sqlite3.connect(path)
    with connection:
        connection.execute("UPDATE progress SET state='acknowledged',receipt='receipt'")
    connection.close()
    with (
        pytest.raises(ImportValidationError, match="audit"),
        Journal(path, plan, retention_days=30),
    ):
        pass
    assert not gateway.writes


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit"])
def test_hard_process_exit_recovers_transaction_and_releases_writer_lock(
    tmp_path: Path, boundary: str
) -> None:
    gateway = Gateway()
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    plan_path, journal_path = tmp_path / "plan.json", tmp_path / "journal.sqlite"
    save_plan(plan_path, plan)
    script = """
import os
import sys
from pathlib import Path
from breeze.interchange import load_plan
from breeze.journal import Journal
plan = load_plan(Path(sys.argv[1]))
with Journal(Path(sys.argv[2]), plan, retention_days=30) as journal:
    if sys.argv[3] == 'before_commit':
        journal.db.execute('BEGIN IMMEDIATE')
        journal.db.execute("UPDATE progress SET state='submitted' WHERE row=1")
    else:
        journal.submit(1)
    os._exit(17)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(plan_path), str(journal_path), boundary],
        timeout=10,
        capture_output=True,
    )
    assert result.returncode == 17
    with Journal(journal_path, plan, retention_days=30) as journal:
        if boundary == "before_commit":
            assert journal.states() == {1: "planned"}
            assert apply_plan(plan, gateway, journal) == 1
        else:
            assert journal.states() == {1: "uncertain"}
            with pytest.raises(ImportValidationError, match="reconciliation"):
                apply_plan(plan, gateway, journal)
            assert not gateway.writes
