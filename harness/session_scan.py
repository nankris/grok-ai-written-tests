"""Pull command lines and file paths out of a Grok session log.

The headless JSON response does not include tool calls. The on-disk session
update log does. This scanner is best-effort: an unrecognized log shape is
reported as an empty extraction rather than guessed.
"""

import json
from pathlib import Path
from urllib.parse import quote

INTERESTING = {"command", "cmd", "path", "file_path", "target_file", "pattern", "url", "directory"}


def session_dir(session_id: str, workdir: Path) -> Path | None:
    root = Path.home() / ".grok" / "sessions"
    direct = root / quote(str(workdir), safe="") / session_id
    if direct.is_dir():
        return direct
    matches = [path for path in root.glob(f"*/{session_id}") if path.is_dir()]
    if matches:
        return matches[0]
    return None


def _walk(node, found: list[dict]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in INTERESTING and isinstance(value, str) and value.strip():
                found.append({"key": key, "value": value[:800]})
            else:
                _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)


def extract_session(session_id: str | None, workdir: Path) -> dict:
    if not session_id:
        return {"found": False, "events": [], "commands": [], "paths": []}
    directory = session_dir(session_id, workdir)
    if directory is None:
        return {"found": False, "session_id": session_id, "events": [], "commands": [], "paths": []}
    events = []
    updates = directory / "updates.jsonl"
    if updates.exists():
        for line in updates.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    found: list[dict] = []
    _walk(events, found)
    commands = [item["value"] for item in found if item["key"] in {"command", "cmd"}]
    paths = [item["value"] for item in found if item["key"] not in {"command", "cmd"}]
    # De-duplicate while keeping order.
    def uniq(items):
        seen = set()
        out = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    return {
        "found": True,
        "session_dir": str(directory),
        "session_id": session_id,
        "n_update_lines": len(events),
        "commands": uniq(commands),
        "paths": uniq(paths),
    }


def command_looks_like_check(command: str) -> bool:
    text = command.lower()
    markers = ("pytest", "python", "python3", "assert ", "unittest")
    return any(marker in text for marker in markers)


def looks_like_peek(value: str, workdir: Path, repo_root: Path) -> bool:
    text = value.replace("\\", "/")
    work = str(workdir)
    if work and work in text:
        return False
    repo = str(repo_root)
    if repo in text:
        return True
    lowered = text.lower()
    if "hidden_tests" in lowered:
        return True
    if "/reference/" in lowered or lowered.endswith("/reference"):
        return True
    return False
