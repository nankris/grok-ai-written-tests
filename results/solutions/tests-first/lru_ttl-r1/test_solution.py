"""Behavioral tests for LRUCache (capacity, TTL, recency)."""

import inspect
import math
import time
from fractions import Fraction

import pytest

from lru_ttl import LRUCache


class Clock:
    """Deterministic zero-argument clock. Time advances only when tests set it."""

    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now


def cache(capacity, ttl, now=0):
    clock = Clock(now)
    return LRUCache(capacity, ttl, clock), clock


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_signature_matches_spec():
    params = inspect.signature(LRUCache.__init__).parameters
    assert list(params) == ["self", "capacity", "ttl_seconds", "time_fn"]
    assert params["time_fn"].default is None


@pytest.mark.parametrize(
    "capacity,ttl",
    [
        (1, 1),
        (1, 1.0),
        (2, 0.5),
        (8, 1e-6),
        (10**6, 10**9),
        (1, 1e-300),
    ],
)
def test_init_accepts_valid_capacity_and_ttl(capacity, ttl):
    LRUCache(capacity, ttl, time_fn=lambda: 0)


@pytest.mark.parametrize(
    "capacity,ttl",
    [
        (0, 1),
        (-1, 1),
        (-100, 5),
        (1.0, 1),  # whole-valued float is still not an int
        (1.5, 1),
        (True, 1),
        (False, 1),
        ("2", 1),
        (None, 1),
        (b"1", 1),
        (Fraction(2), 1),
        (1, 0),
        (1, 0.0),
        (1, -0.0),
        (1, -1),
        (1, -0.1),
        (1, True),
        (1, False),
        (1, "1"),
        (1, None),
        (1, float("nan")),
        (1, float("-inf")),
        (1, 1 + 2j),
        (1, Fraction(1, 2)),
        (0, 0),
        (-3, -0.5),
        (1.2, float("nan")),
        (True, False),
    ],
)
def test_init_rejects_invalid_capacity_or_ttl(capacity, ttl):
    with pytest.raises(ValueError):
        LRUCache(capacity, ttl, time_fn=lambda: 0)


def test_init_does_not_require_time_fn_and_operations_work():
    store = LRUCache(2, 30.0)
    store.put("a", 1)
    assert store.get("a") == 1
    assert "a" in store
    assert len(store) == 1


def test_default_clock_advances_and_expires_entries():
    store = LRUCache(1, 0.05)
    store.put("a", "v")
    assert store.get("a") == "v"
    time.sleep(0.2)
    assert "a" not in store
    assert len(store) == 0
    with pytest.raises(KeyError):
        store.get("a")


def test_keyword_and_positional_construction():
    clock = Clock(0)
    store = LRUCache(capacity=1, ttl_seconds=5, time_fn=clock)
    store.put("k", "v")
    assert store.get("k") == "v"


# ---------------------------------------------------------------------------
# Basic map behavior
# ---------------------------------------------------------------------------


def test_empty_cache():
    store, _clock = cache(3, 10)
    assert len(store) == 0
    assert "missing" not in store
    assert None not in store
    with pytest.raises(KeyError):
        store.get("missing")


def test_put_get_round_trip_and_overwrite():
    store, _clock = cache(2, 10)
    assert store.put("a", 1) is None
    store.put("b", 2)
    assert store.get("a") == 1
    assert store.get("b") == 2
    store.put("a", 3)
    assert store.get("a") == 3
    assert len(store) == 2


def test_values_may_be_none_and_other_falsy_objects():
    store, _clock = cache(4, 10)
    store.put("none", None)
    store.put("zero", 0)
    store.put("false", False)
    store.put("empty", "")
    assert store.get("none") is None
    assert store.get("zero") == 0
    assert store.get("false") is False
    assert store.get("empty") == ""
    assert "none" in store
    assert len(store) == 4


