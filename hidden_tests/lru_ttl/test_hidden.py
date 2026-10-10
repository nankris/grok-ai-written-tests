import pytest

from lru_ttl import LRUCache


class Clock:
    def __init__(self, now=0.0):
        self.now = float(now)

    def __call__(self):
        return self.now


def test_put_get_and_missing():
    clock = Clock()
    cache = LRUCache(2, 10, time_fn=clock)
    cache.put("a", 1)
    assert cache.get("a") == 1
    with pytest.raises(KeyError):
        cache.get("missing")


def test_none_value_is_stored():
    clock = Clock()
    cache = LRUCache(1, 5, time_fn=clock)
    cache.put("k", None)
    assert "k" in cache
    assert cache.get("k") is None


def test_capacity_evicts_least_recently_used():
    clock = Clock()
    cache = LRUCache(2, 100, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert len(cache) == 2


def test_get_refreshes_recency_only():
    clock = Clock()
    cache = LRUCache(2, 10, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    clock.now = 4
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert "b" not in cache
    assert cache.get("a") == 1
    clock.now = 10
    with pytest.raises(KeyError):
        cache.get("a")


def test_contains_does_not_refresh_recency():
    clock = Clock()
    cache = LRUCache(2, 100, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache and "c" in cache


def test_len_does_not_refresh_recency():
    clock = Clock()
    cache = LRUCache(2, 100, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
    cache.put("c", 3)
    assert "a" not in cache


def test_put_refreshes_ttl_and_exact_expiry():
    clock = Clock()
    cache = LRUCache(2, 10, time_fn=clock)
    cache.put("a", 1)
    clock.now = 9.9
    assert cache.get("a") == 1
    clock.now = 10
    assert "a" not in cache
    assert len(cache) == 0
    clock.now = 0
    cache.put("b", 2)
    clock.now = 6
    cache.put("b", 3)
    clock.now = 15.9
    assert cache.get("b") == 3
    clock.now = 16
    with pytest.raises(KeyError):
        cache.get("b")


def test_expired_entry_does_not_consume_capacity():
    clock = Clock()
    cache = LRUCache(1, 5, time_fn=clock)
    cache.put("a", 1)
    clock.now = 5
    cache.put("b", 2)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert len(cache) == 1


def test_replace_existing_does_not_evict_neighbour():
    clock = Clock()
    cache = LRUCache(2, 10, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 3)
    assert cache.get("b") == 2
    assert cache.get("a") == 3
    assert len(cache) == 2


def test_bad_constructor_args():
    with pytest.raises(ValueError):
        LRUCache(0, 1)
    with pytest.raises(ValueError):
        LRUCache(1, 0)
    with pytest.raises(ValueError):
        LRUCache(1, -2)
    with pytest.raises(ValueError):
        LRUCache(1.5, 1)


def test_capacity_one_recency():
    clock = Clock()
    cache = LRUCache(1, 10, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" not in cache
    assert cache.get("b") == 2
