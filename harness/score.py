"""Score a solution directory against the hidden tests, without importing the solution here."""

import ast
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def is_test_file(relative: Path) -> bool:
    name = relative.name
    if name == "conftest.py":
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    return "tests" in relative.parts


def iter_py_files(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        yield path, relative


def implementation_files(root: Path) -> list[Path]:
    found = []
    for path, relative in iter_py_files(root):
        if is_test_file(relative):
            continue
        found.append(path)
    return found


def test_files(root: Path) -> list[Path]:
    found = []
    for path, relative in iter_py_files(root):
        if relative.name == "conftest.py":
            continue
        if is_test_file(relative):
            found.append(path)
    return found


def count_test_functions(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            count += 1
    return count


def parse_junit(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    cases = []
    for suite in suites:
        for case in suite.findall("testcase"):
            status = "passed"
            message = ""
            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")
            if failure is not None:
                status = "failed"
                message = (failure.get("message") or failure.text or "")[:400]
            elif error is not None:
                status = "error"
                message = (error.get("message") or error.text or "")[:400]
            elif skipped is not None:
                status = "skipped"
                message = (skipped.get("message") or "")[:400]
            cases.append(
                {
                    "name": case.get("name"),
                    "classname": case.get("classname"),
                    "status": status,
                    "message": message,
                }
            )
    return cases


def _run_pytest(directory: Path, timeout: int) -> dict:
    junit = directory / "_junit.xml"
    if junit.exists():
        junit.unlink()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--tb=line",
        "-p",
        "no:cacheprovider",
        "--override-ini",
        "addopts=",
        f"--junitxml={junit.name}",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        import os
        import signal

        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    cases = []
    parse_error = None
    if junit.exists():
        try:
            cases = parse_junit(junit)
        except ET.ParseError as exc:
            parse_error = str(exc)
    return {
        "returncode": proc.returncode,
        "timed_out": timed_out,
        "stdout": (stdout or "")[-4000:],
        "stderr": (stderr or "")[-2000:],
        "cases": cases,
        "parse_error": parse_error,
    }


def summarize_cases(cases: list[dict], expected_n: int, pytest_meta: dict) -> dict:
    n_failed = sum(1 for case in cases if case["status"] == "failed")
    n_errors = sum(1 for case in cases if case["status"] == "error")
    n_skipped = sum(1 for case in cases if case["status"] == "skipped")
    n_passed = sum(1 for case in cases if case["status"] == "passed")
    n_total = len(cases)
    collection_failed = n_total == 0
    if collection_failed:
        fraction = 0.0
        denominator = expected_n
    else:
        denominator = n_total
        fraction = n_passed / n_total if n_total else 0.0
    full_pass = (
        not pytest_meta.get("timed_out")
        and n_total == expected_n
        and n_passed == expected_n
        and expected_n > 0
    )
    return {
        "n_passed": n_passed,
        "n_failed": n_failed,
        "n_errors": n_errors,
        "n_skipped": n_skipped,
        "n_collected": n_total,
        "n_expected": expected_n,
        "denominator": denominator,
        "fraction": fraction,
        "full_pass": full_pass,
        "collection_failed": collection_failed,
        "pytest_returncode": pytest_meta.get("returncode"),
        "pytest_timed_out": bool(pytest_meta.get("timed_out")),
        "pytest_stdout": pytest_meta.get("stdout"),
        "pytest_stderr": pytest_meta.get("stderr"),
        "parse_error": pytest_meta.get("parse_error"),
        "per_test": cases,
    }


def score_hidden(solution_dir: Path, hidden_test: Path, module_filename: str, expected_n: int, timeout: int = 60) -> dict:
    staging = solution_dir
    destination = staging / "test_hidden.py"
    shutil.copy(hidden_test, destination)
    meta = _run_pytest(staging, timeout=timeout)
    summary = summarize_cases(meta["cases"], expected_n, meta)
    summary["module_present"] = (staging / module_filename).exists()
    return summary


def prepare_solution_staging(work_dir: Path, staging: Path) -> list[str]:
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    copied = []
    for path, relative in iter_py_files(work_dir):
        if is_test_file(relative):
            continue
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, target)
        copied.append(str(relative))
    return copied


def score_ai_tests(work_dir: Path, reference_file: Path, module_filename: str, staging: Path, timeout: int = 60) -> dict:
    files = test_files(work_dir)
    ast_count = sum(count_test_functions(path) for path in files)
    in_solution = 0
    for path, relative in iter_py_files(work_dir):
        if is_test_file(relative):
            continue
        in_solution += count_test_functions(path)
    result = {
        "test_files": [str(path.relative_to(work_dir)) for path in files],
        "ast_test_count": ast_count,
        "test_functions_inside_solution_modules": in_solution,
        "collected": 0,
        "passed_on_reference": 0,
        "failed_on_reference": 0,
        "errors_on_reference": 0,
        "skipped_on_reference": 0,
        "false_failing": 0,
        "ran": False,
    }
    if not files:
        return result
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copy(reference_file, staging / module_filename)
    for path in files:
        relative = path.relative_to(work_dir)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, target)
    meta = _run_pytest(staging, timeout=timeout)
    cases = meta["cases"]
    failed = sum(1 for case in cases if case["status"] == "failed")
    errors = sum(1 for case in cases if case["status"] == "error")
    skipped = sum(1 for case in cases if case["status"] == "skipped")
    passed = sum(1 for case in cases if case["status"] == "passed")
    result.update(
        {
            "ran": True,
            "collected": len(cases),
            "passed_on_reference": passed,
            "failed_on_reference": failed,
            "errors_on_reference": errors,
            "skipped_on_reference": skipped,
            "false_failing": failed + errors,
            "pytest_timed_out": bool(meta["timed_out"]),
            "pytest_returncode": meta["returncode"],
            "per_test": cases,
        }
    )
    return result
