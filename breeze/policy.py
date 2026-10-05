"""Small synchronous pacing/deadline policy for one coordinated account worker."""

import math
import threading
import time
from collections.abc import Callable

from .errors import BreezeDeadlineError


class RateLimiter:
    """Space attempts, including failed requests, using a monotonic clock.

    Share one limiter among clients accessing the same account. This coordinates
    threads within a process, not other processes/services using the same key.
    Clock/sleep injection enables deterministic tests without wall-clock waits.
    """

    def __init__(
        self,
        interval: float = 3.5,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if not math.isfinite(interval) or interval < 0:
            raise ValueError("Pacing interval must be finite and nonnegative.")
        self.interval = interval
        self.clock = time.monotonic if clock is None else clock
        self.sleep = time.sleep if sleep is None else sleep
        self._next: float | None = None
        self._lock = threading.Lock()

    def wait(self, deadline: float) -> None:
        """Wait for the next slot; never dispatch after the deadline."""
        with self._lock:
            now = self.clock()
            due = now if self._next is None else max(now, self._next)
            if due >= deadline:
                raise BreezeDeadlineError("Breeze deadline exceeded before request.")
            while now < due:
                self.sleep(due - now)
                now = self.clock()
                if now >= deadline:
                    raise BreezeDeadlineError("Breeze deadline exceeded before request.")
            self._next = now + self.interval

    def remaining(self, deadline: float) -> float:
        """Check elapsed budget at synchronous request/stream boundaries."""
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise BreezeDeadlineError("Breeze operation deadline exceeded.")
        return remaining


_limiters: dict[str, RateLimiter] = {}
_registry_lock = threading.Lock()


def account_limiter(host: str, api_key: str) -> RateLimiter:
    """Retain pacing across client lifetimes without plaintext credentials.

    The bounded registry coordinates up to 128 accounts for this process's
    lifetime. Larger deployments must inject explicitly shared limiters; never
    evict an account's state and silently reset its quota window.
    """
    # The host identifies the account. Rotating a key must not reset pacing,
    # and neither plaintext credentials nor their fingerprints are retained.
    identity = host
    with _registry_lock:
        limiter = _limiters.get(identity)
        if limiter is None:
            if len(_limiters) >= 128:
                raise ValueError("Account pacing registry is full; inject a shared RateLimiter.")
            limiter = RateLimiter()
            _limiters[identity] = limiter
        return limiter
