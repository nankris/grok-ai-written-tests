"""Write README.md, post-outline.md, issues, and FINAL_SUMMARY.md from results/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ROOT = _ROOT
RESULTS = ROOT / "results"
ISSUES = ROOT / "issues-found"


def _load(name: str) -> dict:
    path = RESULTS / name
    if not path.exists():
        raise SystemExit(f"missing {path}; run harness/analyze.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value, digits=1) -> str:
    if value is None:
        return "n/a"
    return f"{100 * float(value):.{digits}f}%"


def num(value, digits=1) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):,.{digits}f}"


def plain(value, digits=0) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):,.{digits}f}"


def span(low, high, as_percent=False) -> str:
    if low is None or high is None:
        return "n/a"
    if as_percent:
        return f"{pct(low)} to {pct(high)}"
    return f"{float(low):.2f} to {float(high):.2f}"


def condition_table(summary: dict) -> str:
    lines = [
        "| | tests-first | code-only |",
        "|---|---:|---:|",
    ]
    blocks = summary["conditions"]
    rows = [
        ("Runs (n)", lambda b: str(b["n"])),
        ("Full hidden-suite passes", lambda b: f"{b['n_full_pass']} ({pct(b['full_pass_rate'])})"),
        ("Wilson 95% CI, full pass", lambda b: span(b["full_pass_wilson95"]["low"], b["full_pass_wilson95"]["high"], True)),
        ("Mean fraction passed", lambda b: f"{b['fraction']['mean']:.3f}" if b["fraction"]["mean"] is not None else "n/a"),
        ("Bootstrap 95% CI, mean fraction", lambda b: span(b["fraction"]["low"], b["fraction"]["high"])),
        ("Median wall time (s)", lambda b: num(b["wall_seconds"]["median"], 1)),
        ("Median output tokens", lambda b: plain(b["tokens"]["median_output"], 0)),
        ("Median cache-read tokens", lambda b: plain(b["tokens"]["median_cache_read"], 0)),
        ("Median CLI total tokens", lambda b: plain(b["tokens"]["median_total"], 0)),
        ("Sum of CLI-reported cost (USD)", lambda b: num(b["cost_usd"]["sum"], 3)),
        ("Median turns", lambda b: num(b["turns"]["median"], 1)),
        ("Timeouts", lambda b: str(b["n_timed_out"])),
        ("Wrote a test file", lambda b: str(b["n_wrote_test_file"])),
        ("Ran a check command", lambda b: str(b["n_ran_checks"])),
        ("Peeked at the repo", lambda b: str(b["n_peeked"])),
    ]
    for label, fn in rows:
        lines.append(f"| {label} | {fn(blocks['tests-first'])} | {fn(blocks['code-only'])} |")
    return "\n".join(lines)


def per_task_table(summary: dict) -> str:
    lines = [
        "| Task | tests-first fraction | code-only fraction | tests-first full | code-only full |",
        "|---|---:|---:|---|---|",
    ]
    for pair in summary["paired"]["pairs"]:
        lines.append(
            "| {task} r{rep} | {a:.3f} | {b:.3f} | {af} | {bf} |".format(
                task=pair["task_id"],
                rep=pair["rep"],
                a=pair["tests_first_fraction"],
                b=pair["code_only_fraction"],
                af="yes" if pair["tests_first_full"] else "no",
                bf="yes" if pair["code_only_full"] else "no",
            )
        )
    return "\n".join(lines)


def ai_table(summary: dict) -> str:
    lines = [
        "| Task | rep | test files | AST tests | collected | passed on reference | false-failing |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["ai_tests"]["per_run"]:
        lines.append(
            f"| {item['task_id']} | {item['rep']} | {len(item['test_files'])} | {item['ast_test_count']} | "
            f"{item['collected']} | {item['passed_on_reference']} | {item['false_failing']} |"
        )
    return "\n".join(lines)


def headline(summary: dict) -> str:
    paired = summary["paired"]["fraction_diff_tests_minus_code"]
    counts = summary["paired"]["full_pass_counts"]
    diff = paired["mean"]
    low, high = paired["low"], paired["high"]
    if diff is None:
        return "No paired runs were recorded."
    direction = "higher" if diff > 0 else "lower" if diff < 0 else "the same"
    overlap = low is not None and high is not None and low <= 0 <= high
    if overlap:
        claim = (
            f"Telling Grok 4.7 to write its own tests first produced a mean hidden-test fraction "
            f"{abs(diff):.3f} {direction} than code-only. The bootstrap 95% CI on that paired difference "
            f"({span(low, high)}) includes zero."
        )
    else:
        claim = (
            f"Telling Grok 4.7 to write its own tests first produced a mean hidden-test fraction "
            f"{abs(diff):.3f} {direction} than code-only. The bootstrap 95% CI on that paired difference "
            f"({span(low, high)}) does not include zero."
        )
    claim += (
        f" Full passes: tests-first only {counts['tests_first_only']}, "
        f"code-only only {counts['code_only_only']}, "
        f"both {counts['both']}, neither {counts['neither']} "
        f"(n_pairs={summary['paired']['n_pairs']})."
    )
    return claim


def readme(summary: dict, env: dict, validation: dict) -> str:
    counts = {task_id: info["n_tests"] for task_id, info in validation.get("tasks", {}).items()}
    count_line = ", ".join(f"{task} {n}" for task, n in counts.items())
    tf = summary["conditions"]["tests-first"]
    co = summary["conditions"]["code-only"]
    ai = summary["ai_tests"]
    return f"""# Do AI-written tests help Grok pass hidden tests?

