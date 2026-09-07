from __future__ import annotations

import time
from enum import Enum


class BreakerState(str, Enum):
    closed = "closed"      # normal operation
    open = "open"          # tripped — calls are short-circuited
    half_open = "half_open"  # cooldown elapsed, one trial call is allowed through


class CircuitBreaker:
    """Trips after N consecutive failures and stops making calls for a cooldown
    period — protects both our own retry budget and a struggling upstream API
    from being hammered by every new token that shows up during an outage."""

    def __init__(self, failure_threshold: int, cooldown_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> BreakerState:
        if self._opened_at is None:
            return BreakerState.closed
        if time.time() - self._opened_at >= self.cooldown_seconds:
            return BreakerState.half_open
        return BreakerState.open

    def allow(self) -> bool:
        return self.state != BreakerState.open

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold and self._opened_at is None:
            self._opened_at = time.time()
