def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge closed integer intervals that share at least one integer.

    The input list is left unchanged. Intervals are walked by ascending start.
    The next interval joins the current one when its start is less than or
    equal to the current end (overlap or a shared endpoint). A start of
    current_end + 1 is a gap and begins a new interval. Each merged interval
    uses the smallest start and the largest end of the intervals that formed it.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError(f"interval start {start} is greater than end {end}")

    if not intervals:
        return []

    ordered = sorted(intervals, key=lambda interval: interval[0])
    merged_start, merged_end = ordered[0]
    merged: list[tuple[int, int]] = []

    for start, end in ordered[1:]:
        if start <= merged_end:
            if end > merged_end:
                merged_end = end
        else:
            merged.append((merged_start, merged_end))
            merged_start, merged_end = start, end

    merged.append((merged_start, merged_end))
    return merged
