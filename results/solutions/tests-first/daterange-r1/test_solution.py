"""Tests for inclusive calendar-date overlap."""

import datetime
from datetime import date
from datetime import datetime as dt
from functools import total_ordering

import pytest

from daterange import intersection, ranges_overlap


class DateSubclass(date):
    """A date that is not a datetime. Instances of date are accepted."""


class DateTimeSubclass(dt):
    """A datetime subclass. Rejected because it is a datetime."""


@total_ordering
class OrdinalDay:
    """Ordered stand-in that is not a date. ISO-like ordering must not sneak through."""

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __eq__(self, other):
        if not isinstance(other, OrdinalDay):
            return NotImplemented
        return (self.year, self.month, self.day) == (other.year, other.month, other.day)

    def __lt__(self, other):
        if not isinstance(other, OrdinalDay):
            return NotImplemented
        return (self.year, self.month, self.day) < (other.year, other.month, other.day)


def test_identical_ranges_overlap():
    assert ranges_overlap(
        date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 1), date(2024, 1, 10)
    ) is True


def test_partial_overlap_from_either_side():
    assert ranges_overlap(
        date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 5), date(2024, 1, 15)
    ) is True
    assert ranges_overlap(
        date(2024, 1, 5), date(2024, 1, 15), date(2024, 1, 1), date(2024, 1, 10)
    ) is True


def test_containment_overlaps():
    outer = (date(2024, 1, 1), date(2024, 1, 31))
    inner = (date(2024, 1, 10), date(2024, 1, 12))
    assert ranges_overlap(*outer, *inner) is True
    assert ranges_overlap(*inner, *outer) is True


def test_endpoint_meeting_overlaps_on_that_day():
    assert ranges_overlap(
        date(2024, 3, 1), date(2024, 3, 10), date(2024, 3, 10), date(2024, 3, 20)
    ) is True
    assert ranges_overlap(
        date(2024, 3, 10), date(2024, 3, 20), date(2024, 3, 1), date(2024, 3, 10)
    ) is True


def test_next_day_after_end_does_not_overlap():
    assert ranges_overlap(
        date(2024, 3, 1), date(2024, 3, 10), date(2024, 3, 11), date(2024, 3, 20)
    ) is False
    assert ranges_overlap(
        date(2024, 3, 11), date(2024, 3, 20), date(2024, 3, 1), date(2024, 3, 10)
    ) is False


def test_disjoint_ranges_do_not_overlap():
    assert ranges_overlap(
        date(2020, 1, 1), date(2020, 6, 1), date(2021, 1, 1), date(2021, 6, 1)
    ) is False
    assert ranges_overlap(
        date(2021, 1, 1), date(2021, 6, 1), date(2020, 1, 1), date(2020, 6, 1)
    ) is False


def test_single_day_range_overlaps_itself():
    day = date(2024, 6, 15)
    assert ranges_overlap(day, day, day, day) is True


def test_single_day_on_and_inside_a_longer_range():
    start, end = date(2024, 1, 1), date(2024, 1, 31)
    assert ranges_overlap(start, end, start, start) is True
    assert ranges_overlap(start, end, end, end) is True
    assert ranges_overlap(start, end, date(2024, 1, 15), date(2024, 1, 15)) is True
    assert ranges_overlap(start, start, start, end) is True
    assert ranges_overlap(end, end, start, end) is True


def test_single_day_just_outside_a_longer_range():
    start, end = date(2024, 1, 1), date(2024, 1, 31)
    assert ranges_overlap(start, end, date(2023, 12, 31), date(2023, 12, 31)) is False
    assert ranges_overlap(start, end, date(2024, 2, 1), date(2024, 2, 1)) is False


def test_year_boundary_touch_and_gap():
    assert ranges_overlap(
        date(2023, 12, 1), date(2023, 12, 31), date(2024, 1, 1), date(2024, 1, 15)
    ) is False
    assert ranges_overlap(
        date(2023, 12, 1), date(2024, 1, 1), date(2024, 1, 1), date(2024, 1, 31)
    ) is True


def test_month_boundary_touch_and_gap():
    assert ranges_overlap(
        date(2024, 1, 1), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 10)
    ) is False
    assert ranges_overlap(
        date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 31), date(2024, 2, 10)
    ) is True


