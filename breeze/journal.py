"""One POSIX writer, durable submission boundaries, and explicit reconciliation."""

import hashlib
import math
import os
import sqlite3
import stat
import time
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

from .breeze import JsonValue
from .importing import Action, ImportGateway, ImportPlan, ImportValidationError

STATES = frozenset({"planned", "submitted", "acknowledged", "uncertain", "skipped"})


class Journal:
    def __init__(
        self,
        path: Path | str,
        plan: ImportPlan,
        *,
        retention_days: int,
        recovery_only: bool = False,
    ) -> None:
        if (
            isinstance(retention_days, bool)
            or not isinstance(retention_days, int)
            or not 1 <= retention_days <= 36500
        ):
            raise ImportValidationError("Declare journal retention days between 1 and 36500.")
        self.path, self.plan, self.retention_days = Path(path), plan, retention_days
        self.recovery_only = recovery_only
        self._connection: sqlite3.Connection | None = None
        self._lock: int | None = None

    @property
    def db(self) -> sqlite3.Connection:
        if self._connection is None:
            raise ImportValidationError("Journal is not open.")
        return self._connection

    def __enter__(self) -> Journal:
        if os.name != "posix":
            raise ImportValidationError("Journal apply requires a POSIX local filesystem worker.")
        import fcntl

        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            parent = self.path.parent.stat()
            if (
                self.path.parent.is_symlink()
                or parent.st_uid != os.getuid()
                or parent.st_mode & 0o077
            ):
                raise ImportValidationError("Journal requires a private owned directory.")
            self._lock = os.open(
                self.path.with_suffix(self.path.suffix + ".lock"),
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
                0o600,
            )
            try:
                fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ImportValidationError("Another journal writer is active.") from error
            flags = os.O_RDWR | os.O_NOFOLLOW
            if not self.recovery_only:
                flags |= os.O_CREAT
            descriptor = os.open(self.path, flags, 0o600)
            try:
                info = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_mode & 0o077
                    or info.st_nlink != 1
                ):
                    raise ImportValidationError("Journal requires a private owned regular file.")
            finally:
                os.close(descriptor)
            self._connection = sqlite3.connect(self.path, timeout=0, isolation_level=None)
            self.db.execute("PRAGMA synchronous=FULL")
            if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ImportValidationError("Corrupt journal; reconciliation required.")
            self._prepare()
            return self
        except BaseException as error:
            # Lifecycle boundary must release writer ownership even on cancellation.
            self.close()
            if isinstance(error, sqlite3.Error):
                raise ImportValidationError(
                    "Invalid or corrupt journal; reconciliation required."
                ) from error
            raise

    def close(self) -> None:
        try:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
        finally:
            if self._lock is not None:
                os.close(self._lock)
                self._lock = None

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _prepare(self) -> None:
        account = hashlib.sha256(self.plan.account_id.encode()).hexdigest()
        exists = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if not exists:
            if self.recovery_only:
                raise ImportValidationError("Recovery requires an existing initialized journal.")
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute(
                    "CREATE TABLE meta (version INTEGER, plan TEXT, snapshot TEXT, account TEXT, created REAL, expires REAL, retention INTEGER, rows INTEGER)"
                )
                self.db.execute(
                    "CREATE TABLE progress (row INTEGER PRIMARY KEY, state TEXT NOT NULL CHECK(state IN ('planned','submitted','acknowledged','uncertain','skipped')), receipt TEXT)"
                )
                self.db.execute(
                    "CREATE TABLE audit (sequence INTEGER PRIMARY KEY, row INTEGER, time REAL, state TEXT, reason TEXT)"
                )
                self.db.execute("CREATE INDEX audit_row ON audit(row,sequence)")
                now = time.time()
                self.db.execute(
                    "INSERT INTO meta VALUES (?,?,?,?,?,?,?,?)",
                    (
                        1,
                        self.plan.digest,
                        self.plan.snapshot_digest,
                        account,
                        now,
                        now + self.retention_days * 86400,
                        self.retention_days,
                        len(self.plan.entries),
                    ),
                )
                for entry in self.plan.entries:
                    state = "skipped" if entry.action == Action.SKIP else "planned"
                    self.db.execute("INSERT INTO progress VALUES (?,?,NULL)", (entry.row, state))
                    self.db.execute(
                        "INSERT INTO audit(row,time,state,reason) VALUES (?,?,?,?)",
                        (entry.row, now, state, "plan_created"),
                    )
                self.db.execute("COMMIT")
            except BaseException:
                self.db.execute("ROLLBACK")
                raise
        meta = self.db.execute(
            "SELECT version,plan,snapshot,account,expires,retention,rows FROM meta"
        ).fetchall()
        if (
            len(meta) != 1
            or meta[0][:4] != (1, self.plan.digest, self.plan.snapshot_digest, account)
            or meta[0][5:] != (self.retention_days, len(self.plan.entries))
        ):
            raise ImportValidationError("Journal does not match this immutable plan or retention.")
        if not isinstance(meta[0][4], int | float) or not math.isfinite(meta[0][4]):
            raise ImportValidationError("Invalid journal retention metadata.")
        if time.time() >= meta[0][4] and not self.recovery_only:
            raise ImportValidationError(
                "Journal retention expired; inspect and reconcile before further apply."
            )
        states = self.states()
        if set(states) != {entry.row for entry in self.plan.entries} or any(
            state not in STATES for state in states.values()
        ):
            raise ImportValidationError("Invalid journal progress rows.")
        latest = dict(
            self.db.execute(
                "SELECT row,state FROM audit WHERE sequence IN (SELECT max(sequence) FROM audit GROUP BY row)"
            )
        )
        for row, state, receipt in self.db.execute("SELECT row,state,receipt FROM progress"):
            if (
                latest.get(row) != state
                or state == "acknowledged"
                and (not isinstance(receipt, str) or not receipt.strip())
            ):
                raise ImportValidationError("Journal progress and audit trail disagree.")
        for row, state in states.items():
            if state == "submitted":
                self._transition(row, "submitted", "uncertain", "interrupted_submission")

    def states(self) -> dict[int, str]:
        result: dict[int, str] = {}
        for row, state in self.db.execute("SELECT row,state FROM progress"):
            if not isinstance(row, int) or not isinstance(state, str) or state not in STATES:
                raise ImportValidationError("Invalid journal progress rows.")
            result[row] = state
        return result

    def _transition(
        self, row: int, previous: str, state: str, reason: str, receipt: str | None = None
    ) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            changed = self.db.execute(
                "UPDATE progress SET state=?,receipt=? WHERE row=? AND state=?",
                (state, receipt, row, previous),
            ).rowcount
            if changed != 1:
                raise ImportValidationError("Journal transition requires operator reconciliation.")
            self.db.execute(
                "INSERT INTO audit(row,time,state,reason) VALUES (?,?,?,?)",
                (row, time.time(), state, reason),
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def submit(self, row: int) -> None:
        if self.recovery_only:
            raise ImportValidationError("Recovery-only journals cannot dispatch writes.")
        expires = self.db.execute("SELECT expires FROM meta").fetchone()[0]
        if time.time() >= expires:
            raise ImportValidationError("Journal retention expired before dispatch.")
        self._transition(row, "planned", "submitted", "dispatch_intent")

    def acknowledge(self, row: int, receipt: str) -> None:
        if not isinstance(receipt, str) or not receipt.strip() or len(receipt) > 256:
            raise ImportValidationError("Invalid receipt; reconciliation required.")
        self._transition(row, "submitted", "acknowledged", "provider_receipt", receipt)

    def uncertain(self, row: int) -> None:
        self._transition(row, "submitted", "uncertain", "unconfirmed_outcome")

    def reconcile(self, row: int, decision: str, receipt: str | None = None) -> None:
        if self.states().get(row) != "uncertain":
            raise ImportValidationError("Only uncertain rows may be reconciled.")
        if (
            decision == "received"
            and isinstance(receipt, str)
            and receipt.strip()
            and len(receipt) <= 256
        ):
            self._transition(row, "uncertain", "acknowledged", "operator_verified_receipt", receipt)
        elif decision == "not_applied" and receipt is None:
            self._transition(row, "uncertain", "planned", "operator_verified_absent")
        elif decision == "skip" and receipt is None:
            self._transition(row, "uncertain", "skipped", "operator_skip")
        else:
            raise ImportValidationError("Invalid reconciliation decision or receipt.")


def apply_plan(plan: ImportPlan, gateway: ImportGateway, journal: Journal) -> int:
    """All rows must be resolved; uncertain outcomes never trigger automatic resend."""
    if any(entry.action == Action.UNRESOLVED for entry in plan.entries):
        raise ImportValidationError("Plan contains unresolved rows; zero writes allowed.")
    if plan.account_id != gateway.account_id or journal.plan.digest != plan.digest:
        raise ImportValidationError("Plan, journal and target account must match.")
    states = journal.states()
    if any(state in {"submitted", "uncertain"} for state in states.values()):
        raise ImportValidationError("Journal has uncertain rows requiring reconciliation.")
    pending = [entry for entry in plan.entries if states[entry.row] == "planned"]
    if pending:
        if gateway.account_currency() != plan.policy.currency:
            raise ImportValidationError("Pending plan account currency changed before apply.")
        if not {entry.fund_id for entry in pending} <= gateway.fund_ids():
            raise ImportValidationError("Pending plan funds changed before apply.")
        people = {str(person.id) for person in gateway.people()}
        if not {entry.person_id for entry in pending if entry.person_id is not None} <= people:
            raise ImportValidationError("Pending plan donors changed before apply.")
    completed = 0
    for entry in plan.entries:
        if states[entry.row] in {"acknowledged", "skipped"}:
            continue
        journal.submit(entry.row)
        try:
            receipt = gateway.create(entry)
            journal.acknowledge(entry.row, receipt)
        except BaseException:
            # Once submitted, any failure/cancellation can leave a remote write
            # uncertain. Record that boundary and propagate, never replay.
            if journal.states().get(entry.row) == "submitted":
                journal.uncertain(entry.row)
            raise
        completed += 1
    return completed


def inspect_journal(path: Path | str) -> dict[str, int]:
    """Read-only inspection remains available after expiry or a code rollback."""
    try:
        with closing(
            sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ImportValidationError("Corrupt journal; operator inspection required.")
            result: dict[str, int] = {}
            for state, count in connection.execute(
                "SELECT state,count(*) FROM progress GROUP BY state"
            ):
                if (
                    not isinstance(state, str)
                    or state not in STATES
                    or not isinstance(count, int)
                    or not 0 <= count <= 100_000
                ):
                    raise ImportValidationError("Invalid journal inspection state.")
                result[state] = count
            return result
    except sqlite3.Error as error:
        raise ImportValidationError("Unable to inspect journal.") from error


def export_journal(path: Path | str, output: Path | str) -> int:
    """Export minimal recovery metadata/audit read-only; never include gift bodies."""
    from .exporting import export_records

    def records() -> Iterator[JsonValue]:
        try:
            with closing(
                sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
            ) as connection:
                connection.execute("BEGIN")
                if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise ImportValidationError("Corrupt journal recovery state.")
                meta = connection.execute(
                    "SELECT version,plan,snapshot,created,expires,retention,rows FROM meta"
                ).fetchone()
                if meta is None or meta[0] != 1:
                    raise ImportValidationError("Unsupported journal recovery schema.")
                header: dict[str, JsonValue] = {
                    "kind": "metadata",
                    "version": meta[0],
                    "plan_digest": meta[1],
                    "snapshot_digest": meta[2],
                    "created": meta[3],
                    "expires": meta[4],
                    "retention_days": meta[5],
                    "rows": meta[6],
                }
                yield header
                for row, state, receipt in connection.execute(
                    "SELECT row,state,receipt FROM progress ORDER BY row"
                ):
                    if (
                        not isinstance(row, int)
                        or not isinstance(state, str)
                        or state not in STATES
                        or receipt is not None
                        and not isinstance(receipt, str)
                    ):
                        raise ImportValidationError("Invalid journal recovery row.")
                    progress: dict[str, JsonValue] = {
                        "kind": "progress",
                        "row": row,
                        "state": state,
                        "receipt": receipt,
                    }
                    yield progress
                for sequence, row, timestamp, state, reason in connection.execute(
                    "SELECT sequence,row,time,state,reason FROM audit ORDER BY sequence"
                ):
                    event: dict[str, JsonValue] = {
                        "kind": "audit",
                        "sequence": sequence,
                        "row": row,
                        "time": timestamp,
                        "state": state,
                        "reason": reason,
                    }
                    yield event
        except sqlite3.Error as error:
            raise ImportValidationError("Unable to export journal recovery state.") from error

    return export_records(output, "journal", records(), max_items=1_000_000)
