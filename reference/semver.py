import re

_CORE = re.compile(r"(0|[1-9]\d*)")
_IDENT = re.compile(r"[0-9A-Za-z-]+")


def _split_version(text: str):
    if not isinstance(text, str) or text == "" or any(ch.isspace() for ch in text):
        raise ValueError("invalid version")
    build = None
    if "+" in text:
        text, build = text.split("+", 1)
        if text == "" or build == "":
            raise ValueError("invalid build")
        build_ids = build.split(".")
        if any(part == "" or not _IDENT.fullmatch(part) for part in build_ids):
            raise ValueError("invalid build")
    pre = None
    if "-" in text:
        text, pre = text.split("-", 1)
        if text == "" or pre == "":
            raise ValueError("invalid prerelease")
    parts = text.split(".")
    if len(parts) != 3 or any(_CORE.fullmatch(part) is None for part in parts):
        raise ValueError("invalid core")
    core = tuple(int(part) for part in parts)
    pre_ids = None
    if pre is not None:
        raw = pre.split(".")
        pre_ids = []
        for part in raw:
            if part == "" or not _IDENT.fullmatch(part):
                raise ValueError("invalid prerelease")
            if part.isdigit():
                if _CORE.fullmatch(part) is None:
                    raise ValueError("leading zero in numeric prerelease identifier")
                pre_ids.append((0, int(part)))
            else:
                pre_ids.append((1, part))
    return core, pre_ids


def _cmp_pre(left, right) -> int:
    if left is None and right is None:
        return 0
    if left is None:
        return 1
    if right is None:
        return -1
    for a, b in zip(left, right):
        if a == b:
            continue
        if a[0] != b[0]:
            return -1 if a[0] < b[0] else 1
        return -1 if a[1] < b[1] else 1
    if len(left) == len(right):
        return 0
    return -1 if len(left) < len(right) else 1


def compare_semver(a: str, b: str) -> int:
    core_a, pre_a = _split_version(a)
    core_b, pre_b = _split_version(b)
    if core_a != core_b:
        return -1 if core_a < core_b else 1
    return _cmp_pre(pre_a, pre_b)
