# Per-key sliding-window rate limiter

Create `ratelimit.py` in the current directory with this class:

```python
class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: float, time_fn=None):
        ...
    def allow(self, key: str) -> bool:
        ...
```

Use only the Python standard library.

`max_calls` must be an `int` greater than or equal to 1. `period_seconds` must be a real number (`int` or `float`) greater than 0. Otherwise `__init__` raises `ValueError`. `time_fn` defaults to `time.monotonic` and returns seconds as a `float`. `allow` requires `key` to be a `str` and raises `TypeError` otherwise.

`allow(key)` returns `True` and records one hit at the current time when that key has fewer than `max_calls` hits still inside the window. Otherwise it returns `False` and records nothing. Denied calls do not consume quota. Keys are independent.

A hit recorded at time `t` is inside the window at time `now` when `now - period_seconds < t <= now`. The hit ages out at the exact moment `now == t + period_seconds`. Each successful call records its own hit, including when several calls observe the same timestamp.

If `time_fn()` moves backwards relative to any time previously observed by this instance, `allow` raises `ValueError` and records nothing for that call.