def test_leap_day_is_a_real_calendar_day():
    # 2024-02-28 and 2024-03-01 have 2024-02-29 between them, so they do not meet.
    assert ranges_overlap(
        date(2024, 2, 1), date(2024, 2, 28), date(2024, 3, 1), date(2024, 3, 10)
    ) is False
    # 2024-02-29 and 2024-03-01 are consecutive: meeting the next day is not overlap.
    assert ranges_overlap(
        date(2024, 2, 1), date(2024, 2, 29), date(2024, 3, 1), date(2024, 3, 10)
    ) is False
    # Sharing the leap day itself is overlap, including a one-day range on that day.
    assert ranges_overlap(
        date(2024, 2, 1), date(2024, 2, 29), date(2024, 2, 29), date(2024, 3, 10)
    ) is True
    assert ranges_overlap(
        date(2024, 2, 29), date(2024, 2, 29), date(2024, 2, 1), date(2024, 3, 1)
    ) is True
    assert ranges_overlap(
        date(2024, 2, 29), date(2024, 2, 29), date(2024, 3, 1), date(2024, 3, 1)
    ) is False


def test_non_leap_feb28_and_mar1_are_consecutive_and_do_not_overlap():
    assert ranges_overlap(
        date(2023, 2, 1), date(2023, 2, 28), date(2023, 3, 1), date(2023, 3, 10)
    ) is False
    assert ranges_overlap(
        date(2023, 2, 28), date(2023, 2, 28), date(2023, 3, 1), date(2023, 3, 1)
    ) is False
    assert ranges_overlap(
        date(2023, 2, 1), date(2023, 2, 28), date(2023, 2, 28), date(2023, 3, 10)
    ) is True


def test_extremal_dates():
    lo, hi = date.min, date.max
    assert ranges_overlap(lo, lo, hi, hi) is False
    assert ranges_overlap(lo, hi, lo, lo) is True
    assert ranges_overlap(lo, hi, hi, hi) is True
    assert ranges_overlap(lo, hi, date(2024, 7, 4), date(2024, 7, 4)) is True
    assert ranges_overlap(lo, date(2020, 1, 1), date(2020, 1, 1), hi) is True


def test_overlap_is_symmetric_for_several_layouts():
    pairs = [
        (date(2024, 5, 1), date(2024, 5, 20), date(2024, 5, 10), date(2024, 6, 1)),
        (date(2024, 5, 1), date(2024, 5, 1), date(2024, 5, 1), date(2024, 5, 2)),
        (date(2024, 5, 1), date(2024, 5, 2), date(2024, 5, 3), date(2024, 5, 4)),
        (date.min, date(2000, 1, 1), date(2000, 1, 1), date.max),
    ]
    for a0, a1, b0, b1 in pairs:
        assert ranges_overlap(a0, a1, b0, b1) is ranges_overlap(b0, b1, a0, a1)


def test_partial_intersection_is_later_start_and_earlier_end():
    assert intersection(
        date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 5), date(2024, 1, 15)
    ) == (date(2024, 1, 5), date(2024, 1, 10))
    assert intersection(
        date(2024, 1, 5), date(2024, 1, 15), date(2024, 1, 1), date(2024, 1, 10)
    ) == (date(2024, 1, 5), date(2024, 1, 10))


def test_intersection_of_containment_is_the_inner_range():
    outer = (date(2024, 1, 1), date(2024, 12, 31))
    inner = (date(2024, 3, 1), date(2024, 3, 31))
    assert intersection(*outer, *inner) == inner
    assert intersection(*inner, *outer) == inner


def test_intersection_of_equal_ranges_is_the_range():
    span = (date(2024, 4, 1), date(2024, 4, 30))
    assert intersection(*span, *span) == span


def test_intersection_of_shared_endpoint_is_that_single_day():
    day = date(2024, 3, 10)
    assert intersection(
        date(2024, 3, 1), day, day, date(2024, 3, 20)
    ) == (day, day)
    assert intersection(
        day, date(2024, 3, 20), date(2024, 3, 1), day
    ) == (day, day)


def test_intersection_of_non_overlapping_ranges_is_none():
    assert intersection(
        date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 20)
    ) is None
    assert intersection(
        date(2024, 1, 11), date(2024, 1, 20), date(2024, 1, 1), date(2024, 1, 10)
    ) is None
    assert intersection(
        date(2024, 8, 1), date(2024, 8, 31), date(2024, 9, 1), date(2024, 9, 1)
    ) is None
    assert intersection(
        date(2020, 1, 1), date(2020, 1, 1), date(2020, 1, 2), date(2020, 12, 31)
    ) is None


def test_intersection_single_day_inside_range():
    day = date(2024, 8, 8)
    assert intersection(date(2024, 8, 1), date(2024, 8, 31), day, day) == (day, day)
    assert intersection(day, day, date(2024, 8, 1), date(2024, 8, 31)) == (day, day)


