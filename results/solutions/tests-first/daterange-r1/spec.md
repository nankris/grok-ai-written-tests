# Inclusive calendar-date overlap

Create `daterange.py` in the current directory with these functions:

```python
import datetime

def ranges_overlap(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> bool:
    ...

def intersection(
    a_start: datetime.date,
    a_end: datetime.date,
    b_start: datetime.date,
    b_end: datetime.date,
) -> tuple[datetime.date, datetime.date] | None:
    ...
```

Use only the Python standard library.

Both functions take inclusive calendar ranges. A range includes every day from its start through its end. Each argument must be an instance of `datetime.date` and must not be a `datetime.datetime` (`datetime` is a subclass of `date`; reject it with `TypeError`). Any other type, including an ISO date string, also raises `TypeError`.

If either range has `start > end`, raise `ValueError`. A range whose start equals its end is a single day and is valid.

`ranges_overlap` is true when the two inclusive ranges share at least one calendar day. Ranges that only meet at an endpoint overlap on that day. The next day after a range ends does not overlap that range.

`intersection` returns the inclusive overlapping range, or `None` when the ranges do not overlap. The returned start is the later of the two starts and the returned end is the earlier of the two ends. The two functions use the same validation and the same overlap rule.
