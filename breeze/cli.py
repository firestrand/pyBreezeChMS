"""Thin installed operator commands: offline preview, read-only plan/export, apply."""

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import cast

from .breeze import BreezeApi, BreezeError
from .configuration import breeze_credentials
from .exporting import ExportFormat, breeze_records, export_records, validate_date_window
from .importing import (
    Action,
    BreezeImportGateway,
    ImportPolicy,
    ImportValidationError,
    ReviewDecision,
    plan_import,
)
from .interchange import CsvContributionSource, load_plan, save_plan
from .journal import Journal, apply_plan, export_journal, inspect_journal
from .storage import boolean, integer, object_value, read_json, string


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="breeze", description="Versioned data exchange and reviewed contribution workflows."
    )
    result.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Private dotenv file; ambient variables take precedence.",
    )
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("preview", "plan"):
        command = commands.add_parser(
            name,
            help="Offline report preview."
            if name == "preview"
            else "Read-only Breeze plan; unresolved rows require review.",
        )
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--decisions", type=Path)
        command.add_argument("--output", type=Path, required=name == "plan")
    apply = commands.add_parser(
        "apply", help="Apply a complete reviewed plan using one durable journal."
    )
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--source", type=Path, required=True)
    apply.add_argument("--journal", type=Path, required=True)
    apply.add_argument("--retention-days", type=int, required=True)
    apply.add_argument(
        "--confirm-plan",
        required=True,
        help="Exact reviewed plan digest; explicit write authorization.",
    )
    status = commands.add_parser(
        "journal-status", help="Inspect counts read-only, including after retention expiry."
    )
    status.add_argument("--journal", type=Path, required=True)
    status.add_argument(
        "--output", type=Path, help="Private read-only recovery/audit JSON Lines export."
    )
    reconcile = commands.add_parser(
        "reconcile", help="Record an explicit operator decision for an uncertain row."
    )
    reconcile.add_argument("--plan", type=Path, required=True)
    reconcile.add_argument("--journal", type=Path, required=True)
    reconcile.add_argument("--retention-days", type=int, required=True)
    reconcile.add_argument("--row", type=int, required=True)
    reconcile.add_argument("--decision", choices=("received", "not_applied", "skip"), required=True)
    reconcile.add_argument("--receipt")
    reconcile.add_argument("--confirm-plan", required=True)
    export = commands.add_parser(
        "export", help="Read-only UTF-8 CSV/JSON Lines export with versioned envelopes."
    )
    export.add_argument(
        "dataset", choices=("people", "funds", "contributions", "forms", "form_fields")
    )
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--format", choices=("csv", "jsonl"), default="jsonl")
    export.add_argument("--start")
    export.add_argument("--end")
    export.add_argument("--details", action="store_true")
    export.add_argument("--form-id")
    return result


def load_policy(path: Path | str) -> ImportPolicy:
    payload = object_value(read_json(path))
    try:
        funds = object_value(payload["funds"])
        return ImportPolicy(
            string(payload["currency"]),
            integer(payload["precision"]),
            date.fromisoformat(string(payload["start"])),
            date.fromisoformat(string(payload["end"])),
            tuple((name, string(identifier)) for name, identifier in funds.items()),
        )
    except KeyError as error:
        raise ImportValidationError("Missing required policy fields.") from error


def load_decisions(path: Path | str | None) -> dict[int, ReviewDecision]:
    if path is None:
        return {}
    payload = object_value(read_json(path))
    decisions: dict[int, ReviewDecision] = {}
    for key, raw in payload.items():
        if not re.fullmatch(r"[1-9][0-9]{0,5}", key) or int(key) > 100_000:
            raise ImportValidationError("Review rows must use canonical positive ordinals.")
        value = object_value(raw)
        try:
            decisions[int(key)] = ReviewDecision(
                Action(string(value["action"])),
                None if value.get("person_id") is None else string(value["person_id"]),
                boolean(value.get("anonymous", False)),
            )
        except KeyError as error:
            raise ImportValidationError("Invalid review decision fields.") from error
    return decisions


def run(args: argparse.Namespace) -> int:
    if args.command == "journal-status":
        if args.output is not None:
            export_journal(args.journal, args.output)
        print(json.dumps(inspect_journal(args.journal), sort_keys=True))
        return 0
    if args.command in {"apply", "reconcile"}:
        plan = load_plan(args.plan)
        if args.confirm_plan != plan.digest:
            raise ImportValidationError("Confirm the exact reviewed plan digest.")
        if args.command == "reconcile":
            with Journal(
                args.journal, plan, retention_days=args.retention_days, recovery_only=True
            ) as journal:
                journal.reconcile(args.row, args.decision, args.receipt)
                print(
                    json.dumps(
                        {
                            state: list(journal.states().values()).count(state)
                            for state in set(journal.states().values())
                        },
                        sort_keys=True,
                    )
                )
            return 0
        if plan.summary()["unresolved"]:
            print("Unresolved plans cannot be applied.", file=sys.stderr)
            return 3
        snapshot = CsvContributionSource(args.source).load()
        if snapshot.digest != plan.snapshot_digest or snapshot.records != tuple(
            entry.contribution for entry in plan.entries
        ):
            raise ImportValidationError("Source snapshot changed after planning.")
        url, key = breeze_credentials(args.env_file)
        with (
            BreezeApi(url, key) as client,
            Journal(args.journal, plan, retention_days=args.retention_days) as journal,
        ):
            count = apply_plan(plan, BreezeImportGateway(client), journal)
        print(json.dumps({"acknowledged_this_run": count}))
        return 0
    if args.command in {"preview", "plan"}:
        snapshot = CsvContributionSource(args.source).load()
        policy = load_policy(args.policy)
        decisions = load_decisions(args.decisions)
        if args.command == "preview":
            plan = plan_import(snapshot, policy, None, decisions)
        else:
            url, key = breeze_credentials(args.env_file)
            with BreezeApi(url, key) as client:
                plan = plan_import(snapshot, policy, BreezeImportGateway(client), decisions)
        if args.output is not None:
            save_plan(args.output, plan)
        print(json.dumps({"summary": plan.summary(), "plan_digest": plan.digest}, sort_keys=True))
        return 3 if args.command == "plan" and plan.summary()["unresolved"] else 0
    if args.command == "export":
        if args.dataset == "contributions":
            validate_date_window(args.start, args.end)
        url, key = breeze_credentials(args.env_file)
        with BreezeApi(url, key) as client:
            count = export_records(
                args.output,
                args.dataset,
                breeze_records(
                    client,
                    args.dataset,
                    start=args.start,
                    end=args.end,
                    details=args.details,
                    form_id=args.form_id,
                ),
                format=cast(ExportFormat, args.format),
            )
        print(json.dumps({"exported": count}))
        return 0
    raise ImportValidationError("Unsupported operator command.")


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return run(args)
    except ImportValidationError, ValueError, OSError, UnicodeError, sqlite3.Error:
        print(
            "Operation stopped: check configuration, source, plan and journal state.",
            file=sys.stderr,
        )
        return 4 if args.command == "apply" else 1
    except BreezeError:
        print(
            "Breeze operation failed. Inspect journal state before retrying an apply.",
            file=sys.stderr,
        )
        return 4 if args.command == "apply" else 1


if __name__ == "__main__":
    raise SystemExit(main())