def test_intersection_across_leap_day_and_year_boundary():
    assert intersection(
        date(2024, 2, 28), date(2024, 3, 2), date(2024, 2, 29), date(2024, 2, 29)
    ) == (date(2024, 2, 29), date(2024, 2, 29))
    assert intersection(
        date(2023, 12, 15), date(2024, 1, 15), date(2023, 12, 31), date(2024, 1, 1)
    ) == (date(2023, 12, 31), date(2024, 1, 1))
    assert intersection(
        date(2023, 12, 1), date(2023, 12, 31), date(2024, 1, 1), date(2024, 1, 31)
    ) is None


def test_intersection_of_full_calendar_span():
    lo, hi = date.min, date.max
    day = date(1999, 12, 31)
    assert intersection(lo, hi, day, date(2000, 1, 1)) == (day, date(2000, 1, 1))
    assert intersection(lo, lo, hi, hi) is None
    assert intersection(lo, hi, hi, hi) == (hi, hi)
    assert intersection(lo, lo, lo, hi) == (lo, lo)


def test_intersection_result_contains_plain_dates():
    result = intersection(
        date(2024, 1, 1), date(2024, 1, 5), date(2024, 1, 3), date(2024, 1, 9)
    )
    assert isinstance(result, tuple)
    assert len(result) == 2
    start, end = result
    assert type(start) is date
    assert type(end) is date
    assert start <= end


def test_overlap_and_intersection_agree():
    samples = [
        (date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 10), date(2024, 1, 20)),
        (date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 20)),
        (date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 1), date(2024, 1, 31)),
        (date(2024, 5, 5), date(2024, 5, 5), date(2024, 5, 5), date(2024, 5, 5)),
        (date(2024, 5, 5), date(2024, 5, 5), date(2024, 5, 6), date(2024, 5, 6)),
        (date(2023, 12, 31), date(2024, 1, 2), date(2024, 1, 1), date(2024, 1, 31)),
        (date.min, date.max, date(1999, 12, 31), date(2000, 1, 1)),
        (date(2024, 2, 28), date(2024, 2, 28), date(2024, 2, 29), date(2024, 3, 1)),
        (date(2024, 1, 1), date(2024, 6, 30), date(2024, 6, 30), date(2024, 6, 30)),
        (date(2019, 1, 1), date(2019, 12, 31), date(2020, 1, 1), date(2020, 1, 1)),
    ]
    for a0, a1, b0, b1 in samples:
        hit = intersection(a0, a1, b0, b1)
        assert ranges_overlap(a0, a1, b0, b1) is (hit is not None)
        if hit is not None:
            start, end = hit
            assert start == max(a0, b0)
            assert end == min(a1, b1)
            assert start <= end


def test_keyword_arguments():
    assert ranges_overlap(
        a_start=date(2024, 1, 1),
        a_end=date(2024, 1, 2),
        b_start=date(2024, 1, 2),
        b_end=date(2024, 1, 3),
    ) is True
    assert intersection(
        b_end=date(2024, 1, 3),
        b_start=date(2024, 1, 2),
        a_end=date(2024, 1, 2),
        a_start=date(2024, 1, 1),
    ) == (date(2024, 1, 2), date(2024, 1, 2))


@pytest.mark.parametrize(
    "bad",
    [
        "2024-01-01",
        "2024-01-01T00:00:00",
        None,
        20240101,
        1.5,
        True,
        False,
        (2024, 1, 1),
        [2024, 1, 1],
        b"2024-01-01",
        datetime.time(0, 0),
        dt(2024, 1, 1),
        dt(2024, 1, 1, 0, 0, 0),
        dt(2024, 1, 1, 15, 30, tzinfo=datetime.timezone.utc),
        DateTimeSubclass(2024, 1, 1, 0, 0),
        OrdinalDay(2024, 1, 1),
    ],
)
@pytest.mark.parametrize("slot", [0, 1, 2, 3])
def test_each_argument_rejects_non_dates(bad, slot):
    args = [date(2024, 1, 1), date(2024, 1, 10), date(2024, 1, 5), date(2024, 1, 15)]
    args[slot] = bad
    with pytest.raises(TypeError):
        ranges_overlap(*args)
    with pytest.raises(TypeError):
        intersection(*args)