On 8 Oct 2026, [The Code](https://archive.codenewsletter.ai/2108030810691629403) pointed at a post by Kun Chen ([@kunchenguid](https://x.com/kunchenguid/status/2108030810691629403)). He said that on the DeepSWE eval, banning Claude Sonnet 5.5 (high) from writing tests gave a slightly higher success rate (he marked it not statistically significant) and used significantly less time and fewer tokens. Of the tests the unrestricted arm wrote, he counted 65% unit tests and 35% integration tests, and said neither bucket beat the no-tests arm. A 44-task subset where existing tests were disabled also showed no success-rate change. He did not publish the raw success percentages. The newsletter archive URL itself did not load from this machine (the host resolved to a blocked address). The tweet id in that URL is the post above.

This repo asks a smaller, related question: on 10 original Python tasks with hidden tests, does telling **Grok 4.7** to write pytest tests first raise the hidden-test pass rate, compared with telling it to implement the solution and not write test files?

{headline(summary)}

## Results

{condition_table(summary)}

Mean fraction CIs are percentile bootstraps of the run-level fractions (10,000 resamples, seed 0). Full-pass CIs are Wilson intervals. Cost is the sum of `total_cost_usd` reported by the Grok CLI, including retries when a retry happened. It is the CLI's figure for these calls, not a separate price-list estimate. Token medians use the scored attempt. CLI total tokens are input + cache-read + output, as the CLI defines `total_tokens`. Output tokens include reasoning tokens. A run with no usage block is left out of the token and cost medians; the `n` inside `summary.json` for those fields says how many runs contributed.

### Per task

{per_task_table(summary)}

![Pass rate by condition](images/pass_rate_by_condition.png)

![Per-task fraction](images/per_task_heatmap.png)

![Time and tokens](images/time_tokens.png)

### Tests the agent wrote

Condition tests-first was told to write `test_solution.py`, run it, then implement. Those tests were copied next to the reference solution (not next to the agent's solution) and run.

| | |
|---|---|
| tests-first runs | {ai['n_runs']} |
| runs that wrote at least one test file | {ai['n_with_test_file']} |
| AST `test*` functions | {ai['sum_ast_test_count']} |
| tests pytest collected | {ai['sum_collected']} |
| passed on the reference solution | {ai['sum_passed_on_reference']} |
| failed on the reference | {ai['sum_failed_on_reference']} |
| errors on the reference | {ai['sum_errors_on_reference']} |
| false-failing (failed + errors) | {ai['sum_false_failing']} |

{ai_table(summary)}

Code-only was told not to write test files. It wrote a test file in {co['n_wrote_test_file']} of {co['n']} runs. A session-log scan marked a check command (python or pytest) in {co['n_ran_checks']} of {co['n']} code-only runs and {tf['n_ran_checks']} of {tf['n']} tests-first runs. If the session log could not be read, that run is not counted as a check. See `summary.json` field `n_missing_session_scan`.

## Setup

- Date of the runs: {env.get('recorded_at', 'see results/environment.json')}.
- Model flag: `{env.get('grok_model_flag', 'grok-4.7')}`. CLI: {env.get('grok_version', 'grok')}.
- Python: {env.get('python', '3.13')}.
- Machine: {env.get('uname', 'Linux')}. CPU only.
- Solver flags: `--always-approve --output-format json --cwd <fresh dir> -m grok-4.7 --no-subagents --disable-web-search`. Subagents are off so a run cannot fan out past the two-at-a-time cap (other experiments share the plan quota). Web search is off so the comparison is about tests versus no tests on the spec in front of the model. Timeout 600 seconds, one retry if the process fails and the required module is missing.
- Hidden tests per task (all passed on the reference solution before any solver run): {count_line}.
- Work directory for each run: `/tmp/ai-written-tests-work/<condition>/<task>-r<k>/`, containing only `spec.md`. Scoring copies the solution into a different directory and adds the hidden tests there.

## Caveats

- Ten small tasks, written by the same person who wrote the hidden tests and the reference solutions. That is not DeepSWE, not a sample of GitHub issues, and not a test of Claude. n is the number of runs in the table above. The intervals are wide.
- The specs state the behaviour, including the rules that make the tricky cases determined (touching closed intervals, canonical Roman numerals, TTL expiry, SemVer precedence, and so on). They do not list the hidden cases one by one.
- The solver is a full coding agent. The prompt tells it to stay in the work directory. It can still read other paths. Hidden tests and reference solutions are not in the work directory. Runs that touched the repo path are counted in the table (`Peeked at the repo`) and are not dropped, because dropping them would hide the failure mode.
- A full pass means every hidden test passed. The fraction counts collected tests. If pytest could not collect the suite, the fraction is 0 and the denominator used in the mean is the reference count only for that zero; `per_task.csv` has the collected and expected counts.
- Agent-written tests that error on the reference (import errors, bad fixtures) are counted as false-failing together with assertion failures. `summary.json` splits failed and errors.
- CLI cost includes the large Grok Code system prompt, not just the task text. Do not read it as the cost of the spec alone.
- One repetition was the plan, with a second only if the first finished with time to spare. `summary.json` field `reps` is what actually ran.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
python3 -m venv /tmp/ai-written-tests-pytest
/tmp/ai-written-tests-pytest/bin/pip install pytest==9.1.1
.venv/bin/python -m unittest harness.test_harness
.venv/bin/python harness/run.py --reps 1
.venv/bin/python harness/analyze.py
.venv/bin/python harness/charts.py
.venv/bin/python harness/report.py
```

`harness/run.py` skips task/condition/rep rows already marked `scored` in `results/runs.jsonl`. Raw CLI JSON is under `results/raw/`. Solution trees are under `results/solutions/`.
"""


def issues_markdown(summary: dict, rows: list[dict]) -> dict[str, str]:
    failed = []
    for row in rows:
        problems = []
        if row.get("timed_out"):
            problems.append("timed out")
        if row.get("process_error"):
            problems.append(f"process error: {row['process_error']}")
        if int(row.get("n_attempts") or 1) > 1:
            problems.append(f"attempts={row['n_attempts']}")
        if row.get("score_error"):
            problems.append(f"score error: {row['score_error']}")
        if problems:
            failed.append(f"- `{row['condition']}` `{row['task_id']}` r{row['rep']}: " + "; ".join(problems))
    failed_body = "\n".join(failed) if failed else "No scored run timed out, raised a process error, or needed a retry."
    peeks = [
        f"- `{row['condition']}` `{row['task_id']}` r{row['rep']}: {row.get('peek_evidence')}"
        for row in rows
        if row.get("peeked_outside")
    ]
    mentions = [
        f"- `{row['condition']}` `{row['task_id']}` r{row['rep']}: files {row.get('solution_mentions_repo')}"
        for row in rows
        if row.get("solution_mentions_repo")
    ]
    code_only_tests = [
        f"- `{row['task_id']}` r{row['rep']}: {row.get('test_files')}"
        for row in rows
        if row["condition"] == "code-only" and row.get("wrote_test_file")
    ]
    missing_scan = [
        f"- `{row['condition']}` `{row['task_id']}` r{row['rep']}"
        for row in rows
        if not any(attempt.get("session_scan_found") for attempt in row.get("attempts") or [])
    ]
    false_rows = [
        item
        for item in summary["ai_tests"]["per_run"]
        if item["false_failing"]
    ]
    false_lines = "\n".join(
        f"- `{item['task_id']}` r{item['rep']}: false-failing {item['false_failing']} "
        f"(failed {item['failed_on_reference']}, errors {item['errors_on_reference']}) "
        f"of {item['collected']} collected"
        for item in false_rows
    ) or "No tests-first run had a test that failed or errored on the reference solution."
    return {
        "001-failed-runs.md": f"""# 001 - Failed or retried solver runs

{failed_body}

A retry happens only when the Grok process times out, returns a non-zero status, or does not emit JSON, and the required module file is absent. A finished run that fails hidden tests is not a harness failure and is not listed here unless it also hit one of those process problems.

Session logs that could not be opened ({len(missing_scan)}):

{chr(10).join(missing_scan) if missing_scan else "Every scored run had a session directory."}
""",
        "002-measurement.md": f"""# 002 - Measurement notes

**Peeks outside the work directory.** The prompt forbids reading the rest of the disk. The scanner flags a tool path or command that mentions this repo, `hidden_tests`, or `reference/` and is not inside the work directory. Flagged runs: {len(peeks)}.

{chr(10).join(peeks) if peeks else "None flagged."}

**Solution text mentioning the repo or hidden tests.** {len(mentions)} run(s).

{chr(10).join(mentions) if mentions else "None."}

**Code-only runs that wrote a test file anyway.** {len(code_only_tests)} run(s). Hidden scoring ignores test files, so this does not by itself change the hidden-test score. It does mean the condition was not clean.

{chr(10).join(code_only_tests) if code_only_tests else "None."}

**Agent tests that do not pass on the reference solution.** These are the false-failing tests: the agent's own suite rejects the reference implementation, so the suite is not a correct reading of the spec (or it errors before it can check).

{false_lines}

**Session command scan is best-effort.** `results/raw/*.json` stores the headless response, which has usage and the final text, not the tool trace. Commands are scraped from `~/.grok/sessions/.../updates.jsonl` by looking for `command` and path fields. A future CLI that renames those fields would show up as zero check commands. `n_missing_session_scan` in the condition block counts runs whose session directory was not found.
""",
        "003-workflow.md": """# 003 - Workflow and harness choices

**Extra CLI flags.** The brief's headless pattern is `grok -p ... --always-approve --output-format json --cwd`. The solver calls also pass `--no-subagents` and `--disable-web-search`. Subagents are off because each one would be another model call, and the machine is shared with other experiments under a two-at-a-time cap. Web search is off so a run cannot spend the 600 second budget on search, and so the two conditions see the same spec rather than a textbook solution one of them happened to retrieve. Both choices make this a narrower test than an unrestricted coding agent.

**Parallelism.** At most two Grok processes. The queue alternates which condition is listed first as the task index and repetition change. With two workers, the two conditions of one task usually start together.

**What is scored.** Hidden tests run in a fresh directory that receives the non-test Python files from the work directory. `test_*.py`, `*_test.py`, and `conftest.py` are left behind so the agent's tests cannot weaken the hidden suite. A missing module fails at collection and counts as fraction 0.

**Reference check.** `harness/run.py` refuses to start if any hidden suite fails on `reference/<id>.py`. That validation is `results/reference_validation.json`.

**Cost.** Reported cost is the CLI field `total_cost_usd`. A one-word probe before the experiment returned about 14k input tokens, so most of the bill is the system prompt and tool definitions, repeated every turn.

**Not done.** There is no mutation score of the agent tests, no second model, and no attempt to stop the agent from reading arbitrary paths beyond the prompt and the after-the-fact peek flag.
""",
    }


def outline(summary: dict) -> str:
    tf = summary["conditions"]["tests-first"]
    co = summary["conditions"]["code-only"]
    diff = summary["paired"]["fraction_diff_tests_minus_code"]
    return f"""# Post outline

## Angle

Kun Chen's 8 Oct 2026 DeepSWE note said banning agent-written tests slightly raised success and clearly cut time and tokens. This is a tiny check of the same instruction on Grok 4.7, with hidden tests the agent did not write.

## Hook

{headline(summary)}

## Key numbers (from results/summary.json)

- tests-first full pass {tf['n_full_pass']}/{tf['n']} ({pct(tf['full_pass_rate'])}), Wilson {span(tf['full_pass_wilson95']['low'], tf['full_pass_wilson95']['high'], True)}
- code-only full pass {co['n_full_pass']}/{co['n']} ({pct(co['full_pass_rate'])}), Wilson {span(co['full_pass_wilson95']['low'], co['full_pass_wilson95']['high'], True)}
- mean fraction tests-first {tf['fraction']['mean']}, code-only {co['fraction']['mean']}
- paired difference (tests-first minus code-only) mean {diff['mean']}, 95% bootstrap {span(diff['low'], diff['high'])}, n_pairs={summary['paired']['n_pairs']}
- median wall seconds tests-first {tf['wall_seconds']['median']}, code-only {co['wall_seconds']['median']}
- median total tokens tests-first {tf['tokens']['median_total']}, code-only {co['tokens']['median_total']}
- sum CLI cost USD tests-first {tf['cost_usd']['sum']}, code-only {co['cost_usd']['sum']}
- agent tests collected {summary['ai_tests']['sum_collected']}, false-failing {summary['ai_tests']['sum_false_failing']}

## Charts

- images/pass_rate_by_condition.png
- images/per_task_heatmap.png
- images/time_tokens.png

## Caveats

Author-written tasks, n is small, Grok not Claude, DeepSWE not replicated, agent might read the repo (counted, not dropped), cost includes the system prompt.
"""


def final_summary(summary: dict) -> str:
    return f"""# Final summary

{headline(summary)}

Sample size: {summary['n_runs']} scored runs, reps {summary['reps']}, tasks in the repo {summary['n_tasks_in_repo']}.

tests-first full pass {summary['conditions']['tests-first']['n_full_pass']}/{summary['conditions']['tests-first']['n']}.
code-only full pass {summary['conditions']['code-only']['n_full_pass']}/{summary['conditions']['code-only']['n']}.

Issues worth reading: timeouts and retries in issues-found/001-failed-runs.md, peeks and false-failing tests in issues-found/002-measurement.md, flag and harness limits in issues-found/003-workflow.md.

Incomplete relative to the original brief: a second repetition was optional and is present only if `reps` above contains 2. No mutation testing of the agent suites. The newsletter archive page was not fetched (blocked); the claim is taken from the tweet the archive URL points at.
"""


def main() -> None:
    summary = _load("summary.json")
    env_path = RESULTS / "environment.json"
    env = json.loads(env_path.read_text(encoding="utf-8")) if env_path.exists() else {}
    val_path = RESULTS / "reference_validation.json"
    validation = json.loads(val_path.read_text(encoding="utf-8")) if val_path.exists() else {"tasks": {}}
    from harness.analyze import load_runs

    rows = load_runs()
    (ROOT / "README.md").write_text(readme(summary, env, validation), encoding="utf-8")
    (ROOT / "post-outline.md").write_text(outline(summary), encoding="utf-8")
    (RESULTS / "FINAL_SUMMARY.md").write_text(final_summary(summary), encoding="utf-8")
    ISSUES.mkdir(parents=True, exist_ok=True)
    bodies = issues_markdown(summary, rows)
    index_rows = [
        ("001", "001-failed-runs.md", "Timeouts, retries, process errors"),
        ("002", "002-measurement.md", "Peeks, code-only test files, false-failing tests"),
        ("003", "003-workflow.md", "Flags, scoring rules, what was not run"),
    ]
    index = [
        "# Issues found",
        "",
        "Problems and limits recorded while running this experiment. Numbers come from `results/runs.jsonl`.",
        "",
        "| # | File | Area |",
        "|---|---|---|",
    ]
    for number, filename, area in index_rows:
        index.append(f"| {number} | [{filename}]({filename}) | {area} |")
        (ISSUES / filename).write_text(bodies[filename], encoding="utf-8")
    (ISSUES / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print("wrote README.md, post-outline.md, results/FINAL_SUMMARY.md, issues-found/")


if __name__ == "__main__":
    main()
