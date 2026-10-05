"""Immutable provider-independent records, validated policy, and pure decisions."""

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from .breeze import BreezeApi, JsonValue
from .models import FundAllocation, Person


class ImportValidationError(ValueError):
    """A sanitized policy/source/plan error; never include gift payloads."""


@dataclass(frozen=True)
class ContributionRecord:
    date: date
    amount: Decimal = field(repr=False)
    currency: str
    fund: str = field(repr=False)
    donor_id: str = field(default="", repr=False)
    donor_name: str = field(default="", repr=False)
    transaction_id: str = field(default="", repr=False)
    method: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.date) is not date
            or not isinstance(self.currency, str)
            or not re.fullmatch(r"[A-Z]{3}", self.currency)
        ):
            raise ImportValidationError("Invalid contribution date or currency.")
        if not isinstance(self.amount, Decimal) or any(
            not isinstance(value, str)
            for value in (
                self.fund,
                self.donor_id,
                self.donor_name,
                self.transaction_id,
                self.method,
            )
        ):
            raise ImportValidationError("Contribution requires exact decimal and text fields.")
        if any(
            len(value) > 4096
            for value in (self.fund, self.donor_id, self.donor_name, self.transaction_id)
        ):
            raise ImportValidationError("Contribution field exceeds its bound.")
        if not self.method.strip() or len(self.method) > 128:
            raise ImportValidationError("Declare the contribution payment method.")
        try:
            FundAllocation(self.fund, self.amount)
        except ValueError as error:
            raise ImportValidationError("Invalid contribution fund or amount.") from error


@dataclass(frozen=True)
class Snapshot:
    records: tuple[ContributionRecord, ...] = field(repr=False)
    digest: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.records, tuple)
            or any(not isinstance(record, ContributionRecord) for record in self.records)
            or not isinstance(self.digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", self.digest)
            or len(self.records) > 100_000
        ):
            raise ImportValidationError("Invalid or excessive source snapshot.")


class ContributionSource(Protocol):
    def load(self) -> Snapshot: ...


@dataclass(frozen=True)
class ImportPolicy:
    currency: str
    precision: int
    start: date
    end: date
    funds: tuple[tuple[str, str], ...] = field(repr=False)
    _fund_lookup: Mapping[str, str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.currency, str)
            or not re.fullmatch(r"[A-Z]{3}", self.currency)
            or isinstance(self.precision, bool)
            or not isinstance(self.precision, int)
            or not 0 <= self.precision <= 9
        ):
            raise ImportValidationError("Declare currency and precision between zero and nine.")
        if type(self.start) is not date or type(self.end) is not date or self.start > self.end:
            raise ImportValidationError("Invalid source date window.")
        if not isinstance(self.funds, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or any(not isinstance(value, str) for value in item)
            for item in self.funds
        ):
            raise ImportValidationError("Fund mappings must be immutable text pairs.")
        mapping = dict(self.funds)
        if len(mapping) != len(self.funds) or any(
            not name.strip() or not identifier.strip() for name, identifier in self.funds
        ):
            raise ImportValidationError("Invalid or repeated fund mapping.")
        object.__setattr__(self, "_fund_lookup", MappingProxyType(mapping))

    def validate(self, record: ContributionRecord, row: int) -> str:
        if record.currency != self.currency:
            raise ImportValidationError(f"Row {row}: currency mismatch.")
        if not self.start <= record.date <= self.end:
            raise ImportValidationError(f"Row {row}: date outside source window.")
        parts = record.amount.as_tuple()
        exponent = parts.exponent
        if not isinstance(exponent, int):
            raise ImportValidationError(f"Row {row}: invalid amount.")
        trailing = 0
        for digit in reversed(parts.digits):
            if digit:
                break
            trailing += 1
        if record.amount != 0 and exponent + trailing < -self.precision:
            raise ImportValidationError(f"Row {row}: amount exceeds declared precision.")
        identifier = self._fund_lookup.get(record.fund)
        if identifier is None:
            raise ImportValidationError(f"Row {row}: fund mapping required.")
        return identifier