def test_none_and_composite_keys_are_distinct():
    store, _clock = cache(4, 10)
    store.put(None, "nil")
    store.put(1, "int")
    store.put("1", "str")
    store.put((1, 2), "tuple")
    store.put("", "blank")
    # capacity 4: the first key is evicted when the fifth is inserted
    assert None not in store
    assert store.get(1) == "int"
    assert store.get("1") == "str"
    assert store.get((1, 2)) == "tuple"
    assert store.get("") == "blank"
    assert len(store) == 4


def test_stored_value_identity_is_preserved():
    store, _clock = cache(1, 10)
    payload = {"n": 1}
    store.put("a", payload)
    payload["n"] = 2
    assert store.get("a") is payload
    assert store.get("a")["n"] == 2


def test_unhashable_key_raises_type_error():
    store, _clock = cache(1, 10)
    with pytest.raises(TypeError):
        store.put(["not", "hashable"], 1)


def test_missing_get_does_not_insert():
    store, _clock = cache(1, 10)
    with pytest.raises(KeyError):
        store.get("a")
    assert len(store) == 0
    assert "a" not in store


# ---------------------------------------------------------------------------
# TTL half-open interval: inserted_at <= now < inserted_at + ttl
# ---------------------------------------------------------------------------


def test_live_at_insertion_instant_and_just_before_expiry():
    store, clock = cache(1, 5, now=10)
    store.put("a", "v")
    assert store.get("a") == "v"
    assert "a" in store
    assert len(store) == 1

    clock.now = 14
    assert store.get("a") == "v"

    # Insertion at 10 and ttl 5 expire at exactly 15. The previous float is live.
    clock.now = math.nextafter(15.0, 0.0)
    assert store.get("a") == "v"
    assert "a" in store
    assert len(store) == 1

    clock.now = 15
    assert "a" not in store
    assert len(store) == 0
    with pytest.raises(KeyError):
        store.get("a")


def test_float_ttl_inclusive_start_exclusive_end():
    store, clock = cache(1, 1.5, now=0.0)
    store.put("a", "v")
    assert "a" in store

    clock.now = math.nextafter(1.5, 0.0)
    assert store.get("a") == "v"
    assert "a" in store
    assert len(store) == 1

    clock.now = 1.5
    assert "a" not in store
    assert len(store) == 0
    with pytest.raises(KeyError):
        store.get("a")

    clock.now = 1.5 + 10.0
    assert "a" not in store
    with pytest.raises(KeyError):
        store.get("a")


def test_exact_expiry_is_already_dead_for_int_timeline():
    store, clock = cache(1, 10, now=0)
    store.put("a", 1)
    clock.now = 9
    assert store.get("a") == 1
    clock.now = 10
    assert "a" not in store
    assert len(store) == 0
    with pytest.raises(KeyError):
        store.get("a")


def test_tiny_and_huge_ttl_boundaries():
    tiny, tiny_clock = cache(1, 1e-300, now=0.0)
    tiny.put("a", 1)
    assert tiny.get("a") == 1
    tiny_clock.now = 1e-300
    with pytest.raises(KeyError):
        tiny.get("a")

    huge, huge_clock = cache(1, 10**18, now=0)
    huge.put("a", 1)
    huge_clock.now = 10**18 - 1
    assert huge.get("a") == 1
    assert len(huge) == 1
    huge_clock.now = 10**18
    assert "a" not in huge
    assert len(huge) == 0
    with pytest.raises(KeyError):
        huge.get("a")


def test_each_key_expires_on_its_own_write_time():
    store, clock = cache(4, 10, now=0)
    store.put("early", 1)
    clock.now = 4
    store.put("later", 2)
    clock.now = 10
    assert "early" not in store
    assert store.get("later") == 2
    assert len(store) == 1
    clock.now = 14
    assert "later" not in store
    assert len(store) == 0


def test_expired_key_is_indistinguishable_from_missing_until_rewritten():
    store, clock = cache(2, 5, now=0)
    store.put("a", 1)
    store.put("b", 2)
    clock.now = 5
    assert "a" not in store
    assert "b" not in store
    assert len(store) == 0
    with pytest.raises(KeyError):
        store.get("a")
    with pytest.raises(KeyError):
        store.get("never")

    clock.now = 5
    store.put("a", 9)
    assert store.get("a") == 9
    assert "b" not in store
    assert len(store) == 1
    clock.now = 9
    assert store.get("a") == 9
    clock.now = 10
    assert "a" not in store


