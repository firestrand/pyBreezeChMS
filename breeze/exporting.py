"""Standards-based containers with a versioned, lossless decoded-record envelope."""

import csv
import json
from collections.abc import Iterable, Iterator
from datetime import date
from pathlib import Path
from typing import Literal

from .breeze import BreezeApi, JsonValue
from .importing import ImportValidationError
from .storage import private_output

EXPORT_SCHEMA = "breeze-export-v1"
type ExportFormat = Literal["csv", "jsonl"]


def validate_date_window(start: str | None, end: str | None) -> None:
    """Require canonical calendar dates and an inclusive ordered window."""
    try:
        if start is None or end is None:
            raise ValueError
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.isoformat() != start or last.isoformat() != end or first > last:
            raise ValueError
    except ValueError as error:
        raise ImportValidationError(
            "Declare an inclusive YYYY-MM-DD contribution window."
        ) from error


def export_records(
    path: Path | str,
    dataset: str,
    records: Iterable[JsonValue],
    *,
    format: ExportFormat = "jsonl",
    max_items: int = 100_000,
    max_bytes: int = 64 * 1024 * 1024,
) -> int:
    """Publish only complete exports; UTF-8, exact JSON shapes, no overwrite."""
    path = Path(path)
    if dataset not in {
        "people",
        "funds",
        "contributions",
        "forms",
        "form_fields",
        "journal",
    } or format not in {"csv", "jsonl"}:
        raise ImportValidationError("Unsupported export dataset or format.")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1
        for value in (max_items, max_bytes)
    ):
        raise ImportValidationError("Export limits must be positive integers.")
    if path.exists():
        raise FileExistsError("Export destination already exists.")
    count = 0
    with private_output(path) as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        if format == "csv":
            writer.writerow(("schema", "dataset", "record_json"))
            if stream.tell() > max_bytes:
                raise ImportValidationError("Export byte limit exceeded by the CSV header.")
        for record in records:
            if not isinstance(record, dict):
                raise ImportValidationError("Export expected provider object records.")
            if count >= max_items:
                raise ImportValidationError("Export item limit exceeded; result is incomplete.")
            try:
                if format == "csv":
                    writer.writerow(
                        (
                            EXPORT_SCHEMA,
                            dataset,
                            json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True),
                        )
                    )
                else:
                    stream.write(
                        json.dumps(
                            {"schema": EXPORT_SCHEMA, "dataset": dataset, "record": record},
                            ensure_ascii=False,
                            allow_nan=False,
                            sort_keys=True,
                        )
                        + "\n"
                    )
            except ValueError as error:
                raise ImportValidationError("Invalid numeric value in export record.") from error
            if stream.tell() > max_bytes:
                raise ImportValidationError("Export byte limit exceeded; result is incomplete.")
            count += 1
    return count


def breeze_records(
    client: BreezeApi,
    dataset: str,
    *,
    start: str | None = None,
    end: str | None = None,
    details: bool = False,
    form_id: str | None = None,
) -> Iterator[JsonValue]:
    """Read-only collection boundary; unpaginated endpoints remain byte bounded."""
    if client.dry_run:
        raise ImportValidationError("Export requires read access, not no-call dry-run.")
    if dataset == "people":
        yield from client.iter_people_records(details=details)
        return
    if dataset == "funds":
        response = client.list_funds()
    elif dataset == "contributions":
        validate_date_window(start, end)
        response = client.list_contributions(start_date=start, end_date=end)
    elif dataset == "forms":
        response = client.list_forms()
    elif dataset == "form_fields" and form_id is not None:
        response = client.list_form_fields(form_id)
    else:
        raise ImportValidationError("Unsupported export selection or missing form identifier.")
    if not isinstance(response, list):
        raise ImportValidationError("Provider collection response changed shape.")
    yield from response