class Action(StrEnum):
    CREATE = "create"
    SKIP = "skip"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class ReviewDecision:
    action: Action
    person_id: str | None = field(default=None, repr=False)
    anonymous: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.action, Action)
            or self.action not in (Action.CREATE, Action.SKIP)
            or not isinstance(self.anonymous, bool)
            or self.person_id is not None
            and (not isinstance(self.person_id, str) or not self.person_id.strip())
            or self.anonymous
            and self.person_id is not None
        ):
            raise ImportValidationError("Invalid review decision.")


@dataclass(frozen=True)
class PlanEntry:
    row: int
    contribution: ContributionRecord = field(repr=False)
    fund_id: str = field(repr=False)
    person_id: str | None = field(repr=False)
    anonymous: bool
    candidate: bool
    action: Action
    reason: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.row, bool)
            or not isinstance(self.row, int)
            or not 1 <= self.row <= 100_000
            or not isinstance(self.fund_id, str)
            or not isinstance(self.contribution, ContributionRecord)
            or not self.fund_id.strip()
            or not isinstance(self.action, Action)
            or not isinstance(self.anonymous, bool)
            or not isinstance(self.candidate, bool)
            or not isinstance(self.reason, str)
        ):
            raise ImportValidationError("Invalid plan row or fund identifier.")
        if (
            self.person_id is not None
            and (not isinstance(self.person_id, str) or not self.person_id.strip())
            or self.anonymous
            and self.person_id is not None
        ):
            raise ImportValidationError("Invalid plan donor decision.")
        if self.action == Action.CREATE and (
            not self.anonymous
            and self.person_id is None
            or self.anonymous
            and self.reason != "operator_create"
            or self.candidate
            and self.reason != "operator_create"
        ):
            raise ImportValidationError("Create requires a resolved and reviewed decision.")
        reasons = {
            Action.CREATE: {"unique_match", "operator_create"},
            Action.SKIP: {"operator_skip"},
            Action.UNRESOLVED: {"donor_review", "duplicate_review", "offline_preview"},
        }
        if self.reason not in reasons[self.action]:
            raise ImportValidationError("Plan action and decision category disagree.")


@dataclass(frozen=True)
class ImportPlan:
    snapshot_digest: str
    account_id: str = field(repr=False)
    policy: ImportPolicy
    entries: tuple[PlanEntry, ...] = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.entries, tuple)
            or any(not isinstance(entry, PlanEntry) for entry in self.entries)
            or not isinstance(self.account_id, str)
            or not self.account_id.strip()
        ):
            raise ImportValidationError("Plan requires immutable entries and an account identity.")
        Snapshot(tuple(entry.contribution for entry in self.entries), self.snapshot_digest)
        for row, entry in enumerate(self.entries, 1):
            if entry.row != row or self.policy.validate(entry.contribution, row) != entry.fund_id:
                raise ImportValidationError(
                    "Plan rows must preserve validated order and fund mapping."
                )

    def summary(self) -> dict[str, int]:
        return {
            action.value: sum(entry.action == action for entry in self.entries) for action in Action
        }

    @property
    def digest(self) -> str:
        encoded = json.dumps(
            plan_payload(self), sort_keys=True, ensure_ascii=False, allow_nan=False
        ).encode()
        return hashlib.sha256(encoded).hexdigest()


class ImportGateway(Protocol):
    @property
    def account_id(self) -> str: ...
    def people(self) -> Iterable[Person]: ...
    def fund_ids(self) -> set[str]: ...
    def account_currency(self) -> str: ...
    def has_candidate(self, contribution: ContributionRecord, person_id: str) -> bool: ...
    def create(self, entry: PlanEntry) -> str: ...


