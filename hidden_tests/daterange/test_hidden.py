import datetime

import pytest

from daterange import intersection, ranges_overlap


def d(year, month, day):
    return datetime.date(year, month, day)


@pytest.mark.parametrize(
    "a, b, overlaps",
    [
        ((d(2024, 1, 1), d(2024, 1, 10)), (d(2024, 1, 1), d(2024, 1, 10)), True),
        ((d(2024, 1, 1), d(2024, 1, 10)), (d(2024, 1, 4), d(2024, 1, 5)), True),
        ((d(2024, 1, 1), d(2024, 1, 5)), (d(2024, 1, 5), d(2024, 1, 8)), True),
        ((d(2024, 5, 1), d(2024, 5, 1)), (d(2024, 5, 1), d(2024, 5, 1)), True),
        ((d(2024, 2, 28), d(2024, 3, 1)), (d(2024, 2, 29), d(2024, 2, 29)), True),
        ((d(2025, 12, 31), d(2026, 1, 2)), (d(2026, 1, 1), d(2026, 1, 3)), True),
        ((d(2024, 1, 1), d(2024, 1, 2)), (d(2024, 1, 3), d(2024, 1, 4)), False),
        ((d(2025, 12, 31), d(2025, 12, 31)), (d(2026, 1, 1), d(2026, 1, 1)), False),
        ((d(2024, 1, 3), d(2024, 1, 9)), (d(2024, 1, 1), d(2024, 1, 3)), True),
    ],
)
def test_overlap(a, b, overlaps):
    assert ranges_overlap(*a, *b) is overlaps


def test_intersection_partial():
    assert intersection(d(2024, 1, 1), d(2024, 1, 10), d(2024, 1, 5), d(2024, 1, 20)) == (
        d(2024, 1, 5),
        d(2024, 1, 10),
    )


def test_intersection_touch_is_one_day():
    assert intersection(d(2024, 1, 1), d(2024, 1, 2), d(2024, 1, 2), d(2024, 1, 4)) == (
        d(2024, 1, 2),
        d(2024, 1, 2),
    )


def test_intersection_none_when_disjoint():
    assert intersection(d(2024, 1, 1), d(2024, 1, 2), d(2024, 1, 3), d(2024, 1, 4)) is None


def test_reversed_range_raises():
    with pytest.raises(ValueError):
        ranges_overlap(d(2024, 1, 5), d(2024, 1, 1), d(2024, 1, 1), d(2024, 1, 2))
    with pytest.raises(ValueError):
        intersection(d(2024, 1, 1), d(2024, 1, 2), d(2024, 2, 1), d(2024, 1, 1))


def test_rejects_datetime_and_strings():
    moment = datetime.datetime(2024, 1, 1)
    with pytest.raises(TypeError):
        ranges_overlap(moment, moment, d(2024, 1, 1), d(2024, 1, 1))
    with pytest.raises(TypeError):
        intersection(d(2024, 1, 1), d(2024, 1, 2), "2024-01-01", "2024-01-02")