# ---------------------------------------------------------------------------
# Successful get refreshes recency only, not expiry
# ---------------------------------------------------------------------------


def test_get_does_not_extend_expiry():
    store, clock = cache(1, 10, now=0)
    store.put("a", 1)
    clock.now = 9
    assert store.get("a") == 1
    clock.now = 9
    assert store.get("a") == 1
    clock.now = 10
    with pytest.raises(KeyError):
        store.get("a")


def test_contains_and_len_do_not_extend_expiry():
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)
    store.put("b", 2)
    clock.now = 9
    assert "a" in store
    assert "b" in store
    assert len(store) == 2
    assert len(store) == 2
    clock.now = 10
    assert "a" not in store
    assert "b" not in store
    assert len(store) == 0


def test_failed_get_does_not_revive_or_extend_expired_key():
    store, clock = cache(1, 10, now=0)
    store.put("a", 1)
    clock.now = 10
    with pytest.raises(KeyError):
        store.get("a")
    clock.now = 10
    assert "a" not in store
    assert len(store) == 0


# ---------------------------------------------------------------------------
# Recency and eviction
# ---------------------------------------------------------------------------


def test_put_beyond_capacity_evicts_least_recently_used():
    store, _clock = cache(2, 100)
    store.put("a", 1)
    store.put("b", 2)
    store.put("c", 3)
    assert "a" not in store
    assert store.get("b") == 2
    assert store.get("c") == 3
    assert len(store) == 2


def test_same_timestamp_evicts_in_insertion_order():
    store, _clock = cache(2, 100, now=5)
    store.put("a", 1)
    store.put("b", 2)
    store.put("c", 3)
    store.put("d", 4)
    assert "a" not in store
    assert "b" not in store
    assert store.get("c") == 3
    assert store.get("d") == 4
    assert len(store) == 2


def test_get_marks_key_most_recently_used():
    store, _clock = cache(2, 100)
    store.put("a", 1)
    store.put("b", 2)
    assert store.get("a") == 1  # a is now MRU; b is LRU
    store.put("c", 3)
    assert "b" not in store
    assert store.get("a") == 1
    assert store.get("c") == 3
    assert len(store) == 2


def test_contains_does_not_change_recency():
    store, _clock = cache(2, 100)
    store.put("a", 1)
    store.put("b", 2)
    assert "a" in store
    assert "a" in store
    store.put("c", 3)
    assert "a" not in store
    assert store.get("b") == 2
    assert store.get("c") == 3


def test_len_does_not_change_recency():
    store, _clock = cache(2, 100)
    store.put("a", 1)
    store.put("b", 2)
    assert len(store) == 2
    assert len(store) == 2
    store.put("c", 3)
    assert "a" not in store
    assert "b" in store
    assert "c" in store


def test_failed_get_does_not_change_recency():
    store, _clock = cache(2, 100)
    store.put("a", 1)
    store.put("b", 2)
    with pytest.raises(KeyError):
        store.get("missing")
    store.put("c", 3)
    assert "a" not in store
    assert store.get("b") == 2
    assert store.get("c") == 3


def test_get_of_expired_key_does_not_change_recency_of_live_keys():
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)  # expires at 10
    clock.now = 3
    store.put("b", 2)  # expires at 13; order [a, b]
    clock.now = 3
    assert store.get("a") == 1  # order [b, a], a still expires at 10
    clock.now = 10  # a expired, b live
    with pytest.raises(KeyError):
        store.get("a")
    store.put("c", 3)
    # a must not occupy a slot or become MRU. b stays.
    assert "a" not in store
    assert store.get("b") == 2
    assert store.get("c") == 3
    assert len(store) == 2


