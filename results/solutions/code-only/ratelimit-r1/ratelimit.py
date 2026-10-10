"""Per-key sliding-window rate limiter."""

import time
from collections import deque


class RateLimiter:
    """Allow up to ``max_calls`` successful calls per key in a sliding window.

    A hit recorded at time ``t`` is inside the window at time ``now`` when
    ``now - period_seconds < t <= now``. It ages out at ``now == t + period_seconds``.
    Denied calls do not consume quota. Keys are independent.
    """

    def __init__(self, max_calls: int, period_seconds: float, time_fn=None):
        if isinstance(max_calls, bool) or not isinstance(max_calls, int) or max_calls < 1:
            raise ValueError("max_calls must be an int greater than or equal to 1")
        if (
            isinstance(period_seconds, bool)
            or not isinstance(period_seconds, (int, float))
            or not period_seconds > 0
        ):
            raise ValueError("period_seconds must be a real number greater than 0")
        self._max_calls = max_calls
        self._period = period_seconds
        self._time_fn = time_fn
        self._hits: dict[str, deque] = {}
        self._max_observed = None

    def allow(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a str")

        now = time.monotonic() if self._time_fn is None else self._time_fn()
        # Any previously observed timestamp counts, including denied calls.
        if self._max_observed is not None and now < self._max_observed:
            raise ValueError("time moved backwards")
        self._max_observed = now

        hits = self._hits.get(key)
        if hits is None:
            hits = deque()
            self._hits[key] = hits

        # A hit at t is inside while t <= now < t + period. It ages out when
        # now == t + period_seconds. Oldest hits are a prefix.
        period = self._period
        while hits and hits[0] + period <= now:
            hits.popleft()

        if len(hits) < self._max_calls:
            hits.append(now)
            return True
        return False