class BreezeImportGateway:
    def __init__(self, client: BreezeApi) -> None:
        if client.dry_run:
            raise ImportValidationError(
                "Planning gateway requires read-only access, not no-call mode."
            )
        self.client = client

    @property
    def account_id(self) -> str:
        return self.client.breeze_url

    def people(self) -> Iterable[Person]:
        return self.client.iter_people()

    def fund_ids(self) -> set[str]:
        response = self.client.list_funds()
        if not isinstance(response, list):
            raise ImportValidationError("Invalid fund inventory response.")
        result: set[str] = set()
        for item in response:
            identifier = item.get("id") if isinstance(item, dict) else None
            if (
                isinstance(identifier, bool)
                or not isinstance(identifier, str | int)
                or not str(identifier).strip()
            ):
                raise ImportValidationError("Invalid fund inventory identifier.")
            result.add(str(identifier))
        return result

    def account_currency(self) -> str:
        summary = self.client.get_account_summary()
        details = summary.get("details") if isinstance(summary, dict) else None
        country = details.get("country") if isinstance(details, dict) else None
        currency = country.get("currency") if isinstance(country, dict) else None
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            raise ImportValidationError("Breeze account currency contract could not be verified.")
        return currency

    def has_candidate(self, contribution: ContributionRecord, person_id: str) -> bool:
        response = self.client.list_contributions(
            start_date=contribution.date.isoformat(),
            end_date=contribution.date.isoformat(),
            person_id=person_id,
            amount_min=format(contribution.amount, "f"),
            amount_max=format(contribution.amount, "f"),
        )
        if not isinstance(response, list):
            raise ImportValidationError("Invalid contribution candidate response.")
        return bool(response)

    def create(self, entry: PlanEntry) -> str:
        receipt = self.client.add_allocated_contribution(
            [FundAllocation("", entry.contribution.amount, entry.fund_id)],
            date=entry.contribution.date.isoformat(),
            person_id=entry.person_id,
            # Explicit anonymous decisions must not trigger server name/uid matching.
            processor="CSV interchange",
            method=entry.contribution.method,
        )
        if receipt is None or not str(receipt).strip():
            raise ImportValidationError(
                "Missing contribution receipt; outcome requires reconciliation."
            )
        return str(receipt)


def build_plan(
    snapshot: Snapshot,
    policy: ImportPolicy,
    people_records: Iterable[Person],
    decisions: Mapping[int, ReviewDecision] | None = None,
    *,
    account_id: str = "offline",
    candidates: Mapping[int, bool] | None = None,
) -> ImportPlan:
    """Pure planning: supplied immutable source/read facts, no provider calls."""
    candidates = {} if candidates is None else candidates
    decisions = {} if decisions is None else decisions
    if any(
        isinstance(row, bool)
        or not isinstance(row, int)
        or row < 1
        or row > len(snapshot.records)
        or not isinstance(choice, ReviewDecision)
        for row, choice in decisions.items()
    ):
        raise ImportValidationError("Review references an invalid source row.")
    funds = [policy.validate(record, row) for row, record in enumerate(snapshot.records, 1)]
    index: dict[str, list[str]] = {}
    people: set[str] = set()
    for person in people_records:
        identifier = str(person.id)
        if identifier in people:
            raise ImportValidationError("People index repeated an identifier.")
        people.add(identifier)
        if person.display_name:
            index.setdefault(person.display_name.casefold(), []).append(identifier)
    matches: list[str | None] = []
    for row, record in enumerate(snapshot.records, 1):
        choice = decisions.get(row)
        ids = index.get(record.donor_name.strip().casefold(), [])
        identifier = ids[0] if len(ids) == 1 else None
        if choice is not None:
            if choice.anonymous:
                identifier = None
            elif choice.person_id is not None:
                if account_id != "offline" and choice.person_id not in people:
                    raise ImportValidationError(
                        f"Row {row}: mapped donor is not in the complete people index."
                    )
                identifier = choice.person_id
        matches.append(identifier)
    keys = [
        (identifier, record.date, record.amount)
        if identifier is not None
        else (record.donor_id, record.donor_name, record.date, record.amount)
        for identifier, record in zip(matches, snapshot.records, strict=True)
    ]
    counts = Counter(keys)
    entries: list[PlanEntry] = []
    for row, (record, fund, identifier, key) in enumerate(
        zip(snapshot.records, funds, matches, keys, strict=True), 1
    ):
        choice = decisions.get(row)
        anonymous = choice.anonymous if choice is not None else False
        candidate = counts[key] > 1 or candidates.get(row, False)
        action, reason = Action.UNRESOLVED, "donor_review"
        if account_id == "offline":
            reason = "offline_preview"
        elif choice is not None and choice.action == Action.SKIP:
            action, reason = Action.SKIP, "operator_skip"
        elif identifier is not None or anonymous:
            if candidate and choice is None:
                reason = "duplicate_review"
            else:
                action, reason = Action.CREATE, "operator_create" if choice else "unique_match"
        entries.append(
            PlanEntry(row, record, fund, identifier, anonymous, candidate, action, reason)
        )
    return ImportPlan(
        snapshot.digest,
        account_id,
        policy,
        tuple(entries),
    )