def test_replacing_live_key_refreshes_value_expiry_and_recency_without_growing():
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)
    store.put("b", 2)
    clock.now = 6
    store.put("a", 7)  # a refreshed, expires at 16; order [b, a]
    assert store.get("a") == 7
    assert len(store) == 2
    store.put("c", 3)  # evicts b, not a
    assert "b" not in store
    assert store.get("a") == 7
    assert store.get("c") == 3

    clock.now = 15  # original a expiry (10) has passed; refreshed expiry is 16
    assert store.get("a") == 7
    clock.now = 16
    assert "a" not in store
    # c was written at t=6 and expires at 16 as well
    assert "c" not in store


def test_replace_does_not_evict_other_entries_when_at_capacity():
    store, _clock = cache(2, 50)
    store.put("a", 1)
    store.put("b", 2)
    store.put("a", 3)
    store.put("b", 4)
    assert store.get("a") == 3
    assert store.get("b") == 4
    assert len(store) == 2


def test_capacity_one_keeps_only_newest():
    store, clock = cache(1, 20, now=0)
    store.put("a", 1)
    store.put("b", 2)
    assert "a" not in store
    assert store.get("b") == 2
    assert len(store) == 1
    clock.now = 5
    assert store.get("b") == 2  # b becomes MRU (already the only entry)
    store.put("c", 3)
    assert "b" not in store
    assert store.get("c") == 3
    assert len(store) == 1


def test_recency_chain_evicts_the_current_lru_only():
    store, _clock = cache(3, 100)
    store.put("a", 1)
    store.put("b", 2)
    store.put("c", 3)
    store.get("a")  # order: b, c, a
    store.get("c")  # order: b, a, c
    store.put("d", 4)  # evict b; order: a, c, d
    assert "b" not in store
    assert store.get("a") == 1  # order: c, d, a
    store.put("e", 5)  # evict c
    assert "c" not in store
    assert "a" in store
    assert "d" in store
    assert "e" in store
    assert len(store) == 3


def test_only_one_lru_entry_is_evicted_per_insert_when_full():
    store, _clock = cache(3, 100)
    for key in ("a", "b", "c"):
        store.put(key, key)
    store.put("d", "d")
    assert "a" not in store
    assert [k for k in ("b", "c", "d") if k in store] == ["b", "c", "d"]
    assert len(store) == 3


# ---------------------------------------------------------------------------
# Expired entries do not occupy capacity
# ---------------------------------------------------------------------------


def test_expired_entries_do_not_block_new_keys():
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)
    store.put("b", 2)
    clock.now = 10
    store.put("c", 3)
    store.put("d", 4)
    assert "a" not in store
    assert "b" not in store
    assert store.get("c") == 3
    assert store.get("d") == 4
    assert len(store) == 2


def test_partial_expiry_frees_a_slot_without_evicting_the_live_key():
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)  # expires 10
    clock.now = 5
    store.put("b", 2)  # expires 15
    clock.now = 10
    assert "a" not in store
    assert "b" in store
    assert len(store) == 1
    store.put("c", 3)
    assert store.get("b") == 2
    assert store.get("c") == 3
    assert "a" not in store
    assert len(store) == 2


def test_expired_middle_entry_is_not_kept_in_preference_to_a_live_lru():
    """A live LRU must survive a put when the only other occupant is expired.

    Recency order before the final put is [b live, a expired]. A buggy
    eviction that treats the expired entry as occupying capacity would evict
    live b to make room.
    """
    store, clock = cache(2, 10, now=0)
    store.put("a", 1)  # expires 10
    clock.now = 3
    store.put("b", 2)  # expires 13; order [a, b]
    assert store.get("a") == 1  # order [b, a]; a still expires at 10
    clock.now = 10
    assert "a" not in store
    assert "b" in store
    store.put("c", 3)
    assert "a" not in store
    assert store.get("b") == 2
    assert store.get("c") == 3
    assert len(store) == 2