def test_datetimes_rejected_even_when_every_argument_is_a_datetime():
    a0 = dt(2024, 1, 1, 0, 0)
    a1 = dt(2024, 1, 10, 0, 0)
    b0 = dt(2024, 1, 5, 12, 0)
    b1 = dt(2024, 1, 15, 23, 59)
    with pytest.raises(TypeError):
        ranges_overlap(a0, a1, b0, b1)
    with pytest.raises(TypeError):
        intersection(a0, a1, b0, b1)


def test_iso_strings_rejected_even_when_every_argument_is_a_string():
    with pytest.raises(TypeError):
        ranges_overlap("2024-01-01", "2024-01-10", "2024-01-05", "2024-01-15")
    with pytest.raises(TypeError):
        intersection("2024-01-01", "2024-01-10", "2024-01-05", "2024-01-15")


def test_ordered_non_dates_rejected():
    a0, a1 = OrdinalDay(2024, 1, 1), OrdinalDay(2024, 1, 10)
    b0, b1 = OrdinalDay(2024, 1, 5), OrdinalDay(2024, 1, 15)
    with pytest.raises(TypeError):
        ranges_overlap(a0, a1, b0, b1)
    with pytest.raises(TypeError):
        intersection(a0, a1, b0, b1)


def test_date_subclass_is_accepted():
    start = DateSubclass(2024, 1, 1)
    end = DateSubclass(2024, 1, 10)
    other_start = DateSubclass(2024, 1, 5)
    other_end = DateSubclass(2024, 1, 20)
    assert ranges_overlap(start, end, other_start, other_end) is True
    assert intersection(start, end, other_start, other_end) == (other_start, end)


def test_date_subclass_mixes_with_plain_dates():
    a0 = date(2024, 1, 1)
    a1 = DateSubclass(2024, 1, 10)
    b0 = DateSubclass(2024, 1, 10)
    b1 = date(2024, 1, 20)
    assert ranges_overlap(a0, a1, b0, b1) is True
    assert intersection(a0, a1, b0, b1) == (date(2024, 1, 10), date(2024, 1, 10))


def test_inverted_range_raises_value_error_for_either_side():
    with pytest.raises(ValueError):
        ranges_overlap(date(2024, 1, 10), date(2024, 1, 1), date(2024, 2, 1), date(2024, 2, 2))
    with pytest.raises(ValueError):
        ranges_overlap(date(2024, 2, 1), date(2024, 2, 2), date(2024, 3, 10), date(2024, 3, 1))
    with pytest.raises(ValueError):
        intersection(date(2024, 1, 10), date(2024, 1, 1), date(2024, 2, 1), date(2024, 2, 2))
    with pytest.raises(ValueError):
        intersection(date(2024, 2, 1), date(2024, 2, 2), date(2024, 3, 10), date(2024, 3, 1))


def test_inverted_by_one_day_raises_value_error():
    day = date(2024, 4, 4)
    nxt = date(2024, 4, 5)
    with pytest.raises(ValueError):
        ranges_overlap(nxt, day, day, nxt)
    with pytest.raises(ValueError):
        intersection(day, nxt, nxt, day)


def test_both_ranges_inverted_raises_value_error():
    with pytest.raises(ValueError):
        ranges_overlap(
            date(2024, 5, 2), date(2024, 5, 1), date(2024, 5, 4), date(2024, 5, 3)
        )
    with pytest.raises(ValueError):
        intersection(
            date(2024, 5, 2), date(2024, 5, 1), date(2024, 5, 4), date(2024, 5, 3)
        )


def test_equal_endpoints_are_a_valid_single_day():
    day = date(2024, 4, 4)
    assert ranges_overlap(day, day, date(2024, 4, 1), date(2024, 4, 10)) is True
    assert intersection(day, day, date(2024, 4, 1), date(2024, 4, 10)) == (day, day)


def test_type_error_when_a_bad_type_accompanies_an_inverted_range():
    with pytest.raises(TypeError):
        ranges_overlap(date(2024, 5, 2), date(2024, 5, 1), "2024-05-01", date(2024, 5, 3))
    with pytest.raises(TypeError):
        intersection(dt(2024, 5, 10), date(2024, 5, 1), date(2024, 5, 3), date(2024, 5, 1))
    with pytest.raises(TypeError):
        ranges_overlap(date(2024, 5, 1), date(2024, 5, 2), date(2024, 5, 4), None)


def test_value_error_is_not_used_for_a_mere_gap():
    # A gap is a non-overlap, not an invalid range.
    assert ranges_overlap(
        date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 4), date(2024, 1, 5)
    ) is False
    assert intersection(
        date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 4), date(2024, 1, 5)
    ) is None
