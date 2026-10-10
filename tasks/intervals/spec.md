# Merge closed integer intervals

Create `intervals.py` in the current directory with this function:

```python
def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    ...
```

Use only the Python standard library.

Each item is a closed interval of integers `[start, end]` (every integer from `start` through `end` inclusive). The input may be empty, unsorted, and may contain duplicates or nested intervals. Do not modify the input list.

If any interval has `start > end`, raise `ValueError`.

Merge intervals that share at least one integer. Walk the intervals by ascending start. The next interval joins the current merged interval when its start is less than or equal to the current merged end (they overlap or touch at an endpoint). When its start is greater than the current merged end, there is a gap: keep the current interval and start a new one. In particular, an interval that ends at `k` touches an interval that starts at `k` (they share `k`), and it does not touch an interval that starts at `k + 1`.

Return a new list of merged `(start, end)` tuples sorted by ascending start. Each merged interval uses the smallest start and the largest end of the intervals that went into it. An empty input returns an empty list.
