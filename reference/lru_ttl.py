import time


class LRUCache:
    def __init__(self, capacity: int, ttl_seconds: float, time_fn=None):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be an int >= 1")
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, (int, float))
            or ttl_seconds <= 0
        ):
            raise ValueError("ttl_seconds must be a number > 0")
        self.capacity = capacity
        self.ttl_seconds = float(ttl_seconds)
        self.time_fn = time.monotonic if time_fn is None else time_fn
        self._entries: dict = {}
        self._seq = 0

    def _now(self):
        return self.time_fn()

    def _drop_if_expired(self, key, now) -> bool:
        entry = self._entries.get(key)
        if entry is None:
            return False
        if now >= entry[1]:
            del self._entries[key]
            return False
        return True

    def _purge(self, now) -> None:
        dead = [key for key, entry in self._entries.items() if now >= entry[1]]
        for key in dead:
            del self._entries[key]

    def get(self, key):
        now = self._now()
        if not self._drop_if_expired(key, now):
            raise KeyError(key)
        self._seq += 1
        self._entries[key][2] = self._seq
        return self._entries[key][0]

    def put(self, key, value) -> None:
        now = self._now()
        self._purge(now)
        self._seq += 1
        self._entries[key] = [value, now + self.ttl_seconds, self._seq]
        while len(self._entries) > self.capacity:
            lru_key = min(self._entries.items(), key=lambda item: item[1][2])[0]
            del self._entries[lru_key]

    def __contains__(self, key) -> bool:
        return self._drop_if_expired(key, self._now())

    def __len__(self) -> int:
        self._purge(self._now())
        return len(self._entries)
