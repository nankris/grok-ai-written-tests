"""Tests for merge_intervals: closed integer intervals."""

import pytest

from intervals import merge_intervals


def test_empty_input_returns_empty_list():
    assert merge_intervals([]) == []


def test_single_interval_unchanged():
    assert merge_intervals([(2, 5)]) == [(2, 5)]


def test_single_point_interval():
    assert merge_intervals([(7, 7)]) == [(7, 7)]


def test_already_merged_stays_same():
    intervals = [(1, 4), (6, 8)]
    assert merge_intervals(intervals) == [(1, 4), (6, 8)]


def test_unsorted_overlapping_intervals_merge():
    intervals = [(8, 10), (1, 3), (2, 6)]
    assert merge_intervals(intervals) == [(1, 6), (8, 10)]


def test_duplicates_collapse_to_one():
    assert merge_intervals([(1, 4), (1, 4), (1, 4)]) == [(1, 4)]


def test_nested_interval_is_absorbed():
    assert merge_intervals([(1, 10), (3, 4), (2, 8)]) == [(1, 10)]


def test_nested_interval_appearing_first_is_absorbed():
    assert merge_intervals([(3, 4), (1, 10)]) == [(1, 10)]


def test_partial_overlap_extends_end():
    assert merge_intervals([(1, 5), (4, 9)]) == [(1, 9)]


def test_later_interval_with_smaller_end_does_not_shrink():
    assert merge_intervals([(1, 10), (2, 3)]) == [(1, 10)]


def test_touch_at_shared_endpoint_merges():
    # [1, 2] and [2, 4] share the integer 2.
    assert merge_intervals([(1, 2), (2, 4)]) == [(1, 4)]


def test_adjacent_integers_with_gap_do_not_merge():
    # [1, 2] ends at 2; [3, 4] starts at 3. They share no integer.
    assert merge_intervals([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]


def test_point_touching_end_merges_and_point_just_after_does_not():
    assert merge_intervals([(1, 5), (5, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 5), (6, 6)]) == [(1, 5), (6, 6)]


def test_chain_of_touching_intervals_becomes_one():
    assert merge_intervals([(1, 2), (2, 3), (3, 4)]) == [(1, 4)]


def test_chain_of_gapped_points_stays_separate():
    assert merge_intervals([(1, 1), (2, 2), (3, 3)]) == [(1, 1), (2, 2), (3, 3)]


def test_transitive_merge_through_a_bridge_interval():
    # Unsorted. After sorting by start, the middle interval touches both ends.
    intervals = [(1, 5), (10, 15), (5, 10)]
    assert merge_intervals(intervals) == [(1, 15)]


def test_bridge_does_not_cross_a_real_gap():
    intervals = [(1, 4), (5, 8), (10, 12), (4, 5)]
    assert merge_intervals(intervals) == [(1, 8), (10, 12)]


def test_same_start_keeps_largest_end():
    assert merge_intervals([(2, 3), (2, 9), (2, 4)]) == [(2, 9)]


def test_negative_and_zero_intervals():
    assert merge_intervals([(-5, -1), (-3, 2)]) == [(-5, 2)]
    assert merge_intervals([(-5, -3), (-1, 1)]) == [(-5, -3), (-1, 1)]
    assert merge_intervals([(0, 0), (0, 1)]) == [(0, 1)]
    assert merge_intervals([(-1, 0), (1, 1)]) == [(-1, 0), (1, 1)]


def test_point_does_not_touch_the_next_integer():
    assert merge_intervals([(0, 0), (1, 100)]) == [(0, 0), (1, 100)]


def test_large_integers():
    big = 10**18
    assert merge_intervals([(-big, -big + 5), (big, big)]) == [
        (-big, -big + 5),
        (big, big),
    ]
    assert merge_intervals([(-big, big), (0, 1)]) == [(-big, big)]


def test_many_disjoint_groups_sorted_by_start():
    # (20, 21) and (22, 22) do not share an integer, so they stay apart.
    # (0, 1) shares 1 with (1, 1). (5, 7) overlaps (6, 9).
    intervals = [(20, 21), (0, 1), (5, 7), (6, 9), (22, 22), (1, 1), (15, 15)]
    assert merge_intervals(intervals) == [
        (0, 1),
        (5, 9),
        (15, 15),
        (20, 21),
        (22, 22),
    ]


def test_result_is_a_new_list_of_tuples():
    intervals = [(3, 4), (1, 2)]
    result = merge_intervals(intervals)
    assert result == [(1, 2), (3, 4)]
    assert result is not intervals
    assert all(type(item) is tuple for item in result)


def test_input_list_is_not_modified():
    intervals = [(8, 10), (1, 3), (2, 6), (2, 6)]
    snapshot = list(intervals)
    merge_intervals(intervals)
    assert intervals == snapshot


def test_merge_is_idempotent():
    intervals = [(8, 10), (1, 3), (2, 6), (10, 12), (14, 14)]
    once = merge_intervals(intervals)
    assert merge_intervals(once) == once


def test_start_greater_than_end_raises_value_error():
    with pytest.raises(ValueError):
        merge_intervals([(5, 3)])


def test_equal_endpoints_are_valid():
    assert merge_intervals([(4, 4)]) == [(4, 4)]


def test_invalid_interval_among_valid_ones_raises():
    with pytest.raises(ValueError):
        merge_intervals([(1, 2), (5, 4), (3, 6)])


def test_invalid_interval_does_not_mutate_input():
    intervals = [(1, 5), (3, 1), (0, 2)]
    snapshot = list(intervals)
    with pytest.raises(ValueError):
        merge_intervals(intervals)
    assert intervals == snapshot


def test_negative_invalid_interval_raises():
    with pytest.raises(ValueError):
        merge_intervals([(0, -1)])


def test_only_invalid_interval_raises_before_any_result():
    with pytest.raises(ValueError):
        merge_intervals([(2, 1), (9, 8)])


def test_reverse_sorted_input():
    intervals = [(9, 10), (5, 6), (1, 2), (6, 8)]
    assert merge_intervals(intervals) == [(1, 2), (5, 8), (9, 10)]


def test_contained_duplicate_points_inside_a_span():
    assert merge_intervals([(0, 5), (2, 2), (5, 5), (0, 0), (3, 4)]) == [(0, 5)]
