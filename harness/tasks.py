"""Task metadata. Hidden tests and reference solutions stay out of the solver workdir."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TASKS = [
    {
        "id": "intervals",
        "module": "intervals.py",
        "import_name": "intervals",
    },
    {
        "id": "roman",
        "module": "roman.py",
        "import_name": "roman",
    },
    {
        "id": "lru_ttl",
        "module": "lru_ttl.py",
        "import_name": "lru_ttl",
    },
    {
        "id": "csvline",
        "module": "csvline.py",
        "import_name": "csvline",
    },
    {
        "id": "semver",
        "module": "semver.py",
        "import_name": "semver",
    },
    {
        "id": "ratelimit",
        "module": "ratelimit.py",
        "import_name": "ratelimit",
    },
    {
        "id": "wordwrap",
        "module": "wrap.py",
        "import_name": "wrap",
    },
    {
        "id": "daterange",
        "module": "daterange.py",
        "import_name": "daterange",
    },
    {
        "id": "jsonpath",
        "module": "jsonpath.py",
        "import_name": "jsonpath",
    },
    {
        "id": "rle",
        "module": "rle.py",
        "import_name": "rle",
    },
]


def task_by_id(task_id: str) -> dict:
    for task in TASKS:
        if task["id"] == task_id:
            return task
    raise KeyError(task_id)


def spec_path(task: dict) -> Path:
    return ROOT / "tasks" / task["id"] / "spec.md"


def hidden_test_path(task: dict) -> Path:
    return ROOT / "hidden_tests" / task["id"] / "test_hidden.py"


def reference_path(task: dict) -> Path:
    return ROOT / "reference" / f"{task['id']}.py"
