"""Per-key sliding-window rate limiter."""

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float, time_fn=None):
        if type(max_calls) is not int or max_calls < 1:
            raise ValueError("max_calls must be an int >= 1")
        if type(period_seconds) not in (int, float) or not (period_seconds > 0):
            raise ValueError("period_seconds must be a real number > 0")
        self._max_calls = max_calls
        self._period = period_seconds
        self._time_fn = time.monotonic if time_fn is None else time_fn
        self._hits: dict[str, deque[float]] = {}
        self._latest_observed: float | None = None

    def allow(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a str")
        now = self._time_fn()
        if self._latest_observed is not None and now < self._latest_observed:
            raise ValueError("time moved backwards")
        self._latest_observed = now

        hits = self._hits.get(key)
        if hits is None:
            hits = deque()
            self._hits[key] = hits
        else:
            # Inside the window when now - period < t <= now, so t <= cutoff is expired.
            cutoff = now - self._period
            while hits and hits[0] <= cutoff:
                hits.popleft()

        if len(hits) < self._max_calls:
            hits.append(now)
            return True
        return False
