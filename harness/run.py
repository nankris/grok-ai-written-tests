"""Run the tests-first vs code-only coding-agent experiment.

Each job is a fresh directory that contains only spec.md. Grok is invoked
headless in that directory. Hidden tests are copied into a separate scoring
directory afterwards. At most two Grok processes run at once. A failed process
with no solution file is retried once.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from harness.score import (
    implementation_files,
    prepare_solution_staging,
    score_ai_tests,
    score_hidden,
    test_files,
)
from harness.session_scan import command_looks_like_check, extract_session, looks_like_peek
from harness.tasks import TASKS, hidden_test_path, reference_path, spec_path, task_by_id

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RAW = RESULTS / "raw"
SOLUTIONS = RESULTS / "solutions"
RUNS_PATH = RESULTS / "runs.jsonl"
VALIDATION_PATH = RESULTS / "reference_validation.json"
WORK_ROOT = Path("/tmp/ai-written-tests-work")
SCORE_ROOT = Path("/tmp/ai-written-tests-score")
PROMPT_ROOT = Path("/tmp/ai-written-tests-prompts")
PYTEST_BIN = Path("/tmp/ai-written-tests-pytest/bin")
GROK = Path.home() / ".grok" / "bin" / "grok"
TIMEOUT_S = 600
PYTEST_TIMEOUT_S = 60
MAX_PARALLEL = 2

CONDITIONS = ("tests-first", "code-only")

PREAMBLE = """Use only the Python 3.13 standard library. Do not install packages.
Work only in the current working directory. Do not read or write any path outside this directory, and do not search the rest of the filesystem.
The directory currently contains only spec.md.

