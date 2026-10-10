"""Behavioral tests for the per-key sliding-window RateLimiter."""

import inspect
import math
from decimal import Decimal
from fractions import Fraction

import pytest

from ratelimit import RateLimiter


class Clock:
    """Deterministic clock. Stays put until a test moves it."""

    def __init__(self, now: float = 0.0) -> None:
        self.now = float(now)

    def __call__(self) -> float:
        return self.now

    def set(self, now: float) -> None:
        self.now = float(now)

    def advance(self, delta: float) -> None:
        self.now += float(delta)


def make_limiter(
    max_calls: int,
    period_seconds: float,
    start: float = 0.0,
) -> tuple[RateLimiter, Clock]:
    clock = Clock(start)
    return RateLimiter(max_calls, period_seconds, clock), clock


class TestInit:
    def test_signature(self):
        init_params = list(inspect.signature(RateLimiter.__init__).parameters)
        assert init_params == ["self", "max_calls", "period_seconds", "time_fn"]
        assert inspect.signature(RateLimiter.__init__).parameters["time_fn"].default is None
        assert list(inspect.signature(RateLimiter.allow).parameters) == ["self", "key"]

    def test_minimum_int_arguments(self):
        limiter, _clock = make_limiter(1, 1)
        assert limiter.allow("k") is True

    def test_keyword_construction(self):
        clock = Clock(0.0)
        limiter = RateLimiter(max_calls=2, period_seconds=5, time_fn=clock)
        assert limiter.allow(key="k") is True

    def test_large_max_calls_and_tiny_period(self):
        limiter = RateLimiter(10**6, 1e-300, Clock(0.0))
        assert limiter.allow("k") is True

    def test_infinite_period_never_expires_hits(self):
        limiter, clock = make_limiter(1, float("inf"))
        assert limiter.allow("a") is True
        clock.set(1e300)
        assert limiter.allow("a") is False

    @pytest.mark.parametrize(
        "max_calls",
        [
            0,
            -1,
            -100,
            1.0,
            1.5,
            2.0,
            "1",
            None,
            b"1",
            [],
            (),
            {},
            Decimal(1),
            Fraction(1, 1),
            math.nan,
            math.inf,
        ],
    )
    def test_invalid_max_calls(self, max_calls):
        with pytest.raises(ValueError):
            RateLimiter(max_calls, 1.0)

    @pytest.mark.parametrize(
        "period",
        [
            0,
            0.0,
            -0.0,
            -1,
            -0.01,
            "1",
            None,
            b"1",
            [],
            Decimal("1.0"),
            Fraction(1, 1),
            math.nan,
            float("-inf"),
            complex(1, 0),
        ],
    )
    def test_invalid_period(self, period):
        with pytest.raises(ValueError):
            RateLimiter(1, period)

    def test_missing_required_arguments(self):
        with pytest.raises(TypeError):
            RateLimiter()
        with pytest.raises(TypeError):
            RateLimiter(1)

    def test_default_time_fn_is_monotonic(self):
        limiter = RateLimiter(1, 3600.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False

    def test_explicit_none_time_fn_uses_default_clock(self):
        limiter = RateLimiter(1, 3600.0, None)
        assert limiter.allow("k") is True
        assert limiter.allow(key="k") is False


class TestKeyType:
    @pytest.mark.parametrize(
        "key",
        [None, 0, 1, 1.0, b"k", bytearray(b"k"), ["k"], ("k",), object()],
    )
    def test_non_str_raises_type_error(self, key):
        limiter, _clock = make_limiter(1, 10.0)
        with pytest.raises(TypeError):
            limiter.allow(key)

    def test_distinct_strings_are_independent_keys(self):
        limiter, _clock = make_limiter(1, 10.0)
        for key in ("", " ", "a", "A", "é", "key with spaces"):
            assert limiter.allow(key) is True
        for key in ("", " ", "a", "A", "é", "key with spaces"):
            assert limiter.allow(key) is False


class TestWindow:
    def test_allows_until_max_calls_then_denies(self):
        limiter, _clock = make_limiter(3, 10.0)
        assert [limiter.allow("a") for _ in range(5)] == [True, True, True, False, False]

    def test_same_timestamp_records_separate_hits(self):
        limiter, _clock = make_limiter(3, 5.0, start=2.0)
        assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]

    def test_hit_ages_out_at_exact_period_boundary(self):
        limiter, clock = make_limiter(1, 10)
        assert limiter.allow("k") is True
        clock.set(9.0)
        assert limiter.allow("k") is False
        clock.set(10.0)
        assert limiter.allow("k") is True

    def test_hit_still_inside_just_before_period_boundary(self):
        limiter, clock = make_limiter(1, 1.0)
        assert limiter.allow("k") is True
        clock.set(math.nextafter(1.0, 0.0))
        assert limiter.allow("k") is False
        clock.set(1.0)
        assert limiter.allow("k") is True

    def test_denied_call_does_not_consume_quota(self):
        limiter, clock = make_limiter(1, 10.0)
        assert limiter.allow("k") is True
        clock.set(5.0)
        assert limiter.allow("k") is False
        # A hit stored at t=5 would still be inside the window at t=10.
        clock.set(10.0)
        assert limiter.allow("k") is True

    def test_window_slides_one_hit_at_a_time(self):
        limiter, clock = make_limiter(2, 10.0)
        assert limiter.allow("k") is True
        clock.set(3.0)
        assert limiter.allow("k") is True
        clock.set(6.0)
        assert limiter.allow("k") is False
        clock.set(9.0)
        assert limiter.allow("k") is False
        clock.set(10.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        clock.set(13.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False

    def test_identical_timestamps_expire_together(self):
        limiter, clock = make_limiter(3, 5.0, start=1.5)
        assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]
        clock.set(6.5)
        assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]

    def test_only_expired_hits_are_dropped(self):
        limiter, clock = make_limiter(3, 10.0)
        clock.set(0.0)
        assert limiter.allow("k") is True
        clock.set(1.0)
        assert limiter.allow("k") is True
        clock.set(2.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        clock.set(10.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        clock.set(11.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        clock.set(12.0)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False

    def test_dyadic_float_period_boundary(self):
        limiter, clock = make_limiter(1, 0.25)
        assert limiter.allow("k") is True
        clock.set(0.125)
        assert limiter.allow("k") is False
        clock.set(0.25)
        assert limiter.allow("k") is True

    def test_int_period_boundary(self):
        clock = Clock(0.0)
        limiter = RateLimiter(max_calls=2, period_seconds=5, time_fn=clock)
        assert limiter.allow(key="k") is True
        clock.set(4.0)
        assert limiter.allow(key="k") is True
        clock.set(5.0)
        assert limiter.allow(key="k") is True
        assert limiter.allow(key="k") is False

    def test_full_quota_returns_after_every_hit_expires(self):
        limiter, clock = make_limiter(3, 10.0, start=2.0)
        assert [limiter.allow("k") for _ in range(3)] == [True, True, True]
        clock.set(100.0)
        assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]

    def test_negative_timestamps(self):
        limiter, clock = make_limiter(1, 50.0, start=-100.0)
        assert limiter.allow("k") is True
        clock.set(-60.0)
        assert limiter.allow("k") is False
        clock.set(-50.0)
        assert limiter.allow("k") is True

    def test_keys_do_not_share_quota(self):
        limiter, clock = make_limiter(1, 10.0)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is True
        assert limiter.allow("a") is False
        assert limiter.allow("b") is False
        clock.set(10.0)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is True

    def test_keys_expire_on_their_own_timestamps(self):
        limiter, clock = make_limiter(1, 10.0)
        assert limiter.allow("a") is True
        clock.set(5.0)
        assert limiter.allow("b") is True
        clock.set(10.0)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is False
        clock.set(15.0)
        assert limiter.allow("b") is True

    def test_instances_are_independent(self):
        clock = Clock(0.0)
        first = RateLimiter(1, 10.0, clock)
        second = RateLimiter(1, 10.0, clock)
        assert first.allow("k") is True
        assert second.allow("k") is True
        assert first.allow("k") is False
        assert second.allow("k") is False

    def test_tiny_forward_step_keeps_the_hit(self):
        limiter, clock = make_limiter(1, 10.0, start=1.0)
        assert limiter.allow("k") is True
        clock.set(math.nextafter(1.0, 2.0))
        assert limiter.allow("k") is False

    def test_repeated_cycles_restore_the_full_budget(self):
        limiter, clock = make_limiter(2, 1.0)
        for second in range(40):
            clock.set(float(second))
            assert limiter.allow("k") is True
            assert limiter.allow("k") is True
            assert limiter.allow("k") is False


class TestBackwardsClock:
    def test_backwards_raises_and_does_not_record(self):
        limiter, clock = make_limiter(2, 100.0, start=10.0)
        assert limiter.allow("a") is True
        clock.set(4.0)
        with pytest.raises(ValueError):
            limiter.allow("a")
        clock.set(10.0)
        assert limiter.allow("a") is True
        assert limiter.allow("a") is False

    def test_backwards_attempt_does_not_lower_observed_time(self):
        limiter, clock = make_limiter(2, 1000.0, start=50.0)
        assert limiter.allow("a") is True
        clock.set(10.0)
        with pytest.raises(ValueError):
            limiter.allow("a")
        clock.set(30.0)
        with pytest.raises(ValueError):
            limiter.allow("b")
        clock.set(50.0)
        assert limiter.allow("b") is True
        assert limiter.allow("a") is True

    def test_denied_call_still_observes_time(self):
        limiter, clock = make_limiter(1, 100.0)
        assert limiter.allow("a") is True
        clock.set(40.0)
        assert limiter.allow("a") is False
        clock.set(20.0)
        with pytest.raises(ValueError):
            limiter.allow("b")
        clock.set(40.0)
        assert limiter.allow("b") is True

    def test_backwards_check_is_per_instance(self):
        clock = Clock(5.0)
        first = RateLimiter(1, 10.0, clock)
        assert first.allow("k") is True
        clock.set(1.0)
        second = RateLimiter(1, 10.0, clock)
        assert second.allow("k") is True
        with pytest.raises(ValueError):
            first.allow("k")

    def test_equal_timestamp_is_not_backwards(self):
        limiter, clock = make_limiter(2, 10.0, start=3.0)
        assert limiter.allow("k") is True
        clock.set(3.0)
        assert limiter.allow("k") is True
        clock.set(3.0)
        assert limiter.allow("k") is False

    def test_backwards_raises_even_when_quota_remains(self):
        limiter, clock = make_limiter(5, 10.0, start=1.0)
        assert limiter.allow("a") is True
        clock.set(math.nextafter(1.0, 0.0))
        with pytest.raises(ValueError):
            limiter.allow("a")
        clock.set(1.0)
        assert limiter.allow("a") is True

    def test_backwards_does_not_drop_existing_hits(self):
        limiter, clock = make_limiter(1, 100.0, start=50.0)
        assert limiter.allow("k") is True
        clock.set(10.0)
        with pytest.raises(ValueError):
            limiter.allow("k")
        clock.set(50.0)
        assert limiter.allow("k") is False
        clock.set(150.0)
        assert limiter.allow("k") is True

    def test_observed_time_is_global_across_keys(self):
        limiter, clock = make_limiter(1, 10.0)
        assert limiter.allow("a") is True
        clock.set(100.0)
        assert limiter.allow("b") is True
        clock.set(50.0)
        with pytest.raises(ValueError):
            limiter.allow("a")
        clock.set(100.0)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is False
