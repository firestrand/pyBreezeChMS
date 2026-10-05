"""Sanitized, recoverable Breeze failures; raw causes remain internal."""


class BreezeError(Exception):
    """Base class retained for existing caller recovery contracts."""


class BreezeTransportError(BreezeError):
    """The outcome may be uncertain; never automatically replay a mutation."""


class BreezeDeadlineError(BreezeTransportError):
    """The operation exceeded its configured elapsed-time budget."""


class BreezeResponseError(BreezeError):
    """The provider response or JSON shape is invalid."""


class BreezeHttpError(BreezeError):
    """An HTTP status failure without a URL or response payload."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Breeze returned HTTP {status_code}.")


class BreezeAuthenticationError(BreezeHttpError):
    """Authentication or authorization was rejected."""


class BreezeRateLimitError(BreezeHttpError):
    """The provider quota was exceeded; no automatic retry was performed."""