"""

TAIL = {
    "tests-first": (
        "First write your own pytest tests in test_solution.py covering the spec and edge cases, "
        "run them, then implement and iterate until your tests pass.\n"
    ),
    "code-only": "Implement the solution. Do not write test files.\n",
}

_write_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    line = f"{utc_now()} {message}"
    print(line, flush=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with (RESULTS / "run.log").open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def load_completed() -> set[tuple[str, str, int]]:
    done = set()
    if not RUNS_PATH.exists():
        return done
    for line in RUNS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("status") == "scored":
            done.add((row["task_id"], row["condition"], int(row["rep"])))
    return done


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def validate_references() -> dict:
    """Confirm every hidden suite passes on the reference solution."""
    summary = {"validated_at": utc_now(), "tasks": {}}
    for task in TASKS:
        staging = SCORE_ROOT / "_reference" / task["id"]
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        shutil.copy(reference_path(task), staging / task["module"])
        scored = score_hidden(
            staging,
            hidden_test_path(task),
            task["module"],
            expected_n=10**9,
            timeout=PYTEST_TIMEOUT_S,
        )
        # expected_n was a sentinel so full_pass compares against the real count.
        expected = scored["n_collected"]
        scored["n_expected"] = expected
        scored["full_pass"] = (
            not scored["pytest_timed_out"]
            and scored["n_passed"] == expected
            and expected > 0
            and scored["n_failed"] == 0
            and scored["n_errors"] == 0
            and scored["n_skipped"] == 0
        )
        scored["fraction"] = (scored["n_passed"] / expected) if expected else 0.0
        nodeids = [f"{case['classname']}::{case['name']}" for case in scored["per_test"]]
        summary["tasks"][task["id"]] = {
            "module": task["module"],
            "n_tests": expected,
            "full_pass": scored["full_pass"],
            "n_passed": scored["n_passed"],
            "n_failed": scored["n_failed"],
            "n_errors": scored["n_errors"],
            "nodeids": nodeids,
        }
        log(
            f"reference {task['id']}: {scored['n_passed']}/{expected} "
            f"full_pass={scored['full_pass']}"
        )
        if not scored["full_pass"]:
            raise SystemExit(f"reference solution failed hidden tests for {task['id']}")
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def build_prompt(task: dict, condition: str) -> str:
    spec = spec_path(task).read_text(encoding="utf-8")
    return PREAMBLE + spec.strip() + "\n\n" + TAIL[condition]


def grok_env() -> dict:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    prefix = str(PYTEST_BIN)
    env["PATH"] = prefix + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_grok(prompt: str, workdir: Path) -> dict:
    PROMPT_ROOT.mkdir(parents=True, exist_ok=True)
    prompt_path = PROMPT_ROOT / (hashlib.sha256(prompt.encode()).hexdigest()[:16] + ".txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        str(GROK),
        "--prompt-file",
        str(prompt_path),
        "--always-approve",
        "--output-format",
        "json",
        "--cwd",
        str(workdir),
        "-m",
        "grok-4.7",
        "--no-subagents",
        "--disable-web-search",
    ]
    started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=str(workdir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env=grok_env(),
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
    wall = time.monotonic() - started
    parsed = parse_grok_json(stdout or "")
    return {
        "returncode": proc.returncode,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "parsed": parsed,
        "prompt_path": str(prompt_path),
    }


def parse_grok_json(stdout: str):
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def usage_from(parsed: dict | None) -> dict:
    if not isinstance(parsed, dict):
        return {}
    usage = parsed.get("usage") if isinstance(parsed.get("usage"), dict) else {}
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "num_turns": parsed.get("num_turns"),
        "total_cost_usd": parsed.get("total_cost_usd"),
        "session_id": parsed.get("sessionId") or parsed.get("session_id"),
        "model_usage_keys": sorted((parsed.get("modelUsage") or {}).keys())
        if isinstance(parsed.get("modelUsage"), dict)
        else [],
        "stop_reason": parsed.get("stopReason") or parsed.get("stop_reason"),
    }


def list_files(workdir: Path) -> list[str]:
    files = []
    for path in sorted(workdir.rglob("*")):
        if path.is_file():
            relative = path.relative_to(workdir)
            if any(part == "__pycache__" or part.startswith(".") for part in relative.parts):
                continue
            files.append(str(relative))
    return files


def solution_mentions_repo(workdir: Path) -> list[str]:
    hits = []
    for path in implementation_files(workdir) + test_files(workdir):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "hidden_tests" in text or "ai-written-tests" in text:
            hits.append(str(path.relative_to(workdir)))
    return hits


def attempt_failed(result: dict, workdir: Path, module_filename: str) -> bool:
    """Retry only when the process failed and did not leave the required module."""
    process_bad = result["timed_out"] or result["parsed"] is None or (result["returncode"] not in (0, None))
    module_missing = not (workdir / module_filename).exists()
    return bool(process_bad and module_missing)


def score_attempt(task: dict, workdir: Path, condition: str, expected_n: int, staging_key: str) -> dict:
    staging = SCORE_ROOT / staging_key
    copied = prepare_solution_staging(workdir, staging)
    hidden = score_hidden(staging, hidden_test_path(task), task["module"], expected_n, timeout=PYTEST_TIMEOUT_S)
    hidden["copied_files"] = copied
    ai = None
    if condition == "tests-first" or test_files(workdir):
        ai_staging = SCORE_ROOT / (staging_key + "-aitests")
        ai = score_ai_tests(
            workdir,
            reference_path(task),
            task["module"],
            ai_staging,
            timeout=PYTEST_TIMEOUT_S,
        )
    return {"hidden": hidden, "ai_tests": ai}


def persist_raw(stem: str, payload: dict) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{stem}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def archive_solution(task_id: str, condition: str, rep: int, workdir: Path) -> None:
    dest = SOLUTIONS / condition / f"{task_id}-r{rep}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for path in workdir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(workdir)
        if any(part == "__pycache__" or part.startswith(".") for part in relative.parts):
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, target)


def run_job(task: dict, condition: str, rep: int, expected_n: int) -> dict:
    key = f"{condition}__{task['id']}__r{rep}"
    prompt = build_prompt(task, condition)
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
    attempts = []
    for attempt_index in (1, 2):
        workdir = WORK_ROOT / condition / f"{task['id']}-r{rep}"
        if attempt_index == 2:
            workdir = WORK_ROOT / condition / f"{task['id']}-r{rep}-retry"
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        shutil.copy(spec_path(task), workdir / "spec.md")
        log(f"start {key} attempt {attempt_index}")
        started_at = utc_now()
        try:
            grok_result = run_grok(prompt, workdir)
            error = None
        except Exception as exc:  # noqa: BLE001 - record and maybe retry
            grok_result = {
                "returncode": None,
                "timed_out": False,
                "wall_seconds": None,
                "stdout": "",
                "stderr": "",
                "parsed": None,
                "prompt_path": None,
            }
            error = f"{type(exc).__name__}: {exc}"
            log(f"exception {key} attempt {attempt_index}: {error}\n{traceback.format_exc()}")
        usage = usage_from(grok_result["parsed"])
        session = extract_session(usage.get("session_id"), workdir)
        peek_hits = [
            item
            for item in session.get("commands", []) + session.get("paths", [])
            if looks_like_peek(item, workdir, ROOT)
        ]
        files = list_files(workdir)
        checks = [cmd for cmd in session.get("commands", []) if command_looks_like_check(cmd)]
        raw_payload = {
            "task_id": task["id"],
            "condition": condition,
            "rep": rep,
            "attempt": attempt_index,
            "started_at": started_at,
            "finished_at": utc_now(),
            "wall_seconds": grok_result["wall_seconds"],
            "returncode": grok_result["returncode"],
            "timed_out": grok_result["timed_out"],
            "error": error,
            "usage": usage,
            "stderr": (grok_result["stderr"] or "")[-8000:],
            "parsed": grok_result["parsed"],
            "files": files,
            "session_scan": {
                "found": session.get("found"),
                "n_update_lines": session.get("n_update_lines"),
                "commands": session.get("commands", []),
                "paths": session.get("paths", [])[:80],
            },
        }
        # Keep the unparsed stdout only when JSON parsing failed, so a successful
        # raw file is still the full response object above.
        if grok_result["parsed"] is None:
            raw_payload["stdout_excerpt"] = (grok_result["stdout"] or "")[:20000]
        persist_raw(f"{key}__a{attempt_index}", raw_payload)
        mentions = solution_mentions_repo(workdir)
        process_failed = attempt_failed(grok_result, workdir, task["module"]) or error is not None
        attempt_row = {
            "attempt": attempt_index,
            "workdir": str(workdir),
            "started_at": started_at,
            "finished_at": raw_payload["finished_at"],
            "wall_seconds": grok_result["wall_seconds"],
            "returncode": grok_result["returncode"],
            "timed_out": grok_result["timed_out"],
            "error": error,
            "usage": usage,
            "files": files,
            "wrote_test_file": bool(test_files(workdir)),
            "test_files": [str(path.relative_to(workdir)) for path in test_files(workdir)],
            "check_commands": checks,
            "ran_checks": bool(checks),
            "peeked_outside": bool(peek_hits),
            "peek_evidence": peek_hits[:20],
            "session_scan_found": bool(session.get("found")),
            "solution_mentions_repo": mentions,
            "process_failed": process_failed and not (workdir / task["module"]).exists(),
        }
        should_retry = attempt_index == 1 and attempt_failed(grok_result, workdir, task["module"])
        if not should_retry:
            try:
                scored = score_attempt(task, workdir, condition, expected_n, f"{condition}/{task['id']}-r{rep}-a{attempt_index}")
            except Exception as exc:  # noqa: BLE001
                scored = {"hidden": None, "ai_tests": None, "score_error": f"{type(exc).__name__}: {exc}"}
                log(f"score error {key}: {scored['score_error']}")
            attempt_row["score"] = scored.get("hidden")
            attempt_row["ai_tests"] = scored.get("ai_tests")
            attempt_row["score_error"] = scored.get("score_error")
            archive_solution(task["id"], condition, rep, workdir)
        attempts.append(attempt_row)
        hidden = (attempt_row.get("score") or {})
        log(
            f"done {key} attempt {attempt_index} wall={grok_result['wall_seconds']} "
            f"rc={grok_result['returncode']} timeout={grok_result['timed_out']} "
            f"fraction={hidden.get('fraction') if isinstance(hidden, dict) else None} "
            f"retry={should_retry}"
        )
        if not should_retry:
            break
        log(f"retry {key}: process failed and {task['module']} is missing")

    scored_attempt = attempts[-1]
    hidden = scored_attempt.get("score") or {}
    walls = [a["wall_seconds"] for a in attempts if isinstance(a.get("wall_seconds"), (int, float))]
    costs = [
        a["usage"].get("total_cost_usd")
        for a in attempts
        if isinstance(a.get("usage"), dict) and isinstance(a["usage"].get("total_cost_usd"), (int, float))
    ]
    row = {
        "status": "scored",
        "task_id": task["id"],
        "condition": condition,
        "rep": rep,
        "module": task["module"],
        "prompt_sha256": prompt_sha,
        "n_attempts": len(attempts),
        "wall_seconds": scored_attempt.get("wall_seconds"),
        "wall_seconds_all_attempts": sum(walls) if walls else None,
        "usage": scored_attempt.get("usage"),
        "cost_usd_scored_attempt": (scored_attempt.get("usage") or {}).get("total_cost_usd"),
        "cost_usd_all_attempts": sum(costs) if costs else None,
        "num_turns": (scored_attempt.get("usage") or {}).get("num_turns"),
        "files": scored_attempt.get("files"),
        "wrote_test_file": scored_attempt.get("wrote_test_file"),
        "test_files": scored_attempt.get("test_files"),
        "ran_checks": scored_attempt.get("ran_checks"),
        "check_commands": scored_attempt.get("check_commands"),
        "peeked_outside": any(a.get("peeked_outside") for a in attempts),
        "peek_evidence": [hit for a in attempts for hit in a.get("peek_evidence", [])],
        "solution_mentions_repo": scored_attempt.get("solution_mentions_repo"),
        "timed_out": scored_attempt.get("timed_out"),
        "returncode": scored_attempt.get("returncode"),
        "process_error": scored_attempt.get("error"),
        "fraction": hidden.get("fraction", 0.0) if isinstance(hidden, dict) else 0.0,
        "full_pass": bool(hidden.get("full_pass")) if isinstance(hidden, dict) else False,
        "n_passed": hidden.get("n_passed") if isinstance(hidden, dict) else 0,
        "n_failed": hidden.get("n_failed") if isinstance(hidden, dict) else None,
        "n_errors": hidden.get("n_errors") if isinstance(hidden, dict) else None,
        "n_collected": hidden.get("n_collected") if isinstance(hidden, dict) else 0,
        "n_expected": expected_n,
        "per_test": hidden.get("per_test") if isinstance(hidden, dict) else [],
        "score_error": scored_attempt.get("score_error"),
        "ai_tests": scored_attempt.get("ai_tests") if condition == "tests-first" or scored_attempt.get("wrote_test_file") else None,
        "attempts": [
            {k: v for k, v in attempt.items() if k not in {"score", "ai_tests"}}
            | {
                "fraction": (attempt.get("score") or {}).get("fraction") if isinstance(attempt.get("score"), dict) else None,
                "full_pass": (attempt.get("score") or {}).get("full_pass") if isinstance(attempt.get("score"), dict) else None,
            }
            for attempt in attempts
        ],
        "recorded_at": utc_now(),
    }
    append_jsonl(RUNS_PATH, row)
    return row


def job_order(tasks: list[dict], reps: int) -> list[tuple[dict, str, int]]:
    jobs = []
    for rep in range(1, reps + 1):
        for index, task in enumerate(tasks):
            if (index + rep) % 2 == 0:
                order = ("tests-first", "code-only")
            else:
                order = ("code-only", "tests-first")
            for condition in order:
                jobs.append((task, condition, rep))
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tests-first vs code-only")
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--tasks", nargs="*", default=None, help="Task ids to run. Default: all.")
    parser.add_argument("--conditions", nargs="*", default=list(CONDITIONS))
    parser.add_argument("--skip-validate", action="store_true")
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be >= 1")
    for condition in args.conditions:
        if condition not in CONDITIONS:
            raise SystemExit(f"unknown condition {condition}")
    selected = TASKS
    if args.tasks:
        selected = [task_by_id(task_id) for task_id in args.tasks]
    if not GROK.exists():
        raise SystemExit(f"grok CLI not found at {GROK}")
    if not PYTEST_BIN.exists():
        raise SystemExit(f"pytest tools venv missing at {PYTEST_BIN}. Create it before running.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    env_path = RESULTS / "environment.json"
    if not env_path.exists():
        grok_version = subprocess.run([str(GROK), "--version"], capture_output=True, text=True)
        uname = subprocess.run(["uname", "-a"], capture_output=True, text=True)
        env_path.write_text(
            json.dumps(
                {
                    "recorded_at": utc_now(),
                    "python": sys.version,
                    "grok_version": (grok_version.stdout or grok_version.stderr).strip(),
                    "uname": (uname.stdout or "").strip(),
                    "grok_model_flag": "grok-4.7",
                    "timeout_s": TIMEOUT_S,
                    "max_parallel": MAX_PARALLEL,
                    "extra_flags": ["--no-subagents", "--disable-web-search", "--always-approve", "--output-format", "json"],
                    "pytest": "9.1.1",
                    "matplotlib": "3.11.2",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.skip_validate and VALIDATION_PATH.exists():
        validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    else:
        validation = validate_references()
    expected = {task_id: info["n_tests"] for task_id, info in validation["tasks"].items()}

    done = load_completed()
    jobs = [
        (task, condition, rep)
        for task, condition, rep in job_order(selected, args.reps)
        if condition in args.conditions and (task["id"], condition, rep) not in done
    ]
    log(f"queued {len(jobs)} jobs, skipping {len(done)} already scored, parallel={MAX_PARALLEL}")
    if not jobs:
        log("nothing to do")
        return

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = [
            pool.submit(run_job, task, condition, rep, expected[task["id"]])
            for task, condition, rep in jobs
        ]
        for future in as_completed(futures):
            future.result()
    log("all queued jobs finished")


if __name__ == "__main__":
    main()
