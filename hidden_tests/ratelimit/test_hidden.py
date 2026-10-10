import pytest

from ratelimit import RateLimiter


class Clock:
    def __init__(self, now=0.0):
        self.now = float(now)

    def __call__(self):
        return self.now


def test_allows_up_to_max_then_denies():
    clock = Clock()
    limiter = RateLimiter(2, 10, time_fn=clock)
    assert limiter.allow("a") is True
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False


def test_denied_call_does_not_consume_quota():
    clock = Clock()
    limiter = RateLimiter(1, 10, time_fn=clock)
    assert limiter.allow("a") is True
    clock.now = 5
    assert limiter.allow("a") is False
    clock.now = 10
    assert limiter.allow("a") is True


def test_exact_boundary_ages_out():
    clock = Clock()
    limiter = RateLimiter(1, 10, time_fn=clock)
    assert limiter.allow("a") is True
    clock.now = 9.999
    assert limiter.allow("a") is False
    clock.now = 10
    assert limiter.allow("a") is True


def test_partial_slide():
    clock = Clock()
    limiter = RateLimiter(3, 10, time_fn=clock)
    for stamp in (0, 1, 2):
        clock.now = stamp
        assert limiter.allow("a") is True
    clock.now = 10
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False


def test_keys_are_independent():
    clock = Clock()
    limiter = RateLimiter(1, 10, time_fn=clock)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False


def test_same_timestamp_counts_separately():
    clock = Clock()
    limiter = RateLimiter(2, 5, time_fn=clock)
    assert limiter.allow("a") is True
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False


def test_bad_constructor_args():
    with pytest.raises(ValueError):
        RateLimiter(0, 1)
    with pytest.raises(ValueError):
        RateLimiter(1, 0)
    with pytest.raises(ValueError):
        RateLimiter(2, -0.5)


def test_key_must_be_str():
    limiter = RateLimiter(1, 1, time_fn=Clock())
    with pytest.raises(TypeError):
        limiter.allow(1)  # type: ignore[arg-type]


def test_float_period_and_second_key_after_window():
    clock = Clock()
    limiter = RateLimiter(1, 2.5, time_fn=clock)
    assert limiter.allow("a") is True
    clock.now = 2.5
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True


def test_time_moving_backwards_raises_and_does_not_record():
    clock = Clock(5)
    limiter = RateLimiter(1, 10, time_fn=clock)
    assert limiter.allow("a") is True
    clock.now = 4
    with pytest.raises(ValueError):
        limiter.allow("b")
    clock.now = 5
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False
