"""Python wrapper for Breeze ChMS API: http://www.breezechms.com/api

This API wrapper allows churches to build custom functionality integrated with
Breeze Church Management System.

Usage:
  from breeze import breeze

  breeze_api = breeze.BreezeApi(
      breeze_url='https://demo.breezechms.com',
      api_key='YOUR_API_KEY')
  people = breeze_api.get_people();

  for person in people:
    print(f"{person['first_name']} {person['last_name']}")
"""

__author__ = "alexortizrosado@gmail.com (Alex Ortiz-Rosado)"

import json
import logging
import math
from collections.abc import Iterable, Iterator, Mapping
from decimal import Decimal, localcontext
from enum import StrEnum
from typing import Protocol
from urllib.parse import quote, urlsplit

import requests

from .errors import (
    BreezeAuthenticationError,
    BreezeDeadlineError,
    BreezeError,
    BreezeHttpError,
    BreezeRateLimitError,
    BreezeResponseError,
    BreezeTransportError,
)
from .models import FundAllocation, Person
from .policy import RateLimiter, account_limiter

logger = logging.getLogger(__name__)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type Identifier = str | int
type Amount = str | int | float


class ENDPOINTS(StrEnum):
    """Breeze endpoint paths, usable as strings."""

    PEOPLE = "/api/people"
    EVENTS = "/api/events"
    PROFILE_FIELDS = "/api/profile"
    CONTRIBUTIONS = "/api/giving"
    FUNDS = "/api/funds"
    PLEDGES = "/api/pledges"
    TAGS = "/api/tags"
    ACCOUNT_SUMMARY = "/api/account/summary"
    FORMS = "/api/forms"


class HttpResponse(Protocol):
    """Response operations required by the client."""

    @property
    def status_code(self) -> int: ...
    def iter_content(self, chunk_size: int) -> Iterable[bytes]: ...
    def close(self) -> None: ...


class HttpConnection(Protocol):
    """Injectable transport; the caller owns its lifecycle."""

    def get(
        self,
        url: str,
        *,
        verify: bool,
        params: Mapping[str, str],
        headers: Mapping[str, str],
        timeout: float,
        stream: bool,
        allow_redirects: bool,
    ) -> HttpResponse: ...


