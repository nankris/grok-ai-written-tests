import datetime


def _validate(a_start, a_end, b_start, b_end) -> None:
    for value in (a_start, a_end, b_start, b_end):
        if type(value) is not datetime.date:
            raise TypeError("arguments must be datetime.date, not datetime.datetime or other types")
    if a_start > a_end or b_start > b_end:
        raise ValueError("start must be <= end")


def ranges_overlap(a_start, a_end, b_start, b_end) -> bool:
    _validate(a_start, a_end, b_start, b_end)
    return a_start <= b_end and b_start <= a_end


def intersection(a_start, a_end, b_start, b_end):
    _validate(a_start, a_end, b_start, b_end)
    start = a_start if a_start >= b_start else b_start
    end = a_end if a_end <= b_end else b_end
    if start <= end:
        return (start, end)
    return None
