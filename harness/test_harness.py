"""Local checks for scoring and intervals. These do not call Grok."""

import shutil
import tempfile
import unittest
from pathlib import Path

from harness.score import prepare_solution_staging, score_hidden
from harness.stats import bootstrap_mean_ci, wilson_interval
from harness.tasks import TASKS, hidden_test_path, reference_path


class StatsTests(unittest.TestCase):
    def test_wilson_contains_proportion_and_is_ordered(self):
        low, high = wilson_interval(7, 10)
        self.assertLessEqual(low, 0.7)
        self.assertGreaterEqual(high, 0.7)
        self.assertLess(low, high)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)

    def test_wilson_known_midpoint(self):
        low, high = wilson_interval(50, 100)
        self.assertAlmostEqual(low, 0.4038, places=3)
        self.assertAlmostEqual(high, 0.5962, places=3)

    def test_bootstrap_mean_on_constants(self):
        result = bootstrap_mean_ci([0.5, 0.5, 0.5], reps=200, seed=0)
        self.assertEqual(result["mean"], 0.5)
        self.assertEqual(result["low"], 0.5)
        self.assertEqual(result["high"], 0.5)

    def test_wilson_rejects_empty(self):
        with self.assertRaises(ValueError):
            wilson_interval(0, 0)


class ScoreTests(unittest.TestCase):
    def test_reference_intervals_full_pass(self):
        task = next(task for task in TASKS if task["id"] == "intervals")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            shutil.copy(reference_path(task), work / task["module"])
            staging = root / "stage"
            copied = prepare_solution_staging(work, staging)
            self.assertEqual(copied, ["intervals.py"])
            scored = score_hidden(staging, hidden_test_path(task), task["module"], expected_n=16)
        self.assertTrue(scored["full_pass"], scored)
        self.assertEqual(scored["fraction"], 1.0)
        self.assertEqual(scored["n_passed"], 16)

    def test_touching_intervals_bug_is_not_a_full_pass(self):
        task = next(task for task in TASKS if task["id"] == "intervals")
        buggy = (
            "def merge_intervals(intervals):\n"
            "    rows = []\n"
            "    for start, end in intervals:\n"
            "        if start > end:\n"
            "            raise ValueError\n"
            "        rows.append((start, end))\n"
            "    rows.sort()\n"
            "    merged = []\n"
            "    for start, end in rows:\n"
            "        if not merged or start >= merged[-1][1]:\n"
            "            merged.append((start, end))\n"
            "        elif end > merged[-1][1]:\n"
            "            merged[-1] = (merged[-1][0], end)\n"
            "    return merged\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            (work / "intervals.py").write_text(buggy, encoding="utf-8")
            staging = root / "stage"
            prepare_solution_staging(work, staging)
            scored = score_hidden(staging, hidden_test_path(task), "intervals.py", expected_n=16)
        self.assertFalse(scored["full_pass"])
        self.assertGreater(scored["n_failed"], 0)
        self.assertLess(scored["fraction"], 1.0)


if __name__ == "__main__":
    unittest.main()
