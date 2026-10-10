import datetime


def _require_date(value: object) -> datetime.date:
    """Return value when it is a calendar date and not a datetime."""
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
    """Type-check every bound, then reject either inverted range."""
    a_start_date = _require_date(a_start)
    a_end_date = _require_date(a_end)
    b_start_date = _require_date(b_start)
    b_end_date = _require_date(b_end)
    if a_start_date > a_end_date:
        raise ValueError("a_start must be on or before a_end")
    if b_start_date > b_end_date:
        raise ValueError("b_start must be on or before b_end")
    return a_start_date, a_end_date, b_start_date, b_end_date


def ranges_overlap(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> bool:
    """Return whether two inclusive calendar ranges share at least one day."""
    a_start, a_end, b_start, b_end = _validated_ranges(
        a_start, a_end, b_start, b_end
    )
    return a_start <= b_end and b_start <= a_end


def intersection(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> tuple[datetime.date, datetime.date] | None:
    """Return the inclusive overlap, or None when the ranges are disjoint."""
    a_start, a_end, b_start, b_end = _validated_ranges(
        a_start, a_end, b_start, b_end
    )
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if start > end:
        return None
    return (start, end)
