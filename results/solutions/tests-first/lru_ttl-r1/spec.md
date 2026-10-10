# LRU cache with a time-to-live

Create `lru_ttl.py` in the current directory with this class:

```python
class LRUCache:
    def __init__(self, capacity: int, ttl_seconds: float, time_fn=None):
        ...
    def get(self, key):
        ...
    def put(self, key, value):
        ...
    def __contains__(self, key) -> bool:
        ...
    def __len__(self) -> int:
        ...
```

Use only the Python standard library.

`capacity` is the maximum number of unexpired entries and must be an `int` greater than or equal to 1. `ttl_seconds` is the lifetime of an entry and must be a real number greater than 0 (`int` or `float`). Otherwise `__init__` raises `ValueError`. `time_fn` is a zero-argument callable returning the current time in seconds. It defaults to `time.monotonic`.

An entry written at time `t` expires at `t + ttl_seconds`. The lifetime is half-open: the entry is live for `t <= now < t + ttl_seconds` and is already expired at the exact expiry time. Expired entries are invisible. They do not count toward `capacity`, `__contains__` is false for them, `__len__` does not count them, and `get` raises `KeyError` for them just as it does for a key that was never inserted.

`put(key, value)` inserts or replaces `key`. Values may be any object, including `None`. A put stores the value, sets expiry to `now + ttl_seconds`, and marks the key most recently used. Replacing an existing live key does not grow the number of entries. After the put, if more than `capacity` live entries remain, evict least-recently-used live entries until only `capacity` remain. Expired entries must not be evicted in preference to a live one and must not block a new key; drop them so they do not occupy capacity.

`get(key)` returns the stored value if the key is live. It raises `KeyError` if the key is missing or expired. A successful get marks that key most recently used and does not change its expiry time.

`__contains__` and `__len__` report live keys only. Neither changes recency or expiry.