def _json_value(value: object) -> JsonValue:
    """Validate the decoded JSON boundary before exposing typed data."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {str(key): _json_value(item) for key, item in value.items()}
    raise BreezeResponseError("Invalid JSON value in API response.")


def _validate_json_array(value: str) -> None:
    """Reject malformed field/fund payloads before issuing a write."""
    try:
        decoded: object = json.loads(value)
        validated = _json_value(decoded)
    except (ValueError, RecursionError) as error:
        raise BreezeError("Invalid JSON request parameter.") from error
    if not isinstance(validated, list) or any(not isinstance(item, dict) for item in validated):
        raise BreezeError("JSON request parameter must be an array of objects.")


def _giving_query(fields: Mapping[str, str | int | float | None]) -> str:
    """Preserve giving endpoint omission/ordering rules in one serializer."""
    params: list[str] = []
    for key, value in fields.items():
        if value is None or (not value and key != "amount"):
            continue
        if key == "funds_json" and isinstance(value, str):
            _validate_json_array(value)
        params.append(f"{key}={quote(str(value), safe='')}")
    return "&".join(params)


class BreezeApi:
    """A wrapper for the Breeze REST API."""

    def __init__(
        self,
        breeze_url: str,
        api_key: str,
        dry_run: bool = False,
        connection: HttpConnection | None = None,
        *,
        max_response_bytes: int = 16 * 1024 * 1024,
        rate_limiter: RateLimiter | None = None,
        request_timeout: float = 60,
        operation_timeout: float = 60,
    ) -> None:
        """Create a client for an HTTPS Breeze subdomain.

        A default session is owned by this client; close it or use a context
        manager. Injected transports remain owned by the caller. Responses are
        limited to max_response_bytes; paginate large result sets.
        """
        try:
            parsed = urlsplit(breeze_url)
            port = parsed.port
        except ValueError as error:
            raise BreezeError("Invalid Breeze URL.") from error
        host = parsed.hostname or ""
        subdomain = host.removesuffix(".breezechms.com")
        if (
            parsed.scheme != "https"
            or not host.endswith(".breezechms.com")
            or not subdomain
            or "." in subdomain
            or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in subdomain)
            or subdomain.startswith("-")
            or subdomain.endswith("-")
            or parsed.username is not None
            or parsed.password is not None
            or port not in (None, 443)
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise BreezeError("Provide an HTTPS URL for a Breeze subdomain.")
        if (
            not isinstance(api_key, str)
            or not api_key.strip()
            or "\r" in api_key
            or "\n" in api_key
        ):
            raise BreezeError("Provide a nonempty API key without newlines.")
        if (
            isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or max_response_bytes < 1
        ):
            raise ValueError("max_response_bytes must be a positive integer.")
        if any(
            not math.isfinite(value) or value <= 0 for value in (request_timeout, operation_timeout)
        ):
            raise ValueError("Request and operation timeouts must be finite and positive.")
        self.breeze_url = f"https://{host}"
        self.api_key = api_key
        self.dry_run = dry_run
        self.max_response_bytes = max_response_bytes
        self.rate_limiter = account_limiter(host, api_key) if rate_limiter is None else rate_limiter
        self.request_timeout = request_timeout
        self.operation_timeout = operation_timeout
        self._owns_connection = connection is None
        self.connection: HttpConnection = requests.Session() if connection is None else connection

    def _request(
        self,
        endpoint: str,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> JsonValue:
        """Record fixed categories/counts/timing without sensitive request data."""
        if self.dry_run:
            return self._perform_request(endpoint, params, headers, timeout)
        started = self.rate_limiter.clock()
        outcome = "other_failure"
        try:
            result = self._perform_request(endpoint, params, headers, timeout)
            outcome = "success"
            return result
        except BreezeError as error:
            # Ordered because deadline/auth/rate errors subclass broader errors.
            categories = (
                (BreezeDeadlineError, "deadline"),
                (BreezeAuthenticationError, "authentication"),
                (BreezeRateLimitError, "rate_limit"),
                (BreezeHttpError, "http"),
                (BreezeTransportError, "transport"),
                (BreezeResponseError, "response"),
            )
            outcome = next(
                (category for error_type, category in categories if isinstance(error, error_type)),
                "validation",
            )
            raise
        finally:
            logger.debug(
                "Breeze operation outcome=%s count=1 elapsed_seconds=%.3f",
                outcome,
                max(0.0, self.rate_limiter.clock() - started),
            )

    def _perform_request(
        self,
        endpoint: str,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> JsonValue:
        """Make one bounded request without retrying writes or following redirects."""
        request_headers = dict(headers or {})
        request_headers.update({"Content-Type": "application/json", "Api-Key": self.api_key})
        timeout = self.request_timeout if timeout is None else timeout
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive.")
        if len(endpoint.encode("utf-8")) > 64 * 1024:
            raise BreezeError("Breeze request exceeds the 64 KiB URL limit.")
        if self.dry_run:
            return None
        deadline = self.rate_limiter.clock() + self.operation_timeout
        self.rate_limiter.wait(deadline)
        try:
            response = self.connection.get(
                f"{self.breeze_url}{endpoint}",
                verify=True,
                params=params or {},
                headers=request_headers,
                timeout=min(timeout, self.rate_limiter.remaining(deadline)),
                stream=True,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise BreezeTransportError("Breeze connection failed.") from error
        try:
            self.rate_limiter.remaining(deadline)
            if not 200 <= response.status_code < 300:
                if response.status_code in (401, 403):
                    raise BreezeAuthenticationError(response.status_code)
                if response.status_code == 429:
                    raise BreezeRateLimitError(response.status_code)
                raise BreezeHttpError(response.status_code)
            content = bytearray()
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    self.rate_limiter.remaining(deadline)
                    if len(content) + len(chunk) > self.max_response_bytes:
                        raise BreezeResponseError(
                            "Breeze response exceeds the configured size limit."
                        )
                    content.extend(chunk)
            except requests.RequestException as error:
                raise BreezeTransportError("Failed to read Breeze response.") from error
            try:
                decoded: object = json.loads(content)
            except (ValueError, UnicodeDecodeError, RecursionError) as error:
                raise BreezeResponseError("Breeze returned invalid JSON.") from error
            try:
                result = _json_value(decoded)
            except RecursionError as error:
                raise BreezeResponseError("Breeze response JSON is too deeply nested.") from error
            if not self._request_succeeded(result):
                raise BreezeResponseError("Breeze reported an API error.")
            self.rate_limiter.remaining(deadline)
            return result
        finally:
            response.close()

    def _request_succeeded(self, response: JsonValue) -> bool:
        """Accept containers and true, rejecting error objects and other scalars."""
        if isinstance(response, bool):
            return response
        if isinstance(response, dict):
            return not ("errors" in response or "errorCode" in response)
        return isinstance(response, list)

    def close(self) -> None:
        """Close the owned session; injected transports remain caller-owned."""
        if self._owns_connection and isinstance(self.connection, requests.Session):
            self.connection.close()

    def __enter__(self) -> BreezeApi:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _payment_id(self, response: JsonValue) -> Identifier | None:
        """Validate payment responses while preserving dry-run absence."""
        if response is None and self.dry_run:
            return None
        if not isinstance(response, dict):
            raise BreezeResponseError("Invalid payment response.")
        payment_id = response.get("payment_id")
        if (
            isinstance(payment_id, bool)
            or not isinstance(payment_id, (str, int))
            or isinstance(payment_id, str)
            and not payment_id.strip()
        ):
            raise BreezeResponseError("Missing or invalid payment ID.")
        return payment_id

    def get_account_summary(self) -> JsonValue:
        """Retrieve the details for a specific account using the API key
          and URL. It can also work to see if the key and URL are valid.

        Returns:
          JSON response. For example:
          {
            "id":"1234",
            "name":"Grace Church",
            "subdomain":"gracechurchdemo",
            "status":"1",
            "created_on":"2018-09-10 09:19:35",
            "details":{
                "timezone":"America/New_York",
                "country":{
                    "id":"2",
                    "name":"United States of America",
                    "abbreviation":"USA",
                    "abbreviation_2":"US",
                    "currency":"USD",
                    "currency_symbol":"$",
                    "date_format":"MDY",
                    "sms_prefix":"1"
                }
            }
          }
        """
        return self._request(ENDPOINTS.ACCOUNT_SUMMARY)

    def get_people(
        self, limit: int | None = None, offset: int | None = None, details: bool = False
    ) -> JsonValue:
        """List people from your database.

        Args:
          limit: Number of people to return. If None, will return all people.
          offset: Number of people to skip before beginning to return results.
                  Can be used in conjunction with limit for pagination.
          details: Option to return all information (slower) or just names.

        returns:
          JSON response. For example:
          {
            "id":"157857",
            "first_name":"Thomas",
            "last_name":"Anderson",
            "path":"img/profiles/generic/blue.jpg"
          },
          {
            "id":"157859",
            "first_name":"Kate",
            "last_name":"Austen",
            "path":"img/profiles/upload/2498d7f78s.jpg"
          },
          {
            ...
          }"""

        if (limit is not None and limit < 0) or (offset is not None and offset < 0):
            raise ValueError("limit and offset must be nonnegative.")
        params = []
        if limit is not None:
            params.append("limit={}".format(quote(str(limit), safe="")))
        if offset is not None:
            params.append("offset={}".format(quote(str(offset), safe="")))
        if details:
            params.append("details=1")
        return self._request("{}/?{}".format(ENDPOINTS.PEOPLE, "&".join(params)))

    def iter_people_records(
        self,
        *,
        page_size: int = 100,
        max_pages: int = 1000,
        max_items: int = 100_000,
        details: bool = False,
    ) -> Iterator[dict[str, JsonValue]]:
        """Bounded raw people traversal retaining vendor fields for exporters."""
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in (page_size, max_pages, max_items)
        ):
            raise ValueError("Pagination limits must be positive integers.")
        if self.dry_run:
            return
        seen: set[str] = set()
        offset = 0
        for _ in range(max_pages):
            response = self.get_people(limit=page_size, offset=offset, details=details)
            if not isinstance(response, list) or len(response) > page_size:
                raise BreezeResponseError("Invalid people page.")
            if not response:
                return
            page: list[tuple[Person, dict[str, JsonValue]]] = []
            for value in response:
                person = Person.from_json(value)
                if not isinstance(value, dict):
                    raise BreezeResponseError("Invalid people record.")
                page.append((person, value))
            for person, value in page:
                identifier = str(person.id)
                if identifier in seen:
                    raise BreezeResponseError("People pagination repeated an identifier.")
                if len(seen) >= max_items:
                    raise BreezeResponseError("People pagination item limit exceeded.")
                seen.add(identifier)
                yield value
            if len(page) < page_size:
                return
            offset += len(page)
        raise BreezeResponseError("People pagination page limit exceeded.")

    def iter_people(
        self,
        *,
        page_size: int = 100,
        max_pages: int = 1000,
        max_items: int = 100_000,
        details: bool = False,
    ) -> Iterator[Person]:
        """Yield validated people; consume completely before permitting writes.

        Offset pagination is not a snapshot of changing provider data. Raw
        fields remain available through iter_people_records for exporters.
        """
        for value in self.iter_people_records(
            page_size=page_size, max_pages=max_pages, max_items=max_items, details=details
        ):
            yield Person.from_json(value)

    def get_profile_fields(self) -> JsonValue:
        """List profile fields from your database.

        Returns:
          JSON response."""
        return self._request(ENDPOINTS.PROFILE_FIELDS)

    def get_person_details(self, person_id: Identifier) -> JsonValue:
        """Retrieve the details for a specific person by their ID.

        Args:
          person_id: Unique id for a person in Breeze database.

        Returns:
          JSON response."""
        if str(person_id) in {".", ".."}:
            raise BreezeError("Invalid person ID.")
        return self._request(f"{ENDPOINTS.PEOPLE}/{quote(str(person_id), safe='')}")

    def add_person(
        self, first_name: str, last_name: str, fields_json: str | None = None
    ) -> JsonValue:
        """Adds a new person into the database.

        Args:
          first_name: The first name of the person.
          last_name: The first name of the person.
          fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       ie. [ {
                               "field_id":"929778337",
                               "field_type":"email",
                               "response":"true",
                               "details":{
                                    "address": "tony@starkindustries.com",
                                    "is_private":1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already exist for a specific person.

        Returns:
          JSON response equivalent to get_person_details()."""

        params = []
        params.append("first={}".format(quote(str(first_name), safe="")))
        params.append("last={}".format(quote(str(last_name), safe="")))
        if fields_json:
            _validate_json_array(fields_json)
            params.append("fields_json={}".format(quote(str(fields_json), safe="")))

        return self._request("{}/add?{}".format(ENDPOINTS.PEOPLE, "&".join(params)))

    def update_person(self, person_id: Identifier, fields_json: str) -> JsonValue:
        """Updates the details for a specific person in the database.

        Args:
          person_id: Unique id for a person in Breeze database.
          fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       ie. [ {
                               "field_id":"929778337",
                               "field_type":"email",
                               "response":"true",
                               "details":{
                                    "address": "tony@starkindustries.com",
                                    "is_private":1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already exist for a specific person.


        Returns:
          JSON response equivalent to get_person_details(person_id)."""

        _validate_json_array(fields_json)
        return self._request(
            "{}/update?person_id={}&fields_json={}".format(
                ENDPOINTS.PEOPLE, quote(str(person_id), safe=""), quote(str(fields_json), safe="")
            )
        )

    def get_events(self, start_date: str | None = None, end_date: str | None = None) -> JsonValue:
        """Retrieve all events for a given date range.

        Args:
          start_date: Start date; defaults to first day of the current month.
          end_date: End date; defaults to last day of the current month

        Returns:
          JSON response."""
        params = []
        if start_date is not None:
            params.append("start={}".format(quote(str(start_date), safe="")))
        if end_date is not None:
            params.append("end={}".format(quote(str(end_date), safe="")))
        return self._request("{}/?{}".format(ENDPOINTS.EVENTS, "&".join(params)))

    def add_event(
        self,
        name: str,
        start_date: str | int,
        end_date: str | int | None = None,
        all_day: bool | None = None,
        description: str | None = None,
        category_id: Identifier | None = None,
        event_id: Identifier | None = None,
    ) -> JsonValue:
        """Add event for a given date range.

        Args:
          name: Name of event
          start_date: Start datetimestamp (epoch time)
          end_date: End datetimestamp (epoch time)
          all_day: boolean
          description: description of event (default none)
          category id: which calendar your event is on (defaults to primary)
          event id: series id

        Returns:
          JSON response."""

        params = []
        if name:
            params.append("name={}".format(quote(str(name), safe="")))
        if start_date is not None:
            params.append("starts_on={}".format(quote(str(start_date), safe="")))
        if end_date is not None:
            params.append("ends_on={}".format(quote(str(end_date), safe="")))
        if all_day is not None:
            params.append(f"all_day={int(all_day)}")
        if description:
            params.append("description={}".format(quote(str(description), safe="")))
        if category_id:
            params.append("category_id={}".format(quote(str(category_id), safe="")))
        if event_id:
            params.append("event_id={}".format(quote(str(event_id), safe="")))
        return self._request("{}/add?{}".format(ENDPOINTS.EVENTS, "&".join(params)))

    def event_check_in(self, person_id: Identifier, event_instance_id: Identifier) -> JsonValue:
        """Checks in a person into an event.

        Args:
          person_id: id for a person in Breeze database.
          event_instance_id: id for event instance to check into.."""

        return self._request(
            "{}/attendance/add?person_id={}&instance_id={}".format(
                ENDPOINTS.EVENTS,
                quote(str(person_id), safe=""),
                quote(str(event_instance_id), safe=""),
            )
        )

    def event_check_out(self, person_id: Identifier, event_instance_id: Identifier) -> JsonValue:
        """Remove the attendance for a person checked into an event.

        Args:
          person_id: Breeze ID for a person in Breeze database.
          event_instance_id: id for event instance to check out (delete).

        Returns:
          Successful JSON response; BreezeError if check-out fails."""

        return self._request(
            "{}/attendance/delete?person_id={}&instance_id={}".format(
                ENDPOINTS.EVENTS,
                quote(str(person_id), safe=""),
                quote(str(event_instance_id), safe=""),
            )
        )

    def add_contribution(
        self,
        date: str | None = None,
        name: str | None = None,
        person_id: Identifier | None = None,
        uid: Identifier | None = None,
        processor: str | None = None,
        method: str | None = None,
        funds_json: str | None = None,
        amount: Amount | None = None,
        group: str | None = None,
        batch_number: Identifier | None = None,
        batch_name: str | None = None,
    ) -> Identifier | None:
        """Add a contribution to Breeze.

        Args:
          date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id  (ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to
                 help automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically
                          match the person to the correct profile.
                          (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name.
                      ie. [ {
                              'id':'12345',
                              'name':'General Fund',
                              'amount':'100.00'
                            },
                            {
                              'name':'Missions Fund',
                              'amount':'150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.

        Returns:
          Payment Id.

        Throws:
          BreezeError on failure to add contribution."""

        query = _giving_query(
            {
                "date": date,
                "name": name,
                "person_id": person_id,
                "uid": uid,
                "processor": processor,
                "method": method,
                "funds_json": funds_json,
                "amount": amount,
                "group": group,
                "batch_number": batch_number,
                "batch_name": batch_name,
            }
        )
        response = self._request(f"{ENDPOINTS.CONTRIBUTIONS}/add?{query}")
        return self._payment_id(response)

    def add_allocated_contribution(
        self,
        funds: Iterable[FundAllocation],
        *,
        date: str,
        person_id: Identifier | None = None,
        name: str | None = None,
        uid: Identifier | None = None,
        processor: str | None = None,
        method: str | None = None,
        group: str | None = None,
        batch_name: str | None = None,
    ) -> Identifier | None:
        """Serialize validated fund allocations and derive the exact total.

        Materialization is locally bounded to 1000 allocations. This helper
        does not select an account currency or round caller amounts.
        """
        allocations: list[FundAllocation] = []
        for allocation in funds:
            if len(allocations) >= 1000:
                raise ValueError("Fund allocation limit exceeded.")
            allocations.append(allocation)
        if not allocations:
            raise ValueError("At least one fund allocation is required.")
        integers = max(max(allocation.amount.adjusted() + 1, 1) for allocation in allocations)
        fractions = 0
        for allocation in allocations:
            exponent = allocation.amount.as_tuple().exponent
            if not isinstance(exponent, int):
                raise ValueError("Fund amounts must be finite.")
            fractions = max(fractions, -exponent)
        with localcontext() as context:
            context.prec = integers + fractions + len(str(len(allocations))) + 2
            total = sum((allocation.amount for allocation in allocations), Decimal(0))
        return self.add_contribution(
            date=date,
            person_id=person_id,
            name=name,
            uid=uid,
            processor=processor,
            method=method,
            group=group,
            batch_name=batch_name,
            funds_json=json.dumps([allocation.to_json() for allocation in allocations]),
            amount=format(total, "f"),
        )

    def edit_contribution(
        self,
        payment_id: Identifier | None = None,
        date: str | None = None,
        name: str | None = None,
        person_id: Identifier | None = None,
        uid: Identifier | None = None,
        processor: str | None = None,
        method: str | None = None,
        funds_json: str | None = None,
        amount: Amount | None = None,
        group: str | None = None,
        batch_number: Identifier | None = None,
        batch_name: str | None = None,
    ) -> Identifier | None:
        """Edit an existing contribution.

        Args:
          payment_id: The ID of the payment that should be modified.
          date: Date of transaction in DD-MM-YYYY format (ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id  (ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to
                 help automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically
                          match the person to the correct profile.
                          (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods (FMV), Stocks (FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name.
                      ie. [ {
                              'id':'12345',
                              'name':'General Fund',
                              'amount':'100.00'
                            },
                            {
                              'name':'Missions Fund',
                              'amount':'150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to edit contribution."""

        query = _giving_query(
            {
                "payment_id": payment_id,
                "date": date,
                "name": name,
                "person_id": person_id,
                "uid": uid,
                "processor": processor,
                "method": method,
                "funds_json": funds_json,
                "amount": amount,
                "group": group,
                "batch_number": batch_number,
                "batch_name": batch_name,
            }
        )
        response = self._request(f"{ENDPOINTS.CONTRIBUTIONS}/edit?{query}")
        return self._payment_id(response)

    def delete_contribution(self, payment_id: Identifier) -> Identifier | None:
        """Delete an existing contribution.

        Args:
          payment_id: The ID of the payment that should be deleted.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to delete contribution."""

        response = self._request(
            "{}/delete?payment_id={}".format(
                ENDPOINTS.CONTRIBUTIONS, quote(str(payment_id), safe="")
            )
        )
        return self._payment_id(response)

    def list_forms(self, is_archived: bool = False) -> JsonValue:
        """Discover active or archived forms using the published read endpoint."""
        return self._request(f"{ENDPOINTS.FORMS}/list_forms?is_archived={int(is_archived)}")

    def list_form_fields(self, form_id: Identifier) -> JsonValue:
        """Discover fields before interpreting form-entry responses."""
        return self._request(
            f"{ENDPOINTS.FORMS}/list_form_fields?form_id={quote(str(form_id), safe='')}"
        )

    def list_form_entries(self, form_id: Identifier, details: bool = False) -> JsonValue:
        """return entries for the given form

        Args:
          form_id:the ID of the form
          details: Option to return all information (slower) or just names.

        returns:
          JSON response. For example:
          [
        {
            "id":"11",
            "form_id":"15326",
            "created_on":"2021-03-09 13:04:02",
            "person_id":null,
            "response":{
                "45":{
                "id":"13",
                "oid":"1512",
                "first_name":"Zoe",
                "last_name":"Washburne",
                "created_on":"2021-03-09 13:04:03"
                },
                "46":"zwashburne@test.com",
                "47":"Red"
            }
            },
          ]"""

        params = []
        params.append("form_id={}".format(quote(str(form_id), safe="")))
        if details:
            params.append("details=1")
        return self._request("{}/list_form_entries?{}".format(ENDPOINTS.FORMS, "&".join(params)))

    def list_contributions(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        person_id: Identifier | None = None,
        include_family: bool = False,
        amount_min: Amount | None = None,
        amount_max: Amount | None = None,
        method_ids: Iterable[str] | None = None,
        fund_ids: Iterable[str] | None = None,
        envelope_number: Identifier | None = None,
        batches: Iterable[str] | None = None,
        forms: Iterable[str] | None = None,
    ) -> JsonValue:
        """Retrieve a list of contributions.

        Args:
          start_date: Find contributions given on or after a specific date
                      (ie. 2015-1-1); required.
          end_date: Find contributions given on or before a specific date
                    (ie. 2018-1-31); required.
          person_id: ID of person's contributions to fetch. (ie. 9023482)
          include_family: Include family members of person_id (must provide
                          person_id); default: False.
          amount_min: Contribution amounts equal or greater than.
          amount_max: Contribution amounts equal or less than.
          method_ids: List of method IDs.
          fund_ids: List of fund IDs.
          envelope_number: Envelope number.
          batches: List of Batch numbers.
          forms: List of form IDs.

        Returns:
          List of matching contributions.

        Throws:
          BreezeError on malformed request."""

        params = []
        if start_date is not None:
            params.append("start={}".format(quote(str(start_date), safe="")))
        if end_date is not None:
            params.append("end={}".format(quote(str(end_date), safe="")))
        if person_id:
            params.append("person_id={}".format(quote(str(person_id), safe="")))
        if include_family:
            if not person_id:
                raise BreezeError("include_family requires a person_id.")
            params.append("include_family=1")
        if amount_min is not None:
            params.append("amount_min={}".format(quote(str(amount_min), safe="")))
        if amount_max is not None:
            params.append("amount_max={}".format(quote(str(amount_max), safe="")))
        if method_ids:
            params.append("method_ids={}".format(quote(str("-".join(method_ids)), safe="")))
        if fund_ids:
            params.append("fund_ids={}".format(quote(str("-".join(fund_ids)), safe="")))
        if envelope_number:
            params.append("envelope_number={}".format(quote(str(envelope_number), safe="")))
        if batches:
            params.append("batches={}".format(quote(str("-".join(batches)), safe="")))
        if forms:
            params.append("forms={}".format(quote(str("-".join(forms)), safe="")))
        return self._request("{}/list?{}".format(ENDPOINTS.CONTRIBUTIONS, "&".join(params)))

    def list_funds(self, include_totals: bool = False) -> JsonValue:
        """List all funds.

        Args:
          include_totals: Amount given to the fund should be returned.

        Returns:
          JSON Reponse."""

        params = []
        if include_totals:
            params.append("include_totals=1")
        return self._request("{}/list?{}".format(ENDPOINTS.FUNDS, "&".join(params)))

    def list_campaigns(self) -> JsonValue:
        """List of campaigns.

        Returns:
          JSON response."""
        return self._request(f"{ENDPOINTS.PLEDGES}/list_campaigns")

    def list_pledges(self, campaign_id: Identifier) -> JsonValue:
        """List of pledges within a campaign.

        Args:
          campaign_id: ID number of a campaign.

        Returns:
          JSON response."""
        return self._request(
            "{}/list_pledges?campaign_id={}".format(
                ENDPOINTS.PLEDGES, quote(str(campaign_id), safe="")
            )
        )

    def get_tags(self, folder: Identifier | None = None) -> JsonValue:
        """List of tags

        Args:
          folder: If set, only return tags in this folder id

        Returns:
          JSON response. For example:
            [
            {
                "id":"523928",
                "name":"4th & 5th",
                "created_on":"2018-09-10 09:19:40",
                "folder_id":"1539"
            },
            {
                "id":"51994",
                "name":"6th Grade",
                "created_on":"2018-02-06 06:40:40",
                "folder_id":"1539"
            },
            { ... }
            ]"""

        params = []
        if folder:
            params.append("folder_id={}".format(quote(str(folder), safe="")))
        return self._request("{}/{}/?{}".format(ENDPOINTS.TAGS, "list_tags", "&".join(params)))

    def get_tag_folders(self) -> JsonValue:
        """List of tag folders

        Args: (none)

        Returns:
          JSON response, for example:
             [
             {
                 "id":"1234567",
                 "parent_id":"0",
                 "name":"All Tags",
                 "created_on":"2018-06-05 18:12:34"
             },
             {
                 "id":"8234253",
                 "parent_id":"120425",
                 "name":"Kids",
                 "created_on":"2018-06-05 18:12:10"
             },
             {
                 "id":"1537253",
                 "parent_id":"5923042",
                 "name":"Small Groups",
                 "created_on":"2018-09-10 09:19:40"
             },
             {
                 "id":"20033",
                 "parent_id":"20031",
                 "name":"Student Ministries",
                 "created_on":"2018-12-15 18:11:31"
             }
             ]"""
        return self._request("{}/{}".format(ENDPOINTS.TAGS, "list_folders"))

    def assign_tag(self, person_id: Identifier, tag_id: Identifier) -> JsonValue:
        """
        Update a person's tag/s.

        params:

        person_id: an existing person's user id

        tag_id: the id number of the tag you want to assign to the user

        Returns successful JSON, or raises BreezeError on failure.
        """
        params = []

        params.append("person_id={}".format(quote(str(person_id), safe="")))

        params.append("tag_id={}".format(quote(str(tag_id), safe="")))

        response = self._request("{}/assign?{}".format(ENDPOINTS.TAGS, "&".join(params)))

        return response

    def unassign_tag(self, person_id: Identifier, tag_id: Identifier) -> JsonValue:
        """
        Delete a person's tag/s.

        params:

        person_id: an existing person's user id

        tag_id: the id number of the tag you want to assign to the user

        Returns successful JSON, or raises BreezeError on failure.
        """
        params = []

        params.append("person_id={}".format(quote(str(person_id), safe="")))

        params.append("tag_id={}".format(quote(str(tag_id), safe="")))

        response = self._request("{}/unassign?{}".format(ENDPOINTS.TAGS, "&".join(params)))

        return response
