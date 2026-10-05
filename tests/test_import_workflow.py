"""Approved synthetic financial cases for provider-independent planning."""

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

import pytest

from breeze.importing import (
    Action,
    ContributionRecord,
    ImportPolicy,
    ImportValidationError,
    ReviewDecision,
    Snapshot,
    build_plan,
    plan_import,
)
from breeze.models import Person


class Gateway:
    account_id = "synthetic-account"

    def __init__(self, people: tuple[Person, ...] = (Person("1", "Test", "Donor"),)) -> None:
        self.records = people
        self.existing = False
        self.writes: list[int] = []

    def people(self) -> Iterable[Person]:
        return self.records

    def fund_ids(self) -> set[str]:
        return {"5"}

    def account_currency(self) -> str:
        return "USD"

    def has_candidate(self, contribution: ContributionRecord, person_id: str) -> bool:
        return self.existing

    def create(self, entry: object) -> str:
        self.writes.append(len(self.writes))
        return "receipt"


def record(name: str = "Test Donor", amount: str = "12.34") -> ContributionRecord:
    return ContributionRecord(
        date(2026, 10, 1), Decimal(amount), "USD", "general", "donor", name, method="Cash"
    )


def policy() -> ImportPolicy:
    return ImportPolicy("USD", 2, date(2026, 10, 1), date(2026, 10, 3), (("general", "5"),))


def test_late_ambiguous_donor_is_unresolved_before_any_write() -> None:
    gateway = Gateway(
        (Person("1", "Test", "Donor"), Person("2", "Other", "Donor"), Person("3", "Other", "Donor"))
    )
    plan = plan_import(Snapshot((record(), record("Other Donor")), "a" * 64), policy(), gateway)
    assert plan.summary() == {"create": 1, "skip": 0, "unresolved": 1}
    assert not gateway.writes


def test_equal_gifts_are_review_candidates_and_never_silently_skipped() -> None:
    snapshot = Snapshot((record(), record()), "a" * 64)
    plan = plan_import(snapshot, policy(), Gateway())
    assert plan.summary() == {"create": 0, "skip": 0, "unresolved": 2}
    reviewed = plan_import(
        snapshot,
        policy(),
        Gateway(),
        {1: ReviewDecision(Action.CREATE), 2: ReviewDecision(Action.CREATE)},
    )
    assert reviewed.summary() == {"create": 2, "skip": 0, "unresolved": 0}
    assert [entry.row for entry in reviewed.entries] == [1, 2]


def test_existing_candidate_needs_explicit_create_or_skip() -> None:
    gateway = Gateway()
    gateway.existing = True
    snapshot = Snapshot((record(),), "a" * 64)
    assert plan_import(snapshot, policy(), gateway).entries[0].action == Action.UNRESOLVED
    plan = plan_import(snapshot, policy(), gateway, {1: ReviewDecision(Action.SKIP)})
    assert plan.summary() == {"create": 0, "skip": 1, "unresolved": 0}


def test_anonymous_requires_explicit_review() -> None:
    snapshot = Snapshot((record("Unknown Donor"),), "a" * 64)
    assert plan_import(snapshot, policy(), Gateway()).entries[0].action == Action.UNRESOLVED
    reviewed = plan_import(
        snapshot, policy(), Gateway(), {1: ReviewDecision(Action.CREATE, anonymous=True)}
    )
    assert reviewed.entries[0].anonymous
    assert reviewed.entries[0].action == Action.CREATE


def test_precision_error_prevents_all_provider_reads() -> None:
    class NoReads(Gateway):
        def people(self) -> tuple[Person, ...]:
            raise AssertionError("Validation must precede provider reads")

    with pytest.raises(ImportValidationError, match="precision"):
        plan_import(Snapshot((record(amount="12.345"),), "a" * 64), policy(), NoReads())


def test_offline_plan_accounts_for_rows_without_claiming_resolved_donors() -> None:
    plan = plan_import(Snapshot((record(),), "a" * 64), policy(), None)
    assert plan.summary() == {"create": 0, "skip": 0, "unresolved": 1}


@pytest.mark.parametrize("amount", ["-1", "NaN", "Infinity", "1E1001"])
def test_invalid_amounts_are_rejected_at_the_record_boundary(amount: str) -> None:
    with pytest.raises(ImportValidationError):
        record(amount=amount)


def test_exact_precision_keeps_trailing_zero_values_without_rounding() -> None:
    plan = plan_import(Snapshot((record(amount="12.34000"),), "a" * 64), policy(), Gateway())
    assert plan.entries[0].contribution.amount == Decimal("12.34")
    assert str(plan.entries[0].contribution.amount) == "12.34000"


def test_currency_window_and_mapping_validation_precede_any_reads() -> None:
    from dataclasses import replace

    records = [
        replace(record(), currency="EUR"),
        replace(record(), date=date(2026, 9, 1)),
        replace(record(), fund="unmapped"),
    ]
    for contribution in records:
        with pytest.raises(ImportValidationError):
            plan_import(Snapshot((contribution,), "a" * 64), policy(), None)


def test_failed_people_traversal_prevents_returning_a_plan() -> None:
    from collections.abc import Iterator

    class FailedGateway(Gateway):
        def people(self) -> Iterator[Person]:
            yield Person("1", "Test", "Donor")
            raise ImportValidationError("later people page failed")

    gateway = FailedGateway()
    with pytest.raises(ImportValidationError, match="page"):
        plan_import(Snapshot((record(),), "a" * 64), policy(), gateway)
    assert not gateway.writes


def test_pure_planner_uses_only_supplied_facts_and_empty_names_need_review() -> None:
    snapshot = Snapshot((record(name=""),), "a" * 64)
    plan = build_plan(snapshot, policy(), (Person("1", "", ""),), account_id="synthetic-account")
    assert plan.entries[0].action == Action.UNRESOLVED
    facts = Snapshot((record(),), "a" * 64)
    assert (
        build_plan(
            facts,
            policy(),
            (Person("1", "Test", "Donor"),),
            account_id="synthetic-account",
            candidates={1: True},
        )
        .entries[0]
        .action
        == Action.UNRESOLVED
    )


def test_plan_records_are_frozen_and_do_not_accept_mutable_snapshot_sequences() -> None:
    from dataclasses import FrozenInstanceError
    from typing import cast

    snapshot = Snapshot((record(),), "a" * 64)
    with pytest.raises(ImportValidationError):
        Snapshot(cast(tuple, [record()]), "a" * 64)
    plan = plan_import(snapshot, policy(), Gateway())
    attribute = "account_id"
    with pytest.raises(FrozenInstanceError):
        setattr(plan, attribute, "other-account")
