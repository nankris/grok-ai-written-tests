import pytest

from intervals import merge_intervals


@pytest.mark.parametrize(
    "intervals, expected",
    [
        ([], []),
        ([(4, 4)], [(4, 4)]),
        ([(1, 2), (4, 5)], [(1, 2), (4, 5)]),
        ([(4, 5), (1, 2)], [(1, 2), (4, 5)]),
        ([(1, 4), (2, 3)], [(1, 4)]),
        ([(1, 4), (2, 6)], [(1, 6)]),
        ([(1, 2), (2, 3)], [(1, 3)]),
        ([(1, 2), (3, 4)], [(1, 2), (3, 4)]),
        ([(1, 5), (1, 5), (1, 5)], [(1, 5)]),
        ([(5, 6), (1, 2), (2, 4)], [(1, 4), (5, 6)]),
        ([(-2, -2), (-1, 0)], [(-2, -2), (-1, 0)]),
        ([(-10, -6), (-5, -1)], [(-10, -6), (-5, -1)]),
        ([(1, 10), (2, 3), (10, 12), (13, 13)], [(1, 12), (13, 13)]),
        ([(8, 10), (1, 3), (2, 6), (15, 18)], [(1, 6), (8, 10), (15, 18)]),
    ],
)
def test_merge(intervals, expected):
    assert merge_intervals(intervals) == expected


def test_start_after_end_raises():
    with pytest.raises(ValueError):
        merge_intervals([(1, 1), (3, 2)])


def test_does_not_mutate_input():
    data = [(2, 3), (1, 2), (10, 10)]
    snapshot = list(data)
    merge_intervals(data)
    assert data == snapshot
