"""Aggregate results/runs.jsonl into summary tables. Every reported number comes from that file."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from harness.stats import bootstrap_mean_ci, wilson_interval
from harness.tasks import TASKS

ROOT = _ROOT
RESULTS = ROOT / "results"
RUNS_PATH = RESULTS / "runs.jsonl"
CONDITIONS = ("tests-first", "code-only")


def load_runs(path: Path = RUNS_PATH) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    latest: dict[tuple, dict] = {}
    order: list[tuple] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("status") != "scored":
            continue
        key = (row["task_id"], row["condition"], int(row["rep"]))
        if key not in latest:
            order.append(key)
        latest[key] = row
    for key in order:
        rows.append(latest[key])
    return rows


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _median(values: list[float]):
    if not values:
        return None
    return float(statistics.median(values))


def _condition_block(rows: list[dict]) -> dict:
    n = len(rows)
    full = sum(1 for row in rows if row.get("full_pass"))
    fractions = [float(row.get("fraction") or 0.0) for row in rows]
    walls = [v for v in (_num(row.get("wall_seconds")) for row in rows) if v is not None]
    tokens = []
    input_tokens = []
    output_tokens = []
    reasoning_tokens = []
    cache_tokens = []
    turns = []
    costs = []
    for row in rows:
        usage = row.get("usage") or {}
        for bucket, dest in (
            ("total_tokens", tokens),
            ("input_tokens", input_tokens),
            ("output_tokens", output_tokens),
            ("reasoning_tokens", reasoning_tokens),
            ("cache_read_input_tokens", cache_tokens),
        ):
            value = _num(usage.get(bucket))
            if value is not None:
                dest.append(value)
        turn = _num(usage.get("num_turns") if "num_turns" in usage else row.get("num_turns"))
        if turn is not None:
            turns.append(turn)
        cost = _num(row.get("cost_usd_all_attempts"))
        if cost is None:
            cost = _num(row.get("cost_usd_scored_attempt"))
        if cost is not None:
            costs.append(cost)
    low, high = wilson_interval(full, n) if n else (None, None)
    return {
        "n": n,
        "n_full_pass": full,
        "full_pass_rate": (full / n) if n else None,
        "full_pass_wilson95": {"low": low, "high": high},
        "fraction": bootstrap_mean_ci(fractions),
        "median_fraction": _median(fractions),
        "wall_seconds": {
            "n": len(walls),
            "median": _median(walls),
            "mean": (sum(walls) / len(walls)) if walls else None,
        },
        "tokens": {
            "n": len(tokens),
            "median_total": _median(tokens),
            "sum_total": sum(tokens) if tokens else None,
            "median_input": _median(input_tokens),
            "median_output": _median(output_tokens),
            "median_reasoning": _median(reasoning_tokens),
            "median_cache_read": _median(cache_tokens),
            "sum_cache_read": sum(cache_tokens) if cache_tokens else None,
            "sum_input": sum(input_tokens) if input_tokens else None,
            "sum_output": sum(output_tokens) if output_tokens else None,
            "sum_reasoning": sum(reasoning_tokens) if reasoning_tokens else None,
        },
        "turns": {"n": len(turns), "median": _median(turns), "mean": (sum(turns) / len(turns)) if turns else None},
        "cost_usd": {
            "n": len(costs),
            "median": _median(costs),
            "sum": sum(costs) if costs else None,
            "mean": (sum(costs) / len(costs)) if costs else None,
        },
        "n_timed_out": sum(1 for row in rows if row.get("timed_out")),
        "n_process_error": sum(1 for row in rows if row.get("process_error")),
        "n_peeked": sum(1 for row in rows if row.get("peeked_outside")),
        "n_solution_mentions_repo": sum(1 for row in rows if row.get("solution_mentions_repo")),
        "n_wrote_test_file": sum(1 for row in rows if row.get("wrote_test_file")),
        "n_ran_checks": sum(1 for row in rows if row.get("ran_checks")),
        "n_missing_session_scan": sum(
            1
            for row in rows
            if not any(attempt.get("session_scan_found") for attempt in row.get("attempts") or [])
        ),
        "n_retried": sum(1 for row in rows if int(row.get("n_attempts") or 1) > 1),
    }


def _paired(rows: list[dict]) -> dict:
    by_key: dict[tuple, dict] = {}
    for row in rows:
        by_key[(row["task_id"], int(row["rep"]), row["condition"])] = row
    keys = sorted({(task, rep) for task, rep, _cond in by_key})
    pairs = []
    for task, rep in keys:
        left = by_key.get((task, rep, "tests-first"))
        right = by_key.get((task, rep, "code-only"))
        if left is None or right is None:
            continue
        pairs.append(
            {
                "task_id": task,
                "rep": rep,
                "tests_first_fraction": float(left.get("fraction") or 0.0),
                "code_only_fraction": float(right.get("fraction") or 0.0),
                "tests_first_full": bool(left.get("full_pass")),
                "code_only_full": bool(right.get("full_pass")),
            }
        )
    diffs = [pair["tests_first_fraction"] - pair["code_only_fraction"] for pair in pairs]
    both = sum(1 for pair in pairs if pair["tests_first_full"] and pair["code_only_full"])
    only_tests = sum(1 for pair in pairs if pair["tests_first_full"] and not pair["code_only_full"])
    only_code = sum(1 for pair in pairs if pair["code_only_full"] and not pair["tests_first_full"])
    neither = sum(1 for pair in pairs if not pair["tests_first_full"] and not pair["code_only_full"])
    return {
        "n_pairs": len(pairs),
        "pairs": pairs,
        "fraction_diff_tests_minus_code": bootstrap_mean_ci(diffs),
        "full_pass_counts": {
            "both": both,
            "tests_first_only": only_tests,
            "code_only_only": only_code,
            "neither": neither,
        },
    }


def _ai_tests(rows: list[dict]) -> dict:
    selected = [row for row in rows if row["condition"] == "tests-first"]
    per_task = []
    for row in selected:
        ai = row.get("ai_tests") or {}
        per_task.append(
            {
                "task_id": row["task_id"],
                "rep": row["rep"],
                "test_files": ai.get("test_files") or [],
                "ast_test_count": ai.get("ast_test_count") or 0,
                "collected": ai.get("collected") or 0,
                "passed_on_reference": ai.get("passed_on_reference") or 0,
                "failed_on_reference": ai.get("failed_on_reference") or 0,
                "errors_on_reference": ai.get("errors_on_reference") or 0,
                "false_failing": ai.get("false_failing") or 0,
                "ran": bool(ai.get("ran")),
            }
        )
    collected = sum(item["collected"] for item in per_task)
    false_failing = sum(item["false_failing"] for item in per_task)
    return {
        "n_runs": len(per_task),
        "n_with_test_file": sum(1 for item in per_task if item["test_files"]),
        "sum_ast_test_count": sum(item["ast_test_count"] for item in per_task),
        "sum_collected": collected,
        "sum_passed_on_reference": sum(item["passed_on_reference"] for item in per_task),
        "sum_failed_on_reference": sum(item["failed_on_reference"] for item in per_task),
        "sum_errors_on_reference": sum(item["errors_on_reference"] for item in per_task),
        "sum_false_failing": false_failing,
        "false_failing_rate_among_collected": (false_failing / collected) if collected else None,
        "per_run": per_task,
    }


def build_summary(rows: list[dict]) -> dict:
    reps = sorted({int(row["rep"]) for row in rows})
    return {
        "n_runs": len(rows),
        "reps": reps,
        "n_tasks_in_repo": len(TASKS),
        "conditions": {condition: _condition_block([row for row in rows if row["condition"] == condition]) for condition in CONDITIONS},
        "paired": _paired(rows),
        "ai_tests": _ai_tests(rows),
        "runs": [
            {
                "task_id": row["task_id"],
                "condition": row["condition"],
                "rep": row["rep"],
                "fraction": row.get("fraction"),
                "full_pass": row.get("full_pass"),
                "n_passed": row.get("n_passed"),
                "n_expected": row.get("n_expected"),
                "wall_seconds": row.get("wall_seconds"),
                "num_turns": row.get("num_turns"),
                "total_tokens": (row.get("usage") or {}).get("total_tokens"),
                "input_tokens": (row.get("usage") or {}).get("input_tokens"),
                "cache_read_input_tokens": (row.get("usage") or {}).get("cache_read_input_tokens"),
                "output_tokens": (row.get("usage") or {}).get("output_tokens"),
                "reasoning_tokens": (row.get("usage") or {}).get("reasoning_tokens"),
                "cost_usd_all_attempts": row.get("cost_usd_all_attempts"),
                "timed_out": row.get("timed_out"),
                "peeked_outside": row.get("peeked_outside"),
                "wrote_test_file": row.get("wrote_test_file"),
                "ran_checks": row.get("ran_checks"),
                "n_attempts": row.get("n_attempts"),
                "process_error": row.get("process_error"),
            }
            for row in rows
        ],
    }


def write_outputs(summary: dict, rows: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (RESULTS / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "condition",
                "n",
                "n_full_pass",
                "full_pass_rate",
                "wilson_low",
                "wilson_high",
                "mean_fraction",
                "fraction_ci_low",
                "fraction_ci_high",
                "median_wall_seconds",
                "median_total_tokens",
                "sum_cost_usd",
                "n_timed_out",
                "n_peeked",
                "n_wrote_test_file",
                "n_ran_checks",
            ],
        )
        writer.writeheader()
        for condition, block in summary["conditions"].items():
            writer.writerow(
                {
                    "condition": condition,
                    "n": block["n"],
                    "n_full_pass": block["n_full_pass"],
                    "full_pass_rate": block["full_pass_rate"],
                    "wilson_low": block["full_pass_wilson95"]["low"],
                    "wilson_high": block["full_pass_wilson95"]["high"],
                    "mean_fraction": block["fraction"]["mean"],
                    "fraction_ci_low": block["fraction"]["low"],
                    "fraction_ci_high": block["fraction"]["high"],
                    "median_wall_seconds": block["wall_seconds"]["median"],
                    "median_total_tokens": block["tokens"]["median_total"],
                    "sum_cost_usd": block["cost_usd"]["sum"],
                    "n_timed_out": block["n_timed_out"],
                    "n_peeked": block["n_peeked"],
                    "n_wrote_test_file": block["n_wrote_test_file"],
                    "n_ran_checks": block["n_ran_checks"],
                }
            )
    with (RESULTS / "per_task.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(summary["runs"][0].keys()) if summary["runs"] else ["task_id"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary["runs"])
    with (RESULTS / "per_test.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["task_id", "condition", "rep", "classname", "name", "status"],
        )
        writer.writeheader()
        for row in rows:
            for case in row.get("per_test") or []:
                writer.writerow(
                    {
                        "task_id": row["task_id"],
                        "condition": row["condition"],
                        "rep": row["rep"],
                        "classname": case.get("classname"),
                        "name": case.get("name"),
                        "status": case.get("status"),
                    }
                )


def main() -> None:
    rows = load_runs()
    summary = build_summary(rows)
    write_outputs(summary, rows)
    print(json.dumps({condition: summary["conditions"][condition]["n"] for condition in CONDITIONS}))


if __name__ == "__main__":
    main()