def plan_import(
    snapshot: Snapshot,
    policy: ImportPolicy,
    gateway: ImportGateway | None,
    decisions: Mapping[int, ReviewDecision] | None = None,
) -> ImportPlan:
    """Orchestrate bounded read facts, then invoke the pure planning function."""
    if gateway is None:
        return build_plan(snapshot, policy, (), decisions)
    funds = {policy.validate(record, row) for row, record in enumerate(snapshot.records, 1)}
    if gateway.account_currency() != policy.currency:
        raise ImportValidationError("Declared currency does not match the Breeze account.")
    if not funds <= gateway.fund_ids():
        raise ImportValidationError("Mapped funds are absent from the Breeze fund inventory.")
    people = tuple(gateway.people())
    initial = build_plan(snapshot, policy, people, decisions, account_id=gateway.account_id)
    candidates: dict[int, bool] = {}
    cache: dict[tuple[str, date, Decimal], bool] = {}
    for entry in initial.entries:
        if entry.person_id is not None and entry.action != Action.SKIP:
            key = (entry.person_id, entry.contribution.date, entry.contribution.amount)
            if key not in cache:
                cache[key] = gateway.has_candidate(entry.contribution, entry.person_id)
            candidates[entry.row] = cache[key]
    return build_plan(
        snapshot, policy, people, decisions, account_id=gateway.account_id, candidates=candidates
    )


def plan_payload(plan: ImportPlan) -> dict[str, JsonValue]:
    rows: list[JsonValue] = []
    for entry in plan.entries:
        record = entry.contribution
        rows.append(
            {
                "row": entry.row,
                "date": record.date.isoformat(),
                "amount": format(record.amount, "f"),
                "currency": record.currency,
                "fund": record.fund,
                "donor_id": record.donor_id,
                "donor_name": record.donor_name,
                "transaction_id": record.transaction_id,
                "method": record.method,
                "fund_id": entry.fund_id,
                "person_id": entry.person_id,
                "anonymous": entry.anonymous,
                "candidate": entry.candidate,
                "action": entry.action.value,
                "reason": entry.reason,
            }
        )
    mapping: list[JsonValue] = [[name, identifier] for name, identifier in plan.policy.funds]
    return {
        "schema": "import-plan-v1",
        "snapshot_digest": plan.snapshot_digest,
        "account_id": plan.account_id,
        "currency": plan.policy.currency,
        "precision": plan.policy.precision,
        "start": plan.policy.start.isoformat(),
        "end": plan.policy.end.isoformat(),
        "funds": mapping,
        "entries": rows,
    }
