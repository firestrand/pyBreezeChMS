"""Validated, minimal models alongside the existing raw JSON APIs."""

from dataclasses import dataclass
from decimal import Decimal

from .errors import BreezeResponseError


@dataclass(frozen=True)
class Person:
    """The fields required to identify and display a Breeze person."""

    id: str | int
    first_name: str
    last_name: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.id, bool)
            or not isinstance(self.id, str | int)
            or isinstance(self.id, str)
            and not self.id.strip()
            or not isinstance(self.first_name, str)
            or not isinstance(self.last_name, str)
        ):
            raise BreezeResponseError("Missing or invalid Breeze person fields.")

    @classmethod
    def from_json(cls, value: object) -> Person:
        if not isinstance(value, dict):
            raise BreezeResponseError("Invalid Breeze person response.")
        person_id = value.get("id")
        first = value.get("force_first_name", value.get("first_name"))
        last = value.get("last_name")
        if (
            isinstance(person_id, bool)
            or not isinstance(person_id, (str, int))
            or not isinstance(first, str)
            or not isinstance(last, str)
            or isinstance(person_id, str)
            and not person_id.strip()
        ):
            raise BreezeResponseError("Missing or invalid Breeze person fields.")
        return cls(person_id, first, last)

    @property
    def display_name(self) -> str:
        return f"{self.first_name.strip()} {self.last_name.strip()}".strip()


@dataclass(frozen=True)
class FundAllocation:
    """An exact decimal allocation; account currency/precision are caller policy."""

    name: str
    amount: Decimal
    fund_id: str | int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not isinstance(self.amount, Decimal):
            raise ValueError("Fund allocation requires a text name and exact decimal amount.")
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("Fund amount must be finite and nonnegative.")
        exponent = self.amount.as_tuple().exponent
        if (
            not isinstance(exponent, int)
            or max(self.amount.adjusted() + 1, 1) + max(-exponent, 0) > 1000
        ):
            raise ValueError("Fund amount representation exceeds the 1000-digit limit.")
        if not self.name.strip() and self.fund_id is None:
            raise ValueError("Provide a fund name or identifier.")
        if (
            isinstance(self.fund_id, bool)
            or self.fund_id is not None
            and not isinstance(self.fund_id, str | int)
            or isinstance(self.fund_id, str)
            and not self.fund_id.strip()
        ):
            raise ValueError("Invalid fund identifier.")

    def to_json(self) -> dict[str, str | int]:
        result: dict[str, str | int] = {"name": self.name, "amount": format(self.amount, "f")}
        if self.fund_id is not None:
            result["id"] = self.fund_id
        return result
