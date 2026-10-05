"""Approved synthetic source, exact representation, and atomic export contracts."""

import csv
import io
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from breeze.breeze import JsonValue
from breeze.exporting import export_records
from breeze.importing import ImportValidationError, plan_import
from breeze.interchange import COLUMNS, CsvContributionSource, load_plan, save_plan
from tests.test_import_workflow import Gateway, policy


def source_text() -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    writer.writerow(
        (
            "contributions-v1",
            "2026-10-01",
            "12.34",
            "USD",
            "general",
            "donor",
            'Test "Donor", Café',
            "",
            "Cash",
        )
    )
    return stream.getvalue()


def test_source_is_bom_tolerant_exact_and_plan_roundtrips(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(source_text(), encoding="utf-8-sig")
    snapshot = CsvContributionSource(source).load()
    assert str(snapshot.records[0].amount) == "12.34"
    assert snapshot.records[0].donor_name == 'Test "Donor", Café'
    plan = plan_import(snapshot, policy(), Gateway())
    destination = tmp_path / "plan.json"
    save_plan(destination, plan)
    assert load_plan(destination) == plan
    assert destination.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("change", ["precision", "width", "version", "date", "encoding"])
def test_malformed_source_fails_without_partial_snapshot(tmp_path: Path, change: str) -> None:
    text = source_text()
    if change == "precision":
        text = text.replace("12.34", "NaN")
    elif change == "width":
        text += "one,two\n"
    elif change == "version":
        text = text.replace("contributions-v1", "unknown-v2")
    elif change == "date":
        text = text.replace("2026-10-01", "2026-99-01")
    path = tmp_path / "source.csv"
    path.write_bytes(b"\xff" if change == "encoding" else text.encode())
    with pytest.raises(ImportValidationError):
        CsvContributionSource(path).load()


def test_excessive_source_and_export_stop(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    path.write_text(source_text())
    with pytest.raises(ImportValidationError, match="byte"):
        CsvContributionSource(path, max_bytes=4).load()
    destination = tmp_path / "export.jsonl"
    with pytest.raises(ImportValidationError, match="item"):
        export_records(destination, "people", [{"id": "1"}, {"id": "2"}], max_items=1)
    assert not destination.exists()
    with pytest.raises(ImportValidationError, match="byte"):
        export_records(destination, "people", [], format="csv", max_bytes=1)
    assert not destination.exists()


def test_late_failure_does_not_publish_an_incomplete_export(tmp_path: Path) -> None:
    def records() -> Iterator[JsonValue]:
        yield {"id": "1"}
        raise ImportValidationError("late provider page failure")

    destination = tmp_path / "export.jsonl"
    with pytest.raises(ImportValidationError):
        export_records(destination, "people", records())
    assert not destination.exists()


def test_csv_and_jsonl_preserve_the_same_nested_decoded_record(tmp_path: Path) -> None:
    record: JsonValue = {
        "id": "1",
        "name": 'Café, "quoted"',
        "details": {"custom": [None, True, "line\nbreak"]},
    }
    csv_path, jsonl_path = tmp_path / "export.csv", tmp_path / "export.jsonl"
    assert export_records(csv_path, "people", [record], format="csv") == 1
    assert export_records(jsonl_path, "people", [record]) == 1
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert (
        json.loads(rows[0]["record_json"]) == json.loads(jsonl_path.read_text())["record"] == record
    )
    with pytest.raises(FileExistsError):
        export_records(csv_path, "people", [])


def test_source_row_limit_never_returns_a_partial_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    path.write_text(source_text() + source_text().splitlines()[1] + "\n")
    with pytest.raises(ImportValidationError, match="row"):
        CsvContributionSource(path, max_rows=1).load()
