"""LRU cache with a fixed per-entry time-to-live."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable


class LRUCache:
    """Capacity-bounded cache ordered by recency, with a half-open TTL.

    An entry written at time ``t`` is live while ``t <= now < t + ttl_seconds``.
    Recency and expiry are independent: ``get`` updates recency only, ``put``
    updates both.
    """

    def __init__(
        self,
        capacity: int,
        ttl_seconds: float,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be an int greater than or equal to 1")
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, (int, float))
            or not (ttl_seconds > 0)
        ):
            raise ValueError("ttl_seconds must be a real number greater than 0")
        self._capacity = capacity
        self._ttl = ttl_seconds
        self._time_fn = time.monotonic if time_fn is None else time_fn
        # Least-recently used at the front, most-recently used at the back.
        # Value is (value, written_at, expiry).
        self._entries: OrderedDict = OrderedDict()

    def get(self, key):
        now = self._time_fn()
        entry = self._entries.get(key)
        if entry is None or not _is_live(entry, now):
            raise KeyError(key)
        self._entries.move_to_end(key)
        return entry[0]

    def put(self, key, value):
        now = self._time_fn()
        self._entries[key] = (value, now, now + self._ttl)
        self._entries.move_to_end(key)
        # Expiry follows write time, not recency. An expired key can therefore
        # sit nearer the MRU end than a still-live key and must not take its slot.
        self._drop_nonlive(now)
        while len(self._entries) > self._capacity:
            self._entries.popitem(last=False)

    def __contains__(self, key) -> bool:
        now = self._time_fn()
        entry = self._entries.get(key)
        return entry is not None and _is_live(entry, now)

    def __len__(self) -> int:
        now = self._time_fn()
        return sum(1 for entry in self._entries.values() if _is_live(entry, now))

    def _drop_nonlive(self, now: float) -> None:
        stale = [key for key, entry in self._entries.items() if not _is_live(entry, now)]
        for key in stale:
            del self._entries[key]


def _is_live(entry, now: float) -> bool:
    _value, written_at, expiry = entry
    return written_at <= now < expiry