def test_several_expired_entries_free_every_slot_they_held():
    store, clock = cache(3, 5, now=0)
    store.put("a", 1)
    store.put("b", 2)
    store.put("c", 3)
    clock.now = 5
    assert len(store) == 0
    store.put("d", 4)
    store.put("e", 5)
    store.put("f", 6)
    assert store.get("d") == 4
    assert store.get("e") == 5
    assert store.get("f") == 6
    assert len(store) == 3
    for gone in ("a", "b", "c"):
        assert gone not in store


def test_mix_of_expired_and_live_then_fill_back_to_capacity():
    store, clock = cache(3, 10, now=0)
    store.put("a", 1)
    store.put("b", 2)
    clock.now = 4
    store.put("c", 3)  # expires 14
    clock.now = 10
    assert len(store) == 1
    assert store.get("c") == 3
    store.put("d", 4)
    store.put("e", 5)
    assert "a" not in store
    assert "b" not in store
    assert "c" in store
    assert "d" in store
    assert "e" in store
    assert len(store) == 3
    # contains above must not move c. Insertion order is c, d, e, so c is LRU.
    store.put("f", 6)
    assert "c" not in store
    assert store.get("d") == 4
    assert store.get("e") == 5
    assert store.get("f") == 6
    assert len(store) == 3


def test_len_and_contains_ignore_expired_without_needing_a_put():
    store, clock = cache(3, 8, now=0)
    store.put("a", 1)
    clock.now = 2
    store.put("b", 2)
    clock.now = 3
    store.put("c", 3)
    clock.now = 8
    assert len(store) == 2
    assert "a" not in store
    assert "b" in store
    assert "c" in store
    clock.now = 10
    assert len(store) == 1
    assert "b" not in store
    assert store.get("c") == 3
    clock.now = 11
    assert len(store) == 0
    assert "c" not in store


def test_rewrite_of_expired_key_counts_as_a_new_live_entry():
    store, clock = cache(1, 4, now=0)
    store.put("a", 1)
    clock.now = 4
    assert "a" not in store
    store.put("a", 2)
    assert store.get("a") == 2
    assert len(store) == 1
    clock.now = 7
    assert store.get("a") == 2
    clock.now = 8
    assert "a" not in store


def test_overwriting_live_key_with_none_refreshes_expiry():
    store, clock = cache(1, 5, now=0)
    store.put("a", 1)
    clock.now = 4
    store.put("a", None)
    clock.now = 8
    assert store.get("a") is None
    clock.now = 9
    with pytest.raises(KeyError):
        store.get("a")


def test_put_after_full_expiry_then_lru_among_new_entries():
    store, clock = cache(2, 3, now=0)
    store.put("old1", 1)
    store.put("old2", 2)
    clock.now = 3
    store.put("n1", 1)
    store.put("n2", 2)
    store.put("n3", 3)
    assert "old1" not in store
    assert "old2" not in store
    assert "n1" not in store
    assert store.get("n2") == 2
    assert store.get("n3") == 3


def test_time_fn_is_honored_and_int_timestamps_work_with_float_ttl():
    store, clock = cache(1, 2.5, now=0)
    store.put("a", "v")
    clock.now = 2
    assert store.get("a") == "v"
    clock.now = 2.5
    assert "a" not in store

    store2, clock2 = cache(1, 4, now=1.25)
    store2.put("b", 7)
    clock2.now = math.nextafter(5.25, 0.0)
    assert store2.get("b") == 7
    clock2.now = 5.25
    with pytest.raises(KeyError):
        store2.get("b")


def test_many_inserts_keep_exactly_the_most_recent_window():
    store, _clock = cache(5, 1000)
    for i in range(30):
        store.put(i, i * 10)
    assert len(store) == 5
    for i in range(25):
        assert i not in store
        with pytest.raises(KeyError):
            store.get(i)
    for i in range(25, 30):
        assert store.get(i) == i * 10
    # touch the oldest survivor so the next insert evicts the following one
    assert store.get(25) == 250
    store.put(30, 300)
    assert 26 not in store
    assert store.get(25) == 250
    assert store.get(30) == 300
    assert len(store) == 5
