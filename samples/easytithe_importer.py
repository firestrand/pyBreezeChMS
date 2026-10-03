#!/usr/bin/env python3
"""Import EasyTithe reports into Breeze using runtime environment credentials.

Set EASYTITHE_USERNAME, EASYTITHE_PASSWORD and BREEZE_API_KEY. Run with
--breeze_url, --start_date and --end_date. --dry_run validates the downloaded
report without making Breeze requests. Logs contain counts rather than personal
or financial records. EasyTithe configures its Custom export format on login.
"""

import argparse
import json
import logging
import os
from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation

from easytithe import EasyTithe

from breeze.breeze import BreezeApi, BreezeError, Identifier, JsonValue

logger = logging.getLogger(__name__)


class Contribution:
    """A validated EasyTithe export row; fund edits affect only this instance."""

    def __init__(self, contribution: Mapping[str, str]) -> None:
        required = {"Name", "Date", "Fund", "Amount", "Type", "Email", "PersonID"}
        if not required <= contribution.keys() or not contribution["Name"].strip():
            raise ValueError("Incomplete EasyTithe contribution.")
        self._contribution = dict(contribution)
        # Validate before the importer can send a financial record.
        datetime.strptime(contribution["Date"], "%m/%d/%Y")
        try:
            amount = Decimal(self.amount)
        except InvalidOperation as error:
            raise ValueError("Invalid contribution amount.") from error
        if not amount.is_finite() or amount < 0:
            raise ValueError("Contribution amount must be finite and nonnegative.")

    @property
    def first_name(self) -> str:
        return self.name.split()[0]

    @property
    def last_name(self) -> str:
        return self.name.split()[-1]

    @property
    def full_name(self) -> str:
        return self.name.strip()

    @property
    def name(self) -> str:
        return self._contribution["Name"]

    @property
    def date(self) -> str:
        return datetime.strptime(self._contribution["Date"], "%m/%d/%Y").strftime("%Y-%m-%d")

    @property
    def fund(self) -> str:
        return self._contribution["Fund"]

    @fund.setter
    def fund(self, fund_name: str) -> None:
        self._contribution["Fund"] = fund_name

    @property
    def amount(self) -> str:
        return self._contribution["Amount"].lstrip("$").replace(",", "")

    @property
    def card_type(self) -> str:
        return self._contribution["Type"]

    @property
    def email_address(self) -> str:
        return self._contribution["Email"]

    @property
    def uid(self) -> str:
        return self._contribution["PersonID"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-l", "--breeze_url", required=True)
    parser.add_argument("-s", "--start_date", required=True, help="MM/DD/YYYY")
    parser.add_argument("-e", "--end_date", required=True, help="MM/DD/YYYY")
    parser.add_argument("-d", "--dry_run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def enable_console_logging(default_level: int = logging.INFO) -> None:
    logging.basicConfig(level=default_level, format="%(asctime)s [%(levelname)s] %(message)s")
    # Transport debug logs include query strings containing personal data.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def _people_index(response: JsonValue) -> dict[str, list[Identifier]]:
    if not isinstance(response, list):
        raise BreezeError("Expected a list of Breeze people.")
    result: dict[str, list[Identifier]] = {}
    for person in response:
        if not isinstance(person, dict):
            raise BreezeError("Invalid Breeze person.")
        first = person.get("force_first_name", person.get("first_name"))
        last = person.get("last_name")
        person_id = person.get("id")
        if (
            not isinstance(first, str)
            or not isinstance(last, str)
            or isinstance(person_id, bool)
            or not isinstance(person_id, (str, int))
        ):
            raise BreezeError("Missing or invalid Breeze person fields.")
        name = f"{first.strip()} {last.strip()}".strip().casefold()
        if name:
            result.setdefault(name, []).append(person_id)
    return result


def import_contributions(client: BreezeApi, contributions: Iterable[Contribution]) -> int:
    """Import validated rows, skipping duplicates and rejecting ambiguous names.

    Unmatched rows remain anonymous, as in the original importer. Matching uses
    exact case-insensitive names; names are data, never regular expressions.
    Dry-run validates rows without issuing any Breeze request.
    """
    if client.dry_run:
        count = sum(1 for _ in contributions)
        logger.info("Validated %d contributions in dry-run mode", count)
        return 0
    people = _people_index(client.get_people())
    imported = 0
    for contribution in contributions:
        matches = people.get(contribution.full_name.casefold(), [])
        if len(matches) > 1:
            raise BreezeError("Ambiguous person match; resolve before importing.")
        person_id = matches[0] if matches else None
        if person_id is not None:
            existing = client.list_contributions(
                start_date=contribution.date,
                end_date=contribution.date,
                person_id=person_id,
                amount_min=contribution.amount,
                amount_max=contribution.amount,
            )
            if not isinstance(existing, list):
                raise BreezeError("Expected a contribution list when checking duplicates.")
            if existing:
                logger.info("Skipped a duplicate contribution")
                continue
        else:
            logger.warning("No matching person; importing an anonymous contribution")
        client.add_contribution(
            date=contribution.date,
            name=contribution.name,
            uid=contribution.uid,
            method="Credit/Debit Online",
            funds_json=json.dumps([{"name": contribution.fund, "amount": contribution.amount}]),
            amount=contribution.amount,
            group=contribution.date,
            processor="EasyTithe",
            batch_name=f"EasyTithe ({contribution.date})",
            person_id=person_id,
        )
        imported += 1
    logger.info("Imported %d contributions", imported)
    return imported


def main() -> None:
    args = parse_args()
    enable_console_logging(logging.DEBUG if args.debug else logging.INFO)
    required = ("EASYTITHE_USERNAME", "EASYTITHE_PASSWORD", "BREEZE_API_KEY")
    if any(not os.environ.get(name) for name in required):
        raise ValueError("Set EASYTITHE_USERNAME, EASYTITHE_PASSWORD and BREEZE_API_KEY.")
    with (
        EasyTithe(os.environ["EASYTITHE_USERNAME"], os.environ["EASYTITHE_PASSWORD"]) as source,
        BreezeApi(args.breeze_url, os.environ["BREEZE_API_KEY"], dry_run=args.dry_run) as client,
    ):
        # Validate the complete bounded report before writing any contributions.
        contributions = [
            Contribution(row) for row in source.GetContributions(args.start_date, args.end_date)
        ]
        import_contributions(client, contributions)


if __name__ == "__main__":
    main()
