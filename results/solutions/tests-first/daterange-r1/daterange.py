"""Inclusive calendar-date overlap for two ranges of datetime.date values."""

import datetime


def _require_date(value: object) -> datetime.date:
    """Accept datetime.date, including subclasses, and reject datetime.datetime.

    datetime.datetime is a subclass of datetime.date, so an isinstance check
    against date alone would accept timestamps. Every other type is rejected.
    """
    if isinstance(value, datetime.datetime) or not isinstance(value, datetime.date):
        raise TypeError(
            f"expected datetime.date, got {type(value).__name__}"
        )
    return value


def _validated_ranges(
    a_start: object,
    a_end: object,
    b_start: object,
    b_end: object,
) -> tuple[datetime.date, datetime.date, datetime.date, datetime.date]:
    """Check types first, then that each inclusive range runs start through end."""
    a_start = _require_date(a_start)
    a_end = _require_date(a_end)
    b_start = _require_date(b_start)
    b_end = _require_date(b_end)
    if a_start > a_end:
        raise ValueError("a_start must be on or before a_end")
    if b_start > b_end:
        raise ValueError("b_start must be on or before b_end")
    return a_start, a_end, b_start, b_end


def _intersection_bounds(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> tuple[datetime.date, datetime.date] | None:
    """Inclusive overlap: later start through earlier end, or None if disjoint."""
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if start > end:
        return None
    return start, end


def ranges_overlap(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> bool:
    """Return whether the two inclusive calendar ranges share at least one day."""
    a_start, a_end, b_start, b_end = _validated_ranges(a_start, a_end, b_start, b_end)
    return _intersection_bounds(a_start, a_end, b_start, b_end) is not None


def intersection(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> tuple[datetime.date, datetime.date] | None:
    """Return the inclusive overlapping range, or None when the ranges do not overlap."""
    a_start, a_end, b_start, b_end = _validated_ranges(a_start, a_end, b_start, b_end)
    return _intersection_bounds(a_start, a_end, b_start, b_end)
