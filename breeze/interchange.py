"""Versioned contribution CSV source and private plan serialization."""

import csv
import hashlib
import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .importing import (
    Action,
    ContributionRecord,
    ImportPlan,
    ImportPolicy,
    ImportValidationError,
    PlanEntry,
    Snapshot,
    plan_payload,
)
from .storage import boolean, integer, object_value, read_json, string, write_json

SCHEMA = "contributions-v1"
COLUMNS = (
    "schema",
    "date",
    "amount",
    "currency",
    "fund",
    "donor_id",
    "donor_name",
    "transaction_id",
    "method",
)


class CsvContributionSource:
    """Read one bounded immutable snapshot; source errors never return partial data."""

    def __init__(
        self, path: Path | str, *, max_bytes: int = 16 * 1024 * 1024, max_rows: int = 100_000
    ) -> None:
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in (max_bytes, max_rows)
        ):
            raise ImportValidationError("Source limits must be positive integers.")
        self.path, self.max_bytes, self.max_rows = Path(path), max_bytes, min(max_rows, 100_000)

    def load(self) -> Snapshot:
        digest = hashlib.sha256()
        total = 0
        with self.path.open("rb") as stream:

            def lines() -> Iterator[str]:
                nonlocal total
                first = True
                while raw := stream.readline(self.max_bytes + 1):
                    total += len(raw)
                    if total > self.max_bytes:
                        raise ImportValidationError("Contribution source exceeds its byte limit.")
                    digest.update(raw)
                    yield raw.decode("utf-8-sig" if first else "utf-8")
                    first = False

            records: list[ContributionRecord] = []
            try:
                reader = csv.DictReader(lines(), strict=True)
                if tuple(reader.fieldnames or ()) != COLUMNS:
                    raise ImportValidationError("Expected the contributions-v1 CSV header.")
                for row_number, row in enumerate(reader, 1):
                    if row_number > self.max_rows:
                        raise ImportValidationError("Contribution source exceeds its row limit.")
                    if (
                        None in row
                        or any(value is None for value in row.values())
                        or row["schema"] != SCHEMA
                    ):
                        raise ImportValidationError(f"Row {row_number}: invalid schema or width.")
                    # DictReader's declared row type includes its missing-column
                    # sentinel; copy after validation to expose honest text typing.
                    fields = {
                        key: value
                        for key, value in row.items()
                        if isinstance(key, str) and isinstance(value, str)
                    }
                    if not re.fullmatch(
                        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", fields["date"]
                    ) or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", fields["amount"]):
                        raise ImportValidationError(
                            f"Row {row_number}: invalid ISO date or exact decimal amount."
                        )
                    try:
                        records.append(
                            ContributionRecord(
                                date.fromisoformat(fields["date"]),
                                Decimal(fields["amount"]),
                                fields["currency"],
                                fields["fund"],
                                fields["donor_id"],
                                fields["donor_name"],
                                fields["transaction_id"],
                                fields["method"],
                            )
                        )
                    except ValueError as error:
                        raise ImportValidationError(
                            f"Row {row_number}: invalid contribution fields."
                        ) from error
            except (UnicodeDecodeError, csv.Error) as error:
                raise ImportValidationError("Invalid UTF-8 contribution CSV.") from error
        return Snapshot(tuple(records), digest.hexdigest())


def save_plan(path: Path | str, plan: ImportPlan) -> None:
    write_json(path, plan_payload(plan))


def load_plan(path: Path | str) -> ImportPlan:
    payload = object_value(read_json(path))
    try:
        if payload["schema"] != "import-plan-v1":
            raise ImportValidationError("Unsupported import plan version.")
        mapping = payload["funds"]
        if not isinstance(mapping, list):
            raise ImportValidationError("Invalid plan fund mapping.")
        funds: list[tuple[str, str]] = []
        for item in mapping:
            if not isinstance(item, list) or len(item) != 2:
                raise ImportValidationError("Invalid plan fund mapping.")
            funds.append((string(item[0]), string(item[1])))
        policy = ImportPolicy(
            string(payload["currency"]),
            integer(payload["precision"]),
            date.fromisoformat(string(payload["start"])),
            date.fromisoformat(string(payload["end"])),
            tuple(funds),
        )
        rows = payload["entries"]
        if not isinstance(rows, list) or len(rows) > 100_000:
            raise ImportValidationError("Invalid or excessive plan rows.")
        entries: list[PlanEntry] = []
        for ordinal, raw in enumerate(rows, 1):
            row = object_value(raw)
            record = ContributionRecord(
                date.fromisoformat(string(row["date"])),
                Decimal(string(row["amount"])),
                string(row["currency"]),
                string(row["fund"]),
                string(row["donor_id"]),
                string(row["donor_name"]),
                string(row["transaction_id"]),
                string(row["method"]),
            )
            identifier = None if row["person_id"] is None else string(row["person_id"])
            entry = PlanEntry(
                integer(row["row"]),
                record,
                string(row["fund_id"]),
                identifier,
                boolean(row["anonymous"]),
                boolean(row["candidate"]),
                Action(string(row["action"])),
                string(row["reason"]),
            )
            if entry.row != ordinal or policy.validate(record, ordinal) != entry.fund_id:
                raise ImportValidationError("Plan row ordering or fund mapping changed.")
            if entry.action == Action.CREATE and (
                not entry.anonymous
                and not entry.person_id
                or entry.anonymous
                and entry.person_id is not None
                or entry.candidate
                and entry.reason != "operator_create"
            ):
                raise ImportValidationError("Plan contains an unreviewed create decision.")
            entries.append(entry)
        digest = string(payload["snapshot_digest"])
        Snapshot((), digest)
        return ImportPlan(digest, string(payload["account_id"]), policy, tuple(entries))
    except (KeyError, ValueError, InvalidOperation) as error:
        raise ImportValidationError("Invalid or unresolved operator plan fields.") from error
