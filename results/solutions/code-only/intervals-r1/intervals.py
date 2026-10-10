def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge closed integer intervals that overlap or share an endpoint.

    Intervals are walked by ascending start. The next interval joins the
    current one when its start is less than or equal to the current end.
    A start of ``k + 1`` after an end of ``k`` is a gap and stays separate.
    The input list is not modified. ``start > end`` raises ``ValueError``.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError(f"invalid interval: start {start} > end {end}")

    if not intervals:
        return []

    ordered = sorted(intervals, key=lambda interval: (interval[0], interval[1]))
    merged: list[tuple[int, int]] = []
    current_start, current_end = ordered[0]

    for start, end in ordered[1:]:
        if start <= current_end:
            if end > current_end:
                current_end = end
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    merged.append((current_start, current_end))
    return merged
