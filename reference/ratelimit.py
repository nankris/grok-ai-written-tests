import time


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float, time_fn=None):
        if isinstance(max_calls, bool) or not isinstance(max_calls, int) or max_calls < 1:
            raise ValueError("max_calls must be an int >= 1")
        if (
            isinstance(period_seconds, bool)
            or not isinstance(period_seconds, (int, float))
            or period_seconds <= 0
        ):
            raise ValueError("period_seconds must be a number > 0")
        self.max_calls = max_calls
        self.period_seconds = float(period_seconds)
        self.time_fn = time.monotonic if time_fn is None else time_fn
        self._hits: dict[str, list[float]] = {}
        self._last_now = None

    def allow(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be a str")
        now = self.time_fn()
        if self._last_now is not None and now < self._last_now:
            raise ValueError("time moved backwards")
        self._last_now = now
        window_start = now - self.period_seconds
        hits = [stamp for stamp in self._hits.get(key, []) if window_start < stamp <= now]
        if len(hits) >= self.max_calls:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True
