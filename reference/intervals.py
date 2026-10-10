def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    normalized = []
    for start, end in intervals:
        if start > end:
            raise ValueError(f"invalid interval {(start, end)}")
        normalized.append((start, end))
    normalized.sort()
    merged: list[tuple[int, int]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        elif end > merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
    return merged
